# FALCON System and Component Identity Registry

## Purpose

Prevent naming collisions and free-text causal identities.

## System IDs

-   `hermes`
-   `ares`
-   `helios`
-   `falcon`
-   `tron`
-   `neo`

These IDs are machine identities, not display labels.

## Component IDs

Each producer must register stable component IDs before publication.
Component identity must identify the semantic producer, not an ephemeral
Docker container name.

`producer_instance_id` may identify a runtime instance separately.

## Prohibited

-   ambiguous free-text names;
-   Graylog stream/index IDs as producer identity;
-   hostnames as the sole semantic component identity.
