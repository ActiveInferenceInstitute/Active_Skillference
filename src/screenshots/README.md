# `src/screenshots/` — captured dashboard evidence

`manifest.py` defines the fixed capture views and their chart-contract metadata.
`capture.py` drives a live local dashboard through the browser automation and
writes PNGs plus `screenshot_provenance.json`. `staging.py` prepares the capture
inputs.

Captures land in `manuscript/assets/screenshots/` at a pinned 1440×900 viewport;
the figure registry and dashboard artifact catalog register those exact paths.
The rows are evidence from a running stack, not deterministic renders.

Driver: `scripts/capture_dashboard_screenshots.py`.
Parent guide: [`../AGENTS.md`](../AGENTS.md).
