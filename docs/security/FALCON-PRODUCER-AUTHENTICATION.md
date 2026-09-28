# FALCON Producer Authentication

## Required properties

The chosen Graylog-native/network-native producer connection mechanism
must provide: - TLS; - stable producer identity; - namespace isolation;
- revocation/rotation; - least privilege; - machine-readable auth
failure; - no secret in event payload.

## Selection gate

Rogue/FORGE must not invent a different authentication scheme per
producer, and must not invent a bespoke FALCON authentication gateway.
PID-04 selects and proves one common producer-connection pattern,
built on Graylog-native and network-native mechanisms (TLS,
connection-level auth, source allow-listing, Graylog's own input-level
restrictions), suitable for HERMES, ARES, HELIOS and TRON. Custom
mechanisms are used only where genuinely necessary and evidenced, not by
default.

The choice between mTLS and another strongly authenticated transport
remains an implementation decision until proven against the pinned
Graylog stack. The chosen mechanism must be documented and R2D2-audited
before producer onboarding.
