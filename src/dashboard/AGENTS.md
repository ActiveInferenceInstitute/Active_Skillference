# AGENTS.md — `src/dashboard/`

- Keep payload shapes stable. `/api/status`, `/api/course-materials`, graph,
  artifact and SkillTree-link responses have contract tests; change both sides
  together.
- The CSP starts at `default-src 'none'` and must keep the SkillTree origin in
  `frame-src` and its `ws://`/`wss://` origin in `connect-src`.
- `?defer_live=1` skips only the live parity round trip. Never let a deferred
  block read as a passed check; validators use the default path.
- Bind loopback only. Do not add a remote host default or an app-owned login.
- Parent rules: [../AGENTS.md](../AGENTS.md). Design tokens:
  [`../../DESIGN.md`](../../DESIGN.md).
