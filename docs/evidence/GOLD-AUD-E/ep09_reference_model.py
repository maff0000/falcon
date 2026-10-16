#!/usr/bin/env python3
"""EP-9 reference model and tests: 'FALCON outside the executable path'.

This is a TESTS-ONLY reference model (stdlib) showing that each EP-9 requirement is
mechanically testable. It is not production code, not a FALCON component, and it
does not touch any running system. It is NOT the isolated DEV/test FALCON rehearsal;
that rehearsal (requirement R-5 in EP-9) must still be run against an isolated DEV/test
FALCON by the follow-on work. No elapsed-time bound is asserted anywhere (the proposed
baseline-plus-10-percent rule is not approved and is not relied on). The only timeouts
are hang detectors: a test that has not returned is a failure, not a timing measurement.

Run:  python3 docs/evidence/GOLD-AUD-E/ep09_reference_model.py
"""
import collections
import threading
import unittest

HANG_DETECTOR_SECONDS = 30  # hang detector only; not a performance bound


class FalconRead(Exception):
    """Raised if anything in the decision path tries to read FALCON."""


class ReadTrap:
    def __getattr__(self, name):
        raise FalconRead("decision path attempted to read FALCON: " + name)


class Spool:
    """Bounded, drop-on-full, counted, asynchronous evidence spool (EP-9 R-1, R-2)."""

    def __init__(self, capacity, transport, attempts=2):
        self.capacity = capacity
        self.transport = transport
        self.attempts = attempts
        self._q = collections.deque()
        self._cv = threading.Condition()
        self._stop = False
        self.counters = collections.Counter()
        self._t = threading.Thread(target=self._drain, daemon=True)
        self._t.start()

    def offer(self, event):
        """Never blocks, never raises into the caller."""
        with self._cv:
            if len(self._q) >= self.capacity:
                self.counters["dropped_full"] += 1
                return False
            self._q.append(event)
            self.counters["enqueued"] += 1
            self._cv.notify()
            return True

    def _drain(self):
        while True:
            with self._cv:
                while not self._q and not self._stop:
                    self._cv.wait()
                if self._stop and not self._q:
                    return
                event = self._q.popleft()
            for _ in range(self.attempts):
                try:
                    self.transport(event)
                    self.counters["delivered"] += 1
                    break
                except Exception:  # noqa: BLE001 - any transport failure is absorbed and counted
                    self.counters["transport_failures"] += 1
            else:
                self.counters["lost_after_retry"] += 1

    def depth(self):
        with self._cv:
            return len(self._q)

    def close(self, release):
        release()
        with self._cv:
            self._stop = True
            self._cv.notify_all()
        self._t.join(HANG_DETECTOR_SECONDS)


class Journal:
    """Local durable record: the only record the decision path trusts (R-8)."""

    def __init__(self, fail_commit=False):
        self.entries = []
        self.fail_commit = fail_commit

    def commit(self, kind, trigger_id, **fields):
        if self.fail_commit:
            raise OSError("journal write impaired")
        entry = {"seq": len(self.entries) + 1, "kind": kind, "trigger_id": trigger_id, **fields}
        self.entries.append(entry)
        return entry


def run_path(trigger_id, journal, spool, falcon_read, eligible=True):
    """evaluation -> trigger -> claim -> risk -> order -> reconcile.

    Each step commits to the local journal FIRST, then offers an evidence event to
    the spool (R-7). `falcon_read` is a trap: any read raises (R-4). Returns the
    logical outcome (R-6 equivalence compares exactly this).
    """
    outcome = {"trigger_id": trigger_id, "dispositions": [], "orders": [], "fills": [], "positions": [], "terminal": None}
    steps = ["evaluated", "trigger_emitted", "claimed", "risk_checked"]
    for s in steps:
        journal.commit(s, trigger_id)
        spool.offer({"kind": s, "trigger_id": trigger_id, "after_commit_seq": len(journal.entries)})
    if not eligible:
        journal.commit("disposed", trigger_id, outcome="REFUSED")
        spool.offer({"kind": "disposed", "trigger_id": trigger_id})
        outcome["dispositions"].append("REFUSED")
        outcome["terminal"] = "REFUSED"
        return outcome
    journal.commit("order_submitted", trigger_id, order="o-" + trigger_id)
    spool.offer({"kind": "order_submitted", "trigger_id": trigger_id})
    outcome["orders"].append("o-" + trigger_id)
    journal.commit("filled", trigger_id, fill="f-" + trigger_id)
    spool.offer({"kind": "filled", "trigger_id": trigger_id})
    outcome["fills"].append("f-" + trigger_id)
    journal.commit("reconciled", trigger_id)
    spool.offer({"kind": "reconciled", "trigger_id": trigger_id})
    outcome["positions"].append("p-" + trigger_id)
    outcome["dispositions"].append("EXECUTED")
    outcome["terminal"] = "EXECUTED"
    return outcome


def backfill(journal, delivered_kinds):
    """R-9: gap-fill direction is journal -> FALCON, never the reverse."""
    return [e for e in journal.entries if (e["trigger_id"], e["kind"]) not in delivered_kinds]


class Rig:
    def __init__(self, mode, capacity=4):
        self.gate = threading.Event()
        self.delivered = []
        self.mode = mode

        def transport(event):
            if mode == "ok":
                self.delivered.append(event)
            elif mode == "unreachable":
                raise ConnectionError("unreachable")
            elif mode == "rejecting":
                raise ValueError("rejected by FALCON")
            elif mode in ("blocked", "slow"):
                self.gate.wait(HANG_DETECTOR_SECONDS)  # never released during the run
                raise TimeoutError("released at teardown")
            elif mode == "full":
                self.gate.wait(HANG_DETECTOR_SECONDS)
                raise TimeoutError("released at teardown")

        self.spool = Spool(capacity, transport)
        self.journal = Journal()

    def finish(self):
        self.spool.close(self.gate.set)


class TestEP9(unittest.TestCase):
    MODES = ["ok", "unreachable", "rejecting", "blocked", "slow", "full"]

    def _run(self, mode, n=20, eligible=True):
        rig = Rig(mode)
        done = []
        t = threading.Thread(target=lambda: done.extend(run_path("t%d" % i, rig.journal, rig.spool, ReadTrap(), eligible) for i in range(n)))
        t.start()
        t.join(HANG_DETECTOR_SECONDS)
        self.assertFalse(t.is_alive(), "R-1 violated: execution path hung with FALCON mode=" + mode)
        rig.finish()
        return rig, done

    def test_R1_publication_never_blocks_the_path(self):
        for mode in self.MODES:
            rig, done = self._run(mode)
            self.assertEqual(len(done), 20, mode)

    def test_R2_queue_bounded_and_drop_on_full_counted(self):
        rig, done = self._run("blocked", n=20)
        c = rig.spool.counters
        self.assertLessEqual(rig.spool.depth(), rig.spool.capacity)
        self.assertGreater(c["dropped_full"], 0)
        offered = len(rig.journal.entries)
        self.assertEqual(c["enqueued"] + c["dropped_full"], offered)

    def test_R3_failure_modes_do_not_raise_into_the_path(self):
        for mode in ("unreachable", "rejecting"):
            rig, done = self._run(mode)
            self.assertTrue(all(o["terminal"] == "EXECUTED" for o in done), mode)

    def test_R6_logical_equivalence_with_and_without_falcon(self):
        baseline, base_done = self._run("ok")
        for mode in self.MODES[1:]:
            rig, done = self._run(mode)
            self.assertEqual(done, base_done, "logical outcome differs with FALCON mode=" + mode)
            strip = lambda j: [(e["kind"], e["trigger_id"]) for e in j.entries]  # noqa: E731 - counters and timing excluded
            self.assertEqual(strip(rig.journal), strip(baseline.journal), mode)

    def test_R6_refusal_path_equivalence(self):
        baseline, base_done = self._run("ok", n=5, eligible=False)
        rig, done = self._run("blocked", n=5, eligible=False)
        self.assertEqual(done, base_done)
        self.assertTrue(all(o["terminal"] == "REFUSED" for o in done))

    def test_R4_decision_path_never_reads_falcon(self):
        rig = Rig("ok")
        run_path("t1", rig.journal, rig.spool, ReadTrap())  # a read would raise FalconRead
        rig.finish()
        with self.assertRaises(FalconRead):
            ReadTrap().query("trigger")

    def test_R7_emission_follows_local_durable_commit(self):
        rig = Rig("ok")
        run_path("t1", rig.journal, rig.spool, ReadTrap())
        rig.finish()
        for ev in rig.delivered:
            self.assertGreaterEqual(len(rig.journal.entries), ev["after_commit_seq"] if "after_commit_seq" in ev else 1)
        j = Journal(fail_commit=True)
        spool = Spool(4, lambda e: None)
        with self.assertRaises(OSError):
            run_path("t2", j, spool, ReadTrap())
        self.assertEqual(spool.counters["enqueued"], 0, "evidence emitted although the local commit failed")
        spool.close(lambda: None)

    def test_R8_R9_outage_gap_is_backfilled_from_the_journal_only(self):
        rig, done = self._run("blocked", n=10)
        delivered = {(e["trigger_id"], e["kind"]) for e in rig.delivered}
        missing = backfill(rig.journal, delivered)
        self.assertEqual(len(missing), len(rig.journal.entries))
        self.assertTrue(all("seq" in e for e in missing), "backfill source must be the journal")


if __name__ == "__main__":
    unittest.main(verbosity=2)
