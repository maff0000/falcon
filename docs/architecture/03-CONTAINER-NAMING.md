# FALCON Container and Docker Resource Naming

## FF-CONTAINER-01 — FALCON Resource Naming

> Every container and Docker resource owned specifically by FALCON MUST
> carry the `-falcon` suffix, or an explicitly documented equivalent
> where platform syntax prevents that exact form, so FALCON runtime
> resources remain immediately distinguishable from other THE GOAL
> services.

Mandatory naming convention:

```text
<component>-falcon
```

Examples:

```text
graylog-falcon
datanode-falcon
mongodb-falcon
```

Future FALCON-specific supporting services follow the same rule:
`<service>-falcon`.

## Applies to

At minimum:

- Docker container names;
- Docker Compose service names where practical and unambiguous;
- FALCON-specific Docker networks;
- FALCON-specific Docker volumes;
- FALCON-owned images built locally;
- FALCON-specific supporting containers;
- monitoring/backup/helper containers created specifically for FALCON.

Where Docker naming syntax or external tooling requires a variation, the
resulting resource must still contain an explicit `falcon` identifier
and the exception must be documented at the point it is introduced.

## Purpose

A host may contain infrastructure belonging to multiple THE GOAL
services. An operator must be able to inspect `docker ps`, `docker
network ls`, `docker volume ls` and immediately distinguish FALCON
resources from HERMES, ARES, HELIOS, TRON or unrelated host
infrastructure.

Generic names such as `graylog`, `mongodb`, `datanode`, `database`,
`backend`, `worker` are **not acceptable** for FALCON-owned runtime
resources. Use `graylog-falcon`, `mongodb-falcon`, `datanode-falcon`
instead.

## Isolation

Naming does not replace actual isolation. FALCON must still have its own
configuration, secrets, persistent state, networks as appropriate,
volumes, access controls, lifecycle and backup/restore boundaries.

A resource belonging to another application must never be renamed or
implicitly treated as a FALCON resource simply because FALCON consumes
information from that application.

## Status

Architect ruling, 2026-09-28. Binding acceptance criterion for **PID-02
— Immutable Graylog DEV Stack** onward; PID-00 and PID-01 introduce no
Docker resources and are unaffected. Recorded here and in
`docs/governance/FALCON-DECISION-REGISTER.md` (decision 20).
