# Wave 0 - Thin-Orchestrator Boundaries

> **Path note (2026-07-05):** Full-stack logic now lives in `src/integration/full_app_stack.py`
> (not `src/pipeline/full_app_stack.py`). See [`../PATH_CORRECTIONS.md`](../PATH_CORRECTIONS.md).

Worker: `019ee6e5-ded1-7c12-958e-d63bfd72ea35`

Key findings:
- `scripts/run_kernels.py`, `scripts/validate_live_skilltree_dashboard.py`, and `scripts/validate_release_readiness_inventory.py` were already thin wrappers.
- `scripts/validate_full_app_stack.py` was the main residual boundary violation: command builders, subprocess policy, polling, proof shaping, dependency reconciliation, and dashboard process lifecycle lived in script space.
- Smaller future candidates remain in `scripts/validate_dashboard_console.py`, `scripts/bootstrap_local_skilltree.py`, and `scripts/reset_local_skilltree.py`, but their blast radius is lower.

Implemented from this wave:
- Added `src/pipeline/full_app_stack.py` for reusable full-stack proof orchestration.
- Reduced `scripts/validate_full_app_stack.py` to CLI parsing, error reporting, and JSON printing.
- Updated `tests/test_full_app_stack.py` to cover the new source module directly.
- Updated `scripts/README.md` and `scripts/AGENTS.md` to document `src.pipeline.full_app_stack` as the logic owner.

EXPAND markers:
- LEAD: `scripts/validate_full_app_stack.py` still owns reusable orchestration and command assembly.
- LEAD: `scripts/validate_dashboard_console.py` still owns reusable browser-console gate logic.
- LEAD: `scripts/bootstrap_local_skilltree.py` still owns `build_project` and bootstrap assembly.
- LEAD: `scripts/run_kernels.py`, `scripts/validate_live_skilltree_dashboard.py`, and `scripts/validate_release_readiness_inventory.py` are already thin wrappers.
