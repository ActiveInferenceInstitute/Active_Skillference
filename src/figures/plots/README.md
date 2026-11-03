# `src/figures/plots/` — figure renderers

One module per figure family: `curriculum.py`, `kernels.py`,
`scholarship_coverage.py`, `scholarship_source_map.py`,
`scholarship_source_health.py`, `front_matter_cover.py`,
`front_matter_atlas.py`, `graph_diagnostics.py`, `roadmap.py` and
`validation.py`. `registry_io.py` owns `FigureRenderContext` and `render_all()`;
`style.py` holds the shared palette; `registry_helpers.py` and
`validation_data.py`/`validation_intent.py` support the registry and its checks.

Parent guide: [`../AGENTS.md`](../AGENTS.md).
