# data/ — Static Inputs

A holding place for **static, version-controlled inputs** the project needs.

Active Skillference is generator-driven: generated data artifacts are produced into
`output/data/` by thin orchestrator scripts, not stored here. This directory contains
static source contracts: the scholarship source-role matrix used to validate manuscript
citations, and the course-material pointer matrix used to generate local dashboard Learn
records without copying upstream course prose.

## Static inputs

| File | Consumed by | Role |
| --- | --- | --- |
| `scholarship_sources.yaml` | `src/scholarship/coverage.py`, `scripts/analyze_scholarship.py`, `scripts/run_kernels.py` | Maps every authored citation key to a scholarship lane, source kind, locator, and support role; every row must stay cited |
| `course_material_sources.yaml` | `src/curriculum/materials/`, `scripts/build_course_materials.py`, `scripts/run_kernels.py` | Pins external Active Inference Institute repositories by commit and maps strata/topics to source paths for local dashboard Learn pointers |

## Where the real artifacts live

The canonical provenance ledger and the other derived data are generated under
`output/data/` (regenerable, never hand-edited):

| Generated file | Produced by | Contents |
| --- | --- | --- |
| `output/data/claims.json` | `scripts/run_kernels.py` | **The canonical provenance ledger** — kernel-registered claims (value, units, source) |
| `output/data/manuscript_variables.json` | `scripts/run_kernels.py` | Every claim plus headline curriculum counts for the manuscript |
| `output/data/scholarship_coverage.json` | `scripts/analyze_scholarship.py` / `scripts/run_kernels.py` | Citation lane and source-role coverage audit |
| `output/data/manuscript_artifacts.json` | `scripts/run_kernels.py` / `scripts/validate_manuscript_artifacts.py` | Figure registry, manuscript label/cross-reference, PNG existence, and dashboard figure artifact audit |
| `output/data/course_material_index.json` | `scripts/run_kernels.py` / `scripts/build_course_materials.py` | Local modular lesson records for dashboard Learn actions and pinned external source pointers |
| `output/data/course_material_audit.json` | `scripts/run_kernels.py` / `scripts/build_course_materials.py` | Course-material completeness audit |
| `output/data/curriculum_stats.json` | `scripts/build_curriculum.py` | DAG statistics (skills, subjects, edges, depth) |
| `output/data/skilltree_project.json` | `scripts/export_skilltree.py` | The fully-rendered SkillTree project export (all `{{claim:…}}` tokens resolved) |

If you add another static input here later, document it above and in [`AGENTS.md`](AGENTS.md), and
keep generated CSV/JSON/PNG out of `data/` — those belong under `output/`.

Edit protocol and the provenance model: [`AGENTS.md`](AGENTS.md).
