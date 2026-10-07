# FALCON Decision Register --- Initial

1.  New repository: `maff0000/falcon`.
2.  DEV authority: `dell-debian:/srv/falcon`.
3.  Build engineering: Rogue/FORGE.
4.  Independent assurance: R2D2.
5.  Graylog is principal FALCON implementation technology and technical
    GUI, not semantic authority.
6.  New deployment uses Graylog Data Node rather than choosing
    self-managed OpenSearch by default.
7.  Exact container patch versions/digests are frozen in an immutable
    BOM before deployment.
8.  Configuration is external to immutable images; non-secret
    behavioural configuration is version controlled.
9.  Secrets are external/file-based.
10. Production is separately built and evidence-sized. retirement.
11. ARES is advisory today.
12. HERMES raw/deep historical corpus is not duplicated wholesale into
    FALCON.
13. HELIOS remains execution-blind.
14. HELIOS executable triggers are signed.
15. TRON owns execution truth and durable local dedupe.
16. FALCON outage/lag blocks new entries when FALCON is the
    trigger-discovery dependency, not existing position protection.
17. Strict registries; no arbitrary dynamic fields.
18. UTC-only canonical time.
19. Point-in-time knowability and append-preserving revisions are
    mandatory.
20. Every Docker/container resource owned specifically by FALCON carries
    the `-falcon` suffix (FF-CONTAINER-01, see
    docs/architecture/03-CONTAINER-NAMING.md) — binding acceptance
    criterion from PID-02 onward.
21. Architect ruling, 2026-09-28: the bespoke ingress architecture
    proposed during PID-03 preflight (a custom `ingress-falcon` service,
    a MongoDB durable acceptance ledger, and a custom ACK state machine
    with states such as `DURABLY_ACCEPTED`/`PROJECTED`) is withdrawn as
    unnecessary complexity. Do not build around Graylog. Use Graylog.
22. Graylog-native ingestion is authoritative going forward: producers
    construct their own conformant FalconEvents (per PID-01's existing
    universal envelope, field, event-family and component registries,
    used at their existing granularity, not collapsed into generic
    schemas) and deliver them through an authorised Graylog-native
    transport (inputs/pipelines/streams/journal). No bespoke FALCON
    ingress service, Mongo event-acceptance ledger, Redis, or custom ACK
    state machine exists merely to move messages into Graylog.
23. PID-01's producer templates/contracts remain the sole authority for
    message conformance; producers are responsible for constructing
    conformant events themselves. No central FALCON service exists to
    repair a malformed producer event — bad producers are corrected at
    source.
24. Ingress/network connection security (can a source connect/send to
    FALCON at all) is PID-04's domain, achieved via Graylog-native and
    network-native mechanisms (TLS, connection-level auth, source
    allow-listing, input-level restrictions), not PID-03's. PID-03 does
    not invent temporary bespoke authentication middleware.
25. HELIOS emits Trade Suggestions, not commands or execution
    instructions. A Trade Suggestion is structured, optionally signed
    FALCON evidence. FALCON records the signature as evidence; it does
    not itself decide whether TRON should trust it. This is a
    documentation/framing clarification of what the existing registered
    `helios.strategy_trigger` family means conceptually — it does not
    rename PID-01's closed registered family or fields.
26. TRON independently validates and admits or refuses each HELIOS Trade
    Suggestion (template, producer, signature, freshness, instrument,
    context, execution rules, risk/admission rules). Both outcomes —
    admitted-and-executed and refused-with-reason — become FALCON
    evidence, giving NEO a complete forensic record regardless of
    whether TRON chose to act.
27. PID-01's closed `registry/system_component_registry.v1.json`
    registers a component named `falcon.ingress_gateway` under the
    `falcon` system's component list. This name is a literal echo of
    the bespoke ingress architecture withdrawn by decision 21 —
    recorded here for the same reason as decision 25's
    `helios.strategy_trigger` note: it is a dormant, placeholder-governed
    registered name (no live producers or components exist yet per
    PID-01's own scope), not a live component, not implemented, and not
    to be built merely because the registry names it. PID-01 remains
    closed and is not amended by this decision. If a future PID
    genuinely needs a FALCON-owned component in this space, it must be
    justified on its own evidence, not treated as pre-authorised by this
    dormant name; if the name itself should be retired or renamed, that
    requires separate PID-01 amendment authority, not a
    documentation-only decision.
28. FALCON/Graylog is architected for many producers and many
    consumers, not a single TRON. Consumers (Graylog GUI, NEO, multiple
    simultaneous TRON instances, governed read-only AI trading agents,
    future consumers) access only the evidence/query surfaces they are
    authorised to read, via Graylog's own governed search/API — no
    custom query API is introduced merely because there may be many
    consumers.
29. FF-TRON-IDENTITY-01: every TRON trading entity/instance must
    possess a globally unique, stable governed trader identity
    (`tron_instance_id`) and a unique operational hostname
    (`tron_hostname`) — two distinct concepts, never conflated. These
    map onto PID-01's existing, closed `producer_component_id` (stable
    governed identity) and `producer_instance_id` (operational/runtime
    identity) envelope fields respectively — no PID-01 schema change or
    registry amendment is made by this decision. Restart/redeployment
    must not change `tron_instance_id`; cloning must not silently
    duplicate one; two simultaneously active TRON entities must never
    share one. Binding the authenticated producer connection to the
    claimed `tron_instance_id` is PID-04's responsibility, not
    implemented by this decision.
30. AI trading agents may be granted governed read-only access to
    FALCON/Graylog structured evidence (HERMES, ARES, HELIOS, TRON) as
    an ordinary consumer under decision 28 — a read-side capability
    only, not authority to publish or execute unless separately
    authorised, requiring no bespoke AI query service at this stage.
31. Decision 4 ("Independent assurance: R2D2") is superseded by the
    assurance model established during PID-01/PID-02 and reaffirmed
    here: FORGE Engineer -> fresh independent FORGE Auditor -> Rogue
    review/independent verification -> CI/runtime evidence -> Architect
    acceptance is the normal path for every PID. R2D2 is reserved for
    material architecture/security disputes, major system assurance
    points, production promotion, executable trust-boundary assurance,
    destructive recovery/restore, or when specifically requested by the
    Architect -- not mandatory/default assurance for routine PID
    closure. Decision 4's original text is preserved above, unedited,
    as the historical record of what was originally decided.

32. **Producer Contract Evolution Doctrine** (Architect ruling, following PID-05 HERMES and PID-06
    ARES integration experience): the FALCON envelope is stable and searchable; producer-owned
    evidence is extensible. FALCON owns the transport boundary, authenticated producer identity,
    universal event identity, classification, governed UTC timestamps, the stable searchable
    envelope, evidence preservation, and Graylog routing/searchability. FALCON does not own the
    detailed meaning or internal structure of producer-specific evidence. Adding a producer-owned
    payload field does not, by itself, require a FALCON contract revision; searchable-field
    promotion remains a deliberate, governed architectural decision, not automatic; FALCON must not
    recursively promote arbitrary producer JSON into the searchable envelope. Lossless
    producer-owned payload preservation is required; no particular encoding format (e.g.
    binary/base64) is intrinsically required where JSON string preservation demonstrably preserves
    the evidence (reaffirms the PID-06 lossless-payload ruling). No hindsight enrichment; no
    rewriting of historical evidence. Full doctrine, including the two-layer event model and its
    existing proven realisation (per-family searchable `payload` schema plus a separate
    producer-owned raw-preservation field), the HELIOS-specific non-freezing ruling for any future
    PID-07, and the forward-compatibility acceptance invariant for future implementation/testing:
    `docs/architecture/04-PRODUCER-CONTRACT-EVOLUTION-DOCTRINE.md`. This decision does not reopen or
    amend PID-01's closed registries/schemas.
