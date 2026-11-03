# `src/curriculum/catalog_data/` — authored curriculum data

`assembly.py` exposes the thin `build_subject_list()`. `core_strata.py` holds
the inline stratum tuples; `subjects_canopy.py` shapes the subject tree. The
`subjects_extensions_*.py` modules aggregate the `_ext_*.py` extension modules
that sit one level up in [`..`](..).

This is the directory to edit when adding or changing a skill. `_s` and `_q`
come from [`../authoring.py`](../authoring.py); graph validation stays in
[`../graph.py`](../graph.py).

Build: `uv run python scripts/build_curriculum.py`.
Parent guide: [`../AGENTS.md`](../AGENTS.md).
