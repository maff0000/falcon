# Deployment Assets

This directory will hold Docker Compose and immutable BOM assets created
by the deployment PIDs.

Rules: - no floating image tags; - exact image digests recorded; - no
secrets committed; - environment-specific values external; - persistent
volumes explicit; - DEV and PROD configuration separated; - Graylog/Data
Node/MongoDB compatibility verified before BOM approval.
