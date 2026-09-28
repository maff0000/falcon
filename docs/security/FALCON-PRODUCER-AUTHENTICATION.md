# FALCON Producer Authentication

## Required properties

The final ingress mechanism must provide: - TLS; - stable producer
identity; - namespace isolation; - revocation/rotation; - least
privilege; - machine-readable auth failure; - no secret in event
payload.

## Selection gate

Rogue/FORGE must not invent a different authentication scheme per
producer. PID-04 selects and proves one common FALCON producer-auth
pattern suitable for HERMES, ARES, HELIOS and TRON.

The choice between mTLS and another strongly authenticated transport
remains an implementation decision until the ingress prototype is
proven. The chosen mechanism must be documented and R2D2-audited before
producer onboarding.
