# HELIOS → FALCON Contract

## Authority

HELIOS owns deterministic strategy evaluation, strategy state, chain
state and semantic Trade Suggestions. HELIOS is execution-blind.

## Evaluation evidence

`helios.strategy_evaluated` preserves: - evaluation ID; - strategy
ID/version; - semantic fingerprint; - parameter-set identity; - input
snapshot ID/hash/references; - instrument/timeframe; - state
before/after; - conditions satisfied/failed; - quality; -
produced/available UTC.

Declines, blocks and near-misses must be explainable, not only
successful fires.

## Trade Suggestion evidence

HELIOS's Trade Suggestion (the registered `helios.strategy_trigger`
family) is structured, optionally signed evidence for TRON to
independently evaluate — it is not a command or an execution
instruction FALCON or TRON must obey. Required semantics include: -
trigger/evaluation/strategy identities; - strategy
version/fingerprint/parameter set; - chain identity where applicable; -
instrument; - direction/action type; - timeframe; - trigger UTC; -
valid-from/valid-until; - exact input snapshot/hash; - reference
price/fact; - semantic SL/TP/invalidation/target where strategy defines
them; - optional governed score + `score_definition_id`; - signing key
ID; - signature.

No generic universal `confidence`.

## Execution blindness

HELIOS may define semantic invalidation/target intent. TRON owns broker
symbol, rounding, minimum stop distance, order type, quantity, hard risk
and actual execution.

## Signing

A Trade Suggestion requires a FALCON-approved canonical signing
representation and Ed25519 signature. FALCON preserves the signature as
recorded evidence; it does not itself decide whether TRON should trust
it. TRON verifies authenticity independently of Graylog search success
and independently decides whether to act on it.
