---
title: "Manuscript directory: Active Skillference"
type: "manuscript_guide"
version: "1.0.0"
---

# Manuscript (`manuscript/`)

Project-wide agent rules live in [`../AGENTS.md`](../AGENTS.md) and
[`../docs/agent_instructions.md`](../docs/agent_instructions.md). This file covers
**manuscript-specific** editing: file roles, the `{{claim:NAME}}` provenance protocol, the
figure protocol, and the section-modification workflow.

## File inventory

| File / pattern | Role |
|---|---|
| `00_abstract.md` | Abstract — Active Skillference as a provenance-bound curriculum artifact |
| `01_introduction.md` | Motivation, situation awareness, evaluation questions, and evidence boundary |
| `02_methodology.md` | Methodology spine and reading order |
| `02a_`-`02c_*.md` | Kernels/statistics/provenance, scholarship/curriculum/strata, and SkillTree/dashboard/publication methods |
| `03_results.md` | Results spine and reading order |
| `03a_`-`03d_*.md` | Graph/assessment, scholarship/evidence, kernel-example, and SkillTree/dashboard/front-matter results |
| `04_conclusion.md` | Discussion, interpretation, limitations, and conclusion |
| `05_experimental_setup.md` | Deterministic models, build gates, and planned learner study |
| `06_reproducibility.md` | Verification gates and artifact inventory |
| `07_scope_and_related_work.md` | Theoretical, platform, and outcome boundaries |
| `07a_`-`07d_*.md` | Platform boundary, AIF/information related work, SkillTree/security/reporting context, and limitations |
| `08_supplement_variational_free_energy.md` | Supplemental VFE/EFE walkthroughs and their kernel-backed figures |
| `99_references.md` | Bibliography pointer + `references.bib` validation |
| `config.yaml` | Paper metadata, render wiring, optional publication profile |
| `config.yaml.example` | Annotated reference copy of the configurable fields |
| `preamble.md` | LaTeX packages injected at render |
| `references.bib` | BibTeX bibliography (Active Inference / information theory) |
| `SYNTAX.md` | Citation, figure, equation, and provenance-token syntax |
| `README.md` | Human quick-reference for this directory |
| `AGENTS.md` | This file — agent technical directives |

## `{{claim:NAME}}` provenance protocol

Result numbers in the manuscript **must** be provenance tokens, never hand-typed. A
hardcoded result that drifts when a kernel changes is the primary cause of an inaccurate
manuscript — and here it fails the build.

**The pipeline** (`scripts/run_kernels.py`):
1. `src/kernels/examples.py::build_claim_registry()` runs the worked examples and registers
   every learner-facing value as a named claim `{name, value, units, source}`.
2. `src/provenance/binding.py::validate_curriculum()` and `validate_manuscript_dir()` fail
   the build **closed** if any `{{claim:NAME}}` token (in a skill *or* in the manuscript)
   has no backing claim, or if a bare result decimal appears in prose outside `$…$` math.
3. The resolved values are written to `output/data/manuscript_variables.json` — every claim
   plus the curriculum counts `skill_count`, `subject_count`, `edge_count`, `max_depth`.
4. `src/manuscript/audit.py` checks `figure_registry.json` against manuscript figure
   declarations, `[@fig:...]` references, readable nonblank PNGs, caption/alt-text
   specificity, and dashboard figure artifacts.
5. The renderer substitutes each `{{claim:NAME}}` / `{{count}}` token with its value.

**Adding a number to the manuscript:**
1. Compute it in `src/kernels/examples.py` and register a claim (unique `NAME`).
2. Reference it in prose as `{{claim:NAME}}` (input parameters go in `$…$` math instead).
3. Re-run `uv run python scripts/run_kernels.py` — it re-validates fail-closed and rewrites
   `manuscript_variables.json`. A dangling or malformed token exits non-zero.

**Detecting unresolved tokens** (before rendering):
```bash
uv run python scripts/run_kernels.py   # exits non-zero on any unbacked/malformed token
```

## Figure protocol

The manuscript references generated figures via Pandoc-crossref `[@fig:label]` — never a
hardcoded number or raw `\ref{}`:

| Label | PNG filename | Generator in `../src/figures/plots/` |
|---|---|---|
| `{#fig:curriculum_dag}` | `output/figures/curriculum_dag.png` | `plot_curriculum_dag()` |
| `{#fig:dependency_strata_flow}` | `output/figures/dependency_strata_flow.png` | `plot_dependency_strata_flow()` |
| `{#fig:graph_bottlenecks}` | `output/figures/graph_bottlenecks.png` | `plot_graph_bottlenecks()` |
| `{#fig:skill_neighborhood_paths}` | `output/figures/skill_neighborhood_paths.png` | `plot_skill_neighborhood_paths()` |
| `{#fig:semantic_prerequisite_coverage}` | `output/figures/semantic_prerequisite_coverage.png` | `plot_semantic_prerequisite_coverage()` |
| `{#fig:assessment_depth}` | `output/figures/assessment_depth_matrix.png` | `plot_assessment_depth_matrix()` |
| `{#fig:stratum_balance}` | `output/figures/curriculum_stratum_balance.png` | `plot_curriculum_stratum_balance()` |
| `{#fig:scholarship_coverage}` | `output/figures/scholarship_coverage.png` | `plot_scholarship_coverage()` |
| `{#fig:open_science_sources}` | `output/figures/open_science_source_map.png` | `plot_open_science_source_map()` with scholarship and course-material coverage payloads |
| `{#fig:scholarship_source_health}` | `output/figures/scholarship_source_health.png` | `plot_scholarship_source_health()` |
| `{#fig:validation_surface_matrix}` | `output/figures/validation_surface_matrix.png` | `plot_validation_surface_matrix()` |
| `{#fig:validation_intent_mismatch_matrix}` | `output/figures/validation_intent_mismatch_matrix.png` | `plot_validation_intent_mismatch_matrix()` |
| `{#fig:visual_evidence_contract_ladder}` | `output/figures/visual_evidence_contract_ladder.png` | `plot_visual_evidence_contract_ladder()` |
| `{#fig:scientific_evidence_matrix}` | `output/figures/scientific_evidence_matrix.png` | `plot_scientific_evidence_matrix()` |
| `{#fig:free_energy}` | `output/figures/free_energy_descent.png` | `plot_free_energy_descent()` |
| `{#fig:efe}` | `output/figures/efe_decomposition.png` | `plot_efe_decomposition()` |
| `{#fig:planning_lookahead}` | `output/figures/planning_lookahead.png` | `plot_planning_lookahead()` |
| `{#fig:predictive_coding}` | `output/figures/predictive_coding_descent.png` | `plot_predictive_coding()` |
| `{#fig:vfe_efe_skilltree_bridge}` | `output/figures/vfe_efe_skilltree_bridge.png` | `plot_vfe_efe_skilltree_bridge()` |
| `{#fig:kernel_sensitivity_profiles}` | `output/figures/kernel_sensitivity_profiles.png` | `plot_kernel_sensitivity_profiles()` |
| `{#fig:roadmap_risk}` | `output/figures/roadmap_risk.png` | `plot_roadmap_risk()` |

A sixth family sits in the same registry but is *captured*, not rendered: the five
learner-dashboard recordings below. They are declared and cross-referenced exactly like
the plots, and are held to the same caption, alt-text, and chart-contract floors, but
they carry `evidence_kind: captured` and `asset_root: manuscript/assets/screenshots`,
are version-controlled rather than generated, are staged into `output/figures/` at build
time so the renderer resolves them, and are exempt from the render/registry parity check
because no generator emits them. Refresh with
`scripts/capture_dashboard_screenshots.py` against a live stack — and refresh them
whenever the dashboard display changes, because no gate detects a stale recording.

| Label | Tracked PNG | Produced by |
|---|---|---|
| `{#fig:app_operational_snapshot}` | `manuscript/assets/screenshots/app_operational_snapshot.png` | `capture_dashboard_screenshots.py` |
| `{#fig:app_official_learner_view}` | `manuscript/assets/screenshots/app_official_learner_view.png` | `capture_dashboard_screenshots.py` |
| `{#fig:app_curriculum_learn_material}` | `manuscript/assets/screenshots/app_curriculum_learn_material.png` | `capture_dashboard_screenshots.py` |
| `{#fig:app_dependency_graph}` | `manuscript/assets/screenshots/app_dependency_graph.png` | `capture_dashboard_screenshots.py` |
| `{#fig:app_runtime_deployment_matrix}` | `manuscript/assets/screenshots/app_runtime_deployment_matrix.png` | `capture_dashboard_screenshots.py` |

Current semantics: the DAG figure uses direct stratum labels, root labels, quiet edge
context, and graph stats; the dependency-flow figure summarizes prerequisite traffic
between strata with row/column totals and a hatched backward-dependency zone; the
assessment figure is a floor-pass audit table/bar hybrid; the stratum-balance figure
pairs raw expansion coverage with normalized per-subject and per-skill load; graph-diagnostic figures expose bottlenecks and a representative long
dependency path; the scholarship, open-science, and source-health figures map citation
support; the validation matrix maps gates to artifact surfaces; the scientific
evidence matrix maps claim-support anchors to evidence classes; the free-energy figure is
a supplemental belief sweep over `q(present)`; the EFE figure is a supplemental
sample/commit comparison with the sensor-precision regime boundary; the kernel
sensitivity figure shows base-rate, VFE-bound, and policy-regime sensitivity; the VFE/EFE
SkillTree bridge maps those supplement figures to real subjects, skills, edges,
learn-route fragments, and quiz-route fragments; the visual-evidence ladder shows the figure-question-to-negative-control
authoring path; the roadmap figure renders `tasks.yaml` state.

Every registered figure must carry a figure-specific chart contract. The plot code writes
the PNG and contract metadata; `figure_registry.json` stores `question`, `takeaway`,
`data_sources`, `data_grain`, `encoding`, `palette_policy`, `palette_roots`,
`non_color_encoding`, `static_read`, `mobile_read`, `failure_mode`, existing semantic fields,
claim tokens, and the generator path; manuscript prose declares and references the figure;
the dashboard artifact card exposes the contract first as Question / Grain / Boundary /
Failure, with encoding and QA details behind a secondary disclosure; and
`src/manuscript/audit.py` rejects missing or generic metadata before release.
Figure producers keep meaningful chart text at or above the shared 9.5px-equivalent
small-label floor and reserve 8.5px text for source/caveat notes. When a figure gets
dense, reduce visible labels, wrap text, add a ledger, or enlarge the layout rather than
shrinking the contract text.

`output/figures/active_skillference_cover.png` is a generated first-page cover asset, not
a manuscript figure. It is an evidence-led front page built from count badges, an
artifact-chain spine, compact stratum/load evidence, VFE/EFE equations, and a provenance
footer. It is configured through `book.cover.image`, audited by `validate_cover_asset`,
exposed in the dashboard as category `cover`, and must stay out of `figure_registry.json`
and figure cross-references.

`output/figures/active_skillference_skill_atlas.png` is the generated page-two atlas, also
not a manuscript figure. It is configured through `front_matter.page_two_visual.image`,
audited by `validate_front_matter_visual`, exposed in the dashboard as category `cover`,
and must stay out of `figure_registry.json` and figure cross-references. It intentionally
shows a reduced readable term sample and representative dependency checkpoints; the
complete name ledger and full dependency chain remain in the generated graph artifacts.

**To add a figure:** add a `plot_*` function to `src/figures/plots/`, wire it into
`render_all()`, add the Pandoc image line in the right section (alt text, relative path
under `../output/figures/`, `{#fig:…}`), reference it in prose, and record it in
[`../docs/output_inventory.md`](../docs/output_inventory.md). Re-run
`uv run python scripts/run_kernels.py` or
`uv run python scripts/validate_manuscript_artifacts.py` so the generated figure registry,
manuscript references, readable PNG content, caption/alt-text fields, and dashboard
artifact inventory are checked together.

## Scholarship coverage

Every manuscript citation must exist in `references.bib` and in
`../data/scholarship_sources.yaml`. The source matrix records the support lane, source
kind, locator, and role; it is validated by `src/scholarship/coverage.py` before figures
are emitted.

## Section-modification workflow

1. Update the mathematical/experimental description in `02_methodology.md` /
   `05_experimental_setup.md` as needed.
2. Add or extend tests for any new kernel behavior (pure math in `tests/test_kernels_*.py`;
   provenance in `tests/test_provenance.py`).
3. Regenerate claims, the variable map, scholarship audit, figures, and manuscript
   artifact audit (fail-closed provenance + scholarship + artifact gates):
   ```bash
   uv run python scripts/run_kernels.py
   ```
4. Render to PDF via the parent infrastructure renderer, **from the template monorepo
   root** (`working/` projects are resolved by name, and `00_preflight.py` cannot run
   standalone from the project dir because it imports `infrastructure`):
   ```bash
   uv run python scripts/pipeline/stage_03_render.py --project Active_Skillference
   ```
   (Final PDF assembly uses the monorepo `infrastructure/` renderer; see
   [`../docs/rendering_pipeline.md`](../docs/rendering_pipeline.md).)
5. Confirm the generated figures and the cited references appear; check the render log for
   LaTeX/citation errors.

> **Mermaid prerequisite.** If a section embeds a ```mermaid``` block, the combined-PDF
> render shells out to `mmdc`, which needs a pinned `chrome-headless-shell` in the
> Puppeteer cache (`npx --yes puppeteer browsers install chrome-headless-shell`).

## Conventions

1. No "In summary"/"In conclusion" closers unless a section genuinely needs one.
2. Numbers, citations, and figures in the results sections (`03_results.md` and its
   `03a`-`03d` sub-sections) and in `08_supplement_variational_free_energy.md` must
   match what
   `scripts/run_kernels.py` writes (claims in `output/data/claims.json`, scholarship
   audit in `output/data/scholarship_coverage.json`, artifact audit in
   `output/data/manuscript_artifacts.json`, figures under `output/figures/`).
3. Reference code by concrete path (`src/provenance/binding.py`), not vague dotted names.

## See also

- [`README.md`](README.md) — quick orientation
- [`SYNTAX.md`](SYNTAX.md) — Pandoc + provenance-token syntax
- [`../docs/rendering_pipeline.md`](../docs/rendering_pipeline.md) — manuscript → PDF flow
- [`../src/provenance/binding.py`](../src/provenance/binding.py) — claim-token validation/substitution
- [`../scripts/run_kernels.py`](../scripts/run_kernels.py) — regenerates claims and figures
