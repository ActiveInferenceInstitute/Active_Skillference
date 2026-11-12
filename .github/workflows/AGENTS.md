# AGENTS.md — `.github/workflows/`

- `gates.yml` is the only workflow. Add a job only when it can run on a hosted
  runner; live Docker and browser proofs stay local.
- Every step runs an arm of the repository's single gate entry point,
  [`../../gates.sh`](../../gates.sh). Never inline the command text here: a second
  copy drifts from the arm a contributor runs locally.
- Keep the hosted `gnn conformance (pinned)` job name and read its pin from
  `gnn/upstream.json`. The required merge status is
  [`gnn conformance (local)`](../../README.md#required-local-gnn-check).
- The conformance lane must fail, never skip, when the pinned fetch or parser
  provisioning fails.
- Mirror local commands; the offline job should not invent a stricter command
  that `AGENTS.md` does not document.
- Parent rules: [../AGENTS.md](../AGENTS.md).
