# AGENTS.md — `.github/workflows/`

- `gates.yml` is the only workflow. Add a job only when it can run on a hosted
  runner; live Docker and browser proofs stay local.
- Keep the `gnn conformance (pinned v5.0.3)` job name. It is the required-check
  identity, and the pin must come from `gnn/upstream.json`.
- The conformance lane must fail, never skip, when the pinned fetch or parser
  provisioning fails.
- Mirror local commands; the offline job should not invent a stricter command
  that `AGENTS.md` does not document.
- Parent rules: [../AGENTS.md](../AGENTS.md).
