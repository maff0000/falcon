# HELIOS Trigger Signing

## Purpose

A Graylog/FALCON search hit is not, by itself, an executable
instruction. HELIOS triggers must be independently authenticatable.

## Algorithm

Target: Ed25519, subject to implementation proof.

## Canonical signed content

The signature covers a deterministic canonical representation of all
execution-relevant trigger semantics, including trigger identity,
strategy identity/version, instrument, direction/action, timeframe,
validity window, semantic levels, input snapshot/hash and score
semantics where present.

## Key metadata

Trigger carries `signing_key_id` and `signature`, never private key
material.

## Verification

TRON verifies: - key ID is trusted and not revoked; - signature is
valid; - canonical representation matches; - trigger is within validity
window; - trigger ID has not already reached a terminal local outcome.

Key generation, storage, rotation and revocation are operationally
documented and secret-file based.
