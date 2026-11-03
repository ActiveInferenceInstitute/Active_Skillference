# `src/scholarship/` — citation source-role coverage

`coverage.py` parses the authored manuscript citations, resolves them against
`manuscript/references.bib`, checks each one against a source-role row in
`data/scholarship_sources.yaml`, and writes `scholarship_coverage.json`.
`source_health.py`, `source_health_network.py` and `source_health_report.py`
separate locator and role problems from dead-link and bot-block results.
`frontier_sources.py` and `gap_report.py` keep frontier and boundary support out
of the genuine source-health bucket.

Build: `uv run python scripts/analyze_scholarship.py`.
Parent guide: [`../AGENTS.md`](../AGENTS.md). Method:
[`../../docs/scholarship_coverage.md`](../../docs/scholarship_coverage.md).
