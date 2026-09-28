# Universal FalconEvent Contract

## Design

A FalconEvent consists of: 1. a small mandatory universal envelope; 2.
one registered typed payload.

## Proposed v1 envelope

  --------------------------------------------------------------------------
  Field                      Type                Rule
  -------------------------- ------------------- ---------------------------
  `falcon_event_id`          string/UUID         globally unique immutable
                                                 evidence identity; stable
                                                 across retry

  `envelope_version`         string              universal contract version

  `payload_schema_version`   string              typed payload version

  `producer_system_id`       string              registered machine system
                                                 identity

  `producer_component_id`    string              registered component
                                                 identity

  `producer_instance_id`     string?             runtime instance when
                                                 useful

  `evidence_family`          string              registered family

  `evidence_type`            string              registered type

  `evidence_class`           enum                SOURCE_FACT,
                                                 NORMALIZED_FACT,
                                                 DETERMINISTIC_DERIVATION,
                                                 MODEL_ASSESSMENT,
                                                 DOMAIN_DECISION,
                                                 STATE_SNAPSHOT,
                                                 SOURCE_QUALITY,
                                                 OPERATIONAL_HEALTH,
                                                 EXECUTION

  `produced_at_utc`          RFC3339 UTC         producer created evidence

  `occurred_at_utc`          RFC3339 UTC?        real-world occurrence where
                                                 applicable

  `observed_at_utc`          RFC3339 UTC?        producer observation

  `available_at_utc`         RFC3339 UTC?        first usable by producer
                                                 decision logic

  `effective_from_utc`       RFC3339 UTC?        state/decision effective
                                                 time

  `effective_until_utc`      RFC3339 UTC?        expiry/end

  `falcon_ingested_at_utc`   RFC3339 UTC         FALCON-owned, never
                                                 producer supplied as
                                                 authority

  `subject_id`               string              governed subject

  `instrument_ids`           array\[string\]     canonical instrument
                                                 applicability

  `correlation_id`           string?             logical
                                                 investigation/thread
                                                 grouping

  `causation_id`             string?             immediate causal evidence
                                                 ID

  `revision_id`              string?             family revision identity

  `revision_sequence`        integer?            ordered revision where
                                                 meaningful

  `supersedes_event_id`      string?             append-preserving
                                                 supersession

  `provenance_ref`           string/object       governed producer
                                                 provenance reference

  `quality_state`            string?             registered family semantics

  `config_digest`            string?             truth-affecting
                                                 configuration identity

  `build_id`                 string?             Git SHA/build provenance

  `payload_hash`             string              integrity hash; not sole
                                                 event identity

  `retention_class`          string              FALCON registry value

  `sensitivity_class`        string              FALCON registry value

  `payload`                  object              registered typed schema
                                                 only
  --------------------------------------------------------------------------

## Temporal law

All canonical times are timezone-aware UTC. No naive datetime. FALCON
ingestion time cannot substitute for producer knowledge/availability
time.

## Identity law

Payload hash is integrity data, not event identity. Legitimate
heartbeats may have identical payload content but distinct immutable
evidence IDs.

## Revision law

Corrections/revisions append. Prior evidence remains searchable and
point-in-time queries exclude information not yet knowable.

## Unknown values

Missing evidence stays missing. Never fabricate provenance, timestamps,
confidence or causation.
