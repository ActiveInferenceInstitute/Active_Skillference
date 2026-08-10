# AI Agent Instructions — Active Skillference

## Why this file exists

Active Skillference is a **high-integrity** micro-learning platform for Active Inference
and the Free Energy Principle. Its defining promise is *provenance over assertion*:
every quantitative value a learner sees was computed by a tested kernel and passed a
fail-closed provenance gate before reaching skill content, a figure, or the PDF.
Breaking an invariant below — hand-typing a number, escaping the `src.*` namespace,
introducing a mock, weakening the DAG checks — defeats that promise.

Read this file (and [`../AGENTS.md`](../AGENTS.md)) before touching any other file.

All commands below run from the **project root**.

---

## Rule 1: Read the relevant docs first

| Document | Governs | Skip consequence |
|---|---|---|
| **This file** + [`../AGENTS.md`](../AGENTS.md) | All modifications | Risk every violation below |
| [`architecture.md`](architecture.md) | Any `src/` boundary change | Risk logic in `scripts/` or a bare import |
| [`testing_philosophy.md`](testing_philosophy.md) | Any test change | Risk a mock or a coverage drop |
| [`syntax_guide.md`](syntax_guide.md) | Any skill/manuscript content | Risk a hand-typed number the linter rejects |
| [`rendering_pipeline.md`](rendering_pipeline.md) | Any manuscript/output change | Risk an unresolved token or stale figure reference in the PDF/dashboard |
| [`style_guide.md`](style_guide.md) | Any source modification | Risk wrong import layer, bad error messages |

---

## Rule 2: Provenance — never hand-type a result number

Quantitative values reach learners **only** through `{{claim:NAME}}` tokens that resolve
to a value registered by a tested kernel.

- To show a new number: add a worked example in `src/kernels/examples.py`, register the
  claim in `build_claim_registry()` (name, value, units, source), and reference it as
  `{{claim:NAME}}` in the curriculum.
- Input/parameter numbers in prose go inside `$…$` LaTeX math. The linter
  (`src/provenance/binding.py::find_unbacked_numbers` / `lint_graph`) flags any bare
  decimal with ≥2 fractional digits or scientific notation that is not inside math, not
  inside a claim token, and not allowlisted.
- The gate is **fail-closed**: `validate_curriculum` and `render_graph` raise on any
  unbacked or malformed token, so a typo or a renamed kernel breaks the build, never the
  learner. `export_skilltree.py` writes nothing if `lint_graph` finds violations.

Figure labels have their own non-numeric gate. `src/manuscript/audit.py` validates the
generated figure registry against manuscript declarations, `[@fig:...]` references,
readable nonblank PNGs, captions, alt text, and dashboard figure artifacts. A figure label or dashboard artifact edit should
be followed by `uv run python scripts/validate_manuscript_artifacts.py`.

---

## Rule 3: The DAG must stay valid

The curriculum is a validated prerequisite DAG (`src/curriculum/graph.py`). It must stay:

- **acyclic** (three-colour DFS cycle detection),
- **free of dangling prerequisites** (every prereq id exists),
- **rooted only in foundational strata** (`MATH_FOUNDATIONS`, `PROBABILITY` — only these
  may contain zero-prerequisite skills),
- **connected foundations→applications** (every applications skill is reachable from a
  foundational root).

After any edit to the curriculum under `src/curriculum/catalog_data/`, run:

```bash
uv run python scripts/build_curriculum.py
```

It validates internally and prints the live stats from the current catalog: skills,
subjects, prerequisite edges, strata coverage, max depth, and connectivity. Do not
weaken a `_check_*` method to make an edit pass — fix the curriculum.

---

## Rule 4: Imports use the `src.*` namespace

Everything imports under `src.*` (e.g. `from src.curriculum.model import Skill`). Never
reintroduce bare `kernels.`/`curriculum.`/`skilltree.`/`provenance.`/`figures.` imports:
under `pythonpath = [".", "src"]` a bare import creates a second module identity for the
same file, so e.g. two `ClaimRegistry` classes compare unequal and the provenance gate
silently misbehaves.

```bash
grep -rnE "^(from|import) (kernels|curriculum|skilltree|provenance|figures)\b" src/ scripts/ tests/ \
    && echo "VIOLATION — bare import escapes src.*" \
    || echo "Clean — all imports under src.*"
```

---

## Rule 5: No mocks

No `unittest.mock`, `MagicMock`, `@patch`, or `create_autospec` anywhere in `tests/`.
Tests use real numpy data and real computations. The SkillTree REST client is tested
against a real local server via `pytest-httpserver` (see `tests/test_skilltree_client.py`).
Mock tests can pass while the math is wrong — they assert call shapes, not values.

```bash
grep -r "unittest.mock\|MagicMock\|@patch\|create_autospec" tests/ || echo "Clean — no mocks"
```

---

## Rule 6: Coverage gate — ≥90% on `src/`

Both `pyproject.toml` and the verification commands gate coverage at **90%**. The suite
must pass with `src` coverage at or above that floor. Before changing a module, note its
existing tests; after, run:

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90 --cov-report=term-missing
```

If coverage drops, fix the gap — never delete tests to make the number work.

---

## Rule 7: Determinism

Kernel examples use a fixed seed (`SEED = 20260609` in `src/kernels/examples.py`) and
fixed analytical inputs; re-running the kernels regenerates every number and figure
identically. `ClaimRegistry.register` rejects re-registering a name with a *different*
value or provenance — a non-deterministic kernel is a defect, not an accepted drift.
Prefer analytical inputs over random draws whenever a property can be checked directly.

---

## Rule 8: `output/` is disposable — never edit generated files

The entire `output/` tree is written by the scripts and overwritten on every run.
Editing a file there has zero lasting effect. To change a generated artifact, change its
**generator**:

- `output/data/claims.json` / figures → `src/kernels/examples.py` or `src/figures/plots/` (re-run `run_kernels.py`)
- `output/data/manuscript_artifacts.json` / `output/figures/figure_registry.json` → figure
  generator, manuscript figure labels, or `src/dashboard/artifacts.py` (re-run
  `run_kernels.py` or `validate_manuscript_artifacts.py`)
- `output/data/curriculum_stats.json` → `src/curriculum/catalog.py` (re-run `build_curriculum.py`)
- `output/data/course_material_index.json` / `output/data/course_material_audit.json` →
  `src/curriculum/materials/` or `data/course_material_sources.yaml` (re-run
  `build_course_materials.py`)
- `output/data/skilltree_project.json` → the curriculum + the exporter (re-run `export_skilltree.py`)
- `output/pdf/Active_Skillference_combined.pdf` → the `manuscript/*.md` sources, then re-render

See [`output_conventions.md`](output_conventions.md) for the full regeneration sequence.

---

## Extending the curriculum

Adding a skill is a data edit in `src/curriculum/catalog_data/` (e.g. `core_strata.py` or
an `_ext_*.py` file): append a `_s(...)` with a
unique `skill_id`, a stratum, an objective, a description (claim tokens for any numbers),
the quality-gated minimum `_q(...)` assessments, and prerequisites that already exist. If
the skill
shows a new computed value, add a worked example in `src/kernels/examples.py`, register
the claim, and reference it. `build_curriculum()` re-validates on every build. Full
recipe: [`architecture.md`](architecture.md) → *How to add a skill / subject / kernel*.

---

## SkillTree

Data model: `Project → Subject → Skill`. Prerequisites become learning-path
**dependencies**; assessments become **quizzes**; completion is `Quiz`-gated. The
exporter (`src/skilltree/exporter.py`) is a thin field map; the seeder
(`src/skilltree/seeder.py`) creates everything in dependency-safe order
(project → subjects → quizzes → skills → dependencies). The REST contract is mirrored by
`tests/test_skilltree_client.py`. Local no-login learner display uses
`src/skilltree/local_auth.py` to bootstrap a local `FORM` account and exchange
trusted-client tokens server-side; browser JavaScript never receives SkillTree secrets.
Live bring-up: [`../vendor/README.md`](../vendor/README.md) (Docker or build-from-source).

---

## Verification checklist

Run all four before submitting any change (from the project root):

```bash
# 1. Tests pass + coverage ≥90%
uv run pytest tests/ --cov=src --cov-fail-under=90 -q

# 2. No mocks
grep -r "unittest.mock\|MagicMock\|@patch\|create_autospec" tests/ || echo "Clean — no mocks"

# 3. All imports under src.*
grep -rnE "^(from|import) (kernels|curriculum|skilltree|provenance|figures)\b" src/ scripts/ tests/ \
    && echo "VIOLATION" || echo "Clean — src.* only"

# 4. DAG validates + provenance gate passes
uv run python scripts/build_curriculum.py
uv run python scripts/export_skilltree.py
```

All four must report clean (or print the expected valid stats / export line).
