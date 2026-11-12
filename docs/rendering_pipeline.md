# Rendering Pipeline: Kernels → Provenance → Manuscript → PDF

The [`manuscript/`](../manuscript/) directory holds the platform write-up. It compiles to a
publication PDF, but — because Active Skillference is **provenance-bound** — the manuscript
is not rendered in isolation. Every quantitative result in it is a `{{claim:NAME}}` token
that must first be produced by a tested kernel. So the pipeline runs kernels → registers
claims → validates the manuscript and scholarship matrix fail-closed → renders figures →
audits manuscript/dashboard figure wiring → renders the PDF.

The render itself is in-repo: [`scripts/render_manuscript.py`](../scripts/render_manuscript.py)
hydrates the sections from the kernel-emitted variables and drives Pandoc → XeLaTeX with
the manuscript's own configuration, preamble, and bibliography. It needs `pandoc`,
`pandoc-crossref`, `xelatex` and `bibtex` on `PATH` and nothing from any other
repository; the arm is `./gates.sh render` ([`gates.md`](gates.md)).

## The flow

```
run_kernels.py ──► src.pipeline.generated_outputs.build_generated_outputs()
       │
       └────► claims.json + manuscript_variables.json + scholarship_coverage.json
       │            + manuscript_claim_support.json + figures + cover/atlas PNGs
       │            + figure_registry.json + manuscript_artifacts.json
       │            + cover/front-matter audits + course material index/audit
       │            (validates curriculum, manuscript provenance, scholarship,
       │             claim support, figure/dashboard wiring, and publication-asset wiring,
       │             fail-closed)
       ▼
z_generate_manuscript_variables.py ──► output/manuscript/*.md
       │                                ({{claim:NAME}} and count tokens resolved)
       ▼
render_manuscript.py ──► pandoc --natbib → xelatex → bibtex → xelatex → xelatex
       │                  (title page from config.yaml, preamble.md packages,
       │                   pandoc-crossref figures/sections, references.bib)
       ▼
output/pdf/Active_Skillference_combined.pdf
       │
       ▼
ensure_web_math.py + validate_web_math.py ──► committed output/web/*.html stays MathJax-ready
```

The learner dashboard is a local consumer of the same outputs. It is served by
`scripts/serve_learner_dashboard.py`, reads `output/data/skilltree_project.json`,
`claims.json`, `curriculum_stats.json`, scholarship coverage, figure registry,
manuscript claim-support audit, manuscript artifact audit, cover/front-matter audits,
figures, the generated cover and page-two atlas, and the rendered manuscript artifacts,
then mounts the official SkillTree learner display when local trusted-client auth is
bootstrapped. It is not part of the PDF render pipeline and does not replace the
SkillTree service.

### Step 1 — Run kernels, register claims, validate scholarship/claim support, render figures and lessons

**Script**: [`scripts/run_kernels.py`](../scripts/run_kernels.py) (thin CLI wrapper over
`src.pipeline.generated_outputs`; logic stays in `src.*`).

**Command**:

```bash
uv run python scripts/run_kernels.py
```

**What it does** (in order, fail-closed):

1. `build_claim_registry()` runs every worked example in `src/kernels/examples.py` and
   registers each result as a named claim.
2. `build_curriculum()` builds and validates the Active Inference DAG.
3. `validate_curriculum(graph.skills, registry)` fails closed if any skill references an
   unbacked `{{claim:NAME}}`.
4. `validate_manuscript_dir(manuscript/, registry)` walks every `manuscript/*.md` and fails
   closed if any manuscript prose references an unbacked claim token — so a dead token can
   never render literally into the rendered PDF.
5. `validate_scholarship(...)` checks manuscript citations against `references.bib` and
   `data/scholarship_sources.yaml`, including the reverse check that no stale BibTeX or
   source-matrix row remains after manuscript edits.
6. `plot_active_skillference_cover(...)` writes the deterministic first-page cover PNG.
7. `plot_skill_name_atlas(...)` writes the deterministic page-two named-skill atlas.
8. `validate_claim_support(...)` checks anchored manuscript claims against their declared
   evidence classes and writes `manuscript_claim_support.json`.
9. `render_all(...)` writes the registered deterministic figure PNGs and `figure_registry.json`
   from the canonical rows in `src.figures.registry_manifest`.
10. `validate_manuscript_artifacts(...)` checks that the figure registry, manuscript
   declarations, figure cross-references, readable nonblank PNGs, caption/alt-text
   specificity, semantic metadata, structured chart-contract fields, claim tokens, and dashboard figure artifact links agree before writing
   `manuscript_artifacts.json`.
11. `validate_cover_asset(...)` checks that `book.cover.image` resolves to the generated
   cover PNG, the image is nonblank, the dashboard exposes it as a non-figure artifact,
   and the numbered figure registry does not include it.
12. `validate_front_matter_visual(...)` applies the same nonblank/dashboard/registry
   exclusion checks to `front_matter.page_two_visual.image`.
13. `build_course_material_index(...)` writes local dashboard Learn material records and
   audits pinned external course/source pointers.

**Outputs**:

| File | Location | Content |
|---|---|---|
| `claims.json` | `output/data/` | The provenance ledger — every registered claim with value, units, and source kernel function |
| `manuscript_variables.json` | `output/data/` | Every claim value plus live curriculum, quiz, claim, figure, citation, lane, and configured-floor counts for the manuscript |
| `scholarship_coverage.json` | `output/data/` | Citation source-role coverage by lane and manuscript section |
| `manuscript_claim_support.json` | `output/data/` | Claim-support audit for anchored manuscript scientific claims and evidence classes |
| `manuscript_artifacts.json` | `output/data/` | Cross-surface audit for generated figure registry, manuscript labels/cross-references, PNG information content, captions, alt text, semantic metadata, claim tokens, and dashboard figure artifacts |
| `cover_asset_audit.json` | `output/data/` | Cover-asset audit for `book.cover.image`, nonblank PNG content, dashboard exposure, and registry exclusion |
| `front_matter_visual_audit.json` | `output/data/` | Page-two visual audit for `front_matter.page_two_visual.image`, nonblank PNG content, dashboard exposure, and registry exclusion |
| `course_material_index.json` | `output/data/` | Local modular dashboard Learn records with pinned external pointers |
| `course_material_audit.json` | `output/data/` | Completeness audit for course-material records and pointers |
| `active_skillference_cover.png` | `output/figures/` | Deterministic square first-page cover generated from live graph, claim, and roadmap data (`plot_active_skillference_cover`) |
| `active_skillference_skill_atlas.png` | `output/figures/` | Deterministic page-two atlas generated from every authored skill name, with readable token, stratum, and reduced dependency-spine summaries (`plot_skill_name_atlas`) |
| `curriculum_dag.png` | `output/figures/` | Annotated prerequisite DAG laid out by stratum × depth with wrapped lane labels (`plot_curriculum_dag`) |
| `dependency_strata_flow.png` | `output/figures/` | Prerequisite-edge flow matrix across strata (`plot_dependency_strata_flow`) |
| `graph_bottlenecks.png` | `output/figures/` | High-fanout prerequisite review queue with direct skill labels, stratum context and depth annotations (`plot_graph_bottlenecks`) |
| `skill_neighborhood_paths.png` | `output/figures/` | Representative longest prerequisite path with route callouts and a checkpoint ledger for start, stratum-transition and endpoint reads (`plot_skill_neighborhood_paths`) |
| `semantic_prerequisite_coverage.png` | `output/figures/` | Semantic-prerequisite lollipop audit for load-bearing concepts (`plot_semantic_prerequisite_coverage`) |
| `assessment_depth_matrix.png` | `output/figures/` | Quiz floor-pass audit table/bar hybrid by stratum (`plot_assessment_depth_matrix`) |
| `curriculum_stratum_balance.png` | `output/figures/` | Raw and normalized stratum-level skill, subject, assessment and dependency balance (`plot_curriculum_stratum_balance`) |
| `free_energy_descent.png` | `output/figures/` | Supplemental VFE sweep over `q(present)` against `−log evidence` (`plot_free_energy_descent`) |
| `efe_decomposition.png` | `output/figures/` | Supplemental sample/commit EFE comparison plus sensor-precision regime sweep (`plot_efe_decomposition`) |
| `planning_lookahead.png` | `output/figures/` | Supplemental multi-step planning look-ahead: greedy-vs-optimal gain across a decoupled (zero) and coupled (positive) model plus per-policy EFE (`plot_planning_lookahead`) |
| `predictive_coding_descent.png` | `output/figures/` | Supplemental continuous predictive-coding descent: estimate settling to the analytic posterior plus monotonic free-energy descent (`plot_predictive_coding`) |
| `kernel_sensitivity_profiles.png` | `output/figures/` | Supplemental base-rate, VFE-bound and EFE policy-regime sensitivity profiles (`plot_kernel_sensitivity_profiles`) |
| `vfe_efe_skilltree_bridge.png` | `output/figures/` | Supplemental bridge from VFE/EFE figures to real SkillTree subjects, skills, prerequisite edges, quizzes, learn routes and quiz routes (`plot_vfe_efe_skilltree_bridge`) |
| `scholarship_coverage.png` | `output/figures/` | Citation coverage by source lane and manuscript section (`plot_scholarship_coverage`) |
| `open_science_source_map.png` | `output/figures/` | Active Inference Institute learning-source ledger combining scholarship support rows with generated course-material and cognitive knowledge-base pointer coverage (`plot_open_science_source_map`) |
| `scholarship_source_health.png` | `output/figures/` | Scholarship locator and support-role status ledger (`plot_scholarship_source_health`) |
| `validation_surface_matrix.png` | `output/figures/` | Validation gates by artifact and release-documentation surface plus live evidence counts (`plot_validation_surface_matrix`) |
| `validation_intent_mismatch_matrix.png` | `output/figures/` | Mismatch classes the release validators are expected to reject (`plot_validation_intent_mismatch_matrix`) |
| `visual_evidence_contract_ladder.png` | `output/figures/` | Curriculum-backed visual-evidence contract lifecycle from question through negative control (`plot_visual_evidence_contract_ladder`) |
| `scientific_evidence_matrix.png` | `output/figures/` | Claim-support evidence-class matrix (`plot_scientific_evidence_matrix`) |
| `roadmap_risk.png` | `output/figures/` | Roadmap status, external blockers, git-authorization hygiene and live metrics (`plot_roadmap_risk`) |
| `figure_registry.json` | `output/figures/` | Labels, filenames, captions, alt text, semantic metadata, structured chart contracts, visual QA fields, claim tokens, and generators for every generated manuscript/dashboard figure |

Figure data come from the `ClaimRegistry`, `CurriculumGraph`, validated scholarship
audit, claim-support audit, or the canonical render configuration. The figure registry is
loaded through `src.figures.registry` and generated from `src.figures.registry_manifest`;
planned before count-bearing visuals render, then checked against the PNGs written in the
same pass; the artifact validator checks that registry against the manuscript and
dashboard surfaces. The cover and page-two atlas audits check generated front-matter
images as separate publication assets, not numbered figures. Re-running this script
regenerates every number, audit, registry, figure, and front-matter asset.
Chart-contract fields (`question`, `takeaway`, `data_sources`, `encoding`,
`data_grain`, `palette_policy`, `palette_roots`, `non_color_encoding`, `static_read`,
`mobile_read`, `failure_mode`) are additive registry fields: figure code produces them,
the manuscript references the figure, the dashboard displays them, and the artifact
validator rejects absent or generic metadata.
The figure producer also owns the visual readability contract: meaningful chart text must
stay at or above the shared 9.5px-equivalent floor, 8.5px is reserved for source/caveat
notes, and dense visuals should widen, wrap, summarize, or use ledger layouts instead of
shrinking labels. The dashboard artifact gallery exposes a full-size image link before
metadata and groups the first-read contract as Question / Grain / Boundary / Failure.

### Step 2 — Hydrate the authored sections

**Script**: [`scripts/z_generate_manuscript_variables.py`](../scripts/z_generate_manuscript_variables.py).

By default it re-runs `scripts/run_kernels.py` first, so the variables file and every
figure are current, then writes a resolved copy of every section to
`output/manuscript/`. Tokens are substituted from
`output/data/manuscript_variables.json`: `{{claim:NAME}}` resolves strictly (an unknown
claim name raises) and a bare `{{count_token}}` resolves from the same file. Code spans
are left alone so the syntax documentation stays readable, and any unresolved `{{…}}`
leftover fails the run. `--skip-kernels` reuses the artifacts already on disk.

### Step 3 — Render the PDF (repository toolchain)

```bash
./gates.sh render
# equivalent, and useful when iterating on prose without re-running the kernels:
uv run python scripts/render_manuscript.py --skip-kernels
```

[`scripts/render_manuscript.py`](../scripts/render_manuscript.py) assembles
`output/manuscript/*.md` in lexicographic order (`00_abstract.md` …
`08_supplement_variational_free_energy.md` … `99_references.md`) with a page break
between sections, prepends a title page generated from
[`manuscript/config.yaml`](../manuscript/config.yaml) (cover image, title, subtitle,
authors, DOI, version), and then runs one Pandoc pass followed by the standard LaTeX
citation cycle:

1. `pandoc --to=latex --natbib --standalone --toc --number-sections` with
   `pandoc-crossref` and the `manuscript/preamble.md` packages;
2. `xelatex`, `bibtex`, `xelatex`, `xelatex` — the second pass resolves the `.bbl`,
   the third settles cross-references.

The combined Markdown, `.tex`, `.aux`, `.log`, `.bbl`, bibliography copy and the first
PDF passes stay in a scratch directory one level below the repository root; only the final
`output/pdf/Active_Skillference_combined.pdf` is kept. The scratch directory has to sit at
that depth because the manuscript writes figure paths as `../output/figures/x.png`.

After the passes, the script reads `combined.log` and fails if any reference or citation
is still undefined, so a PDF with `[??]` in it is never published as the build output.

**Final PDF target**: `output/pdf/Active_Skillference_combined.pdf`.

The committed `output/web/`, `output/docx/`, `output/epub/` and `output/slides/` bundles
are deposited publication artifacts from the wider publishing pipeline; this arm does not
rewrite them. It does keep their math surfaces honest:

```bash
uv run python scripts/ensure_web_math.py
uv run python scripts/validate_web_math.py
```

The first normalizes rendered HTML that contains math so it loads MathJax; the second
fails if the manuscript web output or the learner dashboard can still surface formulas as
escaped text. `./gates.sh render` runs both after the PDF.

**Inputs the renderer consumes**:

- The manuscript sections in `manuscript/*.md`, whose `{{claim:NAME}}` tokens resolve from
  the kernel-emitted values (`manuscript_variables.json` / the registry).
- `manuscript/config.yaml` — title, book cover image, authors, DOI, keywords (see the table below).
- `manuscript/preamble.md` — LaTeX packages (`amsmath`, `cleveref`, `natbib`, …).
- `manuscript/references.bib` — BibTeX entries for `[@key]` citations.
- `data/scholarship_sources.yaml` — source-role matrix for cited BibTeX keys.
- The figures in `output/figures/`, referenced from the results sections
  `03a_results_curriculum_graph_and_assessment_quality.md`,
  `03b_results_scholarship_source_health_and_evidence_audits.md`, and
  `03c_results_kernel_examples.md` for platform evidence, and from
  `08_supplement_variational_free_energy.md` for the VFE/EFE walkthroughs.
- `output/figures/figure_registry.json` and `output/data/manuscript_artifacts.json`,
  which are generated before rendering and catch figure-label or dashboard-inventory drift.

## config.yaml controls

[`manuscript/config.yaml`](../manuscript/config.yaml) links the prose to the execution and
publication layers:

| YAML key | Controls | Consumed by |
|---|---|---|
| `paper.title` / `paper.subtitle` / `paper.version` | PDF title page and headers | `infrastructure/rendering/pdf_renderer.py` |
| `authors[*]` | Author list, ORCID, affiliation on the title page | `infrastructure.publishing.metadata` + renderer |
| `publication.doi` / `publication.version_doi` | Citation DOIs on the cover page and `CITATION.cff` | renderer + publishing tools |
| `keywords` | Keyword metadata | renderer / publishing metadata |
| `render.formats.{pdf,html,slides,docx,epub}` | Per-format render toggles | `infrastructure/rendering/config.py` |
| `experiment.strata` | The eight pedagogical strata | `scripts/build_curriculum.py` / `run_kernels.py` |
| `experiment.kernel_seed` | Deterministic claim generation | the worked examples |
| `experiment.units` | Information units (`nats`) | the kernels / curriculum |

### Optional publication features

These are configured in `manuscript/config.yaml` and are **optional**; they engage only
through the wider publishing tooling and are not required to produce the
combined PDF. **In this project both are disabled** — it is an open (MIT) educational
manuscript, so no watermarking or transmission bookends are applied.

- **`publication.transmission_bookends`** (`enabled: false`): when enabled and engaged by
  the publishing pipeline, the combined PDF can include generated front/back transmission
  pages (compact metadata, an integrity strip, and prior-release rows). Off here.
- **`steganography`** (`enabled: false`): when enabled, a profile consumed by the parent
  monorepo's secure / steganography step to produce a hardened `*_steganography.pdf` and a
  hashes manifest. Off here — no `CONFIDENTIAL` overlay on an open educational PDF.

If you do not run those publishing steps, omit them — the core kernels → manuscript → PDF
flow above does not depend on either.

## Troubleshooting

### Learner dashboard shows SkillTree offline

**Symptom**: `http://127.0.0.1:8765` loads, but the SkillTree status tile is offline and
the official learner display falls back to direct links.

**Cause**: The dashboard is reachable but `http://localhost:8080/public/status` is not.
The local dashboard can browse generated artifacts without Docker, but learner progress,
ranking, quizzes, and self-reporting require the SkillTree service.

**Fix**:

```bash
./scripts/run_learning_dashboard.sh
# or, if SkillTree is already running:
uv run python scripts/bootstrap_local_skilltree.py --base-url http://localhost:8080
uv run python scripts/serve_learner_dashboard.py --local-auth
```

### Unresolved `{{claim:NAME}}` appears (or the build refuses)

**Symptom**: `run_kernels.py` raises `ProvenanceError`, or a literal `{{claim:...}}` would
otherwise reach the PDF.

**Cause**: A manuscript section or skill references a claim that no kernel emits (e.g. after
a kernel/claim was renamed in `src/kernels/examples.py`), or a malformed token like
`{{claim:}}`.

**Fix**: The error names the offending file/skill and the missing claim. Either add/restore
the worked example + registration in `src/kernels/examples.py`, or correct the token name.
Re-run:

```bash
uv run python scripts/run_kernels.py
# cross-check the exported curriculum is token-free (also asserted by the smoke test):
grep -F "{{claim" output/data/skilltree_project.json && echo "UNRESOLVED" || echo "clean"
```

### Missing figure in the PDF

**Symptom**: A broken image placeholder where `[@fig:curriculum_dag]` / `[@fig:free_energy]`
/ `[@fig:efe]` should be.

**Cause**: `run_kernels.py` did not render the figures into `output/figures/`.

**Fix**:

```bash
ls output/figures/*.png
uv run python scripts/run_kernels.py
```

### BibTeX citation error

**Symptom**: XeLaTeX fails with an undefined citation key or BibTeX error.

**Cause**: A `[@key]` in a manuscript section has no matching entry in
[`manuscript/references.bib`](../manuscript/references.bib), or the entry is malformed.

**Fix**: Confirm every cited key exists and entries have at least `author`, `title`, `year`.

### The render arm stops on a missing tool

**Symptom**: `render_manuscript.py` exits non-zero naming `pandoc`,
`pandoc-crossref`, `xelatex` or `bibtex`.

**Cause**: One of the four tools the render path needs is not on `PATH`, or
`pandoc-crossref` was built for a different Pandoc major version (it refuses to run
against an incompatible one).

**Fix**: Install the named tool and re-run `./gates.sh render`. On macOS:
`brew install pandoc pandoc-crossref` and a TeX Live with `xelatex`/`bibtex`
(TinyTeX or MacTeX). The script names the missing tool precisely and writes no partial
PDF.

### The render arm reports unresolved references or citations

**Symptom**: `render_manuscript.py` exits with lines from `combined.log` naming an
undefined citation or reference.

**Cause**: A `[@key]` with no entry in `manuscript/references.bib`, a `[@fig:label]`
with no matching `{#fig:label}` image attribute, or a `[@sec:label]` with no matching
section id.

**Fix**: Add the missing bibliography entry, add the label to the figure or heading, or
correct the reference. Re-run `./gates.sh render`; the log check fails the run rather than
publishing a PDF with `[??]` in it.

## See also

- [`syntax_guide.md`](syntax_guide.md) — the `{{claim:NAME}}` token system and figure registry
- [`style_guide.md`](style_guide.md) — kernel purity and claim-binding rules
- [`testing_philosophy.md`](testing_philosophy.md) — the no-mocks testing standard
- [`../AGENTS.md`](../AGENTS.md) — invariants and the provenance chain
