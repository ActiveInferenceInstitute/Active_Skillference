# AGENTS.md — `src/scholarship/`

- Every authored citation resolves to a BibTeX entry and a source-role row. A
  missing row is a failure, not an "unclassified" pass.
- Keep network health separate from coverage. A dead link is reported in its own
  bucket; it does not silently satisfy or fail the role matrix.
- Never downgrade a specific source role to a generic one to make a gate green.
- The audit JSON is deterministic. Sort rows and omit timestamps.
- Run `uv run python scripts/analyze_scholarship.py` after citation edits.
- Parent rules: [../AGENTS.md](../AGENTS.md).
