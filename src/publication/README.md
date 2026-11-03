# `src/publication/` — release boundary

`zenodo.py` reserves a Zenodo concept DOI for an unpublished draft and reads the
token from `ZENODO_PROD_TOKEN`. It deliberately has no publish call: minting a
live DOI is an outward-facing action for a human running release tooling, not a
build step.

The module talks to `https://zenodo.org/api` with a 60-second timeout and raises
`ZenodoError` on an unusable response. Nothing here runs during tests, imports or
artifact builds.

Parent guide: [`../AGENTS.md`](../AGENTS.md). Release status:
[`../../docs/publication_readiness.md`](../../docs/publication_readiness.md).
