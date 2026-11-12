# AGENTS.md - scripts/

Thin orchestrators for Active Skillference live here. Scripts should coordinate
I/O and delegate logic to `src/`; do not place curriculum, kernel, provenance, or
SkillTree business logic in this directory.

## Current Scripts

| Script | Role | Main source surface |
| --- | --- | --- |
| `build_curriculum.py` | Validate the curriculum DAG and print graph stats | `src/curriculum/` |
| `analyze_scholarship.py` | Validate citation source coverage and render scholarship audit artifacts | `src/scholarship/`, `src/figures/`, `data/scholarship_sources.yaml`, `manuscript/` |
| `run_kernels.py` | Print the generated-output bundle; pipeline logic registers computational claims, validates scholarship, renders deterministic figures, audits manuscript/dashboard figure wiring, and builds local course-material artifacts | `src/pipeline/generated_outputs.py`, `src/kernels/`, `src/provenance/`, `src/scholarship/`, `src/figures/plots/`, `src/manuscript/`, `src/dashboard/`, `src/curriculum/materials/` |
| `build_course_materials.py` | Build local modular lesson records for dashboard Learn actions | `src/curriculum/materials/`, `data/course_material_sources.yaml` |
| `validate_course_material_sources.py` | Validate pinned external course-material sources and optionally verify GitHub paths online | `src/curriculum/materials/`, `data/course_material_sources.yaml` |
| `validate_course_material_alignment.py` | Validate exported skills, local course materials, learning paths, and quizzes agree | `src/curriculum/alignment.py`, generated SkillTree/course-material artifacts |
| `validate_manuscript_artifacts.py` | Re-check figure registry, manuscript labels/cross-references, PNG information content, captions, alt text, and dashboard figure artifacts | `src/manuscript/`, `src/dashboard/`, `manuscript/`, `output/figures/` |
| `validate_live_skilltree_dashboard.py` | Re-check local dashboard, SkillTree status, artifact count, local auth, token exchange, figure contracts, and optional live parity | `src/dashboard/live_validation.py`, generated outputs, live dashboard and SkillTree endpoints |
| `validate_full_app_stack.py` | Run the strict Docker + SkillTree + dashboard + browser proof as a CLI wrapper | `src/integration/full_app_stack.py`, generated outputs, live dashboard and SkillTree endpoints |
| `export_skilltree.py` | Export provenance-resolved SkillTree project JSON | `src/skilltree/`, `src/provenance/` |
| `seed_skilltree.py` | Seed a SkillTree server from the exported graph | `src/skilltree/client.py` |
| `bootstrap_local_skilltree.py` | Bootstrap local SkillTree auth and seed with a session client | `src/skilltree/local_auth.py` |
| `serve_learner_dashboard.py` | Serve the local learner dashboard shell and token bridge | `src/dashboard/` |
| `run_skilltree.sh` | Start the Docker-backed SkillTree runtime and seed it | `docker-compose.yml`, `vendor/` |
| `run_learning_dashboard.sh` | Start Docker SkillTree, regenerate/seed, then serve the learner dashboard | `src/dashboard/`, `docker-compose.yml`, `vendor/` |
| `render_manuscript.py` | Authoritative render path: hydrate, assemble, and drive Pandoc → XeLaTeX (PDF) / Pandoc → HTML (web) | `scripts/z_generate_manuscript_variables.py`, `manuscript/`, `output/manuscript/` |
| `check_docs_links.py` | Fail on a relative Markdown link or image that does not resolve | authored `*.md` surfaces |
| `z_generate_gate_metrics.py` | Render or check `docs/gate_metrics.md` from the recorded arm timings | `docs/_generated/arm_timings.json` |
| `validate_gnn_spec.py` | Validate the discrete-agent GNN specification against the pinned GNN revision and the kernel | `gnn/`, `src/gnn_conformance.py` |

## Verification

```bash
uv run pytest tests/test_scripts_smoke.py -q
uv run python scripts/build_curriculum.py
uv run python scripts/analyze_scholarship.py
uv run python scripts/run_kernels.py
uv run python scripts/build_course_materials.py
uv run python scripts/validate_course_material_sources.py --online
uv run python scripts/validate_course_material_alignment.py
uv run python scripts/validate_manuscript_artifacts.py
uv run python scripts/export_skilltree.py
uv run python scripts/validate_gnn_spec.py   # needs the pinned GNN checkout (GNN_ROOT)
uv run python scripts/serve_learner_dashboard.py --check
uv run python scripts/bootstrap_local_skilltree.py --check
```

`tests/test_scripts_smoke.py` subprocess-invokes the core Python scripts and checks that
they emit the expected curriculum, claim, scholarship, manuscript-artifact, and SkillTree
outputs.

## Rules

- Keep script outputs deterministic and under `output/`.
- Keep Docker-dependent live seeding honest: local REST-contract tests are valid
  evidence, but a live SkillTree seed requires Docker availability.
- When a script changes, update `README.md`, `docs/quickstart.md`, and the smoke
  test if the command surface changes.
- The dashboard server is local glue only: progress, ranking, quiz completion, and
  learner records stay inside SkillTree. Local trusted-client secrets stay server-side
  under the ignored state directory and must never enter static assets.

## See Also

- [`README.md`](README.md) - Quick reference for this directory.
- [`../src/AGENTS.md`](../src/AGENTS.md) - Source-code boundaries.
- [`../tests/test_scripts_smoke.py`](../tests/test_scripts_smoke.py) - Script smoke tests.
