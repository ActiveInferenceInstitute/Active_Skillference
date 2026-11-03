# AGENTS.md — `src/integration/`

- This is a live proof, not a unit test. Do not make a green offline run imply
  that Docker or the browser proof ran.
- Bind local services to loopback. Never add a public host default, a remote
  URL or a deployment helper here.
- Restart a stale browser session at most once, as
  `ensure_browser_session_responsive` does; then fail with the named harness
  cause.
- Do not duplicate dashboard, SkillTree or curriculum logic. Call the owning
  package and assert on its real output.
- Parent rules: [../AGENTS.md](../AGENTS.md).
