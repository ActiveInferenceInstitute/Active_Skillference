#!/usr/bin/env bash
# Active Skillference — the single gate entry point.
#
# Every offline gate the project runs is one arm of this script, and CI runs the
# same arms: `.github/workflows/gates.yml` calls `./gates.sh <arm>`, never a copy
# of a command. An arm you run here is exactly the arm CI runs.
#
#   ./gates.sh              default arms: lint, types, fast (the developer loop)
#   ./gates.sh lint         Ruff check + format check
#   ./gates.sh types        mypy over src/
#   ./gates.sh fast         test suite minus the `slow`-marked modules
#   ./gates.sh test         full test suite + the 90% src/ coverage floor
#   ./gates.sh artifacts    curriculum, kernels/figures, SkillTree export
#   ./gates.sh checks       provenance, scholarship, manuscript, roadmap validators
#   ./gates.sh docs         documentation links + generated gate-metrics freshness
#   ./gates.sh gnn          pinned-upstream GNN conformance (needs GNN_ROOT)
#   ./gates.sh sync         install the locked environment (uv sync --frozen)
#   ./gates.sh all          every CI arm, in CI order
#   ./gates.sh record       time every arm, refresh docs/gate_metrics.md
#   ./gates.sh list         print the arms
#
# Arms are independently runnable and ordered only where one consumes another's
# output: `checks` and `test` read the artifacts `artifacts` writes, and `docs`
# reads the receipt `record` writes. Nothing else is serialized.
#
# The GNN arm needs the pinned upstream parser. Provision it once with the
# commands in README.md ("Required local GNN check") and export GNN_ROOT; the arm
# fails — never skips — when the checkout is missing or unusable.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_ROOT"

TIMINGS_DIR="${TIMINGS_DIR:-docs/_generated}"
TIMINGS_JSON="$TIMINGS_DIR/arm_timings.json"

say() { printf '\n\033[1m== %s\033[0m\n' "$*"; }

arm_sync() {
  uv sync --frozen
}

arm_lint() {
  # Ruff comes from the locked dev group, so CI and a local run share one
  # resolution; `uvx ruff` would resolve an unpinned tool outside uv.lock.
  uv run ruff check src scripts tests
  uv run ruff format --check src scripts tests
}

arm_types() {
  uv run mypy src
}

arm_fast() {
  # `slow` is the repository's opt-in selection for the module-level suites that
  # pay for figure rendering or a full artifact rebuild; the full arm still runs
  # them, and CI runs the full arm.
  uv run pytest -m "not slow" -q
}

arm_test() {
  uv run pytest --cov=src --cov-fail-under=90 -q
}

arm_artifacts() {
  uv run python scripts/build_curriculum.py
  uv run python scripts/run_kernels.py
  uv run python scripts/export_skilltree.py
}

arm_checks() {
  uv run python scripts/validate_claim_support.py
  uv run python scripts/validate_manuscript_artifacts.py
  uv run python scripts/validate_manuscript_variables.py
  uv run python scripts/validate_american_english.py
  uv run python scripts/validate_scholarship_sources.py
  uv run python scripts/validate_course_material_alignment.py
  uv run python scripts/validate_learner_pilot_contract.py
  uv run python scripts/validate_live_counts.py
  uv run python scripts/validate_roadmap.py
  uv run python scripts/validate_docker_digests.py
}

arm_docs() {
  uv run python scripts/check_docs_links.py
  uv run python scripts/z_generate_gate_metrics.py --check
}

arm_gnn() {
  : "${GNN_ROOT:?Set GNN_ROOT to a prepared pinned GNN checkout (see README.md 'Required local GNN check')}"
  uv run python scripts/validate_gnn_spec.py
  uv run pytest tests/test_gnn_conformance.py -q -p no:cacheprovider
}

arm_render() {
  uv run python scripts/render_manuscript.py
  uv run python scripts/ensure_web_math.py
  uv run python scripts/validate_web_math.py
  uv run python scripts/validate_rendered_freshness.py
}

ALL_ARMS=(sync lint types artifacts checks test docs gnn)
# Everything `record` times before the metrics document exists; `docs` is timed after,
# and `render` needs a LaTeX toolchain.
RECORDED_ARMS=(sync lint types fast artifacts checks test gnn)

run_arm() {
  case "$1" in
    sync | lint | types | fast | test | artifacts | checks | docs | gnn | render) "arm_$1" ;;
    *)
      printf 'unknown arm: %s\n\n' "$1" >&2
      list_arms >&2
      return 2
      ;;
  esac
}

list_arms() {
  printf 'arms: sync lint types fast test artifacts checks docs gnn render all record\n'
  printf 'default (no argument): lint types fast\n'
}

# `record` is the only arm that writes the timing receipt; run it after changing
# an arm so docs/gate_metrics.md reports numbers the script can reproduce.
#
# The `docs` arm verifies the very document `record` writes, so it cannot pass
# mid-record: the receipt and document are written first, then `docs` is timed against
# the fresh files and merged into the final receipt. `render` is excluded because it
# needs a LaTeX toolchain; time it on its own.
arm_record() {
  [ -x /usr/bin/time ] || {
    printf 'record needs /usr/bin/time to measure each arm; install it or time the arms by hand\n' >&2
    return 2
  }
  mkdir -p "$TIMINGS_DIR"
  local tmp
  tmp="$(mktemp -d)"
  trap 'rm -rf "${tmp:-}"' EXIT
  local name real rc failures=0
  : >"$tmp/rows"
  _time_arm() {
    say "record: $1"
    rc=0
    /usr/bin/time -p bash "${BASH_SOURCE[0]}" "$1" >"$tmp/$1.log" 2>"$tmp/$1.err" || rc=$?
    real="$(sed -n 's/^real[[:space:]]\{1,\}//p' "$tmp/$1.err" | tail -1)"
    printf '%s\t%s\t%s\n' "$1" "${real:-0}" "$rc" >>"$tmp/rows"
    if [ "$rc" -ne 0 ]; then
      failures=$((failures + 1))
      printf 'arm %s exited %s (see %s)\n' "$1" "$rc" "$tmp/$1.err" >&2
    fi
  }
  for name in "${RECORDED_ARMS[@]}"; do
    _time_arm "$name"
  done
  uv run python scripts/z_generate_gate_metrics.py --write \
    --rows "$tmp/rows" --test-log "$tmp/test.log" --timings "$TIMINGS_JSON"
  _time_arm docs
  uv run python scripts/z_generate_gate_metrics.py --write \
    --rows "$tmp/rows" --test-log "$tmp/test.log" --timings "$TIMINGS_JSON"
  sed -n '1,$p' "$tmp/rows"
  [ "$failures" -eq 0 ] || {
    printf '%s arm(s) failed while recording; see the log above\n' "$failures" >&2
    return 1
  }
}

case "${1:-default}" in
  default) arm_lint; arm_types; arm_fast ;;
  all)
    for name in "${ALL_ARMS[@]}"; do
      say "arm: $name"
      run_arm "$name"
    done
    ;;
  list | -h | --help) list_arms ;;
  record) arm_record ;;
  *) run_arm "$1" ;;
esac
