#!/usr/bin/env bash
# =============================================================================
# FALCON PID-02 — DEV .env bootstrap
#
# Generates a real ./.env (gitignored) from ./.env.example with freshly
# generated random secrets. Idempotent: refuses to overwrite an existing
# .env unless --force is passed. Fails loudly on any missing prerequisite —
# no silent defaults.
#
# IMPORTANT — MongoDB secret rotation caveat:
# `--force` regenerates FALCON_MONGO_ROOT_PASSWORD. MongoDB's own
# MONGO_INITDB_ROOT_PASSWORD environment variable is only ever applied the
# very first time a container initializes an EMPTY volume — it is silently
# ignored on every later container recreate/restart against an
# already-initialized mongodb-falcon-data volume. So a plain `--force`
# against a stack that has already run once writes a new password into
# .env that no longer matches what MongoDB actually has stored, and the
# next `docker compose up`/`--force-recreate` makes mongodb-falcon
# permanently unhealthy (SCRAM "storedKey mismatch"), which cascades into
# datanode-falcon and graylog-falcon never starting at all (both have
# depends_on: mongodb-falcon: condition: service_healthy). To prevent this
# being triggered by accident, `--force` against an already-initialized
# stack additionally requires
# --i-know-this-requires-a-data-wipe-or-manual-mongo-rotation (see the
# refusal message this script prints for the two safe ways to actually
# proceed). Fresh/first-time bootstrap is unaffected — see below.
#
# Usage:
#   ./bootstrap.sh            # create .env if one does not already exist
#   ./bootstrap.sh --force    # regenerate .env, overwriting the existing one
#                             # (against a genuinely fresh/uninitialized
#                             # mongodb-falcon volume this works exactly as
#                             # before; against an already-initialized one
#                             # it now refuses — see caveat above)
#   ./bootstrap.sh --force --i-know-this-requires-a-data-wipe-or-manual-mongo-rotation
#                             # required in addition to --force to actually
#                             # regenerate secrets against an
#                             # already-initialized mongodb-falcon volume
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

ENV_FILE="./.env"
ENV_EXAMPLE="./.env.example"
FORCE=0
ACK_MONGO_ROTATION=0

for arg in "$@"; do
  case "$arg" in
    --force) FORCE=1 ;;
    --i-know-this-requires-a-data-wipe-or-manual-mongo-rotation) ACK_MONGO_ROTATION=1 ;;
    *)
      echo "ERROR: unknown argument '$arg' (only --force and" >&2
      echo "       --i-know-this-requires-a-data-wipe-or-manual-mongo-rotation are accepted)" >&2
      exit 1
      ;;
  esac
done

if [[ ! -f "$ENV_EXAMPLE" ]]; then
  echo "ERROR: $ENV_EXAMPLE not found — cannot bootstrap without the template." >&2
  exit 1
fi

if [[ -f "$ENV_FILE" && "$FORCE" -ne 1 ]]; then
  echo "ERROR: $ENV_FILE already exists. Refusing to overwrite it." >&2
  echo "       Re-run with --force if you explicitly want to regenerate it" >&2
  echo "       (this will invalidate existing Graylog sessions/root password)." >&2
  exit 1
fi

# ---------------------------------------------------------------------------
# Guard: refuse to regenerate secrets with --force against a mongodb-falcon
# volume/container that has already been initialized, unless the operator
# has explicitly acknowledged the consequence. See the caveat in the header
# comment above for the full root cause.
# ---------------------------------------------------------------------------
if [[ -f "$ENV_FILE" && "$FORCE" -eq 1 ]]; then
  MONGO_ALREADY_INITIALIZED=0
  if docker volume inspect mongodb-falcon-data >/dev/null 2>&1 \
     && docker container inspect mongodb-falcon >/dev/null 2>&1; then
    MONGO_ALREADY_INITIALIZED=1
  fi

  if [[ "$MONGO_ALREADY_INITIALIZED" -eq 1 && "$ACK_MONGO_ROTATION" -ne 1 ]]; then
    OLD_MONGO_USER="$(grep -m1 '^FALCON_MONGO_ROOT_USERNAME=' "$ENV_FILE" | cut -d= -f2-)"
    OLD_MONGO_PASS="$(grep -m1 '^FALCON_MONGO_ROOT_PASSWORD=' "$ENV_FILE" | cut -d= -f2-)"
    cat >&2 <<EOF
ERROR: refusing to regenerate secrets with --force.

The mongodb-falcon-data volume and mongodb-falcon container already exist,
i.e. this MongoDB has already been initialized once. MongoDB's own
MONGO_INITDB_ROOT_PASSWORD is applied ONLY the very first time a container
initializes an EMPTY volume — it does nothing on a later recreate/restart.
If this script overwrites .env with a brand-new FALCON_MONGO_ROOT_PASSWORD
now, that new password will NOT match what MongoDB actually has stored,
and the next 'docker compose up'/'--force-recreate' will leave
mongodb-falcon permanently unhealthy ("SCRAM authentication failed,
storedKey mismatch"), which cascades into datanode-falcon and
graylog-falcon never starting at all.

You have two real options:

  1) Accept full FALCON DEV data loss, then bootstrap clean:
       ./reset-dev.sh --i-understand-this-destroys-falcon-dev-data
       ./bootstrap.sh --force

  2) Zero data loss — rotate MongoDB's actual stored credential in place
     FIRST, using the CURRENT (about-to-be-overwritten) .env credentials,
     then let this script write a new .env with that same new password.
     With mongodb-falcon currently running:

       NEW_MONGO_PASSWORD="\$(openssl rand -base64 36 | tr -d '\n/+=' | cut -c1-32)"
       docker exec -i mongodb-falcon mongosh --quiet \\
         --username '${OLD_MONGO_USER}' --password '${OLD_MONGO_PASS}' \\
         --authenticationDatabase admin --eval \\
         "db.getSiblingDB('admin').changeUserPassword('${OLD_MONGO_USER}', '\$NEW_MONGO_PASSWORD')"

     Then manually set FALCON_MONGO_ROOT_PASSWORD=\$NEW_MONGO_PASSWORD in
     .env yourself (do NOT run bootstrap.sh --force for this step — it
     would generate a DIFFERENT random password than the one you just set
     in MongoDB, recreating this exact problem).

If you understand this and still want --force to proceed and overwrite
.env anyway (e.g. because you already did step 2's rotation by hand, or
you are about to run reset-dev.sh), re-run with the second flag:

  ./bootstrap.sh --force --i-know-this-requires-a-data-wipe-or-manual-mongo-rotation
EOF
    exit 1
  fi

  if [[ "$MONGO_ALREADY_INITIALIZED" -eq 1 ]]; then
    echo "WARNING: proceeding with --force against an already-initialized" >&2
    echo "         mongodb-falcon volume (acknowledged via" >&2
    echo "         --i-know-this-requires-a-data-wipe-or-manual-mongo-rotation)." >&2
    echo "         The new FALCON_MONGO_ROOT_PASSWORD will NOT take effect in" >&2
    echo "         MongoDB unless you rotate it there yourself or wipe the" >&2
    echo "         volume — see bootstrap.sh's header comment." >&2
  fi
fi

for bin in openssl sha256sum; do
  if ! command -v "$bin" >/dev/null 2>&1; then
    echo "ERROR: required tool '$bin' not found on PATH." >&2
    exit 1
  fi
done

echo "Generating fresh secrets..."

MONGO_ROOT_USERNAME="falcon_mongo_root"
MONGO_ROOT_PASSWORD="$(openssl rand -base64 36 | tr -d '\n/+=' | cut -c1-32)"
GRAYLOG_PASSWORD_SECRET="$(openssl rand -hex 48)"   # 96 hex chars, well over Graylog's 64-char minimum
ROOT_PASSWORD_PLAINTEXT="$(openssl rand -base64 36 | tr -d '\n/+=' | cut -c1-24)"
ROOT_PASSWORD_SHA2="$(printf '%s' "$ROOT_PASSWORD_PLAINTEXT" | sha256sum | awk '{print $1}')"

if [[ -z "$MONGO_ROOT_PASSWORD" || -z "$GRAYLOG_PASSWORD_SECRET" || -z "$ROOT_PASSWORD_SHA2" ]]; then
  echo "ERROR: secret generation produced an empty value — aborting, refusing to write a weak .env." >&2
  exit 1
fi

# Build .env from .env.example, substituting the generated/fixed values.
# Any line not explicitly handled below is carried through unchanged from
# .env.example (so new non-secret defaults added to the template survive
# bootstrap without code changes here).
awk -v mongo_user="$MONGO_ROOT_USERNAME" \
    -v mongo_pass="$MONGO_ROOT_PASSWORD" \
    -v gl_secret="$GRAYLOG_PASSWORD_SECRET" \
    -v gl_root_sha2="$ROOT_PASSWORD_SHA2" '
  /^FALCON_MONGO_ROOT_USERNAME=/      { print "FALCON_MONGO_ROOT_USERNAME=" mongo_user; next }
  /^FALCON_MONGO_ROOT_PASSWORD=/      { print "FALCON_MONGO_ROOT_PASSWORD=" mongo_pass; next }
  /^FALCON_GRAYLOG_PASSWORD_SECRET=/  { print "FALCON_GRAYLOG_PASSWORD_SECRET=" gl_secret; next }
  /^FALCON_GRAYLOG_ROOT_PASSWORD_SHA2=/ { print "FALCON_GRAYLOG_ROOT_PASSWORD_SHA2=" gl_root_sha2; next }
  { print }
' "$ENV_EXAMPLE" > "$ENV_FILE.tmp"

mv "$ENV_FILE.tmp" "$ENV_FILE"
chmod 600 "$ENV_FILE"

echo ""
echo "Wrote $ENV_FILE (mode 600, gitignored)."
echo ""
echo "=============================================================================="
echo " Graylog root (admin) password — shown ONCE, not stored anywhere in plaintext:"
echo ""
echo "   username: admin"
echo "   password: $ROOT_PASSWORD_PLAINTEXT"
echo ""
echo " Record this now (e.g. in your own password manager). Only its SHA-256 hash"
echo " is persisted, in $ENV_FILE."
echo "=============================================================================="
