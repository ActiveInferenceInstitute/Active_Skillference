# docs/ — Agent-Facing Documentation Hub

## Overview

Technical index for `Active_Skillference/docs/` — the operational guide for AI agents
and developers working on this project. Active Skillference is a high-integrity
micro-learning platform for Active Inference (AIF) and the Free Energy Principle (FEP):
it renders the AIF/FEP body of knowledge as a *validated prerequisite DAG* with live
counts written by `scripts/build_curriculum.py`, covering all 8 strata and exporting to the
[SkillTree](https://skilltreeplatform.dev) framework, where every learner-facing number
is produced by a tested kernel and every cited source is mapped to a scholarship lane.
Generated figures are also audited against manuscript labels/cross-references and the
dashboard artifact inventory.

This folder is documentation, but its top-level inventories are still checked by
`tests/test_docs_inventory.py`. Treat the prose as an audit surface: drift here silently
misleads future contributors even when the code gates are green.

## File inventory

| File | Purpose |
|---|---|
| `README.md` | Quick navigation and audience-targeted entry points for this folder |
| `AGENTS.md` | This index — technical overview of `docs/` + verification commands |
| `quickstart.md` | 5-minute first-run walkthrough (build → kernels → export → test) |
| `learner_dashboard.md` | Local learner dashboard route map, SkillTree ownership boundary, offline behavior |
| `architecture.md` | Thin-orchestrator flow: the `src/` layers, dependency direction, how to add a skill/subject/kernel |
| `agent_instructions.md` | Behavioral invariants for agents (provenance, DAG, `src.*` imports, no mocks, coverage) + checklist |
| `testing_philosophy.md` | Zero-mock policy; coverage mechanics; test-file inventory |
| `syntax_guide.md` | Markdown/LaTeX in skill + manuscript content; the `{{claim:NAME}}` token system; figure references |
| `rendering_pipeline.md` | Manuscript → PDF flow; preflight; claim-token substitution |
| `scholarship_coverage.md` | Citation source-role matrix, validator, outputs, and edit protocol |
| `pilot/` | Protocol-only learner-pilot contract, privacy boundary, export schema, and analysis sequence |
| `ip_license_status.md` | MIT declaration, third-party boundaries, DOI/public-repository blockers, and deployment review caveats |
| `publication_readiness.md` | Initial static publication readiness, allowed claims, and release blockers |
| `release_readiness_inventory.md` | Machine-checked dirty worktree, untracked-file, generated-output and blocker inventory for release isolation |
| `todo/` | Generated active roadmap handoff folder with one scoped Markdown page per open TODO |
| `curriculum_expert_audit.md` | Deterministic expert-review sample over high-depth, high-fanout and templated curriculum surfaces |
| `style_guide.md` | Source-code rules: zero-mock, thin orchestrator, `src.*` imports, type hints, error messages |
| `output_conventions.md` | `output/` directory layout and regeneration |
| `output_inventory.md` | Producer/consumer graph for pipeline artifacts |
| `forking_guide.md` | Adapting the platform to a new curriculum domain |
| `troubleshooting.md` | Symptom-driven recipes for common failures |
| `faq.md` | Frequently asked questions: provenance, DAG, SkillTree |

## Key conventions

> These invariants are summarized here for a quick orientation; the authoritative,
> complete rules live in [agent_instructions.md](agent_instructions.md), with the
> repo-root [`../AGENTS.md`](../AGENTS.md) as the top-level landing page.

**Provenance over assertion.** Learner-facing numbers reach skill content, figures, and
the manuscript only through `{{claim:NAME}}` tokens that resolve to values registered by
a tested kernel in `src/kernels/examples.py`. `src/provenance/binding.py` resolves the
tokens (`render` / `render_graph`), fails closed on any unbacked or malformed token
(`validate_curriculum`, `validate_manuscript_dir`), and lints bare result numbers out of
prose (`lint_graph`). A hand-typed result number is a defect the linter flags.

**A validated DAG.** `src/curriculum/graph.py::CurriculumGraph.validate()` enforces:
unique skill ids, no duplicate or dangling prerequisites, no self-loops, roots only in
foundational strata, and acyclicity (three-colour DFS). `is_connected_foundations_to_applications()`
confirms every applications skill traces back to a foundational root. Run
`scripts/build_curriculum.py` after any catalog edit.

**Scholarship coverage.** `src/scholarship/coverage.py` checks authored manuscript
citations against `manuscript/references.bib` and `data/scholarship_sources.yaml`. Every
cited key needs a source-role matrix row with a lane, kind, locator, and role. Run
`scripts/analyze_scholarship.py` after citation edits. `src/scholarship/gap_report.py`
adds a frontier-source report so added formal-provenance, knowledge-space, pedagogy,
assessment, design-based-evaluation, reproducibility, open-science, security,
accessibility, and course-material-provenance sources are bound to explicit
claim-support classes instead of merely increasing the bibliography.

**Manuscript artifact coverage.** `src/manuscript/audit.py` checks
`output/figures/figure_registry.json` against manuscript figure declarations,
`[@fig:...]` references, readable nonblank PNGs, caption/alt-text specificity, semantic
metadata, claim tokens, and dashboard figure artifacts. Run
`scripts/validate_manuscript_artifacts.py` after changing a figure label, figure output,
or dashboard artifact entry.

**Claim support.** Anchored manuscript claims in `manuscript/*.md` must have rows in
`data/manuscript_claim_support.yaml`. Run `scripts/validate_claim_support.py` after
changing scientific wording, citations, figure references, or limitation language.

**The `src.*` namespace.** All imports are `from src.<package> ...`. Bare
`kernels.`/`curriculum.`/`skilltree.`/`provenance.`/`figures.` imports are forbidden:
under `pythonpath = [".", "src"]` they create a second module identity for the same file
(the dual-identity hazard), so type checks and registry comparisons silently break.

**Thin orchestrator.** All logic lives in `src/`; `scripts/` only coordinate I/O. The
scripts that exist are `00_preflight.py`, `analyze_scholarship.py`,
`audit_scholarship_gaps.py`,
`build_curriculum.py`, `build_course_materials.py`, `run_kernels.py`,
`validate_american_english.py`, `validate_claim_support.py`,
`validate_course_material_alignment.py`, `validate_course_material_sources.py`,
`capture_dashboard_screenshots.py`, `reserve_zenodo_doi.py`, `publish_zenodo_deposit.py`, `validate_dashboard_console.py`, `validate_docker_digests.py`,
`validate_full_app_stack.py`, `validate_gnn_spec.py`, `validate_skilltree_form_login.py`, `validate_live_counts.py`,
`validate_live_skilltree_dashboard.py`, `validate_manuscript_artifacts.py`,
`validate_manuscript_variables.py`, `validate_rendered_freshness.py`,
`validate_roadmap.py`, `validate_release_readiness_inventory.py`,
`validate_learner_pilot_contract.py`, `validate_scholarship_sources.py`, `ensure_web_math.py`,
`validate_web_math.py`, `export_skilltree.py`, `seed_skilltree.py`,
`bootstrap_local_skilltree.py`, `reconcile_live_dependencies.py`,
`reset_local_skilltree.py`, `z_generate_manuscript_variables.py` (the
provenance-resolved manuscript render hook), `serve_learner_dashboard.py`,
`run_skilltree.sh`, and `run_learning_dashboard.sh`.

**Zero mocks.** No `unittest.mock`, `MagicMock`, `@patch`, or `create_autospec` in
`tests/`. Real numpy data everywhere; the SkillTree REST client is tested against a real
local server with `pytest-httpserver` (`tests/test_skilltree_client.py`). Mock tests can
pass while the math is wrong.

**Coverage ≥90%.** `pyproject.toml` gates `src/` coverage at 90%; use the coverage run
as the source of truth for the current test count and percentage.

**Roadmap surfaces.** `tasks.yaml` is the canonical roadmap/history source.
`TODO.md` is generated, forward-only, and links each active item to a generated
`docs/todo/<task-id>.md` implementation handoff page. Refresh both surfaces with
`uv run python scripts/validate_roadmap.py --write-todo`; do not edit them by hand.

## Reading order

1. **`agent_instructions.md`** + the project root [`../AGENTS.md`](../AGENTS.md) — the invariants and the verification checklist.
2. **`architecture.md`** — the `src/` layers and dependency direction before touching file structure.
3. **`testing_philosophy.md`** — the zero-mock constraint and test inventory before writing tests.
4. **`syntax_guide.md`** — the `{{claim:NAME}}` token system before editing skill or manuscript content.
5. **`rendering_pipeline.md`** — the manuscript → PDF flow before editing manuscript or output paths.
6. **`style_guide.md`** — the source-code rules before writing Python.

## Verification commands

Run all four from the project root before submitting any change:

```bash
# Test suite passes + coverage ≥90% on src/
uv run pytest tests/ --cov=src --cov-fail-under=90 -q

# No mocks in tests/
grep -r "unittest.mock\|MagicMock\|@patch\|create_autospec" tests/ || echo "Clean"

# All imports under the src.* namespace
grep -rnE "^(from|import) (kernels|curriculum|skilltree|provenance|figures)\b" src/ scripts/ tests/ \
    && echo "VIOLATION — bare import" || echo "Clean — src.* only"

# DAG validates + provenance-gated export succeeds
uv run python scripts/build_curriculum.py
uv run python scripts/export_skilltree.py
```

## Source layout reference

| Path | Role |
|---|---|
| `src/kernels/` | Tested math — the only source of quantitative values (`information.py`, `distributions.py`, `inference.py`, `active_inference.py`, `predictive_coding.py`, `examples.py`) |
| `src/provenance/` | `ClaimRegistry` (`claims.py`) + token binding / fail-closed validation / linter (`binding.py`) |
| `src/scholarship/` | Citation source-role matrix validation, source-health checks, and scholarship gap-report JSON audit generation |
| `src/manuscript/` | Generated figure registry / manuscript / dashboard artifact validation |
| `src/curriculum/` | Typed model (`model.py`), DAG engine (`graph.py`), catalog assembly (`catalog_data/`), quality normalization (`normalize.py`, `assessment_normalize.py`), and local course-material records (`materials/`) |
| `src/skilltree/` | SkillTree model, shared export summaries, exporter, REST transport/admin ops, `form_login_core` / `form_login_validation`, seeder |
| `src/figures/` | Deterministic figure renderers (`plots/`) plus typed registry loader and registry manifest |
| `src/dashboard/` | Local learner dashboard over generated artifacts, reusable live validation, local token bridge, and official SkillTree views |
| `src/integration/` | Live-stack orchestration (`full_app_stack.py`) for Docker + SkillTree + dashboard proofs |
| `src/pipeline/` | Importable multi-artifact pipelines invoked by thin scripts such as `run_kernels.py` |
| `src/artifacts/` | Shared deterministic JSON artifact read/write helpers |
| `src/project_paths.py` | Project root + `output/` directory resolution |
| `scripts/` | Thin orchestrators (see list above) |
| `tests/` | Zero-mock test suite (every `test_*.py` in `tests/`, e.g. `test_kernels_*`, `test_curriculum_*`, `test_skilltree_*`, `test_dashboard*`, `test_pilot_contract`, `test_net_guard`, `test_full_app_stack`, `test_publication_readiness`, `test_release_readiness_inventory`, `test_pipeline_generated_outputs`, `test_docs_inventory`, `test_figures`, `test_roadmap`, `test_scripts_smoke`, `test_course_materials`, `test_claim_support`) |
| `manuscript/` | The platform write-up rendered to PDF (`{{claim:NAME}}` tokens substituted) |
| `vendor/` | Runnable SkillTree instance wiring (`vendor/README.md`) |

## Generated figures

`src/figures/plots/` produces deterministic cover/page-two front-matter assets plus
registered figures, all driven by the registry/graph (headless `Agg` backend):

- `active_skillference_cover.png` — first-page cover generated from live graph, claim and
  roadmap data; it is a cover artifact, not a numbered manuscript figure.
- `active_skillference_skill_atlas.png` — page-two named-skill atlas generated from every
  authored skill name; it is a front-matter artifact, not a numbered manuscript figure.
- `curriculum_dag.png` — the prerequisite graph laid out by stratum × depth, with direct
  stratum/root labels, quiet edges, and invariant callouts.
- `dependency_strata_flow.png` — prerequisite-edge flow between source and dependent
  strata, with row/column totals, skill counts, and a hatched backward-dependency zone.
- `assessment_depth_matrix.png` — quiz floor-pass audit table/bar hybrid by stratum.
- `curriculum_stratum_balance.png` — raw stratum-level expansion counts plus normalized
  per-subject and per-skill companion measures.
- `free_energy_descent.png` — a supplemental VFE sweep over `q(present)` showing the
  exact posterior minimum against the negative log-evidence line.
- `efe_decomposition.png` — supplemental sample/commit expected free energy plus a
  sensor-precision sweep showing the regime boundary.
- `planning_lookahead.png` — supplemental multi-step planning look-ahead: the measured
  greedy-vs-optimal gain in a decoupled model (zero) beside a coupled investment model
  (positive), plus per-policy expected free energy with the greedy and optimal plans marked.
- `predictive_coding_descent.png` — supplemental continuous predictive-coding descent:
  the latent estimate settling to the analytic precision-weighted posterior beside the
  monotonically descending free energy.
- `vfe_efe_skilltree_bridge.png` — supplemental bridge from VFE/EFE worked examples to
  real SkillTree subjects, skills, prerequisite edges, learn routes and quiz routes.
- `graph_bottlenecks.png` / `skill_neighborhood_paths.png` — graph diagnostic views for
  high fan-out skills and a representative long prerequisite path with a checkpoint ledger.
- `semantic_prerequisite_coverage.png` — semantic-prerequisite lollipop audit showing
  concept reachability versus assessed concept use.
- `kernel_sensitivity_profiles.png` — supplemental base-rate, VFE-bound, and EFE-regime
  sensitivity panels.
- `scholarship_coverage.png` — citation source coverage by scholarship lane and
  manuscript section.
- `open_science_source_map.png` — Active Inference Institute learning-source ledger
  combining scholarship support rows with generated course-material and cognitive
  knowledge-base pointer coverage.
- `scholarship_source_health.png` — locator and source-role health status ledger.
- `validation_surface_matrix.png` — validation gates by artifact and release-documentation
  surface plus live evidence counts.
- `validation_intent_mismatch_matrix.png` — mismatch classes that release gates must
  reject.
- `visual_evidence_contract_ladder.png` — visual-evidence authoring path from chart
  question contract through data grain, encoding, annotation, static/mobile survival, and
  negative-control validation.
- `scientific_evidence_matrix.png` — evidence-class matrix for anchored manuscript claims.
- `roadmap_risk.png` — roadmap status, external blockers, git-authorization hygiene and live metrics.
- `figure_registry.json` — labels, filenames, captions, semantic metadata, structured chart-contract fields (`question`, `takeaway`, `data_sources`, `data_grain`, `encoding`, `palette_policy`, `palette_roots`, `non_color_encoding`, `static_read`, `mobile_read`, `failure_mode`), claim tokens, and generators for the figure
  artifact validator. The cover must not appear in this registry.

Figure code produces the PNG and chart contract; the registry stores it; manuscript prose
declares and references it; the dashboard exposes the same fields in artifact detail
cards with a full-size image link and grouped Question / Grain / Boundary / Failure
metadata; and the artifact validator fails closed on missing or generic chart-contract
metadata. Meaningful figure text uses the shared 9.5px-equivalent floor; 8.5px is
reserved for source/caveat notes.

## Cross-references

- [`README.md`](README.md) — Quick reference with audience-targeted entry points.
- [`../README.md`](../README.md) — Project overview and quick start.
- [`../AGENTS.md`](../AGENTS.md) — Project-level agent guidance and the auditable provenance chain.
- [`../ISA.md`](../ISA.md) — The Ideal State Artifact (problem, principles, criteria, verification).
- [`../pyproject.toml`](../pyproject.toml) — Coverage gate, pytest options (`pythonpath = [".", "src"]`), dependencies.
- [`../manuscript/AGENTS.md`](../manuscript/AGENTS.md) — Manuscript directory rules and the `{{claim:NAME}}` protocol.
- [`../vendor/README.md`](../vendor/README.md) — Live SkillTree instance (Docker / build-from-source).
