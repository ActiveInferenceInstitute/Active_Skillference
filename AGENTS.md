# AGENTS.md — Active_Skillference

Guidance for agents working in this project. It is a high-integrity micro-learning
platform for Active Inference / the Free Energy Principle, built on standard
thin-orchestrator (`src/` logic, `scripts/` I/O) conventions and targeting the
SkillTree framework.

## Architecture (thin-orchestrator)

All logic lives in `src/`; `scripts/` only coordinate I/O. Layers, bottom-up:

1. `src/kernels/` — pure, tested math (information theory, distributions, Bayesian +
   variational inference, a discrete active-inference agent). The **only** source of
   quantitative values. Deterministic; nats units.
2. `src/provenance/` — `ClaimRegistry` (kernels register named claims) and `binding`
   (resolve `{{claim:NAME}}` tokens, fail closed on unbacked tokens, lint bare numbers).
3. `src/scholarship/` — citation source-role coverage over `manuscript/references.bib`
   and `data/scholarship_sources.yaml`.
4. `src/manuscript/` — figure registry / manuscript / dashboard artifact validation.
5. `src/curriculum/` — typed `Stratum`/`Subject`/`Skill`/`AssessmentQuestion`, the
   `CurriculumGraph` DAG engine (validate/topo/levels/connectivity), thin `catalog.py`
   entry plus `catalog_data/` assembly, `normalize.py` / `assessment_normalize.py`,
   and `materials/` for local Learn records.
6. `src/skilltree/` — `exporter` (graph → SkillTree project), `client` (admin/report REST),
   `transport`/`admin_ops` (shared HTTP), `form_login_core`/`form_login_validation`
   (browser FORM proof helpers), `seeder` (dependency-safe creation order).
7. `src/figures/` — `plots/` package (deterministic figures, `FigureRenderContext`,
   `render_all`), registry loaders, table companions.
8. `src/integration/` — live-stack orchestration (`full_app_stack.py`) for Docker +
   SkillTree + dashboard proofs.
9. `src/dashboard/` — read-only local learner dashboard shell over generated artifacts
   and official SkillTree views. It must not become a second SkillTree implementation
   or an app-owned authentication layer. Its static frontend is vanilla HTML/CSS/JS and
   follows the project root `DESIGN.md` token contract.
10. `src/pilot/` — protocol-only learner-pilot contract validation. It defines privacy,
    read-only SkillTree exports, feasibility outcomes, and missing-data handling without
    storing learner state or making efficacy claims.

## Invariants (do not break)

- **Provenance.** Never hand-type a result number into skill content. Compute it in
  `src/kernels/examples.py`, register a claim, and reference `{{claim:NAME}}`. Input
  numbers in prose go inside `$…$` LaTeX math; the linter flags bare decimals.
- **DAG.** The curriculum must stay acyclic, fully connected foundations→applications,
  with prerequisites resolving and roots only in the two foundational strata. Run
  `scripts/build_curriculum.py` after edits.
- **Scholarship.** Every authored citation must resolve to a BibTeX entry and a
  source-role row in `data/scholarship_sources.yaml`. Run
  `scripts/analyze_scholarship.py` after citation edits.
- **Manuscript artifacts.** Generated figure labels/files, manuscript declarations and
  cross-references, and dashboard figure artifact links must agree. Run
  `scripts/validate_manuscript_artifacts.py` after figure-label or dashboard-artifact edits.
- **Imports.** Everything imports under the `src.*` namespace (e.g.
  `from src.curriculum.model import Skill`). Do not reintroduce bare `kernels.`/
  `skilltree.`/`curriculum.` imports — they create dual module identities under the
  `pythonpath=[".", "src"]` config.
- **No mocks.** HTTP is tested with `pytest-httpserver`; everything else with real data.
- **GNN specification.** The discrete agent kernel's generative model is specified in
  `gnn/discrete_active_inference_agent.gnn.md` (Generalized Notation Notation) and
  validated against the GNN revision pinned in `gnn/upstream.json`, read from that pinned
  commit via `git archive`, never from the GNN checkout's working tree. Keep the
  specification and `src/kernels/active_inference.py` in step: changing either means
  updating `src/gnn_conformance.py` and `tests/test_gnn_conformance.py` in the same
  change. CI runs `scripts/validate_gnn_spec.py` and the conformance tests in the
  `gnn conformance (pinned)` job, which fetches the pinned revision from the
  public upstream repository and provisions its interpreter, so the pin is re-checked on
  every push and pull request. GNN's [downstream adoption
  guide](https://github.com/ActiveInferenceInstitute/Generalized_Notation_Notation/blob/main/docs/gnn/integration/downstream_adoption.md)
  documents the adoption patterns, pin discipline, and drift-guard checks this invariant
  implements.
- **Coverage.** `src/` ≥ 90%; kernels should remain fully covered.
- **Dashboard design system.** Dashboard UI changes must read `DESIGN.md` first, use
  declared CSS tokens, keep payload shapes unchanged, and prove browser-facing behavior
  through the local dashboard surface.

## Gates (run before declaring done)

```bash
uv run pytest --cov=src --cov-fail-under=90
uvx ruff check src scripts tests && uvx ruff format --check src scripts tests
uv run mypy src
uv run python scripts/validate_gnn_spec.py  # needs the pinned GNN checkout (GNN_ROOT)
```

## Extending the curriculum

Adding a skill is a data edit in `catalog_data/` (e.g. `core_strata.py`): append a
`_s(...)` with a unique `skill_id`, a stratum, an objective, a description (claim tokens
for any numbers), the quality-gated minimum `_q(...)` assessments, and prerequisites that
already exist. If the skill shows a
new computed value, add a worked example in `src/kernels/examples.py`, register the claim,
and reference it. `build_curriculum()` re-validates on every build.

## SkillTree

Data model: `Project → Subject → Skill`; prerequisites become learning-path
**dependencies**; assessments become **quizzes**; completion is `Quiz`-gated. The REST
contract is mirrored by `tests/test_skilltree_client.py`. Live bring-up: see
[`vendor/README.md`](vendor/README.md) (Docker or build-from-source). The local learner
dashboard is a shell around this runtime: progress, ranking, quizzes, and learner state
remain owned by SkillTree.

## Provenance chain (auditable)

kernel fn → `examples.register(...)` → `{{claim:NAME}}` in a skill → `render`/`export`
(fail-closed) → SkillTree skill description + `output/data/claims.json`. Generated figures
also write `figure_registry.json`, and `src.manuscript.audit` checks that registry against
the manuscript and dashboard surfaces.
