# `gnn/` — pinned GNN specification

`discrete_active_inference_agent.gnn.md` is the Generalized Notation Notation
specification of the discrete-agent kernel's generative model.
`upstream.json` records the parser pin: repository
`ActiveInferenceInstitute/Generalized_Notation_Notation`, tag `v5.1.0`, commit
`75c834bd8519dc7b5adc4d24f16bf393cfd1ecdf`.

`scripts/validate_gnn_spec.py` extracts that pinned commit with `git archive`
and validates the specification. `tests/test_gnn_conformance.py` checks the
specification against [`../src/kernels/active_inference.py`](../src/kernels/active_inference.py).
CI runs both in `gnn conformance (pinned)`.
