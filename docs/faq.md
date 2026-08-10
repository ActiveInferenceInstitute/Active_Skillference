# Frequently Asked Questions

Answers for working in Active Skillference — a high-integrity micro-learning
platform that renders the Active Inference / Free Energy Principle body of knowledge
as a validated prerequisite graph and exports it to [SkillTree](https://skilltreeplatform.dev).

## Architecture and imports

### Why does everything import under the `src.*` namespace?

`pyproject.toml` sets `pythonpath = [".", "src"]`. With both the project root and
`src/` on the path, a module like `curriculum/graph.py` is reachable two ways — as
`src.curriculum.graph` *and* as `curriculum.graph`. Those are two distinct module
objects to Python: two `Stratum` enums, two `ClaimRegistry` classes, so an `isinstance`
check or a `frozen` dataclass identity comparison can silently fail. To keep a single
canonical identity, **every import uses the `src.*` prefix** (e.g.
`from src.curriculum.model import Skill`). Do not reintroduce bare `kernels.` /
`curriculum.` / `skilltree.` imports. `mypy` is run as `mypy src` for the same reason —
one canonical name, no `MYPYPATH`.

### What is the "thin orchestrator" pattern here?

All logic lives in `src/`; the files in `scripts/` only coordinate I/O. A script builds
the registry/graph, runs the provenance gate, and writes JSON or figures to `output/`.
It never computes a curriculum value itself. If you find yourself computing an entropy or
a free-energy number inside a script, move it into `src/kernels/` and register a claim.

### Why is provenance binding ("provenance over assertion") the defining rule?

Every quantitative value a learner sees must be *computed by a tested kernel*, never
hand-typed. A kernel function in `src/kernels/examples.py` produces a value, registers it
as a named `Claim`, and skill content references it only through a `{{claim:NAME}}` token
(see `src/provenance/binding.py`). At build time the token is substituted with the
registered value. Change a kernel and the claim, the rendered skill text, the manuscript,
and the figures all change together — there is no place for a number to drift out of sync.
An unbacked or malformed token is a build failure, not a silent literal a learner reads.

## Adding content

### How do I add a new skill?

Adding a skill is a data edit in a stratum source — append an `_s(...)` to a
`src/curriculum/catalog_data/` file (e.g. `core_strata.py`) or to one of the
`src/curriculum/_ext_*.py` extension modules that `catalog_data/subjects_extensions_*.py`
aggregates:

1. a unique `skill_id` (alphanumeric/underscore, starting with a letter — `Skill.__post_init__` enforces it),
2. a `Stratum` (one of the eight),
3. a one-line `objective`,
4. a markdown `description` — any quantitative result goes in a `{{claim:NAME}}` token, and input numbers go inside `$…$` LaTeX math,
5. the quality-gated minimum `_q(...)` assessments — `MIN_ASSESSMENTS_PER_SKILL` (currently 4) failable items, including a transfer-style `MultipleChoice` item,
6. `prerequisites` that already exist (and, for a non-foundational stratum, at least one prerequisite — only `math_foundations` and `probability` may contain roots).

Then re-validate: `uv run python scripts/build_curriculum.py` rebuilds and re-runs the
full DAG validation (unique ids, no dangling/duplicate prerequisites, no cycles,
foundational-only roots).

### How do I add a new claim (a new computed number)?

If a skill needs a value no kernel emits yet:

1. Add a worked example in `src/kernels/examples.py` (or a new producer function) that runs a tested kernel on a fixed, documented input and returns the result.
2. Register it inside `build_claim_registry()` — give it a stable name, set `units` and a `source` (the producing function's qualified name).
3. Reference it as `{{claim:NAME}}` in the skill description (or manuscript prose).
4. Run `uv run python scripts/run_kernels.py` to re-register claims and re-render figures, and `uv run python scripts/export_skilltree.py` to re-run the fail-closed export.

The registry rejects a string claim that contains a digit (numbers must be numeric
claims) and rejects re-registering a name with a different value or provenance — a
non-deterministic kernel is treated as a defect.

### Why are mocks forbidden?

Mocking asserts that a function *was called*, not that it produced the *correct value*.
The kernels are pure and deterministic, so they are tested with real inputs and exact
expected outputs. The only external surface is the SkillTree REST API, tested with
`pytest-httpserver` (a real local HTTP server), not a mock client. Zero mocks is what
makes the reproducibility guarantee meaningful.

## Figures

### How are the figures generated?

`scripts/run_kernels.py` calls `render_all(graph, registry, …)` (re-exported from
`src/figures/plots/registry_io.py` as `src.figures.plots.render_all`), which writes
deterministic PNGs to `output/figures/` (illustrative sample below — the full figure
inventory is in [`quickstart.md`](quickstart.md) and `output/figures/figure_registry.json`):

- `curriculum_dag.png` — the prerequisite graph laid out by stratum (x) × depth (y),
  with direct stratum/root labels, quiet edges, and graph invariant stats.
- `dependency_strata_flow.png` — a source/target stratum matrix for prerequisite edges,
  with row/column totals, per-stratum skill counts, and a hatched backward-dependency zone.
- `scholarship_coverage.png` — citation source coverage by scholarship lane and
  manuscript section.
- `free_energy_descent.png` — a supplemental VFE sweep over `q(present)`, showing the
  posterior minimum and the negative log-evidence line.
- `efe_decomposition.png` — supplemental sample/commit expected free energy plus a
  sensor-precision sweep showing where the information-seeking preference changes.
- `vfe_efe_skilltree_bridge.png` — supplemental bridge from VFE/EFE figures to the real
  SkillTree subjects, skills, prerequisite edges, learn-route fragments and quiz-route
  fragments.

Every numeric input comes from the `ClaimRegistry` or the `CurriculumGraph`; the
scholarship figure comes from the validated citation source matrix. `matplotlib` uses
the headless `Agg` backend.

### How do I add a figure?

Add a `plot_*` function to `src/figures/plots/` that reads its values from the registry
or graph (never hand-typed), then add it to `render_all()`. Reference the resulting PNG
from a manuscript section with a relative path (`../output/figures/<name>.png`).

## SkillTree export and seeding

### How does the export work?

`scripts/export_skilltree.py` runs a fail-closed pipeline: build + validate the DAG →
build the kernel-derived registry → run the provenance gate (`validate_curriculum` +
`lint_graph`) → `render_graph` substitutes every `{{claim:NAME}}` in every learner-facing
field → `src/skilltree/exporter.py` maps the graph onto SkillTree's `Project → Subject →
Skill` model and writes `output/data/skilltree_project.json`. Prerequisite edges become
SkillTree **dependencies**; `Quiz`-typed skills' assessments become **quizzes**. If any
token is unbacked or any bare result number is found, nothing is written.

### How do I seed a live SkillTree instance?

`./scripts/run_skilltree.sh` brings up SkillTree (Postgres + skills-service) via
`docker compose`, waits for the REST API at `http://localhost:8080`, then runs
`scripts/bootstrap_local_skilltree.py` by default. The bootstrap path creates/reuses
local `FORM` auth, builds + provenance-renders the project, drives
`src/skilltree/seeder.py` to create it over REST in dependency-safe (topological) order,
and verifies trusted-client token exchange. The live seed requires Docker; without it,
the export-to-JSON path still works fully offline. Use `scripts/seed_skilltree.py`
directly only when the target deployment supports explicit admin bearer-token writes.

## See also

- [`quickstart.md`](quickstart.md) — basic commands.
- [`troubleshooting.md`](troubleshooting.md) — symptom-driven recipes.
- [`forking_guide.md`](forking_guide.md) — extending the curriculum and kernels.
- [`output_conventions.md`](output_conventions.md) — the `output/` tree and regeneration.
- [`architecture.md`](architecture.md) — module boundaries.
- [`../AGENTS.md`](../AGENTS.md) — invariants and the provenance chain.
