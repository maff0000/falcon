# PID-02 --- Immutable Graylog DEV Stack

**Slug:** `graylog-dev-stack`\
**Owner:** Rogue/FORGE\
**Assurance:** R2D2\
**Ops authority where applicable:** HELM\
**Time:** UTC only

## Purpose

Deploy the first reproducible Dockerised FALCON infrastructure on
dell-debian.

## Dependencies

PID-00.

## Scope / deliverables

-   verify official Graylog compatibility;
-   freeze exact Graylog/Data Node/MongoDB image tags and SHA256 digests
    in BOM;
-   Docker Compose stack;
-   external mounted non-secret config;
-   external secret files;
-   persistent volumes;
-   healthchecks;
-   host prerequisite check including `vm.max_map_count >= 262144`;
-   no automatic updater/floating tags.

## Mandatory engineering law

-   no config in code;
-   no hidden defaults/fallbacks;
-   required missing config fails loudly;
-   no secrets in Git/images/events;
-   container-compatible;
-   UTC-aware canonical timestamps only;
-   bounded branch/PR with clean Git hygiene;
-   exact SHA/runtime evidence;
-   documentation updated with implementation;

## Required tests/evidence

-   cold start;
-   restart persistence;
-   health checks;
-   exact image digest proof;
-   config mount proof;
-   secret non-leak proof;
-   host reboot recovery plan;
-   Graylog GUI reachable on governed DEV interface.

## Definition of Done

Exact immutable stack runs on dell-debian and can be destroyed/recreated
from Git + external config/secrets.

A PID is not complete until its behaviour is running and proven, not
merely coded or documented.
