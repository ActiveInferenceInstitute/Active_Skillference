# Extending Active Skillference

> How to grow the curriculum — add a skill or subject, add a kernel and register a
> claim, then re-validate — without breaking the high-integrity guarantees.

Active Skillference is a **local-only** project, not a public, forkable template: it is a
single curriculum (Active Inference / the Free Energy Principle) rendered as a validated
prerequisite graph and exported to [SkillTree](https://skilltreeplatform.dev). You extend
it in place; you do not copy it into a new project name. This guide covers the two edits
you will actually make.

## The non-negotiables you must preserve

Every extension must keep all of these true, or a gate fails:

- **Provenance over assertion.** No quantitative result is hand-typed. Every number a learner sees arrives through a `{{claim:NAME}}` token backed by a tested kernel.
- **A validated DAG.** Acyclic, no dangling/duplicate prerequisites, foundational-only roots, connected foundations → applications.
- **`src.*` imports.** Everything imports under the `src.*` namespace (see [`faq.md`](faq.md#architecture-and-imports)).
- **No mocks.** Kernels tested with real values; the REST client with `pytest-httpserver`.
- **Coverage ≥ 90%** on `src/`; kernel changes need focused tests, and the source of
  truth for current coverage is the test report, not prose.

## Setup

```bash
uv sync
uv run python scripts/build_curriculum.py    # baseline: prints live skills / subjects / edges, 8/8 strata
```

## 1. Add a skill

A skill is one node of the prerequisite graph. Adding one is a data edit in a stratum
source — either a `src/curriculum/catalog_data/` file (e.g. `core_strata.py`) or one of the
`src/curriculum/_ext_*.py` extension modules that `catalog_data/subjects_extensions_*.py`
aggregates: append an `_s(...)` entry to the appropriate stratum's subject list. Required
ingredients (all enforced by
`Skill.__post_init__`, the quality gate, and the DAG validator):

| Ingredient | Rule |
|---|---|
| `skill_id` | Unique across the whole graph; alphanumeric/underscore, starts with a letter |
| `stratum` | One of the eight `Stratum` values (use the `_M`/`_P`/`_IT`/… shorthands) |
| `objective` | A non-empty one-line learning objective |
| `description` | Markdown. Derived results go in `{{claim:NAME}}` tokens; input numbers go inside `$…$` LaTeX math (the linter flags bare decimal results in prose) |
| assessment(s) | The quality gate (`MIN_ASSESSMENTS_PER_SKILL`, currently 4) requires at least four failable questions, including a transfer-style `MultipleChoice` item; a `SingleChoice` question must have exactly one correct index |
| `prerequisites` | A tuple of `skill_id`s that already exist. Outside `math_foundations`/`probability`, a skill must have ≥1 prerequisite (only those two strata may contain roots) |

Example shape (mirrors the entries already in `catalog_data/`; a real skill carries the
full minimum assessment set — one `_q(...)` is shown here for brevity):

```python
_s(
    "ai_my_new_skill",                       # unique skill_id
    "My New Skill",                          # name
    _AI,                                     # stratum (active_inference)
    "State the objective in one line.",      # objective
    "Prose with a derived value of {{claim:efe_epistemic_uncertain}} and an "
    "input parameter $\\alpha = 0.9$.",      # description (claim token + LaTeX math)
    ("ai_existing_prereq",),                 # prerequisites that already exist
    _q(
        "What does positive epistemic value indicate?",
        ["Information to be gained", "No uncertainty", "A pragmatic preference"],
        0,                                   # index of the correct answer
    ),
)
```

Then re-validate:

```bash
uv run python scripts/build_curriculum.py
```

A clean build re-runs the full DAG validation and prints updated counts. Any cycle,
dangling/duplicate prerequisite, or non-foundational root fails the build with a
`CurriculumError` naming the offending skill (see [`troubleshooting.md`](troubleshooting.md#curriculumerror-on-build_curriculum--cycle--dangling--non-foundational-root)).

## 2. Add a subject

A `Subject` is a themed container of skills within one stratum. Add a `Subject(...)` to
the `src/curriculum/catalog_data/` source files with a unique `subject_id`
(alphanumeric/underscore), a `name`, a `stratum`,
a `description` (claim tokens for any numbers), and its `skills` tuple. Every skill in a
subject must share the subject's stratum — `Subject.__post_init__` raises otherwise.
Re-run `scripts/build_curriculum.py`.

## 3. Add a kernel and register a claim

If your new skill needs a value no kernel emits, add it to the kernels rather than typing
it.

1. **Compute it.** Add a worked example to `src/kernels/examples.py` (or extend an existing
   producer like `info_examples` / `efe_examples`) that runs a tested kernel from
   `src/kernels/` on a fixed, documented input and returns the result. Stochastic examples
   use the module-level fixed `SEED`.
2. **Register it.** Inside `build_claim_registry()`, the producer's outputs are registered
   under their dict keys; set `units` in `_UNITS` and the `source` is recorded
   automatically as the producing function's qualified name. Names are stable
   `{{claim:NAME}}` references.
3. **Test the kernel.** Add a real-numerical test under `tests/` asserting the exact
   expected value (no mocks).
4. **Reference it.** Use `{{claim:NAME}}` in the skill description (step 1).

The registry rejects a string claim containing a digit and rejects re-registering a name
with a different value or provenance — so a number can never silently drift.

## 4. Re-validate end to end

After any edit, run the full local chain:

```bash
uv run python scripts/build_curriculum.py     # DAG validation + stats
uv run python scripts/run_kernels.py          # claims, scholarship, figures, artifact audit
uv run python scripts/build_course_materials.py
uv run python scripts/validate_course_material_sources.py --online
uv run python scripts/validate_course_material_alignment.py
uv run python scripts/validate_manuscript_artifacts.py
uv run python scripts/export_skilltree.py     # fail-closed provenance gate + SkillTree JSON
uv run pytest --cov=src --cov-fail-under=90   # full suite, ≥90% coverage
uvx ruff check src scripts tests && uvx ruff format --check src scripts tests
uv run mypy src
```

The export step is the strict gate: it runs `validate_curriculum` + `lint_graph` and
`render_graph`, and writes `output/data/skilltree_project.json` only if every claim token
resolves and no bare result number appears.

## Optional: extend a figure

If a new skill warrants a figure, add a `plot_*` function to `src/figures/plots/` that
reads its values from the `ClaimRegistry` or `CurriculumGraph` (never hand-typed), then
add it to `render_all()`. `scripts/run_kernels.py` renders it into `output/figures/`,
writes `figure_registry.json`, and validates the registry against the manuscript and
dashboard artifact inventory.
The registry row must include a structured chart contract (`question`, `takeaway`,
`data_sources`, `data_grain`, `encoding`, `palette_policy`, `palette_roots`,
`non_color_encoding`, `static_read`, `mobile_read`, `failure_mode`) so manuscript,
dashboard, and validator surfaces describe the same evidence boundary.

## See also

- [`architecture.md`](architecture.md) — module boundaries.
- [`faq.md`](faq.md) — imports, provenance, and authoring questions.
- [`troubleshooting.md`](troubleshooting.md) — symptom-driven fixes.
- [`output_inventory.md`](output_inventory.md) — every artifact and its producer.
- [`../AGENTS.md`](../AGENTS.md) — invariants and the provenance chain.
