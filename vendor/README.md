# Vendored SkillTree runtime

This platform targets the NSA-origin open-source **SkillTree** micro-learning framework
([skilltreeplatform.dev](https://skilltreeplatform.dev),
[github.com/NationalSecurityAgency/skills-service](https://github.com/NationalSecurityAgency/skills-service),
[code.nsa.gov](https://code.nsa.gov/)).
Two supported ways to run a live instance and seed it with the Active Inference
curriculum exported by this repo.

The NSA provenance is source attribution for the platform substrate. It is not an
endorsement of Active Skillference and does not remove the need for deployment-specific
identity, logging, supply-chain, backup, incident-response, and operator-access controls.

> **Version history.** The live records below against `4.4.2` and the digest-pin bump to
> `4.5.2` predate this repo's current pin to `4.6.0` (upstream release 2026-07-28). The
> `4.6.0` digest was re-pinned via the documented Docker Hub procedure and the `AuthMode`
> enum re-confirmed from the `4.6.0` tag — but a fresh live full-app boot against `4.6.0`
> is not yet recorded here (tracked in `tasks.yaml` as `asf-skilltree-460-live-reverify`).
> Do not read the earlier live records as proof for `4.6.0`.

## Option A — Docker (recommended, one command)

```bash
./scripts/run_skilltree.sh
```

This uses [`docker-compose.yml`](../docker-compose.yml) to start the published
`skilltree/skills-service:4.6.0` image plus PostgreSQL, waits for the REST API at
`http://localhost:8080`, then runs `scripts/bootstrap_local_skilltree.py` by default.
That bootstrap path creates/reuses local `FORM` auth, seeds the project, stores ignored
trusted-client state, and verifies token exchange for the fixed local learner. The
The Compose file pins `platform: linux/amd64` because the published `4.6.0` image runs
under emulation on this arm64 Docker/Colima host; the wrapper waits up to 20 minutes by
default, and `SKILLTREE_WAIT_ATTEMPTS` can extend the readiness window.

## Option A+ — Docker plus the local learner dashboard

```bash
./scripts/run_learning_dashboard.sh
```

This starts the same SkillTree runtime, regenerates the curriculum outputs, bootstraps a
local root/admin account when SkillTree is fresh, seeds the `activeInference` project, and
serves the project-owned dashboard at `http://127.0.0.1:8765`. The dashboard uses
SkillTree as the system of record: learner progress, ranking, self-reporting, and quiz
completion remain in the SkillTree service. The local interface reads generated artifacts
and mounts the official SkillTree learner display through a server-side trusted-client
token endpoint at `/api/skilltree/token`.

The local Docker stack uses SkillTree password authentication (`FORM`). The dashboard
does not disable auth; it hides login locally by using one fixed learner identity,
`local-learner`, and a server-side token exchange. Local bootstrap secrets are written to
ignored `.active_skillference_local/`. If a root account already exists but that state
file is missing, bootstrap fails with a recovery message instead of guessing credentials.

Raw SkillTree at `http://localhost:8080` is still a real `FORM` login surface. For a fresh
local Docker volume, the default development root login is
`active-skillference-admin@localhost.invalid` / `active-skillference-local`. Override
fresh-bootstrap defaults with `ACTIVE_SKILLFERENCE_LOCAL_ADMIN_USERNAME` and
`ACTIVE_SKILLFERENCE_LOCAL_ADMIN_PASSWORD`. Existing ignored local state is never
silently overwritten; inspect the current local credentials with
`uv run python scripts/bootstrap_local_skilltree.py --show-local-credentials`.
If the raw SkillTree browser login rejects the documented email/password, the local
Docker volume probably still contains an older non-email root account. Reset only the
local development runtime with:

```bash
uv run python scripts/reset_local_skilltree.py --confirm-local-reset
```

That command stops the detached dashboard if present, backs up
`.active_skillference_local/skilltree_auth.json`, runs `docker compose down -v`, removes
stale local auth state, restarts the app-ready stack with
`--skip-regenerate --keep-running --app-ready`, and leaves both
`http://localhost:8080` and `http://127.0.0.1:8765` available when proof succeeds.
Run `uv run python scripts/reconcile_live_dependencies.py` when you also need every
exported prerequisite edge present in the live SkillTree graph.
For slow local hosts, use `uv run python scripts/reconcile_live_dependencies.py
--check-only` to refresh status without writes, `--max-edges 5` to seed a small chunk, or
`--max-runtime-seconds 900` to bound a resume run. The live SkillTree graph is the source
of truth; `.active_skillference_local/dependency_seed_progress.json` is only a resume
and diagnostics aid.

For any shared or regulated environment, do not reuse the local root account pattern as an
operations model. Put SkillTree behind organization-owned access control, require short
lived admin credentials, audit `/api/skilltree/token` access, pin and scan container
images, and attach SBOM/provenance/signature evidence to release artifacts.

For non-local deployments, direct admin REST writes still need deployment-supported auth.
If your SkillTree instance accepts bearer tokens for admin writes, provide one as:

```bash
ACTIVE_SKILLFERENCE_LOCAL_AUTH=0 SKILLTREE_TOKEN=... ./scripts/run_skilltree.sh
ACTIVE_SKILLFERENCE_LOCAL_AUTH=0 SKILLTREE_TOKEN=... ./scripts/run_learning_dashboard.sh
```

Without `SKILLTREE_TOKEN`, `run_learning_dashboard.sh` uses the local bootstrap path.
Set `ACTIVE_SKILLFERENCE_LOCAL_AUTH=0` to disable the local trusted-client bridge and
fall back to explicit deployment auth; `run_skilltree.sh` fails early in that mode unless
`SKILLTREE_TOKEN` is set.

## Option A++ — Strict full-app proof

```bash
uv run python scripts/validate_full_app_stack.py
uv run python scripts/validate_full_app_stack.py --keep-running
```

Use this when the claim is “the full local SkillTree app is running,” not merely that
generated artifacts exist. The validator requires Docker plus a running Docker
Desktop/Colima daemon, starts the Compose stack, waits for SkillTree `/public/status`,
regenerates the curriculum/kernel/figure/export artifacts, bootstraps local `FORM` auth,
seeds `activeInference` subjects/skills/quizzes, reconciles missing prerequisite edges,
starts the learner dashboard, verifies `/healthz`, requires live admin skill-count
parity, requires live dependency parity, requires figure-registry/dashboard
chart-contract parity, and runs the browser console gate with `chrome-devtools-axi`.
Use `--app-ready` for the faster local usability proof; that mode is explicit and does
not claim full prerequisite parity. If Docker is installed but the daemon is down, this
command fails closed with an explicit preflight error instead of falling back to
artifact-only mode.

The pinned `skilltree/skills-service:4.6.0` image is single-arch; on Apple/ARM Docker
or Colima, late dependency writes can be CPU-bound in the SkillTree JVM while Postgres is
idle. For faster strict parity, allocate more Colima/Docker CPU and memory or run a
native SkillTree service from source.

## Option B — Build from source (git submodule)

Pin the upstream backend as a submodule and build it with Gradle (Java 17+):

```bash
git submodule add https://github.com/NationalSecurityAgency/skills-service vendor/skills-service
git -C vendor/skills-service checkout 4.6.0           # pin a release (upstream tags have no "v" prefix)
cd vendor/skills-service && ./gradlew bootRun          # needs a local PostgreSQL
```

Then seed against the running instance:

```bash
uv run python scripts/seed_skilltree.py --base-url http://localhost:8080 --token "$SKILLTREE_TOKEN" --require-live
```

## What gets seeded

`scripts/seed_skilltree.py` builds the validated curriculum DAG, resolves every
`{{claim:…}}` provenance token against the tested kernels, exports a SkillTree project
(`Project → Subjects → Skills` with prerequisite **learning-path dependencies** and
**quizzes**), and creates it over the admin REST API in dependency-safe topological
order (subjects → quizzes → skills → dependencies). Quizzes are created before
quiz-gated skills because SkillTree validates `quizId` during skill creation.

Without `--require-live`, the seeder exits successfully with a skip message when no
server is listening. That mode is for offline template renders; live validation should
use `--require-live`. In `FORM` auth mode, a reachable server can still reject admin
writes with `401`; this is expected until a valid admin auth mechanism is supplied.

## Local dashboard without Docker

The dashboard can still inspect already generated artifacts when the service is absent:

```bash
uv run python scripts/serve_learner_dashboard.py --check
uv run python scripts/serve_learner_dashboard.py
```

SkillTree status will show offline and the official learner display will fall back to
direct links, but the curriculum explorer and artifact inventory remain usable if
`output/data/skilltree_project.json` and the other generated files exist.

> **Historical local Docker status.** Docker client `29.5.3`, Compose `5.1.4`, and daemon
> `29.5.2` under the `colima` context previously started PostgreSQL plus
> `skilltree/skills-service:4.4.2`, and `http://localhost:8080/public/status` returned
> `{"status":"OK"}`. Treat that as an environment smoke check, not a current seed claim:
> the active export is larger and live SkillTree re-verification remains tracked in
> `tasks.yaml`.
