# Wave 0 - Coverage And Negative Controls

> **Path note (2026-07-05):** Figure logic is under `src/figures/plots/` (not `plots.py`).
> See [`../PATH_CORRECTIONS.md`](../PATH_CORRECTIONS.md).

Worker: `019ee6e5-d8ee-7701-b2fb-03cdbb3ce8ee`

Key findings:
- `src/skilltree/summary.py` had only valid-export parity coverage; malformed strict and non-strict branches were untested.
- `src/figures/registry.py` had no direct file-backed loader negatives for non-list payloads, non-object rows, invalid labels, invalid filenames, duplicate labels, or duplicate filenames.
- `src/dashboard/live_validation.py` had integration-style coverage but lacked direct failure-mode tests for non-object endpoint JSON, missing project export, malformed project export shape, and token secret exposure.
- `src/artifacts/json_io.py` lacked invalid-JSON propagation and `ensure_ascii=False` coverage.

Implemented from this wave:
- Added malformed export summary tests in `tests/test_skilltree_exporter.py`.
- Added direct live-dashboard validation tests in `tests/test_dashboard_live_validation.py`.
- Added invalid JSON and non-ASCII writer tests in `tests/test_artifacts_json_io.py`.
- Added direct figure registry loader tests in `tests/test_figures.py`.

EXPAND markers:
- LEAD: `load_figure_registry_rows()` has no direct tests for invalid JSON shape, duplicate labels/files, or bad filenames.
- LEAD: `summarize_export_payload()` strict/fallback branches are untested.
- LEAD: `build_generated_outputs()` has only the success path covered.
- LEAD: `validate_active_skillference_material_contract()` still lacks required-source and per-stratum pointer negatives.
- LEAD: `validate_live_skilltree_dashboard()` helper branches are not directly unit-tested.
- LEAD: `read_json_object()` / `read_json_array()` lack invalid-JSON regression tests.
