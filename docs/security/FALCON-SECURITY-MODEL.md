# FALCON Security Model

## Trust boundaries

Every producer is independently authenticated and namespace restricted.
ARES cannot publish HELIOS events; TRON cannot publish HERMES facts.

## Requirements

-   encrypted transport;
-   least privilege;
-   dedicated producer identity;
-   credential rotation;
-   no secrets in FalconEvents;
-   no secrets in Git or images;
-   secret files/mounted secret mechanisms;
-   explicit ingress allow-list;
-   schema validation before storage;
-   security violations generate operational evidence/alerts;
-   operator GUI access separated from producer credentials.

## Validation order

There is no single bespoke FALCON application process that performs
these steps synchronously in one request/response. Instead, five
distinct layers apply, each with its own owner and its own question:

1.  **source is authorised to connect** — can this source connect/send
    to FALCON at all? (Graylog/network-native mechanisms; PID-04's
    domain);
2.  **message is received** — Graylog's native input/pipeline/journal
    receives the message. Receipt is not itself a conformance or trust
    judgement;
3.  **message/template conformance is evaluated** — does the message
    conform to its registered PID-01 template (universal envelope +
    typed family schema, registered fields only)? The producer
    constructs this itself before the message ever leaves the
    producer; PID-03 proves exactly what the pinned Graylog stack can
    and cannot evaluate natively;
4.  **message is recorded/routed as appropriate** — conformant evidence
    is indexed as FALCON evidence. For non-conformant messages, PID-03
    must empirically prove the pinned Graylog 7.1.9 behaviour and use
    whichever the native stack actually supports — rejection,
    quarantine/separate routing, or visible classification/alerting as
    invalid evidence. Do not introduce bespoke middleware merely to
    force a theoretical universal "reject" outcome;
5.  **downstream consumer trust/admission** — does *this* consumer (for
    example TRON) independently choose to act on the message? This is
    the consuming system's own governed admission logic, not a
    FALCON-wide acknowledgement state.

Being recorded/routed by FALCON (layers 1–4) means the message exists —
it does **not** mean the message is a semantically valid FalconEvent,
and it does not mean any particular consumer trusts or acts on it.
Invalid or untrusted evidence does not necessarily mean invisible: where
Graylog cannot natively reject a malformed class without unnecessary
middleware, deterministic classification, separate routing, flagging or
alerting is an acceptable way to keep that evidence visible and marked
as untrusted, rather than letting it silently become trusted canonical
evidence. Whether recorded evidence is valid, current and trustworthy
enough to act on is decided independently at layer 5 by each consumer —
never assumed from the fact of storage alone.

Producer delivery retries preserve canonical event identity where
applicable. PID-03 will empirically characterise and prove the
selected Graylog-native ingestion/replay behaviour. FALCON currently
provides no separate bespoke application-level acceptance or
idempotency service. Consumers requiring action-level deduplication,
including TRON, retain their own governed durable dedupe.

## DEV

DEV may use development certificates/keys but must exercise the same
trust boundaries. No architecture that only becomes secure in PROD is
acceptable.
