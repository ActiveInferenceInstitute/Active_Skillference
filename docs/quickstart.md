# Quick Start Guide

## The one-command path

```bash
./run.sh
```

That is the whole cold start: it installs the environment, builds the curriculum and every
generated artifact, brings up SkillTree, and serves the learner surface at
`http://127.0.0.1:8765`, printing a signposted tour of the five views and the keyboard and
screen-reader affordances. Use `./run.sh --offline` when Docker is unavailable and
`./run.sh --check` to test readiness without starting anything. The step-by-step commands
below are what `run.sh` runs, for when you want to drive them individually.


Get Active Skillference running in 5 minutes: validate the curriculum DAG, run the
kernels that produce every claim, export a provenance-gated SkillTree project, and run
the test suite.

## Prerequisites

- Python 3.10 or higher (the dev environment is 3.12).
- [`uv`](https://github.com/astral-sh/uv) package manager.
- Docker is **only** needed for the optional live-SkillTree step at the end.

All commands below run from the **project root**
(`.../working/Active_Skillference/`).

## Setup (one-time)

```bash
# Install dependencies into a local virtualenv
uv sync

# Verify
uv run python --version
```

## 1. Build and validate the curriculum DAG

```bash
uv run python scripts/build_curriculum.py
```

This assembles the Active Inference curriculum from `src/curriculum/catalog_data/` and the
`src/curriculum/_ext_*.py` extension modules it aggregates (via the `catalog.py` entry
point) and validates it (acyclic, no dangling prerequisites, roots only in foundational strata,
connected foundations→applications, and the learner-quality gate). It prints live
headline stats and writes `output/data/curriculum_stats.json` plus
`output/data/curriculum_diagnostic_gap_map.json`:

```
curriculum valid: <skills> skills / <subjects> subjects / <prerequisite edges> prerequisite edges
strata present: 8/8 (all=True), max depth <depth>, connected foundations→applications=True
```

A cycle, a dangling prerequisite, or a non-foundational root makes this script raise —
the DAG never silently degrades.

## 2. Run the kernels and render figures

```bash
uv run python scripts/run_kernels.py
```

This runs the tested computational kernels (`src/kernels/`), registers their results as
provenance claims, validates scholarship coverage, **fails closed** if any
`{{claim:NAME}}` token in the curriculum or the manuscript is unbacked, renders figures,
and validates that generated figure labels/files match the manuscript and dashboard before
it writes:

- `output/data/claims.json` — the provenance ledger (every claim, value, units, source).
- `output/data/manuscript_variables.json` — claims + headline curriculum counts.
- `output/data/curriculum_diagnostic_gap_map.json` — bottlenecks, long chains, assessment balance, and remediation queue rows.
- `output/data/scholarship_coverage.json` — citation lane/source-role coverage.
- `output/data/scholarship_source_health.json` — source locator and role-quality audit.
- `output/data/scholarship_source_health_network.json` — dead-link, bot-block, role-gap, boundary-source, and uncited-drift buckets.
- `output/data/scholarship_gap_report.json` — remaining frontier/boundary support gaps.
- `output/data/figure_table_companions.json` — table companions for dense figure cards.
- `output/data/manuscript_claim_support.json` — anchored scientific-claim evidence audit.
- `output/data/manuscript_artifacts.json` — figure registry / manuscript / dashboard drift audit.
- `output/data/cover_asset_audit.json` — first-page cover image / dashboard / registry-boundary audit.
- `output/data/front_matter_visual_audit.json` — page-two atlas image / dashboard / registry-boundary audit.
- `output/data/course_material_index.json` — local modular lesson records for dashboard Learn actions, including source/role/match-scope coverage for pinned course and cognitive knowledge-base links.
- `output/data/course_material_audit.json` — completeness audit for course-material records, pointers, and cognitive knowledge-base coverage counts.
- Figures under `output/figures/` (the cover and skill-atlas are front-matter assets, not
  numbered registry figures; the rest are the generated, registry-tracked figures):
  - `active_skillference_cover.png` — deterministic first-page cover asset generated from live project data,
  - `active_skillference_skill_atlas.png` — deterministic page-two named-skill atlas generated from every skill name,
  - `curriculum_dag.png` — the annotated prerequisite graph laid out by stratum × depth,
  - `dependency_strata_flow.png` — a source/target stratum matrix for prerequisite edges,
  - `graph_bottlenecks.png` — high-impact dependency bottlenecks,
  - `skill_neighborhood_paths.png` — a representative long prerequisite path with a checkpoint ledger,
  - `semantic_prerequisite_coverage.png` — semantic-prerequisite concept-reachability audit,
  - `assessment_depth_matrix.png` — quiz floor-pass audit by stratum,
  - `curriculum_stratum_balance.png` — raw and normalized stratum-level expansion balance,
  - `scholarship_coverage.png` — citation coverage by source lane and manuscript section,
  - `open_science_source_map.png` — cited and linked Institute learning-source ledger with cognitive knowledge-base pointer coverage,
  - `scholarship_source_health.png` — scholarship locator and support-role status ledger,
  - `validation_surface_matrix.png` — validation gates by artifact and release-documentation surface,
  - `validation_intent_mismatch_matrix.png` — mismatch classes release gates must reject,
  - `visual_evidence_contract_ladder.png` — visual-evidence chart-contract ladder,
  - `scientific_evidence_matrix.png` — claim-support evidence classes by manuscript claim type,
  - `roadmap_risk.png` — roadmap state by release surface and blocker class,
  - `free_energy_descent.png` — a supplemental VFE belief sweep with the posterior
    minimum,
  - `efe_decomposition.png` — supplemental sample/commit EFE plus a sensor-precision
    regime sweep,
  - `planning_lookahead.png` — supplemental multi-step planning look-ahead,
  - `predictive_coding_descent.png` — supplemental continuous predictive-coding descent,
  - `kernel_sensitivity_profiles.png` — supplemental base-rate, bound-tightness and
    policy-regime sensitivity profiles,
  - `vfe_efe_skilltree_bridge.png` — supplemental bridge from VFE/EFE figures to real
    SkillTree subjects, skills, prerequisite edges, quizzes and routes.
- `output/figures/figure_registry.json` — the generated figure label, metadata, optional companion id, and filename registry.

It prints the live provenance-claim count, then `validated scholarship coverage`,
`validated manuscript artifacts`, `validated cover asset`, `validated page-two visual`,
`validated American English manuscript language`, `validated manuscript claim support`,
`validated scholarship gap report`, and `validated course materials`, followed by each
output path.

## 3. Export a SkillTree project (provenance-gated)

```bash
uv run python scripts/export_skilltree.py
uv run python scripts/validate_course_material_alignment.py
```

This builds + validates the DAG, builds the claim registry, runs the provenance gate
(every claim token must resolve; the linter must find no bare result numbers), resolves
every `{{claim:NAME}}` token into skill content, and writes a SkillTree-native project
JSON to `output/data/skilltree_project.json`. If any token is unbacked, `render_graph`
raises and **nothing is written**.
The alignment validator then checks that the exported skills, local course-material
records, learning-path prerequisites, handoff routes, and generated quiz definitions all
describe the same curriculum.

It prints, e.g.:

```
exported SkillTree project 'Active Skillference' (<skills> skills, <dependencies> dependencies)
```

## 4. Run the test suite

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
```

Expected: all tests pass with zero mocks and `src/` line coverage at or above the 90%
gate. The coverage command is the source of truth for the current test count and
percentage.

The discrete active-inference agent's generative model is also specified in
[`../gnn/discrete_active_inference_agent.gnn.md`](../gnn/discrete_active_inference_agent.gnn.md)
(Generalized Notation Notation). With the pinned GNN checkout available (`GNN_ROOT`, or the
sibling clone), `uv run python scripts/validate_gnn_spec.py` re-parses that specification
with the pinned GNN parser and checks it against the kernel; without the checkout the
script exits `2` and the pytest module runs its structural half only.

## View results

- **Claims ledger**: `output/data/claims.json`
- **Scholarship coverage**: `output/data/scholarship_coverage.json`
- **Scholarship source health**: `output/data/scholarship_source_health.json`
- **Scholarship health network**: `output/data/scholarship_source_health_network.json`
- **Manuscript artifact audit**: `output/data/manuscript_artifacts.json`
- **Course material index**: `output/data/course_material_index.json`
- **Curriculum stats**: `output/data/curriculum_stats.json`
- **Curriculum diagnostics**: `output/data/curriculum_diagnostic_gap_map.json`
- **Figure table companions**: `output/data/figure_table_companions.json`
- **SkillTree project**: `output/data/skilltree_project.json`
- **Figures**: `output/figures/` (DAG, flow, diagnostics, scholarship, validation, roadmap, and kernel examples)
- **PDF write-up** (if rendered): `output/pdf/Active_Skillference_combined.pdf`

## Optional: a live, gamified SkillTree instance (requires Docker)

```bash
./scripts/run_skilltree.sh   # docker compose up (skills-service + Postgres) + seed
# then open http://localhost:8080
```

`run_skilltree.sh` starts the SkillTree containers, waits for the REST API, then calls
`scripts/bootstrap_local_skilltree.py`. In the pinned local `FORM` auth mode, that
bootstrap path creates/reuses local admin state, seeds the project, and verifies the
trusted-client token exchange for `local-learner`.
Standalone `seed_skilltree.py` invocations skip cleanly when no server is listening, so
the render pipeline remains usable without Docker. See
[`../vendor/README.md`](../vendor/README.md) for the Docker and build-from-source paths.
Set `ACTIVE_SKILLFERENCE_LOCAL_AUTH=0 SKILLTREE_TOKEN=...` only when targeting a
deployment that already supports bearer-token admin writes.

## Optional: local learner dashboard (requires Docker for live progress)

```bash
./scripts/run_learning_dashboard.sh
# then open http://127.0.0.1:8765
```

This starts the same Docker SkillTree runtime, regenerates the curriculum/provenance
artifacts, seeds `activeInference`, and serves a local no-build dashboard. The dashboard
bootstraps local SkillTree auth, exposes `/api/skilltree/token` as a server-side
trusted-client bridge, opens **Learn** actions as local modular lesson records, and
mounts the official SkillTree client display as the fixed local learner `local-learner`.
It does not store ranking, progress, self-reporting, or quiz state; those remain
SkillTree-owned. The page paints from `/api/status?defer_live=1` and swaps in the live
dependency-parity result when it lands, so scripts that need the parity check must call
`/api/status` without `defer_live`.
See [`learner_dashboard.md`](learner_dashboard.md) for the full route map.

For an artifact-only check without Docker:

```bash
uv run python scripts/serve_learner_dashboard.py --check
uv run python scripts/serve_learner_dashboard.py
```

## Common next steps

- **Add a skill**: append a `_s(...)` entry to the appropriate stratum file under
  `src/curriculum/catalog_data/` with a unique
  `skill_id`, a stratum, an objective, a description (claim tokens for any numbers), the
  quality-gated minimum `_q(...)` assessments, and prerequisites that already exist.
  Re-run step 1.
- **Add a computed value**: add a worked example to `src/kernels/examples.py`, register
  its claim, and reference it via `{{claim:NAME}}` in the curriculum. Re-run steps 2–3.
- **See the manuscript flow**: [`rendering_pipeline.md`](rendering_pipeline.md).

## Getting help

- **Docs hub**: [`README.md`](README.md)
- **Agent rules**: [`agent_instructions.md`](agent_instructions.md)
- **Architecture**: [`architecture.md`](architecture.md)
- **Troubleshooting**: [`troubleshooting.md`](troubleshooting.md)

## Quick command reference

| Task | Command (from project root) |
|---|---|
| Install deps | `uv sync` |
| Build + validate DAG | `uv run python scripts/build_curriculum.py` |
| Run kernels + figures | `uv run python scripts/run_kernels.py` |
| Build local course materials | `uv run python scripts/build_course_materials.py` |
| Validate course-material sources | `uv run python scripts/validate_course_material_sources.py --online` |
| Validate material/quiz alignment | `uv run python scripts/validate_course_material_alignment.py` |
| Validate manuscript artifacts | `uv run python scripts/validate_manuscript_artifacts.py` |
| Export SkillTree JSON | `uv run python scripts/export_skilltree.py` |
| Validate the GNN agent spec (needs the pinned GNN checkout) | `uv run python scripts/validate_gnn_spec.py` |
| Run tests + coverage | `uv run pytest tests/ --cov=src --cov-fail-under=90` |
| Live SkillTree + seed (Docker) | `./scripts/run_skilltree.sh` |
| Live SkillTree + learner dashboard (Docker) | `./scripts/run_learning_dashboard.sh` |
| Serve artifact dashboard only | `uv run python scripts/serve_learner_dashboard.py` |
| Seed a running instance | `uv run python scripts/seed_skilltree.py --base-url http://localhost:8080` |
| Clean outputs | `rm -rf output/` |
