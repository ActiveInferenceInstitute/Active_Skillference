# `.github/` — repository automation

`dependabot.yml` declares the dependency-update policy. `workflows/gates.yml`
is the only workflow: it runs the offline gate set and the pinned-GNN
conformance job on pushes to `main`, pull requests and manual dispatch.

The live Docker + SkillTree + browser proofs are deliberately not simulated
here; see [`workflows/README.md`](workflows/README.md) and the project
[`../AGENTS.md`](../AGENTS.md) gate list.

Local check before editing a workflow: `uvx ruff check src scripts tests` and
`uv run pytest --cov=src --cov-fail-under=90` cover the same code paths the
offline job runs.
