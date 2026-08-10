# data/ — Agent Guide

Static, version-controlled **inputs** only. Generated artifacts must not be committed here —
they live under `output/`.

## There is no manual claim ledger

In Active Skillference, every learner-facing number is provenance-bound at the source. Skill
content references numbers only through `{{claim:NAME}}` tokens that resolve to claims
**registered by the tested kernels** (`src/kernels/`). The registry is built by
`src/kernels/examples.py` (`build_claim_registry`) and serialized by
`scripts/run_kernels.py` into the canonical ledger at **`output/data/claims.json`**.

There is therefore **no hand-maintained ledger in this directory**. The binding gate in
`src/provenance/binding.py` is **fail-closed**: the curriculum export and the manuscript
render both refuse if any `{{claim:NAME}}` token is unbacked or malformed, and a linter
rejects bare result numbers typed into prose. Provenance is enforced by code and tests
(`tests/test_provenance.py`, `tests/test_kernels_examples.py`), not by editing a YAML file.

## Static source matrix

`scholarship_sources.yaml` is a hand-authored input, not a generated artifact. It maps
each cited manuscript source to a scholarship lane, source kind, authoritative locator,
and support role. The validator in `src/scholarship/coverage.py` checks this matrix
against `manuscript/references.bib` and the authored citations before figures are written.
Rows are bidirectionally aligned: every cited key must have a row, and every row must
remain cited by the current manuscript.

`course_material_sources.yaml` is also a hand-authored input. It pins external Active
Inference Institute source repositories by commit and maps curriculum strata/topics to
specific source paths. The generated dashboard Learn records link to those pinned paths;
they do not copy upstream course or knowledge-base prose into this repository.

Edit it only when adding, removing, or reclassifying manuscript citations. After editing,
run:

```bash
uv run python scripts/analyze_scholarship.py
uv run python scripts/build_course_materials.py
uv run python scripts/validate_course_material_sources.py --online
uv run python scripts/run_kernels.py
```

## What to put here

- Only genuinely static inputs such as `scholarship_sources.yaml` and
  `course_material_sources.yaml`.
- Document any new input file in [`README.md`](README.md) with its role and source.

## What must NOT go here

- `claims.json`, `manuscript_variables.json`, `curriculum_stats.json`,
  `skilltree_project.json`, or any other generated artifact — those are written to
  `output/data/` and are regenerable.
- Generated CSV / JSON / PNG of any kind.

To change a learner-facing number, change (or add) a kernel claim in `src/kernels/` and
re-run `scripts/run_kernels.py`; never edit a data file by hand.

Quick orientation: [`README.md`](README.md).
