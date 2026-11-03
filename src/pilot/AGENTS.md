# AGENTS.md — `src/pilot/`

- Keep the contract protocol-only. Do not add learner records, identifiers,
  storage or an outcome claim.
- Validation stays fail-closed: missing privacy, feasibility or missing-data
  fields raise `PilotContractError`.
- Read-only SkillTree exports only. No writes, no live calls from validation.
- Change the schema and [`../../docs/pilot/`](../../docs/pilot/) together, with
  a test for both the accepted and rejected shape.
- Parent rules: [../AGENTS.md](../AGENTS.md).
