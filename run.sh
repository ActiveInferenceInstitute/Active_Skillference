#!/usr/bin/env bash
# Active Skillference — cold start to the interactive learner surface.
#
# One command, from a fresh checkout to a browser page you can learn from. Every
# step announces what it is doing, why, and what to do if it stops. Stopping
# early with a clear reason is the intended behavior: this project would rather
# refuse than show you a page that looks alive and is not.
#
#   ./run.sh              full path: dependencies, build, live SkillTree, dashboard
#   ./run.sh --offline    no Docker: build and serve artifacts only
#   ./run.sh --check      report readiness and exit without starting anything
#
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_ROOT"

DASHBOARD_HOST="${DASHBOARD_HOST:-127.0.0.1}"
DASHBOARD_PORT="${DASHBOARD_PORT:-8765}"
SKILLTREE_URL="${SKILLTREE_URL:-http://localhost:8080}"
DASHBOARD_URL="http://${DASHBOARD_HOST}:${DASHBOARD_PORT}"
SKILLTREE_WAIT_ATTEMPTS="${SKILLTREE_WAIT_ATTEMPTS:-240}"
ACTIVE_SKILLFERENCE_LOCAL_STATE_DIR="${ACTIVE_SKILLFERENCE_LOCAL_STATE_DIR:-.active_skillference_local}"
ACTIVE_SKILLFERENCE_LEARNER_ID="${ACTIVE_SKILLFERENCE_LEARNER_ID:-local-learner}"
# Compose interpolates this; it must match the value the stack was created
# with, so reuse the stored one and generate it only on first run. This mirrors
# src/integration/full_app_stack.py::ensure_postgres_password.
_pg_file="$ACTIVE_SKILLFERENCE_LOCAL_STATE_DIR/postgres_password"
if [ -z "${ACTIVE_SKILLFERENCE_POSTGRES_PASSWORD:-}" ]; then
  if [ -s "$_pg_file" ]; then
    ACTIVE_SKILLFERENCE_POSTGRES_PASSWORD="$(tr -d '\n' < "$_pg_file")"
  else
    mkdir -p "$ACTIVE_SKILLFERENCE_LOCAL_STATE_DIR"
    chmod 700 "$ACTIVE_SKILLFERENCE_LOCAL_STATE_DIR" 2>/dev/null || true
    ACTIVE_SKILLFERENCE_POSTGRES_PASSWORD="$(LC_ALL=C tr -dc 'A-Za-z0-9' < /dev/urandom | head -c 40)"
    printf '%s\n' "$ACTIVE_SKILLFERENCE_POSTGRES_PASSWORD" > "$_pg_file"
    chmod 600 "$_pg_file" 2>/dev/null || true
  fi
fi
export ACTIVE_SKILLFERENCE_POSTGRES_PASSWORD

MODE="full"
for arg in "$@"; do
  case "$arg" in
    --offline) MODE="offline" ;;
    --check) MODE="check" ;;
    -h|--help) sed -n '2,12p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "unknown option: $arg (try --help)" >&2; exit 2 ;;
  esac
done

TOTAL_STEPS=6
[ "$MODE" = "offline" ] && TOTAL_STEPS=4
STEP=0

say() { printf '\n\033[1m%s\033[0m\n' "$*"; }
step() { STEP=$((STEP + 1)); printf '\n\033[1m[%d/%d] %s\033[0m\n' "$STEP" "$TOTAL_STEPS" "$*"; }
note() { printf '      %s\n' "$*"; }
fail() { printf '\n\033[1mSTOPPED:\033[0m %s\n' "$1" >&2; shift; for line in "$@"; do printf '      %s\n' "$line" >&2; done; exit 1; }

say "Active Skillference — starting the learner surface"
note "Mode: $MODE"
note "The learner page will be at $DASHBOARD_URL"

# ---------------------------------------------------------------- prerequisites
step "Checking prerequisites"
command -v uv >/dev/null 2>&1 || fail "uv is not installed." \
  "uv manages this project's Python environment." \
  "Install it with:  curl -LsSf https://astral.sh/uv/install.sh | sh" \
  "Then re-run:      ./run.sh"
note "uv: $(uv --version 2>/dev/null || echo present)"

DOCKER_READY=0
if [ "$MODE" != "offline" ]; then
  if ! command -v docker >/dev/null 2>&1; then
    note "docker: not installed"
    fail "Docker is required for the live learning surface." \
      "The live path runs SkillTree, which owns quizzes, progress, and ranking." \
      "Install Docker Desktop or Engine, or run the artifact-only path:" \
      "  ./run.sh --offline"
  elif ! docker info >/dev/null 2>&1; then
    note "docker: installed but the daemon is not reachable"
    fail "The Docker daemon is not running." \
      "Start Docker Desktop or Colima, confirm 'docker info' succeeds, then re-run." \
      "Or run without it:  ./run.sh --offline"
  else
    DOCKER_READY=1
    note "docker: daemon reachable"
  fi
fi

if [ "$MODE" = "check" ]; then
  say "Readiness check complete"
  note "uv present; docker ready=$DOCKER_READY"
  note "Run ./run.sh for the live surface, or ./run.sh --offline for artifacts only."
  exit 0
fi

# ------------------------------------------------------------------ environment
step "Installing the Python environment"
note "uv sync — resolves the locked dependency set (first run downloads packages)"
uv sync

# ----------------------------------------------------------------- build inputs
step "Building the curriculum and generated artifacts"
note "The learner page reads generated files, so they are built before it starts."
note "build_curriculum.py — validates the prerequisite graph is acyclic and connected"
uv run python scripts/build_curriculum.py
note "run_kernels.py — computes every claim, figure, and lesson record from source"
uv run python scripts/run_kernels.py
note "export_skilltree.py — provenance-gated export; refuses on any unbacked number"
uv run python scripts/export_skilltree.py

if [ "$MODE" = "offline" ]; then
  step "Serving the artifact-only learner page"
  note "SkillTree is not running, so quizzes and progress are unavailable by design."
  note "The curriculum explorer, lesson records, graph, and artifacts all work."
  say "Open:  $DASHBOARD_URL"
  note "Stop with Ctrl-C."
  exec uv run python scripts/serve_learner_dashboard.py \
    --host "$DASHBOARD_HOST" --port "$DASHBOARD_PORT"
fi

# ------------------------------------------------------------- live SkillTree
# Run a long command with a live elapsed-time heartbeat, so a slow step is
# visibly slow rather than indistinguishable from a hang.
run_with_heartbeat() {
  local label="$1"; shift
  local log
  log="$(mktemp -t asf-run)"
  "$@" >"$log" 2>&1 &
  local pid=$!
  local elapsed=0
  while kill -0 "$pid" 2>/dev/null; do
    sleep 15
    elapsed=$((elapsed + 15))
    printf '      … %s: %dm%02ds elapsed — %s\n' \
      "$label" "$((elapsed / 60))" "$((elapsed % 60))" "$(tail -n 1 "$log" | cut -c1-90)"
  done
  local status=0
  wait "$pid" || status=$?
  if [ "$status" -ne 0 ]; then
    printf '\n--- last 30 lines of %s ---\n' "$label" >&2
    tail -n 30 "$log" >&2
  fi
  rm -f "$log"
  return "$status"
}

step "Starting the SkillTree container stack"
note "SkillTree owns learning state: quizzes, completion, points, and ranking."
note "Expect seconds if the stack is already up; several minutes on a first"
note "image pull. Re-running is safe: compose reuses the running containers."
if ! run_with_heartbeat "docker compose" docker compose up -d; then
  fail "The SkillTree containers did not start." \
    "Check 'docker compose ps' and docs/troubleshooting.md." \
    "The artifact-only page still works:  ./run.sh --offline"
fi
printf '      waiting for %s/public/status' "$SKILLTREE_URL"
for _ in $(seq 1 "${SKILLTREE_WAIT_ATTEMPTS:-240}"); do
  if curl -fsS "$SKILLTREE_URL/public/status" >/dev/null 2>&1; then
    printf ' — ready\n'
    break
  fi
  printf '.'
  sleep 2
done
curl -fsS "$SKILLTREE_URL/public/status" >/dev/null 2>&1 || fail \
  "SkillTree did not answer at $SKILLTREE_URL." \
  "On Apple/ARM the pinned image boots slowly; raise the window with" \
  "  SKILLTREE_WAIT_ATTEMPTS=600 ./run.sh" \
  "Or run without it:  ./run.sh --offline"

step "Seeding the curriculum into SkillTree"
note "This is the slow step, and it is idempotent: if SkillTree already reports"
note "the exported subject and skill counts, seeding is skipped entirely and"
note "this finishes in seconds."
note "A first seed writes every subject, skill, and quiz over REST. Budget"
note "10-40 minutes on Apple/ARM Docker emulation; it is working, not stuck."
note "Prerequisite edges are NOT seeded here. They are far slower and the"
note "learner surface does not need them, so they are a separate opt-in step."
if ! run_with_heartbeat "seeding" uv run python scripts/bootstrap_local_skilltree.py \
  --base-url "$SKILLTREE_URL" \
  --state-dir "$ACTIVE_SKILLFERENCE_LOCAL_STATE_DIR" \
  --learner-id "$ACTIVE_SKILLFERENCE_LEARNER_ID" \
  --skip-seed-if-live-counts-ready \
  --skip-dependencies; then
  fail "Seeding did not complete." \
    "The output above ends with the failing call." \
    "If local login state is stale, reset it with:" \
    "  uv run python scripts/reset_local_skilltree.py --confirm-local-reset" \
    "See docs/troubleshooting.md."
fi
note "SkillTree is seeded and reachable at $SKILLTREE_URL"

# ---------------------------------------------------------------- learner page
step "Serving the interactive learner surface"
cat <<BANNER

  ────────────────────────────────────────────────────────────────────────
   Learner surface:  $DASHBOARD_URL
   Raw SkillTree:    $SKILLTREE_URL

   What to click, in order:
     1. Official Display  — the SkillTree learner view: points, level, rank
     2. Curriculum        — search a topic, then press Learn on any skill to
                            open its lesson; Quiz hands off to SkillTree
     3. Graph             — prerequisite lanes plus an accessible flow table
     4. Artifacts         — every generated figure and audit, with its contract
     5. Runtime           — deployment readiness and the browser-safe payload

   Accessibility: the page is keyboard-navigable end to end. Tab reaches a
   "Skip to main content" link first; the view switcher is a WAI-ARIA tab list
   (Arrow keys move, Home/End jump); every status is a word, not a color; and
   the dependency graph ships a captioned table carrying the same relations as
   the drawing.

   Local SkillTree sign-in, if a page asks for it:
     username  active-skillference-admin@localhost.invalid
     password  active-skillference-local
   If that is rejected, the local volume predates these defaults — see
   docs/troubleshooting.md and run reset_local_skilltree.py.

   Prerequisite edges are seeded separately because they are slow:
     uv run python scripts/reconcile_live_dependencies.py --check-only
     uv run python scripts/reconcile_live_dependencies.py
   The Graph tab and lesson records work without them; only the live
   dependency-parity metric reports them as outstanding.

   Stop everything with Ctrl-C, then:  docker compose down
  ────────────────────────────────────────────────────────────────────────

BANNER
exec uv run python scripts/serve_learner_dashboard.py \
  --host "$DASHBOARD_HOST" --port "$DASHBOARD_PORT" --local-auth
