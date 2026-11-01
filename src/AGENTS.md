# AGENTS.md — src/

Guidance for agents working in `src/`. This is the importable logic of
Active Skillference — a high-integrity micro-learning platform for Active Inference /
the Free Energy Principle. Scripts in `scripts/` only orchestrate I/O; everything here
computes, validates, or converts.

## Layering (bottom-up)

1. **`kernels/`** — pure, tested, deterministic math (nats). The **only** source of
   quantitative values.
   - `information.py`: `entropy`, `kl_divergence`, `cross_entropy`, `mutual_information`, `surprise`
   - `distributions.py`: `softmax`, `normalize`, `log_stable`, `dirichlet_expected`, `dirichlet_expected_log`
   - `inference.py`: `bayes_posterior`, `variational_free_energy`, `log_evidence`, `elbo`
   - `active_inference.py`: `expected_free_energy`, `policy_posterior`, `DiscreteActiveInferenceAgent`
   - `predictive_coding.py`: linear-Gaussian precision-weighted descent to the analytic minimum
   - `examples.py`: worked examples on fixed inputs; `build_claim_registry()` runs them all and registers the deterministic claim ledger (`SEED` for any stochastic step).
2. **`provenance/`** — the integrity gate.
   - `claims.py`: `ClaimRegistry.register(name, value, *, units, source, description)`; `has`/`get`/`value`/`names`/`to_json`. Re-registration with a different value/provenance raises; string claim values may not contain digits.
   - `binding.py`: `render` / `render_graph` (substitute `{{claim:NAME}}`, fail closed on unbacked **or** malformed tokens); `validate_curriculum` / `validate_skill`; `validate_manuscript_dir` / `validate_manuscript_text`; `lint_graph` / `lint_curriculum` / `find_unbacked_numbers` (flag bare decimal result numbers in prose).
3. **`scholarship/`** — citation source coverage.
   - `coverage.py`: load `data/scholarship_sources.yaml`, parse authored manuscript citations, validate them against `references.bib`, and write `scholarship_coverage.json`.
   - `source_health.py` / `source_health_network.py` / `source_health_report.py`: locator syntax, role specificity, and dead-link / bot-block / role-gap / boundary-source buckets.
   - `frontier_sources.py` / `gap_report.py`: separate frontier and boundary support from genuine source-health issues.
4. **`manuscript/`** — generated figure-surface validation.
   - `audit.py`: validate `figure_registry.json` against manuscript figure declarations,
     `[@fig:...]` references, readable nonblank PNGs, caption/alt-text specificity,
     semantic metadata, claim tokens, and dashboard figure artifacts; write
     `manuscript_artifacts.json`.
   - `claim_support.py`: validate manuscript `claim-support` anchors against evidence
     classes, citations, variables, claim tokens, figures, validators, and limitation
     markers; write `manuscript_claim_support.json`.
   - `variables.py`: keep generated counts bound to tokens rather than prose literals.
   - `american_english.py`: reject British spelling variants in authored prose.
   - `web_math.py`: check that rendered HTML surfaces carrying math load MathJax.
5. **`curriculum/`** — the validated DAG.
   - `model.py`: frozen `Stratum`/`Subject`/`Skill`/`AssessmentQuestion` (`Skill.claim_tokens()` scans every learner-facing field).
   - `graph.py`: `CurriculumGraph.validate()` (acyclic via iterative three-color DFS, unique ids, no dangling/duplicate/self prerequisites, foundational roots only), `topological_order()` (Kahn, deterministic), `levels()`, `is_connected_foundations_to_applications()`, `stats()`.
   - `catalog.py`: entry point only — `build_subject_list()`, then `validate()`, the
     foundations→applications connectivity check, and `quality.py::validate_curriculum_quality`.
   - `catalog_data/assembly.py`: thin `build_subject_list()`; canopy in
     `subjects_canopy.py` over the inline stratum tuples in `core_strata.py`; extensions
     split across `subjects_extensions_pass5.py`, `subjects_extensions_tracks.py`,
     `subjects_extensions_hardening.py`, `subjects_extensions_review.py` (aggregated by
     `subjects_extensions.py`), each importing the `_ext_*.py` modules that sit one level
     up in `curriculum/`. Authoring shorthands live in `authoring.py`; graph hardening in
     `normalize.py` with per-question strategies in `assessment_normalize.py`.
   - `diagnostics.py` / `recommendations.py` / `alignment.py` / `vfe_efe_bridge.py`:
     diagnostic gap map, next-skill ordering by dependency depth, exported-skill/material/
     quiz alignment, and the VFE/EFE→SkillTree bridge data.
   - `materials/`: package (`builders`, `validation`, `github_sources`, `models`) that
     builds local modular dashboard Learn records from the graph and
     `data/course_material_sources.yaml`; shared GitHub commit regex in
     `source_contracts.py`.
6. **`skilltree/`** — the export target.
   - `model.py`: `SkillTreeProject`/`SkillTreeSubject`/`SkillTreeSkill`/`SkillDependency`/`Quiz`/`QuizQuestion` dataclasses (snake_case attrs, camelCase `to_dict`/`to_export_dict`).
   - `summary.py`: shared `ExportSummary` counts for exported projects, dashboard status,
     live-count auditing, and manuscript variables.
   - `exporter.py`: `export_project` / `export_to_json` (graph → SkillTree project; thin field map via the `CurriculumGraphLike` protocol).
   - `client.py`: `SkillTreeClient` (`create_project`/`create_subject`/`create_skill`/`assign_dependency`/`create_quiz`/`report_skill`).
   - `transport.py` / `admin_ops.py`: shared HTTP transport and canonical REST paths.
   - `dependency_reconciler.py`: reconciles exported prerequisite edges against a live
     instance. Each edge gets `attempts_per_edge` bounded attempts; a timed-out write is
     resolved by re-reading the live graph, so an edge that landed late is reported as
     `confirmedAfterTimeout` and a genuine retry increments `retried`. Judge a run by
     `missingAfter`/`extraAfter`, not by the retry counters.
   - `deployment_matrix.py`: the browser-safe deployment modes the dashboard reports.
   - `form_login_core.py` / `form_login_validation.py`: pure FORM-login helpers vs
     browser subprocess orchestration.
   - `local_auth.py` / `local_auth_state.py`: local `FORM` bootstrap, session/XSRF handling,
     ignored on-disk state, trusted-client token exchange.
   - `seeder.py`: `seed(client, project)` — project → subjects → quizzes → skills → dependencies.
7. **`figures/`** — `plots/` package: domain modules (`curriculum`, `kernels`,
   `scholarship_coverage` / `scholarship_source_map` / `scholarship_source_health`,
   `front_matter_cover` / `front_matter_atlas`, `validation`, …), thin re-export shims
   (`scholarship.py`, `front_matter.py`), `registry_io.py` with `FigureRenderContext` and
   `render_all()`; `registry.py`: typed registry/contract loader;
   `registry_manifest.py`: canonical registry rows and semantic overrides. Numeric
   inputs come from the registry/graph; scholarship inputs come from the validated audit;
   claim-support inputs come from the manuscript support audit; `render_all` writes
   `figure_registry.json`; headless `Agg`.
8. **`dashboard/`** — `config.py`/`status.py`/`payload.py`/`artifacts.py`/
   `artifact_catalog.py`/`figure_metadata.py`/`graph_analysis.py`/`live_validation.py`
   plus a tiny HTTP server (`server.py`) for the local learner dashboard. It reads
   generated outputs, exposes a local-only token bridge when bootstrapped, runs reusable
   live-dashboard validation, and mounts/links official SkillTree views plus an additive
   read-only graph recommendation endpoint; progress, ranking, quizzes, and learner
   records remain SkillTree-owned. The static frontend in `dashboard/assets/` is vanilla
   HTML/CSS/JS; read `../DESIGN.md` before editing it, use declared CSS tokens, and do not
   add a frontend framework or npm dependency for this surface.
   Three browser-facing contracts are load-bearing and must not be relaxed casually:
   - `_dashboard_csp()` starts at `default-src 'none'` and then names the SkillTree origin
     in `frame-src` and its `ws://`/`wss://` origin in `connect-src`. The official
     `skills-client-js` display is an iframe on that origin with a SockJS socket back to
     it, and the browser matches the socket against the WebSocket scheme, not the
     configured `http:` origin. Drop either and the Official Display panel is an empty box.
   - `/api/status?defer_live=1` skips only the live parity round trip for first paint;
     `payload.deferred_live_skilltree_summary` returns an explicit
     `checked: false, deferred: true` block. Never let a deferred block be read as a passed
     parity check — validators request the default path.
   - JSON responses above a size threshold are gzip-encoded when the client advertises
     `gzip`, with `Vary: Accept-Encoding`. The decoded bytes are unchanged, so payload
     contracts are unaffected.
9. **`pipeline/`** — importable multi-artifact builders such as
   `generated_outputs.py`; scripts call these and only handle arguments/stdout/exit.
10. **`integration/`** — live-stack orchestration (`full_app_stack.py`) for Docker +
    SkillTree + dashboard browser proofs; invoked from `scripts/validate_full_app_stack.py`.
    `ensure_browser_session_responsive` probes the browser automation daemon and restarts
    it once before a browser proof, so a stale session fails as a named harness problem
    rather than an opaque application failure.
11. **`validation/`** — shared `Finding` base for gate issue dataclasses.
12. **`artifacts/`** — shared deterministic JSON artifact read/write helpers and audit
    payload TypedDicts (`contracts.py`).
13. **`pilot/`** — protocol-only learner-pilot contract validation; it specifies privacy,
    read-only SkillTree exports, feasibility outcomes, and missing-data handling without
    storing learner state or claiming efficacy.
14. **Top-level modules** — `gnn_conformance.py` (the pinned-GNN harness for the
    discrete-agent specification: pin record, pinned `git archive` extraction, and
    specification-vs-kernel checks), `project_paths.py` (`resolve_project_root`,
    `project_output_dirs`), `project_identity.py` (the pinned SkillTree project id/name),
    `live_counts.py` (stale generated-count audit across authored surfaces),
    `roadmap.py` (`tasks.yaml` schema/evidence and the generated roadmap pages),
    `release_readiness.py` (release-isolation inventory), and `net_guard.py` (HTTP(S)-only
    and loopback URL guards).

## Invariants (do not break)

- **Provenance over assertion.** Never hand-type a result number into skill content.
  Compute it in `kernels/examples.py`, register a claim, and reference `{{claim:NAME}}`.
  Input parameters/probabilities in prose go inside `$…$` LaTeX math; `lint_graph` flags
  bare decimals (≥2 fractional digits or scientific notation) in learner-facing prose.
- **DAG.** The curriculum must stay acyclic, fully connected foundations→applications,
  with prerequisites resolving and roots only in the two foundational strata
  (`MATH_FOUNDATIONS`, `PROBABILITY`). Re-run `scripts/build_curriculum.py` after edits.
- **Scholarship.** Every authored manuscript citation must resolve to `references.bib`
  and `data/scholarship_sources.yaml`; re-run `scripts/analyze_scholarship.py` after
  citation edits.
- **`src.*` imports only.** Everything imports under the `src.*` namespace (e.g.
  `from src.curriculum.model import Skill`, `from src.kernels.information import entropy`).
  Do **not** reintroduce bare `kernels.`/`curriculum.`/`skilltree.` imports — they create
  dual module identities under the `pythonpath = [".", "src"]` config, silently splitting
  the registry/graph types and breaking the provenance and DAG invariants.
- **Pure kernels.** Functions in `kernels/` are side-effect-free: inputs in, values out,
  no I/O. File writes and figure rendering live in `figures/` and `scripts/`.
- **No mocks.** HTTP is tested with `pytest-httpserver`; everything else with real data.
- **Coverage.** The enforced floor is 90% on `src/`. `kernels/` is held well above it —
  every kernel change lands with a real-value test asserting an analytic result, not a
  smoke call. Read the current number off the coverage report, not off prose.
- **Dashboard payload compatibility.** Frontend polish must not change `/api/status`,
  `/api/course-materials`, graph, artifact, or SkillTree-link payload shapes without an
  explicit contract update and corresponding tests.

## Gates (run before declaring done, from the project root)

```bash
uv run pytest --cov=src --cov-fail-under=90
uvx ruff check src scripts tests && uvx ruff format --check src scripts tests
uv run mypy src
```

## CLI entry points (orchestrators in scripts/)

| Script | Drives |
| --- | --- |
| `../scripts/build_curriculum.py` | `src.curriculum.catalog.build_curriculum` → stats JSON |
| `../scripts/analyze_scholarship.py` | `src.scholarship.coverage` + `src.figures.plots` |
| `../scripts/run_kernels.py` | `src.pipeline.generated_outputs` |
| `../scripts/validate_claim_support.py` | `src.manuscript.claim_support` + `data/manuscript_claim_support.yaml` |
| `../scripts/validate_manuscript_artifacts.py` | `src.manuscript.audit` + `src.dashboard.artifacts` |
| `../scripts/validate_live_skilltree_dashboard.py` | `src.dashboard.live_validation` |
| `../scripts/validate_release_readiness_inventory.py` | `src.release_readiness` + git-derived release inventory checks |
| `../scripts/export_skilltree.py` | provenance gate + `src.skilltree.export_to_json` |
| `../scripts/seed_skilltree.py` | `src.skilltree.SkillTreeClient` + `seed` |
| `../scripts/reconcile_live_dependencies.py` | `src.skilltree.dependency_reconciler` against a live instance |
| `../scripts/validate_full_app_stack.py` | `src.integration.full_app_stack` live Docker + SkillTree + dashboard proof |
| `../scripts/validate_live_counts.py` | `src.live_counts` stale generated-count audit |
| `../scripts/serve_learner_dashboard.py` | `src.dashboard` local dashboard server |
| `../scripts/validate_learner_pilot_contract.py` | `src.pilot.contract` protocol validator |

## Provenance chain (auditable)

kernel fn → `examples.register(...)` → `{{claim:NAME}}` in a skill → `render`/`export`
(fail-closed) → SkillTree skill description + `output/data/claims.json`. Figures then
register labels/files in `figure_registry.json`, and `src.manuscript.audit` verifies
registry, image content, manuscript, and dashboard surfaces.

## Extending the curriculum

Adding a skill is a data edit in a stratum source — either a `curriculum/catalog_data/`
file (`core_strata.py`, `subjects_*.py`) or one of the `curriculum/_ext_*.py` extension
modules that `catalog_data/subjects_extensions_*.py` aggregates; `_s`/`_q` are defined
in `curriculum/authoring.py`, and `assembly.py` only joins the subject builders. Append
an `_s(...)` with a unique `skill_id`, a stratum, an objective, a description (claim
tokens for any numbers), the quality-gated minimum `_q(...)` assessments
(`MIN_ASSESSMENTS_PER_SKILL`, currently 4, including a transfer-style `MultipleChoice`),
and prerequisites that already exist. If the skill shows a new computed value, add a
worked example in `kernels/examples.py`, register the claim, and reference it.
`build_curriculum()` re-validates on every build.

## See Also

- [`README.md`](README.md) — Subpackage overview
- [`STYLE.md`](STYLE.md) — Code style for `src/`
- [`../tests/test_curriculum_graph.py`](../tests/test_curriculum_graph.py) — DAG engine tests
- [`../tests/test_kernels_active_inference.py`](../tests/test_kernels_active_inference.py) — active-inference kernel tests
- [`../tests/test_provenance.py`](../tests/test_provenance.py) — provenance gate tests
- [`../tests/test_skilltree_exporter.py`](../tests/test_skilltree_exporter.py) — exporter tests
