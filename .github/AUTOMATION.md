# `.github/` — repository automation

`dependabot.yml` declares the dependency-update policy. `workflows/gates.yml`
is the only workflow: it runs the offline gate arms of [`../gates.sh`](../gates.sh),
plus the pinned-GNN conformance lane, on pushes to `main`, pull requests and
manual dispatch. Each workflow step is one arm, so CI carries no second copy of
a gate command — see [`../docs/gates.md`](../docs/gates.md).

The live Docker + SkillTree + browser proofs are deliberately not simulated
here; see [`workflows/README.md`](workflows/README.md) and the project
[`../AGENTS.md`](../AGENTS.md) gate list.

Local check before editing a workflow: `./gates.sh all` runs every arm the
workflow calls (`gnn` needs a prepared `GNN_ROOT`; see the root
[`../README.md`](../README.md#required-local-gnn-check)).
