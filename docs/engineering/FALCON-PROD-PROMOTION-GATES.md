# FALCON DEV → PROD Promotion Gates

Production is a new controlled deployment, not DEV copied to another
host.

Required gates: 1. universal contract frozen at approved version; 2.
registries machine-readable and tested; 3. HERMES/ARES/HELIOS/TRON
integrations green; 4. paper TRON trigger discovery/execution green; 5.
signature/authentication proven; 6. point-in-time reconstruction proven;
7. outage/retry/replay/dead-letter proven; 8. backup/restore proven; 9.
capacity report complete; 10. immutable BOM complete; 11. security
review complete; 12. R2D2 exact-SHA/runtime audit green; 13. HELM
production runbook complete; 14. rollback/recovery plan complete; 15.
Matt final acceptance.

Production configuration and secrets are independently provisioned.
