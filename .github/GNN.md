# GNN conformance

`gnn conformance (pinned)` is defined in `.github/workflows/gates.yml` as the
`gnn-conformance` job and reads `gnn/upstream.json`, which pins
`ActiveInferenceInstitute/Generalized_Notation_Notation` at `v5.0.3`
(`8f293d9ba810e6eda5c09842d9c7ed9ffa5f92c1`).

The job fetches that commit into its own checkout, then runs
`uv run python scripts/validate_gnn_spec.py`: the script checks the pinned tag
and commit resolve to the same object, extracts the pinned `src/gnn` tree with
`git archive`, and parses `gnn/discrete_active_inference_agent.gnn.md` with the
pinned `python -m gnn.extract`. The extracted matrices must match the kernel's
canonical two-state, two-observation, two-action model in `src/kernels/`.
`tests/test_gnn_conformance.py` repeats that extraction and also checks the pin
record, the declared specification sections and the declared dimensions. It
does not scan the rest of the repository for `*.gnn.md`; the claim covers that
one specification and the pin.