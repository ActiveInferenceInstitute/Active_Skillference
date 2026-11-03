# AGENTS.md — `src/publication/`

- Never publish implicitly. Do not add a publish call, a background request or a
  side effect on import.
- Read the token from `ZENODO_PROD_TOKEN`; never commit, log or echo it.
- Network calls need an explicit operation, a bounded timeout and a typed error.
  Tests use a local server or a stub, never the real Zenodo API.
- A new release action needs a test proving the no-op path writes and sends
  nothing.
- Parent rules: [../AGENTS.md](../AGENTS.md).
