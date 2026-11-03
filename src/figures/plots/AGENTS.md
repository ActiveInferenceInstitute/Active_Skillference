# AGENTS.md — `src/figures/plots/`

- One renderer per registered figure. Register it in `registry.py`; do not add a
  second filename or caption rule here.
- Use `style.py` tokens and the headless backend. No random, date or
  environment-dependent labels.
- Read inputs through `FigureRenderContext`; do not reach into another package's
  private state.
- A renderer change that moves a label, filename or caption must update the
  manuscript declaration and dashboard artifact in the same change.
- Parent rules: [../AGENTS.md](../AGENTS.md).
