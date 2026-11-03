# `src/curriculum/` — the validated prerequisite DAG

`model.py` defines the frozen `Stratum`, `Subject`, `Skill` and
`AssessmentQuestion` types. `graph.py` owns `CurriculumGraph` validation,
topological order, levels and the foundations→applications connectivity check.
`catalog.py` is the entry point: `build_curriculum()` assembles the subjects and
runs `quality.py`.

Subject content lives in [`catalog_data/`](catalog_data/); the many `_ext_*.py`
modules are curriculum extensions aggregated by
`catalog_data/subjects_extensions_*.py`. `normalize.py` and
`assessment_normalize.py` harden authored data; `diagnostics.py`,
`recommendations.py`, `alignment.py` and `vfe_efe_bridge.py` derive read-only
views.

Build: `uv run python scripts/build_curriculum.py`.
Parent guide: [`../AGENTS.md`](../AGENTS.md). Architecture:
[`../../docs/architecture.md`](../../docs/architecture.md).
