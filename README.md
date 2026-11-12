# Active Skillference

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21865644.svg)](https://doi.org/10.5281/zenodo.21865644)
[![Release](https://img.shields.io/github/v/release/ActiveInferenceInstitute/Active_Skillference)](https://github.com/ActiveInferenceInstitute/Active_Skillference/releases/latest)
[![License: MIT](https://img.shields.io/badge/License-MIT-informational.svg)](LICENSE)
[![gates](https://github.com/ActiveInferenceInstitute/Active_Skillference/actions/workflows/gates.yml/badge.svg)](https://github.com/ActiveInferenceInstitute/Active_Skillference/actions/workflows/gates.yml)

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

## Contents

- [Start here](#start-here) · [Read it without installing anything](#read-it-without-installing-anything) · [Why it is "high-integrity"](#why-it-is-high-integrity) · [The eight strata](#the-eight-strata)
- [Model specification (GNN)](#model-specification-gnn) · [Layout](#layout) · [Quick start](#quick-start)
- [Code availability, license, and citation](#code-availability-license-and-citation) · [Captured evidence of the running app](#captured-evidence-of-the-running-app) · [Verification at a glance](#verification-at-a-glance) · [Contributing and reporting](#contributing-and-reporting)
- Documentation: [`docs/README.md`](docs/README.md) (index) · [`docs/quickstart.md`](docs/quickstart.md) · [`docs/architecture.md`](docs/architecture.md) · [`docs/learner_dashboard.md`](docs/learner_dashboard.md)

## Start here

```bash
git clone https://github.com/ActiveInferenceInstitute/Active_Skillference.git
cd Active_Skillference
./run.sh              # dependencies, build, live SkillTree, learner dashboard
./run.sh --offline    # no Docker: build and serve generated artifacts only
./run.sh --check      # report readiness and exit without starting anything
```

One command from a fresh clone to a browser page you can learn from. Each step says what
it is doing and what to do if it stops; a run that refuses with a reason is working as
intended. The live path needs a running Docker daemon because SkillTree owns quizzes,
completion, points, and ranking. The offline path needs neither Docker nor a network.

## Read it without installing anything

Generated outputs are committed, so the artifacts are browsable straight from the
repository:

| What | Where |
| --- | --- |
| The archived manuscript, exactly as deposited | [`Active_Skillference_v1.0.0_DOI-10.5281-zenodo.21865644.pdf`](Active_Skillference_v1.0.0_DOI-10.5281-zenodo.21865644.pdf) |
| The current build of the manuscript | [`output/pdf/Active_Skillference_combined.pdf`](output/pdf/Active_Skillference_combined.pdf) |
| Every generated figure | [`output/figures/`](output/figures/) with [`figure_registry.json`](output/figures/figure_registry.json) |
| The SkillTree export | [`output/data/skilltree_project.json`](output/data/skilltree_project.json) |
| The claim ledger | [`output/data/claims.json`](output/data/claims.json) |
| Audits and coverage records | [`output/data/`](output/data/) |
| Web, DOCX, EPUB and slide builds | [`output/web/`](output/web/), [`output/docx/`](output/docx/), [`output/epub/`](output/epub/), [`output/slides/`](output/slides/) |
| Dashboard screenshots | [`manuscript/assets/screenshots/`](manuscript/assets/screenshots/) |

Committing them does not weaken the regenerability claim. Running the kernels rebuilds
every one from source, and `validate_rendered_freshness.py` fails if a committed artifact
has drifted from what the current source produces. Only renderer logs and LaTeX
intermediates are withheld, since they change on every run and carry nothing to read.

The two PDFs are deliberately distinct. The root file is the frozen v1.0.0 deposit,
byte-identical to what `10.5281/zenodo.21865644` archives (MD5 `7e43004d…`), so the
filename's claim about that DOI stays true no matter how the source moves on. The file
under `output/pdf/` is the current build from the current source, and will differ whenever
the manuscript has changed since the deposit.

**Versions.** The repository is at **v1.0.1**; the Zenodo deposit archives the **v1.0.0**
manuscript. The DOI is unchanged and still correct to cite, because v1.0.1 adds committed
outputs, a rewritten README, and the code-availability wording, and revises no result. A
future release that changes the science gets its own version DOI under the same concept.

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

## Model specification (GNN)

The discrete active-inference agent kernel (`src/kernels/active_inference.py`, the
sample/commit model of `src/kernels/examples.py`) is specified in
[`gnn/discrete_active_inference_agent.gnn.md`](gnn/discrete_active_inference_agent.gnn.md) in
[Generalized Notation Notation](https://github.com/ActiveInferenceInstitute/Generalized_Notation_Notation)
(GNN): the informative sensor, the sample/commit transition tensor, the neutral
preference vector, and the uniform state prior.

The gate parses the specification with the extractor pinned in
[`gnn/upstream.json`](gnn/upstream.json) and checks that the declared matrices reproduce
the kernel's expected-free-energy values. It reads the parser source with `git archive`
at the recorded commit.

### Required local GNN check

Merges to `main` require `gnn conformance (local)`. The hosted
`gnn conformance (pinned)` job provides a separate CI signal.

Use a clean checkout of the current PR head. Prepare the frozen Skillference environment
with `uv sync --frozen` and stage the parser before starting the offline run. Use a
dedicated checkout containing the recorded commit and its tag, plus a Python 3.12
environment with `numpy` and `defusedxml` for the parser. From the Skillference checkout,
set `GNN_ROOT` to a new scratch path and run the preparation commands below. In GitVault,
follow its repository admission rules for this staging work.

```sh
set -eu
repo=ActiveInferenceInstitute/Active_Skillference
: "${PR_NUMBER:?Set PR_NUMBER}" "${GNN_ROOT:?Set GNN_ROOT to a new absolute scratch path}"
pr_head=$(gh pr view "$PR_NUMBER" --repo "$repo" --json headRefOid --jq .headRefOid)
test "$(git rev-parse HEAD </dev/null)" = "$pr_head"
changes=$(git status --porcelain </dev/null)
test -z "$changes"

gnn_revision=$(jq -er .commit gnn/upstream.json)
gnn_tag=$(jq -er .tag gnn/upstream.json)
gnn_repo=$(jq -er .repository gnn/upstream.json)
test "$gnn_repo" = ActiveInferenceInstitute/Generalized_Notation_Notation
mkdir "$GNN_ROOT"
git init --quiet "$GNN_ROOT" </dev/null
git -C "$GNN_ROOT" remote add origin "https://github.com/$gnn_repo.git" </dev/null
git -C "$GNN_ROOT" fetch --depth 1 origin "$gnn_revision" \
  "refs/tags/$gnn_tag:refs/tags/$gnn_tag" </dev/null
git -C "$GNN_ROOT" checkout --quiet --detach "$gnn_revision" </dev/null
test "$(git -C "$GNN_ROOT" rev-parse --verify "refs/tags/$gnn_tag^{commit}" </dev/null)" = "$gnn_revision"
uv venv --python 3.12 --no-project "$GNN_ROOT/.venv"
GNN_PYTHON="$GNN_ROOT/.venv/bin/python"
uv pip install --python "$GNN_PYTHON" numpy defusedxml
```

For a standalone run from the Skillference checkout, export `GNN_ROOT` and
`GNN_PYTHON`, then run the checks with the prepared environments.

```sh
set -eu
export GNN_ROOT GNN_PYTHON
uv sync --frozen --check --offline
uv run --frozen --offline --no-sync python -B scripts/validate_gnn_spec.py
uv run --frozen --offline --no-sync python -B -m pytest \
  tests/test_gnn_conformance.py -q -p no:cacheprovider
```

For GitVault publication, run both checks in its governed offline test runner
(`execute --classification test`, described in GitVault's `docs/EXECUTE.md`). Bind
the intent to the clean PR head and pin inputs. Pass both absolute parser paths as
arguments to the test runner and set `GNN_ROOT` and `GNN_PYTHON` inside the child so
the launcher cannot drop them. Set `VAULT_ROOT` to the configured GitVault checkout
and `GNN_INTENT` to the prepared test intent. From the PR checkout, run the gate
with its existing project Python.

```sh
"$VAULT_ROOT/_tools/vault" --config "$VAULT_ROOT/vault.toml" execute \
  --classification test --intent "$GNN_INTENT" --repository "$repo" --cwd "$PWD" -- \
  "$PWD/.venv/bin/python" -B -c '
import os, subprocess, sys
from pathlib import Path

out = Path(os.environ["GITVAULT_EXECUTION_OUTPUT"])
env = dict(os.environ, GNN_ROOT=sys.argv[1], GNN_PYTHON=sys.argv[2],
           TMPDIR=str(out), TEMP=str(out), TMP=str(out), PYTHONDONTWRITEBYTECODE="1",
           GIT_NO_REPLACE_OBJECTS="1", UV_PROJECT_ENVIRONMENT=str(Path(sys.executable).parent.parent))

def run(argv, log):
    with (out / log).open("x") as stream:
        subprocess.run(argv, env=env, stdin=subprocess.DEVNULL, stdout=stream,
                       stderr=subprocess.STDOUT, check=True)

run(["uv", "sync", "--frozen", "--check", "--offline"], "locked-environment.log")
run([sys.executable, "-B", "scripts/validate_gnn_spec.py"], "conformance.json")
run([sys.executable, "-B", "-m", "pytest", "tests/test_gnn_conformance.py",
     "-q", "-p", "no:cacheprovider"], "pytest.log")
summary = (out / "pytest.log").read_text().splitlines()[-1]
if "passed" not in summary or "skipped" in summary or "failed" in summary:
    raise SystemExit("Pinned GNN tests must pass with zero skips")
' "$GNN_ROOT" "$GNN_PYTHON" </dev/null
```

Keep the strict validator JSON, pytest log and terminal receipt. The validator must
succeed, and the focused pytest suite must finish with zero skips or failures.

### Publish the local GNN result

An authorized maintainer uses GitVault's `github-status` plan with the mapped identity
and the `state` write class enabled. Set `VAULT_ROOT` to the configured GitVault checkout,
`PR_NUMBER` to the pull request number and `GNN_RECEIPT` to the run's `exit.json`.
Review the run evidence for both checks and verify that the receipt reports success and
unchanged source at the live PR head. A new head needs a fresh run.

```sh
set -eu
repo=ActiveInferenceInstitute/Active_Skillference
: "${VAULT_ROOT:?Set VAULT_ROOT}" "${PR_NUMBER:?Set PR_NUMBER}" "${GNN_RECEIPT:?Set GNN_RECEIPT}"
vault() { "$VAULT_ROOT/_tools/vault" --config "$VAULT_ROOT/vault.toml" "$@"; }
tested_head=$(jq -er --arg repo "$repo" '
  .payload | select(.classification == "test" and .outcome == "SUCCEEDED"
    and .returncode == 0 and .source_unchanged == true and .binding.source == $repo
    and .descendants.sample_errors == 0 and .descendants.remaining == [])
  | .binding.revision | select(test("^[0-9a-f]{40}$"))
' "$GNN_RECEIPT")
pr_head=$(gh pr view "$PR_NUMBER" --repo "$repo" --json headRefOid --jq .headRefOid)
test "$tested_head" = "$pr_head"
digest=$(shasum -a 256 "$GNN_RECEIPT")
request=$(jq -nc --arg repo "$repo" --arg head "$tested_head" --arg digest "${digest%% *}" '
  {method:"plan",arguments:{action:"github-status",parameters:{
    repository:$repo,expected_commit:$head,context:"gnn conformance (local)",state:"success",
    description:("Local pinned GNN checks passed. Receipt SHA-256 " + $digest[:16])
  }}}
')
plan=$(vault api --json "$request" | jq -er 'select(.ok == true) | .result.github')
vault github-apply --plan "$plan"
```

After reviewing the plan, recheck the live PR head, apply the exact confirmation phrase
and verify that the local context is successful on the tested commit.

```sh
test "$tested_head" = "$(gh pr view "$PR_NUMBER" --repo "$repo" --json headRefOid --jq .headRefOid)"
vault github-apply --plan "$plan" --apply --confirm 'REPORT 1 COMMIT STATUS'
gh api --method GET "repos/$repo/commits/$tested_head/status" | \
  jq -e --arg head "$tested_head" '
    .sha == $head and any(.statuses[]; .context == "gnn conformance (local)" and .state == "success")
  '
```

For specification edits, start from GNN's [Start Here](https://github.com/ActiveInferenceInstitute/Generalized_Notation_Notation/blob/v5.0.3/docs/START_HERE.md),
[framework integration guide](https://github.com/ActiveInferenceInstitute/Generalized_Notation_Notation/blob/v5.0.3/docs/gnn/integration/framework_integration_guide.md),
and [syntax reference](https://github.com/ActiveInferenceInstitute/Generalized_Notation_Notation/blob/v5.0.3/docs/gnn/reference/gnn_syntax.md).
For the wider picture (the adoption patterns sibling repositories use, pin discipline, and
the drift guard these checks implement), see GNN's
[downstream adoption guide](https://github.com/ActiveInferenceInstitute/Generalized_Notation_Notation/blob/main/docs/gnn/integration/downstream_adoption.md),
linked on GNN's default branch because it landed after the v5.0.3 pin.

### Related repositories

- [Generalized_Notation_Notation](https://github.com/ActiveInferenceInstitute/Generalized_Notation_Notation) —
  the specification and implementation core this repository's agent spec is pinned to.
- [ants](https://github.com/ActiveInferenceInstitute/ants) — the 2021 ant-colony foraging
  MDP companion code; it owns that model's GNN specification.
- [Active_InferAnts](https://github.com/ActiveInferenceInstitute/Active_InferAnts) — the
  multi-language Active Inference framework; its framework agent is specified in that
  repository's `gnn/` directory.

Each concept has one canonical home: this repository owns the discrete agent kernel and
its curriculum; the other two specify their own models.

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
| `src/screenshots/` | Captured browser evidence: manifest, capture driver, build-time staging |
| `src/publication/` | Zenodo DOI reservation and the separate, confirmation-gated publish path |
| `scripts/` | Thin orchestrators (build / run kernels / export / seed / capture / validate) |
| `manuscript/` | The platform write-up, its assets, and the captured dashboard screenshots |
| `output/` | Committed generated artifacts: figures, data, audits, PDF, web, DOCX, EPUB, slides |
| `data/` | Authored inputs: scholarship matrix, claim-support rows, course-material pins |
| `gnn/` | The GNN specification of the discrete agent kernel and the pinned GNN revision |
| `docs/` | Documentation, grouped by the question you arrived with ([index](docs/README.md)) |
| `vendor/` | Runnable SkillTree instance wiring (see `vendor/README.md`) |
| `run.sh` | Cold start to the learner surface, with offline and readiness modes |
| `gates.sh` | The single gate entry point: every offline arm CI runs ([docs/gates.md](docs/gates.md)) |

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

Released at
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

Everything under `output/` is regenerable and committed for convenience. The
learner-dashboard evidence in `manuscript/assets/screenshots/` is different in kind: a
recording of a running system is not a function of project data and cannot be rebuilt from
a checkout at all, so those images live beside a provenance record naming the dashboard
address, viewport, live SkillTree counts, full-stack proof mode, capture timestamp, and a
digest per image. They are registered in `figure_registry.json` as
`evidence_kind: captured`, held to the same caption, alt-text, and chart-contract floors as
the generated figures, and excluded from the deterministic render/registry parity check
because no generator emits them. No gate can detect a screenshot that has gone stale
against a changed interface, so re-capture after any change to what the dashboard displays:

```bash
uv run python scripts/capture_dashboard_screenshots.py
```

## Verification at a glance

One entry point runs every offline gate: `./gates.sh` (default: `lint`, `types`, `fast`) and
`./gates.sh all` for the full set, with `./gates.sh gnn` for the pinned conformance check and
`./gates.sh render` for the manuscript PDF. CI runs the same arms, so a command here is the
command CI runs; [`docs/gates.md`](docs/gates.md) documents each arm and
[`docs/gate_metrics.md`](docs/gate_metrics.md) carries the measured per-arm wall times.

Full test suite · ≥90% `src/` line coverage gate · ruff + mypy clean · no mock frameworks ·
every `{{claim}}` resolves · provenance linter clean. Re-running the kernels regenerates
every number and figure in the curriculum; exact current coverage comes from the test
report.

The gates that run offline are enforced in CI. The live proofs are not: Docker, a seeded
SkillTree, raw `FORM` login, and the browser console check need a daemon and a real
browser, so they stay local and are deliberately never simulated. A green badge here means
the offline gate set passed, and nothing more. Full live dependency parity has been proven
locally against skills-service 4.6.0.

Two boundaries stated plainly. SkillTree's NSA-origin provenance is cited for platform
context and is not an endorsement of this curriculum. This release makes **no claim of
learner efficacy**: the learner-pilot contract in `src/pilot/` is protocol-only, defining
privacy, exports, and missing-data handling without storing learner state or measuring
outcomes.

## Contributing and reporting

Issues and pull requests are welcome at
[the repository](https://github.com/ActiveInferenceInstitute/Active_Skillference/issues).
Before changing curriculum content, kernels, or the manuscript, read
[`AGENTS.md`](AGENTS.md) for the invariants and [`docs/`](docs/README.md) for the layer
you are touching. The short version: numbers reach learners only through claim tokens, the
prerequisite graph stays acyclic and connected, citations resolve in two places, and every
gate fails closed. Run `./gates.sh all` (or the individual arms — `lint`, `types`,
`artifacts`, `checks`, `test`, `docs`, `gnn`, `render`) before opening a pull request;
[`docs/gates.md`](docs/gates.md) lists exactly what each arm runs.

## InstituteOS sidecar

This repository carries a committed [`.aii/`](.aii/README.md) sidecar with curated
InstituteOS metadata (`aii-sidecar/v1`): category, maturity, ecosystem relations,
key artifacts, provenance, and portable tasks. It is read by
[InstituteOS](https://github.com/ActiveInferenceInstitute/InstituteOS) tooling and
does not affect the project's build or runtime.
