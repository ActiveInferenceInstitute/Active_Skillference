# AGENTS.md — `src/validation/`

- Keep `Finding` frozen and its fields stable; reports depend on
  `code at location: message`.
- Add gate-specific issue types as `IssueLike` objects and adapt them with
  `finding_from_issue()` rather than changing `Finding`.
- No printing or exiting here. Return findings; the calling script owns the
  process status.
- Parent rules: [../AGENTS.md](../AGENTS.md).
