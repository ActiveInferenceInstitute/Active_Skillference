# `src/figures/` — figure registry and renderers

`registry.py` loads the typed figure registry and its chart contract;
`registry_manifest.py` holds the canonical rows and semantic overrides;
`table_companions.py` emits the table companions. The renderers live in
[`plots/`](plots/).

`plots.render_all()` writes the PNGs and `figure_registry.json`. Numeric inputs
come from the curriculum graph and the validated audit payloads, never from
literals in a renderer. Rendering is headless (`Agg`).

Check: `uv run pytest tests/test_figures.py -q`.
Parent guide: [`../AGENTS.md`](../AGENTS.md).
