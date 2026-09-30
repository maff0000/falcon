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
