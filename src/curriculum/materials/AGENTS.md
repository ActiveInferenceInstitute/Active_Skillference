# AGENTS.md — `src/curriculum/materials/`

- Every material row needs a resolvable source in
  `data/course_material_sources.yaml`; do not invent a URL or a commit.
- Keep records read-only projections of the graph and source catalog. No learner
  progress, ranking or completion state belongs here.
- Validation is fail-closed: an unaligned skill, quiz or material must fail
  `scripts/validate_course_material_alignment.py`.
- Keep the JSON shape stable; the dashboard and manuscript variables read it.
- Parent rules: [../AGENTS.md](../AGENTS.md).
