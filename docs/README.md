# docs/ — Project Documentation

> **Operational guide** for Active Skillference — a high-integrity micro-learning
> platform for Active Inference (AIF) and the Free Energy Principle (FEP).

**Quick Reference:** [Quickstart](quickstart.md) | [Learner Dashboard](learner_dashboard.md) | [Architecture](architecture.md) | [Active TODO Details](todo/) | [Scholarship](scholarship_coverage.md) | [Learner Pilot](pilot/) | [IP/License](ip_license_status.md) | [Publication Readiness](publication_readiness.md) | [Release Inventory](release_readiness_inventory.md) | [Curriculum Audit](curriculum_expert_audit.md) | [Agent Instructions](agent_instructions.md) | [Testing](testing_philosophy.md) | [Rendering](rendering_pipeline.md) | [Style](style_guide.md) | [Syntax](syntax_guide.md) | [Index](AGENTS.md)

## Purpose

The `docs/` directory contains the behavioral and architectural rules that govern work
on Active Skillference. The project renders the AIF/FEP body of knowledge as a
*validated prerequisite graph* across all eight strata and exports it to
the [SkillTree](https://skilltreeplatform.dev) gamification framework, where **every
quantitative claim a learner sees is produced by a tested computational kernel, never
hand-typed**. Citations are also mapped through a source-role matrix before generated
artifacts are emitted. Provenance over assertion is the defining principle; the docs here
exist to keep it true.

The authoritative file index for this folder lives in [`AGENTS.md`](AGENTS.md). The
project-level guides live one level up: [`../README.md`](../README.md) (overview),
[`../AGENTS.md`](../AGENTS.md) (agent guidance), and [`../ISA.md`](../ISA.md) (the Ideal
State Artifact / build spec).

Roadmap work is source-of-truth driven from [`../tasks.yaml`](../tasks.yaml).
[`../TODO.md`](../TODO.md) is generated and forward-only, while [`todo/`](todo/) contains
one generated implementation handoff page for each active TODO entry.

## What "high-integrity" means here

Four enforced invariants, all checked by the project's own code:

- **Provenance binding.** Learner-facing numbers appear only through `{{claim:NAME}}`
  tokens that resolve to values registered by a tested kernel. The export fails closed
  on any unbacked or malformed token, and a linter rejects bare result numbers typed
  into prose.
- **A validated DAG.** The curriculum is checked to be acyclic, free of dangling
  prerequisites, connected foundations→applications, with roots only in the two
  foundational strata.
- **Scholarship coverage.** Authored citations must resolve to BibTeX entries and to
  rows in `data/scholarship_sources.yaml`, where each source has a lane, role, kind, and
  locator.
- **Tested kernels.** Information theory, Bayesian/variational inference, and a discrete
  active-inference agent are deterministic no-mock reference implementations covered by
  the project-wide `src/` coverage gate.

## The eight strata

`mathematics → probability → information theory → variational methods → the Free Energy
Principle → active inference → computation → applications`

## Cold start

One command takes a fresh checkout to the interactive learner surface, announcing each
step and what to do if it stops:

```bash
./run.sh              # dependencies, build, live SkillTree, learner dashboard
./run.sh --offline    # no Docker: build and serve generated artifacts only
./run.sh --check      # report readiness and exit without starting anything
```

The live path needs a running Docker daemon because SkillTree owns quizzes, completion,
points, and ranking. The offline path needs neither Docker nor a network and still serves
the curriculum explorer, generated lesson records, dependency graph, and artifact browser.
Individual pipeline commands are listed under Verification Commands below and in
[`quickstart.md`](quickstart.md).

## Contents

Grouped by the question you arrived with. Every file in this folder appears
exactly once; `AGENTS.md` carries the same set as a technical index and a test
fails if the two drift apart.

### Start here

| File | Purpose | Audience |
|---|---|---|
| [`quickstart.md`](quickstart.md) | 5-minute run: `uv sync` → build curriculum → run kernels → export → test | New users |
| [`faq.md`](faq.md) | Recurring questions: provenance, DAG, SkillTree | All |
| [`troubleshooting.md`](troubleshooting.md) | Diagnosed failures with fix commands | Developers |

### Architecture and conventions

| File | Purpose | Audience |
|---|---|---|
| [`architecture.md`](architecture.md) | Thin-orchestrator layers (kernels → provenance → curriculum → skilltree → figures), dependency direction, how to add a skill/kernel | Developers |
| [`style_guide.md`](style_guide.md) | Source-code rules: zero-mock, thin orchestrator, `src.*` imports, type hints, error messages | Developers |
| [`testing_philosophy.md`](testing_philosophy.md) | Zero-mock policy, test-file inventory, coverage mechanics (≥90% gate) | Developers, testers |
| [`agent_instructions.md`](agent_instructions.md) | Hard rules for AI agents: provenance, DAG, `src.*` imports, no mocks, coverage; verification checklist | AI agents, all developers |
| [`AGENTS.md`](AGENTS.md) | Technical index of this `docs/` folder; verification commands | Developers, agents |

### Authoring content

| File | Purpose | Audience |
|---|---|---|
| [`syntax_guide.md`](syntax_guide.md) | Markdown/LaTeX in skill + manuscript content; the `{{claim:NAME}}` token system; figure references | Content authors |
| [`scholarship_coverage.md`](scholarship_coverage.md) | Citation source-role matrix, validator, outputs, and edit protocol | Content authors, developers |
| [`rendering_pipeline.md`](rendering_pipeline.md) | Manuscript → PDF flow; preflight; `{{claim:NAME}}` token substitution | Content authors, developers |
| [`curriculum_expert_audit.md`](curriculum_expert_audit.md) | Deterministic expert-review sample over high-depth, high-fanout and templated curriculum surfaces | Maintainers, curriculum reviewers |
| [`forking_guide.md`](forking_guide.md) | Adapting the platform to a new curriculum domain | Developers, agents |

### Delivery and runtime

| File | Purpose | Audience |
|---|---|---|
| [`learner_dashboard.md`](learner_dashboard.md) | Local dashboard commands, routes, SkillTree ownership boundary, offline behavior | Learners, developers |
| [`output_conventions.md`](output_conventions.md) | `output/` directory layout, what's disposable, regeneration rules | Developers |
| [`output_inventory.md`](output_inventory.md) | Producer/consumer graph for pipeline artifacts | Developers |

### Release and governance

| File | Purpose | Audience |
|---|---|---|
| [`ip_license_status.md`](ip_license_status.md) | MIT declaration, third-party boundaries, DOI/public-repository blockers, and deployment review caveats | Maintainers, release reviewers |
| [`publication_readiness.md`](publication_readiness.md) | Initial static publication readiness, allowed claims, and remaining release blockers | Maintainers, release reviewers |
| [`release_readiness_inventory.md`](release_readiness_inventory.md) | Machine-checked dirty worktree, untracked-file, generated-output and blocker inventory for release isolation | Maintainers, release reviewers |
| [`pilot/`](pilot/) | Protocol-only learner-pilot contract, privacy boundary, export schema, and analysis sequence | Study designers, reviewers |
| [`todo/`](todo/) | Generated active roadmap handoff pages, one per open TODO item | Maintainers, agents |

## Quick Navigation

### Before modifying any source code

1. Read **[agent_instructions.md](agent_instructions.md)** — the invariants and the verification checklist.
2. Read **[architecture.md](architecture.md)** — the `src/` layer boundaries before touching file structure.
3. Read **[testing_philosophy.md](testing_philosophy.md)** — the zero-mock constraint before writing tests.

### Before editing the curriculum (`src/curriculum/catalog_data/`)

1. Read **[architecture.md](architecture.md) → How to add a skill / subject / kernel**.
2. Any learner-facing number must arrive through a `{{claim:NAME}}` token backed by
   `src/kernels/examples.py` — see **[syntax_guide.md](syntax_guide.md)**.
3. Re-run `uv run python scripts/build_curriculum.py` after edits — it re-validates the DAG.

### Before editing manuscript files (`manuscript/*.md`)

1. Read **[rendering_pipeline.md](rendering_pipeline.md)** — the manuscript → PDF flow.
2. Read **[syntax_guide.md](syntax_guide.md)** — the `{{claim:NAME}}` token system and figure references.
3. Read **[scholarship_coverage.md](scholarship_coverage.md)** before adding or changing citations.
4. Run `uv run python scripts/validate_american_english.py` before rendering if prose changed.

## Verification Commands

Run from the project root:

```bash
# Tests pass + coverage ≥90% on src/
uv run pytest tests/ --cov=src --cov-fail-under=90

# No mocks anywhere in tests/
grep -r "unittest.mock\|MagicMock\|@patch\|create_autospec" tests/ || echo "Clean"

# Imports use the src.* namespace (no bare kernels./curriculum./skilltree. imports)
grep -rnE "^(from|import) (kernels|curriculum|skilltree|provenance|figures)\b" src/ scripts/ tests/ \
    && echo "VIOLATION — bare import escapes the src.* namespace" \
    || echo "Clean — all imports under src.*"

# The DAG validates and prints its stats
uv run python scripts/build_curriculum.py

# Local dashboard Learn material validates
uv run python scripts/build_course_materials.py
uv run python scripts/validate_course_material_sources.py --online
uv run python scripts/validate_course_material_alignment.py

# Optional local learner dashboard status (read-only artifact + SkillTree check)
uv run python scripts/serve_learner_dashboard.py --check
```

## See Also

- [`../README.md`](../README.md) — Project overview and quick start.
- [`../AGENTS.md`](../AGENTS.md) — Project-level agent guidance and the provenance chain.
- [`../ISA.md`](../ISA.md) — The Ideal State Artifact (problem, principles, criteria, verification).
- [`../manuscript/AGENTS.md`](../manuscript/AGENTS.md) — Manuscript directory rules and the `{{claim:NAME}}` protocol.
- [`../vendor/README.md`](../vendor/README.md) — Running a live SkillTree instance (Docker / build-from-source).

## Local SkillTree login troubleshooting

If `http://localhost:8080` is up but the raw SkillTree login rejects
`active-skillference-admin@localhost.invalid` / `active-skillference-local`, the local
Docker volume likely predates the deterministic email-style bootstrap. Reset only the
local development runtime with:

```bash
uv run python scripts/reset_local_skilltree.py --confirm-local-reset
```

The command backs up ignored local auth state, resets the SkillTree/Postgres Compose
volume, restarts the strict full-app stack, and leaves the no-login learner dashboard at
`http://127.0.0.1:8765` running when proof succeeds.
