# FALCON Git and Delivery Governance

## Repository

`maff0000/falcon`

## Rules

-   `main` is canonical.
-   Work occurs on bounded branches/worktrees.
-   No unrelated changes in a PID branch.
-   PR required for governed implementation changes.
-   clean working tree before/after handoff;
-   exact head SHA recorded in evidence;
-   CI must run on exact candidate SHA;
-   merge proof records PR, merge SHA, UTC and post-merge verification;
-   no secrets or production data;
-   `.gitignore` established before runtime secrets/data;
-   gitleaks/detect-secrets or equivalent secret scanning required.

Rogue/FORGE owns build engineering workflow. R2D2 audits independently.

A major session handover records state in Memory Fabric before agent
restart.
