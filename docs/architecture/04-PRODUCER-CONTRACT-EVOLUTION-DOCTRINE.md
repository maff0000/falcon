# FALCON Producer Contract Evolution Doctrine

**Status:** Binding architectural doctrine, FALCON-wide. Recorded by Central Architecture following the
PID-05 (HERMES) and PID-06 (ARES) integration experience. See `docs/governance/FALCON-DECISION-REGISTER.md`
decision 32 for the binding record; this document is the detailed doctrine that decision references.

**Applies to:** every current and future FALCON producer (HERMES, ARES, HELIOS, TRON, and any later
producer), and to every PID/WO that integrates one.

## Binding principle

> **The FALCON envelope is stable and searchable. Producer-owned evidence is extensible.**

FALCON must not require every external application to freeze its internal evidence model before it can
publish evidence. HERMES, ARES, HELIOS, TRON, and future producers remain owners of their domain semantics.

FALCON owns: the evidence transport boundary; authenticated producer identity; universal event identity;
event classification; governed UTC event timestamps; the stable searchable envelope; evidence preservation;
Graylog routing/searchability; security and ingestion validity.

FALCON does **not** own the detailed meaning or internal structure of producer-specific trading/news/risk/
execution evidence.

## 1. Two-layer event model

**Layer A — stable FALCON searchable envelope.** A deliberately small, stable set of fields required for
identification, provenance, authentication, classification, chronology, correlation, and useful cross-system
searching. The universal envelope fields (`docs/contracts/FALCON-UNIVERSAL-EVENT-CONTRACT.md`) are mandatory
globally. Per-family promoted searchable dimensions (e.g. `instrument_id`, `market_state` for
`ares.market_status.session_state`) are registered per event family (PID-01's field/event-family registries)
and are mandatory only for that family, by that family's own registered schema — not universally mandatory
across all producers.

**Layer B — producer-owned evidence payload.** An extensibility boundary. It may contain producer-specific
fields, nested structures, arrays, experimental fields, instrument-specific evidence, strategy-specific
evidence, diagnostic information, and future fields unknown to FALCON today. FALCON must preserve this
evidence losslessly and must not maintain a manual allow-list that silently discards unknown producer
fields.

**How this is realised today (existing, proven mechanism — not new architecture):** a FALCON event carries
two separate JSON bodies over GELF: (1) the small, per-family `payload` object, validated against that
family's registered JSON Schema (`schemas/payloads/<family>.v1.schema.json`, `additionalProperties: false`)
— this is the Layer A searchable-promotion contract, and (2) a separate, family-named raw-preservation field
(proven in production as `ares_market_status_raw_json` in ARES's Stage 2B evidence publisher,
`app/src/ares/marketstatus/evidence.py`) carrying the complete, generically-serialized producer row
(`dataclasses.asdict()` plus any extra instance attributes — not an allow-list), independent of the small
schema's `additionalProperties: false` restriction. The PID-06 runtime acceptance event
(`docs/operations/FALCON-PID06-RUNTIME-ACCEPTANCE-EVIDENCE.md` §3) proved this mechanism losslessly
preserves the full producer object, including an unknown nested future field, with zero promotion into the
searchable envelope. This doctrine formalises the pattern; it does not introduce a new mechanism. Future
producer integrations should follow the same pattern (a small registered `payload` schema for deliberately
promoted fields, plus a separate family-named raw-preservation field for the complete producer-owned
evidence) unless a future PID has a specific reason to do otherwise.

## 2. Optional means optional

If an optional field does not exist: **omit it.** Do not fabricate it, infer it, default it, reject the
event because it is absent, or substitute another semantic concept. Only agreed compulsory fields (the
universal envelope's mandatory fields, and a given family's own registered required `payload` fields) may
cause rejection when missing or invalid. Unknown producer-specific context remains producer-owned and opaque
to FALCON unless deliberately promoted per §4.

## 3. Forward compatibility

> Adding a producer-owned payload field does not, by itself, require a FALCON contract revision.

If HELIOS later adds chain strength, near-miss evidence, confirmation timeframes, market-structure evidence,
rejection reasons, experimental scores, or strategy diagnostics — or HERMES, ARES, or TRON add equivalent
future evidence — FALCON must be capable of preserving those additions (via the raw-preservation field, §1)
without requiring corresponding FALCON schema work. A FALCON contract revision is required only when a
*searchable* (Layer A) field changes, per §4 and §6.

## 4. Searchable field promotion

Producer fields become first-class searchable FALCON fields only deliberately. Promotion should occur when
there is demonstrated value such as: regular trader queries; cross-producer correlation; NEO/R2D2 analysis;
operational filtering; TRON discovery requirements; durable reporting requirements. Promotion is **a
governed architectural decision** (a PID/amendment + registry change, per PID-01's existing change-control
law) — it is not automatically triggered because a producer added a field. This prevents uncontrolled
Graylog field/index growth.

## 5. No automatic field explosion

FALCON must not recursively promote arbitrary producer JSON into hundreds or thousands of Graylog indexed
fields. Rich producer evidence remains within the producer-owned raw-preservation mechanism (§1) unless
particular fields are deliberately promoted (§4). This protects Graylog field cardinality, index stability,
query usability, and contract stability.

## 6. Producer semantic ownership

FALCON records producer claims as authenticated evidence; it does not independently reinterpret them.
Examples: ARES owns what `OPEN`/`CLOSED`/`UNKNOWN` mean for market status. HERMES owns the semantics of its
signals and derived market evidence. HELIOS owns the semantics of strategy evaluation, strategy state,
strategy firing, near-miss, alignment, chain evidence, and strategy-specific reasoning. TRON owns execution
decision, admission/refusal, order lifecycle, and execution/risk semantics.

## 7. Schema versioning (lightweight)

A schema/contract version represents a meaningful compatibility or semantic boundary. A producer adding
another evidence field does **not necessarily** require a new version. Version changes are appropriate where,
for example: required envelope semantics change; an existing field changes meaning incompatibly; identity
semantics change; or consumers can no longer safely interpret the previous representation as equivalent. This
doctrine does not introduce migration machinery.

## 8. Lossless preservation (carries forward the PID-06 Architect ruling)

> FALCON requires lossless producer-owned payload preservation, not any particular encoding format.

JSON string preservation is acceptable where it demonstrably preserves the producer evidence (proven, §1).
Binary/base64 encoding is not intrinsically required. The preservation mechanism must allow future
unknown/nested producer fields to survive without FALCON contract changes.

## 9. No hindsight enrichment

FALCON must not retrospectively invent information that was not supplied at event time. Do not infer
session, regime, bias, volatility, timeframe, strategy state, market state, or other producer semantics
after the fact merely to fill optional searchable fields. Evidence must remain historically truthful.

## 10. Historical compatibility

Do not rewrite historical HERMES or ARES events. Existing historical evidence remains valid according to the
contract/version under which it was produced. Future producer evolution must not require mutation of old
evidence merely for structural uniformity.

## 11. Forward-compatibility acceptance invariant (for future implementation/testing)

For producer event families using the extensible payload model, deterministic tests should prove that an
unknown future producer-owned field, including nested content where applicable: (1) survives serialization;
(2) survives FALCON ingestion/preservation; (3) retains its value/structure; (4) does not cause event
rejection merely because it is unknown; (5) is not automatically promoted into the searchable envelope. This
becomes a reusable acceptance criterion for future producer integrations. Fixtures/unit/integration evidence
is appropriate; do not fabricate live production fields merely to prove this.

## 12. HELIOS-specific ruling (for PID-07)

**HELIOS is not mature enough for FALCON to freeze a detailed HELIOS evidence schema.** Any future PID-07
work must not begin by designing a comprehensive fixed HELIOS field definition. The initial objective for any
such PID is to discover the smallest currently stable surface necessary to authenticate, identify, preserve,
correlate, and usefully search HELIOS evidence — everything else remains producer-owned payload (§1 Layer B)
until demonstrated otherwise, per §4's governed-promotion discipline. This is a specific application of §§1-7
above to HELIOS; it is not a separate rule.

## Scope note

This document does not modify the PID-01 JSON Schema engine, registries, validator implementation, or any
already-registered family's schema. It states the architectural doctrine under which existing mechanisms
(verified in §1) already operate and under which future family registrations and promotions should be
evaluated. No PID-01 registry is reopened or amended by this document.
