# Methods: SkillTree Export, Dashboard Ownership, and Publication Surfaces {#sec:methodology-skilltree-dashboard-publication}

## SkillTree export as a dependency-safe project, subject, skill, and quiz map

<!-- claim-support:method_skilltree_export -->
`src/skilltree` converts the validated, provenance-rendered graph into SkillTree's Project
-> Subject -> Skill model, emitting prerequisite **learning-path dependencies** and a
**quiz** per skill from its assessment questions. A REST client and seeder create the
project on a configured SkillTree instance, when available, in dependency-safe topological order: subjects, then quizzes,
then skills, then dependencies. Quiz definitions must exist before quiz-gated skills are
created, and dependencies are assigned only after both endpoint skills exist. The REST
contract is verified against a local
`pytest-httpserver` mirror of SkillTree's documented endpoints, so the integration is
tested without requiring a running Java service.

## Learner dashboard as a local lesson surface and read-only SkillTree handoff

<!-- claim-support:method_dashboard_handoff -->
The local learner dashboard is intentionally a shell rather than a competing learning
runtime. It reads generated artifacts (`skilltree_project.json`, claims, stats, figures,
and the rendered manuscript), probes SkillTree's public status endpoint, and mounts the
official `@skilltree/skills-client-js` learner display when a local trusted-client bridge
is ready. The bridge keeps SkillTree credentials server-side: browser code sees only the
configured service URL, project id, and a dashboard-local token endpoint.

The curriculum explorer in the dashboard is therefore read-only. It renders the exported
subjects, skills, quiz identifiers, and prerequisites so authors can inspect the exact
artifact that will be seeded. The **Learn** action opens a local modular lesson record
for the selected skill from `course_material_index.json`: concept, prerequisite context,
downstream role, assessment summary, provenance note, related local skills, and pinned
external pointers. **Open Subject** exits to the official SkillTree subject learning path
(`/subjects/{subjectId}`), where SkillTree lists subject progress, rank, and quiz
affordances. **Quiz** deep-links to
`/subjects/{subjectId}/skills/{skillId}/quizzes/{quizId}`. This distinction matters
operationally. Lesson summaries, search, artifact previews, and status summaries are
project-owned conveniences; progress, ranking, scoring, and completion remain
SkillTree-owned learner state.

## Publication surfaces for cover, page-two atlas, figures, and artifact audits

<!-- claim-support:method_cover_asset -->
The first and second pages are also generated, not hand-composed.
`scripts/run_kernels.py` writes `active_skillference_cover.png` from the live curriculum
graph, claim registry and roadmap metrics, and writes `active_skillference_skill_atlas.png`
from every authored skill name in the curriculum graph. The cover audit checks that
`book.cover.image` resolves to the cover PNG; the front-matter visual audit checks that
`front_matter.page_two_visual.image` resolves to the atlas PNG. Both audits require a
nonblank image, dashboard exposure as non-figure artifacts, and exclusion from
`figure_registry.json`. This keeps the public entry surfaces aligned with the same
artifact layer that drives the results figures while preserving the stricter
cross-reference contract for numbered manuscript figures.
