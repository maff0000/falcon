# FALCON Decision Register --- Initial

1.  New repository: `maff0000/falcon`.
2.  DEV authority: `dell-debian:/srv/falcon`.
3.  Build engineering: Rogue/FORGE.
4.  Independent assurance: R2D2.
5.  Graylog is principal FALCON implementation technology and technical
    GUI, not semantic authority.
6.  New deployment uses Graylog Data Node rather than choosing
    self-managed OpenSearch by default.
7.  Exact container patch versions/digests are frozen in an immutable
    BOM before deployment.
8.  Configuration is external to immutable images; non-secret
    behavioural configuration is version controlled.
9.  Secrets are external/file-based.
10. Production is separately built and evidence-sized. retirement.
11. ARES is advisory today.
12. HERMES raw/deep historical corpus is not duplicated wholesale into
    FALCON.
13. HELIOS remains execution-blind.
14. HELIOS executable triggers are signed.
15. TRON owns execution truth and durable local dedupe.
16. FALCON outage/lag blocks new entries when FALCON is the
    trigger-discovery dependency, not existing position protection.
17. Strict registries; no arbitrary dynamic fields.
18. UTC-only canonical time.
19. Point-in-time knowability and append-preserving revisions are
    mandatory.
20. Every Docker/container resource owned specifically by FALCON carries
    the `-falcon` suffix (FF-CONTAINER-01, see
    docs/architecture/03-CONTAINER-NAMING.md) — binding acceptance
    criterion from PID-02 onward.
