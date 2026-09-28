# PID-04 --- Producer Authentication and Namespace Security

**Slug:** `producer-auth`\
**Owner:** Rogue/FORGE\
**Assurance:** R2D2\
**Ops authority where applicable:** HELM\
**Time:** UTC only

## Purpose

Select and implement one common secure producer-authentication model.

## Dependencies

PID-03.

## Scope / deliverables

-   TLS;
-   producer credentials;
-   rotation/revocation procedure;
-   namespace ACL;
-   secret-file integration;
-   operator vs producer access separation;
-   security event/alerting.

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

-   valid producer accepted;
-   wrong/revoked credential rejected;
-   producer cannot write another namespace;
-   secrets absent from Git/log/events;
-   rotation without semantic data loss.

## Definition of Done

Authentication and namespace isolation are running and independently
audited.

A PID is not complete until its behaviour is running and proven, not
merely coded or documented.
