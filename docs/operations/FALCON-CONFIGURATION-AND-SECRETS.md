# FALCON Configuration and Secrets

## Separation

-   container image = software;
-   Git-tracked config = non-secret behavioural definition;
-   external environment config = installation-specific values;
-   external secrets = credentials/private keys;
-   persistent volumes = state.

## DEV target layout

``` text
/srv/falcon/
  docker-compose.yaml
  config/
    templates/
    graylog/
    falcon/
  runtime/              # ignored where site-specific/sensitive
    config/
    secrets/
    data/
```

## Law

No configuration in code. No hidden defaults for required settings.
Missing required configuration fails loudly. No silent endpoint
fallback.

Secrets are mounted/read from files or an approved secret mechanism;
they are not committed, baked into images or included in FalconEvents.

## Compose

Compose references mounted config/secrets and persistent volumes.
Production-specific values must not require rebuilding application
images.
