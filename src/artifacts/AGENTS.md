# AGENTS.md — `src/artifacts/`

- Write atomically, through `json_io.write_json_artifact`; do not scatter
  `json.dump` calls through producers.
- Keep output deterministic: sorted keys, stable separators, no wall-clock
  timestamps or machine paths unless the payload schema explicitly owns them.
- Add or change a stable payload in `contracts.py` first, then update every
  reader. Consumers type their inputs with these `TypedDict` shapes.
- A malformed payload fails at the write boundary, not when a figure renders.
- Parent rules: [../AGENTS.md](../AGENTS.md).
