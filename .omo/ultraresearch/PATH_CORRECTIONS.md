# Historical path corrections (2026-07-05)

Wave notes under `20260620-*` predate the thermo-nuclear refactor. When reading archived
synthesis files, map stale paths as follows:

| Archived reference | Current location |
| --- | --- |
| `src/pipeline/full_app_stack.py` | `src/integration/full_app_stack.py` |
| `src/curriculum/materials.py` | `src/curriculum/materials/` package |
| `src/figures/plots.py` | `src/figures/plots/` package |
| `catalog_data/assembly.py` (monolith) | `assembly.py` + `subjects_canopy.py` + `subjects_extensions*.py` |

Coverage counts and test totals in archived evidence files are snapshots only; re-run
`uv run pytest --cov=src --cov-fail-under=90` for live figures.
