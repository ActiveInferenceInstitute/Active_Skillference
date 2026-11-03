# AGENTS.md — `src/dashboard/assets/`

- No frontend framework, bundler or npm dependency. Keep this surface vanilla and
  directly servable.
- Read [`../../../DESIGN.md`](../../../DESIGN.md) before styling; use declared CSS
  tokens, not raw colors.
- Do not rename payload keys or reshape a response from the browser side alone.
  Update `src/dashboard/` and its tests in the same change.
- Treat `vendor/skills-client-js.esm.min.js` as third-party. Do not edit it by
  hand; replace it only with a reviewed upstream build.
- Parent rules: [../AGENTS.md](../AGENTS.md).
