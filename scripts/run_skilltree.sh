#!/usr/bin/env bash
# Bring up a local SkillTree instance and seed it with the Active Inference curriculum.
#
# One command:   ./scripts/run_skilltree.sh
#
# Requires Docker + the Docker Compose plugin. The SkillTree dashboard will be served
# at http://localhost:8080. By default this uses the local FORM-auth bootstrap path
# and stores ignored local trusted-client state in .active_skillference_local/.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

SKILLTREE_URL="${SKILLTREE_URL:-http://localhost:8080}"
SKILLTREE_WAIT_ATTEMPTS="${SKILLTREE_WAIT_ATTEMPTS:-240}"
ACTIVE_SKILLFERENCE_LOCAL_AUTH="${ACTIVE_SKILLFERENCE_LOCAL_AUTH:-}"
ACTIVE_SKILLFERENCE_LEARNER_ID="${ACTIVE_SKILLFERENCE_LEARNER_ID:-local-learner}"
ACTIVE_SKILLFERENCE_LOCAL_STATE_DIR="${ACTIVE_SKILLFERENCE_LOCAL_STATE_DIR:-.active_skillference_local}"
POSTGRES_PASSWORD_FILE="$ACTIVE_SKILLFERENCE_LOCAL_STATE_DIR/postgres_password"

if [ -z "$ACTIVE_SKILLFERENCE_LOCAL_AUTH" ]; then
  if [ -n "${SKILLTREE_TOKEN:-}" ]; then
    ACTIVE_SKILLFERENCE_LOCAL_AUTH=0
  else
    ACTIVE_SKILLFERENCE_LOCAL_AUTH=1
  fi
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "ERROR: docker is not installed. Install Docker Desktop / Engine, then re-run." >&2
  echo "Alternatively build skills-service from source — see vendor/README.md." >&2
  exit 1
fi

if ! command -v uv >/dev/null 2>&1; then
  echo "ERROR: uv is not installed or is not on PATH." >&2
  exit 1
fi

if ! command -v curl >/dev/null 2>&1; then
  echo "ERROR: curl is required to poll SkillTree's public status endpoint." >&2
  exit 1
fi

if [ "$ACTIVE_SKILLFERENCE_LOCAL_AUTH" != "1" ] && [ -z "${SKILLTREE_TOKEN:-}" ]; then
  echo "ERROR: ACTIVE_SKILLFERENCE_LOCAL_AUTH=0 requires SKILLTREE_TOKEN for admin REST seeding." >&2
  echo "Use the default local bootstrap path, or run:" >&2
  echo "  ACTIVE_SKILLFERENCE_LOCAL_AUTH=0 SKILLTREE_TOKEN=... ./scripts/run_skilltree.sh" >&2
  exit 1
fi

if [ -z "${ACTIVE_SKILLFERENCE_POSTGRES_PASSWORD:-}" ]; then
  mkdir -p "$ACTIVE_SKILLFERENCE_LOCAL_STATE_DIR"
  chmod 700 "$ACTIVE_SKILLFERENCE_LOCAL_STATE_DIR"
  if [ ! -s "$POSTGRES_PASSWORD_FILE" ]; then
    (
      umask 077
      uv run python - <<'PY' > "$POSTGRES_PASSWORD_FILE"
import secrets

print(secrets.token_urlsafe(32))
PY
    )
  fi
  ACTIVE_SKILLFERENCE_POSTGRES_PASSWORD="$(cat "$POSTGRES_PASSWORD_FILE")"
fi
export ACTIVE_SKILLFERENCE_POSTGRES_PASSWORD

echo "==> Starting SkillTree (postgres + skills-service) via docker compose ..."
docker compose up -d

echo "==> Waiting for SkillTree REST API at ${SKILLTREE_URL} ..."
for _ in $(seq 1 "$SKILLTREE_WAIT_ATTEMPTS"); do
  if curl -sf "${SKILLTREE_URL}/public/status" >/dev/null 2>&1; then
    echo "==> SkillTree is up."
    break
  fi
  sleep 5
done

if ! curl -sf "${SKILLTREE_URL}/public/status" >/dev/null 2>&1; then
  echo "ERROR: SkillTree did not become reachable at ${SKILLTREE_URL}" >&2
  exit 1
fi

if [ "$ACTIVE_SKILLFERENCE_LOCAL_AUTH" = "1" ]; then
  echo "==> Bootstrapping local FORM auth and seeding the Active Inference curriculum ..."
  uv run python scripts/bootstrap_local_skilltree.py \
    --base-url "$SKILLTREE_URL" \
    --state-dir "$ACTIVE_SKILLFERENCE_LOCAL_STATE_DIR" \
    --learner-id "$ACTIVE_SKILLFERENCE_LEARNER_ID"
else
  echo "==> Seeding the Active Inference curriculum with SKILLTREE_TOKEN ..."
  uv run python scripts/seed_skilltree.py \
    --base-url "$SKILLTREE_URL" \
    --require-live
fi

echo "==> Done. Open ${SKILLTREE_URL} to explore the skill tree."
