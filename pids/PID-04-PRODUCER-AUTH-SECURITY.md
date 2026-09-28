# PID-04 --- Graylog Producer Connection Security

**Slug:** `producer-auth`\
**Owner:** Rogue/FORGE\
**Assurance:** R2D2\
**Ops authority where applicable:** HELM\
**Time:** UTC only

## Purpose

Select and implement one common, secure producer-connection model for
HERMES, ARES, HELIOS and TRON, using Graylog-native and network-native
mechanisms rather than a bespoke FALCON authentication gateway. This PID
answers only one question: can this source connect/send to FALCON at
all? It does not decide whether a message's content is well-formed
(PID-01's contracts) or whether a consumer should act on it (the
consumer's own admission logic).

## Dependencies

PID-03.

## Scope / deliverables

-   TLS, terminated at the Graylog input (or an explicitly documented
    equivalent) rather than a custom FALCON gateway;
-   producer credentials, using Graylog's own input-level authentication
    and/or connection-level auth where Graylog provides it, custom only
    where genuinely necessary and evidenced;
-   rotation/revocation procedure;
-   namespace ACL, enforced via Graylog-native and network-native
    restrictions (source allow-listing, input-level restrictions) where
    Graylog can express it;
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
