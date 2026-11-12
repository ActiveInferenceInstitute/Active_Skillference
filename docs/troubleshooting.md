# Troubleshooting

Symptom-driven recipes for the most common breakage modes in Active Skillference.
All commands run from the project root unless noted.

## `ProvenanceError: unresolved claim token {{claim:NAME}}` (export refused)

**Cause.** A skill description, objective, name, or assessment references a
`{{claim:NAME}}` token whose name is not registered by any kernel example. The export
is fail-closed (`src/provenance/binding.py::render` / `validate_curriculum`), so nothing
is written rather than letting a literal token reach a learner.

**Fix.**

1. Confirm the claim name the curriculum expects matches a name `build_claim_registry()` registers:
   ```bash
   uv run python -c "from src.kernels.examples import build_claim_registry; print(build_claim_registry().names())"
   ```
2. If the name is missing, add a worked example in `src/kernels/examples.py` and register it under that exact name (see [`faq.md`](faq.md#how-do-i-add-a-new-claim-a-new-computed-number)).
3. If the token is a typo in `src/curriculum/catalog_data/`, fix the token to match the registered name.
4. Re-run the gate:
   ```bash
   uv run python scripts/export_skilltree.py
   ```

A residual `{{claim:...}}` that survives substitution (e.g. a malformed `{{claim:}}` with
an empty name) also raises `ProvenanceError` — well-formed tokens always substitute, so any
leftover is a malformed placeholder.

## `provenance linter found N unbacked numbers — export refused`

**Cause.** `lint_graph` (in `src/provenance/binding.py`) found a hand-typed decimal
*result* (≥2 fractional digits, e.g. `1.6094`, or scientific notation like `1.6e-3`) in a
learner-facing free-text field — a skill name, objective, description, or assessment
prompt, a correct assessment answer option, or a subject description — instead of arriving
through a `{{claim:NAME}}` token.

**Fix.**

1. Find the offending literals:
   ```bash
   uv run python -c "from src.curriculum.catalog import build_curriculum; from src.provenance.binding import lint_graph; [print(v) for v in lint_graph(build_curriculum())]"
   ```
2. For a *derived result*: compute it in `src/kernels/examples.py`, register a claim, and reference `{{claim:NAME}}` instead of the literal.
3. For a legitimate *input* parameter (a probability, a coefficient): move it inside `$…$` LaTeX math — math spans are excluded from the scan.
4. Re-run `scripts/export_skilltree.py`.

Note: integers, years, single-decimal counts (`0.5`, version `4.2`) are deliberately not
flagged. Wrong assessment distractors are out of scope because they are intentionally
incorrect; correct numeric answers are scanned and should use a claim token when they
contain a derived result.

## `CurriculumError` on `build_curriculum()` — cycle / dangling / non-foundational root

The DAG validator (`src/curriculum/graph.py::validate`) is run inside
`build_curriculum()`, so a structural defect fails the build immediately.

| Message | Cause | Fix |
|---|---|---|
| `cycle detected: a -> b -> a` | A prerequisite chain loops | Break the cycle; prerequisites must point strictly toward foundations |
| `skill 'X' has dangling prerequisite 'Y'` | `Y` is not a defined `skill_id` | Add `Y`, or fix the typo in `X`'s `prerequisites` |
| `skill 'X' lists a duplicate prerequisite` | The same id appears twice | Deduplicate the `prerequisites` tuple |
| `skill 'X' lists itself as a prerequisite` | Self-loop | Remove `X` from its own `prerequisites` |
| `non-foundational skill 'X' (...) has no prerequisites` | A skill outside `math_foundations`/`probability` is a root | Give it at least one prerequisite that already exists |
| `duplicate skill_id 'X'` | Two skills share an id | Rename one; ids must be unique across the whole graph |

Re-validate after any edit:
```bash
uv run python scripts/build_curriculum.py
```
A healthy build prints a live `curriculum valid: <skills> skills / <subjects> subjects /
<edges> prerequisite edges` line and `strata present: 8/8`.

## `ClaimError: ... re-registered with conflicting value/provenance`

**Cause.** `build_claim_registry()` registered a claim name twice with a different value
or different `source`/`units`/`description`. Idempotent re-registration is allowed only
for an *identical* claim; a changed value means a non-deterministic kernel (a defect) or
two examples competing for one name.

**Fix.** Make the kernel deterministic (it should be — examples use a fixed seed), or give
the second example a distinct claim name. A string claim that contains a digit is also
rejected (numeric results must be numeric claims).

## `ModuleNotFoundError: No module named 'curriculum'` (or `kernels` / `skilltree`)

**Cause.** A bare top-level import (`from curriculum.model import ...`) instead of the
`src.*` namespace. Under `pythonpath = [".", "src"]` this creates a *second* module
identity and breaks dataclass/enum identity checks (see [`faq.md`](faq.md#architecture-and-imports)).

**Fix.** Use the `src.*` prefix everywhere, e.g. `from src.curriculum.model import Skill`.
Run tests and type-checking the canonical way:
```bash
uv run pytest --cov=src --cov-fail-under=90
uv run mypy src
```

## SkillTree REST contract mismatch (client test fails or live seed 404s)

**Cause.** `tests/test_skilltree_client.py` mirrors SkillTree's documented admin/report
endpoints with `pytest-httpserver` (a real local server — no mocks). A failure means the
path/body in `src/skilltree/client.py` drifted from what the test (and a real server)
expects. Against a live server, a wrong path returns a non-2xx, which the client raises as
`SkillTreeClientError`.

**Fix.**

1. Compare the asserted path in the failing `test_skilltree_client.py` case against the method in `src/skilltree/client.py` (e.g. `/admin/projects/{projectId}/subjects/{subjectId}/skills/{skillId}`).
2. Keep the client method and the test in lockstep with the documented API.
3. `project_id` must be non-empty — the client rejects an empty id rather than emitting a `//` path that 404s.

## Live SkillTree seed: Docker absent

**Symptom.** `./scripts/run_skilltree.sh` exits with
`ERROR: docker is not installed`.

During the template render pipeline, `scripts/seed_skilltree.py` may instead print
`live SkillTree seed skipped: no service is accepting connections...`; that is an
intentional skip for offline rendering. `run_skilltree.sh` is a requested live bring-up,
so it still fails if Docker or the SkillTree service is absent.

**Scope.** Only the live proof needs Docker. When `docker info` cannot reach the
Docker/Colima daemon, the live path is unavailable, but the build, validation, provenance
gate, dashboard artifact check, and the `output/data/skilltree_project.json` export all run
fully offline.

**Fix / alternatives.**

- Install Docker Desktop / Engine + the Compose plugin, then re-run `./scripts/run_skilltree.sh`.
- On first boot under arm64 Docker/Colima emulation, the pinned amd64 image can take several minutes. Increase the readiness window with `SKILLTREE_WAIT_ATTEMPTS=300 ./scripts/run_skilltree.sh` if the logs show Spring Boot is still starting.
- Or build skills-service from source (see [`../vendor/README.md`](../vendor/README.md)) and seed against it with `uv run python scripts/bootstrap_local_skilltree.py --base-url http://localhost:8080`.
- Either way, the exported JSON in `output/data/skilltree_project.json` is the canonical, verifiable artifact.

## Live SkillTree seed: admin auth required

**Symptom.** `ACTIVE_SKILLFERENCE_LOCAL_AUTH=0 ./scripts/run_skilltree.sh` exits before
starting Docker, or `scripts/seed_skilltree.py --require-live` reaches
`http://localhost:8080/public/status`, then exits with:

```text
ERROR: live SkillTree seed requires admin authentication.
```

**Cause.** The pinned local Docker stack uses SkillTree password auth (`FORM`). A browser
can reach the dashboard and create/login to accounts, but anonymous REST writes to
`/admin/...` endpoints are rejected with `401`.

**Fix / alternatives.**

- Provide a deployment-supported admin bearer token:
  ```bash
  ACTIVE_SKILLFERENCE_LOCAL_AUTH=0 SKILLTREE_TOKEN=... ./scripts/run_skilltree.sh
  ```
- For the local no-login learner shell, run:
  ```bash
  ./scripts/run_skilltree.sh
  ./scripts/run_learning_dashboard.sh
  ```
  That path bootstraps a local root/admin account when the SkillTree database is fresh,
  stores ignored local credentials under `.active_skillference_local/`, seeds the project
  with a session/XSRF-aware admin client, and exposes `/api/skilltree/token` for the
  official learner display.
- For a fresh local Docker volume, raw SkillTree login uses the documented development
  credentials:
  ```text
  username: active-skillference-admin@localhost.invalid
  password: active-skillference-local
  ```
  Override fresh-bootstrap credentials with
  `ACTIVE_SKILLFERENCE_LOCAL_ADMIN_USERNAME` and
  `ACTIVE_SKILLFERENCE_LOCAL_ADMIN_PASSWORD`.
- If a local state file already exists, it remains authoritative. Inspect the current
  ignored local credentials with:
  ```bash
  uv run python scripts/bootstrap_local_skilltree.py --show-local-credentials
  ```
- If a root account already exists but `.active_skillference_local/skilltree_auth.json`
  is missing, restore that state file, reset the local Docker volume, or use the explicit
  `SKILLTREE_TOKEN` deployment path. Do not guess the root password.
- Do not add SkillTree credentials or trusted-client secrets to static dashboard assets.

## Learner dashboard loads but official SkillTree view does not embed

**Symptom.** `http://127.0.0.1:8765` opens and the curriculum/artifact panels work, but
the official learner view shows a fallback link.

**Cause.** SkillTree is offline, local auth was disabled, `.active_skillference_local/`
is incomplete, or the dashboard server was started without `--local-auth`. The dashboard
only mounts the official display when it can exchange a trusted-client token server-side.

**Fix / alternatives.**

- Start the full local path:
  ```bash
  ./scripts/run_learning_dashboard.sh
  ```
- If SkillTree is already running and artifacts are current:
  ```bash
  uv run python scripts/bootstrap_local_skilltree.py --base-url http://localhost:8080
  uv run python scripts/serve_learner_dashboard.py --local-auth
  ```
- Inspect browser-safe readiness:
  ```bash
  uv run python scripts/bootstrap_local_skilltree.py --check
  uv run python scripts/serve_learner_dashboard.py --check --local-auth
  ```
- If a PKI or trusted-client deployment is configured later, pass the matching
  authenticator via `--authenticator` or `SKILLTREE_AUTHENTICATOR`.
- For remote deployments, provide a deployment-owned trusted-client endpoint; do not put
  SkillTree client secrets into static dashboard assets or browser JavaScript.

## Official SkillTree frame is an empty box and the console reports a CSP violation

**Symptom.** The Official Display panel renders as a blank/grey area, and the browser
console shows `Framing 'http://localhost:8080/' violates the following Content Security
Policy directive: "default-src 'none'"` or `Connecting to
'ws://localhost:8080/skills-websocket/...' violates ... "connect-src ..."`.

**Cause.** The dashboard page ships a strict Content-Security-Policy. The official
`skills-client-js` display is an iframe on the SkillTree origin and opens a SockJS
WebSocket to the same host, so the policy must name both explicitly: browsers match the
socket against the `ws:`/`wss:` scheme, not the `http:`/`https:` origin the client was
configured with. Without `frame-src` the `default-src 'none'` fallback blocks the frame
outright.

**Fix.** `_dashboard_csp()` in `src/dashboard/server.py` emits `frame-src <skilltree
origin>` and adds the matching `ws://`/`wss://` origin to `connect-src`. If the panel is
empty again after a CSP edit, run the gate that catches it:

```bash
uv run python scripts/validate_dashboard_console.py \
  --dashboard-url http://127.0.0.1:8765 --require-browser --require-dashboard
```

The known-noise allow-list covers only SkillTree's built-in `Inception` project token
probe; a CSP violation is always a real failure.

## The dashboard takes seconds to show anything on first load

**Symptom.** `http://127.0.0.1:8765` is blank or skeletal for several seconds before any
panel appears, and the delay scales with the size of the live SkillTree graph.

**Cause.** The default `/api/status` response includes a live parity check that logs in as
the local admin and pulls the whole live dependency graph. That is the right answer for a
validator and the wrong answer for first paint.

**Fix.** The page requests `/api/status?defer_live=1` for its first render, which returns
an explicit `"liveSkilltree": {"checked": false, "deferred": true, ...}` block instead of
the parity result, then fetches the full status afterwards. If you are scripting against
the API, omit `defer_live` — a deferred block is not a passed parity check:

```bash
curl -s 'http://127.0.0.1:8765/api/status' | head -c 400          # real parity
curl -s 'http://127.0.0.1:8765/api/status?defer_live=1' | head -c 400   # first paint
```

Large JSON responses are gzip-encoded when the client sends `Accept-Encoding: gzip`, so
add `--compressed` to `curl` (or read `Content-Encoding`) if a raw body looks like binary.

## `reconcile_live_dependencies.py` reports edges as missing that already exist

**Symptom.** A dependency POST times out, the run reports `retried` attempts, and a later
pass shows the same edge already present.

**Cause.** A slow SkillTree write can complete on the server after the client gives up.
Treating that timeout as a failure would either lose the edge or double-post it.

**Fix.** None needed — this is the designed behavior. `src/skilltree/dependency_reconciler.py`
gives each edge `attempts_per_edge` bounded attempts (`--attempts-per-edge`), and after a
timeout it re-reads the live graph authoritatively before deciding. An edge observed live
is counted in `confirmedAfterTimeout` rather than re-posted. Judge the run by
`missingAfter`/`extraAfter` and `complete`, not by the retry counters. Re-check without
writing anything:

```bash
uv run python scripts/reconcile_live_dependencies.py --check-only
```

## `validate_rendered_freshness.py` reports stale text in a deposited bundle

**Symptom.** The freshness gate reports stale roadmap text in a path like
`output/docx/Active_Skillference_combined.docx`, and re-running the PDF render never
fixes it.

**Cause.** `./gates.sh render` owns the PDF only. The DOCX, EPUB, slides and web bundles
under `output/` are deposited publication artifacts from the wider publishing pipeline; the
roadmap-open-count sentence in them is checked by
`check_publication_bundle_roadmap_freshness`, so a roadmap change makes those committed
bundles stale until the publishing pipeline regenerates them.

**Fix.** Regenerate the affected bundle with the publishing pipeline that produced it, or
restore it from the last published release if the change is not meant to be published yet.
Everything under `output/` is generated; do not hand-edit a bundle.

## Browser proofs fail with `browser command timed out` or `code: TIMEOUT`

**Symptom.** `validate_skilltree_form_login.py`, `validate_dashboard_console.py`, or the
full-app validator fails with a browser timeout, and running `chrome-devtools-axi pages`
by hand also returns `MCP error -32001: Request timed out`.

**Cause.** The long-lived `chrome-devtools-axi` daemon session went stale. Every command
then times out regardless of what the page is doing, so the failure looks like a broken
app when the browser harness is the broken part.

**Fix.** `validate_full_app_stack.py` probes the session
(`src/integration/full_app_stack.py::ensure_browser_session_responsive`) and restarts it
once before running a browser proof, so a single stale daemon recovers by itself. If the
restart also fails, the validator names the remediation instead of blaming the app. To
recover manually:

```bash
chrome-devtools-axi stop && chrome-devtools-axi start
chrome-devtools-axi pages   # must answer before rerunning a proof
```

Use `--skip-browser` only to run the non-browser portion of the stack proof; the result
is then explicitly not a browser-verified proof.

## Learn opens a SkillTree error page

**Symptom.** A direct SkillTree skill page shows "Error Page has loaded" or "Tiny-bit of
an error!" after clicking a skill-level Learn link.

**Cause.** Direct SkillTree skill-detail routes are not the stable dashboard Learn
surface for this local stack. The dashboard should open local modular material from
`output/data/course_material_index.json`; official SkillTree navigation is split into
**Open Subject** and **Quiz**.

**Fix / alternatives.**

- Regenerate local lesson material:
  ```bash
  uv run python scripts/build_course_materials.py
  uv run python scripts/validate_course_material_sources.py --online
  ```
- Reopen the dashboard and use **Learn** for the local material panel, **Open Subject**
  for `/subjects/{subjectId}`, and **Quiz** for
  `/subjects/{subjectId}/skills/{skillId}/quizzes/{quizId}`.
- If dashboard JavaScript contains a Learn target shaped like
  `/subjects/{subjectId}/skills/{skillId}`, treat it as a regression and run
  `uv run pytest tests/test_dashboard.py tests/test_course_materials.py`.

## Coverage gate fails (under 90%)

**Fix.**

1. Find the uncovered lines:
   ```bash
   uv run pytest --cov=src --cov-report=term-missing -v
   ```
2. Add real-data tests for the missing branches (no mocks).
3. Re-run until coverage is back at the target and all tests pass.

## `uv` command not found

**Fix.** Install `uv` via the canonical installer (the repo invariant is `uv`-only; never
bootstrap `uv` through `pip`):

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
# Homebrew (macOS)
brew install uv
```

Make sure the install location (e.g. `~/.local/bin`) is on your `PATH`.

## Manuscript references an unbacked claim token

**Cause.** A `manuscript/*.md` section references a `{{claim:NAME}}` token that no kernel
emits (e.g. after a kernel rename). `scripts/run_kernels.py` runs
`validate_manuscript_dir`, which fails closed so a dead token cannot render literally into
the PDF.

**Fix.** Reconcile the token name with `build_claim_registry().names()` (rename the token
or add/register the claim), then re-run `uv run python scripts/run_kernels.py`. Tokens
inside code spans/fences in prose are treated as illustrative syntax and are excluded.

## See also

- [`output_conventions.md`](output_conventions.md) — the `output/` tree and regeneration.
- [`output_inventory.md`](output_inventory.md) — every artifact and its producer.
- [`faq.md`](faq.md) — architecture, imports, and content-authoring questions.
- [`quickstart.md`](quickstart.md) — basic run commands.
- [`../AGENTS.md`](../AGENTS.md) — invariants and the provenance chain.
