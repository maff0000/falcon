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

1.  **source/network connection security** — can this source connect/
    send to FALCON at all? (Graylog/network-native mechanisms; PID-04's
    domain);
2.  **producer/message contract** — does the message conform to its
    registered PID-01 template (universal envelope + typed family
    schema, registered fields only)? (the producer constructs this
    itself before it ever leaves the producer);
3.  **Graylog ingestion/processing** — native inputs, pipelines,
    streams and journal receive and route the message;
4.  **evidence storage/search** — Data Node/indexes persist the message;
    the event now exists as recorded FALCON evidence;
5.  **downstream consumer trust/admission** — does *this* consumer (for
    example TRON) choose to act on the message? This is the consuming
    system's own governed admission logic, not a FALCON-wide
    acknowledgement state.

A message existing in FALCON (layers 1–4 passed) means the event exists
as evidence. It does not by itself mean any particular consumer trusts
or acts on it — that is layer 5, decided independently by each
consumer.

## DEV

DEV may use development certificates/keys but must exercise the same
trust boundaries. No architecture that only becomes secure in PROD is
acceptable.
