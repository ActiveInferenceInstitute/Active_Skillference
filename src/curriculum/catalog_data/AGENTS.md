# AGENTS.md — `src/curriculum/catalog_data/`

- Append skills with `_s(...)`/`_q(...)`. Give each a unique `skill_id`, a
  stratum, an objective, and prerequisites that already exist.
- Every description number is a claim token. No literal result values.
- Keep `assembly.py` thin; subject construction belongs in the `subjects_*`
  modules and their aggregated `_ext_*` sources.
- Do not add graph rules here. Validation belongs in `../graph.py` and
  `../quality.py`.
- Rebuild and test after edits:
  `uv run python scripts/build_curriculum.py` then
  `uv run pytest tests/test_curriculum_catalog.py -q`.
- Parent rules: [../AGENTS.md](../AGENTS.md).
