# `.github/workflows/` — CI jobs

`gates.yml` defines two jobs, and every step delegates to an arm of
[`../../gates.sh`](../../gates.sh):

- `gates` — `sync`, `lint`, `types`, `artifacts`, `checks`, `test` (the 90%
  coverage floor), `docs`.
- `gnn-conformance`, displayed as `gnn conformance (pinned)` — provisions the
  commit in [`../../gnn/upstream.json`](../../gnn/upstream.json) and its own
  Python 3.12 parser runtime, then runs the `gnn` arm (the strict validator plus
  `tests/test_gnn_conformance.py`).

The conformance job keeps a separate environment because the extractor must
import from the pinned upstream tree, never from the project environment; hosted
jobs cannot share a filesystem, so that is the one install the workflow pays
twice. Both jobs use the uv cache and neither carries its own copy of a command.

Live Docker, SkillTree and browser proofs stay local. Keep the hosted job
names stable. The required GNN merge status is
[`gnn conformance (local)`](../../README.md#required-local-gnn-check).

Arm-by-arm detail, measured runtimes, and the pinned action SHAs:
[`../../docs/gates.md`](../../docs/gates.md).
