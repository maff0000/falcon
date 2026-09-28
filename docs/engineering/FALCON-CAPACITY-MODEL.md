# FALCON Capacity Model

## Purpose

Use measured DEV/MVP behaviour to size a separate production
environment.

## Measure

-   average/peak events per second;
-   burst profile around scheduled events;
-   average/p95/p99 event size;
-   daily indexed bytes;
-   index expansion factor;
-   journal/backlog growth;
-   CPU;
-   Graylog JVM memory;
-   Data Node/OpenSearch heap and memory;
-   MongoDB memory/storage;
-   disk IOPS/latency;
-   query concurrency and p95/p99 latency;
-   TRON discovery latency;
-   NEO research query load;
-   retention by evidence class;
-   backup size/duration;
-   restore duration.

## Sizing output

Produce: - minimum DEV baseline; - MVP observed load; - production
nominal load; - peak/event-day load; - 12-month growth assumption; -
headroom target; - single-node vs multi-node recommendation; -
storage/IOPS requirement; - memory/CPU requirement; - network
requirement; - backup capacity; - RPO/RTO implications.

No production server size is guessed before measurements exist.
