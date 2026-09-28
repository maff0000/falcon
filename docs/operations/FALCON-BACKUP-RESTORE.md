# FALCON Backup and Restore

## Objective

A backup is not accepted until restore is proven.

## Scope

Document and test: - MongoDB metadata/config; - Data Node/search
evidence; - Graylog configuration/exportable content; - FALCON
registries/schemas from Git; - secrets/key recovery process without
committing secrets; - producer replay boundary; - TRON local journal
independence.

## DEV proof

PID-12 must: 1. ingest deterministic fixture corpus; 2. take backup; 3.
destroy/recreate relevant containers/state; 4. restore; 5. prove event
counts/hashes/query results; 6. prove trigger history and causal
reconstruction; 7. record RTO/RPO observations.

## PROD

Production backup frequency and topology are derived from business
RPO/RTO plus measured dataset size and restore duration.
