# Gates: one entry point, separately runnable arms

`./gates.sh` is the only gate entry point. Every check the project runs offline is an
arm of that script, and `.github/workflows/gates.yml` calls the arms — it does not carry a
second copy of any command. Running an arm locally executes exactly what CI executes for
that step.

```bash
./gates.sh              # default developer loop: lint, types, fast
./gates.sh all          # every CI arm, in CI order
```

## Arms

| Arm | Runs | Reads / writes |
| --- | --- | --- |
| `sync` | `uv sync --frozen` — the locked environment | `uv.lock` |
| `lint` | `uv run ruff check`, `uv run ruff format --check` over `src scripts tests` | read-only |
| `types` | `uv run mypy src` | read-only |
| `fast` | `uv run pytest -m "not slow"` | read-only |
| `test` | `uv run pytest --cov=src --cov-fail-under=90` | read-only |
| `artifacts` | `build_curriculum.py`, `run_kernels.py`, `export_skilltree.py` | writes `output/` |
| `checks` | the ten provenance / scholarship / manuscript / roadmap / metadata validators | reads `output/` |
| `docs` | `check_docs_links.py`, `z_generate_gate_metrics.py --check` | read-only |
| `gnn` | `validate_gnn_spec.py`, the pinned `tests/test_gnn_conformance.py` | needs `GNN_ROOT` |
| `render` | `render_manuscript.py`, `ensure_web_math.py`, `validate_web_math.py` | writes `output/pdf/`; normalizes the committed `output/web/*.html` in place when math needs the loader |
| `record` | times every arm except `render` (which needs a LaTeX toolchain), refreshes [`gate_metrics.md`](gate_metrics.md) | writes `docs/_generated/` |
| `list` | prints the arms | — |

Ordering is a real dependency, not a preference: `checks` and `test` read the artifacts
`artifacts` writes, and `record` refreshes the timing receipt `docs` verifies. Everything
else is independent and can run alone.

## The fast arm and the full arm

`fast` deselects the module-level suites marked `slow` — the ones that repaint every
figure or rebuild a full artifact set. The full arm (`test`) runs them and enforces the
`src/` coverage floor. CI runs the full arm; `fast` exists so a local editing loop does not
pay for a full artifact rebuild. Both use the same pytest selection mechanism
(`-m`, registered in `pyproject.toml`), so neither arm can silently collect nothing:
`--strict-markers` is on and a mistyped marker is an error.

## GNN conformance arm

`./gates.sh gnn` validates `gnn/discrete_active_inference_agent.gnn.md` against the parser
revision pinned in `gnn/upstream.json` (schema `gnn-importer-pin/v1`): tag `v5.0.3`,
commit `8f293d9ba810e6eda5c09842d9c7ed9ffa5f92c1`. It needs a prepared
pinned checkout and fails — never skips — when `GNN_ROOT` is missing or unusable. The
preparation commands are in [`../README.md`](../README.md#required-local-gnn-check); the
job that runs this arm in CI is `gnn-conformance`, displayed as
`gnn conformance (pinned)`, and [`.github/GNN.md`](../.github/GNN.md) records what it
parses.

## Render arm

`./gates.sh render` is the manuscript render path: it hydrates the authored sections
through `z_generate_manuscript_variables.py`, drives Pandoc → XeLaTeX, and normalizes the
web build for MathJax. It needs on `PATH`:

- `pandoc` (3.x; the manuscript relies on `raw_attribute`, fenced divs and MathJax support),
- `pandoc-crossref` built for the same Pandoc major version (it resolves `[@fig:label]`
  and `[@sec:label]`),
- a XeLaTeX engine (`xelatex`) with the packages `manuscript/preamble.md` loads.

A missing tool is named and the arm stops; it never emits a partial PDF. See
[`rendering_pipeline.md`](rendering_pipeline.md) for the file-by-file flow.

## CI mapping

| CI job (key) | Display name | Arms, in order |
| --- | --- | --- |
| `gates` | `gates` | `sync`, `lint`, `types`, `artifacts`, `checks`, `test`, `docs` |
| `gnn-conformance` | `gnn conformance (pinned)` | `gnn` (after provisioning the pinned parser runtime) |

Two jobs exist because the conformance lane must import the extractor from the pinned
upstream tree, never from the project environment — that isolation is the check. Hosted
jobs cannot share a filesystem, so each job installs the locked set once for itself; the
conformance job relies on `uv run` syncing on demand instead of an explicit sync step, and
both jobs share the uv cache (`astral-sh/setup-uv` with `enable-cache: true`). The
workflow pins `actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1` (v7.0.1) and
`astral-sh/setup-uv@68559e99cc807c1eb7e9238fd43a15bba460eec2` (v10.3.3). The repository
does not use the organization's composite
`ActiveInferenceInstitute/.github/.github/actions/setup-python-uv` action; both jobs call
`astral-sh/setup-uv` directly, and the uv version is pinned twice on purpose — once in the
action input and once as `[tool.uv] required-version` in `pyproject.toml` — so a drift
between them fails instead of silently changing the resolution.

The live half of the gate set (Docker, a real SkillTree, browser proofs, captured
screenshots) stays local and explicit. No arm here simulates it.

## Measured numbers

Per-arm wall times and the test/coverage counts are generated, not written by hand:
`./gates.sh record` times each arm (except `render`, which needs the LaTeX toolchain and is
timed on its own) and refreshes [`gate_metrics.md`](gate_metrics.md) from
the recorded receipt at [`_generated/arm_timings.json`](_generated/arm_timings.json).
`./gates.sh docs` fails when the document and the receipt disagree, so a stale measurement
cannot be published.
