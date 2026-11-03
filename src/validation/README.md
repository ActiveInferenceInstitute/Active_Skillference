# `src/validation/` — shared finding type

`finding.py` defines the frozen `Finding` dataclass (`code`, `location`,
`message`), the structural `IssueLike` protocol, and `finding_from_issue()`.
Gate dataclasses across the project adapt their issues to this shape so one
report renderer can print them.

Parent guide: [`../AGENTS.md`](../AGENTS.md).
