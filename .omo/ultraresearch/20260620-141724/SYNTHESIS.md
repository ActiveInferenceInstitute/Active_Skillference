# Ultraresearch Synthesis: Active_Skillference Follow-On Refactor

> **Path note (2026-07-05):** Archived references to `src/pipeline/full_app_stack.py`,
> `src/curriculum/materials.py`, and `src/figures/plots.py` now live under
> `src/integration/full_app_stack.py`, `src/curriculum/materials/`, and
> `src/figures/plots/`. See [`../PATH_CORRECTIONS.md`](../PATH_CORRECTIONS.md).

Workers: 4. Waves: 1 implementation wave plus direct verification. Sources: local codebase, tests, generated artifact gates. Verifications: targeted affected band, full coverage gate, lint/format, mypy, artifact validators, release inventory, live full-stack probe.

## Executive Summary

The highest-value follow-on work was not more curriculum or kernel churn. The strongest improvements were to harden the new shared seams introduced by the refactor stack: direct negative controls for `src.skilltree.summary`, `src.figures.registry`, and `src.dashboard.live_validation`; generated JSON writer consolidation under `src.artifacts.json_io`; safer local SkillTree secret persistence; and extraction of the remaining large full-stack validator logic from `scripts/validate_full_app_stack.py` into `src.pipeline.full_app_stack`.

The implemented changes preserve exported JSON and CLI surfaces. The final local deterministic gates pass: `uv run pytest --cov=src --cov-fail-under=90` reported 750 passed with 91.61% coverage; `uvx ruff check src scripts tests`, `uvx ruff format --check src scripts tests`, and `uv run mypy src` pass; artifact/manuscript/roadmap validators pass. The only live-readiness blocker remains external Docker daemon availability: `uv run python scripts/validate_full_app_stack.py --app-ready --skip-browser --timeout 30` fails before app logic with Docker daemon unreachable.

## Findings By Theme

### Shared Schema Oracles

Evidence: `wave-0-codebase-coverage.md`, `tests/test_skilltree_exporter.py`, `tests/test_figures.py`, `tests/test_dashboard_live_validation.py`, `tests/test_artifacts_json_io.py`.

Implemented:
- `summarize_export_payload()` now has strict malformed collection tests and non-strict fallback tests.
- `load_figure_registry_rows()` now has direct file-backed negatives for non-list payloads, non-object rows, invalid labels, invalid filenames, duplicate labels, and duplicate filenames.
- `validate_live_skilltree_dashboard()` now has direct module tests for non-object SkillTree status JSON, missing export, malformed export shape, and token secret exposure.
- `read_json_object()` now has invalid-JSON propagation coverage, and `write_json_artifact(..., ensure_ascii=False)` has explicit coverage.

Verified: targeted 37-test band passed; full suite passed.

### Generated JSON Ownership

Evidence: `wave-0-codebase-json-ownership.md`, `src/artifacts/json_io.py`, generated writer modules.

Implemented:
- Replaced local generated JSON writers with `write_json_artifact()` in manuscript audit, claim support, scholarship coverage, source health, gap report, course materials, and curriculum stats.
- Replaced direct manuscript-variable JSON reads with `read_json_object()` and fixed the script path bootstrap for direct execution.

Intentionally excluded:
- Local auth state, HTTP clients, dashboard response JSON, CLI stdout JSON, and release markdown stay bespoke because their failure modes are not file-backed artifact schema ownership.

Verified: script smoke tests, artifact validators, and full suite passed.

### Security-Sensitive Local Auth

Evidence: `wave-0-codebase-release-security.md`, `src/skilltree/local_auth.py`, `tests/test_skilltree_local_auth.py`.

Implemented:
- Local auth now constructs the trusted-client secret state in memory, verifies token exchange first when requested, then saves the state.
- Added a regression test proving a failed token exchange does not persist the newly acquired client secret.

Verified: `tests/test_skilltree_local_auth.py` passed in the affected band and full suite.

### Thin-Orchestrator Boundary

Evidence: `wave-0-codebase-script-boundaries.md`, `src/pipeline/full_app_stack.py`, `scripts/validate_full_app_stack.py`, `tests/test_full_app_stack.py`.

Implemented:
- Moved full-stack command builders, subprocess policy, Docker checks, JSON polling, dashboard process lifecycle, proof shaping, and validation sequence into `src.pipeline.full_app_stack`.
- Reduced `scripts/validate_full_app_stack.py` to argument parsing, error reporting, and JSON output.
- Updated tests to cover the source module directly and docs to document the new owner.

Verified: `tests/test_full_app_stack.py`, `tests/test_reset_local_skilltree.py`, wrapper `--help`, affected band, ruff, mypy, and full suite passed.

## Codebase Findings

- `/Users/4d/Documents/GitHub/projects/working/Active_Skillference/src/skilltree/summary.py` is now fully covered for malformed export summaries.
- `/Users/4d/Documents/GitHub/projects/working/Active_Skillference/src/figures/registry.py` has direct loader negative controls.
- `/Users/4d/Documents/GitHub/projects/working/Active_Skillference/src/dashboard/live_validation.py` has direct failure-mode tests.
- `/Users/4d/Documents/GitHub/projects/working/Active_Skillference/src/artifacts/json_io.py` remains the canonical generated artifact JSON helper.
- `/Users/4d/Documents/GitHub/projects/working/Active_Skillference/src/skilltree/local_auth.py` no longer persists a newly fetched client secret before required token verification succeeds.
- `/Users/4d/Documents/GitHub/projects/working/Active_Skillference/src/pipeline/full_app_stack.py` is the new owner for full-app validation logic.

## Verified Claims

| Claim | Verdict | Evidence |
| --- | --- | --- |
| Full test coverage gate passes | CONFIRMED | `uv run pytest --cov=src --cov-fail-under=90`: 750 passed, 91.61% coverage |
| Lint and format gates pass | CONFIRMED | `uvx ruff check src scripts tests`; `uvx ruff format --check src scripts tests` |
| Type checking passes | CONFIRMED | `uv run mypy src` |
| Generated artifact/manuscript/roadmap gates pass | CONFIRMED | `scripts/run_kernels.py`, `export_skilltree.py`, manuscript, roadmap, freshness, web math, alignment, live-count validators |
| Live full-stack proof is not locally runnable yet | PARTIAL | `validate_full_app_stack.py --app-ready --skip-browser --timeout 30` fails at Docker daemon reachability |

## Gaps

- `build_generated_outputs()` failure propagation and some `src/curriculum/materials.py` branch negatives remain useful future tests.
- `scripts/validate_dashboard_console.py` and `scripts/bootstrap_local_skilltree.py` still contain smaller reusable logic pockets, but lower leverage than the extracted full-stack validator.
- Live Docker/SkillTree/browser proof remains blocked by local Docker daemon reachability.

## Expansion Trace

Wave 0 spawned four axes: coverage, thin scripts, generated JSON ownership, and release/security. The actionable high-confidence leads from all four were implemented and verified. Remaining leads were either lower priority branch-coverage work or higher-blast-radius script extraction candidates and are documented above.
