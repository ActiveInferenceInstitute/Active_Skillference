# `src/curriculum/materials/` — local Learn records

Builds the modular dashboard "Learn" records from the curriculum graph and
`data/course_material_sources.yaml`. `builders.py` assembles records,
`validation.py` checks them, `github_sources.py` resolves pinned GitHub
citations, and `models.py`/`helpers.py` hold the shared types.

The contract keeps material sources traceable to a real URL or commit while
leaving learner state to SkillTree. The validation entry point is
`write_course_material_artifacts`.

Check: `uv run python scripts/validate_course_material_alignment.py`.
Parent guide: [`../AGENTS.md`](../AGENTS.md).
