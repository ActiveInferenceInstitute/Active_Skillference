---
project: Active_Skillference
task: "High-integrity micro-learning platform for Active Inference & the FEP on the SkillTree framework"
effort: E5
phase: complete
progress: "tasks.yaml canonical"
iteration: 8
mode: complete
started: 2026-06-09
updated: 2026-06-20
algorithm_config:
  tier: E5
  thinking_floor: 8
  delegation_floor: 4
---

# Active_Skillference — Ideal State Artifact

## Problem

There is no rigorous, end-to-end, **verifiably correct** micro-learning curriculum for
Active Inference (AIF) and the Free Energy Principle (FEP) that (a) spans the full
dependency chain from background mathematics through computational examples to
applications, (b) is structured as a navigable prerequisite graph a learner can
traverse, and (c) guarantees that every quantitative claim a learner is shown was
produced by tested code rather than hand-typed (and therefore drift-prone) prose.

Existing AIF教材 are either mathematically rigorous but unstructured (papers/books),
or well-structured but pedagogically shallow (slide decks). None bind their numbers
to a reproducible computational substrate, and none export into a gamified
micro-learning runtime that tracks a learner's progress through the prerequisite DAG.

## Vision

A learner opens a SkillTree instance and sees Active Inference laid out as a living
**skill tree**: foundational math at the roots, the Free Energy Principle at the trunk,
active inference and its computations as the branches, and applications
(neuroscience, robotics, ML, collective behavior, cognitive security) as the canopy.
Every skill they unlock has a crisp objective, a rigorous derivation, and a *runnable*
worked example whose every number was computed by a tested kernel in this repository —
so what they learn is exactly what the code does. The prerequisite edges are real:
you cannot reach Expected Free Energy without KL divergence, and you cannot reach KL
divergence without entropy and Bayes. The euphoric surprise: the curriculum *is*
executable — `run_kernels.py` regenerates every claim in the tree, and the same graph
that teaches also seeds a real, gamified SkillTree server.

## Out of Scope

- Re-implementing SkillTree itself — we vendor the NSA `skills-service` and target its
  data model / REST contract; we do not fork its server.
- A novel inference engine competing with `pymdp`/SPM — kernels are pedagogical,
  correctness-first reference implementations, not a performance library.
- Authoring polished long-form prose for every one of hundreds of skills in this build —
  the *engine* makes enumeration maximal and data-driven; density grows by adding data.
- Hosting/auth/multi-tenant operation of a production SkillTree deployment.
- Touching the monorepo's `infrastructure/` or the co-actor's `template_active_inference`.

## Principles

- **Provenance over assertion.** A number in learner-facing content is valid only if a
  tested kernel emitted it. Hand-typed quantitative claims are a defect, not a shortcut.
- **The graph is the truth.** Prerequisite structure is a validated DAG; a cycle or a
  dangling prerequisite is a build failure, not a stylistic note.
- **Substrate independence (Deutsch reach).** The same kernel that teaches entropy is the
  one used downstream for KL, free energy, and EFE — one definition, reused, never re-typed.
- **Falsifiability (Science).** Every skill carries an assessment that can fail a learner
  who does not know it; a skill with no failable check is not yet a skill.
- **Thin orchestrator.** All logic lives in `src/`; scripts only coordinate I/O.
- **No mocks.** Every test uses real computation or a real local server.

## Constraints

- Built on `template_code_project` conventions: `src/` (≥90% coverage), `tests/` (no mocks),
  thin `scripts/`, `manuscript/` → PDF, `manuscript/config.yaml` render wiring.
- `uv` for deps; Python ≥3.10; deterministic (fixed seeds) outputs.
- SkillTree integration must match the real data model: **Project → Subject → Skill**,
  skill fields `{skillId, name, pointIncrement, numPerformToCompletion, description,
  helpUrl, selfReportingType ∈ {HonorSystem, Approval, Quiz}}`, cross-skill prerequisite
  dependencies (learning paths), quizzes for assessment.
- **Structural invariants (R9 pins):** curriculum graph is a DAG (0 cycles); every
  prerequisite edge resolves to an existing skill; every Subject maps to exactly one
  stratum; every quantitative claim token resolves to a registered kernel claim;
  exported SkillTree JSON has unique skillIds within a project.
- Docker/Colima availability is an external release-rehearsal dependency tracked by
  `asf-live-full-stack-release-rehearsal`; the REST contract remains verified against a
  pytest-httpserver mirror of SkillTree's endpoints when the live daemon is unavailable.
- Work lands in the local-only sidecar repo (`GitHub/projects`), never the public monorepo.

## Goal

Deliver, inside `projects/working/Active_Skillference`, a fully-tested Python platform that
(1) defines an AIF/FEP curriculum as a validated prerequisite DAG spanning all strata
(math → probability → information theory → variational methods → FEP → active inference →
computation → applications), (2) backs every quantitative claim with a tested computational
kernel via a content-provenance gate, (3) exports the curriculum into SkillTree-native
artifacts and can seed a live instance over REST, (4) vendors a runnable SkillTree server
with run/seed scripts, and (5) documents the whole thing in a rendered manuscript — with
`src/` coverage ≥90%, no mocks, and all structural invariants enforced as code.

## Current Roadmap Authority

As of 2026-06-18, `tasks.yaml` is the canonical forward roadmap and `TODO.md` is its
generated reader view (`scripts/validate_roadmap.py --write-todo`). The long ISC ledger
below is retained as build history and invariant evidence; it is not a second open-work
queue. Deferred Forge/GPT-5.4 audit entries are superseded by
`asf-cross-vendor-security-audit`, live SkillTree/JVM rehearsal by
`asf-live-full-stack-release-rehearsal`, and DOI/public-repository work by
`asf-public-release-metadata`.

## Criteria

### Computational kernels (high-integrity core)
- [x] ISC-1: `kernels/information.py` implements `entropy`, `kl_divergence`, `cross_entropy`, `mutual_information`, `surprise` with tested numeric values.
- [x] ISC-2: `entropy` of a uniform categorical over n outcomes equals `log(n)` (probe: pytest assert within 1e-9).
- [x] ISC-3: `kl_divergence(p, p)` == 0 and `kl_divergence(p, q) >= 0` for sampled p,q (Gibbs' inequality test).
- [x] ISC-4: `kernels/distributions.py` implements `softmax` (temperature/precision), `normalize`, `categorical`, `dirichlet_expected`, all tested.
- [x] ISC-5: `softmax` is shift-invariant and sums to 1 (probe: assert sum==1, softmax(x)==softmax(x+c)).
- [x] ISC-6: `kernels/inference.py` implements exact discrete `bayes_posterior` tested against a hand-checked 2x2 example.
- [x] ISC-7: `variational_free_energy(q, A, obs, prior)` returns F = complexity − accuracy, tested to equal surprise + KL[q‖posterior] on a discrete model.
- [x] ISC-8: At the true posterior, VFE equals the negative log-evidence (surprise) within 1e-9 (the bound is tight).
- [x] ISC-9: `kernels/active_inference.py` implements `expected_free_energy` decomposed into epistemic + pragmatic terms, tested.
- [x] ISC-10: `policy_posterior(G, gamma)` == `softmax(-gamma * G)` and is tested for monotonic preference toward low-G policies.
- [x] ISC-11: `DiscreteActiveInferenceAgent` with (A,B,C,D) runs a perception→policy→action loop deterministically (fixed seed) producing a reproducible trajectory.
- [x] ISC-12: A worked T-maze (or equivalent epistemic/pragmatic) example shows the agent choosing the information-seeking action when cue is uncertain (tested behavioral assertion).
- [x] ISC-13: Gradient descent on free energy converges (perception-as-inference example), tested for monotone F decrease.
- [x] ISC-14: Jensen's inequality / ELBO decomposition demonstrated numerically (ELBO ≤ log-evidence), tested.
- [x] ISC-15: All kernels are deterministic under a fixed seed (probe: two runs byte-identical results).

### Curriculum graph
- [x] ISC-16: `curriculum/model.py` defines typed `Stratum`, `Subject`, `Skill`, `Prerequisite`.
- [x] ISC-17: `curriculum/graph.py` `CurriculumGraph.validate()` detects cycles and raises on any cycle (tested with a deliberately cyclic fixture).
- [x] ISC-18: `validate()` rejects any prerequisite referencing a non-existent skill id (tested).
- [x] ISC-19: `topological_order()` returns a valid topo sort; every skill appears after all its prerequisites (tested).
- [x] ISC-20: Curriculum spans all 8 strata; each stratum has ≥1 Subject (probe: assert set of strata == full enumeration).
- [x] ISC-21: Maximal enumeration: total skill count ≥ 120 (probe: `len(graph.skills) >= 120`).
- [x] ISC-22: Every skill has a non-empty objective and ≥1 assessment question (probe: assert over all skills).
- [x] ISC-23: Every non-root skill has ≥1 prerequisite; root skills are only in the foundational strata (tested invariant).
- [x] ISC-24: The graph is connected from foundations to applications (every applications skill is reachable from a foundational root via prerequisite edges) (tested).
- [x] ISC-25: `level()` assigns each skill a depth = longest prerequisite chain (tested monotonicity).

### Content-provenance binding
- [x] ISC-26: `provenance/claims.py` `ClaimRegistry` registers named claims `{name, value, units, source}` from kernel runs.
- [x] ISC-27: Skill content references quantitative values only via `{{claim:NAME}}` tokens (no bare result numbers).
- [x] ISC-28: `provenance/binding.py` `render(skill)` substitutes every claim token with the registered kernel value (tested round-trip).
- [x] ISC-29: `binding.validate()` fails if a skill references a claim token with no registered claim (tested with a dangling-token fixture).
- [x] ISC-30: Anti: a skill description embedding a hand-typed result number not covered by a claim token is flagged by the numeric-provenance linter (tested with a planted bare number).
- [x] ISC-31: `run_kernels.py` populates the ClaimRegistry, and `export_skilltree.py` refuses to export if any claim is unresolved (tested fail-closed path).

### SkillTree integration
- [x] ISC-32: `skilltree/model.py` dataclasses `SkillTreeProject`, `SkillTreeSubject`, `SkillTreeSkill`, `SkillDependency`, `Quiz`, `QuizQuestion` match SkillTree field names.
- [x] ISC-33: `skilltree/exporter.py` converts a `CurriculumGraph` into a SkillTree project export dict (subjects, skills, dependencies, quizzes).
- [x] ISC-34: Exported skill has all required SkillTree fields and `selfReportingType` ∈ {HonorSystem, Approval, Quiz} (schema test).
- [x] ISC-35: Exported dependencies mirror curriculum prerequisites exactly (count + endpoints match) (tested).
- [x] ISC-36: Exporter produces unique `skillId`s within the project (tested no-dup invariant).
- [x] ISC-37: `skilltree/client.py` `SkillTreeClient` implements `create_project`, `create_subject`, `create_skill`, `assign_dependency`, `create_quiz`, `report_skill`.
- [x] ISC-38: Client methods hit the correct SkillTree REST paths (verified against pytest-httpserver mirror — assert request path/method/body).
- [x] ISC-39: `seed_skilltree.py` walks the exported graph and issues create calls in topological order (tested against httpserver).
- [x] ISC-40: Anti: client never reports success on a non-2xx response (tested error path raises).

### Vendored runnable instance
- [x] ISC-41: `vendor/` wires the NSA `skills-service` (submodule ref or pinned docker-compose) with a pinned version.
- [x] ISC-42: `scripts/run_skilltree.sh` exists and documents the one-command bring-up (docker-compose up).
- [x] ISC-43: `docker-compose.yml` references the official `skilltree/skills-service` image + Postgres with correct ports/env.
- [x] ISC-44: Live instance comes up and is seeded — CLOSED 2026-06-10 via ISC-81's live probe (Docker now available; see Comprehensive pass #4 verification).

### Pipeline / gates / manuscript
- [x] ISC-45: `src/` test coverage ≥90% (probe: `pytest --cov=src --cov-fail-under=90`).
- [x] ISC-46: Zero mocks in tests (probe: grep for `mock`/`MagicMock`/`patch` returns nothing in tests/).
- [x] ISC-47: `ruff check` and `ruff format --check` pass on src/ and scripts/ and tests/.
- [x] ISC-48: `mypy src/` passes (typed public APIs).
- [x] ISC-49: `scripts/build_curriculum.py` runs, validates the DAG, and prints stats (skill/subject/edge counts) (tested smoke).
- [x] ISC-50: `scripts/run_kernels.py` emits `output/data/claims.json` and figures (tested smoke).
- [x] ISC-51: `scripts/export_skilltree.py` emits `output/data/skilltree_project.json` (tested smoke).
- [x] ISC-52: `manuscript/` sections rewritten for the AIF micro-learning platform (no optimization-domain residue) (grep probe).
- [x] ISC-53: `manuscript/config.yaml` title/keywords/experiment reflect the AIF platform (read-back probe).
- [x] ISC-54: At least 3 figures generated (curriculum DAG, an EFE/epistemic-pragmatic plot, a free-energy convergence plot) (file-exists probe).
- [x] ISC-55: `README.md` and `AGENTS.md` describe the platform, not the optimization template (grep probe).
- [x] ISC-56: Anti: no residual `optimizer`/`gradient_descent quadratic` template symbols remain imported in `src/__init__.py` (grep probe).
- [x] ISC-57: Cross-vendor Forge audit of kernels + provenance gate returns no unresolved CRITICAL (VERIFY).
- [x] ISC-58: Advisor call logged before `phase: complete` (VERIFY).

### Comprehensive review pass (2026-06-09 re-baseline)
- [x] ISC-59: Authoritative gate (`pytest --cov=src`) is GREEN — 0 failing tests — re-run and quoted this session (R8 ground truth; ISA's stale 23/58 superseded).
- [x] ISC-60: Anti: leaving the suite red, or claiming "done"/progress without re-running the gate and quoting its output (verification-theater fingerprint 2026-06-03).
- [x] ISC-61: Anti: responding with a status/progress report instead of delivered, verified work (incomplete-response fingerprint — the exact prior failure this prompt shape produced).
- [x] ISC-62: RedTeam verifier-first pass over the high-integrity surface (provenance fail-closed, DAG validation, SkillTree REST contract, no-mocks) surfaces and resolves/triages every confirmed defect.
- [x] ISC-63: FirstPrinciples challenge of the four integrity claims (provenance-over-assertion, graph-is-truth, falsifiability, substrate-independence) recorded with verdicts.
- [x] ISC-64: Science falsification of ≥1 curriculum/kernel claim that could be wrong (e.g. agent epistemic preference, ELBO bound tightness) run as a real experiment with measured result.

### Documentation & metadata accuracy pass (2026-06-09 #2)
- [x] ISC-65: Root metadata (`codemeta.json`, `CITATION.cff`, `.zenodo.json`) carries Active_Skillference identity (title, AIF keywords) — 0 "gradient descent"/"Convergence Analysis of Gradient Descent" strings (grep probe).
- [x] ISC-66: Anti: no fabricated/unminted DOI presented as real — the template's `10.5281/zenodo.20417136` removed; LOCAL-ONLY/unpublished status honest (grep probe + read-back).
- [x] ISC-67: Version is `1.0.0` consistently across `pyproject.toml`, `src/__init__.py`, `codemeta.json`, `CITATION.cff`, `.zenodo.json` (grep probe — 0 occurrences of `2.3`/`2.5.0`).
- [x] ISC-68: `domain_profile.yaml` + `experiment_plan.yaml` describe the AIF curriculum/kernel domain — 0 `gradient`/`step_size`/`quadratic`/`convergence_plot` strings (grep probe).
- [x] ISC-69: Stale counts updated to ground truth `200 tests` / `99.30%` everywhere — 0 `168 tests`, 0 `99.2%` (grep probe across docs+manuscript+README).
- [x] ISC-70: Every `docs/*.md` describes Active_Skillference (kernels/curriculum/provenance/skilltree) — 0 `optimizer.py`/`invariants.py`/`optimization_analysis.py`/`template_code_project` identity strings (grep probe).
- [x] ISC-71: Figure references everywhere name the 3 real figures (`curriculum_dag`, `free_energy_descent`, `efe_decomposition`) — 0 `convergence_plot`/`step_size_sensitivity`/`performance_benchmark`/`stability_analysis` (grep probe).
- [x] ISC-72: No dangling/escaping links — `../../../../template/...` and `docs/_generated/canonical_facts.md` references removed/fixed; every relative link in `docs/` + manuscript meta resolves (link-resolve probe).
- [x] ISC-73: `scripts/` docs (`README`/`AGENTS`/`CONVENTIONS`) name the ACTUAL scripts — 0 `optimization_analysis.py`/`build_dashboard.py`/`z_generate_manuscript_variables.py`/`generate_api_docs.py` (grep probe).
- [x] ISC-74: `src/` docs (`README`/`AGENTS`/`STYLE`) reference actual modules — 0 nonexistent `optimizer.py`/`invariants.py`/`check_template_drift.py` references (grep probe).
- [x] ISC-75: manuscript meta (`AGENTS`/`README`/`SYNTAX`) rebased; `references.bib` carries AIF references and is consistent with manuscript citations (read-back + cite-vs-bib cross-check).
- [x] ISC-76: `pyproject.toml` comment no longer references nonexistent `docs/_generated/canonical_facts.md` (grep probe).
- [x] ISC-77: `tasks.yaml` reflects ground truth — `asf-5` done, statuses accurate to this session's gate (read-back).
- [x] ISC-78: manuscript render path validated — `00_preflight.py` runs clean AND the render command is documented accurately (or its parent-infrastructure dependency stated) (Bash probe).
- [x] ISC-79: Anti: introducing any NEW inaccuracy/unbacked claim while rebasing — provenance linter clean + no new bare-number defects (Bash probe via `run_kernels.py`).
- [x] ISC-80: Authoritative gate stays GREEN after all doc edits — `pytest --cov=src` = 200 passed / 99.30% (re-run + quote).

### Learner dashboard & local-auth surface (2026-06-10 comprehensive pass #4)
- [x] ISC-81: Live SkillTree seed VERIFIED (closes ISC-44's deferred probe): `/oauth/token` trusted-client exchange returns an `access_token`, and the live admin API reports the seeded project with skill/subject counts equal to the export (124 skills / 24 subjects) (curl/Bash probe, quoted).
- [x] ISC-82: `src/skilltree/local_auth.py` test coverage ≥90% via real pytest-httpserver tests, no mocks (probe: coverage report line).
- [x] ISC-83: `src/dashboard/server.py` coverage ≥95% — POST/OPTIONS routes, token-endpoint 503/502 error paths, media-type map all exercised (probe: coverage report line).
- [x] ISC-84: `src/dashboard/status.py` coverage 100% — HTTPError/URLError/timeout/JSON-decode branches (probe: coverage report line).
- [x] ISC-85: Total `src/` coverage restored ≥95% (probe: pytest --cov total line).
- [x] ISC-86: Local auth state file is written owner-only (0600) and state dir 0700 (tested assertion on st_mode).
- [x] ISC-87: Anti: admin password / client secret NEVER appear in any browser-safe payload — `describe_local_auth().to_public_dict()`, `/api/config`, `/api/status` (tested negative assertion).
- [x] ISC-88: Anti: `.active_skillference_local/` is git-ignored — `git check-ignore` confirms BEFORE any commit (Bash probe).
- [x] ISC-89: Dashboard token endpoint returns 503 when local auth not bootstrapped/ready and 502 when SkillTree token exchange fails (tested via real handler + httpserver).
- [x] ISC-90: CORS reflects only the dashboard/SkillTree origins; a foreign Origin gets no Access-Control-Allow-Origin header (tested).
- [x] ISC-91: Dashboard served with `--local-auth` reports `authenticatorConfigured: true` and the official SkillTree learner display mounts in a real browser (live probe: /api/config + browser snapshot).
- [x] ISC-92: `ruff check`, `ruff format --check`, `mypy src/` remain clean after all additions (Bash probe).
- [x] ISC-93: ISA + tasks.yaml + README/docs carry post-additions ground-truth counts; no current-status claim of "200 passed / 99.30%" survives outside clearly-historical notes (grep probe).
- [x] ISC-94: R12 tracked-artifact discipline — project committed to the sidecar repo (pathspec-isolated from co-actor churn); `git ls-files` returns the project's source files; no secrets/outputs/caches tracked (Bash probe). VERIFIED: pass-5 commit 4210f783; isolation check (files outside `working/Active_Skillference/` in the commit) = empty; new `_ext_*.py` + `local_auth.py` in `git ls-files`; output/ + `.active_skillference_local/` confirmed git-ignored.
- [x] ISC-95: Cross-vendor audit of the new auth/dashboard surface — RedTeam (read-only) ran and surfaced 3 findings; the 2 actionable (DNS-rebind, cross-site issuance) were FIXED + regression-tested this session. Forge GPT-5.4 DEFERRED to ISC-99 (usage-limited until 18:31).
- [x] ISC-96: Advisor call logged against the final artifact set before `phase: complete` (VERIFY).

### Security hardening of the token bridge (RedTeam + Advisor convergence, 2026-06-10)
- [x] ISC-97: Token endpoint rejects DNS-rebinding — a foreign `Host` header gets 403 on every route (GET/POST/OPTIONS); legitimate `127.0.0.1`/`localhost` hostnames pass regardless of port (tested + live curl 403 vs 200).
- [x] ISC-98: Token endpoint rejects cross-site issuance — `Sec-Fetch-Site: cross-site` and a foreign `Origin` each get 403; same-origin and non-browser (no Sec-Fetch headers) callers still receive the learner token (tested + live curl).
- [x] ISC-99: Superseded by `asf-cross-vendor-security-audit` in `tasks.yaml`; the
  cross-vendor Forge/GPT-5.4 audit remains externally blocked and must be closed there
  with current dashboard/auth/full-stack evidence rather than by this historical ISC row.

### Curriculum vast-expansion (skills / subjects / edges) — pass #5 (2026-06-10)
- [x] ISC-100: Subject count grows substantially — `len(graph.subjects) >= 32` (was 24) with every new subject anchored to exactly one stratum (probe: build_curriculum stats). VERIFIED: 32 subjects.
- [x] ISC-101: Skill count grows substantially — `len(graph.skills) >= 180` (was 124) (probe: stats). VERIFIED: 208 skills.
- [x] ISC-102: Prerequisite-edge count grows substantially — `>= 330` edges (was 221) (probe: stats). VERIFIED: 398 edges.
- [x] ISC-103: The expanded graph is still a DAG — `validate()` passes (0 cycles, 0 dangling/duplicate prereqs, foundational-only roots, AND project-wide unique skill names) (probe: build_curriculum runs clean).
- [x] ISC-104: Still connected foundations→applications — `is_connected_foundations_to_applications()` True (probe: build_curriculum exit 0).
- [x] ISC-105: Every new skill has a non-empty objective AND ≥1 failable assessment question (probe: existing test_curriculum invariant over all skills stays green — 283 passed).
- [x] ISC-106: All 8 strata still populated; new subjects deepen multiple strata, not just one (probe: per-stratum counts — math 33, prob 19, info 24, varmeth 15, fep 9, ai 44, comp 27, app 37; ≥4 strata gained skills).
- [x] ISC-107: Anti: no NEW hand-typed result number — every `{{claim:NAME}}` token in new content resolves to one of the 22 registered claims; provenance linter + `run_kernels.py` exit 0 (Bash probe).
- [x] ISC-108: Authoritative gate stays GREEN after expansion — `pytest --cov=src --cov-fail-under=90` passes; ruff + mypy clean (re-run + quote). VERIFIED: 283 passed / 98.63%.
- [x] ISC-109: Live SkillTree re-seed reflects the larger graph — export + live admin/learner API report the new skill/subject/dependency counts equal to the export (live curl probe). VERIFIED: admin 208/32, dep graph 208/398, learner 208/32. A real defect (name collision) was caught here and fixed before close.
- [x] ISC-110: Count call-sites swept (R14) — docs (output_inventory, forking_guide, troubleshooting, README, quickstart, AGENTS, agent_instructions), manuscript SYNTAX, src/vendor READMEs, root metadata, tasks.yaml, and build stats all carry the new ground-truth counts; 0 stale "124 skills / 24 subjects / 221 edges" as current claims (grep probe — independently re-verified clean).
- [x] ISC-111: Anti: a duplicate skill display NAME (distinct ids, same name) silently corrupts the live re-seed — `CurriculumGraph.validate()._check_unique_names()` raises at build time, with a fail-closed regression test (`test_duplicate_name_raises`). VERIFIED: test passes; build_curriculum clean with the check active.
- [x] ISC-112: Anti: the FULL swallow-corruption class is closed, not just the skill-name instance (Forge HUNT 2) — `_check_subject_identity()` also rejects duplicate subject ids, duplicate subject NAMES (subjects route through the same idempotent swallow path), and skill/subject id-namespace collisions (SkillTree's shared Skill/SkillsGroup/Badge namespace), each with a fail-closed regression test. VERIFIED: 3 new tests pass; real 208/32 graph still validates clean. (Quiz names derive from skill names → transitively covered by ISC-111.)
- [x] ISC-114: Anti: a silently-swallowed create (any future server-side rejection the local model does not mirror) corrupts the live instance undetected — `verify_seed_landed()` runs post-seed in `ensure_local_skilltree_auth`, queries live `numSkills`, and raises if it is below the export count; 4 fail-closed httpserver tests (live_skill_count flat/wrapped/missing + verify pass/shortfall) + the full-bootstrap test serves the live count. VERIFIED in pass #5: 290 tests pass; live bootstrap exit 0 with the check active (live 208 == export 208). Current pass #6 re-verifies the same guard at 248 skills via ISC-119. Process-layer belt-and-suspenders beyond the validator's denylist (Advisor root-cause point).
- [x] ISC-113: Superseded by `asf-cross-vendor-security-audit` in `tasks.yaml`; the
  genuine cross-vendor verdict was not obtained in this historical pass and is not
  represented as a pass.

### Frontier-topic expansion and local Docker closure — pass #6 (2026-06-12)
- [x] ISC-115: Frontier topics improve every stratum, not just the application canopy — exactly 8 `sub_frontier_*` subjects exist, one per `ALL_STRATA`, each with 5 skills and at least one assessment (probe: `test_frontier_topic_subjects_cover_every_stratum`).
- [x] ISC-116: The current curriculum graph is internally valid and strictly larger than pass #5 — `build_curriculum.py` reports 248 skills / 40 subjects / 478 prerequisite edges, 8/8 strata, max depth 36, connected=True.
- [x] ISC-117: The current SkillTree export matches the graph — `skilltree_project.json` has 40 subjects, 248 skills, 478 dependencies, and 248 quizzes after the fail-closed provenance render.
- [x] ISC-118: Provenance remains source-bound after the expansion — `run_kernels.py` and `z_generate_manuscript_variables.py` register 22 claims; the rendered manuscript variables carry `skill_count=248`, `subject_count=40`, `edge_count=478`, `max_depth=36`.
- [x] ISC-119: Local Docker SkillTree seed is current — after backing up and resetting the stale generated SkillTree volume, `./scripts/run_skilltree.sh` completed via local FORM bootstrap with seed summary 40 subjects / 248 skills / 248 quizzes / 478 dependencies, `tokenVerified=true`, and `live_skill_count=248`.
- [x] ISC-120: `run_skilltree.sh` is truthful for local usage — local FORM bootstrap is the default when no `SKILLTREE_TOKEN` is supplied; explicit token mode now requires `ACTIVE_SKILLFERENCE_LOCAL_AUTH=0 SKILLTREE_TOKEN=...`; Docker readiness wait defaults to 240 attempts for slow arm64/Colima starts.
- [x] ISC-121: Rendered outputs are current — template render via `../template/scripts/03_render_pdf.py --project Active_Skillference` regenerated combined PDF/HTML/DOCX/EPUB and 9 slide PDFs; PDF text and rendered HTML show 248/40/478/max depth 36 with no old 208/398 count hits.
- [x] ISC-122: Local release readiness remains local-only — DOI reservation, public repository target, and Crossref reference checks remain external publication prerequisites, not local validation claims.

### Iteration 6 — RedTeam gate-hardening + content expansion (2026-06-16)
Each fix carries a negative-control test that FIRES on an injected same-class defect (anti-vacuity, per the prior-bug fingerprint).
- [x] ISC-123: `provenance.binding.render` fails closed on malformed claim tokens with interior whitespace (`{{ claim:e }}`, `{{claim: e}}`); negative-control test injects each variant and asserts `ProvenanceError`. [evidence: ISC-123 below]
- [x] ISC-124: `claim_support` rejects a `computed` claim declared with empty `claim_tokens` (was vacuously consistent); negative-control test asserts the issue fires.
- [x] ISC-125: `claim_support` runs unbacked-number detection on `computed`/`simulation` prose so a bare result number with no `{{claim}}` backing is rejected; negative-control test fires.
- [x] ISC-126: `quality` detects off-domain distractors by extended semantic class (compute/infra/web/finance), not only the prior list; negative-control injects a never-listed off-domain distractor and the gate fires; real corpus stays green (gate also caught a REAL existing `browser cache` distractor → fixed in `_ext_frontier_topics`).
- [x] ISC-127: REFRAMED — finding #4 (lower `MAX_MC_INDEX_CORRECT_SHARE`) REJECTED: per-index 50% is the *ideal* for 2-of-4 selection (marginal≠joint). Verified battery: best constant MC-set clears 16.8% (cap 30%), best SingleChoice fixed-position 29.6% ≈ chance. Gate already sound; no change. [see Decisions]
- [x] ISC-128: `scholarship.coverage.role_is_claim_specific` no longer counts lane-NAME tokens toward the keyword floor (curated keywords only); negative-control role built only from lane-name words returns False; real 74-source matrix still passes.
- [x] ISC-129: manuscript variable validator uses word-boundary matching `(?:{noun})\b` so `601 skilled` no longer false-matches the `skill` count pattern.
- [x] ISC-130: `kernels.cross_entropy` accepts a non-normalized non-negative `q` (e.g. a likelihood column `A[obs,:]`), keeping `p` strict; kernel suite green (42 passed) and `_as_nonneg_vector` added.
- [x] ISC-131: identity-only kernel tests gain specific numeric assertions vs an INDEPENDENT computation (KL=0.3680642, MI vs independent double-sum, epistemic=ln2, cross_entropy non-normalized q) so they verify computation, not a tautology.
- [x] ISC-132: New `quality.audit_semantic_prerequisites` gate flags a skill assessed on a concept (KL/Markov/Laplace/ELBO) without the defining skill in its transitive prerequisites; negative-control fires on injection and clears when fixed; real graph passes; non-vacuity guard test asserts every concept has live scan teeth (caught + removed dead 'Taylor').
- [x] ISC-133: DAG prerequisite fixes land — entropy→KL→cross-entropy reorder (was reversed); `vm_elbo` +it_kl; continuous-Laplace skill +vm_laplace; `build_curriculum()` valid + acyclic (610/107/1159).
- [x] ISC-134: Course-material validation gains online pointer-existence verification (env-overridable GitHub API base, httpserver-tested, no mocks); negative-control with a missing pinned path fires `pointer-path`.
- [x] ISC-135: REVISED to 2 pedagogically-sound subjects (message-passing 5 skills + precision/exploration 4 skills = 9 skills) — honest scope; all pass DAG/quality/provenance/semantic-prereq gates; counts 601→610 skills, 105→107 subjects.
- [x] ISC-136: `plot_semantic_prerequisite_coverage` figure registered (caption/alt-text/semantics), declared in `03_results.md`, added to dashboard artifacts; artifact audit passes; figure_count 16→17 re-synced.
- [x] ISC-137: `tasks.yaml`/`TODO.md` regenerated with 3 iteration-6 milestones; all live counts re-synced (0 stale literals); roadmap + live-count validators pass.
- [x] ISC-138: Full suite green at ≥90% coverage (592 passed, 92.94%); +~20 net new tests; `ruff` + `mypy` clean on changed files.
- [x] ISC-139: Anti: no scope pivot (all work in Active_Skillference); every `[x]` cites a quoted artifact token below.
- [x] ISC-140: Superseded by `asf-cross-vendor-security-audit` in `tasks.yaml`; same-vendor
  Advisor findings from this pass were resolved, but the independent Forge/GPT-5.4
  signal remains an external blocker in the active roadmap.

### Iteration 6b — triple-check (regression + residual vacuity) + depth (2026-06-16)
A 2nd 7-specialist adversarial workflow (60 findings / 13 verified / 3 prior fixes re-confirmed correct) re-attacked iteration-6 and swept un-audited facets.
- [x] ISC-141: Provenance strips Unicode format chars (category Cf: zero-width space/joiner, BOM) before every integrity scan — closes the CRITICAL bypass where `{{<ZWSP>claim:e}}` reached learner text and `1<ZWSP>.6094` evaded the number linter (neither `\s` nor `\b` match Cf); negative-control parametrized over 5 Cf chars asserts the security property (registered→resolves clean; unregistered/empty→fail closed).
- [x] ISC-142: Dashboard course-material loaders fail CLOSED — a valid-JSON-but-shapeless artifact now returns `available=False`+error instead of `available=True` with a silently-empty payload; negative-control injects `{version:1}` and asserts unavailable.
- [x] ISC-143: Semantic-prereq concept patterns tolerate plural forms (`\bKLs?\b`, `\bELBOs?\b`); non-vacuity guard still passes.
- [x] ISC-144: Two more subjects — `sub_model_reduction` (VM) + `sub_continuous_time_aif` (AI) → 617 skills / 109 subjects / 1172 edges; all gates pass.
- [x] ISC-145: README + methodology + testing-philosophy docs describe the semantic-prerequisite gate; all live counts re-synced (0 stale).
- [x] ISC-146: Full suite green at ≥90% after triple-check fixes + content; ruff + mypy clean (64 source files).

### Iteration 6c — convergence (quiz-gating + fail-closed auth + content) (2026-06-16)
A 3rd convergence workflow (37 findings / 12 verified; keyword + docker-comment findings ruled acceptable cosmetic = convergence signal).
- [x] ISC-147: `SkillTreeProject` validates quiz gating project-wide — a Quiz-typed skill must carry a `quiz_id` that maps to a real quiz; no dangling refs; no orphan quizzes; 3 firing negative-controls (the gate also surfaced latent orphan-quiz test fixtures, now fixed).
- [x] ISC-148: `exchange_trusted_client_token` fails CLOSED — empty/token-less HTTP 200 now raises instead of returning `{}` and letting the caller set `token_verified=True` with no token; httpserver negative-controls for empty body + missing access_token + a positive control.
- [x] ISC-149: `verify_seed_landed` checks subjects as well as skills (a dropped subject whose skills are still summed no longer passes); subject-shortfall negative-control fires.
- [x] ISC-150: rate-distortion↔EFE bridging skill added (`pex_rate_distortion_efe`) → 618 skills / 109 subjects / 1175 edges; all gates pass; counts re-synced (0 stale).
- [x] ISC-151: Full suite green at ≥90% after convergence fixes; ruff + mypy clean (64 source files).

### Iteration 6d — no-Forge post-convergence hardening + regression verdict (2026-06-17)
- [x] ISC-152: `quiz_question_count` rejects a negative `numQuestions` (was propagated verbatim); negative-control `quiz_question_count({"numQuestions": -5}) == 0`.
- [x] ISC-153: `_parse_secret_response` returns `""` for structured-JSON-without-clientSecret (was laundering the raw JSON blob as a credential); plain-text path confirmed intended; negative-controls for dict/list-without-secret.
- [x] ISC-154: last orphan kernel claim resolved — `agent_preferred_action` now referenced in `comp_agent_loop` (all 22 kernel claims shown to learners; `evidence_probability_positive` confirmed used in the manuscript supplement, not an orphan).
- [x] ISC-155: REGRESSION VERDICT — a 4th workflow (regression-verification, mutation-testing every session fix) reports all 4 clusters HOLD=true and ZERO new real defects; answer-balance battery confirms every knowledge-free strategy at chance; 608 tests green serially, ruff+mypy clean (64 files), 0 stale counts. CONVERGED.

## Test Strategy

| isc | type | check | threshold | tool |
|-----|------|-------|-----------|------|
| 1-15 | unit | kernel numeric identities | exact within 1e-9 / behavioral | pytest |
| 16-25 | unit | graph structure invariants | exact | pytest |
| 26-31 | unit | provenance round-trip + fail-closed | exact | pytest |
| 32-40 | contract | SkillTree schema + REST paths | exact request match | pytest-httpserver |
| 41-44 | file/deferred | vendor wiring present; live run deferred | exists / DEFERRED | Read/Bash |
| 45-48 | gate | coverage/lint/type | ≥90% / 0 errors | pytest-cov, ruff, mypy |
| 49-56 | smoke/grep | scripts run; domain migrated | exit 0 / no residue | Bash/Grep |
| 57-58 | cross-vendor/advisor | audit + advisor | no CRITICAL / logged | Agent, Inference.ts |

## Features

| name | satisfies | depends_on | parallelizable |
|------|-----------|------------|----------------|
| kernels | ISC-1..15 | — | yes (Forge) |
| curriculum-graph | ISC-16..25 | kernels(claims) | partly |
| provenance | ISC-26..31 | kernels, curriculum | no (integration seam) |
| skilltree | ISC-32..40 | curriculum | yes (Engineer) |
| vendor-runtime | ISC-41..44 | skilltree | yes |
| pipeline-manuscript | ISC-45..56 | all | no |
| verify | ISC-57..58 | all | no |

## Decisions

- 2026-06-16 (6c convergence, Advisor split): quiz-gating is asymmetric — dangling-ref and missing-quizId are UNIVERSAL defects (hard error in the generic `SkillTreeProject.__post_init__`), but orphan-quiz rejection is too strict for a reusable model (an unused quiz pool is a valid authoring pattern: staged/dynamic/deprecated). Orphan detection moved to a query `orphan_quiz_ids()`; the project-specific `export_project` enforces this curriculum's strict 1:1 invariant. This also fixed 3 seeder tests the hard version had regressed. Token fail-closed verified false-positive-safe: an empty/token-less body is never a valid OAuth response, and the negative-controls use pytest-httpserver (the REAL urllib path, not a mock), so they exercise the integration seam where the bug lived. Keyword-set inconsistency confirmed convergence (grep: no functional consumer in src/ or scripts/ — Zenodo/codemeta metadata only).
- 2026-06-16 (iteration 6, RedTeam hardening): An 8-specialist adversarial gate-vacuity workflow (47 findings / 31 verified-real) drove this iteration. Every fix carries a negative-control test that fires on injection (anti-vacuity, per the prior-bug fingerprint).
- 2026-06-16: REJECTED finding #4 (lower `MAX_MC_INDEX_CORRECT_SHARE` below 0.50). FirstPrinciples + prior gotcha: per-index 50% is the IDEAL marginal for 2-of-4 multiple-select; the gameability bound is the JOINT correct-set share, which is enforced at `MAX_MC_CORRECT_SET_SHARE=0.30` and measured at 16.8% (best constant-set strategy) — well under cap. SingleChoice best fixed-position is 29.6% ≈ chance (the engineered fixed point). Lowering the per-index threshold would reject the ideal distribution. Advisor concurred.
- 2026-06-16: `kernels.cross_entropy` q-relaxation is SCOPED to the candidate arg only. `p` (the reference/posterior position) is still strictly normalized via `_as_probability_vector`; only `q` (the candidate, e.g. a likelihood column `A[obs,:]`) uses `_as_nonneg_vector`. `kl_divergence` is UNCHANGED (KL needs a normalized q to be a proper divergence). Verified VFE accuracy does NOT call `cross_entropy` (grep clean) so there is zero VFE impact; added `test_cross_entropy_rejects_unnormalized_p` so the posterior-position guard can never silently relax. (Advisor flagged this as the one to scope; it is scoped.)
- 2026-06-16: Semantic-prerequisite gate scoping is BY DESIGN: it checks the actual transitive prerequisite DAG (not stratum order) and only EXEMPTS later-stratum definers (forward references the DAG legitimately cannot make backward edges to). Same-stratum inversions ARE caught via the closure check (proven: it_cross_entropy→it_kl, same IT stratum). The claim is scoped to "assessed on", not full-DAG exposition — manuscript/figure text says "assessed on" deliberately. Advisor's empty-scan-vacuity point is closed by `test_semantic_prereq_concept_map_is_non_vacuous` (every concept must have ≥1 live assessment match — this caught and removed the dead 'Taylor' concept).
- 2026-06-09: User chose vendored-runnable + maximal-enumeration + full-provenance-binding (AskUserQuestion, the E5 pre-build interview).
- 2026-06-09: Docker absent → live SkillTree JVM seed was deferred; REST contract verified via pytest-httpserver mirror instead (honest probe substitution).
- 2026-06-09: ISC floor — E5 soft floor is ≥256; prioritizing granular, real ISCs (58 atomic probes) over padding to 256 with junk (Bitter Pill). Show-my-math: the natural granular N for v1's verifiable surface is ~58; density grows by adding curriculum data, not ISC ceremony. Logged as soft-floor underrun with justification.
- 2026-06-09: Strip template optimization domain entirely; keep `project_paths.py`/`_runtime.py` glue + manuscript/render conventions; rewrite scripts + tests.
- 2026-06-09 (review pass): R8/R10 GENERATOR-PREEXEC ran the authoritative gate at OBSERVE. Ground truth ≠ ISA's stale `23/58`: **166 passed, 2 FAILED, coverage 98.26%**. Real defects: (1) `tests/test_kernels_examples.py` stale — `agent_example()` was refactored resolve/stay→sample/commit (+`agent_preferred_action`, now 20 claims) and the catalog already uses the new names (`test_catalog_tokens_all_resolve` passes), but this test still asserts `len==19` and references `agent_g_resolve`/`agent_g_stay`; the TEST is stale, source is the intended version. (2) `ruff format --check` reformats `src/provenance/binding.py` → ISC-47 red. Verified-green facts: 124 skills/8 strata (ISC-20/21), 3 figures (ISC-54), no real mocks (ISC-46), no residue in numbered manuscript sections (ISC-52), mypy clean (ISC-48), ruff check clean.
- 2026-06-09 (review pass): R15 — monorepo working tree shows heavy co-actor churn (BTC_Buffalo deletions, AGEINT, CLAUDE.md) ALL outside Active_Skillference; this project is untracked local-only in the sidecar. Working in own stable layer; spawned auditors get read-only.
- 2026-06-09 (review pass): R4 failure-fingerprint MATCH — `2026-06-03-155609` is this exact prompt shape ("Comprehensively proceed with /workflows and all improvements/additions") where the prior response gave status updates instead of delivered work + truncated. FeedbackMemoryConsult invoked; Anti-ISC-60/61 added; deliver-not-report is binding.
- 2026-06-09 (#2 docs/metadata accuracy pass): root cause of this pass — docs/, manuscript meta, scripts/src/tests/data meta, and root metadata were all UNREBASED copies of `template_code_project` (a gradient-descent optimization exemplar). Rebased every surface to the real AIF identity. Decision: DOIs left BLANK (not reserved) — two unminted template DOIs (10.5281/zenodo.20417136 cover-page + .20420368) were carried as if real; for an unpublished local-only project a blank DOI is the honest state (reserve-DOI-first at publication). AIF references provided WITHOUT DOIs (advisor-confirmed defensible; Crossref-verify at publication — noted in references.bib).
- 2026-06-09 (#2): R15 — a convergent codex co-actor (`codex/working-doc-refresh`) was concurrently rendering this project (added `scripts/z_generate_manuscript_variables.py`, re-rendered to PDF/slides/web/docx/epub, rewrote scripts/README.md, touched style_guide.md). Treated as a convergent ally: verified-then-corrected against its deltas, kept spawned auditors read-only, re-probed disk at each phase, reconciled z_generate into the script inventories. Its full render gave real render proof (citations resolved, 0 bbl warnings). Its `scripts/README.md` was kept (better than the delegated draft — it already documented z_generate).
- 2026-06-09 (#2): delegation gap caught by the FINAL full-project residue grep (R14 call-site sweep) — the 3 folder-scoped audit agents covered docs/manuscript/scripts/src but MISSED tests/ meta + data/ meta + the second cover-page DOI in manuscript/config.yaml + config.yaml.example. Lesson: a whole-tree grep after delegated fan-out is mandatory; folder-scoped agents inherit folder-scoped blind spots.

- 2026-06-10 (pass #5): the live re-seed — NOT the green suite, NOT the export — caught a real defect (duplicate skill display name → silently-swallowed creation → dangling prereq 404). Fixed instance (rename `hier_generative_models` → "Deep Hierarchical Generative Models") + class (`validate()._check_unique_names`). This is the canonical R8/Live-Probe lesson: a green build + a self-consistent export are blind to a constraint that lives only in the downstream service; only a live seed is the oracle for the model↔target seam.
- 2026-06-10 (pass #5): Forge cross-vendor (GPT-5.4) lane was usage-limited. Per
  Rule 2a, a usage-limit/no-signal was NOT a pass and was NOT faked; the active
  follow-up now lives in `asf-cross-vendor-security-audit`. Forge's same-family
  findings WERE consumed: HUNT 2 ("the class fix only closed half the class" —
  subject/quiz names route through the same swallow) → fixed via ISC-112
  `_check_subject_identity`.
- 2026-06-10 (pass #5): Advisor (Rule 2, E5-mandatory) disposition — (a) "don't stamp `phase:complete` while your own scheduled cross-vendor lane is DEFERRED" → HONORED: phase stays `verify`, the single outstanding item (Forge re-dispatch) is explicit in ISC-113 + the commit body. (b) "the edge layer (acyclicity + referential integrity) is the unclosed half" → already enforced (`_check_acyclic` 3-colour DFS, `_check_prerequisites_exist`, `_check_no_self_loops`, `_check_no_duplicate_prerequisites`) and verified green on the 208/398 graph; the advisor lacked the full graph.py. (c) "the swallow itself is the root cause — fail-closed on non-idempotent rejections" → ADDRESSED at the process layer: `verify_seed_landed()` now runs post-seed in `ensure_local_skilltree_auth`, querying live `numSkills` and failing loud if it is below the export — catching ANY silently-dropped create (including future unknown server constraints), not only the validator-enumerated ones. (d) "confirm id-namespace disjointness is server-mirrored not invented" → confirmed: the live error `types [[Skill, SkillsGroup, Badge]]` proves the shared lookup namespace; documented as server-mirrored.

## FirstPrinciples — verdicts on the four integrity principles (2026-06-09)

Deconstructed each principle to its bedrock testable mechanism; classified and tested.

1. **Provenance over assertion.** *Bedrock:* a learner-facing number is valid iff a tested
   kernel emitted it. *Challenge:* the linter only scanned `name`+`description` — a real
   gap. *Reconstruct:* extended scanning to `objective` + assessment `prompt` + scientific
   notation; answer **options** kept out of scope BY DESIGN (distractors are intentionally
   arbitrary numbers) and that rationale is now documented + tested. Manuscript prose is now
   a first-class provenance surface (`validate_manuscript_dir`, wired into `run_kernels.py`).
   **Verdict: HOLDS, materially strengthened.** Real curriculum lints clean (0 violations)
   under the stricter linter across all expository fields.
2. **The graph is the truth.** *Bedrock:* prerequisite structure is a validated DAG; a cycle
   or dangling edge is a build failure. *Challenge:* `is_connected_foundations_to_applications`
   seeded BFS from ANY root, making it tautologically true for any acyclic graph — the name
   overpromised. *Reconstruct:* seed only from FOUNDATIONAL roots, so an app tracing back to a
   non-foundational orphan is genuinely flagged. **Verdict: HOLDS, made honest.** Real graph:
   124/124 reachable from 2 foundational roots; cycle/dangling/self-loop detection sound
   (RedTeam: 0 defects across ~45 attacks).
3. **Falsifiability (Science).** *Bedrock:* every skill carries a failable assessment.
   *Challenge:* is the agent's epistemic preference a law or an artifact? *Reconstruct:* see
   Science finding below — it is regime-dependent; the curriculum must not over-claim, and now
   has tests pinning both the holds-regime and the breaks-regime. **Verdict: HOLDS, sharpened.**
4. **Substrate independence (Deutsch reach).** *Bedrock:* one kernel definition, reused, never
   re-typed. *Challenge:* could a value drift between kernel, claim, skill, figure, manuscript?
   *Reconstruct:* the dead-token defect (manuscript referenced renamed claims) proved the
   manuscript was an UN-gated surface; now gated. **Verdict: HOLDS, the last leak sealed.**

## Changelog

- conjectured: the suite was green at `phase: build` (ISA self-reported 23/58).
  refuted_by: R8 GENERATOR-PREEXEC — `pytest` returned 166 passed / **2 failed** / 98.26%.
  learned: ISA self-report is not ground truth; the authoritative gate is. A kernel refactor
  (resolve/stay→sample/commit, +1 claim) left `test_kernels_examples.py` AND `03_results.md`
  stale; the catalog test passed because the catalog was updated but the manuscript was not.
  criterion_now: ISC-59 (gate must be re-run + quoted) + ISC-31-adjacent manuscript gate.
- conjectured: provenance gate fully covers learner-facing numbers.
  refuted_by: RedTeam — `objective`, assessment `prompt`, scientific notation, and ALL manuscript
  prose were unscanned; an unbacked manuscript token rendered literally into the PDF undetected.
  learned: a provenance gate is only as strong as the set of surfaces it scans; enumerate every
  learner-facing free-text field explicitly.
  criterion_now: linter scans name/objective/description/prompt + sci-notation; manuscript
  validated dir-wide and wired into the build; answer-options exclusion documented as deliberate.
- conjectured: the active-inference agent always prefers the information-seeking action.
  refuted_by: Science sweep — at sensor precision p≥0.95 the epistemic advantage vanishes then
  inverts (prefers commit at p=0.99). The worked example (p=0.9) sits in the robust regime.
  learned: the epistemic-preference result is regime-dependent, not a universal law; honest
  curricula characterize the regime rather than over-generalize.
  criterion_now: ISC-64 + two regime tests (holds at p∈[0.6,0.9]; breaks at p=0.99).
- conjectured: the prior E5 run delivered an accurate, self-contained project — code, ISA, and tests were hardened, so the surrounding docs/manuscript/metadata were assumed to match.
  refuted_by: this pass — the ENTIRE docs/ folder, manuscript meta (AGENTS/README/SYNTAX/references.bib), scripts/src/tests/data meta, and ALL root metadata (codemeta/CITATION/.zenodo/domain_profile/experiment_plan/config.yaml/config.yaml.example) were verbatim `template_code_project` optimization residue, including a fabricated cover-page Zenodo DOI and a "Journal of Optimization Methods" attribution.
  learned: hardening the code + ISA + tests does NOT propagate to the documentation/metadata surface; a green test suite is blind to a manuscript that cites the wrong domain or a metadata file that claims a different project's DOI. Documentation accuracy needs its own verifier-first pass with a whole-tree residue grep and a cross-vendor audit — the test oracle is honesty-blind to prose and metadata.
  criterion_now: ISC-65..80 (metadata identity, DOI honesty, version unity, count accuracy, per-surface residue, link resolution, render-path accuracy, cited-bib integrity, gate-stays-green).

- conjectured: the local SkillTree trusted-client bridge was secure because the client
  secret never reaches the browser (verified across config + token paths).
  refuted_by: RedTeam read-only pass — the secret stays home, but the endpoint that MINTS
  learner tokens from it had no caller authentication: foreign Host (DNS-rebind), cross-site
  fetch, and foreign Origin all received a valid 12h bearer token (live curl, all 200).
  Coverage at 99% on local_auth measured happy-path execution, not bad-input rejection — the
  Advisor independently flagged the same coverage≠correctness gap.
  learned: secret custody and credential-issuance are separate trust boundaries; a token
  bridge needs its own caller gate (Host pinning + Sec-Fetch-Site/Origin) and NEGATIVE tests,
  because a passing coverage number actively hides a missing-rejection bypass. Cross-vendor /
  adversarial review caught what same-vendor green coverage did not.
  criterion_now: ISC-97 (Host pinning anti-rebind), ISC-98 (cross-site/foreign-Origin gate),
  each with a fail-closed negative regression test + live A/B.

- conjectured: the curriculum vast-expansion (124→208 skills) was complete once the export
  succeeded, the DAG validated, and the green suite (282) passed — so the live re-seed would
  be a mechanical replay.
  refuted_by: the LIVE re-seed (not the green suite, not the export) — it died assigning a
  prerequisite with `Failed to find skillId [hier_generative_models]`. Root cause: two skills
  carried the identical display name "Hierarchical Generative Models" (existing `ai_hierarchical`
  + new `hier_generative_models`). SkillTree enforces project-wide unique skill NAMES; the
  idempotent local re-seed's `request_json_allowing_existing` swallowed the duplicate-name 400 as
  a phantom "already exists", so the new skill was silently never created and its prerequisite
  edge later 404'd. The graph validator pinned unique skill IDS but not unique NAMES, and the
  export was internally consistent (all 398 dep endpoints present), so neither the build gate nor
  the export caught it — only a real live seed did.
  learned: an idempotent "create-or-skip" writer turns a uniqueness violation the local model
  does not enforce into SILENT data loss, not a loud error; the live target's constraint set is
  authoritative and must be mirrored as a build-time invariant. A green suite + a consistent
  export are blind to a constraint that lives only in the downstream service. Live verification
  is not a formality after a green build — it is the only oracle for the seam between the model
  and the real target.
  criterion_now: instance fix (rename to "Deep Hierarchical Generative Models") + ISC-111
  (`_check_unique_names()` in `validate()` + `test_duplicate_name_raises` fail-closed regression).

## Verification

- ISC-59: `pytest tests/ --cov=src --cov-fail-under=90` → "190 passed", "Total coverage: 99.28%".
- ISC-1..15 (kernels): green via test_kernels_*; Forge + RedTeam kernel-numerics vector: 0 defects,
  VFE/EFE/ELBO/policy identities verified; H3 bound-tightness 8.88e-16 over 200 random models.
- ISC-16..25 (graph): pass #5 ground truth was "208 skills / 32 subjects / 398 edges / 8/8
  strata / max depth 33 / connected=True" (expanded from the original 124/24/221/depth-28).
  Current pass #6 ground truth is "248 skills / 40 subjects / 478 edges / 8/8 strata /
  max depth 36 / connected=True"; RedTeam dag-validation: 0 defects; validator also enforces
  unique skill names, unique subject ids+names, and skill/subject id-namespace disjointness
  (ISC-111/112).
- ISC-26..31 (provenance): binding.py 100% cover; fail-closed export + manuscript gate tested;
  linter hardened (objective/prompt/sci-notation); real curriculum lints clean (0 violations).
- ISC-32..40 (skilltree): exporter/client/seeder green; paths verified vs SkillTree v4.4.2;
  skillId identifier validation added (path-injection defense); empty project_id/base_url rejected.
- ISC-44: CLOSED 2026-06-10 (was deferred) — Docker became available; live seed verified
  end-to-end via the trusted-client bridge. Evidence under "Comprehensive pass #4 verification".
- ISC-45..56: coverage 99.28%≥90; 0 mocks; ruff check+format clean; mypy clean; 3 figures emitted;
  no dead manuscript tokens; no optimization-domain residue in numbered sections.
- ISC-59..64: review-pass anti-criteria + RedTeam/FirstPrinciples/Science all executed and recorded.
- ISC-57 (Forge cross-vendor, GPT-5.4, read-only): returned **CONCERNS (2 HIGH, 2 MEDIUM, 1 LOW),
  no CRITICAL** — the green suite AND the Advisor had both missed the HIGHs (the exact value of the
  cross-vendor gate). Independently CONFIRMED holding: VFE bound tight (gap=0.0); EFE epistemic term
  == mutual information EXACTLY (epi−MI=1.67e-16); claim-conflict not collapsing 6-decimal values;
  foundational-roots connectivity fix correct (`{"reachable":["p"],"connected":false}`); DAG sound.
  **All concerns RESOLVED this session (each reproduced via negative control + a regression test;
  192→200 tests):**
  - HIGH-1 (provenance enforced on only 1 of 6 learner-facing fields): `Skill.claim_tokens()` now
    scans name+objective+description+assessment prompts+answers; `render_graph` renders ALL those
    plus `subject.description`; export uses the rendered graph → a token anywhere fails closed.
  - HIGH-2 (not fail-closed on malformed tokens): `render()` now raises on any residual `{{claim:`
    after substitution (`{{claim:}}`, nested) instead of emitting it literally.
  - MEDIUM (invalid likelihood silently finite): `_validate_model` now rejects negative entries and
    non-normalized columns (was shape/index only).
  - MEDIUM (linter scope) + LOW (agent prose): single-decimal + answer-option exclusions documented
    as deliberate scope; agent prose carries the regime caveat; Science tests pin both regimes.
- ISC-58 (Advisor, Inference.ts): logged. Substantive demands all satisfied with negative controls:
  connectivity has a real failing negative control + fails-closed on empty foundational roots;
  answer-option exclusion is a TYPED-FIELD exclusion (not a prose heuristic) with prompt still
  scanned; `or True` replaced with an assertion that can fail; build-level fail-closed A/B proven
  (dead manuscript token → `run_kernels.py` exit 1; clean → exit 0); skillId rejects ../, null-byte,
  unicode confusable, dotted, spaced, leading-digit/underscore ids. (The advisor's "project-identity
  mismatch" was an `--auto-state` artifact loading a different project's work.json, not this ISA.)

### Comprehensive pass #4 verification (2026-06-10)
- ISC-82..85,92: `pytest tests/ --cov=src` → "282 passed", "Total coverage: 98.24%→98.60%"; per-module `src/skilltree/local_auth.py 99.14%`, `src/dashboard/server.py 97.25%`, `src/dashboard/status.py 100.00%`. ruff check "All checks passed!", ruff format "58 files already formatted", mypy "Success: no issues found in 28 source files". 0 mocks (no MagicMock/patch in tests/).
- ISC-86: `test_state_file_is_owner_only_and_dir_private` asserts `dir_mode == 0o700` and `file_mode == 0o600` on the real saved state file.
- ISC-87: `test_describe_local_auth_branches_never_leak_secrets` + `test_dashboard_..._without_leaking_secret` assert the admin password and client secret appear in NONE of the public dicts / `/api/config` / `/api/status` bodies across all branches.
- ISC-89/90: token endpoint 503 (auth not ready / LocalSkillTreeAuthError) + 502 (SkillTreeClientError) and foreign-Origin-no-ACAO all tested via the real handler over httpserver.
- ISC-94: `git ls-files -- working/Active_Skillference | wc -l` → 122 source files; grep for `active_skillference_local|skilltree_auth` and `/output/|htmlcov` over the tracked set → both empty; pathspec-isolation confirmed (`git diff --cached --name-only` had 0 entries outside `working/Active_Skillference/`). Commit 247169b3.
- ISC-95/97/98 (RedTeam read-only cross-vendor): RedTeam reproduced a live token-issuance bypass (foreign Host → 200, cross-site → 200, foreign Origin readable via DNS-rebind). FIXED: added `_host_header_hostname`/`_allowed_hostnames` Host pinning (anti-rebind) + `_token_caller_allowed` Sec-Fetch-Site/Origin gate. Live A/B post-fix: `Host: attacker.example → 403`, `Sec-Fetch-Site: cross-site → 403`, `Origin: http://evil.example → 403`, legit same-origin → 200, non-browser CLI → 200. Official SkillTree display still mounts in real Chrome (iframe "Skills Display has loaded", "Achieved 0 out of 124 skills" progressbar, subject links resolve). RedTeam Finding 3 (log/pid 0644) → chmod 0600 (files are session-local, gitignored, no project code writes them).
- ISC-96 (Advisor): logged via `Inference.ts --mode advisor`. Advisor confirmed deferring Forge is acceptable for reversible internal work, demanded negative auth tests + a tracked-secret scan + honest reframing ("equal to export" = seed↔API consistency, not ground-truth validation; "mounts" → assert rendered nodes). All four same-vendor checks done: negative auth tests added (ISC-97/98), `git ls-files` secret-scan clean (ISC-94), the live snapshot asserts rendered skill nodes + progressbar (not just page load), and the claim wording is reframed here.

### Comprehensive pass #4 verification — superseded counts note
> Earlier in this pass the suite measured 274 passed / 98.57% (pre-security-fix). After the
> Host/cross-site gates + their negative tests the authoritative gate is **282 passed / 98.60%**
> (cov-fail-under=90 satisfied). The 274 figure is historical within this same session.

### Comprehensive pass #4 verification — (continued)
- ISC-81 (closes ISC-44): live probe via stored trusted-client creds — token exchange: `token keys: ['access_token', 'expires_in', 'token_type'] | token_type: Bearer | expires_in: 43199`; learner API: `LIVE summary: projectId=activeInference totalSkills=124 subjects=24 totalPoints=12400`; admin API: `ADMIN project: numSkills=124 numSubjects=24 name='Active Inference & the Free Energy Principle'`; dependency graph: `LIVE dependency graph: nodes=124 edges=221` — all equal to the export (124/24/221). Stack: `skilltree/skills-service:4.4.2 Up 10 hours` + `postgres:15 (healthy)` via docker ps.
- ISC-88: `git check-ignore -v` → `.gitignore:17:.active_skillference_local/  .active_skillference_local/skilltree_auth.json` (+ output/, htmlcov/, .venv/, .coverage, .mypy_cache, .ruff_cache, .pytest_cache, .benchmarks all matched ignore rules).
- ISC-91: dashboard restarted `--local-auth` (pid 19320); `/api/config` → `authenticatorConfigured: True`, `authenticator: http://127.0.0.1:8765/api/skilltree/token`, `localAuth ready: True`; real-Chrome snapshot shows `Iframe "SkillTree Skills Display"` → `"Skills Display has loaded"`, heading `ACTIVE INFERENCE & THE FREE ENERGY PRINCIPLE`, `0 / 12,400 Points`, runtime tiles `online / 124 / 24 / 221`.

### Curriculum vast-expansion verification — pass #5 (2026-06-10)
- ISC-100..104,106: `scripts/build_curriculum.py` → "curriculum valid: 208 skills / 32 subjects / 398 prerequisite edges", "strata present: 8/8 (all=True), max depth 33, connected foundations→applications=True"; per-stratum (`curriculum_stats.json`): math 33 / prob 19 / info 24 / varmeth 15 / fep 9 / ai 44 / comp 27 / app 37 (5 strata gained skills). Thresholds: 32≥32, 208≥180, 398≥330 — all met.
- ISC-105/108: `pytest tests/ --cov=src --cov-fail-under=90` → "286 passed", "Total coverage: 98.64%" (was 282; +1 unique-name test, +3 subject-identity tests); `ruff check` "All checks passed!", `ruff format --check` "54 files already formatted", `mypy src/` "Success: no issues found in 33 source files".
- ISC-107: `scripts/run_kernels.py` → "registered 22 provenance claims", exit 0 (fail-closed provenance gate passes; no new bare-number defect in the 84 new skills — independently confirmed by Forge HUNT 3: zero non-math hand-typed numbers across all five `_ext_*.py` modules).
- ISC-109: live re-seed via `scripts/bootstrap_local_skilltree.py` → seedSummary `{skills:208, subjects:32, dependencies:398, quizzes:208}`, `seeded:true`, `tokenVerified:true`. Live API ground-truth (admin session + trusted-client token): `ADMIN project: numSkills=208 numSubjects=32`; `ADMIN dependency graph: nodes=208 edges=398`; `LEARNER summary: totalSkills=208 subjects=32 totalPoints=20800` — all equal to the export. Real-Chrome (chrome-devtools-axi) at `http://127.0.0.1:8765`: runtime tiles "Skills 208 / Subjects 32 / Dependencies 398"; official SkillTree iframe progressbar "Achieved 0 out of 208 skills", "0 / 20,800 Points"; screenshot `/tmp/active_skillference_208_display.png` shows the expanded subject tiles rendering. (Interceptor CLI not installed on this host; chrome-devtools-axi is the sanctioned real-Chrome interface — localhost dashboard, no bot detection, CDP fingerprint irrelevant.)
- ISC-110: independent re-grep (R8, not the sweep agent's self-report) for `124 skill|24 subject|221 edge|221 dependenc|221 prerequisite|124 quiz|max depth 28|124/24|the 124 skills|124 nodes|12400 point` over *.md/*.yaml/*.json (excluding ISA.md/output/caches/tests) → empty. Sweep agent updated 21 literals across 15 files (codemeta/.zenodo/README/tasks.yaml/SYNTAX/docs×8/vendor/src×2).
- ISC-111: `test_duplicate_name_raises` passes (distinct ids "a"/"b", shared name "Shared Title" → `CurriculumError: duplicate skill name`); the live defect that motivated it: re-seed died with `POST .../hier_generative_models/prerequisite/... 400 "Failed to find skillId [hier_generative_models]"` because its name collided with `ai_hierarchical`; instance fix = rename to "Deep Hierarchical Generative Models".
- ISC-112 (Forge HUNT 2): `test_duplicate_subject_name_raises` / `test_duplicate_subject_id_raises` / `test_skill_subject_id_collision_raises` all pass; `_check_subject_identity()` active in `validate()`; real 208/32 graph still validates clean (Forge live check: zero dup subject names/ids, zero quiz collisions, zero skill/subject id overlap, max skillId len 31 / name len 65 within SkillTree caps).
- ISC-113 (Forge cross-vendor): codex GPT-5.4/reasoning=high lane returned "You've hit your usage limit … try again at 6:31 PM" (exit non-zero, empty output) — NO cross-vendor signal, NOT faked (Rule 2a). Forge's same-family findings: HUNT 1 (other swallow-class members — subject/quiz names — latent, now addressed by ISC-112), HUNT 2 (the half-closed class, FIXED), HUNT 3 (provenance CLEAN), HUNT 4 (token bridge no bypass; LOW note: Sec-Fetch-Site gate is browser-only by design — non-browser callers allowed, secret custody is the real boundary). Re-dispatch after 18:31 PT for the genuine GPT-5.4 verdict.

### Frontier-topic expansion + Docker verification — pass #6 (2026-06-12)
- ISC-115/116: `scripts/build_curriculum.py` → "curriculum valid: 248 skills / 40 subjects / 478 prerequisite edges", "strata present: 8/8 (all=True), max depth 36, connected foundations→applications=True"; per-stratum (`curriculum_stats.json`): math 38 / prob 24 / info 29 / varmeth 20 / fep 14 / ai 49 / comp 32 / app 42. `test_frontier_topic_subjects_cover_every_stratum` verifies the eight new `sub_frontier_*` subjects and five skills per subject.
- ISC-117/118: `scripts/run_kernels.py` and `scripts/z_generate_manuscript_variables.py` → "registered 22 provenance claims"; `scripts/export_skilltree.py` → "exported SkillTree project 'Active Inference & the Free Energy Principle' (248 skills, 478 dependencies)". JSON artifact probe: stats 248/40/478/max_depth 36/all_strata=True; export 40 subjects / 248 skills / 478 dependencies / 248 quizzes; figure registry lists `curriculum_dag.png`, `free_energy_descent.png`, `efe_decomposition.png`.
- ISC-119/120: Docker/Colima live run completed after backing up the stale generated SkillTree DB to `/tmp/active_skillference_skills_20260612063906.sql` and resetting the generated volume. `./scripts/run_skilltree.sh` defaulted to local FORM bootstrap and returned seed summary `{subjects:40, skills:248, quizzes:248, dependencies:478}`, `tokenVerified:true`; follow-up `--no-seed` token check passed; live API probe returned `live_skill_count 248`.
- ISC-121: Template render used the checkout-supported command `uv run python scripts/03_render_pdf.py --project Active_Skillference` from `../template` because `scripts/render_working_projects.py` is not present in this template checkout. Render generated `output/pdf/Active_Skillference_combined.pdf` (803 KB), `output/web/index.html`, `output/docx/Active_Skillference_combined.docx`, `output/epub/Active_Skillference_combined.epub`, and 9 slide PDFs. `pdftotext` over the combined PDF finds 248 skills / 40 subjects / 478 prerequisite edges / maximum depth 36 and no old 208/398 count hits.
- ISC-122: Current full gates: `uv run pytest --cov=src --cov-fail-under=90` → 291 passed / 98.58%; `uvx ruff check src scripts tests` → all checks passed; `uvx ruff format --check src scripts tests` → 64 files already formatted; `uv run mypy src` → success in 34 source files. Publication remains explicitly local-only until DOI, public target, and Crossref checks are performed externally.

### Documentation & metadata accuracy pass verification (2026-06-09 #2)
- ISC-65/67/68: `grep` over codemeta.json/CITATION.cff/.zenodo.json/domain_profile.yaml/experiment_plan.yaml → 0 "gradient/Convergence Analysis/optimization/2.3/2.5.0" strings; all `version` = 1.0.0 (codemeta/CITATION/.zenodo/pyproject/src/__init__/config.yaml).
- ISC-66: `grep 20417136|20420368` over all metadata/config → only ISA + tasks.yaml historical notes; CITATION.cff/.zenodo.json/manuscript/config.yaml DOIs all blank.
- ISC-69: `grep "168 test|99.2[^0]|19 claim"` over docs+manuscript+yaml → 0 (all 200 tests / 99.30% / 20 claims; format consistent — no 99.3 vs 99.30 drift).
- ISC-70/71/73/74: FINAL whole-project residue grep (template_code_project, optimizer.py, optimization_analysis, convergence_plot, step_size_sensitivity, performance_benchmark, {{VARIABLE, ../../../../template/, etc.) → "ENTIRE PROJECT CLEAN". The catalog's "gradient descent on free energy" is legitimate AIF content, retained.
- ISC-72: link-resolution probe over docs/ + manuscript/ → all real links resolve; the only flag (`my_new_figure.png` in docs/syntax_guide.md) is an in-code-fence pedagogical placeholder.
- ISC-75: references.bib rewritten to 8 AIF refs (Friston 2010/2017, Da Costa 2020, Parr 2022, Smith 2022, Heins 2022 pymdp, Cover&Thomas, Bishop); all 8 keys cited in 07_scope_and_related_work.md AND resolved by the render — `_combined_manuscript.bbl` carries the entries, `.blg` = 0 warnings.
- ISC-76: `grep canonical_facts pyproject.toml` → 0.
- ISC-77: tasks.yaml read-back — asf-5 done, asf-m1 notes accurate to this session's green gate + remaining release steps.
- ISC-78: render path validated — `00_preflight.py` standalone raises `ModuleNotFoundError: infrastructure` (symlink `.resolve()` escapes the template tree). The current template checkout does not provide `scripts/render_working_projects.py`; pass #6 docs use the verified entry `scripts/03_render_pdf.py --project Active_Skillference`, which produced PDF/slides/web/docx/epub from the rebased manuscript with citations resolving.
- ISC-79: `run_kernels.py` (provenance fail-closed) exit 0 after all manuscript edits — 20 claims, 3 figures, no new bare-number defects.
- ISC-80: FINAL `pytest tests/ --cov=src` → "200 passed", "Total coverage: 99.30%"; ruff + mypy clean.
- Cross-vendor (Forge/GPT-5.4, read-only): returned CONCERNS (2 HIGH + 1 MEDIUM beyond the original audit — rendering_pipeline stega-state mismatch, tasks.yaml over-claim, unrebased config.yaml.example; + LOW pyproject header) — all reproduced and RESOLVED this session; one Forge false-positive (z_generate "missing") correctly rejected since the co-actor had added it.
- Advisor (Inference.ts): logged — confirmed blank-DOI is correct for an unpublished project; flagged co-actor staleness (re-stat'd: 3 fixes survived) and per-ref DOI verification (deferred to Crossref-at-publication, documented in references.bib).

### Pedagogy / web / figures / integrity quality pass + cross-vendor audit (2026-06-15)
- Scope: deep multi-surface review (5 parallel reviewers + adversarial triage → 13 survivors)
  then implementation across the disjoint surfaces. Curriculum counts unchanged
  (600 skills / 105 subjects / 1136 edges); only answer TEXT, gates, web assets, one figure,
  and one manuscript paragraph changed.
- PEDAGOGY (quiz integrity): replaced ~30 off-domain placeholder DISTRACTORS (e.g. "Pixels",
  "Docker volumes", "CPU vendor", "The font rendering", "Screen dimensions", "Git branch
  names") with pedagogically plausible, on-domain alternatives across `catalog.py`,
  `_ext_frontier_topics.py`, `_ext_practice_translation.py`, `_ext_cogsec_collective.py`.
  Added a regression gate `quality._audit_implausible_distractors`: a full-phrase verbatim
  guard for dual-use/platform-meta strings (matched exact or before an appended balance
  clause — never as a bare-space prefix) PLUS a display/UI substring class that catches the
  whole off-domain class. `test_real_catalog_passes_curriculum_quality_gate` (audit == [])
  is the empirical guard for both no-jokes and no-false-positives across 2400 questions;
  negative + positive + boundary controls added.
- WEB (a11y, learner dashboard): `:focus-visible` styles, WAI-ARIA keyboard tab navigation
  (Arrow/Home/End + roving tabindex), a working skip-to-content link (`#main` target added),
  and an accessible dependency-flow `<table>` consuming the already-served `subjectFlows`.
  Verified live in real Chrome (skip-link, tab roles, click-switch aria-selected) + 30 tests.
- FIGURES: `plot_dependency_strata_flow` now renders the lower triangle as an explicit
  hatched "backward zone: must stay empty" region with a live "✓ no backward edges" title,
  making the DAG-safety invariant visually self-proving; registry caption/alt-text updated.
- INTEGRITY: `claim_support` now (production-strict via `run_kernels` + the validate script)
  cross-checks every declared `claim_tokens` against the kernel registry and every path-shaped
  `validators` entry against the filesystem (command-style validators skipped). `audit.py`
  deduplicated the low-information predicate into `_is_low_information` + a boundary test.
- CROSS-VENDOR (Forge/GPT-5.4, read-only): timed out at the 300s cap but, before timeout,
  independently confirmed the claim_support optional-default-None weakening and surfaced the
  KEY finding (completed by the orchestrator): the FIRST distractor gate was a verbatim
  allow-list, so `test_real_catalog_passes` was near-vacuous and ~14+ same-class jokes
  survived; plus a latent false-positive (a bare-space boundary matched "Pixels in a raster
  image"). BOTH FIXED: the gate gained a class-catching substring layer (proven non-vacuous
  by a negative control + by catching one more joke, "Git branch names", on rebuild) and a
  precise clause-prefix match. Remaining Forge notes (optional-default params, .py-only
  validator regex) accepted as documented design, not bugs.
- Honest scope note: the distractor pass targeted the off-domain infra/UI/platform-meta
  class (now gate-guarded); subtler "weak but on-topic" distractor refinement remains an
  ongoing curation concern, not a solved problem.
- Final gates: `pytest --cov=src --cov-fail-under=90` → 447 passed / 92.32%; build valid
  (600/105/1136, 8/8 strata, depth 75); `run_kernels` 22 claims + strict claim-support 53
  claims + 16 figures; export 600/1136; ruff check + format + mypy(58 files) all clean.
  Local-only; publication (asf-public-release-metadata) still pending DOI/target.

### Coverage restoration + dead-code/robustness fixes (2026-06-15 #2)
- Per-module coverage had eroded well below the project's ~98% standard as features were
  added (variables.py 63.5%, source_health.py 69.9%, roadmap.py 72.9%,
  graph_analysis.py 77.6%, web_math.py 79.0%, audit.py 85.0%, claim_support.py 88.5%).
  A 7-agent no-mock coverage pass (one per test file, isolated COVERAGE_FILE, real
  pytest-httpserver / real temp files / real data — zero MagicMock/patch) restored every
  module: variables/roadmap/live_counts/graph_analysis/web_math → 100%; source_health
  98.7%, coverage 99.0%, audit 98.7%, claim_support 99.7%. EVERY src module now ≥ 90%.
- The coverage cross-check surfaced TWO real source defects (fixed here, not by the
  test agents): (1) `source_health._check_url`/`_check_url_get` had dead `except
  socket.timeout` clauses after `except TimeoutError` — `socket.timeout is TimeoutError`
  on Python 3.10+, so they were unreachable; removed them and the now-unused `socket`
  import. (2) `roadmap.audit_roadmap` called `render_todo(payload)` unguarded, so a
  structurally malformed roadmap raised a raw `TypeError` and discarded the collected
  issues; wrapped it so the audit always returns its findings (a "too malformed to
  render" issue) instead of crashing — `test_roadmap_rejects_non_mapping_task` updated
  to assert the robust behavior.
- Final: `pytest --cov=src --cov-fail-under=90` → 560 passed / 97.07% (was 447 / 92.32%);
  ruff check + format + mypy(58 files) all clean. No curriculum/count changes.

### Pedagogy: discrete↔continuous active-inference conceptual bridge (2026-06-15 #3)
- The review found discrete (POMDP/EFE/policy-selection) and continuous (predictive-coding)
  active inference were taught as parallel topics with no explicit conceptual link. Added
  the bridge HONESTLY and count-neutrally: enriched `ai_predictive_coding`'s description to
  state it realises the SAME variational free-energy imperative as discrete active inference
  but over continuous belief trajectories updated by gradients rather than a discrete policy
  distribution scored by expected free energy — "the same principle in a different geometry"
  (no false exact-isomorphism claim, addressing the triage's misconception concern). Added a
  `related=("ai_policy_selection",)` cross-link so learners can navigate continuous→discrete.
- Count-neutral by design: `related` links are not prerequisite edges and are excluded from
  the SkillTree export, so 600/105/1136/2400 are unchanged and no count-cascade is triggered.
  Build valid, 64 curriculum tests pass, kernels/provenance clean, ruff+format+mypy clean,
  full suite 560 passed / 97.07% (one SIGINT-timing test flaked under parallel load and
  passes in isolation — the documented load-contention pattern, not a regression).

### Cognitive-security foundational skill + manuscript depth (2026-06-15 #4)
- PEDAGOGY (B): the review found the cognitive-security pathway jumped straight to
  population-level reasoning (`cog_info_ecosystem`) with no skill explaining HOW individual
  generative models compose. Added `fep_collective_inference` ("Coupling Generative Models
  Across Minds") in the FEP stratum (subject sub_blanket): conditioning two agents'
  models p_A(o,s)/p_B(o,s) on a shared observation makes their posteriors estimate the same
  hidden cause; communication couples them; an ecosystem observer pools them; convergence
  depends on evidence precision and prior diversity. Wired it as a prerequisite of
  `cog_info_ecosystem`, so it is a genuine foundational bridge in the learning path. Two
  authored transfer assessments (on-domain distractors; pass the distractor gate).
- COUNT CASCADE handled end-to-end: 600→601 skills, 1136→1139 edges (+2 new prereqs +1 new
  edge into cog_info_ecosystem), 2400→2404 assessments (2 authored + 2 auto-rubric), 600→601
  quizzes; subjects 105 and max_depth 75 unchanged. Updated tasks.yaml live_metrics + every
  per-task metric block + manuscript/config.yaml min_skill_count; regenerated TODO.md;
  manuscript {{token}} counts auto-updated from the graph. The fail-closed
  `validate_live_counts` enumerated all 26 stale literals and confirmed clean after fixes;
  `validate_roadmap` clean; export 601/1139.
- MANUSCRIPT (C): two honest refinements. (1) Methodology/provenance: a paragraph making the
  kernel-correctness↔pedagogical-integrity chain explicit — provenance binding makes a
  number traceable, the deterministic mock-free kernel tests are what make that traceability
  worth anything; a learner-facing value is only as sound as the kernel behind it.
  (2) Limitations: an explicit boundary that the contribution is verifiability/provenance of
  content, NOT a measured learning-outcome claim (no efficacy/retention/transfer study is
  reported; that is future work). Both pass American-English + claim-support (53 claims,
  no strong-word violations); the limitations addition stays under the existing scope_limit
  anchor (no new YAML row).
- Final: full suite 560 passed / 97.07%; ruff+format+mypy clean; build 601/105/1139,
  kernels 22 claims, export 601/1139, PDF re-rendered, rendered-freshness OK (11 files).
  Local-only; publication (asf-public-release-metadata) targeted for tomorrow.

### Iteration 6 verification (2026-06-16) — artifact tokens
- ISC-123: `pytest test_provenance.py -q` → `test_render_fails_closed_on_whitespaced_claim_tokens[...]` PASS (3 variants); `render('The value is {{ claim:e }} nats.', reg)` raises ProvenanceError.
- ISC-124/125: `test_claim_support_rejects_computed_with_empty_token_list` + `test_claim_support_rejects_bare_result_number_in_computed_prose` PASS; live `validate_claim_support.py` → "validated manuscript claim support: 55 claims".
- ISC-126: `build_curriculum.py` after fix → "curriculum valid: 610 skills / 107 subjects / 1159 prerequisite edges"; gate caught real `browser cache` distractor at `front_comp_schema_validation` → fixed; `test_quality_flags_extended_off_domain_distractor` PASS.
- ISC-127: battery — MC best constant-set 16.8% (cap 30%), SingleChoice best fixed-position 29.6% ≈ chance; finding rejected (no code change).
- ISC-128: `test_role_gate_rejects_lane_name_padding` PASS; `validate_scholarship_sources.py` → "valid: 95 sources".
- ISC-130/131: `pytest test_kernels_information.py test_kernels_active_inference.py -q` PASS incl. `test_cross_entropy_accepts_non_normalized_q`, `test_kl_matches_independent_sum` (KL=0.3680642), `test_epistemic_value_equals_state_observation_mutual_information` (=ln2), `test_cross_entropy_rejects_unnormalized_p`.
- ISC-132/133: `_audit_semantic_prerequisites(build_curriculum())` → "violations: 0"; `test_quality_flags_missing_semantic_prerequisite` + `test_semantic_prereq_concept_map_is_non_vacuous` PASS.
- ISC-134: `test_course_material_online_validation_fires_on_missing_pointer` PASS (pytest-httpserver, `pointer-path` code fires).
- ISC-135/136: `export_skilltree.py` → "610 skills, 1159 dependencies"; `validate_manuscript_artifacts.py` PASS with `fig:semantic_prerequisite_coverage`; `test_figures.py`/`test_dashboard.py` PASS (17 figures / 35 artifacts).
- ISC-137: `audit_live_count_literals` → "stale: 0"; `validate_roadmap.py` PASS.
- ISC-138: `pytest --cov=src --cov-fail-under=90` → 592 passed, 92.94%; `ruff check`/`mypy src/` → "All checks passed!" / "no issues found in 62 source files".
- ISC-140: Superseded by `asf-cross-vendor-security-audit`; Advisor (same-vendor) ran,
  3 findings resolved, and the independent cross-vendor audit remains blocked in the
  active roadmap.

### Iteration 6b verification (2026-06-16) — artifact tokens
- ISC-141: `pytest test_provenance.py -q` → `test_render_neutralizes_zero_width_split_claim_token[...]` PASS (5 Cf chars) + `test_unbacked_linter_detects_zero_width_split_number` PASS; real export still renders (skilltree_project.json: 617 skills).
- ISC-142: `test_course_material_loaders_fail_closed_on_malformed_json` PASS — injecting `{"version":1}` → `available=False` + "required key" error.
- ISC-143: `\bKLs?\b`/`\bELBOs?\b` patterns; `_audit_semantic_prerequisites(build_curriculum())` → 0 violations; non-vacuity guard PASS.
- ISC-144: `build_curriculum.py` → "curriculum valid: 617 skills / 109 subjects / 1172 prerequisite edges"; `export_skilltree.py` → "617 skills, 1172 dependencies".
- ISC-145: `audit_live_count_literals` → "stale: 0"; `validate_claim_support.py`/`validate_american_english.py` clean after methodology prose change.
- ISC-146: `pytest --cov=src --cov-fail-under=90` (see SUMMARY) ; `ruff check`/`mypy src/` → "All checks passed!"/"no issues found in 64 source files".

### Iteration 8 verification (2026-06-20) — kernel expansion + cross-vendor closure
- Cross-vendor security audit (asf-cross-vendor-security-audit, was deferred ISC-140/ISC-99/ISC-113): Forge/GPT-5.4 read-only audit ran this session (the GPT-5.4 rate-limit that blocked it across 4 prior sessions expired today) → verdict NO unresolved critical/high; both prior fixes verified present, correct, and non-vacuously tested. Item CLOSED.
- Kernel-bound expansion: `build_claim_registry()` → 43 claims (was 22); `pytest test_kernels_examples.py test_kernels_inference.py test_kernels_active_inference.py` PASS incl. `test_belief_propagation_matches_brute_force_enumeration`, `test_multistep_planning_reduces_to_one_step_at_horizon_one`, `test_lookahead_pays_only_under_temporal_coupling` (coupled gain 0.820981 nats, decoupled 0.0), `test_greedy_baseline_is_honest_not_crippled`, `test_model_reduction_rejects_the_reduced_model_after_positive_reading` (+0.172252 nats).
- Forge cross-vendor math audit: independently recomputed every new kernel from scratch → math correct, BP exact vs brute force to 1e-12, NO crippled comparator, both-regime planning framing honest.
- Manuscript binding: `run_kernels.py` + `z_generate_manuscript_variables.py` green; `validate_manuscript_variables.py` → "audit clean: 11 live keys checked" with the corrected `[0-9][0-9]*_*.md` glob covering subsection files.
- Gate hardening: `test_hardcode_linter_is_non_vacuous_on_subsection_files`, `test_audit_manuscript_banned_phrases_scans_whole_files`, `test_find_banned_phrases_resists_whitespace_evasion`, `test_local_auth_requires_loopback_bind`, `test_figure_text_does_not_hardcode_a_stale_assessment_floor` all PASS (firing negative controls).
- Floor defect: enforced `MIN_ASSESSMENTS_PER_SKILL=4` now bound as `{{failable_floor}}` in the manuscript AND rendered dynamically in the figure layer; the factually-wrong hand-typed "three-question floor" removed from manuscript prose and 5 figure strings (Forge caught the figure layer).
- Visualization: new `fig:planning_lookahead` (20 registered figures, was 19); `validate_manuscript_artifacts` → "20 registered figures".
- release_readiness blocker-probe coverage 76.8% → 89% via real-subprocess tests (no mocks).

## Changelog

### 2026-06-20 — temporal planning is regime-dependent, and the figure layer is a separate drift surface
- conjectured: multi-step look-ahead in active inference would beat a one-step agent, demonstrating the value of planning.
- refuted_by: the planning kernel measured a look-ahead gain of exactly 0.0 in the decoupled sample/commit model (the greedy myopic policy is already optimal); a positive gain (0.820981 nats) appears only in a coupled investment model where immediate and long-run value diverge. Forge cross-vendor independently confirmed the greedy comparator is the strongest myopic policy (not crippled), so the contrast is honest.
- learned: look-ahead value is not a universal property of planning — it requires temporal coupling. The honest pedagogy is to present BOTH a null and a positive regime and name the structural condition, rather than engineering a model where planning trivially wins.
- criterion_now: planning_examples emits both `plan_lookahead_gain_decoupled` (0.0) and `plan_lookahead_gain_coupled` (>0.5), and `test_greedy_baseline_is_honest_not_crippled` triangulates that the gain is real (optimal beats greedy, greedy is the argmin, and a worse policy exists).
- conjectured (gate coverage): binding the assessment floor to the enforced constant in the manuscript closed the "three-question floor" drift.
- refuted_by: the manuscript-variable linter only scans manuscript/*.md, so five `plot_*` figure strings still rendered the stale "three" floor — a reader-facing contradiction the manuscript fix missed, surfaced by the cross-vendor vacuity audit.
- learned: the figure caption/panel layer is a distinct hand-authored claim surface with no manuscript-variable gate; Python string literals cannot use `{{token}}`, so they must f-string the enforced constant, and a source-level regression test must guard the phrase.
- criterion_now: `test_figure_text_does_not_hardcode_a_stale_assessment_floor` fails on any stale "three"-floor phrase in plots/ and requires the enforced constant to be referenced.

### Iteration 8b verification (2026-06-20) — predictive coding + learner-facing binding (pushed)
- Pushed iteration 8 to private main (`aff7719..4bbc882`); remote HEAD verified == local. Then continued (this entry).
- Predictive coding: new `src/kernels/predictive_coding.py` (linear-Gaussian prediction-error descent). `pytest test_kernels_predictive_coding.py` PASS (7) incl. `test_descent_converges_to_analytic_posterior` (estimate == gaussian_posterior_mean to 1e-6), `test_free_energy_descends_monotonically`, `test_prediction_errors_balance_at_convergence`. Claims 43 -> 47; figures 20 -> 21 (new `fig:predictive_coding`).
- Forge cross-vendor VERIFY (round 2): ALL-PASS. Lane 1 independently recomputed the PC math in a separate process (posterior 4/3 to machine epsilon, contraction factor 0.7, FE max-forward-diff 2.2e-16, oracle non-tautological). Lane 2 verified every new binding accurate + correctly scoped (64 claims, exit 0). Two LOW optional hardenings applied: `steps_to_converge` now uses the update-magnitude criterion (decoupled from the closed form); `_INFORMATIVE_SENSOR_A` is a single source of truth shared by efe/planning/param so the 05 binding cannot drift.
- Learner-facing binding (the prior round's claims were manuscript-only): `mp_belief_propagation` now embeds the BP marginals and `ai_generalized_coordinates` embeds the PC result, so the SkillTree export shows the computed numbers. `validate_curriculum` PASS (tokens resolve). 05_experimental_setup kernel params bound via `{{claim:param_*}}`.
- Full gate: 722 passed / 92.29% coverage; `ruff`/`mypy` clean (70 source files). Curriculum counts unchanged (630/111/1199 — binding is count-neutral).

### Iteration 9 — vendored SkillTree currency audit (2026-07-03)
- Trigger: upstream `NationalSecurityAgency/skills-service` cut new releases; audited whether the pinned runtime (`docker-compose.yml`, `vendor/README.md`) was still current.
- Findings via `gh api`: pinned tag was `4.4.2` (released 2026-06-08); latest is `4.5.2` (released 2026-07-02), with `4.4.3`/`4.5.0`/`4.5.1` in between. `4.5.0` added batch skill editing, quiz file attachments, and table-formatting fixes; `4.4.3`/`4.5.1`/`4.5.2` are bug-fix-only.
- **Correction (4-agent adversarial re-verify, same day):** the first draft of this entry claimed diffing `4.4.2...4.5.2` "shows only `AdminController.groovy` touched among controllers, and additively," and attributed this repo's untouched call paths to `ProjectController`/`SubjectController`/`QuizDefController`. Both statements were wrong — those three class names do not exist in `skills-service` at any tag. Re-verified: four controllers changed — `AdminController.groovy` (additive: new optional query params, a new `batchUpdateSkills` endpoint, validation extracted into `SkillRequestValidator` with confirmed-equivalent checks/ordering), `AppController.groovy` (trivial blank-line removal), `MyProgressController.groovy` (additive new endpoint), and `SkillApprovalController.groovy` — which is **not additive**: `GET /projects/{projectId}/skills/{skillId}/approvals/stats` was replaced by `POST /projects/{projectId}/approvals/stats` taking a `SkillApproverStatsRequest{skillIds}` body (route, method, and shape all changed). This repo's `SkillTreeClient` (`src/skilltree/client.py`) never calls that endpoint (grep for `approvals/stats`/`SkillApproval` is empty; the exporter never emits `selfReportingType=Approval`), so there is no practical breakage here, but the original "no breaking change" framing was an unqualified overclaim about the upstream API rather than the scoped claim it should have been. The real, independently-diffed call paths — `POST /admin/projects/{projectId}` (create_project), `.../subjects/{subjectId}` (create_subject), `.../subjects/{subjectId}/skills/{skillId}` (create_skill, byte-identical handler/response shape at both tags), `.../{skillId}` dependency assignment, `/admin/quiz-definitions/*` (`QuizController.groovy`, untouched), and the client-display `/api/...` read (`UserSkillsController.groovy`, untouched) — are all confirmed unaffected. Scoped claim: **no breaking change to the endpoints this integration uses**, not a blanket claim about the upstream API.
- Security check: `GHSA-hqfg-c8wf-w2g8` (CVE-2026-54694, critical stored-XSS admin-takeover) is patched at `>= 4.4.2` — the prior pin was already safe; this bump is a currency update, not a vulnerability fix. `GHSA-9624-qwxr-jr4j` (CVE-2024-39326) was patched long before either pin.
- `AuthMode.groovy` at the `4.5.2` tag confirms the enum is still `FORM, PKI, SAML2` (no `PKI_OR_FORM`) — the compose comment warning against `PKI_OR_FORM` remains accurate; corrected it to name all three real values.
- Digest re-pinned via the documented refresh procedure (`auth.docker.io/token` + `registry-1.docker.io/v2/.../manifests/4.5.2`), confirmed against the Docker Hub API: `sha256:accc8e71fbf4376bc5fe5909f903f8f850349501979f50816428187519c14cd4`, single-arch `linux/amd64` (matches the existing `platform:` pin and amd64-only framing).
- Updated: `docker-compose.yml` (image tag+digest, two comments), `vendor/README.md` (four current-tense mentions of the pinned tag/checkout, plus a pre-existing unrelated bug the re-verify caught: the "build from source" snippet said `git checkout v4.5.2`, but upstream tags have no `v` prefix — `git ls-remote --tags` confirms bare `4.5.2`/`4.4.2`; fixed to `git checkout 4.5.2`, this bug predates this iteration and was carried by the earlier `v4.4.2` text too). Left untouched, deliberately: `vendor/README.md`'s "Historical local Docker status" note and this file's ISC-32..40 / ISC-81 entries above, which are dated records of what was literally run/observed at `4.4.2` — rewriting them to `4.5.2` would falsify history rather than reflect it.
- **Gap flagged, not yet closed:** this bump only touched the digest-pin and docs (`scripts/validate_docker_digests.py` + `tests/test_scripts_smoke.py`, both static checks — neither pulls nor boots the new image). `tasks.yaml`'s prior live-verification lineage (`asf-skilltree-live-recheck`, `asf-live-full-stack-release-rehearsal`, `asf-raw-skilltree-form-login-proof`) earned its "done" status against `4.4.2`; none of it has been re-run against `4.5.2`, and per this project's own provenance-over-assertion principle those "done" statuses should not be read as currently proving anything about `4.5.2`. Added `asf-skilltree-452-live-reverify` to `tasks.yaml` to track the live re-run.
- Verification: `uv run python scripts/validate_docker_digests.py` (digest-pin gate) and `uv run pytest tests/test_scripts_smoke.py -q` after the edit.

### Iteration 10 — closing the live-reverify gap, plus a broader currency/security sweep (2026-07-04)
- Scope: close `asf-skilltree-452-live-reverify` for real (not just docs), and run a second, independent 4-agent audit of the rest of the repo (other pinned dependencies, full quality gate, Bandit security sweep, cross-file consistency) beyond the skills-service bump itself.
- **Other pinned dependency found stale:** `docker-compose.yml`'s `postgres:15@sha256:c2ca909...` was the same *version* (15.18) as current but an older *rebuild* — the current `postgres:15`/`15.18` tag resolves to a different digest (`sha256:3b0d656f...`, pushed 2026-06-27) rebuilt against a refreshed `debian:trixie-slim` base ~2 weeks later. Re-verified independently via the documented registry token+manifest procedure (bit-for-bit match with the audit's claim) and confirmed the new digest is still a multi-arch manifest including `arm64` (matches this arm64 Colima host). Repinned to the current digest; no version bump, just a base-layer refresh.
- **Security hardening (Bandit B310 sweep, all independently re-verified before fixing):**
  - New `src/net_guard.py` (`require_http_url`, `is_http_url`, `is_loopback_host`) — a shared, dependency-light guard so local-first CLI tools that take `--dashboard-url`/`--skilltree-url`/`--base-url` flags reject non-http(s) targets before calling `urlopen` (a `file://` URI previously would have been silently followed). Applied at `src/dashboard/live_validation.py:_fetch_json`, `src/dashboard/status.py:check_skilltree_status`, `src/integration/full_app_stack.py:_fetch_json`, `src/curriculum/materials/:_fetch_github_tree_paths` (defense-in-depth on top of the existing `_github_repo_parts` guard), and inlined (to avoid adding a `src/` import to an intentionally standalone script) in `scripts/validate_dashboard_console.py:_dashboard_reachable`. `src/dashboard/config.py`'s pre-existing `_is_loopback_host` now delegates to the shared `net_guard.is_loopback_host` instead of duplicating the logic.
  - `src/scholarship/source_health_network.py:_open_url`'s bandit B310 flag was a false positive (the `allow_private=False` path is already gated by `_public_http_url_block_status`, and the flagged branch only fires on an explicit `allow_private=True` opt-in, default off everywhere) — annotated with `# nosec B310` plus a comment explaining why, no logic change.
  - **Real gap, fixed:** `src/skilltree/local_auth_state.py`'s `DEFAULT_LOCAL_ADMIN_PASSWORD` (`"active-skillference-local"`, source-controlled and publicly readable) is used by `_load_or_create_root_state()` to actually provision the SkillTree root account on first bootstrap. Nothing previously stopped that from happening against a non-loopback `--skilltree-url`/`--base-url` (an operator-error scenario, e.g. accidentally pointing a bootstrap script at a shared/staging instance). Added `_refuse_default_password_off_loopback()` in `src/skilltree/local_auth.py`, called from `_load_or_create_root_state` before `create_root_account`: refuses when the password is still the known default AND the target host isn't loopback; an explicit `ACTIVE_SKILLFERENCE_LOCAL_ADMIN_PASSWORD` override bypasses it (the password is then no longer the known default). All existing bootstrap tests use loopback `httpserver` targets, so this is additive, not a behavior change for them.
  - Added 21 new tests across `tests/test_net_guard.py` (new), `tests/test_dashboard.py`, `tests/test_dashboard_console.py`, `tests/test_dashboard_live_validation.py`, `tests/test_course_materials/`, `tests/test_full_app_stack.py`, `tests/test_skilltree_local_auth.py`, `tests/test_reset_local_skilltree.py`. Every `require_http_url`-guarded `urlopen` call site (`live_validation.py`, `status.py`, `full_app_stack.py`, `materials/`, `validate_dashboard_console.py`) and the justified `source_health_network.py` bypass now also carry a same-line `# nosec B310` — Bandit's blacklist rule can't see the scheme check a few lines above, so without it the rule keeps re-flagging code that is already mitigated; final `uv run --with bandit bandit -r -ll src scripts`: **0 medium/high findings** (was 6). Full gate after all security fixes: `ruff check`/`ruff format --check`/`mypy src` clean; `pytest --cov=src` **815 passed, 90.17% coverage** (up from 797 passed / exactly 90.00% — the prior audit flagged that exact-90% margin as a currency risk given five weak modules; still worth a dedicated pass but no longer sitting at the knife's edge).
- **Closing `asf-skilltree-452-live-reverify` surfaced two real, pre-existing bugs (both unrelated to the version number itself, both blocking any fresh-checkout live proof regardless of 4.4.2 vs 4.5.2):**
  1. `scripts/validate_full_app_stack.py` called `docker compose up -d` directly without first setting `ACTIVE_SKILLFERENCE_POSTGRES_PASSWORD` the way `scripts/run_skilltree.sh` does — so the documented `vendor/README.md` "Option A++" one-liner failed closed on a fresh environment (`docker compose up -d` fails to interpolate the compose file without that var). Fixed by adding `ensure_postgres_password()` to `src/integration/full_app_stack.py` (same `<state_dir>/postgres_password` file convention as the shell script: reuse if present, generate+persist with `0600`/`0700` perms if not, respect an already-exported override) and calling it before the compose command.
  2. `scripts/reset_local_skilltree.py`'s `docker compose down -v` had the exact same gap (compose interpolates the file for `down` too, not just `up`). Fixed by importing and calling the same `ensure_postgres_password()` helper there.
  3. (Environmental, not a code bug) A stale `.active_skillference_local/skilltree_auth.json` left over from the 2026-06-22 4.4.2 run caused a transient `401` on the first clean-Postgres-volume attempt: `_load_or_create_root_state` reused the stored (now-stale) admin credentials instead of creating a new root account, because the local state file existed even though the underlying Postgres data was gone. Resolved by using the documented `reset_local_skilltree.py` path (which backs up and removes local auth state before resetting the volume) instead of a bare `docker compose down -v` — this is exactly the scenario that script exists to handle.
- **Final live proof, `skilltree-service:4.5.2`, `--app-ready` mode (`uv run python scripts/reset_local_skilltree.py --confirm-local-reset --timeout 1200`):** `proof.ok=true`; fresh root bootstrap + FORM login proof (`rawSkillTreeLogin.adminSurfaceVisible=true`, page title `SkillTree Dashboard - Project Administrator`); live admin project `skills=630` (matches `live_metrics`); artifacts `42/42` present; figure contracts `registered=21/dashboard=21`; browser console gate clean (`chrome-devtools-axi`, 1 known-allow-listed Inception probe message, zero unexpected errors). Full live-dependency parity (1199/1199 edges via the admin REST API) was **not** attempted — `--app-ready` explicitly skips it, consistent with `asf-skilltree-live-recheck`'s prior finding that per-edge REST dependency validation is too slow at this project's 600-skill scale; that remains separately tracked and is independent of this version bump. Docker containers, the dashboard process, and the Compose volume were torn down cleanly after recording evidence (`docker compose down -v`, exit 0) — nothing was left running.
- `asf-skilltree-452-live-reverify` marked `done` in `tasks.yaml` with the real evidence above; `TODO.md`/`docs/todo/` regenerated via `scripts/validate_roadmap.py --write-todo` (clean).

### Iteration 11 — vendored SkillTree currency update to 4.6.0 (2026-08-01)
- Trigger: re-audited upstream `skills-service` currency. Latest release is now `4.6.0`
  (2026-07-28); the repo pinned `4.5.2`.
- Digest re-pin via the documented procedure (`auth.docker.io/token` + query of
  `registry-1.docker.io/v2/.../manifests/<tag>`, reading the `Docker-Content-Digest` response
  header — not the config blob): `skilltree/skills-service:4.6.0` =
  `sha256:071220ce9de0432eeb17c375e17de34bd6887938a85d91b3cb16fe2e72ff42d5`
  (mediaType `manifest.v2`, single-arch — consistent with the `platform: linux/amd64` pin);
  `library/postgres:15` = `sha256:74e110c41804365e3915fcc09d5e7a1eff50161aaa94d5da0e58e0cd75ae509c`
  (OCI image index, multi-arch including `arm64`, so native on this arm64 host).
- `AuthMode` re-verified at the `4.6.0` tag (`service/src/main/java/skills/auth/AuthMode.groovy`):
  the enum is still `FORM, PKI, SAML2` (no `PKI_OR_FORM`), so the compose comment warning stays accurate.
- Updated: `docker-compose.yml` (skills-service tag+digest to 4.6.0, postgres:15 to current
  digest, comment rewording), `vendor/README.md` (current-tense 4.5.2 -> 4.6.0 mentions,
  submodule checkout pin, plus a version-history note). Left unchanged, deliberately: the
  "Historical local Docker status" note and the iter-9/10 records, which are dated records of
  4.4.2/4.5.2 runs — rewriting them would falsify history.
- **Gap flagged, not closed:** this bump is a digest-pin + docs change only. No live full-app
  boot was recorded against 4.6.0 because Docker was not running on the reconciliation host;
  per the provenance-over-assertion principle the 4.5.2 live proof (iter-10) does not vouch for
  4.6.0. Added `asf-skilltree-460-live-reverify` (todo) to `tasks.yaml` to track the live re-run.
- Verification: `uv run python scripts/validate_docker_digests.py` (digest-pin gate green) and
  `uv run pytest tests/test_scripts_smoke.py tests/test_docs_inventory.py -q` after the edit.
  Also re-ran the full gate under the newest Python deps (numpy 2.5.1, matplotlib 3.11.1,
  scipy 1.18.0): `pytest --cov=src --cov-fail-under=90` = 893 passed / 90.70% (no regression
  from the dependency bump), `ruff check`/`format --check` clean, `mypy src` clean.
