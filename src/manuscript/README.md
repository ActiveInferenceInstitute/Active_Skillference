# `src/manuscript/` — manuscript surface validation

- `audit.py` — validates `figure_registry.json` against manuscript figure
  declarations, `[@fig:...]` references, readable PNGs, caption/alt text,
  semantic metadata and dashboard artifacts; writes `manuscript_artifacts.json`.
- `claim_support.py` — validates `claim-support` anchors against evidence
  classes, citations, variables, claim tokens, figures and limitations.
- `variables.py` — keeps generated counts bound to tokens, not prose literals.
- `american_english.py` — rejects British spelling variants in authored prose.
- `web_math.py` — checks rendered HTML that carries math loads MathJax.

Drivers: `scripts/validate_manuscript_artifacts.py`,
`scripts/validate_claim_support.py`, `scripts/validate_manuscript_variables.py`,
`scripts/validate_american_english.py`.

Parent guide: [`../AGENTS.md`](../AGENTS.md). Writing rules:
[`../../docs/agent_instructions.md`](../../docs/agent_instructions.md).
