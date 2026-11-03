# AGENTS.md — `src/figures/`

- Keep rendering deterministic and headless. Set `MPLBACKEND=Agg`; do not open a
  window or read the clock for a label.
- Numeric inputs come from the graph or a validated audit payload. No hardcoded
  results in a renderer.
- A new figure needs a registry row, filename, caption, alt text and semantic
  metadata; the manuscript audit cross-checks them.
- Keep `figure_registry.json` and the dashboard artifact catalog in step; both
  name the same files.
- Parent rules: [../AGENTS.md](../AGENTS.md).
