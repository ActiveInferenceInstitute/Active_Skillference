# `src/dashboard/assets/` — dashboard frontend

`index.html`, `app.js` and `styles.css` are the vanilla HTML/CSS/JS learner
dashboard. `vendor/skills-client-js.esm.min.js` is the pinned official
SkillTree client; it is vendored, not built.

The frontend renders the payloads from [`..`](..) and embeds the official
SkillTree display. It follows the root [`../../../DESIGN.md`](../../../DESIGN.md)
token contract and has no npm build step.

Parent guide: [`../AGENTS.md`](../AGENTS.md).
