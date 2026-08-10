#!/usr/bin/env bash
# Bring up SkillTree, seed Active_Skillference, and serve the local learner dashboard.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

SKILLTREE_URL="${SKILLTREE_URL:-http://localhost:8080}"
SKILLTREE_WAIT_ATTEMPTS="${SKILLTREE_WAIT_ATTEMPTS:-240}"
DASHBOARD_HOST="${DASHBOARD_HOST:-127.0.0.1}"
DASHBOARD_PORT="${DASHBOARD_PORT:-8765}"
DASHBOARD_AUTHENTICATOR="${DASHBOARD_AUTHENTICATOR:-${SKILLTREE_AUTHENTICATOR:-}}"
ACTIVE_SKILLFERENCE_LOCAL_AUTH="${ACTIVE_SKILLFERENCE_LOCAL_AUTH:-1}"
ACTIVE_SKILLFERENCE_LEARNER_ID="${ACTIVE_SKILLFERENCE_LEARNER_ID:-local-learner}"
ACTIVE_SKILLFERENCE_LOCAL_STATE_DIR="${ACTIVE_SKILLFERENCE_LOCAL_STATE_DIR:-.active_skillference_local}"
POSTGRES_PASSWORD_FILE="$ACTIVE_SKILLFERENCE_LOCAL_STATE_DIR/postgres_password"
SEED_ARGS=(--base-url "$SKILLTREE_URL" --require-live)

if ! command -v docker >/dev/null 2>&1; then
  echo "ERROR: docker is not installed. Install Docker Desktop / Engine, then re-run." >&2
  echo "The static dashboard can still inspect generated artifacts with:" >&2
  echo "  uv run python scripts/serve_learner_dashboard.py --check" >&2
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

echo "==> Regenerating curriculum, claims, figures, and SkillTree export ..."
uv run python scripts/build_curriculum.py
uv run python scripts/run_kernels.py
uv run python scripts/export_skilltree.py

if [ "$ACTIVE_SKILLFERENCE_LOCAL_AUTH" = "1" ]; then
  echo "==> Bootstrapping local no-login SkillTree auth and seeding curriculum ..."
  uv run python scripts/bootstrap_local_skilltree.py \
    --base-url "$SKILLTREE_URL" \
    --state-dir "$ACTIVE_SKILLFERENCE_LOCAL_STATE_DIR" \
    --learner-id "$ACTIVE_SKILLFERENCE_LEARNER_ID"
else
  echo "==> Seeding the Active Inference curriculum ..."
  if ! uv run python scripts/seed_skilltree.py "${SEED_ARGS[@]}"; then
    if [ -z "${SKILLTREE_TOKEN:-}" ] && [ "${REQUIRE_SKILLTREE_SEED:-0}" != "1" ]; then
      echo "WARNING: SkillTree is running, but live seeding requires admin authentication." >&2
      echo "WARNING: Continuing with the local dashboard over generated artifacts." >&2
      echo "WARNING: To require a live seed, set REQUIRE_SKILLTREE_SEED=1 and provide SKILLTREE_TOKEN." >&2
    else
      exit 1
    fi
  fi
fi

SERVE_AUTH_ARGS=()
if [ "$ACTIVE_SKILLFERENCE_LOCAL_AUTH" = "1" ]; then
  SERVE_AUTH_ARGS+=(--local-auth --local-state-dir "$ACTIVE_SKILLFERENCE_LOCAL_STATE_DIR" --learner-id "$ACTIVE_SKILLFERENCE_LEARNER_ID")
else
  SERVE_AUTH_ARGS+=(--no-local-auth)
fi

if [ -n "$DASHBOARD_AUTHENTICATOR" ]; then
  SERVE_AUTH_ARGS+=(--authenticator "$DASHBOARD_AUTHENTICATOR")
fi

echo "==> Serving learner dashboard at http://${DASHBOARD_HOST}:${DASHBOARD_PORT} ..."
uv run python scripts/serve_learner_dashboard.py \
  --skilltree-url "$SKILLTREE_URL" \
  --host "$DASHBOARD_HOST" \
  --port "$DASHBOARD_PORT" \
  "${SERVE_AUTH_ARGS[@]}"
