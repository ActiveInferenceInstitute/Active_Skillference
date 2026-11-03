# `src/kernels/` — pure Active Inference math

Deterministic NumPy/SciPy functions in nats. This package is the only source of
quantitative values used in learner-facing content.

- `information.py` — entropy, KL divergence, cross-entropy, mutual information, surprise.
- `distributions.py` — softmax, normalize, stable logs, Dirichlet expectations.
- `inference.py` — Bayes posterior, variational free energy, log evidence, ELBO.
- `active_inference.py` — expected free energy, policy posterior, `DiscreteActiveInferenceAgent`.
- `predictive_coding.py` — precision-weighted descent to the analytic minimum.
- `examples.py` — fixed-input worked examples and `build_claim_registry()`.

Check: `uv run pytest tests/test_kernels_*.py -q`.
Parent guide: [`../AGENTS.md`](../AGENTS.md). GNN specification: [`../../gnn/README.md`](../../gnn/README.md).
