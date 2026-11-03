# `src/provenance/` — claim registry and token binding

`claims.py` holds `ClaimRegistry`, which records named numeric claims with
units, source and description. `binding.py` substitutes `{{claim:NAME}}` tokens,
fails closed on unbacked or malformed tokens, and lints bare decimal result
numbers in learner-facing prose.

The chain is: kernel example registers a claim, skill content references the
token, and export fails if the token cannot resolve. `output/data/claims.json`
is the emitted ledger.

Check: `uv run pytest tests/test_provenance.py -q`.
Parent guide: [`../AGENTS.md`](../AGENTS.md).
