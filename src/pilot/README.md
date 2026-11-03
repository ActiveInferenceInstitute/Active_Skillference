# `src/pilot/` — learner-pilot protocol contract

`contract.py` validates the protocol-only learner-pilot contract:
`load_pilot_contract()` reads a JSON object and `validate_pilot_contract()`
checks that the protocol is measurable, privacy-bounded and non-causal. Failures
raise `PilotContractError`.

The package stores no learner state and makes no efficacy claim. The schema and
privacy boundary are documented in [`../../docs/pilot/`](../../docs/pilot/).

Check: `uv run python scripts/validate_learner_pilot_contract.py`.
Parent guide: [`../AGENTS.md`](../AGENTS.md).
