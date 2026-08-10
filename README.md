# Active Skillference

**A high-integrity micro-learning platform for Active Inference and the Free Energy
Principle, built on the NSA-origin open-source
[SkillTree](https://skilltreeplatform.dev) framework.**

Active Skillference renders the Active Inference / FEP body of knowledge as a *validated
prerequisite graph* spanning all eight strata, from the mathematics of surprise through
to applications, where **every quantitative claim a learner sees is produced by a tested
computational kernel**, never hand-typed. The validated graph exports directly into
SkillTree's `Project → Subject → Skill` data model with prerequisite learning-paths and
quiz-gated completion, and can seed a live, gamified instance over REST. The manuscript
also validates scholarly support through a source-role matrix before generated artifacts
are emitted.

SkillTree itself is developed in the National Security Agency open-source ecosystem
([press release](https://www.nsa.gov/Press-Room/Press-Releases-Statements/Press-Release-View/article/2380858/),
[skills-service](https://github.com/NationalSecurityAgency/skills-service),
[code.nsa.gov](https://code.nsa.gov/)). Active Skillference cites that provenance for
platform context only; it is not an NSA endorsement and does not replace deployment
threat modeling, supply-chain attestation, or organization-specific access-control
review.

## Why it is "high-integrity"

- **Provenance binding.** Skill content references numbers only through `{{claim:NAME}}`
  tokens that resolve to tested-kernel outputs. The export fails closed if any token is
  unbacked, and a linter rejects bare result numbers typed into prose.
- **A validated DAG.** The curriculum is checked to be acyclic, free of dangling
  prerequisites, connected from foundations to applications, with roots only in the
  foundational strata.
- **A learner-quality gate.** The build also rejects shallow assessment depth, biased
  answer positions, terse descriptions, missing tags, backward learning-path edges, and
  off-domain placeholder distractors (UI/plumbing "junk" wrong answers that a learner could
  eliminate without understanding).
- **A semantic-prerequisite gate.** A skill may not be *assessed on* a load-bearing concept
  (KL divergence, Markov chains, the Laplace approximation, the ELBO) unless the concept's
  defining skill is in its transitive prerequisites — so a learner is never tested on
  something they could not yet have learned. A non-empty-scan guard keeps the gate from
  silently going vacuous if the corpus drifts.
- **Scholarship coverage.** Authored citations must resolve to both
  `manuscript/references.bib` and `data/scholarship_sources.yaml`, where each source has
  a support lane, role, kind, and locator.
- **Claim-support taxonomy.** Anchored manuscript claims must declare whether they are
  computed, descriptive counts, simulations, literature claims, scope limits, delivery
  checks, or visual evidence; unsupported strong scientific language fails validation.
- **Manuscript artifact audit.** Generated figures register labels, captions, alt text,
  semantic metadata, claim tokens, filenames, and generators; the build checks manuscript
  declarations, cross-references, readable nonblank PNGs, and dashboard artifact links.
- **Pinned course-material pointers.** Local dashboard Learn panels are generated from
  `data/course_material_sources.yaml`, which pins external Active Inference Institute
  course and knowledge-base repositories by commit instead of copying prose or using
  unpinned embeddings.
- **License/IP signposting.** The repository declares MIT in `LICENSE` and metadata
  files, records vendored/runtime notices in `THIRD_PARTY_NOTICES.md`, and keeps the
  owner-confirmed public-review boundary explicit in
  [`docs/ip_license_status.md`](docs/ip_license_status.md).
- **Tested kernels.** Information theory, Bayesian/variational inference, and a discrete
  active-inference agent are deterministic, no-mock reference implementations covered by
  the project-wide `src/` coverage gate.

## The eight strata

`mathematics → probability → information theory → variational methods → the Free Energy
Principle → active inference → computation → applications`

## Layout

| Path | Contents |
| --- | --- |
| `src/kernels/` | Tested computational kernels (the source of every claim) |
| `src/provenance/` | Claim registry + provenance binding/lint gate |
| `src/scholarship/` | Citation source-role coverage validation |
| `src/manuscript/` | Figure registry / manuscript / dashboard artifact drift validation |
| `src/curriculum/` | Typed model, prerequisite-DAG engine, and the Active Inference catalog |
| `src/skilltree/` | Curriculum → SkillTree exporter, REST clients, local auth bridge, and seeder |
| `src/figures/` | Deterministic, data-driven figures |
| `src/dashboard/` | Local learner dashboard shell over generated artifacts + official SkillTree views |
| `src/pilot/` | Protocol-only learner-pilot contract and privacy/missing-data validation |
| `scripts/` | Thin orchestrators (build / run kernels / export / seed) |
| `manuscript/` | The platform write-up rendered to PDF |
| `vendor/` | Runnable SkillTree instance wiring (see `vendor/README.md`) |

## Quick start

```bash
uv sync
uv run python scripts/build_curriculum.py    # DAG stats + diagnostic gap map
uv run python scripts/analyze_scholarship.py # citation coverage + source-health network
uv run python scripts/run_kernels.py          # claims, scholarship, figures, companions, audits
uv run python scripts/build_course_materials.py # local Learn material records
uv run python scripts/validate_claim_support.py # validate manuscript scientific support
uv run python scripts/export_skilltree.py     # provenance-gated SkillTree JSON
uv run python scripts/validate_course_material_alignment.py # material/quiz parity
uv run pytest --cov=src --cov-fail-under=90   # full suite, ≥90% coverage
```

### Run a live SkillTree instance and seed it (requires Docker)

```bash
./scripts/run_skilltree.sh   # docker compose up (skills-service + Postgres) + seed
# then open http://localhost:8080
```

The pinned local stack uses SkillTree password auth (`FORM`). The service starts and
`/public/status` is reachable without credentials; `run_skilltree.sh` then uses the
local bootstrap path to create/reuse local admin state, seed the project, and verify the
trusted-client token exchange. Direct admin seeding through `scripts/seed_skilltree.py`
still requires deployment-supported admin auth such as `SKILLTREE_TOKEN`.

See [`vendor/README.md`](vendor/README.md) for the Docker and build-from-source paths.

### Run the local learner dashboard (requires Docker for live SkillTree)

```bash
./scripts/run_learning_dashboard.sh
# then open http://127.0.0.1:8765
```

The dashboard serves a no-build HTML/CSS/JS interface from this project. The **Official
Display** tab embeds SkillTree's own `skills-client-js` learner view, so the page CSP
names the SkillTree origin in both `frame-src` and (as `ws://`/`wss://`) `connect-src`;
the browser console gate fails closed if either is missing. First paint does not wait on
the live dependency-parity read — the page loads `/api/status?defer_live=1`, then swaps in
checked parity — and large JSON responses are gzip-encoded on request. In the default
local path it bootstraps one local SkillTree root/admin account, stores local-only secrets
under ignored `.active_skillference_local/`, seeds `activeInference`, and exposes
`/api/skilltree/token` as a server-side trusted-client bridge for the official
`skills-client-js` learner display. Browser JavaScript never receives the admin password,
client secret, or bearer token. Learner identity is the fixed local id `local-learner`;
the dashboard's **Learn** buttons open local modular material records, while progress,
ranking, quiz completion, and self-reporting remain SkillTree-owned. Artifact-only mode
still shows generated curriculum diagnostics, scholarship-health buckets, figure
companion tables, and exact offline/local-auth/missing-material states without claiming
live learner progress.

Raw SkillTree at `http://localhost:8080` remains the real SkillTree `FORM` login surface.
For a fresh local Docker volume, the development root login is:

```text
username: active-skillference-admin@localhost.invalid
password: active-skillference-local
```

Override these fresh-bootstrap defaults with
`ACTIVE_SKILLFERENCE_LOCAL_ADMIN_USERNAME` and
`ACTIVE_SKILLFERENCE_LOCAL_ADMIN_PASSWORD`. Existing
`.active_skillference_local/skilltree_auth.json` state remains authoritative; inspect it
with `uv run python scripts/bootstrap_local_skilltree.py --show-local-credentials`.
If browser login at `http://localhost:8080` rejects the documented email/password, the
local Docker volume likely predates these defaults. Reset only the local SkillTree
runtime and restart both sites with:

```bash
uv run python scripts/reset_local_skilltree.py --confirm-local-reset
```

The reset command stops the detached dashboard if present, backs up the ignored local
auth file, runs `docker compose down -v`, recreates SkillTree with the deterministic
default login, and leaves the learner dashboard running at `http://127.0.0.1:8765`.
By default reset proves the fast **app-ready** path: SkillTree login, dashboard health,
token bridge, live skills/subjects, artifacts, raw `FORM` login, and browser proof. Full
live prerequisite parity is intentionally separate because the pinned SkillTree container
can spend a long time validating late dependency writes on Apple/ARM Docker emulation:

```bash
uv run python scripts/reconcile_live_dependencies.py --check-only
uv run python scripts/reconcile_live_dependencies.py --max-edges 5
uv run python scripts/reconcile_live_dependencies.py --max-runtime-seconds 900
uv run python scripts/reconcile_live_dependencies.py
uv run python scripts/validate_full_app_stack.py --skip-regenerate --keep-running
```

The reconciler treats the live SkillTree graph as authoritative and the ignored progress
file as advisory. `--check-only` refreshes/reports parity without writing edges; bounded
`--max-edges` and `--max-runtime-seconds` runs are useful on slow Docker/Colima hosts and
return explicit partial JSON until live dependency parity is reached.

The dashboard also shows a **Local SkillTree Login** card with the default credentials
and reset/show-credentials commands.
For shared or deployed SkillTree instances, replace these local defaults with deployment
auth, `SKILLTREE_TOKEN`, or a deployment-owned trusted-client authenticator.

See [`docs/learner_dashboard.md`](docs/learner_dashboard.md) for routes, ownership
boundaries, and offline behavior.

### Validate the full local app stack (strict)

```bash
uv run python scripts/validate_full_app_stack.py
# or keep the dashboard open after proof:
uv run python scripts/validate_full_app_stack.py --keep-running
```

This is the fail-closed local app proof. It requires Docker plus a running
Docker Desktop/Colima daemon, starts SkillTree with `docker compose up -d`, waits for
`http://localhost:8080/public/status`, regenerates generated artifacts, bootstraps local
SkillTree auth, seeds the current `activeInference` export, starts the dashboard at
`http://127.0.0.1:8765`, reconciles missing live prerequisite edges, checks live admin
count parity, requires live dependency parity, checks figure-registry/dashboard contract
parity, proves the raw SkillTree `FORM` login with `chrome-devtools-axi`, and runs the
browser console gate. Use `--app-ready` for the faster local usability proof that does
not claim full dependency parity.
If Docker is installed but the daemon is down, the validator fails with an explicit
preflight message instead of falling back to artifact-only mode.

For national-security or regulated environments, treat the dashboard and Docker stack as
local development tooling unless your organization adds its own zero-trust access
controls, SBOM/provenance/signing process, monitoring, incident response, and SkillTree
operator controls.

## Code availability, license, and citation

Released as **v1.0.0** at
[github.com/ActiveInferenceInstitute/Active_Skillference](https://github.com/ActiveInferenceInstitute/Active_Skillference),
archived on Zenodo at
[**10.5281/zenodo.21865644**](https://doi.org/10.5281/zenodo.21865644). The same DOI
appears in `CITATION.cff`, `codemeta.json`, `.zenodo.json`, `manuscript/config.yaml`, and
on the manuscript cover page; `tests/test_publication_readiness.py` cross-checks every one
of them against `data/zenodo_reservation.json` and fails on any divergence, so a wrong
identifier cannot reach a citation. Cite with `CITATION.cff` or the DOI.

Authored code and content are MIT licensed (`LICENSE`), copyright Daniel Ari Friedman.
Vendored runtime dependencies and their separate notices live in
[`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md); the release boundary is tracked in
[`docs/ip_license_status.md`](docs/ip_license_status.md) and
[`docs/publication_readiness.md`](docs/publication_readiness.md).

## Captured evidence of the running app

Everything under `output/` is regenerable, so it is not committed. The exception is the
learner-dashboard evidence in `manuscript/assets/screenshots/`: a recording of a running
system is not a function of project data and cannot be rebuilt from a checkout, so those
images are version-controlled beside a provenance record naming the dashboard address,
viewport, live SkillTree counts, and full-stack proof mode of the session that produced
them. They are registered in `figure_registry.json` as `evidence_kind: captured`, held to
the same caption, alt-text, and chart-contract floors as the generated figures, and
excluded from the deterministic render/registry parity check. Refresh them against a live
stack with:

```bash
uv run python scripts/capture_dashboard_screenshots.py
```

## Verification at a glance

Full test suite · ≥90% `src/` line coverage gate · ruff + mypy clean · no mock frameworks ·
every `{{claim}}` resolves · provenance linter clean. Re-running the kernels regenerates
every number and figure in the curriculum; exact current coverage comes from the test
report.
