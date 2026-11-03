# AGENTS.md — `.github/`

- Keep action references pinned to full commit SHAs with the release in a
  trailing comment. `dependabot.yml` owns upgrades.
- Keep the offline/live split. Do not add a job that pretends to run the Docker
  or browser proofs; those stay local and explicit.
- The `gnn-conformance` job reads its tag and commit from
  [`../gnn/upstream.json`](../gnn/upstream.json); do not duplicate the pin here.
- Keep `permissions` least-privilege and `timeout-minutes` bounded.
- Parent rules: [../AGENTS.md](../AGENTS.md).
