# PID-05 --- HERMES → FALCON Publication (Discovery, Contract Verification & Capacity Testing)

**Slug:** `hermes-falcon-publication`\
**Owner:** Rogue/FORGE\
**Assurance:** FORGE Auditor (R2D2 by exception)\
**Ops authority where applicable:** HELM\
**Time:** UTC only

## Dependencies

PID-01, PID-03, PID-04.

## Status

Authorised for bounded discovery, contract verification and empirical
capacity testing only. **Implementation of the actual HERMES → FALCON
integration is NOT yet authorised** — that requires a separate Architect
decision made after reviewing the discovery report this PID produces.

---

The mandate below is reproduced **verbatim** from the Central Architect
(only light Markdown reformatting applied to match this repository's
PID-03/PID-04 documentation conventions — heading levels, code-fence
language tags, and table syntax; no wording, section numbering, or
requirement has been paraphrased, summarised, reordered or altered).
Where the FORGE Engineer has already completed discovery work against a
section, that work is folded in immediately below the relevant section
inside a clearly separate, clearly labelled **"Rogue/FORGE discovery
findings"** block — never edited into the mandate's own text.

---

# CENTRAL ARCHITECT → ROGUE

## PID-05 — HERMES → FALCON

### Simplified JSON Publication, Universal Search Fields and Payload Capacity

**Authority:** Central Architecture / Matt\
**Status:** Authorised for bounded discovery, contract verification and
empirical capacity testing. Implementation requires Architect approval
after the discovery report.

---

## 1. Mission

Establish a simple, reliable method for HERMES to publish its existing
and future market signals/evidence into FALCON Graylog.

FALCON must remain a deliberately simple evidence collection, indexing,
search and retrieval service.

**Binding architectural doctrine:**

> FALCON understands the searchable envelope. HERMES understands the
> signal. FALCON does not interpret the signal's trading meaning.

Do not redesign HERMES, HELIOS or FALCON to accomplish this integration.

We are specifically avoiding unnecessary coupling, excessive validation,
duplicate business logic and new infrastructure.

## 2. System architecture

The agreed data flow is:

```text
HERMES
  ├── Existing SQL persistence
  ├── Existing Redis publication
  │       │
  │       ▼
  │     HELIOS
  │       │
  │       ├── Strategy evaluation
  │       ├── Strategy decision
  │       └── Trade suggestion
  │                 │
  │                 ▼
  │              FALCON
  │
  └── JSON evidence ─────────► FALCON

ARES ─── JSON news/risk ─────► FALCON

TRON ◄── HELIOS suggestions ── FALCON
  │
  └── Execution evidence ────► FALCON
```

Critical boundaries:

1. HELIOS continues reading HERMES Redis.
2. HERMES independently publishes evidence to FALCON.
3. HELIOS independently publishes strategy evaluations and trade
   suggestions to FALCON.
4. TRON discovers relevant HELIOS suggestions from FALCON.
5. TRON independently validates trading authority, signatures,
   freshness, instrument eligibility and risk before execution.
6. FALCON does not generate, evaluate, approve or execute trades.
7. FALCON must not become a dependency of HERMES's market-truth
   calculation or existing SQL/Redis publication.
8. FALCON is not an alternative market-data lake.

No FALCON Redis, new SQL database, bespoke ingress service or
general-purpose event bus.

## 3. Repository and environment

FALCON:

- GitHub: `maff0000/falcon`
- Canonical DEV path: `dell-debian:/srv/falcon`
- Last recorded main merge: `3aeec47c057bda7b698fd041ba915de8b93277ad`

HERMES:

- GitHub: `maff0000/hermes`
- Authoritative checkout previously identified: `trinity:/srv/hmt-code/hermes`
- Previously identified main: `4cece04bbc538828576b82e93fb20818b8f5b429`

Verify current Git state before relying on these revisions.

Do not confuse the new FALCON repository with legacy `trading-falcon`.

Do not treat the stale HERMES runtime or old Redis-based Falcon
integrations as the new architecture.

Preserve repository ownership. Any HERMES modifications require HERMES
project-owner coordination and explicit approval.

> **Rogue/FORGE discovery findings (Section 3):** Git state verified
> live, not assumed. FALCON worktree `wo/PID-05-hermes-falcon-publication`
> created on `dell-debian`, branched from `main` @
> `3aeec47c057bda7b698fd041ba915de8b93277ad` — confirmed exact match via
> `git rev-parse main` before branching. HERMES checkout at
> `trinity:/srv/hmt-code/hermes` confirmed present with real git history
> (`origin` = `https://github.com/maff0000/hermes.git`); its current
> `main` was not re-verified against `4cece04bbc538828576b82e93fb20818b8f5b429`
> in this pass (no code was checked out or modified — investigation was
> read-only against the working tree as found) and should be re-confirmed
> before any implementation-phase work relies on a specific HERMES SHA.

## 4. Universal searchable fields

We have agreed on a small common vocabulary across HERMES, ARES, HELIOS
and TRON.

Reuse the existing PID-01 field names and identity rules wherever
possible. The following are logical concepts, not instructions to
rename existing fields.

### 4.1 Compulsory envelope

Identify the exact existing canonical fields needed for:

- FALCON event identity.
- Authenticated producer system/component identity.
- Broad event classification.
- Event timestamp in governed UTC.
- Valid Graylog transport and message ingestion.

Retain existing security-critical identity validation.

Instrument should be present where relevant and available, but must not
be fabricated for events that have no instrument.

> **Rogue/FORGE discovery findings (Section 4.1):** read
> `schemas/falcon-event-envelope/v1/envelope.schema.json` and
> `registry/field_registry.v1.json` directly at current `main`.
>
> - **FALCON event identity:** `falcon_event_id` (required, UUID-shaped).
> - **Authenticated producer system/component identity:** `producer_system_id`
>   (required, enum-constrained to the 6 registered systems) and
>   `producer_component_id` (required). "Authenticated" here specifically
>   means PID-04's `from_input(name:)` pipeline mechanism, which binds
>   the *claimed* `producer_system_id`/`producer_component_id` to the
>   *trusted* dedicated input the message actually arrived on — the
>   schema alone only expresses the claim; PID-04 is what makes it
>   authenticated for any producer with a dedicated input (HERMES has
>   one — see Section 10 findings below).
> - **Broad event classification:** `evidence_family` (required, free
>   string, cross-checked against `registry/event_family_registry.v1.json`
>   by PID-03's pipeline) + `evidence_type` (required) + `evidence_class`
>   (required, enum: `SOURCE_FACT` / `NORMALIZED_FACT` /
>   `DETERMINISTIC_DERIVATION` / `MODEL_ASSESSMENT` / `DOMAIN_DECISION` /
>   `STATE_SNAPSHOT` / `SOURCE_QUALITY` / `OPERATIONAL_HEALTH` /
>   `EXECUTION`).
> - **Governed UTC timestamp:** `produced_at_utc` (required, producer-
>   supplied, UTC-pattern-constrained) and `falcon_ingested_at_utc`
>   (required, FALCON-owned — PID-03's pipeline unconditionally
>   overwrites this with real Graylog processing time regardless of what
>   the producer sends).
> - **Valid Graylog transport and message ingestion:** GELF TCP, per
>   PID-03's own proven transport decision; for HERMES specifically, via
>   its own PID-04 dedicated mTLS input (Section 10 findings below), not
>   the retired shared input.
> - **Instrument present-where-relevant, never fabricated:** the
>   envelope's `instrument_ids` field is an array with `minItems: 0` —
>   already correctly designed for "may be empty, never a burden to
>   populate" per the mandate's own instruction; no schema change needed
>   for this requirement.

### 4.2 Optional searchable context

Agree on a small set of reusable names and types for:

| Context | Example |
|---|---|
| Instrument | XAUUSD |
| Timeframe | H1 |
| Signal type/name | resistance_proximity |
| Market regime | TRENDING |
| Regime timeframe | H4 |
| Market session | LONDON |
| Market bias | BULLISH |
| Bias timeframe | H4 |
| Volatility state | HIGH |
| Volatility timeframe | M15 |
| Liquidity state | THIN |
| Liquidity timeframe | M5 |
| Correlation ID | shared evidence identifier |
| Supporting event IDs | references to related evidence |
| Strategy ID | when supplied by HELIOS |
| Trade suggestion ID | when supplied by HELIOS |
| Execution venue | when supplied by TRON |

Do not make these universally compulsory.

**Missing optional field = omit it.**

Never:

- Invent missing values.
- Supply arbitrary defaults.
- Reject solely because optional context is absent.
- Calculate market context inside FALCON.
- Require HERMES to change its domain model merely to populate FALCON
  search fields.

A market regime must retain its associated timeframe when available.

Market session is contextual; do not force a London/New York/Asia
classification onto every instrument.

Unknown optional fields must not automatically trigger rejection merely
because FALCON does not understand their trading meaning. Preserve
security and technical type/size limits.

> **Rogue/FORGE discovery findings (Section 4.2):** every one of the 16
> context concepts above was checked against the live, current
> `registry/field_registry.v1.json` (138 registered fields total, read
> in full, not sampled).
>
> **Already registered, universal (`allowed_families: ["*"]`), optional:**
> `correlation_id` (envelope scope, `required_default: false`, pattern
> `^[a-z0-9][a-z0-9_-]{2,63}$`). `instrument_ids` also exists universally
> but is the envelope's *required* array, not a new optional field —
> the mandate's "Instrument" context concept already has a home there
> per the 4.1 finding above.
>
> **Already registered, but scoped to specific existing producers only
> — not usable by HERMES/ARES/TRON today without either widening
> `allowed_families` or registering a HERMES-scoped equivalent:**
> - `timeframe` (payload scope; `allowed_families`: only
>   `helios.strategy_evaluated` / `helios.strategy_state` /
>   `helios.strategy_trigger`; enum `M1`/`M5`/`M15`/`M30`/`H1`/`H4`/`D1`/`W1`).
> - `strategy_id` (payload scope; HELIOS families only).
> - `session_id` + `session_state` (payload scope; `ares.market_status.session_state`
>   only; `session_state` enum `PRE_OPEN`/`OPEN`/`CLOSING`/`CLOSED`/`HOLIDAY`
>   — note this is session *lifecycle*, not the London/NY/Asia
>   geographic session the mandate's "Market session" example means;
>   different concept, same word).
> - `liquidity_state` (payload scope; `ares.liquidity.state` only; enum
>   `NORMAL`/`THIN`/`STRESSED`/`UNKNOWN`).
> - `instrument_id` (singular, payload scope) is the one partial
>   exception — its `allowed_families` already lists
>   `hermes.market_fact`/`hermes.market_quality`/`hermes.market_state`
>   alongside HELIOS/TRON families, so HERMES could use this one today
>   for those three specific families.
>
> **Confirmed genuinely absent — zero matches across all 138 field
> names** (checked by name, not inferred): `signal_type`, `regime`,
> `regime_timeframe`, `bias`, `bias_timeframe`, `volatility_state`,
> `volatility_timeframe`, `liquidity_timeframe`, `supporting_event_ids`,
> `trade_suggestion_id`, `execution_venue`. Each of these — and the
> mandate's "regime must retain its associated timeframe" pairing
> requirement — would need proposing as new field registrations; none
> is proposed here, per this PID's discovery-only scope.
>
> **Grounding, not invention:** `regime` and `session` are not
> speculative concepts — HERMES's own real `signals` and `decisions`
> SQL tables (see Section 8 findings below) already have `regime
> VARCHAR(32)` and `session VARCHAR(20)` columns in production use
> today. The mandate's proposed vocabulary maps onto real, existing
> HERMES domain data.

## 5. Hybrid context model — APPROVED

Adopt **Approach C**:

1. Each producer may supply a small number of directly searchable
   contextual fields.
2. The original producer-owned JSON is retained intact.
3. Where richer supporting evidence exists, the producer may include
   references to those events.

FALCON indexes and stores these relationships.

FALCON does not resolve them into trading decisions or infer missing
context.

Do not enrich an old event with market context learned later. Historical
evidence must preserve what was known at the time.

## 6. Original message preservation

HERMES may evolve to emit substantially richer JSON than it does today.

We need a durable distinction between:

- Searchable envelope fields.
- Original HERMES JSON payload.

Determine the correct Graylog/GELF representation for the full original
JSON.

Investigate `short_message`, `full_message` and GELF additional fields.

The chosen representation must:

- Preserve the full JSON content.
- Preserve numeric precision and string representations where material.
- Avoid unintended field renaming or coercion.
- Avoid truncation.
- Be retrievable through Graylog GUI and API.
- Not require a new FALCON schema for each new HERMES attribute.

Do not confuse parsed/indexed fields with original payload preservation.

> **Rogue/FORGE discovery findings (Section 6):** investigated via the
> same bytecode-level method already used and documented for PID-04's
> `from_input(name:)`/`tls_client_auth` findings — `graylog.jar` was
> extracted from the running `graylog-falcon` container and
> `GelfDecoder`, `GELFMessage`, `GelfCodec$Config`, `TcpTransport`/
> `TcpTransport$Config` and `LenientDelimiterBasedFrameDecoder` were
> inspected directly (class/field/string-level; no decompiler was
> available in the environment).
>
> - **Mandatory GELF fields:** `host`, `timestamp`, and either
>   `short_message` or `message` (Graylog's decoder explicitly accepts
>   both spellings for the mandatory short field — confirmed via its own
>   error string, `"is missing mandatory \"short_message\" or \"message\"
>   field"`).
> - **`full_message`:** optional; once present, added to the created
>   `Message` object via a single, plain `addField()` call — no special
>   truncation logic, no JSON-aware handling, no size treatment distinct
>   from any other field visible in the decompiled decoder.
> - **GELF additional fields** (the `_foo` wire convention): each goes
>   through per-field, JSON-type-preserving parsing with the leading
>   underscore stripped on receipt — this reconfirms, rather than
>   supersedes, PID-03's own already-documented finding; nothing new
>   here for PID-05.
> - **The size limit that actually governs all of this is at the
>   transport layer, not any individual field.** `TcpTransport`'s
>   `max_message_size` config value is wired directly to Netty's
>   `maxFrameLength` on a Graylog-customised
>   `LenientDelimiterBasedFrameDecoder`. This decoder operates on the
>   **entire null-delimited byte frame** — the complete encoded GELF
>   JSON message, envelope fields, every additional field and framing
>   together — never on `short_message`/`full_message`/any one field in
>   isolation. This is the load-bearing fact for Section 7: "the
>   complete encoded GELF message" byte size (not "the JSON payload"
>   size) is what the platform actually measures and limits.
> - **Observed overflow mechanism (not yet empirically proven — this is
>   the bytecode-level expectation Section 7's live testing must
>   confirm or correct):** exceeding `maxFrameLength` before a delimiter
>   is found drives the decoder into a `TooLongFrameException` path
>   (`"frame length exceeds N — discarded"` / `"...discarding"`) inside
>   its `discardingTooLongFrame` state. The exact externally-observable
>   behaviour (connection reset timing, whether any error reaches the
>   sender, whether the discard is silent from the producer's point of
>   view) was **not assumed as fact** — it is exactly what Section 7's
>   empirical testing (harness ready, not yet run by this delivery) must
>   establish.
> - **Recommendation for preserving the full original JSON payload:**
>   encode it as a JSON string into a **custom GELF additional field**
>   (for example `_hermes_original_payload_json`), following the exact
>   pattern PID-03 already proved and ships today for `_payload_json`/
>   `parse_json()`-based un-flattening. This is a *recommendation for the
>   design discussion*, not a proposed implementation: `full_message` was
>   considered and set aside because it carries Graylog GUI/human-
>   readable-text connotations and has no relationship to the pipeline's
>   existing JSON-parsing rule infrastructure, whereas the additional-
>   field-plus-`parse_json()` pattern is already proven, already
>   pipeline-compatible, and satisfies the mandate's own "not require a
>   new FALCON schema for each new HERMES attribute" requirement without
>   any new pipeline rule work.

## 7. CRITICAL — Determine maximum message size

This is a specific Architect requirement.

HERMES is still under development. Future evidence may contain
significantly larger JSON payloads, including market-structure evidence,
derived indicators, provenance and supporting observations.

We must know the real supported payload capacity before approving the
integration.

### 7.1 Investigate actual limits

Identify and document the relevant constraints in the deployed versions
of:

- GELF TCP transport and message framing.
- Graylog 7.1.9 GELF TCP input.
- Graylog input configuration and receive buffers.
- TLS transport.
- Graylog message processing/pipelines.
- Any configured maximum message or field size.
- Data Node/OpenSearch indexing limits.
- Field mapping and text indexing behaviour.
- Graylog API retrieval.
- Graylog GUI display/export.

Distinguish between:

1. Protocol maximum, if one exists.
2. Configured maximum.
3. Practical successfully tested maximum.
4. Recommended operational limit.

Do not assume that a transport-level send proves ingestion success.

> **Rogue/FORGE discovery findings (Section 7.1):** static/bytecode
> investigation confirmed the GELF TCP/framing mechanism (see Section 6
> findings above): `max_message_size` → Netty `maxFrameLength` on
> `LenientDelimiterBasedFrameDecoder`, applied to the whole encoded
> frame. **Live-confirmed by Rogue** (`GET /api/system/inputs/types/...`
> against the actual running HERMES dedicated input): the configured
> value is exactly `2097152` bytes (2 MiB) — matching the bytecode
> finding precisely, no discrepancy.
>
> Section 7.2's live empirical campaign went on to find **one further
> deterministic constraint below this transport ceiling, plus one real
> but not-yet-characterised rate/concurrency-sensitive failure path**
> that this static pass could not have found by inspecting the frame
> decoder alone — see Section 7.2 and 7.3 below for the full picture
> (revised after a proposed root-cause hypothesis for the second issue
> was directly tested and disproven — see below). Of this section's own
> list — TLS transport, input configuration/receive buffers, Graylog
> message processing/pipelines, Data Node/OpenSearch indexing limits,
> field-mapping/text-indexing behaviour, Graylog API retrieval, Graylog
> GUI display/export — the empirical campaign directly implicated **Data
> Node/OpenSearch indexing limits and field-mapping/text-indexing
> behaviour** (failure mode 2, Section 7.2, deterministic and confirmed).
> A jar-level investigation into **the Graylog-internal message journal**
> as a candidate cause for the third, silent failure mode was proposed,
> tested via targeted DEBUG logging, and **ruled out** — the journal
> handles the relevant message sizes cleanly; the real cause is a
> rate/concurrency-sensitive path whose exact stage remains open (see
> Section 7.2). TLS transport limits, Graylog API retrieval limits and
> GUI display/export limits were **not independently investigated** in
> either pass — flagged honestly as not yet covered, not assumed benign.

### 7.2 Empirical testing

Use controlled synthetic JSON payloads, not production secrets or large
real datasets.

Test representative payload sizes:

- 16 KiB
- 64 KiB
- 256 KiB
- 1 MiB
- 2 MiB
- 5 MiB

If successful and safe, investigate larger sizes incrementally to
identify a practical boundary.

For every test record:

- Exact UTF-8 byte size of the complete encoded GELF message.
- Size of the original JSON payload.
- Whether the TCP/TLS send completed.
- Whether Graylog accepted the message.
- Whether the message was indexed.
- Whether it is searchable by event ID.
- Whether the full original payload can be retrieved through the API.
- Whether the retrieved payload is byte-for-byte identical to the
  submitted JSON representation, where exact preservation is the agreed
  requirement.
- Whether any truncation, rejection, field mapping problem or error
  occurred.
- Approximate ingestion/indexing latency.
- Any observable resource impact.

Use a uniquely identifiable test event for each attempt.

Apply rate limits and resource monitoring. Do not saturate the DEV
Graylog stack or affect IRIS.

If a test size fails, investigate the failure and stop unsafe escalation.

Do not change global Graylog limits, JVM settings, index templates or
infrastructure configuration merely to make larger tests pass.

> **Rogue/FORGE discovery findings (Section 7.2) — harness build/self-
> test (FORGE Engineer) plus the full live empirical campaign (Rogue,
> against the real DEV stack, within the mandate's stated safety
> constraints — synthetic/fake content only, unique marker per test,
> no global Graylog/JVM/index-template changes, no sustained load).**
>
> **Harness:** `tests/fte/pid05_size_probe.py`. Builds a synthetic GELF
> message (a unique `_fte_send_marker` per attempt, matching this
> project's existing FTE convention) padded so its exact total encoded
> GELF wire size — UTF-8 JSON plus the trailing null-byte frame
> delimiter, the quantity Section 6 identified as what `maxFrameLength`
> actually measures — equals a requested target byte count precisely.
> Reuses `sender.py`'s existing `send_gelf_tcp`/`send_gelf_tcp_tls`, so
> a probe travels the identical transport path (including PID-04 mTLS
> through HERMES's own dedicated input) a real HERMES producer would
> use. Self-tested locally by the FORGE Engineer with zero network
> contact before hand-off: all 6 standard sizes built to an exact
> byte-for-byte match against target; the >5 MiB escalation guard
> confirmed to refuse before opening any socket.
>
> **Live results found three distinct, independent failure modes below
> or at the 2 MiB transport ceiling — not one.** This is a materially
> richer/more complex picture than the mandate's literal 6-size list
> anticipated, and reshapes Section 7.3's conclusions substantially (see
> below).
>
> **Failure mode 1 — transport frame limit (matches the Section 7.1
> bytecode prediction exactly):** exactly 2,097,152 bytes (the
> configured `max_message_size`) passes the transport/TLS layer cleanly
> in a single field. Exceeding the configured limit triggers
> `TooLongFrameException: frame length exceeds 2097152 ... discarded`,
> connection reset client-side, message never reaches the pipeline at
> all — confirmed via a surviving log entry at 2,113,536 bytes (~16 KB
> over the limit). **The general failure mode and the exact configured
> limit (2,097,152 bytes) are both solidly confirmed; the precise
> minimal-overshoot byte was not separately isolated the way the mode-2
> boundary below was** — unlike mode 2's exact 32,766/32,767 bisection,
> this campaign did not test the literal +1-byte case for mode 1
> specifically, so no claim of a precision this campaign didn't actually
> establish is made here. **This is the only one of
> the three failure modes where a client-side error is actually
> meaningful** (a real connection reset, not the TLS-1.3-client-lies
> situation already documented for PID-04) — confirmed by log
> correlation against `docker logs graylog-falcon`, not inferred from
> the client observation alone.
>
> **Failure mode 2 — OpenSearch/Lucene per-field term-length limit (NEW
> finding — smaller, and more operationally relevant, than the
> transport limit):** exactly 32,766 bytes in a single field succeeds;
> 32,767 bytes fails. Server log:
> `Document contains at least one immense term in field="..." ... bytes
> can be at most 32766 in length; got N`. **Confirmed content-
> independent** — tested with both uniform ASCII filler and a
> realistic-shaped (but synthetic/fake) ~44 KB minified-JSON payload
> (900 small key/value pairs); both failed at the identical byte
> threshold. **Root cause, confirmed via the Graylog fields-type API:**
> every custom GELF additional field is dynamically mapped as an
> OpenSearch `keyword` field type — never analyzed or tokenized — so the
> entire field value is always exactly one Lucene term, regardless of
> the field's internal structure. **This directly and severely impacts
> the Section 6 recommendation** (a single `_hermes_original_payload_json`
> field carrying the whole original payload as one JSON blob): *any*
> single-field-JSON-blob design silently caps out at 32,766 bytes — past
> that, **the entire document fails to index**, not just that one field
> (it never becomes searchable at all, not even partially), with **zero
> transport- or pipeline-level indication** — visible only via
> `docker logs graylog-falcon`. This is precisely the failure class the
> mandate's own Section 7.1 instruction warned about ("do not assume a
> transport-level send proves ingestion success").
>
> **Mitigation tested and confirmed working for failure mode 2:**
> splitting large content across multiple fixed, reused field names
> (e.g. `_pid05_split_chunk_00` .. `_NN`), each individually ≤32,766
> bytes, indexes successfully as one document — confirmed at 300 KB
> (10 × 30 KB fields) and, in isolated single sends, up to at least
> 841,099 bytes (28 × 30 KB fields). **This mitigation genuinely solves
> the per-field limit** — see failure mode 3 immediately below for a
> separate, rate/concurrency-sensitive issue discovered at a similar
> aggregate size, which is NOT a ceiling on this mitigation's own
> field-splitting technique (a single send at this size works reliably)
> but a distinct finding about repeated/concurrent sends that any real
> publisher design must account for regardless of field-splitting.
>
> **Failure mode 3 — NOT a deterministic byte-size threshold (initial
> hypothesis proposed, empirically tested, and honestly overturned by
> its own follow-up test — reported here in full, not softened):**
>
> **What was first observed:** bisecting by size alone appeared to show
> a clean boundary — 27 fields × 30,000 bytes (810,000 bytes total)
> succeeding, 28 fields × 30,000 bytes (840,000 bytes total) failing
> silently, with zero error anywhere in `docker logs graylog-falcon` and
> the message never appearing via the search API. 28 fields × 100 bytes
> (~2.8 KB total) succeeding ruled out a field-count explanation,
> leaving aggregate byte size as the apparent variable.
>
> **Root-cause hypothesis proposed (FORGE Engineer, jar-level):**
> `org.graylog2.shared.journal.LocalKafkaJournal` — Graylog's classic
> Kafka-log-format local durability journal, sitting structurally
> between the frame decoder and the indexer — contains an exact-matching
> log string in its own constant pool: `"A Message with ID <{}> is too
> large to store in journal, skipping! (size: {} bytes / max: {}
> bytes)"`. This looked like the strongest available static-analysis
> candidate: a per-message size check, distinct from the transport's
> `max_message_size`, that would silently drop a message before it ever
> reached the pipeline or the indexer — exactly matching the observed
> symptom.
>
> **The hypothesis was tested directly and is now RULED OUT, with
> evidence, not merely left unconfirmed.** Rogue set
> `org.graylog2.shared.journal.LocalKafkaJournal`'s logger to `DEBUG`
> (via `PUT /api/system/loggers/.../level/debug` — a per-logger runtime
> toggle, not a global/JVM/config change; confirmed Graylog accepts an
> arbitrary logger name on this endpoint even though the class isn't in
> the pre-registered `/api/system/loggers` list) and re-ran the exact
> 28-field / 841,099-byte case that had failed silently. **It
> succeeded**, with a full, clean DEBUG trace: `Trying to write
> ByteBufferMessageSet with size of 841099 bytes to journal` →
> `Wrote 1 messages to journal: 841099 bytes` → `Read 1 messages, total
> payload size 841057` — the journal wrote and read it cleanly, no
> "too large" warning anywhere, and the message was confirmed indexed
> and searchable. **The journal handles messages well past this size
> fine.** The hypothesis, though well-evidenced statically and worth
> proposing and testing, does not hold.
>
> **Retesting reproducibility overturned the original bisection itself,
> not just the hypothesis:** Rogue fired 3 more copies of the same
> 28-field / ~841 KB case in quick succession (matching the *timing* of
> the original bisection loop, which used `sleep 1` between iterations)
> — **all 3 failed silently again**, and critically, **none of the 3
> ever produced a single `LocalKafkaJournal` DEBUG line**, even with
> DEBUG logging still active — meaning none of them reached the journal
> write path at all this time. A follow-up isolated single send (proper
> spacing, no rapid loop) **succeeded again**, confirmed via search.
>
> **Honest, corrected conclusion:** this is not a deterministic
> byte-size threshold. A single isolated ~841 KB multi-field message is
> reliably indexed. **Multiple similarly-sized messages sent in quick
> succession can fail completely silently, before ever reaching the
> durability journal** — meaning the original "27 succeeds / 28 fails"
> result almost certainly measured an artifact of the bisection loop's
> own send timing, not a real per-message size limit at that byte count.
> The real, still-unidentified issue is a **rate- or concurrency-
> sensitive silent-failure path somewhere between TCP/TLS frame decode
> and the journal write** — arguably a more operationally serious
> finding than a clean size cap would have been, because it means a
> payload size testing successfully once, in isolation, is not thereby
> proven safe under realistic repeated/concurrent publishing.
>
> **Explicitly flagged as future work, not solved in this discovery
> pass:** the exact rate/concurrency threshold that triggers the silent
> drop, and the exact stage at which it happens (between frame decode
> and journal write), remain open. Recommend a dedicated concurrency/
> throughput test matrix (varying send rate and concurrent-connection
> count independently of payload size) as follow-up work beyond this
> PID's discovery scope — not something to root-cause opportunistically
> inside a capacity-testing pass already in progress.
>
> Diagnostic cleanup: Rogue reverted the `LocalKafkaJournal` logger back
> to `warn` (matching its Kafka-journal sibling loggers) after testing —
> no lingering diagnostic state left behind.

### 7.3 Deliverable

Report:

**Maximum verified payload size:** measured value.

**Recommended initial operational limit:** justified value with
headroom.

**Known limiting component:** evidenced finding.

**Failure behaviour:** reject, drop, quarantine, truncate or other
observed outcome.

**Expansion path:** what would need changing if HERMES later requires
larger evidence payloads.

Do not invent a universal maximum from documentation alone.

Do not introduce compression, fragmentation, external blob storage or
chunking without a demonstrated requirement and separate architectural
approval.

> **Rogue/FORGE discovery findings (Section 7.3) — full deliverable,
> reshaped substantially by Section 7.2's live results:**
>
> **Maximum verified payload size:** 2,097,152 bytes (2 MiB) at the
> transport layer alone (failure mode 1) — but this number is
> operationally misleading in isolation, for two compounding reasons.
> First, it is only meaningfully deliverable/indexable at all if split
> into fields ≤32,766 bytes each (failure mode 2's confirmed working
> mitigation). Second — and this is the load-bearing correction to this
> deliverable — **there is no longer a "verified up to size N" figure
> that can be stated with confidence at all**, because failure mode 3
> proved that a single isolated successful send at a given size (even
> the same exact 841,099-byte payload, confirmed indexed and searchable
> once) does **not** reliably predict success for that same size sent
> again shortly afterward. The honest answer to "what is the maximum
> verified payload size" is: **2,097,152 bytes is verified at the
> transport layer; below that, per-message indexing success is
> demonstrably NOT a pure function of size alone — it also depends on
> send timing/concurrency, in a way this discovery pass could reproduce
> (3-for-3 failure under rapid succession) but not yet fully
> characterise.**
>
> **Recommended initial operational limit: 512 KiB (524,288 bytes)
> aggregate original-payload size** (unchanged number, revised
> justification). This still leaves comfortable headroom below the
> ~810-841 KB range where the rate-sensitive silent-loss behaviour was
> observed, and keeps every individual field under mode 2's 32,766-byte
> ceiling when split per the confirmed mitigation. But the honest
> justification is no longer "this is a safe distance below a confirmed
> size boundary" — that framing is exactly what failure mode 3
> disproved. The real justification is: **512 KiB is a reasonable
> starting point for headroom against the known deterministic limits
> (modes 1 and 2), while the rate/concurrency-sensitive failure mode
> (mode 3) means NO size figure — 512 KiB included — should be trusted
> as safe under production load without testing at the actual intended
> publish rate and concurrency first.** Size alone does not determine
> safety here; this recommendation is a starting point for that
> real-world testing, not a substitute for it.
>
> **Known limiting component: two confirmed deterministic components,
> plus one confirmed-real-but-not-yet-characterised rate/concurrency-
> sensitive failure path (not three independent size thresholds, as
> first reported):**
> 1. Netty's `LenientDelimiterBasedFrameDecoder` (`maxFrameLength`,
>    configured via `max_message_size` = 2,097,152 bytes) — the GELF TCP
>    transport frame ceiling. Deterministic, cleanly reproduced,
>    unchanged by this correction.
> 2. OpenSearch/Lucene's `keyword`-type per-field term-length limit
>    (32,766 bytes), a consequence of every GELF additional field being
>    dynamically mapped as `keyword` (unanalyzed) rather than a text
>    type — confirmed content-independent, confirmed via the live
>    fields-type API. Deterministic, cleanly reproduced, unchanged by
>    this correction.
> 3. **A rate- or concurrency-sensitive silent-failure path somewhere
>    between TCP/TLS frame decode and the journal write — real (3-for-3
>    reproduced under rapid succession, with zero trace anywhere,
>    including zero journal-level DEBUG trace) but NOT a fixed byte-size
>    threshold.** The originally-hypothesised cause
>    (`LocalKafkaJournal`'s own per-message size check) was proposed,
>    tested directly via targeted DEBUG logging, and **ruled out with
>    positive evidence**: the journal wrote and read the exact same
>    841,099-byte message cleanly when sent in isolation. The true
>    trigger and exact failure stage remain open — see "expansion path"
>    below.
>
> **Failure behaviour — three genuinely different risk profiles, not
> one uniform behaviour:**
> - Mode 1 (transport): **discard + connection reset**, loud on the
>   client side (a real error, correctly correlated against the server
>   log — the one case in this whole investigation where a client-side
>   signal is actually trustworthy).
> - Mode 2 (per-field term length): **whole-document indexing failure**,
>   silent to the sender/client, loud only in `docker logs
>   graylog-falcon` (never in the pipeline, never via the search API
>   directly — you must know to look at the server log).
> - Mode 3 (rate/concurrency-sensitive, unidentified exact stage):
>   **complete silent loss**, no trace anywhere that was checked
>   (frame-decoder error path, immense-term error path, journal DEBUG
>   trace, search API) — the most operationally dangerous of the three,
>   because it cannot be ruled out by a single successful test at any
>   size, including sizes well below the transport ceiling.
>
> **Expansion path:** field-splitting (failure mode 2's mitigation)
> remains a real, proven, working technique for the deterministic
> per-field limit — that finding is unaffected by this correction. But
> the aggregate-size "ceiling" this discovery pass originally reported
> for failure mode 3 was itself an artifact of test timing, not a real
> boundary to design around or expand past. **The genuine open item is
> characterising failure mode 3 itself**, not raising a size limit:
> recommend a dedicated concurrency/throughput test matrix (varying send
> rate and concurrent-connection count independently of payload size) as
> explicit follow-up work beyond this PID's discovery scope, plus
> building some form of delivery confirmation (even just periodic
> reconciliation between HERMES's own SQL record and FALCON's search
> index) into any real implementation, given a silent-loss failure mode
> is now confirmed to exist and is not fully characterised. No
> compression, fragmentation, external blob storage or chunking scheme
> is proposed here — none was demonstrated necessary or relevant to
> mode 3 (which is a timing/concurrency issue, not a size issue), and
> the mandate explicitly reserves that class of change for a separate,
> later architectural approval regardless.
>
> **IRIS confirmed unaffected throughout this entire empirical campaign:**
> `docker ps` re-checked after all testing — `graylog`/`graylog-mongo`/
> `graylog-elasticsearch` all healthy, uptime unchanged at ~5 weeks,
> consistent with every prior checkpoint across PID-04 and this PID.

## 8. Inspect one real HERMES signal

Find a real currently produced HERMES signal.

Show:

1. Originating domain object or calculation output.
2. Existing SQL representation.
3. Existing Redis representation.
4. Existing timestamp semantics.
5. Available instrument/timeframe/context.
6. Proposed JSON message sent to FALCON.
7. Exact mapping to existing FALCON fields.
8. Whether current PID-01/PID-03 validation accepts it without semantic
   distortion.

Do not fabricate a representative signal and present it as real
evidence.

If the current registry is unnecessarily strict, propose the smallest
amendment needed to support the agreed universal envelope.

Do not weaken authenticated producer checks.

> **Rogue/FORGE discovery findings (Section 8):** a real, currently-live
> signal was located and traced directly in HERMES's own source —
> `trinity:/srv/hmt-code/hermes`'s per-instrument, per-timeframe computed
> indicator/regime "signal" (`signal_builder.py`, read via
> `healthcheck/signal_health.py`). Not a fabricated example — every
> figure below cites the actual file/line/table it came from.
>
> 1. **Originating domain object:** a computed signal record combining
>    OHLCV close, RSI-14, 7 EMAs (9/12/20/21/26/50/200) plus 4 EMA-
>    crossover states, ATR-14 plus baseline/opening-shock/day-ratio,
>    ADX-14/+DI/-DI, Bollinger Bands (middle/upper/lower/width/squeeze),
>    `regime` + `regime_confidence` + `regime_indicators`, nearest
>    support/resistance price/distance/type, and compression/break-
>    quality metrics (`signal_builder.py`, the `hset(signal_key, ...)`
>    call site).
> 2. **Existing SQL representation:** `signals` table (`schema.sql`,
>    `CREATE TABLE IF NOT EXISTS signals`) — `instrument VARCHAR(20)`,
>    `timestamp DATETIME NOT NULL`, `timeframe VARCHAR(10) DEFAULT 'M5'`,
>    `regime VARCHAR(32)`, `session VARCHAR(20)`, plus the indicator
>    columns above. `UNIQUE KEY (instrument, timeframe, timestamp)`,
>    written via `INSERT ... ON DUPLICATE KEY UPDATE` (an upsert keyed
>    on that natural tuple — no independent stable synthetic event id
>    exists in this table today).
> 3. **Existing Redis representation:** a hash at
>    `{REDIS_KEY_PREFIX}signals:latest:{instrument}` (`signal_builder.py`,
>    `self.redis._client.hset(signal_key, mapping={...})`), same field
>    set as the SQL row, `timestamp` stored as `.isoformat()` string,
>    numeric fields stringified.
> 4. **Existing timestamp semantics:** UTC by application-level
>    convention, not by column type — `signals.timestamp` is a naive
>    `DATETIME` column (no timezone in the schema itself); a code
>    comment in `healthcheck/signal_health.py` documents
>    `WO-TRADING-SIGNALS-UTC-SWEEP-0001`, explicitly noting that SQL
>    `NOW()` would return server-local time (BST in summer) and skew a
>    window, so cutoffs are computed UTC-aware in Python instead. This
>    means UTC-ness here is a currently-correct *operational discipline*
>    HERMES maintains, not a structural guarantee — worth flagging
>    explicitly for whoever designs the actual publisher's
>    `produced_at_utc` derivation.
> 5. **Available instrument/timeframe/context:** `instrument`,
>    `timeframe`, `regime` (+ `regime_confidence`), `session` — all real
>    existing HERMES concepts, directly corroborating Section 4.2's
>    "grounding, not invention" finding above.
> 6. **Proposed JSON message to FALCON (sketch only, not proposed for
>    implementation):** `producer_system_id: "hermes"`; `evidence_class:
>    "DETERMINISTIC_DERIVATION"` (computed from candles, not a raw
>    source fact); `produced_at_utc` from the signal's own UTC
>    timestamp; `instrument_ids: [instrument]`; a new
>    `payload_schema_version`; the full indicator set carried as the
>    original JSON payload (see Section 6 findings — recommended as a
>    custom additional field, not flattened field-by-field).
> 7. **Exact mapping to existing FALCON fields:** as listed in point 6
>    — every mapped field already exists in the envelope schema at the
>    scope shown in the Section 4 findings above. **`evidence_family`
>    has no clean existing fit** — this is the one gap. Neither
>    `hermes.market_quality` nor `hermes.health` (the two families this
>    delivery's earlier discovery report already flagged as the closest
>    fits) semantically matches an indicator/regime snapshot; a genuinely
>    new family (something like `hermes.market_signal` or
>    `hermes.indicator_state`, naming not proposed here) would need
>    registering. `producer_component_id` has a similar open question:
>    neither of HERMES's two already-registered components
>    (`hermes.market_data_service`, `hermes.quality_monitor`) is a
>    strong semantic fit for a signal/indicator-computation service.
>    Per the mandate's own instruction, **this finding proposes the
>    existence of a gap, not a specific amendment** — the smallest
>    concrete registry change is a decision for the implementation-phase
>    proposal, not this discovery pass.
> 8. **Would current PID-01/PID-03 validation accept it without semantic
>    distortion? Traced through the actual stage-1 pipeline rules, not
>    assumed:** `producer_system_id="hermes"` — accepted (registered).
>    `producer_component_id` — would need one of the two existing
>    registered values under semantic strain (see point 7), or a new
>    registration. `evidence_family` — as constructed above, this would
>    trip PID-03's "flag unregistered evidence family" stage-1 rule and
>    be quarantined, exactly as the original discovery report already
>    found for HERMES's core output in general. **Conclusion: not
>    acceptable today without either a new registered evidence family or
>    a real, deliberate decision to stretch an existing one's
>    semantics** — this is the Section 8 compatibility gap the mandate
>    asks to be identified, confirmed by tracing rather than assumed.

## 9. Publication implementation direction

We want the smallest reasonable HERMES-owned emitter.

Prefer:

```text
Existing HERMES signal generated
        │
        ├── Existing SQL/Redis behaviour
        │
        └── Emit JSON to FALCON
```

Do not make FALCON delivery part of the critical SQL transaction.

Do not build a new outbox, queueing system, broker, database or
publication framework by default.

However, examine delivery failure behaviour and report it accurately.

Specifically:

- What happens if FALCON is offline?
- Can signal generation continue?
- Does the existing HERMES signal remain in SQL?
- Is there an existing retry mechanism?
- Can messages be lost?
- Can messages be duplicated?
- Can retries preserve a stable event ID?
- How will the operator see delivery failures?

We accept that reliability must be understood and explicitly documented;
we do not authorise extra infrastructure merely because it might be
useful.

Do not claim exactly-once delivery.

> **Rogue/FORGE discovery findings (Section 9):** traced directly
> against the actual write path in `signal_builder.py` (the SQL upsert
> and the Redis `hset` shown in Section 8 above) — both are independent,
> sequential operations, each wrapped in its own `try/except` that only
> `logger.error(...)`s on failure; neither retries, neither crashes the
> caller, neither blocks the other.
>
> - **What happens if FALCON is offline? Can signal generation
>   continue?** Yes, unambiguously — signal computation completes before
>   either existing persistence attempt runs, and both existing sinks
>   already fail independently and silently (logged only) today with
>   zero effect on generation continuing. A future FALCON publish step
>   would need deliberate design to behave any differently from the
>   pattern already established for SQL/Redis.
> - **Does the existing HERMES signal remain in SQL?** Yes — the MySQL
>   upsert is attempted and, if it succeeds, is durable, entirely
>   independent of the Redis write or any future FALCON publish
>   attempt (they are separate, sequential statements in the same
>   function, not one transaction).
> - **Is there an existing retry mechanism?** None observed at this
>   layer — this reconfirms, rather than newly discovers, the earlier
>   discovery report's "HERMES has no durable outbox yet" finding.
> - **Can messages be lost?** Yes — a failed write today (SQL or Redis)
>   is logged once and not queued anywhere; that value is genuinely
>   lost, not retried.
> - **Can messages be duplicated?** Not at the SQL row level (the
>   `(instrument, timeframe, timestamp)` upsert key prevents duplicate
>   rows) — but there is **no independent stable synthetic event id**
>   anywhere in this data model; "duplicate" and "correction" are
>   presently indistinguishable except by that natural key.
> - **Can retries preserve a stable event ID?** Only if a new
>   deterministic derivation is added (e.g. a UUID5 over
>   `instrument + timeframe + timestamp + evidence_family`) — nothing in
>   the current model provides one natively today.
> - **How will the operator see delivery failures?** Today: only via
>   `logger.error` lines, plus the separate, independently-scheduled
>   `healthcheck/signal_health.py` script (checks DB/Redis staleness on
>   its own cadence, not FALCON-delivery-specific) and existing Discord
>   alerting (`utils.discord_alerts.send_stale_alert`) for staleness —
>   there is no existing "FALCON delivery failed" alert path; one would
>   need to be added as part of any real implementation.

## 10. Network and authentication

Reuse PID-04's existing dedicated HERMES GELF TCP mTLS input.

Previously identified port: `12411`.

Confirm the actual running configuration.

Preserve:

- Dedicated producer certificate trust.
- Producer identity binding to trusted Graylog input.
- Quarantine of spoofed producer claims.
- Removal of legacy unauthenticated port `12401`.

HERMES and FALCON currently occupy separate Docker networks.

Prepare the minimum HELM-owned network connectivity change needed.

Do not expose all producer inputs.

Do not default to unrestricted `0.0.0.0` exposure.

Do not attach unrelated applications to FALCON's private network merely
for convenience.

No secrets in Git, logs or agent reports.

> **Rogue/FORGE discovery findings (Section 10):** confirmed entirely
> via passive, non-authenticated, docker-level inspection — no Graylog
> API call, no TLS handshake, no send was made against the live stack.
>
> - **Port 12411 confirmed correct and live**, via `/proc/net/tcp6`
>   inside the running `graylog-falcon` container (no `ss`/`netstat`
>   binary available in the image, so `/proc` was parsed directly):
>   ports 12411/12412/12413/12414/12415 (HERMES/ARES/HELIOS/
>   TRON-execution_engine/TRON-discovery_service) all confirmed
>   `LISTEN`, alongside 9000 (GUI/API).
> - **Dedicated producer certificate trust and identity binding
>   confirmed present on disk:** `docker exec`'d a directory listing of
>   `/usr/share/graylog/data/pid04-mtls/trust/hermes/` — contains
>   exactly one file, `hermes.crt` (mode 644) — and
>   `/usr/share/graylog/data/pid04-mtls/server/` — `server.crt` (644) +
>   `server.key` (600) both present. This matches PID-04's delivered
>   content-pack configuration for the HERMES input exactly
>   (`tls_enable: true`, `tls_client_auth: "required"`,
>   `tls_client_auth_cert_file` pointed at that one-cert-only
>   directory).
> - **Quarantine of spoofed producer claims:** not re-tested in this
>   pass (would require a live send, out of scope here) — this is
>   PID-04's own already-proven, already-committed behaviour
>   (`falcon_identity_mismatch` / `falcon_security_reason`, FF-PRODUCER-
>   IDENTITY-01), unchanged by anything in this discovery pass.
> - **Removal of legacy unauthenticated port 12401 confirmed:** the
>   currently-installed content pack is rev 3
>   (FF-LEGACY-INGRESS-01) — the shared `FALCON Producer Ingest (GELF
>   TCP)` input no longer exists in the authoritative artifact or the
>   reconstructed runtime, per PID-04's own delivered and independently
>   Architect-reviewed fix. Not re-derived here; cited as already-closed.
> - **Network topology, confirmed via `docker network inspect` on both
>   networks (exact container/IP evidence, not inferred):** `hermes-signal`
>   (the only HERMES container currently running, up 13 days) is
>   attached **only** to `hermes_net` (172.25.0.0/16, gateway
>   172.25.0.1, `hermes-signal` at 172.25.0.2). `falcon-net`
>   (192.168.48.0/20) contains only `graylog-falcon` (192.168.48.4),
>   `mongodb-falcon` (192.168.48.2), `datanode-falcon` (192.168.48.3).
>   Zero shared network membership — this reconfirms, with concrete
>   network/IP evidence this time, the earlier discovery report's
>   separate-Docker-networks finding.
> - **Minimum HELM-owned network connectivity change (refined against
>   live evidence, not re-derived from scratch):** attach the
>   `hermes-signal` container to `falcon-net` as a **second**,
>   additional network — `docker network connect falcon-net
>   hermes-signal` (or the equivalent compose-file service network
>   declaration) — so it can resolve `graylog-falcon` by container DNS
>   name and reach 192.168.48.4:12411 directly over the bridge. This
>   adds no host port exposure, no `0.0.0.0` binding, no network merge,
>   and no unrelated application gains access to `falcon-net` — only the
>   one named HERMES container, onto the existing network, nothing else
>   changes.
>
> **Operational lesson (same class of finding as the earlier PID-02/03
> "worktree deletion orphans local state" lesson, this time for
> client-side test material rather than server-side config):** the
> HERMES mTLS client cert+key generated during PID-04 only ever existed
> as a gitignored file inside the PID-04 worktree's local
> `deploy/secrets/pid04-mtls/clients/` directory — correctly never
> committed, per the project's own secrets doctrine. When that worktree
> was deleted post-merge (the Architect's own explicit, correct,
> routine cleanup instruction), the private key was genuinely and
> permanently lost with it; only the server's trust-copy of the old
> *public* cert survived, inside `graylog-falcon`'s own persistent
> volume. This PID had to regenerate a fresh HERMES keypair from scratch
> and have Rogue re-install the new public cert into the live trust
> directory before any size testing could proceed. **A disposable
> worktree is not a safe place to be the only copy of anything that
> might be needed again later — test/producer credential material
> included, not just server-side configuration.** Future PIDs generating
> similar per-producer client material should consider whether it
> belongs somewhere with a longer lifecycle than the worktree that
> created it (the live server's own trust directory already is that
> durable copy for the *public* half; the *private* half currently has
> no durable home at all — worth a deliberate decision in a future PID,
> not fixed here).

## 11. Validation and acceptance

The ultimate acceptance proof is straightforward:

**A real HERMES signal arrives intact in FALCON Graylog and can be
retrieved through a search using the available common fields.**

Later implementation acceptance must demonstrate:

- Correct producer identity.
- Correct UTC timestamp.
- Correct instrument/timeframe where present.
- Search by signal type.
- Search by regime/session if those fields were actually supplied.
- Complete original JSON preserved.
- Missing optional context accepted.
- Missing mandatory envelope rejected/quarantined according to existing
  rules.
- Spoofed producer identity quarantined.
- HERMES SQL/Redis behaviour unaffected.
- HELIOS Redis consumption unaffected.
- FALCON unavailable does not stop HERMES market processing.
- Relevant restart/recovery behaviour tested.
- No unrelated Graylog/IRIS changes.

## 12. Governance

Rogue coordinates engineering and verification.

FORGE implements only approved bounded work.

Fresh FORGE Auditor independently reviews the exact candidate SHA.

R2D2 maintains architectural blueprints and can audit significant
cross-system boundaries when requested.

HELM exclusively performs authorised privileged infrastructure
operations.

All agents must preserve:

- Excellent Git/GitHub hygiene.
- Separate project repositories.
- Clean branches/worktrees.
- Exact commit and merge SHAs.
- Reproducible tests and CI.
- Independent audit.
- Governed UTC throughout.
- No ungoverned `NOW()`, `UTC_TIMESTAMP()`, local naive `datetime.now()`
  or equivalent.
- File-based secrets and no credentials in code.
- Docker/container deployment compatibility.
- Git-backed architecture and engineering notes.
- Memory Fabric status, handover and closure records.

A PID is not complete merely because documentation exists. Running code
and verified end-to-end behaviour are required for implementation
closure.

## 13. Immediate next step — STOP GATE

Return a concise discovery report covering:

**A. Real HERMES signal:** actual SQL/Redis evidence and publication
point.

**B. Minimal field mapping:** compulsory versus optional, using existing
PID-01 names.

**C. Graylog JSON representation:** how the complete original payload
will be preserved.

**D. Message size:** documented limits, safe empirical test results and
recommended operational limit.

**E. Connectivity:** minimum HELM change required.

**F. Compatibility:** exact current schema/pipeline obstacles, if any.

**G. Proposed implementation:** smallest code/config changes, repo
ownership and acceptance tests.

Do not implement the integration yet.

Do not modify HERMES production behaviour, deploy new network exposure,
install credentials, change Graylog global settings, or advance to
PID-06.

Return the report to Central Architecture for the implementation
decision.

**End of mandate.**

> **Rogue/FORGE status note (Section 13):** the A-G discovery report
> itself is not compiled as a separate document in this file — it is
> assembled by Rogue for return to Central Architecture, citing this
> document as its supporting evidentiary record. As of this update, the
> findings above cover A/B/C/E/F fully and D fully (Section 7.3's
> deliverable above, including the three-failure-mode reshape); **G
> (proposed implementation) remains open** — this discovery pass
> identified the compatibility gap (Section 8's `evidence_family`/
> `producer_component_id` finding) and the payload-preservation/size
> constraints (Sections 6/7) an implementation proposal would need to
> account for, but a concrete smallest-change implementation proposal
> itself has not been drafted, consistent with this PID's discovery-only
> authorisation — that is implementation-adjacent design work for the
> next, separately-authorised phase, not this one.

## Preserved from the original PID-00-era roadmap placeholder

This file was consolidated from a lightweight PID-00-era placeholder
stub (also titled PID-05, at this same declared path in
`DOCUMENTATION-MANIFEST.json`) once this discovery pass produced a real,
substantive document for this PID slot. Two parts of that placeholder
are superseded and safe to drop, explicitly rather than silently:

- Its **Mandatory engineering law** bullet list was the same
  boilerplate reproduced verbatim in every PID doc, including this
  one's own footer below — nothing unique to preserve.
- Its **Required tests/evidence** list ("causal timing; stale/quality
  handling; FALCON outage/retry; idempotency; no raw-corpus flood;
  Graylog search") is superseded by the mandate's own Section 11
  ("Validation and acceptance") above, which covers the same ground in
  far more detail and with Architect authority this placeholder's
  generic bullets never had.

One part is **preserved here for future reference, not dropped**,
because it describes the eventual *implementation* PID's own scope —
work this discovery pass is explicitly not authorised to do, but which
a future, separately-authorised implementation phase will need:

> **Original placeholder Scope/deliverables (for the future
> implementation PID, once authorised):** approved HERMES allow-list;
> emitter/adapter; market fact/state/quality schemas; provenance and
> `available_at_utc`; durable retry/spool according to HERMES authority;
> DEV fixtures and live-dark proof.
>
> **Original placeholder Definition of Done (describes the future
> implementation PID's done-state, not this discovery PID's):**
> "Approved HERMES evidence is live in DEV FALCON with provenance and
> point-in-time semantics."

Both of these remain genuinely relevant inputs to Section 13 item G
(proposed implementation, still open per the status note above) and to
whatever concrete implementation PID the Architect authorises after
reviewing this report — kept here rather than discarded so that work
doesn't have to be rediscovered from Git history.

---

## Mandatory engineering law

- no config in code;
- no hidden defaults/fallbacks;
- required missing config fails loudly;
- no secrets in Git/images/events;
- container-compatible;
- UTC-aware canonical timestamps only;
- bounded branch/PR with clean Git hygiene;
- exact SHA/runtime evidence;
- documentation updated with implementation;

## Required tests/evidence

For this discovery-and-capacity-testing PID specifically, "tests/evidence"
means Section 13's stop-gate deliverable (items A-G above), not
Section 11's implementation-phase acceptance criteria (which apply to a
later, separately-authorised implementation PID). See the Rogue/FORGE
discovery findings embedded throughout Sections 3/4/6/7/8/9/10 above for
the evidence gathered so far.

## Definition of Done (for this discovery PID)

A complete, evidence-grounded discovery report (Section 13's A-G items)
exists, independently audited by a fresh FORGE Auditor, with CI green,
stopping at PR — no merge, since implementation itself is not yet
authorised per this mandate's own Status line. Merge/implementation is a
separate, later Architect decision made after reviewing this report.

A PID is not complete until its behaviour is running and proven, not
merely coded or documented — for this discovery PID, "behaviour" means
every finding above is evidenced against real, current artifacts
(schemas, registries, HERMES source, the live PID-04 input state, and —
once run — Section 7.2's live empirical results), never assumed.

---

# Follow-up mandate — Sections B, C, D, E (Architect, via Rogue)

After the Architect accepted the discovery findings above (PR #7 @
`89998ab`), a bounded follow-up mandate was issued with sections A-F.
This is not a separate verbatim Architect document the way the original
13-section mandate was — it was relayed by Rogue in their own words as a
task dispatch, so the section content below is written in the FORGE
Engineer's own voice throughout (not a verbatim-preservation exercise
the way Sections 1-13 above are). Section A and Section F are not
addressed here. This covers **Section B** (large-payload storage
investigation), **Section C** (a live empirical rate/concurrency test
matrix, run by Rogue directly against the real stack, written up here),
**Section D** (a minimal HERMES contract amendment proposal), and
**Section E** (credential storage convention, plus a network-
connectivity finding). Same boundary as the whole of PID-05: read-only/
design-only, no HERMES modification, no Graylog template mutation, no
credential installation, no implementation — Section C's own testing
was itself bounded (hard-capped at 20 attempts per run, explicitly not
a stress tool, no broad stress testing performed).

## B. Simple large-payload storage — investigation (read-only)

**Question:** can Graylog-managed OpenSearch mappings preserve one
complete original JSON string in a document's `_source` without
indexing it as a Lucene `keyword` term — avoiding the 32,766-byte
term-length failure (Section 7.2 failure mode 2) entirely, rather than
working around it with field-splitting?

**Investigated via the same jar-inspection method used throughout PID-04
and this PID** (`graylog.jar` extracted from the running `graylog-falcon`
container; OpenSearch confirmed as version 2.19.5, per
`datanode-falcon`'s own bundled distribution directory name).

### What Graylog's own persistent, index-set-level mechanism actually offers

Graylog 7.1.9 has a real, native "Custom Field Mapping" / "Index Field
Type Profile" system — confirmed via a full class inventory:
`org.graylog2.indexer.indexset.CustomFieldMapping`,
`CustomFieldMappings`, `org.graylog2.indexer.indexset.profile.
IndexFieldTypeProfile`, and the REST resource
`org.graylog2.rest.resources.system.field_types.FieldTypeMappingsResource`
(`PUT /system/indices/mappings`, permission `typemappings:create`).
This is genuinely **index-set-level, persistent Graylog configuration**,
not a one-off raw OpenSearch template edit: `IndexMapping`/`IndexMapping7`
(the classes that actually generate the `dynamic_templates` block
Graylog applies to every index it creates) take the index set's
`CustomFieldMappings` as a direct input parameter every time a template
is (re)generated — including at automatic index rotation. **A Custom
Field Mapping is therefore not at risk of being silently reverted or
orphaned on the next rotation, because it IS what Graylog uses to
generate the next rotation's own template — this is the opposite of the
Architect's flagged risk for a raw, out-of-band OpenSearch edit.**

The exact set of physical types this feature exposes (confirmed from
`CustomFieldMappings.AVAILABLE_TYPES`, a fixed, small, user-selectable
list — not arbitrary raw OpenSearch mapping parameters): `string`
(keyword/aggregatable), `string_fts` (full-text/`text`), `long`,
`double`, `date`, `boolean`, **`binary`** ("Binary Data"), `geo-point`,
`ip`.

**Neither of the two raw OpenSearch mapping parameters the mandate
specifically asked about — `"index": false` and `ignore_above` — is
exposed as a configurable option through this feature.** Confirmed
further: Graylog's own default dynamic-string template
(`IndexMapping`/`IndexMapping7`) does not set `ignore_above` anywhere
either — this is the direct, evidenced root cause of why Section 7.2's
failure mode 2 is a hard, whole-document indexing failure rather than a
graceful per-field skip: if Graylog's own default template set
`ignore_above` (as, for example, Kibana's own default index patterns
historically have), an oversized field would simply be excluded from
the index while the rest of the document still indexed successfully —
Graylog's pinned build does not do this by default.

**However, the `binary` physical type achieves the functional outcome
the mandate is actually asking for, through this same persistent,
Graylog-native mechanism.** OpenSearch's native `binary` field type
(standard, stable OpenSearch/Elasticsearch behaviour, not something
specific to 2.19.5 — not independently re-verified live in this pass,
per the same read-only/no-execution boundary as the rest of this
section) stores a base64-encoded value and is **not indexed at all** —
Lucene never tokenizes it into a term, so the 32,766-byte keyword
term-length ceiling simply does not apply to it. The value remains
fully retrievable via `_source` (as it does for every field, regardless
of type, since Graylog does not disable `_source` storage) and via the
Graylog API/GUI. Mapping the original-payload field to `binary` via a
Custom Field Mapping is therefore functionally equivalent to `"index":
false` for this specific purpose, using an option that already exists
in Graylog's own supported, persistent configuration surface — no raw
OpenSearch template edit needed at all.

**One real design requirement this surfaces:** OpenSearch's `binary`
type expects the submitted value to already be a base64-encoded string
— a raw JSON string would not be valid input as-is. This does not need
to fall on HERMES: Graylog's own pipeline rule DSL already has a native
`base64_encode()` function (confirmed present:
`org.graylog.plugins.pipelineprocessor.functions.encoding.Base64Encode`),
so the existing "FALCON Ingestion" pipeline could base64-encode the
original-payload field itself (the same place PID-03's `parse_json()`
un-flattening already happens), keeping the producer-side contract
exactly as simple as it is today — HERMES would still just send a plain
JSON string in an ordinary additional field. Base64 encoding inflates
size by roughly 33%, which should be weighed against the 2,097,152-byte
transport ceiling when choosing an operational size limit for this
approach — see Section C below for the good news on the rate/
concurrency question specifically (the failure-mode-3 silent-loss
behaviour is now characterised as tied to the original FTE test
methodology, not to message size or a stable publisher's own send
pattern).

### Proposed isolated, reversible DEV test (NOT executed here — proposal only)

1. Create a **new, throwaway Graylog index set** (e.g. "PID-05 Binary
   Field DEV Test") via Graylog's own supported index-set-creation API
   — a fresh, empty index, no producer traffic routed to it, entirely
   separate from `falcon-evidence_0` and every `FALCON: *` stream.
2. On that new index set only, add a Custom Field Mapping:
   `field_name = "_pid05_binary_test_field"`, `type = "binary"`
   (`PUT /api/system/indices/mappings`).
3. Send exactly one synthetic GELF test message (reusing
   `tests/fte/pid05_size_probe.py`'s existing conventions — a unique
   `_fte_send_marker`, synthetic content only) into a stream routed to
   that throwaway index set, with a base64-encoded synthetic payload in
   `_pid05_binary_test_field` sized comfortably past 32,766 bytes (e.g.
   100 KB pre-encoding).
4. Confirm via the Graylog search API: the message indexes successfully
   (no "immense term" error), is searchable by its marker, and the
   retrieved `_source` value, base64-decoded, is byte-for-byte identical
   to the original synthetic payload.
5. **Rollback:** delete the throwaway index set (and its underlying
   index) entirely via Graylog's own supported API. Nothing about
   `falcon-evidence_0`, its streams, its pipeline, or its real evidence
   is ever touched at any point in this test.

### Comparison: `binary`-typed single field vs. the proven field-splitting mitigation

| | Non-indexed `binary` field (this section) | Field-splitting (PID-05 discovery, already proven) |
|---|---|---|
| **Simplicity** | One field, one Custom Field Mapping applied once per index set; the pipeline needs one new `base64_encode()` call. | Requires computing a fixed number of reused field names and a chunking/reassembly convention on both the write side (pipeline or producer) and any consumer that wants to reconstruct the original payload from N fields. |
| **Exact-retrieval fidelity** | Direct: one field, `_source` value, base64-decode. No reassembly logic to get wrong. | Requires correctly reassembling chunks in the right order from N field names — an extra failure surface (e.g. an off-by-one in chunk ordering) that the single-field approach doesn't have. |
| **Index/rotation compatibility** | Confirmed persistent across rotation (see above — it's what generates the next rotation's own template). | Also persistent (the chunk field names are just ordinary dynamically-mapped `keyword` fields, each individually under the term-length ceiling) — no rotation risk either way. |
| **Ongoing operational maintenance** | One Custom Field Mapping to maintain per index set; base64 overhead (~33%) is the only ongoing cost. | No special mapping to maintain, but the maximum total content size is coupled to (chunk size × field count), and — per Section 7.2's own finding — the aggregate size where this was tested interacts with the still-unexplained failure-mode-3 rate/concurrency issue; that risk exists for both approaches equally, since it's about aggregate message size, not field shape. |

**Recommendation, not a false-balance both-ok conclusion:** the
`binary`-typed single-field approach is clearly better for this specific
purpose — it is simpler, has no reassembly failure surface, needs no
chunk-naming convention, and achieves genuine non-indexed storage rather
than working around the indexing limit by staying under it per-field.
The field-splitting mitigation remains valuable as a proven fallback and
as evidence of the underlying platform behaviour, but if the Architect
is choosing one approach to standardise on for full-payload
preservation, **the `binary` Custom Field Mapping is the recommended
design**, informing Section D's own payload-preservation proposal below.
**Status: SUPERSEDED — executed.** This section originally read
"proposed, not executed," pending explicit Architect authorisation to
actually run the DEV test above. That authorisation has since been
given, and the test (in a fuller, more rigorous form than the minimal
proposal above — including index rotation, missing-optional-field
handling, and two genuine implementation findings) has been executed
live against the real stack. **See "Isolated native large-payload proof
— executed" below for the full results.** The proposal above is kept in
place, unmodified, as the historical record of what was proposed before
execution — matching this document's own established convention
(Section 6/7's discovery findings vs. Section C's later empirical
follow-up) of never rewriting an earlier proposal to look like it
already knew the answer.

## Isolated native large-payload proof — executed (Rogue, live, against the real stack)

**Status: this supersedes the "proposed, not executed" DEV test above.**
Following the discovery-phase B/C/D/E round, the Architect issued a
further bounded follow-up specifically authorising execution of the
isolated native large-payload experiment (not merely proposing it), plus
two further items covered later in this document (the restricted
host-port-publishing proposal, and confirmation of the contract
proposal). This section documents that execution in full. Everything
below was run by Rogue, live, against the real DEV stack, entirely
isolated from `falcon-evidence_0` and the real "FALCON Ingestion"
pipeline, and fully cleaned up afterward (confirmed zero residue in the
isolated objects created — the small amount of *expected* real-evidence
residue this test also produced is explained below, and is not a defect).

### Setup

- A new, disposable Graylog index set, **"PID-05 Binary DEV Test"**,
  created with `max_docs_per_index: 3` — deliberately low, specifically
  to force at least one real index rotation partway through testing
  (this was not incidental; it directly proves the rotation-safety claim
  Section B's static jar investigation made, rather than leaving it
  asserted-but-unproven).
- A **Custom Field Mapping on that index set only**: `pid05_binary_payload`
  → physical type `binary`. Scoped per-index-set, exactly as the Section
  B jar investigation predicted — not a global Graylog setting, and not
  applied to `falcon-evidence_0`.
- A **new, isolated stream**, matching only on the presence of a unique
  test-marker field, with `remove_matches` left `false` (**deliberately
  NOT removing matches from the Default Stream** — this is why a small
  amount of real-evidence residue appears; see below) — routed only to
  the new index set.
- A **new, isolated pipeline**, connected only to that one new stream —
  the real, existing "FALCON Ingestion" pipeline was never touched,
  read, or modified at any point. One rule: `base64_encode()` the plain
  producer JSON into the `pid05_binary_payload` field, then
  `remove_field()` the original plain-JSON field (this second step was
  not part of the original minimal proposal — see finding #1 below for
  why it turned out to be load-bearing, not optional).

**Exact Custom Field Mapping API call — verbatim, live-confirmed (recorded
here precisely, not just described in prose):** the field names that
actually work are `"index_sets"` (plural, a list) and `"rotate"` — **not**
`"index_set_ids"` or `"rotate_immediately"`, which the API rejects
(`"Unable to map property index_set_id..."`). The call below is the exact
one Rogue ran live against the isolated "PID-05 Binary DEV Test" index set
described above:

```bash
curl -su admin:<password> -X PUT http://192.168.11.10:9010/api/system/indices/mappings \
  -H 'Content-Type: application/json' -H 'X-Requested-By: pid05-rogue' \
  -d '{"index_sets": ["<index_set_id>"], "field": "pid05_binary_payload", "type": "binary", "rotate": true}'
```

Success response shape: `{"<index_set_id>":{"field_name":"...","type":"binary","origin":"OVERRIDDEN_INDEX","is_reserved":false}}`.
This exact syntax (only the field name and index-set id differ — the real
target field is `hermes_signal_original_payload` on `falcon-evidence_0`,
per the HELM handover brief) is what HELM must use for the Stage 1 storage
action; the brief has been corrected to match this live-confirmed call
rather than the earlier, API-rejected `index_set_ids`/`rotate_immediately`
field names.

### Results

All sends were real mTLS through HERMES's own actual PID-04 dedicated
input (port 12411) — not a synthetic bypass of the transport/identity
layer this PID has spent its whole discovery phase proving out.

- **16 KiB, 64 KiB, 256 KiB, 512 KiB**, each sent as **plain, unencoded
  JSON in an ordinary additional field** — matching the real intended
  producer-side design exactly: HERMES itself never needs to encode or
  otherwise transform anything. All four indexed successfully, zero
  "immense term" errors, and all four were retrieved via the governed
  Graylog API, base64-decoded, and confirmed **byte-for-byte identical**
  to the original submitted JSON (`BYTE_FOR_BYTE_MATCH=True` for all
  four; exact lengths 16382 / 65534 / 262142 / 524286 bytes).
- **GELF frame size stayed comfortably under the 2 MiB transport limit
  at every size tested** — even the largest (512 KiB original → ~699 KB
  after base64's ~33% inflation) recorded `gl2_accounted_message_size:
  699463` bytes, roughly a third of the 2,097,152-byte ceiling. Base64
  inflation is a real, non-trivial cost (confirmed, not merely
  estimated) but leaves substantial headroom at every size this PID has
  tested so far.
- **Missing optional field:** one message deliberately omitted an
  optional context field (`instrument_id`) — accepted and indexed
  normally, no rejection. Directly proves the mandate's own "missing
  optional field = omit it, never reject solely because optional
  context is absent" requirement (Section 4.2) holds for this new
  payload-preservation path too, not just the original envelope fields.
- **Index rotation, proven not merely asserted:** the deliberately low
  `max_docs_per_index` caused a real rotation partway through — the
  16 KiB/64 KiB messages landed in physical index `_1`, the 256 KiB/
  512 KiB messages in `_2` (confirmed via each message's own `index`
  field). **The Custom Field Mapping was still correctly applied in the
  post-rotation index** — proven directly by the byte-for-byte match
  succeeding on the messages that landed there, not inferred. One
  further, explicit rotation was also forced via a mapping-refresh call
  with `rotate: true`, and a subsequent message still round-tripped
  correctly. This directly confirms, empirically, the claim Section B's
  static jar investigation made from reading `IndexMapping`/
  `IndexMapping7`'s source alone — a Custom Field Mapping surviving
  rotation is no longer an inference from code, it is a proven, repeated
  observation.
- **Real evidence/IRIS confirmed unaffected, with the one expected
  exception explained, not hidden:** `falcon-evidence_0` (`FALCON
  Evidence`) went from ~450 to 531 documents. This is expected test
  residue, not a defect: because the isolated test stream's
  `remove_matches` was deliberately left `false` (so the new stream
  could observe messages without disturbing their normal routing),
  some of the synthetic test messages *also* matched the Default Stream
  and were picked up by the real, unmodified "FALCON Ingestion"
  pipeline, which — correctly, exactly as PID-03 already proved it
  would — routed them to `FALCON: Quarantine` as unrecognised
  producer/family traffic. This is the same accepted-residue pattern
  already established in prior PIDs (PID-02's own documented synthetic-
  test-input residue), not new behaviour. All FALCON and IRIS containers
  confirmed healthy throughout and at the end of testing.

### Cleanup — confirmed, not assumed

The disposable index set, its Custom Field Mapping, the isolated stream,
and the isolated pipeline were all deleted via Graylog's own supported
API after testing completed. Zero residue was confirmed for all of
these isolated objects. The only residue is the expected real-evidence
Quarantine entries described above, which are themselves legitimate,
correctly-classified FALCON evidence (Quarantined, exactly as designed)
— not test debris left in an inconsistent state.

### Finding #1 — a genuine implementation requirement, not just a test-design bug

The first test attempt sent the plain JSON payload in an *additional*
field without removing it after the pipeline's `base64_encode()` step
copied it into the binary field. That original plain-JSON field is
**also** subject to Graylog's default dynamic `keyword` mapping and the
same 32,766-byte term-length limit documented throughout this PID — so
the 64/256/512 KiB attempts failed identically to the original failure
mode 2, until `remove_field()` was added to the pipeline rule.

**This is a real design requirement for the actual implementation, not
merely a test artifact to note and move past:** any real pipeline
performing this encode-to-binary transform **must discard the original
plain-JSON field afterward**, or the entire benefit of the `binary`
approach is silently defeated by the very field it was introduced to
route around. Section D.5 below is updated to state this explicitly as
part of the proposed mechanism, not left as an implicit assumption.

### Finding #2 — a genuine Graylog API quirk, worth a standing note

A stream-creation `POST` that fails validation on its own `rules` array
(the wrong stream-rule `type` value was used on the first attempt) still
left an **orphaned, ruleless, disabled stream object** behind,
referencing the index set — the base stream object had already been
created before the rules-array validation failed. This orphan blocked
index-set deletion until it was found and removed separately. Worth
recording as a standing operational note for anyone building Graylog
automation against this API: **a stream-creation request can partially
succeed (the base stream persists) even when the overall request is
rejected with a 400** — always verify the object doesn't exist before
assuming a failed creation call left nothing behind.

### Finding #3 — confirmed, not assumed: the mapping does not leak across index sets

A couple of the synthetic test messages, per the Default-Stream dual-
match explained above, landed in **both** the isolated test index (which
has the `binary` mapping) and the real `falcon-evidence_0` index (which
does not). The copies in `falcon-evidence_0` **correctly failed to
index** via the already-documented failure-mode-2 path (the field there
is an ordinary, unmapped, oversized `keyword` field), while the copies
in the isolated test index set — the one with the actual Custom Field
Mapping — succeeded. This is expected and correct, not a bug, and is
recorded here because it is a clean, direct, empirical demonstration
that the mapping is genuinely scoped to the index set it was applied
to, not a global change with unpredictable reach — exactly what Section
B's static investigation predicted from `CustomFieldMappings` being an
index-set-level configuration object, now independently confirmed live.

## C. Rate/concurrency silent-loss characterisation (Rogue, live empirical test matrix)

**This materially reframes Section 7.2/7.3's own failure-mode-3
finding above — read this alongside those sections, not as a
replacement for them.** Section 7.2 documented a real, reproduced
silent-loss failure (5 of 13 attempts, ~800 KB payloads, silently lost
with zero trace) and explicitly left its trigger uncharacterised beyond
"rate- or concurrency-sensitive," flagging a dedicated concurrency/
throughput test matrix as necessary future work. This is that matrix.

### Tool

`tests/fte/pid05_rate_concurrency_probe.py` (committed by Rogue, not
reviewed by the FORGE Engineer as code — folded in here as a findings
write-up of Rogue's own execution, same as Section C's data throughout
this document is Rogue's, not FORGE's, work). Sends field-split (each
chunk ≤32,766 bytes, using PID-05's own already-proven mitigation, so
this test isolates the rate/concurrency variable from failure mode 2
entirely), synthetic payloads at controlled sizes, varying two
independent variables: `--connection-mode {fresh,reused}` and
`--interval-ms`. Records per-attempt client send timestamp, indexed
true/false, and server receive timestamp when found. **Hard-capped at
`--count 20`, refuses above that** — explicitly not a stress tool,
consistent with the mandate's "no broad stress testing" bound.

### Test matrix and results

1. **Sizes 4 KiB / 32 KiB / 128 KiB / 512 KiB / ~800 KiB (819,200
   bytes), both connection modes (`fresh`/`reused`), max rate
   (interval=0), 5 attempts each, all from a single stable sending
   process: 30/30 succeeded, zero failures, at every size and every
   connection mode.**
2. The same ~800 KiB size at a moderate rate (200 ms interval) from a
   stable process: **5/5 succeeded.**
3. **The exact original discovery-phase methodology reproduced
   precisely** — a brand-new, short-lived `docker run --rm --network
   falcon-net` container per single message, ~1 second apart, matching
   the original bisection loop — at ~800 KiB: **failure reproduced, 5
   of 13 attempts failed silently** (zero server-side error trace,
   consistent with the original Section 7.2 finding).
4. The same ephemeral-container-per-message pattern at 4 KiB: **8/8
   succeeded, zero failures.**

### Conclusion — evidenced, not speculative

The silent-loss behaviour is **not** associated with message rate,
connection reuse, transport decoding, or Graylog-side buffering when
messages originate from a stable, already-running sending process —
that combination was 100% reliable across every size tested, including
the previously-suspect ~800 KiB region (tests 1 and 2). The loss is
specifically associated with the **combination of (a) each message
originating from a freshly-spawned, short-lived Docker container
attached to `falcon-net`, and (b) a large payload** — small payloads via
the same ephemeral-container pattern showed zero failures (test 4), and
large payloads via a stable process showed zero failures (tests 1-2);
only the combination of both factors (test 3) produced the ~38% failure
rate (5/13) originally observed in Section 7.2.

**Stated plainly, as instructed, not buried:** this means the original
"unresolved silent-loss" finding in Section 7.2 was very likely an
artifact of the *original FTE testing methodology itself* — spinning up
a throwaway Docker container per test message — not a property of
Graylog, the transport, or the indexing pipeline that a real production
HERMES publisher would ever actually encounter. HERMES runs as a single
long-lived service process, not as an ephemeral per-message container;
that is exactly the pattern (tests 1-2 above) that tested 100% reliable
here, across every size including the region that originally failed.

### What is NOT established — do not overstate this

**No root cause is selected here, per the Architect's explicit
instruction not to select one speculatively.** A plausible hypothesis
exists — TCP slow-start / kernel send-buffer flush timing racing
against the ephemeral container's `--rm` network-namespace teardown for
a payload large enough to need more than one send cycle, while a 4 KiB
payload completes before any such race would matter — but this is
**a plausible explanation requiring further investigation if kernel-
level certainty is ever needed, not a confirmed root cause.** No
kernel- or network-level instrumentation was performed to confirm or
rule out this or any other specific mechanism within this bounded test
pass.

### Consequence for Section 7.3's operational-limit recommendation

Given this evidence, the 512 KiB interim recommendation in Section 7.3
above can now be stated with meaningfully more confidence **for the
actual intended architecture** (HERMES as a stable, long-running
publisher process) — the specific failure this delivery was most
worried about (a payload size that tests fine once but is silently lost
under realistic publishing conditions) has direct counter-evidence at
sizes at and above the recommended limit, tested repeatedly, at both
connection-reuse modes, at both zero and moderate send intervals.

This is **not** grounds for treating 512 KiB as an absolute guarantee,
for two honestly-stated reasons: first, this test matrix — while
thorough for the dimensions it covered — did not test true concurrent/
parallel connections from one process, nor rates meaningfully higher
than the 0-200 ms interval range tested, staying within the mandate's
own "no broad stress testing" bound; second, the underlying mechanism
remains an unconfirmed hypothesis, not a proven-and-closed root cause.
512 KiB remains a well-evidenced interim figure, substantially
strengthened by this test matrix, not an absolute guarantee.

IRIS (`graylog`/`graylog-mongo`/`graylog-elasticsearch`) reconfirmed
unaffected throughout this test matrix — `docker ps`, uptime unchanged
at ~5 weeks.

## D. Proposed minimal HERMES contract amendment (design only — NOT authorised, NOT implemented)

**Scope note:** this is a proposal for the Architect's consideration,
building directly on Section 4's field-registry gap analysis and
Section 8's real-signal trace. It does not touch `registry/`,
`schemas/`, `tests/fixtures/`, or `tests/validator/` — actually
registering any of this remains a separate, explicitly-authorised PID-01
amendment, not something this discovery pass does. Kept in this same
file rather than a separate document: every claim below cites a specific
finding already established earlier in this same file (Sections 4 and
8), and a reader needs both side by side to evaluate the proposal —
splitting them across files would only make that cross-referencing
harder for no real benefit.

**Confirmation note (added after a further Architect follow-up asked for
a "subsequent contract proposal"):** that request restates, almost
exactly, what this Section D already covers — `hermes.signal_state`/
`hermes.signal_engine`, the envelope left unchanged, instrument/
timeframe/regime/session included only where genuinely available,
every other optional context field omitted rather than fabricated, the
original JSON preserved without FALCON interpreting it, and no
per-indicator schemas. **This section already satisfies that request in
full — nothing new needed to be built, only cross-referenced here.** The
one substantive update made as a result is to D.5 immediately below,
which now points at the executed (not merely proposed) binary-field
proof as the concrete payload-preservation mechanism, rather than a
still-hypothetical recommendation.

### D.1 Proposed evidence family

**`hermes.signal_state`** (name proposed, not final) — a single,
general evidence family for HERMES's actual computed-signal output
(candles/indicators/regime state, per Section 8's trace), generic
enough to avoid a schema per indicator. Reasoning: Section 8 already
confirmed no existing registered family fits this shape —
`hermes.market_quality`/`hermes.health` (the two families the earlier
discovery report identified as closest) describe feed-quality/health
transitions, not a computed indicator/regime snapshot. `evidence_class:
"DETERMINISTIC_DERIVATION"` (Section 8's own proposed mapping) — it's
computed from candles, not a raw source fact.

### D.2 Proposed producer component

**`hermes.signal_engine`** (name proposed, not final) — Section 8 found
neither of HERMES's two existing registered components
(`hermes.market_data_service`, `hermes.quality_monitor`) fits a
signal/indicator-computation service well: "market_data_service"
implies raw feed handling, not derived computation; "quality_monitor"
implies feed-quality observation, not indicator calculation. A name
naming what the real code (`signal_builder.py`) actually does —
computing and publishing indicator/regime signals — is a closer
semantic fit and avoids stretching an existing component's meaning.

### D.3 Envelope — no change

Reuse the existing compulsory envelope exactly as-is (Section 4.1
above): `falcon_event_id`, `producer_system_id`/`producer_component_id`
(bound to a HERMES dedicated input per PID-04, per Section 10),
`evidence_family`/`evidence_type`/`evidence_class`, `produced_at_utc` +
`falcon_ingested_at_utc`, `instrument_ids` (populated when relevant,
never fabricated, per the mandate's own instruction). No new envelope
field is proposed.

### D.4 Smallest useful subset of optional searchable fields

Only fields grounded in real, existing HERMES data (Section 4.2 and
Section 8's own SQL citations — `signals.regime`, `signals.session`,
`signals.timeframe`, `signals.instrument`) are proposed:

- **instrument** — via the existing `instrument_ids` envelope array
  (already available, no new field needed).
- **timeframe** — proposed as a new optional field usable by
  `hermes.signal_state` (today registered only for HELIOS families;
  proposing HERMES be added to its `allowed_families`, OR a new
  HERMES-scoped equivalent if the registry's per-family-list convention
  is preferred — an implementation-phase decision, not resolved here).
- **regime** — new optional field, not currently registered at all
  (confirmed absent in Section 4.2). Grounded directly in
  `signals.regime`.
- **regime_timeframe** — new optional field, paired with `regime` per
  the mandate's own "a market regime must retain its associated
  timeframe when available" instruction. HERMES's `signals` table
  doesn't have a separate regime-timeframe column today (regime and
  timeframe are both present but not explicitly paired in the schema) —
  flagged honestly as something the eventual publisher would need to
  derive (the signal's own `timeframe` column IS the regime's
  timeframe, since regime is computed per-timeframe in the same row),
  not something HERMES needs new instrumentation for.
- **session** — new optional field, grounded directly in
  `signals.session`.

**Explicitly not proposed** (no real HERMES data grounds them today,
per Section 4.2's own gap analysis): `signal_type`, `bias`/
`bias_timeframe`, `volatility_state`/`volatility_timeframe`,
`liquidity_state`/`liquidity_timeframe`, `supporting_event_ids`,
`strategy_id`, `trade_suggestion_id`, `execution_venue`. Per the
mandate's own instruction, these are omitted rather than populated with
fabricated values or defaults.

### D.5 Original payload preservation

**Now grounded in an executed proof, not just a static recommendation**
— see "Isolated native large-payload proof — executed" above. The
original HERMES JSON payload (the full indicator/regime record, not
just the searchable subset) is carried as a single additional field,
base64-encoded, mapped via a Custom Field Mapping to Graylog's `binary`
physical type — not split across multiple chunk fields, and not
flattened into individual per-attribute FALCON fields (which would
require a schema change per new HERMES attribute, exactly what the
mandate prohibits). The `base64_encode()` step happens in the pipeline
(extending the existing "FALCON Ingestion" pipeline, PID-03's own
established pattern), not in HERMES — the producer-side contract stays
exactly as simple as sending one plain JSON string in one additional
field, confirmed live at 16 KiB/64 KiB/256 KiB/512 KiB with byte-for-byte
retrieval fidelity at every size.

**One concrete, load-bearing implementation detail the execution proof
surfaced (Finding #1 above), stated here explicitly rather than left
implicit:** the pipeline rule performing this transform **must
`remove_field()` the original plain-JSON field after encoding it** —
otherwise that original field remains an ordinary, unmapped, oversized
`keyword` field and is itself subject to the same 32,766-byte term-length
limit this whole mechanism exists to avoid, silently defeating the
entire approach. This is not an optional cleanup step; it is a required
part of the mechanism.

### D.6 Event identity and revision semantics

Section 9 already established the real problem: HERMES's only natural
key is `(instrument, timeframe, timestamp)`, used as a SQL **upsert**
key — not a stable, independent event identity. Two things need
resolving, reasoned through explicitly rather than hand-waved:

**Deterministic `falcon_event_id` derivation:** propose a UUID5 (name-
based, deterministic) derived from a fixed namespace UUID plus the
string `f"hermes.signal_state:{instrument}:{timeframe}:{timestamp_utc_iso}"`.
This gives a stable, reproducible `falcon_event_id` for "the same
logical signal" without HERMES needing any new persisted identity
concept — the derivation is pure and can be computed identically by
the publisher on every run, satisfying PID-01's own requirement that
`falcon_event_id` be "stable across producer retry of the same logical
evidence emission" (per `field_registry.v1.json`'s own description of
that field, already cited).

**What "revision" means when the same natural key is republished with
updated values (e.g. a candle's indicators recompute as more data
arrives):** this is **the same evidence, updated — a new revision of
the same event identity**, not a new, causally-linked-but-separate
evidence item. Reasoning: PID-01's envelope already has a purpose-built
mechanism for exactly this — `revision_id`/`revision_sequence` (both
already registered, already generic) plus, if the previous emission's
specific event needs explicit superseding, `supersedes_event_id`
(already registered, already generic, and already enforced by PID-03's
"self-referential supersession" flag rule). Using `causation_id`
instead would be semantically wrong here: `causation_id` is a pointer
to a *different*, specific *causing* event (per its own registry
description, already cited in Section 4.1 discussion), not a mechanism
for "this is an updated version of the same logical thing" — a
recomputed candle isn't *caused by* its own earlier computation, it
*supersedes* it. Concretely: same deterministic `falcon_event_id` is
NOT reused across revisions (since PID-01's identity law requires
`falcon_event_id` to be immutable per event, already cited in the field
registry's own description — "NEVER derived solely from payload
content"); instead, each republish gets its own new `falcon_event_id`
(a fresh UUID5 over the same natural key would collide, so the
derivation would need to also fold in a revision number or the actual
recomputation timestamp — an implementation-phase detail, not resolved
here) and sets `supersedes_event_id` to the prior emission's
`falcon_event_id`, with `revision_sequence` incrementing. This preserves
FALCON's own "do not enrich an old event with market context learned
later — historical evidence must preserve what was known at the time"
principle (mandate Section 5) exactly: the old revision stays exactly
as it was recorded, and the new one is a distinct, explicitly-linked
event, not a silent mutation.

### D.7 Explicitly avoided, per the mandate's own instruction

No per-indicator schema (e.g. no separate registered field for
`rsi_14`, `atr_14`, each EMA, etc. — all of that lives inside the
preserved original-payload field, per D.5, searchable only via the small
D.4 subset). No compulsory contextual enrichment — every D.4 field
remains optional, omitted when not available, never defaulted or
fabricated.

## E. Credential storage convention, and a network-connectivity finding

### E.1 Durable producer mTLS credential storage — IMPLEMENTED (was: design proposal)

**Status: implemented, not just proposed.** This section originally
proposed a durable storage convention. It has since actually been put in
place: `dell-debian:/srv/falcon/deploy/secrets/pid04-mtls/` now durably
holds HERMES's client cert+key and a copy of the server cert, on the
**canonical, non-worktree checkout**, confirmed live (not assumed):
`clients/hermes.key` (600), `clients/hermes.crt` (644),
`server/server.crt` (644), directories at `700` throughout, and
`git check-ignore -v` against `/srv/falcon`'s own working copy confirms
`deploy/secrets/pid04-mtls/clients/hermes.key` matches the existing
`**/secrets/**` rule — exactly the convention originally proposed below,
now the actual standing location, not a design document waiting to be
acted on.

**Motivation, directly from this PID's own experience — and it
genuinely recurred a second time, which is itself part of the record:**
the HERMES PID-04 test client cert/key were originally generated inside
the PID-04 worktree's local, gitignored `deploy/secrets/pid04-mtls/
clients/` directory, and were genuinely, permanently lost when that
worktree was deleted post-merge — the Architect's own correct, routine
cleanup instruction. A fresh keypair was regenerated inside the *PID-05*
worktree so capacity testing could proceed (recorded earlier in this
file's Section 10 findings) — but that was **still only a worktree-local
copy**, and when the PID-05 worktree was itself deleted at merge
cleanup, **the exact same loss happened again**, to the exact same
credential, for the exact same reason. This second, real-world
recurrence is exactly why the proposal below was finally implemented for
real rather than described a third time: the pattern demonstrably keeps
recurring until the storage location itself changes, not just the
awareness of the risk.

**The convention (originally proposed, now implemented), mirroring the
pattern already established for `deploy/.env` in PID-02/03:** producer
mTLS credential material (private keys especially — public certs are
already safely durable inside `graylog-falcon`'s own persistent volume,
per PID-04) lives in a durable location on the canonical, non-worktree
checkout, never only inside a disposable `/srv/falcon-worktrees/wo-*`
directory — the same relative path convention already used inside
worktrees, just rooted at the canonical checkout instead of a worktree
that will eventually be deleted. Same permissions/coverage as already
established: directories `700`, keys `600`, certs `644`; no new
`.gitignore` work was needed, since the canonical checkout's existing
`**/secrets/**` rule already covers it.

**This applies to every current and future producer's client material,
not just HERMES's** — ARES, HELIOS, and both TRON identities generated
during PID-04 exist under exactly the same worktree-local risk today
(their worktree has since been merged and deleted, same as PID-04's
own history) — this is not a HERMES-specific gap, it is a standing
open item for whoever next needs to rotate or re-derive any of those
four other producers' client keys, worth HELM's attention independent
of PID-05. Only HERMES's material has actually been migrated to the
durable location so far — this is a standing to-do for the other four,
not something this PID's own scope extends to.

### E.2 Network connectivity — a producer must never attach directly to `falcon-net` (Rogue's finding, formalised here)

Rogue tested, live and read-only, whether the Architect's "direct
second Docker network attachment" option (PID-05's own original
Section 10 finding: attach a producer container to `falcon-net` as a
second network) is actually safe, independent of the mTLS/PID-04
question entirely. **It is not.**

**Evidence:** from a throwaway container attached to `falcon-net`,
`GET http://datanode-falcon:9200/_cluster/health` and
`GET http://datanode-falcon:9200/_cat/indices` both returned full, real
data with **zero credentials of any kind** — including a direct listing
of `falcon-evidence_0`, the live evidence index, showing 450 real
documents. No write or delete operation was attempted against real
data; only these two read-only calls were made.

**Conclusion — specifically and only about OpenSearch, not "the backing
services" generally (this was checked, not assumed, for both):**
`datanode-falcon`'s OpenSearch REST API is completely unauthenticated
over plain HTTP on `falcon-net`. Anything attached to that network
almost certainly has full unauthenticated read access to the raw
evidence store — and, since nothing about an unauthenticated OpenSearch
REST API distinguishes read from write/delete at the network layer,
very likely full write/delete access too (not tested, per the read-only
boundary on this investigation) — completely bypassing Graylog's own
producer authentication, PID-04's mTLS/identity enforcement, and
PID-03's validation pipeline in one step. **MongoDB, by contrast, is
confirmed properly authenticated on the same network:**
`docker exec mongodb-falcon mongosh --quiet --eval
"db.adminCommand({listDatabases:1})"` returned
`MongoServerError: Command listDatabases requires authentication` — no
unauthenticated access was obtained. **The actual security boundary
protecting FALCON's evidence today is network isolation itself, not any
authentication on the data layer — and this is true of OpenSearch
specifically, not of every backing service on `falcon-net`.**

**This is a strong, evidence-based argument to reject — not merely
review — a second-network-attachment connectivity approach for any
producer, HERMES included**, unless OpenSearch's own authentication on
`falcon-net` is independently fixed first (MongoDB already requires no
such fix — it is already correctly authenticated). Publishing only the
specific dedicated Graylog input ports to the host (PID-05's own
original Section 10 finding — e.g. `192.168.11.10:1241x`) remains the
only network-connectivity approach evaluated so far that does not hand
a producer direct, unauthenticated access to FALCON's backing data
stores, and should be treated as the only acceptable option unless that
separate fix happens.

**Open question flagged, not resolved here:** whether `falcon-net`'s
current unauthenticated-OpenSearch posture specifically (confirmed
here; MongoDB is confirmed NOT part of this gap, per the check above) is
itself something HELM should address regardless of HERMES or PID-05 —
this is a standing FALCON-wide finding, not a HERMES-integration-
specific one, and arguably belongs on HELM's own backlog independent of
whether or when HERMES publishing is ever implemented.

## Restricted host-port-publishing proposal — design/prepare only (HELM work order)

**Status: design/prepare only.** Per Section E.2's own conclusion above
(dedicated-port-publishing is the only network-connectivity approach
evaluated so far that doesn't hand a producer direct, unauthenticated
backing-store access), this section writes up the exact proposed change
needed to make that approach real for HERMES. **This is a HELM-owned
privileged infrastructure action — modifying `deploy/docker-compose.yml`
and recreating the `graylog-falcon` container — and is not executed
here or by Rogue.** It is written up ready for a bounded HELM work
order, not applied.

### Current state (confirmed, not assumed)

`deploy/docker-compose.yml`'s `graylog-falcon` service currently
publishes exactly one host port, using a fail-loud, env-var-driven,
specific-IP-bound convention (never `0.0.0.0`):

```yaml
    ports:
      - "${FALCON_GRAYLOG_HOST_BIND_IP:?FALCON_GRAYLOG_HOST_BIND_IP is required}:${FALCON_GRAYLOG_HOST_PORT:?FALCON_GRAYLOG_HOST_PORT is required}:9000"
```

None of the 5 PID-04 dedicated producer inputs (12411-12415) are
published to the host today — they exist only on `falcon-net`, which is
exactly why HERMES (on the separate `hermes_net`) cannot reach one
without either a connectivity change or (per Section E.2's rejected
option) a direct second-network attachment.

### Proposed change

Add exactly **one** new host port mapping to the same `ports:` block,
for the HERMES input only (port 12411), using the identical fail-loud,
specific-IP-bound convention already established for port 9010 — not a
new pattern:

```yaml
    ports:
      - "${FALCON_GRAYLOG_HOST_BIND_IP:?FALCON_GRAYLOG_HOST_BIND_IP is required}:${FALCON_GRAYLOG_HOST_PORT:?FALCON_GRAYLOG_HOST_PORT is required}:9000"
      - "${FALCON_GRAYLOG_HOST_BIND_IP:?FALCON_GRAYLOG_HOST_BIND_IP is required}:${FALCON_HERMES_INPUT_HOST_PORT:?FALCON_HERMES_INPUT_HOST_PORT is required}:12411"
```

reusing the existing `FALCON_GRAYLOG_HOST_BIND_IP` variable (the bind IP
is the same host, `192.168.11.10`, for every published port — no reason
to introduce a second IP variable) and adding one new required variable,
`FALCON_HERMES_INPUT_HOST_PORT` (proposed value: `12411`, matching the
input's own internal port — no renumbering), to `deploy/.env.example`
and the real `.env`, following the exact same `:?required` fail-loud
pattern every other port/host variable in this file already uses.
Result: `192.168.11.10:12411` reachable from `hermes_net` (once HERMES
is also given a route to the host, or more simply, since the host itself
routes between its own Docker networks, from any container that can
reach the dell-debian host's own LAN IP) — matching the existing
convention for port 9010 exactly, never `0.0.0.0`.

### Explicitly NOT proposed

The other 4 producer ports (12412-12415, for ARES/HELIOS/both TRON
identities) are **explicitly not proposed for publishing** in this work
order — each would need its own separate authorisation once that
specific producer's integration is actually being implemented, exactly
mirroring how PID-05 itself required its own dedicated authorisation for
HERMES. Publishing all 5 speculatively, before the other 4 producers
have any integration work authorised at all, would be exposing
attack surface with no corresponding requirement yet — precisely the
"do not expose all producer inputs" instruction this mandate's own
Section 10 (network and authentication) already gave.

### Acceptance criteria for the eventual HELM work order

- `docker compose -p falcon config` shows exactly one new published
  port (12411), bound to `192.168.11.10`, never `0.0.0.0`.
- `FALCON_HERMES_INPUT_HOST_PORT` fails loudly (compose refuses to start)
  if unset, matching every other required variable in this file.
- Ports 12412-12415 remain unpublished — confirmed via
  `docker port graylog-falcon` showing only 9010 and 12411.
- IRIS confirmed unaffected before and after (same checkpoint discipline
  as every other privileged change in this PID's history).
- A real mTLS connection from a HERMES-reachable network path to
  `192.168.11.10:12411` succeeds exactly as it already does from
  `falcon-net` directly — no behavioural change to the input itself,
  only its host reachability.

---

# Stage 1 implementation — hermes.signal_state / hermes.signal_engine (genuine PID-01 amendment)

**Status: this is real implementation, authorised by the Architect as
Stage 1 of a 4-stage plan — not another proposal.** Approved, final
names for Stage 1: evidence family `hermes.signal_state`, producer
component `hermes.signal_engine`. Everything below was built by the
FORGE Engineer and verified against this project's own actual test
suite before hand-off; live privileged execution (content-pack install,
the FTE test suite, the HELM handover actions) remains Rogue's/HELM's
own work, per the same split as every prior round of this PID.

## Registry additions

Read the live registries first, then extended precisely:

- **`registry/event_family_registry.v1.json`**: new live family
  `hermes.signal_state`, system `hermes`, `evidence_class:
  DETERMINISTIC_DERIVATION` (per this document's own earlier D.1
  proposal), one registered type (`indicator_regime_snapshot`), schema
  file `payloads/hermes/signal_state.v1.schema.json`,
  `required_payload_fields: ["signal_natural_key"]` only — every other
  searchable field is optional, per the mandate's own explicit
  instruction.
- **`registry/system_component_registry.v1.json`**: new component
  `hermes.signal_engine` added to the `hermes` system's component list.
- **`registry/field_registry.v1.json`**:
  - `instrument_id` and `timeframe`'s existing `allowed_families`
    extended to include `hermes.signal_state` — not renamed, not
    restructured, exactly as instructed.
  - `correlation_id`: no change (already universal/envelope-scope).
  - New field `signal_natural_key` (payload scope,
    `hermes.signal_state` only) — the schema's one required identity
    property; see the schema section below for why this does not
    contradict this document's own Section 9/D.6 finding.
  - New field `regime` (payload scope, `hermes.signal_state` only),
    enum `BULL_TREND`/`BEAR_TREND`/`TRANSITION`/`LOW_VOLATILITY` —
    **confirmed against the real HERMES source**
    (`signal_builder.py`'s `_determine_regime()`), not invented.
  - New field `session` (payload scope, `hermes.signal_state` only),
    enum `london`/`newyork`/`asia`/`overlap_ldn_ny`/`off_hours` —
    **confirmed against the real HERMES source**
    (`utils/trading_hours.py`'s `get_current_session()` and
    `utils/hermes_sessions_v1.py`'s `SESSION_NAMES`). Deliberately
    distinct from `ares.market_status.session_state`'s `session_id`/
    `session_state` (a session *lifecycle* enum —
    PRE_OPEN/OPEN/CLOSING/CLOSED/HOLIDAY — a different concept from this
    geographic/named session, exactly as this document's own earlier
    Section 4.2 finding already flagged; checked both existing fields'
    definitions directly before deciding a new field was genuinely
    needed, rather than guessing).
  - New field `signal_type` (payload scope, `hermes.signal_state`
    only), free string, **no enum imposed** — unlike `regime`/`session`,
    this delivery found no evidenced, closed HERMES-side value set to
    cite, and would rather leave it open than fabricate one.

**Verified, not assumed:** `python3 -m unittest discover -s tests -p
"test_*.py"` and `python3 -m tests.validator.cli` were both run against
these exact changes before hand-off — all 27 tests pass, including the
registry-consistency tests (every schema field registered, every
registered field used, family-scope enforcement, no duplicate field
names) and the full valid/invalid fixture corpus. One existing test
needed a one-line update as a direct, necessary consequence of adding a
28th live family: `tests/test_contracts.py`'s
`test_all_27_live_families_have_a_valid_fixture` had a hardcoded
`assertEqual(len(registered), 27)` — bumped to `28`. No other existing
test, fixture, or registry entry was touched.

## Payload schema — `schemas/payloads/hermes/signal_state.v1.schema.json`

Deliberately minimal, per the mandate's own "avoid separate schemas for
individual indicators" and "avoid interpreting the JSON's trading
content": validates only `signal_natural_key` (required) and the five
optional searchable properties above (`instrument_id`, `timeframe`,
`regime`, `session`, `signal_type`) — never any of HERMES's actual
indicator values (RSI, EMAs, ATR, Bollinger Bands, support/resistance
levels, etc.). Those live entirely in the full original HERMES JSON,
preserved separately via the binary-field pipeline mechanism below,
never structurally validated or interpreted by this schema at all.
`additionalProperties: false`, matching every other family's schema
convention exactly.

**`signal_natural_key` — the one required property, reasoned through
explicitly, not hand-waved:** this document's own Section 9/D.6 already
established that HERMES has no natural stable *event* identity — its
`(instrument, timeframe, timestamp)` SQL key is an upsert key, not an
event id, and D.6 proposed deriving a deterministic `falcon_event_id`
(UUID5) from exactly that natural key at publish time. `signal_natural_key`
does **not** contradict that finding — it is an honest, required,
producer-constructed string representation of that same real, already-
existing natural key (pattern: `instrument:timeframe:produced_at_utc`,
enforced via the schema's own regex), required so the payload always
carries at least one concrete anchor. It is explicitly not a claim that
HERMES has independent event identity; the eventual UUID5
`falcon_event_id` derivation (D.6) is expected to be computed *from*
this same field, not from a separately invented identity concept.

## New PID-01 fixtures

- **`tests/fixtures/valid/hermes_signal_state.json`** — realistic, not
  fabricated-looking: `producer_component_id: hermes.signal_engine`,
  `evidence_family: hermes.signal_state`, `evidence_type:
  indicator_regime_snapshot`, `evidence_class: DETERMINISTIC_DERIVATION`,
  and a payload shaped directly from this document's own earlier
  Section 8 trace of the real `signal_builder.py` output
  (`instrument_id: XAUUSD`, `timeframe: M5`, `regime: BULL_TREND`,
  `session: london`).
- **`tests/fixtures/invalid/missing_signal_natural_key.json`** —
  identical to the valid fixture except `payload.signal_natural_key` is
  missing entirely, with a `tests/fixtures/invalid/MANIFEST.json` entry
  explaining exactly why (the mandatory identity field, reasoned as
  above) — the *only* existing-file change in the entire `tests/
  fixtures/` tree is this one new `MANIFEST.json` entry; no existing
  fixture was touched.

Confirmed via the actual test suite run above that both fixtures behave
exactly as intended (the valid one accepted, the invalid one rejected
for precisely its documented reason) — not merely asserted.

## Content-pack / pipeline changes (rev 3 → rev 4)

Read the live content-pack JSON and the actual deployed rule source
directly before changing anything — confirmed, not assumed, that the
stage-1 "unknown producer system"/"unknown component"/"unregistered
evidence family" rules enumerate known values literally in their own
DSL source (a flat chain of `to_string(...) != "..."` comparisons), not
a runtime registry read.

- **`FALCON - flag unknown producer system`**: **no change needed** —
  `hermes` was already a recognised `producer_system_id` (HERMES has
  had registered families since PID-01's original closure); this rule
  only enumerates *systems*, not components or families, and was
  already correct.
- **`FALCON - flag unknown component`**: extended with one new line,
  `to_string($message.producer_component_id) != "hermes.signal_engine"`,
  in the same enumerated style as every existing entry.
- **`FALCON - flag unregistered evidence family`**: extended with one
  new line, `to_string($message.evidence_family) != "hermes.signal_state"`,
  same style.
- **Stage-2 routing: no new rule, no new stream — reused as-is, with
  reasoning stated explicitly, not assumed:** `hermes.signal_state` is
  a non-`.health` HERMES family. The existing `FALCON - route valid
  HERMES evidence` rule's condition is already generic
  (`producer_system_id == "hermes"` AND not `.health`), exactly the same
  way it already covers `hermes.market_fact`/`market_state`/
  `market_quality` without family-specific logic — `hermes.signal_state`
  is already correctly covered by this existing rule with **zero
  changes to it**. No new stream was needed or created.
- **New stage-0 rule, `FALCON - encode hermes signal raw payload to
  binary field`**: implements the proven `base64_encode()`+
  `remove_field()` pattern from the earlier "Isolated native large-
  payload proof — executed" section. Field-naming convention (permanent,
  documented here as the standing convention for this mechanism): a
  producer sends the full raw signal JSON as GELF additional field
  `_hermes_signal_raw_json` (Graylog strips the leading underscore on
  receipt, per PID-03's own already-documented convention, arriving as
  `hermes_signal_raw_json`); the new rule `base64_encode()`s it into
  `hermes_signal_original_payload` and `remove_field()`s the original —
  the `remove_field()` step is restated here as load-bearing, not
  optional, per Finding #1 above. **Scoped via `has_field(
  "hermes_signal_raw_json")` to only messages carrying that exact
  field** — never applied broadly to all messages or all producers, per
  the mandate's own explicit instruction.
- **The actual OpenSearch Custom Field Mapping (physical type
  `binary`) is deliberately NOT applied to the live `falcon-evidence_0`
  index set by this commit** — per the mandate's own instruction, that
  stays a documented, precise, not-yet-executed HELM action (see the
  new HELM handover brief below). Until it is applied,
  `hermes_signal_original_payload` is indexed as an ordinary keyword
  field, functionally correct up to 32,766 bytes, silently subject to
  the already-documented failure mode 2 above that — stated plainly,
  not left implicit.
- **Verified nothing existing is touched:** traced every stage-1 and
  stage-2 rule; the only two modified rules gained exactly one new
  enumerated `!=` line each, in the existing style, with every prior
  comparison byte-for-byte unchanged; every other producer's registered
  family/component/routing is completely untouched. **Rogue's own live
  install must NOT be run against the real `falcon-evidence_0` index
  set for its FIRST proof pass** — per the mandate's own instruction,
  test this rev-4 pack against a fresh isolated test index set first,
  exactly like the binary-field proof. Per PID-04's own established,
  proven precedent: because this revision *modifies* two existing rules'
  source (and the pipeline's own stage-list source), installing rev 4
  over an already-installed rev 3 will hit
  `DivergingEntityConfigurationException` unless those two rules plus
  the pipeline entity are deleted first — see
  `docs/operations/FALCON-PID04-PRIVILEGED-OPERATIONS-RUNBOOK.md` step 2
  for the exact, already-proven procedure; the same procedure applies
  here unchanged.

## Tests — `tests/fte/pid05_stage1_signal_state_tests.py`

A new FTE suite (not executed by this delivery — same credential/live-
execution boundary as every prior round) covering exactly the
mandate's checklist: valid signal accepted with correct family/producer
identity and instrument/timeframe searchable; optional regime/session
searchable when supplied; missing optional context accepted, never
rejected; the new missing-`signal_natural_key` fixture quarantined per
existing policy; a spoofed producer identity (legitimate HERMES mTLS
cert, false `producer_system_id` claim) quarantined with the false claim
preserved, reusing PID-04's own proven spoof-test pattern; the complete
original JSON preserved via the binary-field mechanism with an exact
base64 round-trip and confirmation the original field was actually
removed; 16/64/256/512 KiB payload behaviour as a **functional
regression check reusing `pid05_size_probe.py`'s already-proven
`build_realistic_payload_json()` builder directly** — explicitly not a
fresh capacity-research pass, per the mandate's own instruction; a
quick two-fixture regression check that `hermes.market_fact` and
`ares.calendar.event_state` remain functional; and a closing reminder
to confirm no IRIS impact (the script does not check this itself — a
manual `docker ps` checkpoint, same as every prior round).

**Isolated-test-first, by design, not by accident:** `--stream-name`
and `--quarantine-stream-name` both default to the real production
stream names, because that's what the committed pipeline actually
routes to — but neither is hardcoded internally, and the module's own
docstring instructs running this first against an isolated test
setup (mirroring the binary-field proof's disposable stream/pipeline/
index-set pattern) by overriding both arguments, before ever pointing
this suite at the real `falcon-evidence_0`.

**Self-tested locally before hand-off** (no network, matching this
project's own established discipline): imported the module directly
and exercised every pure-local code path — `build_signal_state_event()`
builds a correct payload with all five optional fields present, and
correctly produces exactly `{"signal_natural_key"}` as the only payload
key when every optional field is explicitly omitted; the new invalid
fixture loads correctly with `signal_natural_key` genuinely absent;
`sender.build_gelf_message()` correctly flattens the event, including
`_payload_json`, confirming the existing PID-03 un-flattening pipeline
rule will correctly reconstruct it. `python3 -m py_compile` clean on
this file and on `sender.py`/`pid05_size_probe.py` (reused, unmodified).

## HELM handover brief

`docs/operations/FALCON-PID05-STAGE1-HELM-HANDOVER-BRIEF.md` (new file,
declared in `DOCUMENTATION-MANIFEST.json`, file_count bumped to 52) —
kept as a **separate file under `docs/operations/`, not a section in
this document**, mirroring PID-04's own successful precedent
(`FALCON-PID04-PRIVILEGED-OPERATIONS-RUNBOOK.md`): an action-oriented,
precise, runbook-style document HELM can execute directly, distinct
from this file's own narrative discovery/reasoning record. Covers
exactly the mandate's four sub-sections: **connectivity** (the
restricted host-port-publishing `docker-compose.yml` change from the
prior round, with acceptance criteria); **storage** (the precise,
not-yet-applied Custom Field Mapping API call for
`hermes_signal_original_payload` → `binary` on the real evidence index
set, with the same verification method the DEV test already proved);
**credentials** (confirms HERMES's durable storage is done, and hands
over the now-near-certain loss of ARES/HELIOS/both TRON identities'
PID-04 keys as a standing action item, so it isn't discovered the hard
way a third and fourth time); and the **security finding**
(`falcon-net`'s unauthenticated OpenSearch, cross-referenced from this
document's own Section E.2, with MongoDB's confirmed-authenticated
status stated precisely so the finding isn't over-generalised). None of
these four actions has been executed by this delivery or by Rogue.
