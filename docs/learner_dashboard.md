# Learner Dashboard

The local learner dashboard is a project-owned shell around the official SkillTree
runtime. It exists to make the Active Skillference export inspectable and usable from one
local page; it is not a second SkillTree implementation.

SkillTree is an NSA-origin open-source training platform
([skills-service](https://github.com/NationalSecurityAgency/skills-service),
[code.nsa.gov](https://code.nsa.gov/)). That provenance is relevant to architecture and
source attribution, but it is not an endorsement of this curriculum or a deployment
assurance. Treat the dashboard as educational inspection infrastructure unless an
operator adds its own zero-trust, supply-chain, monitoring, and incident-response
controls.

## Run It

Live SkillTree plus dashboard:

```bash
./scripts/run_learning_dashboard.sh
```

This command starts Docker Compose (`skills-service` plus PostgreSQL), waits for
`http://localhost:8080/public/status`, regenerates the
curriculum/provenance/scholarship/artifact outputs,
bootstraps local SkillTree auth, seeds the `activeInference` project, then serves the
dashboard at `http://127.0.0.1:8765`.

The pinned local Docker stack uses SkillTree `FORM` password-auth mode. The dashboard
does not disable SkillTree auth; it creates or reuses one local root/admin account and
uses SkillTree's trusted-client token flow to proxy one fixed learner identity:
`local-learner`. Local bootstrap state is stored under ignored
`.active_skillference_local/`.

Raw SkillTree login remains available at `http://localhost:8080`. For a fresh local
Docker volume, the default development root credentials are:

```text
username: active-skillference-admin@localhost.invalid
password: active-skillference-local
```

These defaults are only for local development. Override fresh-bootstrap credentials with
`ACTIVE_SKILLFERENCE_LOCAL_ADMIN_USERNAME` and
`ACTIVE_SKILLFERENCE_LOCAL_ADMIN_PASSWORD`. If `.active_skillference_local/` already
contains `skilltree_auth.json`, that state file remains authoritative and is not silently
rewritten; inspect it with:

```bash
uv run python scripts/bootstrap_local_skilltree.py --show-local-credentials
```

If the raw SkillTree page is reachable but login fails with the documented defaults, the
local Docker volume likely predates the email-style root account. Reset only the local
development runtime and leave both sites running with:

```bash
uv run python scripts/reset_local_skilltree.py --confirm-local-reset
```

The reset backs up the ignored state file, removes the local SkillTree/Postgres volume,
recreates the default root account, reseeds `activeInference` through the app-ready
surface, and leaves the dashboard open at `http://127.0.0.1:8765`. The dashboard home
page includes a **Local SkillTree Login** card with the default username, password, raw
SkillTree link, reset command, and show-credentials command.

Full prerequisite parity is a separate long-running proof:

```bash
uv run python scripts/reconcile_live_dependencies.py --check-only
uv run python scripts/reconcile_live_dependencies.py --max-edges 5
uv run python scripts/reconcile_live_dependencies.py --max-runtime-seconds 900
uv run python scripts/reconcile_live_dependencies.py
uv run python scripts/validate_full_app_stack.py --skip-regenerate --keep-running
```

The live SkillTree dependency graph is authoritative. The ignored progress file is
refreshed from that graph and is only a resume/diagnostics aid, so a stale progress file
cannot be used as proof of full parity. Bounded reconciliation runs emit explicit partial
JSON with `stoppedReason` until all exported dependencies are live.

Because the graph — not the HTTP result — is the authority, a dependency write that times
out on the client but is visible in the live graph on the following authoritative read
counts as `confirmedAfterTimeout`, not as a failure. On Apple/ARM Docker emulation a
single prerequisite write can exceed the 600s client timeout and still land, so treating
that as an error aborted otherwise-healthy runs.

Strict full-app proof:

```bash
uv run python scripts/validate_full_app_stack.py
uv run python scripts/validate_full_app_stack.py --keep-running
```

Use this when reporting that the app is live. It starts or reuses the Docker Compose
SkillTree stack, regenerates project artifacts, bootstraps and seeds local SkillTree auth,
reconciles missing live prerequisite edges, starts the dashboard, requires `/healthz`,
requires live admin count parity, requires live dependency parity, checks
figure-registry/dashboard chart-contract parity, proves the raw SkillTree `FORM` login
through `chrome-devtools-axi`, and runs the Chrome console gate. Docker daemon
availability is a hard precondition: if Docker or Colima is not running, this command
fails rather than silently downgrading to artifact-only mode. `--app-ready` is the faster
local usability proof and is explicitly not a full dependency-parity proof.
`--keep-running` leaves the dashboard process open for manual inspection at
`http://127.0.0.1:8765`.

Artifact-only mode:

```bash
uv run python scripts/serve_learner_dashboard.py
uv run python scripts/serve_learner_dashboard.py --check
```

Artifact-only mode does not require Docker. SkillTree status shows offline, the official
learner panel shows a controlled fallback link, and the curriculum/artifact panels remain
usable if `output/data/skilltree_project.json` exists. If local auth is enabled but not
ready, the official panel names the local-auth blocker while leaving generated artifacts,
curriculum diagnostics, and local lesson material status visible. If course material is
missing, **Learn** shows a generated-material failure state instead of inventing a local
lesson.

## What It Owns

- Runtime panel: the deployment matrix plus a runtime-state JSON slice (config, SkillTree
  status, live parity, curriculum stats, claim/artifact counts). It deliberately omits the
  exported project and graph analysis, which are megabytes of JSON; **Full status JSON**
  links to `/api/status` for the complete payload.
- Runtime status: SkillTree reachability, active project id, generated artifact presence.
  The dependency metric displays live/exported parity when local admin graph access is
  available; otherwise it is labeled as exported-only. The live parity read costs a
  SkillTree login plus a full dependency-graph fetch, so the page paints from
  `/api/status?defer_live=1` (metric reads `N exported · checking live`) and swaps in the
  checked figure when the unqualified `/api/status` call returns. Validators and the proof
  artifacts always use the checked form; a deferred payload is never proof of parity.
- Curriculum explorer: read-only rendering of `output/data/skilltree_project.json`.
- Local lesson material: **Learn** opens the generated read-only lesson record for the
  selected skill from `output/data/course_material_index.json`.
- Curriculum diagnostics: reads `output/data/curriculum_diagnostic_gap_map.json` to show
  bottlenecks, long chains, assessment balance, and remediation rows.
- Scholarship health network: reads `output/data/scholarship_source_health_network.json`
  to keep dead links, bot blocks, role gaps, boundary sources, and uncited drift separate.
- SkillTree handoff links: **Open Subject** reopens the official SkillTree subject path,
  and **Quiz** reopens the subject-scoped SkillTree quiz path for the selected skill.
- Path prototype: the dashboard can display deterministic prerequisite-frontier candidates
  from the exported graph and routes each candidate to the official SkillTree subject and
  quiz surfaces. It does not claim personalization or effectiveness and does not store a
  learner profile.
- Raw SkillTree login/admin: `localhost:8080` is labeled as the SkillTree login/admin
  surface; the no-login learner entrypoint is the project dashboard at
  `http://127.0.0.1:8765`.
- Artifact links: README, docs, claims, scholarship coverage, stats, figure registry,
  manuscript artifact audit, course-material audit, figure previews, manuscript PDF, and
  web output. Registered figure cards put the full-size image link before the metadata,
  group the first-read contract as Question / Grain / Boundary / Failure, and then expose
  chart family, subtitle/source context, takeaway, encoding, data source, mobile reading
  note, QA role, claim-token count, visual grammar, and optional table-companion id behind
  the details disclosure. Dense companions come from
  `output/data/figure_table_companions.json`.
- Artifact integrity: the exported SkillTree project is structurally validated before it is
  summarized or served. Invalid collections, dangling quiz/dependency references, duplicate
  identifiers, and dependency cycles fail closed as unavailable artifacts rather than being
  rendered as an empty project. External course-material links are displayed only when they
  are absolute, credential-free HTTP(S) URLs; unsafe schemes remain plain text.
- SkillTree deployment matrix: exposes only browser-safe deployment mode status for local
  FORM bootstrap, ignored local state, token-backed admin seeding, and externally operated
  SkillTree. Admin secrets, client secrets, and bearer tokens remain server-side.
- Official display host: imports `@skilltree/skills-client-js` and configures
  `SkillsConfiguration` with `serviceUrl`, `projectId=activeInference`, and an absolute
  dashboard URL for the local `/api/skilltree/token` authenticator when bootstrap is
  ready.
- Local trusted-client bridge: `/api/skilltree/token` exchanges server-side project
  credentials with SkillTree and returns SkillTree's token response to the official
  client library. The route allows CORS only for the configured local SkillTree/dashboard
  origins so the SkillTree iframe can request its token without exposing secrets in
  static assets. `localAuth.ready` means the ignored bridge state is complete; it is not
  proof that the live SkillTree process is currently running or accepting browser
  passwords.

## Accessibility

The shell targets WCAG 2.1 Level A keyboard and structure basics: a visually-hidden
**Skip to main content** link (targets `#main`), visible `:focus-visible` outlines on
buttons/tabs/nav links, and a WAI-ARIA tab pattern on the view switcher (Arrow keys cycle,
Home/End jump to ends, roving `tabindex`, click still works). The subject dependency graph
uses server-computed `subjectLayout` lanes with subject counts, skill counts,
incoming/outgoing flow counts, and top incoming/outgoing partner summaries. It ships
alongside an accessible **prerequisite-flow table** (semantic
`<caption>`/`<th>`) built from the same server-computed `subjectFlows` data. The
prerequisite structure therefore remains legible to screen-reader and keyboard users, not
only as the SVG.

## What SkillTree Owns

SkillTree remains the system of record for learner state. Do not move these concerns into
the dashboard:

- progress reporting and ranking,
- self-reporting approvals,
- quiz completion and scoring.

The dashboard only bootstraps local credentials and obtains temporary SkillTree tokens.
Do not put SkillTree admin passwords, client secrets, or bearer tokens in static
dashboard assets or browser JavaScript.

## Recommendation Boundary

`/api/recommendations` is an additive, read-only prototype over
`output/data/skilltree_project.json`. With no progress signal supplied by the local
dashboard, it exposes available foundation candidates and labels
`signalSource: "none"` and `personalized: false`. The pure recommender also accepts
explicit completed and unsuccessful SkillTree skill ids for future integration tests;
those signals are never persisted by this project-owned shell.

Each row includes its reason, prerequisite depth, assessment count, concept tokens, and
official SkillTree subject/quiz routes. SkillTree remains the source of truth for
completion, quiz state, ranking, approvals, and any future learner-state integration.
The prototype does not infer latent knowledge, run knowledge tracing or cognitive
diagnosis, rank learners, or establish tutoring efficacy.

## Course Material Source Boundary

The local **Learn** panel is generated from the curriculum graph plus
`data/course_material_sources.yaml`. That YAML pins the Active Inference Institute
`courses` and `cognitive` repositories by commit, records path globs and topic/stratum
mappings, and keeps external material as links rather than copied prose. The dashboard
therefore gives each skill concept context, prerequisite context, downstream role,
assessment summary, provenance note, related local skills, and pinned external pointers
without creating unpinned embeddings or importing upstream course text into this repo.
The generated index also records source, role, and match-scope coverage so maintainers
can distinguish stratum fallback links from topic-matched cognitive knowledge-base
pointers.

Regenerate and validate this layer with:

```bash
uv run python scripts/build_course_materials.py
uv run python scripts/validate_course_material_sources.py --online
uv run python scripts/export_skilltree.py
uv run python scripts/validate_course_material_alignment.py
```
The alignment validator compares the generated SkillTree export with the local lesson
index and fails if a skill is missing material, a material record has the wrong
prerequisite list, a route drifts back to the unsafe direct skill-detail path, or a quiz
question count/correct-answer contract no longer matches its material summary.

## Auth Boundary

The default local dashboard is no-login for the learner, not anonymous. It uses the fixed
SkillTree learner id `local-learner`. If SkillTree is fresh, bootstrap creates a local
root account and stores its generated password plus the project trusted-client secret in
`.active_skillference_local/skilltree_auth.json` with owner-only permissions where the
filesystem supports them.

If a root account already exists but that local state file is missing, bootstrap fails
with a recovery message instead of guessing. Reset the local Docker volume, restore the
state file, or use a deployment-supported admin token path.

Remote deployments should provide their own trusted-client endpoint or PKI/SAML setup and
pass it with `--authenticator` / `SKILLTREE_AUTHENTICATOR`; the local bridge is a
development-only convenience.

## Security Posture Boundary

- The dashboard page ships a strict Content-Security-Policy: `default-src 'none'` with
  narrow allowances for its own assets, the MathJax CDN, and the configured SkillTree
  origin. The official learner display is an iframe on that origin and opens a SockJS
  WebSocket to it, so the policy names `frame-src <skilltree origin>` and puts the
  matching `ws://`/`wss://` origin in `connect-src`; the browser matches the socket by
  scheme, not by the configured HTTP origin. Narrowing either directive silently blanks
  the Official Display panel, which is why `validate_dashboard_console.py` treats any CSP
  violation as a hard failure.
- Large JSON responses are gzip-encoded when the client advertises it (`/api/status`
  carries the full export and compresses roughly 15x). Compression is content-encoding
  only; no route caches, and every JSON response stays `Cache-Control: no-store`.
- The local trusted-client bridge keeps SkillTree client secrets server-side and never
  writes them into static HTML, JavaScript, generated JSON, or manuscript artifacts.
- Artifact-only mode is intentionally read-only: it inspects generated files while
  SkillTree remains offline.
- Docker Compose is a local runtime convenience. Production or regulated deployments need
  organization-owned identity policy, network segmentation, logging, backup/restore,
  software-bill-of-materials review, artifact provenance, signing, and vulnerability
  management.
- The curriculum can teach provenance and threat-review practices, but SkillTree learner
  records, approvals, ranking, quiz state, and platform hardening remain outside this
  repository's system of record.

## Browser Verification

In local `FORM` mode the embedded SkillTree client can log a 401 for SkillTree's built-in
`Inception` project token refresh while the `activeInference` display still works. Treat
that as upstream SkillTree noise only when all project-owned checks are green:
`/api/skilltree/token` returns an `access_token`, `/api/status` reports
`authenticatorConfigured=true`, the official frame renders the `activeInference` overview
or subject page, the **Learn** buttons open local material records, and a quiz route such as
`/?skillsClientDisplayPath=%2Fsubjects%2Fsub_linalg%2Fskills%2Fm_sets%2Fquizzes%2Fm_sets_quiz`
shows real SkillTree questions.
For a stricter local-runtime check, run `validate_live_skilltree_dashboard.py` with
`--require-live-admin`; this compares SkillTree's live admin project skill count with the
exported project instead of relying on the embedded learner overview label alone. Add
`--require-live-dependencies` when live prerequisite edges must exactly match
`output/data/skilltree_project.json`. The full-stack validator also runs
`validate_skilltree_form_login.py` before the console gate, so the documented local
username/password must reach the authenticated SkillTree administrator surface. It then
runs `validate_dashboard_console.py --require-browser --require-dashboard`, so missing
`chrome-devtools-axi` or a missing dashboard is a failed app proof rather than an
optional skip.

The dashboard intentionally does not use direct SkillTree skill-detail routes for
**Learn**. Local probing reproduced an upstream SkillTree error page on direct
`/subjects/{subjectId}/skills/{skillId}` navigation, while subject and quiz routes remain
the verified official handoff surfaces.

## Local Routes

| Route | Purpose |
|---|---|
| `/` | Dashboard HTML |
| `/healthz` | Minimal local server health check |
| `/api/config` | Browser-safe dashboard and SkillTree config |
| `/api/status` | Combined config, SkillTree status, project summary, claims, stats, artifacts |
| `/api/status?defer_live=1` | Same payload with the live SkillTree parity call skipped (`liveSkilltree.deferred=true`); the page uses it for first paint and then re-requests the checked form |
| `/api/recommendations` | Deterministic graph-only prerequisite-frontier candidates with official SkillTree routes |
| `/api/skilltree/token` | Local-only trusted-client token endpoint for `skills-client-js` |
| `/api/project` | Exported SkillTree project summary |
| `/api/claims` | Provenance claim summary |
| `/api/course-materials` | Generated local course-material index for the Learn panel |
| `/api/artifacts` | Known artifact inventory |
| `/artifacts/<id>` | Read-only artifact file |

All artifact routes are read-only. `/api/skilltree/token` performs only a server-side
SkillTree token exchange; it does not mutate curriculum artifacts. Regeneration still
belongs to the source-of-truth scripts:

```bash
uv run python scripts/build_curriculum.py
uv run python scripts/run_kernels.py
uv run python scripts/build_course_materials.py
uv run python scripts/validate_manuscript_artifacts.py
uv run python scripts/export_skilltree.py
uv run python scripts/validate_course_material_alignment.py
```
