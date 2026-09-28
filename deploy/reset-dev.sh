#!/usr/bin/env bash
# =============================================================================
# FALCON PID-02 — deliberate DEV-reset mechanism
#
# Destroys and recreates the FALCON Graylog DEV stack from scratch, wiping
# FALCON's own named volumes only:
#
#   graylog-falcon-journal
#   datanode-falcon-opensearch-data
#   mongodb-falcon-data
#   mongodb-falcon-config
#
# It is STRUCTURALLY INCAPABLE of touching the unrelated Project IRIS
# Graylog stack: that stack uses different container names (graylog,
# graylog-mongo, graylog-elasticsearch), a different compose project
# (no -p flag / default project name there), a different network
# (graylog_default vs falcon-net) and entirely different volume names.
# This script only ever names resources with the literal "falcon" suffix
# from the list above and the "-p falcon" compose project scope — it never
# takes a resource name as input and never uses a wildcard/prefix match
# that could accidentally widen to another project's resources.
#
# Requires an unmistakable confirmation flag. Safe to inspect (--dry-run).
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

FALCON_VOLUMES=(
  graylog-falcon-journal
  datanode-falcon-opensearch-data
  mongodb-falcon-data
  mongodb-falcon-config
)

usage() {
  cat >&2 <<'EOF'
Usage:
  ./reset-dev.sh --dry-run
      Show exactly what would be destroyed, change nothing.

  ./reset-dev.sh --i-understand-this-destroys-falcon-dev-data
      Actually stop the falcon compose project, remove ONLY the FALCON-named
      volumes listed in this script, then bring the stack back up clean.
EOF
  exit 1
}

[[ $# -eq 1 ]] || usage

MODE="$1"

echo "FALCON-owned volumes this script is scoped to (and ONLY these):"
for v in "${FALCON_VOLUMES[@]}"; do
  echo "  - $v"
done
echo ""
echo "Compose project scope: -p falcon (this compose file's services only:"
echo "  graylog-falcon, datanode-falcon, mongodb-falcon)"
echo ""

case "$MODE" in
  --dry-run)
    echo "[dry-run] docker compose -p falcon -f docker-compose.yml down"
    echo "[dry-run] would remove volumes (only if they exist and belong to this list):"
    for v in "${FALCON_VOLUMES[@]}"; do
      if docker volume inspect "$v" >/dev/null 2>&1; then
        echo "  [dry-run] docker volume rm $v   (EXISTS)"
      else
        echo "  [dry-run] docker volume rm $v   (does not exist, no-op)"
      fi
    done
    echo "[dry-run] docker compose -p falcon -f docker-compose.yml up -d"
    echo "[dry-run] No changes made."
    ;;
  --i-understand-this-destroys-falcon-dev-data)
    if [[ ! -f .env ]]; then
      echo "ERROR: .env not found — refusing to proceed without explicit config." >&2
      exit 1
    fi
    echo "Stopping falcon compose project..."
    docker compose -p falcon -f docker-compose.yml down

    echo "Removing FALCON-owned named volumes..."
    for v in "${FALCON_VOLUMES[@]}"; do
      if docker volume inspect "$v" >/dev/null 2>&1; then
        docker volume rm "$v"
        echo "  removed $v"
      else
        echo "  $v did not exist, skipping"
      fi
    done

    echo "Bringing falcon compose project back up clean..."
    docker compose -p falcon -f docker-compose.yml up -d

    echo "Done. Stack recreated with empty FALCON volumes."
    ;;
  *)
    usage
    ;;
esac
