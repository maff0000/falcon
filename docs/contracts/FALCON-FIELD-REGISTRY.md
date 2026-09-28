# FALCON Field Registry

## Law

The registry is the single authority for FALCON-visible field names and
types. Producers may not create arbitrary dynamic fields or synonyms.

Each registered field records: - canonical name; - data type; - semantic
definition; - required/optional; - allowed event families; - enum
values; - unit/precision; - authoritative producer; -
temporal/provenance meaning; - retention class; - sensitivity class; -
version introduced; - deprecation/supersession where applicable.

## Naming

Use stable semantic names, not vendor or UI names. Do not create
`strategy`, `strategy_name`, `strat` for one concept. Graylog internal
IDs are forbidden from domain contracts.

## Numbers

For audit-sensitive prices/quantities/levels, authoritative
representation is decimal string with defined precision semantics.
Optional numeric mirror fields may exist for aggregation/search but are
not the forensic authority.

## Change control

Registry change requires: 1. architecture reason; 2. schema impact; 3.
compatibility assessment; 4. tests; 5. R2D2 review when
contract-affecting; 6. versioned merge.
