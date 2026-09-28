# FALCON Graylog Architecture

## Role

Graylog is FALCON's principal ingestion/search infrastructure and native
technical GUI. It is replaceable behind FALCON contracts and owns no
trading authority.

## DEV stack

Current official Graylog 7.1 documentation describes the container stack
as: - Graylog; - Graylog Data Node; - MongoDB.

Data Node is preferred over self-managed OpenSearch for the new
deployment.

## Immutable BOM law

No `latest`, floating major/minor tag or automatic updater.

Before first deployment, PID-02 must record: - exact Graylog image tag +
digest; - exact Data Node image tag + digest; - exact MongoDB image
tag + digest; - Docker/Compose versions; - compatibility evidence; - BOM
approval UTC.

The approved BOM is committed. Upgrades require a new governed BOM
change and full compatibility/restore/contract proof.

## Host prerequisite

`vm.max_map_count` must be at least 262144 for the Data Node stack. Host
readiness is HELM-owned and evidenced.

## Configuration

Version-controlled non-secret Graylog configuration is mounted into
containers. Environment/site configuration and secrets remain external
to immutable images.

## Persistent state

Persistent volumes are explicit for Graylog journal/data, Data
Node/search data and MongoDB metadata. Destructive DEV rebuild
procedures must distinguish disposable state from evidence intentionally
retained for tests.
