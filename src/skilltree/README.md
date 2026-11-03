# `src/skilltree/` — SkillTree export and live client

`model.py` holds the SkillTree project/subject/skill/quiz dataclasses.
`exporter.py` projects the curriculum graph to that model; `seeder.py` creates
project → subjects → quizzes → skills → dependencies in order.
`client.py`, `transport.py` and `admin_ops.py` are the REST boundary;
`dependency_reconciler.py` checks live prerequisite edges.
`form_login_core.py`/`form_login_validation.py` and
`local_auth.py`/`local_auth_state.py` own the local FORM bootstrap.
`deployment_matrix.py` describes the browser-safe deployment modes.

Export: `uv run python scripts/export_skilltree.py`. Seed and reconcile need a
live instance. Parent guide: [`../AGENTS.md`](../AGENTS.md).
