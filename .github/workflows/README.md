# `.github/workflows/` — CI jobs

`gates.yml` defines two jobs:

- `gates` — locked sync, Ruff check/format, mypy, curriculum and artifact
  builds, the provenance/scholarship/manuscript validators, and the test suite
  with the 90% coverage floor.
- `gnn conformance (pinned)` — fetches the commit in
  [`../../gnn/upstream.json`](../../gnn/upstream.json), provisions its own
  Python 3.12 environment, validates the specification, and runs
  `tests/test_gnn_conformance.py`.

Live Docker, SkillTree and browser proofs stay local. Keep the hosted job
names stable. The required GNN merge status is
[`gnn conformance (local)`](../../README.md#required-local-gnn-check).
