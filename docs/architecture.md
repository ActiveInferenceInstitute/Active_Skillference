# Architecture: The Thin-Orchestrator Flow

Active Skillference is built around a strict separation of concerns: **all logic lives
in `src/`; `scripts/` only coordinate I/O.** Understanding this before modifying any
file prevents the most common errors — quantitative values hand-typed instead of bound
to a kernel, business logic trapped in a CLI script, mocks in tests, or imports
escaping the `src.*` namespace.

The single organizing principle is *provenance over assertion*: every number a learner
sees is computed by a tested kernel and flows through a fail-closed provenance gate
before it can reach skill content, a figure, or the rendered PDF.

## The `src/` layers (bottom-up)

| Layer | Package | Responsibility | Key contents |
|---|---|---|---|
| 1. Kernels | `src/kernels/` | Pure, tested math — the **only** source of quantitative values. Deterministic; nats units. | `information.py` (entropy, surprise, KL, mutual information), `distributions.py` (softmax, normalize, Dirichlet), `inference.py` (Bayes posterior, variational free energy, log-evidence, ELBO), `active_inference.py` (`expected_free_energy`, `policy_posterior`, `DiscreteActiveInferenceAgent`), `predictive_coding.py` (linear-Gaussian descent), `examples.py` (worked examples that register every claim) |
| 2. Provenance | `src/provenance/` | Bind content to kernel values; fail closed on unbacked tokens; lint bare numbers. | `claims.py` (`Claim`, `ClaimRegistry`), `binding.py` (`render`, `validate_curriculum`, `render_graph`, `lint_graph`, manuscript validators) |
| 3. Scholarship | `src/scholarship/` | Validate authored citations against the BibTeX bibliography and source-role matrix; separate source-health issue classes from frontier/boundary support. | `coverage.py` (`audit_scholarship`, `validate_scholarship`, `write_scholarship_audit`), `source_health.py`, `source_health_network.py`, `source_health_report.py`, `frontier_sources.py`, `gap_report.py` |
| 4. Manuscript | `src/manuscript/` | Validate generated figure registry, manuscript figure labels/cross-references, readable nonblank PNGs, caption/alt-text/semantic metadata, dense figure companions, dashboard figure artifacts, claim-support anchors, variable binding, spelling, and web math. | `audit.py` (`validate_manuscript_artifacts`, `write_manuscript_artifact_audit`), `claim_support.py` (`validate_claim_support`), `variables.py`, `american_english.py`, `web_math.py` |
| 5. Curriculum | `src/curriculum/` | The typed domain model, the DAG engine, catalog assembly (`catalog_data/` over the `_ext_*.py` stratum sources), quality normalization, diagnostic gap map, next-skill recommendation, export alignment, and local read-only lesson material records. | `model.py`, `graph.py`, `diagnostics.py`, `quality.py`, `recommendations.py`, `alignment.py`, `catalog.py`, `catalog_data/`, `_ext_*.py`, `normalize.py`, `assessment_normalize.py`, `materials/` |
| 6. SkillTree | `src/skilltree/` | Map the validated graph to SkillTree-native artifacts, summarize export counts, drive a live instance over REST, reconcile live prerequisite edges, define browser-safe deployment modes, and support the local trusted-client bridge. | `model.py`, `summary.py`, `deployment_matrix.py`, `exporter.py`, `client.py`, `transport.py`, `admin_ops.py`, `dependency_reconciler.py`, `form_login_core.py`, `form_login_validation.py`, `local_auth.py`, `local_auth_state.py`, `seeder.py` |
| 7. Figures | `src/figures/` | Deterministic figures and companion tables driven by the registry, graph, roadmap, scholarship audits, and claim-support audit (headless `Agg`). | `plots/` (rendering functions and `render_all`), `registry.py` (typed figure registry/contract loader), `registry_manifest.py` (canonical figure rows and semantic overrides), `table_companions.py` |
| 8. Dashboard | `src/dashboard/` | Local learner shell over generated artifacts, live dashboard validation, a server-side token route, and official SkillTree views. | `config.py`, `status.py`, `payload.py`, `artifacts.py`, `artifact_catalog.py`, `figure_metadata.py`, `graph_analysis.py`, `live_validation.py`, `server.py`, `assets/` |

`src/project_paths.py` resolves the project root and the standard `output/`
subdirectories, and `src/project_identity.py` pins the SkillTree project id/name every
producer shares. `src/pipeline/generated_outputs.py` owns the multi-artifact kernel /
scholarship / figure / manuscript-output build that `scripts/run_kernels.py` invokes,
and `src/artifacts/json_io.py` owns the shared deterministic JSON read/write contract for
generated artifacts. Beyond these core authoring→render layers, `src/integration/`
orchestrates the live Docker + SkillTree + dashboard full-app proof, `src/validation/`
hosts shared runtime validation findings, `src/pilot/` holds the protocol-only
learner-pilot contract, and the release-surface modules `src/live_counts.py`,
`src/roadmap.py`, `src/release_readiness.py` and `src/net_guard.py` back the
count-drift, roadmap, release-inventory and URL-scheme gates (see
[`docs/AGENTS.md`](AGENTS.md) for the full source layout).

SkillTree is an NSA-origin open-source substrate. This layer boundary is attribution and
integration guidance, not an endorsement or deployment guarantee: the dashboard keeps
trusted-client exchange server-side, while organization-owned zero-trust, supply-chain,
monitoring, backup, and incident-response controls remain outside this repository.

## Handoff boundaries are verifier-first

The most dangerous seams are not the pure kernels; they are transitions between trusted
representations. The project therefore validates the representation that the next layer
actually consumes:

- `src/skilltree/summary.py::validate_export_payload` checks the serialized SkillTree
  project for unique identifiers, resolvable quiz/dependency references, and acyclic
  dependencies. `export_to_json()` invokes it before writing, and the dashboard invokes it
  before exposing the artifact. A malformed export is unavailable, not an empty project.
- `src/skilltree/client.py` accepts only HTTP(S) service URLs, while
  `src/skilltree/admin_ops.py` quotes every identifier as one path segment. An identifier
  cannot turn into a local-file request, query string, or additional REST path.
- Course-material alignment accepts only absolute, credential-free HTTP(S) pointers, and
  `src/dashboard/assets/app.js` applies the same policy before creating an anchor. Backend
  validation and browser rendering are separate gates because either side can drift.
- Full-stack proof summaries are derived from subproof results. A successful subprocess or
  JSON parse cannot relabel a failed dependency, browser, or admin proof as `ok=true`.
- `src/skilltree/dependency_reconciler.py` treats a write timeout as unknown, not failed.
  Each edge gets `attempts_per_edge` bounded attempts, and a timed-out POST is followed by
  an authoritative read of the live graph; an edge observed live is recorded as
  `confirmedAfterTimeout`, and a genuine retry increments `retried`. The summary therefore
  distinguishes "the server was slow" from "the edge is missing".
- `src/integration/full_app_stack.py::ensure_browser_session_responsive` probes the browser
  automation daemon and restarts it once before any browser proof runs. A stale long-lived
  session answers every command with a request timeout, which would otherwise be reported
  as an application failure instead of a harness failure.

These are narrow contracts rather than a second application framework: pure validators live
under `src/`, scripts continue to coordinate I/O, and each negative control injects the
smallest malformed boundary object that should be rejected.

## The dashboard is a browser-contract surface, not just a file reader

`src/dashboard/server.py` carries three contracts that only a real browser exercises, so
each has its own test and its own gate:

- **Content-Security-Policy.** The page policy starts from `default-src 'none'` and then
  names the SkillTree origin in `frame-src` and its `ws://`/`wss://` origin in
  `connect-src`. The official `skills-client-js` learner display is an iframe on the
  SkillTree origin that opens a SockJS connection back to the same host, and browsers match
  that socket against the WebSocket scheme rather than the configured `http:` origin. Miss
  either directive and the Official Display panel renders as an empty box.
- **First paint versus parity.** `/api/status?defer_live=1` skips only the live parity
  round trip — the call that logs in as the local admin and pulls the whole live dependency
  graph. `src/dashboard/payload.py::deferred_live_skilltree_summary` returns an explicit
  `checked: false, deferred: true` shape with the expected edge count, so a deferred answer
  can never be mistaken for a passed parity check. Validators and proof artifacts request
  the default, non-deferred path.
- **Transfer encoding.** JSON responses over a size threshold are gzip-compressed when the
  client advertises `gzip` (and not when it sends `q=0`), with `Vary: Accept-Encoding`. The
  decoded bytes are identical either way, so payload contracts are unaffected.

## Scripts are thin orchestrators

Every script in `scripts/` only coordinates I/O — it imports `src.*` functions, runs
them, and writes outputs. None contains domain logic.

| Script | What it orchestrates | Writes |
|---|---|---|
| `build_curriculum.py` | `build_curriculum()` (validates the DAG), prints stats and diagnostic review rows | `output/data/curriculum_stats.json`, `output/data/curriculum_diagnostic_gap_map.json` |
| `analyze_scholarship.py` | validates manuscript citation coverage and renders audit artifacts | `output/data/scholarship_coverage.json`, `output/data/scholarship_source_health.json`, `output/data/scholarship_source_health_network.json`, `output/figures/scholarship_coverage.png` |
| `run_kernels.py` | delegates to `src.pipeline.generated_outputs.build_generated_outputs()` to build the registry + graph, run provenance, scholarship, claim-support, figure companion, course-material, and dashboard-artifact gates, and render figures | `output/data/claims.json`, `output/data/curriculum_diagnostic_gap_map.json`, `output/data/manuscript_variables.json`, `output/data/scholarship_coverage.json`, `output/data/scholarship_source_health.json`, `output/data/scholarship_source_health_network.json`, `output/data/scholarship_gap_report.json`, `output/data/figure_table_companions.json`, `output/data/manuscript_claim_support.json`, `output/data/manuscript_artifacts.json`, `output/data/cover_asset_audit.json`, `output/data/front_matter_visual_audit.json`, `output/data/course_material_index.json`, `output/data/course_material_audit.json`, figures, `output/figures/figure_registry.json` |
| `build_course_materials.py` | builds local dashboard lesson records and audits pinned external source pointers | `output/data/course_material_index.json`, `output/data/course_material_audit.json` |
| `validate_course_material_sources.py` | validates pinned external source metadata; `--online` verifies GitHub paths | (exit status only) |
| `validate_course_material_alignment.py` | compares exported SkillTree skills/quizzes/routes against local course-material records | (exit status only) |
| `validate_scholarship_sources.py` | re-checks scholarship source locator syntax, role specificity, lane coverage, and optional online reachability | `output/data/scholarship_source_health.json` |
| `validate_claim_support.py` | re-checks anchored manuscript scientific claims against declared evidence classes | `output/data/manuscript_claim_support.json` |
| `validate_manuscript_artifacts.py` | re-checks generated figure registry, manuscript labels/cross-references, PNGs, semantic metadata, dense table companions, claim tokens, and dashboard figure artifacts | `output/data/manuscript_artifacts.json` |
| `validate_manuscript_variables.py` | fails when manuscript prose hard-codes live generated counts that should remain variable-bound | (exit status only) |
| `validate_american_english.py` | fails on British spelling variants in authored manuscript prose | (exit status only) |
| `validate_live_counts.py` | fails on stale generated counts in docs, metadata, roadmap, or manuscript surfaces | (exit status only) |
| `validate_rendered_freshness.py` | confirms rendered manuscript copies match the current source artifacts | (exit status only) |
| `validate_roadmap.py` | validates `tasks.yaml` schema/evidence, generated `TODO.md` text, and generated `docs/todo/*.md` handoff pages | (exit status only; `--write-todo` refreshes `TODO.md` and `docs/todo/*.md`) |
| `ensure_web_math.py` | inserts MathJax into generated HTML pages that contain math | updated `output/web/*.html` when needed |
| `validate_web_math.py` | checks dashboard and rendered web math surfaces for MathJax support | (exit status only) |
| `validate_dashboard_console.py` | classifies expected versus blocking dashboard browser console messages | (exit status only) |
| `validate_docker_digests.py` | checks Docker/Compose image references for digest pinning where the local stack requires it | (exit status only) |
| `export_skilltree.py` | DAG + registry + provenance gate + `render_graph` → SkillTree JSON | `output/data/skilltree_project.json` |
| `seed_skilltree.py` | builds the provenance-rendered project, drives `seed()` over REST | (network: creates the project on a running SkillTree) |
| `bootstrap_local_skilltree.py` | bootstraps local SkillTree `FORM` auth, seeds, stores ignored trusted-client state | (network + `.active_skillference_local/`) |
| `serve_learner_dashboard.py` | serves the local dashboard shell, checks SkillTree status, reads generated artifacts | (local HTTP server at `http://127.0.0.1:8765`) |
| `run_skilltree.sh` | `docker compose up` (skills-service + Postgres) → local bootstrap seed by default | (live instance at `http://localhost:8080`) |
| `run_learning_dashboard.sh` | Docker SkillTree → regenerate/export → seed → dashboard server | (live SkillTree + local dashboard) |
| `00_preflight.py` | imports `infrastructure.rendering.preflight` from the parent monorepo and checks the `manuscript/` dir before PDF render | (exit status only) |

The table above is illustrative — the authoritative, complete `scripts/` inventory and
its coverage gate live in [`docs/AGENTS.md`](AGENTS.md) (and `scripts/README.md`).
Validator-only scripts not shown here (e.g. `audit_scholarship_gaps.py`,
`validate_full_app_stack.py`, `validate_skilltree_form_login.py`,
`validate_live_skilltree_dashboard.py`, `validate_release_readiness_inventory.py`,
`validate_learner_pilot_contract.py`, `reconcile_live_dependencies.py`,
`reset_local_skilltree.py`, `z_generate_manuscript_variables.py`) follow the same
thin-orchestrator or exit-status-only pattern.

## Dependency direction

```
scripts/  ──→ src.*                  (import + call; I/O only)
src/kernels/        ──→ [stdlib + numpy]   (pure; imports src.provenance.claims only, in examples.py)
src/artifacts/      ──→ [stdlib json/pathlib] (shared generated-artifact JSON I/O)
src/provenance/     ──→ src.curriculum, src.kernels
src/scholarship/    ──→ data/scholarship_sources.yaml + manuscript/
src/manuscript/     ──→ manuscript/ + data/manuscript_claim_support.yaml + output/figures/figure_registry.json + src/dashboard/artifacts.py
src/curriculum/     ──→ (self-contained typed model + DAG engine + pinned material pointers)
src/skilltree/      ──→ src.curriculum.model (via a structural Protocol; no hard graph dep)
src/figures/        ──→ src.curriculum, src.provenance, src.scholarship audit payloads
src/dashboard/      ──→ src.project_paths + src.skilltree (client, summary, reconciler, local auth) + generated output files
src/pipeline/       ──→ src.kernels + src.curriculum + src.scholarship + src.figures + src.manuscript
src/integration/    ──→ src.artifacts.json_io + src.net_guard (subprocess-drives the scripts/ validators)
tests/    ──→ src.*                   (direct testing; pytest-httpserver for REST)
```

No arrows go upward, and **every import is under the `src.*` namespace** — never bare
`kernels.`/`curriculum.`/`skilltree.`/`provenance.`/`figures.`. Under the
`pythonpath = [".", "src"]` config a bare import creates a *second* module identity for
the same file, so two `ClaimRegistry` classes would compare unequal. Keep `from
src.curriculum.model import Skill`, not `from curriculum.model import Skill`.

## The provenance + curriculum flow

```mermaid
graph TD
    K[src/kernels/*.py<br/>tested math] --> EX[src/kernels/examples.py<br/>worked examples]
    EX -->|register name,value,units,source| REG[ClaimRegistry<br/>src/provenance/claims.py]

    CAT[src/curriculum/catalog.py<br/>build_curriculum] --> G[CurriculumGraph<br/>src/curriculum/graph.py]
    G -->|validate: acyclic, no dangling,<br/>foundational roots, connected| G

    G --> GATE[src/provenance/binding.py]
    REG --> GATE
    GATE -->|validate_curriculum + lint_graph<br/>FAIL CLOSED on unbacked/bare number| GATE
    GATE -->|render_graph: resolve every {{claim:NAME}}| RG[rendered graph]

    RG --> EXP[src/skilltree/exporter.py] --> VALIDATE[serialized export validator]
    VALIDATE --> JSON[output/data/skilltree_project.json]
    RG --> SEED[src/skilltree/seeder.py] -->|REST, dependency-safe order| LIVE[live SkillTree]
    JSON --> DASH[src/dashboard<br/>local learner shell]
    LIVE --> DASH

    REG --> FIG[src/figures/plots/]
    G --> FIG
    SCH[data/scholarship_sources.yaml<br/>+ references.bib] --> SA[src/scholarship/coverage.py]
    SA --> FIG
    FIG --> PNG[output/figures/*.png]
    FIG --> FREG[output/figures/figure_registry.json]
    FREG --> MA[src/manuscript/audit.py]
    MAN[manuscript/*.md] --> MA
    DASH --> MA
    MA --> MJSON[output/data/manuscript_artifacts.json]

    REG --> CLAIMS[output/data/claims.json]
```

Change a kernel and its result changes; the claim, the rendered skill content, and the
figures are regenerated together. The manuscript artifact audit closes the separate drift
path where a figure file exists but the registry, manuscript label, cross-reference, or
dashboard artifact inventory no longer agrees.

## Infrastructure dependency (PDF only)

The project's own pipeline (kernels, DAG, export, figures, tests) has **no dependency**
on the parent monorepo. The single exception is PDF rendering: `scripts/00_preflight.py`
imports `infrastructure.rendering.preflight` from the surrounding monorepo to validate
the `manuscript/` directory before a render. The PDF (`output/pdf/Active_Skillference_combined.pdf`)
is produced via that monorepo's `infrastructure/` rendering. See
[`rendering_pipeline.md`](rendering_pipeline.md).

## Forbidden patterns

| Pattern | Why it is forbidden | Correct alternative |
|---|---|---|
| Hand-typing a result number into skill or manuscript prose | Breaks provenance; the linter flags decimals with ≥2 fractional digits or scientific notation | Compute it in `src/kernels/examples.py`, register a claim, reference `{{claim:NAME}}` |
| Adding a manuscript citation without `data/scholarship_sources.yaml` | Citation exists syntactically but has no declared support role or lane | Add the BibTeX entry and a source-matrix row, then run `scripts/analyze_scholarship.py` |
| Bare `from kernels...` / `from curriculum...` imports | Dual module identity under `pythonpath=[".","src"]` | Always `from src.<package>...` |
| Domain logic inside `scripts/` | Cannot be unit-tested without running the script | Move it into the matching `src/` package and add a test |
| Re-implementing learner progress in `src/dashboard/` | Splits the SkillTree system of record | Link/embed official SkillTree views; keep progress, ranking, self-reporting, quizzes, and auth in SkillTree |
| A non-foundational skill with zero prerequisites | `CurriculumGraph._check_foundational_roots` raises | Add prerequisites, or place genuinely-root content in a foundational stratum |
| Adding a prerequisite to a skill that does not exist yet | Dangling edge — `validate()` raises | Add the prerequisite skill first |
| `unittest.mock`, `MagicMock`, `@patch` in `tests/` | Zero-mock policy | Real numpy data; `pytest-httpserver` for the SkillTree REST client |

## How to add a skill

1. **Append a `_s(...)` entry to the appropriate stratum source** — either a
   `src/curriculum/catalog_data/` file (e.g. `core_strata.py`, `subjects_canopy.py`) or one
   of the `src/curriculum/_ext_*.py` extension modules that
   `catalog_data/subjects_extensions_*.py` aggregates; `_s` and `_q` are defined in
   `src/curriculum/authoring.py`. Give it a unique `skill_id`
   (alnum/underscore, starting with a letter), its `Stratum`, a one-line `objective`,
   a markdown `description` (LaTeX inside `$…$` for equations; `{{claim:NAME}}` for any
   computed value), the quality-gated minimum `_q(...)` assessments, and a
   `prerequisites` tuple whose ids already exist. The skill must belong to a `Subject`
   in the same stratum. (`src/curriculum/catalog.py` holds no authored content — it calls
   `build_subject_list()` from `catalog_data/assembly.py`, then runs `validate()`, the
   foundations→applications connectivity check, and `validate_curriculum_quality`.)
2. **If it shows a new computed value**, add a worked example to
   `src/kernels/examples.py`, register the claim in `build_claim_registry()`, and
   reference it via `{{claim:NAME}}`.
3. **Re-validate**: `uv run python scripts/build_curriculum.py` (acyclic, connected,
   foundational roots). Then `uv run python scripts/run_kernels.py` and
   `uv run python scripts/export_skilltree.py` to confirm the provenance gate passes.
4. **Test**: `uv run pytest tests/ --cov=src --cov-fail-under=90`. Add or extend a test
   in `tests/test_curriculum_catalog.py` if the skill encodes a new structural property.

## How to add a subject

Append a `Subject(subject_id, name, stratum, description, skills=(...))` in the
`src/curriculum/catalog_data/` source files and include it in the subject list that
`build_subject_list()` in `catalog_data/assembly.py` assembles (`build_curriculum()`
in `src/curriculum/catalog.py` calls `build_subject_list()`). All skills in the
subject must share the subject's stratum (`Subject.__post_init__` enforces this).

## How to add a kernel

1. Add the pure function to the right module in `src/kernels/` (e.g. a new information
   quantity in `information.py`), with type hints and a docstring. Keep it deterministic
   and dependency-free apart from numpy.
2. Add a test in the matching `tests/test_kernels_*.py` asserting a known analytical
   value, and keep the project-wide `src/` coverage gate at or above 90%.
3. Expose a result through `src/kernels/examples.py` (register a claim) so the
   curriculum can reference it via `{{claim:NAME}}`.
