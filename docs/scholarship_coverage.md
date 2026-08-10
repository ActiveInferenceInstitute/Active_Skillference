# Scholarship Coverage

Active Skillference treats scholarship as a checked build input. A citation that merely
exists in `manuscript/references.bib` is not enough; every authored citation must also
have a declared source role in `data/scholarship_sources.yaml`. The reverse is checked as
well: source-matrix rows and BibTeX entries are expected to be cited by the current
manuscript, so stale support claims cannot linger after prose changes.

## Source Matrix

`data/scholarship_sources.yaml` is a static, version-controlled input. Each row has:

| Field | Meaning |
|---|---|
| `key` | BibTeX key cited from `manuscript/*.md` |
| `lane` | One of the expected scholarship lanes |
| `kind` | Source kind: primary, review, tutorial, textbook, methods, software, documentation, or historical |
| `locator` | DOI, URL, ISBN, arXiv id, JSTOR URL, or book identifier |
| `role` | Short explanation of what the source supports |

Expected lanes are defined in `src/scholarship/coverage.py`:

- `perception_as_inference`
- `active_inference_core`
- `mathematical_foundations`
- `pedagogy_and_learning_paths`
- `delivery_and_reporting`
- `applications_and_scope`

## Validator

`src/scholarship/coverage.py` parses authored manuscript sections, strips code spans,
extracts Pandoc citation keys, validates them against `references.bib`, and checks that
each cited key has a source-matrix row with a lane, kind, locator, and substantive role.
It also rejects source-matrix rows or BibTeX entries that are no longer cited.

Open roadmap tasks carry a validated `scholarship_plan` in `tasks.yaml`. The plan records
the lanes, existing source keys, verified future source targets, claim-support types,
boundaries, and phase-exit conditions rendered into `TODO.md` and `docs/todo/*.md`.
This keeps future release, runtime, pilot, adaptive-path, and archive work explicit without
turning a planned phase into present evidence.

Run the audit directly:

```bash
uv run python scripts/analyze_scholarship.py
```

`scripts/run_kernels.py` also runs the same audit before writing learner-facing
artifacts. A missing matrix row, undefined BibTeX key, stale source-matrix row, or
uncited bibliography entry therefore blocks the figure build and the PDF render path.

## Generated Outputs

The audit emits:

| Output | Role |
|---|---|
| `output/data/scholarship_coverage.json` | Deterministic JSON summary of lanes, source roles, section citations, and issues |
| `output/data/scholarship_source_health.json` | Locator and role-quality health audit, optionally refreshed with online reachability checks |
| `output/data/scholarship_source_health_network.json` | Read-only network report that separates dead links, bot blocks, role gaps, metadata issues, boundary sources, and uncited drift for dashboard/release review |
| `output/data/scholarship_gap_report.json` | Frontier-source audit that binds formal and workflow provenance, information theory, variational Bayes, predictive inference, knowledge spaces, cognitive diagnosis, learner-state comparisons, pilot reporting, responsible learning analytics, pedagogy, reproducibility, open science, citation metadata, archive workflow, accessibility, security, applications/scope evidence, and course-material provenance to claim-support classes and boundary rows |
| `output/figures/scholarship_coverage.png` | Visual coverage matrix used in the manuscript and dashboard |
| `output/figures/open_science_source_map.png` | Active Inference Institute learning-source ledger combining scholarship rows with generated course-material and cognitive knowledge-base pointer coverage |
| `output/figures/scholarship_source_health.png` | Source-health status summary used in the manuscript and dashboard |

The figures are referenced in `manuscript/03b_results_scholarship_source_health_and_evidence_audits.md` as
`{#fig:scholarship_coverage}`, `{#fig:open_science_sources}`, and
`{#fig:scholarship_source_health}`.

## Adding A Citation

1. Add the BibTeX entry to `manuscript/references.bib`.
2. Add the citation to the manuscript using Pandoc syntax, for example
   `[@smith2022tutorial]`.
3. Add a row for the same key in `data/scholarship_sources.yaml`.
4. Run:

```bash
uv run python scripts/analyze_scholarship.py
uv run python scripts/audit_scholarship_gaps.py
uv run python scripts/validate_scholarship_sources.py --online
uv run python scripts/run_kernels.py
```

Do not add a citation only to satisfy apparent coverage. The row's `role` should explain
what the source actually supports in the manuscript, and frontier additions should be
bound in `data/manuscript_claim_support.yaml` so the gap report can distinguish
argument support from bibliography padding.

## Removing A Citation

When deleting or replacing a citation, remove the corresponding source-matrix row and
BibTeX entry unless another manuscript section still cites the same key. The validator is
strict about this because the coverage figure should describe only live manuscript
support.
