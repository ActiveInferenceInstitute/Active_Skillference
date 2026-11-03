# AGENTS.md — `src/screenshots/`

- These pixels are live-browser evidence. Never hand-edit a PNG or
  `screenshot_provenance.json`; rerun the capture instead.
- Keep the viewport and view list in `manifest.py` stable. A new view needs its
  registry row, dashboard artifact entry and manuscript consumer.
- Capture only a local, explicitly started stack. Do not point it at a remote
  host or store credentials in the provenance record.
- Keep the capture deterministic where it can be: fixed viewport, fixed route,
  explicit readiness wait.
- Parent rules: [../AGENTS.md](../AGENTS.md).
