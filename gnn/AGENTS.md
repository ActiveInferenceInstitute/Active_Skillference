# AGENTS.md — `gnn/`

- `discrete_active_inference_agent.gnn.md` and
  [`../src/kernels/active_inference.py`](../src/kernels/active_inference.py) are
  one contract. Change them together, with
  [`../src/gnn_conformance.py`](../src/gnn_conformance.py) and
  [`../tests/test_gnn_conformance.py`](../tests/test_gnn_conformance.py).
- Read the pin from `upstream.json`; never read a GNN checkout's working tree.
  The validator extracts the recorded commit with `git archive`.
- A pin change needs a fresh conformance run:
  `uv run python scripts/validate_gnn_spec.py` and
  `uv run pytest tests/test_gnn_conformance.py -q`.
- Parent rules: [../AGENTS.md](../AGENTS.md).
