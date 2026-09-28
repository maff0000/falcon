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

1.  authenticate producer;
2.  validate universal envelope;
3.  validate registered family/schema/types;
4.  reject unregistered fields;
5.  enforce producer namespace;
6.  verify family-specific security (including HELIOS signature where
    FALCON validates it);
7.  assign FALCON ingestion UTC;
8.  route/index;
9.  acknowledge.

## DEV

DEV may use development certificates/keys but must exercise the same
trust boundaries. No architecture that only becomes secure in PROD is
acceptable.
