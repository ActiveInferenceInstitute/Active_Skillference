# `src/dashboard/` — local learner dashboard

A read-only shell over generated artifacts and official SkillTree views.
`server.py` is the small HTTP server; `payload.py`, `status.py` and
`artifacts.py` build its JSON; `artifact_catalog.py` and `figure_metadata.py`
register the evidence surfaces; `graph_analysis.py` serves the additive graph
recommendation; `live_validation.py` runs the live parity check.

SkillTree owns progress, ranking, quizzes and learner records. The dashboard
must not become a second implementation or an app-owned authentication layer.
The static frontend lives in [`assets/`](assets/).

Run: `uv run python scripts/serve_learner_dashboard.py`.
Parent guide: [`../AGENTS.md`](../AGENTS.md).
