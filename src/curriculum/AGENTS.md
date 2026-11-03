# AGENTS.md — `src/curriculum/`

- Keep the graph acyclic and fully connected foundations→applications. Roots
  stay in `MATH_FOUNDATIONS` and `PROBABILITY`; ids stay unique and
  prerequisites must resolve.
- Add skills as data in `catalog_data/` or an `_ext_*.py` module, not in
  `graph.py`. Use the `_s`/`_q` shorthands from `authoring.py`.
- Any learner-facing number is a `{{claim:NAME}}` token. Author input values
  inside `$...$` math; the bare-number linter must stay green.
- Imports are `src.*` only. A bare `curriculum.` import creates a second module
  identity and breaks the DAG types.
- Run `uv run python scripts/build_curriculum.py` after edits, plus the
  curriculum tests. Parent rules: [../AGENTS.md](../AGENTS.md).
