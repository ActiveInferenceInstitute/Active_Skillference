# Active Skillference Manuscript Authoring and Render Guide

The platform write-up: how the Active Inference / Free Energy Principle curriculum is built
as a validated prerequisite DAG, why every learner-facing number is produced by a tested
kernel, and how the curriculum exports to the SkillTree runtime. These Markdown sections
render to a single academic PDF via the parent monorepo's `infrastructure/` renderer.

## Manuscript inventory and section roles

| File | Contents |
|---|---|
| `00_abstract.md` | Abstract — Active Skillference as a provenance-bound curriculum artifact |
| `01_introduction.md` | Motivation, situation awareness, evaluation questions, and evidence boundary |
| `02_methodology.md` | Methods spine and reading order |
| `02a_`-`02c_*.md` | Kernels/statistics/provenance, scholarship/curriculum/strata, and SkillTree/dashboard/publication methods |
| `03_results.md` | Results spine and reading order |
| `03a_`-`03d_*.md` | Graph/assessment, scholarship/evidence, kernel-example, and SkillTree/dashboard/front-matter results |
| `04_conclusion.md` | Discussion, interpretation, limitations, and conclusion |
| `05_experimental_setup.md` | Deterministic models, build gates, and planned learner study |
| `06_reproducibility.md` | Artifact-chain regeneration, verification gates, and release evidence |
| `07_scope_and_related_work.md` | Theoretical, platform, and outcome boundaries |
| `07a_`-`07d_*.md` | Platform boundary, AIF/information related work, SkillTree/security/reporting context, and limitations |
| `08_supplement_variational_free_energy.md` | Auditable VFE/EFE teaching examples tied to SkillTree subjects |
| `99_references.md` | Bibliography pointer and validation command |

Authoring support files: `config.yaml` (paper metadata + render wiring),
`config.yaml.example` (annotated reference), `preamble.md` (LaTeX packages),
`references.bib` (bibliography), `SYNTAX.md` (citation/figure/provenance-token syntax),
and `AGENTS.md` (agent editing protocol).

## Core provenance rule for numbers and claim support

Every result number is a `{{claim:NAME}}` provenance token resolving to a tested-kernel
value; input parameters live in `$…$` math. `scripts/run_kernels.py` registers the claims,
writes `output/data/manuscript_variables.json`, renders the generated figures, and **fails the
build closed** if any token is unbacked or any bare result decimal is typed into prose. See
[`SYNTAX.md`](SYNTAX.md) and [`AGENTS.md`](AGENTS.md).

Manuscript scientific claims also use `<!-- claim-support:... -->` anchors backed by
`data/manuscript_claim_support.yaml`. Run `uv run python scripts/validate_claim_support.py`
after changing claim strength, citations, figures, or limitation language.

## Build sequence for claims, figures, and PDF rendering

```bash
# From the project root — regenerate claims + figures (fail-closed provenance gate)
uv run python scripts/run_kernels.py

# From the template monorepo root — render the PDF with the monorepo infrastructure
# on the path. The renderer resolves projects/working/Active_Skillference by name.
uv run python scripts/pipeline/stage_03_render.py --project Active_Skillference
```

The generated visual assets are written to `output/figures/`: deterministic first-page
cover and page-two named-skill atlas PNGs plus registered manuscript figures for the
annotated DAG, dependency-flow and quiz floor-pass audit, graph diagnostics,
scholarship/open-science coverage views, a validation-surface matrix, a scientific
evidence matrix, roadmap status view, and supplemental VFE/EFE walkthrough and
sensitivity plots. The cover is configured through `book.cover.image`, and the atlas is
configured through `front_matter.page_two_visual.image`; both are validated separately
from `figure_registry.json`, so neither is cited as a numbered manuscript figure.
Final PDF assembly
(`output/pdf/Active_Skillference_combined.pdf`) is
performed by the parent monorepo `infrastructure/` renderer; see
[`../docs/rendering_pipeline.md`](../docs/rendering_pipeline.md).

## Related authoring and rendering references

- [`AGENTS.md`](AGENTS.md) — manuscript editing protocol and the provenance pipeline
- [`SYNTAX.md`](SYNTAX.md) — citation, figure, equation, and `{{claim:NAME}}` syntax
- [`../README.md`](../README.md) — project overview
- [`../docs/rendering_pipeline.md`](../docs/rendering_pipeline.md) — manuscript → PDF flow
