# Testing Philosophy: The Zero-Mock Standard

Active Skillference tests real computation without mock frameworks. The suite verifies
actual mathematical properties, the structural invariants of the curriculum DAG, the
fail-closed behavior of the provenance gate, and the real HTTP contract of the
SkillTree client — all with deterministic data and (for HTTP) a real local server.

**Current standard: all tests passing, line coverage on `src/` at or above the 90%
floor, and no mock-framework objects.** Use the coverage command below as the source of
truth for current test count and percentage.

## Why Zero Mocks?

The insight is architectural: if a function requires a mock to be tested, it is doing I/O,
calling external systems, or producing side-effects — which means it belongs in `scripts/`
(orchestration), not in `src/` (pure logic). The purity of the kernels in
[`src/kernels/`](../src/kernels/) is what makes zero-mock testing achievable: every kernel
is deterministic and side-effect-free, so tests call it with real numpy arrays and assert
real outputs against analytic ground truth.

If you feel the urge to mock quantitative or protocol behavior in a `src/` test, treat it
as a signal: the boundary is in the wrong place. The one place real network behavior
matters — the SkillTree REST client and seeder — is tested against a **real local HTTP
server** (`pytest-httpserver`), not a stubbed transport. Some orchestration and
failure-path tests use `pytest`'s `monkeypatch` to isolate environment variables,
executable discovery, or injected OS errors. Those substitutions must not replace a
kernel, fabricate an HTTP response, or serve as evidence that an external integration
works.

## Negative controls for handoffs

Every high-value validator should have a nearby planted failure that proves the validator
can actually see its defect. The current boundary set includes malformed or dangling
SkillTree export references, dependency cycles, non-HTTP service URLs, path-segment
characters that require quoting, `javascript:` course-material pointers, stale alignment
summary counts, failed live subproofs, and unsafe local secret-file types or permissions.
The same reasoning covers states that could be *mistaken* for a pass: a deferred live-parity
payload carries `checked: false` and a reason string, and its test asserts that deferring
changes nothing else in the response, so a fast first paint can never be read as a
successful parity check.

These tests are intentionally small: they exercise the boundary contract with real domain
objects and payloads, then assert the specific failure class. A passing test that only checks
the happy path is evidence of execution, not evidence that the gate is non-vacuous.

The same principle applies to visuals. The validation-surface matrix derives cells from
validator/test file existence, and its rows distinguish the SkillTree handoff from
serialized export integrity and material-link safety. Removing a bound file flips the cell
to `n/a`; the figure cannot continue certifying a gate that is absent.

## The test suite

Modules that repaint every figure or rebuild the full artifact chain carry a module-level
`slow` mark (`test_figures.py`, `test_pipeline_generated_outputs.py`,
`test_rendered_freshness.py`, `test_scripts_smoke.py`). `./gates.sh fast` deselects them so
the editing loop stays short; `./gates.sh test` runs them all and is what CI runs. The
marker is registered in `pyproject.toml`, and `--strict-markers` is on, so a typo fails
collection instead of silently selecting nothing.

| File | Covers |
| --- | --- |
| [`test_kernels_information.py`](../tests/test_kernels_information.py) | `surprise`, `entropy`, `cross_entropy`, `kl_divergence`, `mutual_information` — analytic identities and input guards |
| [`test_kernels_distributions.py`](../tests/test_kernels_distributions.py) | `normalize`, `softmax` (sum-to-one, shift-invariance, precision sharpening), `log_stable`, Dirichlet helpers |
| [`test_kernels_inference.py`](../tests/test_kernels_inference.py) | `bayes_posterior`, `variational_free_energy`, `elbo`, `log_evidence` — bound tightness at the posterior, ELBO ≤ log-evidence, input guards |
| [`test_kernels_active_inference.py`](../tests/test_kernels_active_inference.py) | `expected_free_energy`, `policy_posterior`, `DiscreteActiveInferenceAgent` — epistemic value, policy softmax, deterministic seeded action, multi-step rollout, the regime-dependence of the epistemic preference |
| [`test_kernels_examples.py`](../tests/test_kernels_examples.py) | The worked examples / claim registry: expected claim count, analytic values, registry determinism, and that every catalog token resolves against the registry |
| [`test_kernels_predictive_coding.py`](../tests/test_kernels_predictive_coding.py) | Linear-Gaussian predictive-coding kernel: precision-weighted posterior settling, monotone free-energy descent, analytic-minimum agreement |
| [`test_curriculum_model.py`](../tests/test_curriculum_model.py) | `Stratum` ordering and foundational flags, `AssessmentQuestion` / `Skill` validation, claim-token parsing, `is_root` |
| [`test_curriculum_graph.py`](../tests/test_curriculum_graph.py) | `CurriculumGraph` validation (duplicate id, dangling/self-loop prerequisite, cycle path, non-foundational root), topological order determinism, depth levels, foundations→applications connectivity |
| [`test_curriculum_catalog.py`](../tests/test_curriculum_catalog.py) | The real Active Inference catalog: builds + validates, maximal-enumeration floor, all eight strata present, every stratum has a subject, connectivity, every skill has an objective + assessment, roots only in foundational strata, unique ids, applications as the canopy |
| [`test_curriculum_quality.py`](../tests/test_curriculum_quality.py) | Curriculum quality gates: backward prerequisites, shallow assessments, answer-position leakage, duplicate objectives, missing tags, weak descriptions, distractor hygiene, and the semantic-prerequisite gate (a skill may not be assessed on a load-bearing concept its transitive prerequisites cannot reach), with a non-empty-scan guard against silent vacuity |
| [`test_provenance.py`](../tests/test_provenance.py) | `ClaimRegistry` register/get, idempotent re-registration, conflict detection, string-claim digit guard, JSON round-trip; `render`/`validate_skill`/`validate_curriculum` fail-closed behavior |
| [`test_scholarship.py`](../tests/test_scholarship.py) | Citation source-role matrix validation, stale matrix/BibTeX rejection, planted failure cases, real manuscript coverage, deterministic audit JSON |
| [`test_course_materials.py`](../tests/test_course_materials.py) | Course-material source contract validation, complete per-skill local Learn records, resolved claim tokens, official subject/quiz handoff boundaries, deterministic material artifacts, and exported skill/material/quiz alignment |
| [`test_curriculum_alignment.py`](../tests/test_curriculum_alignment.py) | SkillTree/material/quiz alignment validator: duplicate ids, dangling quiz references, malformed shapes, dependency self-loops/cycles, and material-record content mismatches |
| [`test_assessment_normalize.py`](../tests/test_assessment_normalize.py) | Assessment normalization and quality-enforcement helpers |
| [`test_claim_support.py`](../tests/test_claim_support.py) | Claim-support anchors, evidence-class requirements, and unsupported strong scientific language |
| [`test_pilot_contract.py`](../tests/test_pilot_contract.py) | Protocol-only learner-pilot contract: required nested fields, privacy/efficacy boundaries, export shape, and validation error branches |
| [`test_artifacts_json_io.py`](../tests/test_artifacts_json_io.py) | Shared deterministic JSON read/write helpers and their error modes |
| [`test_manuscript_artifacts.py`](../tests/test_manuscript_artifacts.py) | Figure registry, manuscript declarations/cross-references, PNG readability/information content, caption/alt text, semantic metadata, claim tokens, and dashboard figure artifact drift validation |
| [`test_manuscript_language.py`](../tests/test_manuscript_language.py) | American English spelling gate for authored manuscript prose |
| [`test_manuscript_variables.py`](../tests/test_manuscript_variables.py) | Live manuscript variable counts and roadmap/scholarship summary propagation |
| [`test_publication_readiness.py`](../tests/test_publication_readiness.py) | Publication-readiness wording stays bounded to local artifact readiness |
| [`test_rendered_freshness.py`](../tests/test_rendered_freshness.py) | Rendered manuscript copies and live graph counts stay fresh against current source artifacts |
| [`test_pipeline_generated_outputs.py`](../tests/test_pipeline_generated_outputs.py) | Multi-artifact pipeline outputs and generated counter files stay current |
| [`test_release_readiness_inventory.py`](../tests/test_release_readiness_inventory.py) | Machine-checked release-isolation inventory: dirty-worktree snapshot, artifact hashes, untracked-files |
| [`test_skilltree_model.py`](../tests/test_skilltree_model.py) | SkillTree-native types: camelCase field mapping, defaults, validation, nested round-trips, dependency self-loop guard, quiz question correct-flag mapping |
| [`test_skilltree_exporter.py`](../tests/test_skilltree_exporter.py) | `export_project` / `export_to_json`: subject/skill/dependency counts, edge direction, quizzes built only for `Quiz` skills with assessments, verbatim descriptions, duplicate-id guard, deterministic sorted JSON, serialized export validation |
| [`test_skilltree_summary.py`](../tests/test_skilltree_summary.py) | Export-payload summary plus fail-closed validation: duplicate ids, dangling quiz references, self-loop/cyclic dependencies, malformed collection shapes |
| [`test_skilltree_client.py`](../tests/test_skilltree_client.py) | The REST contract against a real `pytest-httpserver`: admin/subject/skill/prerequisite/quiz paths, bearer token, non-2xx → `SkillTreeClientError`, empty-body handling, HTTP-only base URLs, encoded path identifiers |
| [`test_skilltree_seeder.py`](../tests/test_skilltree_seeder.py) | `seed`: summary counts, dependencies issued only after all skills exist, exact full-path ordering — against a real local server |
| [`test_dependency_reconciler.py`](../tests/test_dependency_reconciler.py) | Live prerequisite-edge reconciliation against a real local server: heartbeat/parity callbacks, bounded `attempts_per_edge` retries, and post-timeout authoritative confirmation (a timed-out write that landed is counted as confirmed, not re-posted) |
| [`test_recommendations.py`](../tests/test_recommendations.py) | Recommend-next-skill ordering by dependency depth, with remediation/retake categories and fail-closed cycle handling |
| [`test_net_guard.py`](../tests/test_net_guard.py) | URL-scheme and loopback guards shared by local-first CLI tools (http(s)-only, loopback host checks) |
| [`test_skilltree_local_auth.py`](../tests/test_skilltree_local_auth.py) | Local SkillTree `FORM` bootstrap state, root-account/session/XSRF request shapes, trusted-client token exchange, and secret redaction |
| [`test_skilltree_form_login.py`](../tests/test_skilltree_form_login.py) | Raw SkillTree browser-login validator helpers: state redaction, Chrome command parsing, admin-surface detection, and secret-safe failures |
| [`test_form_login_core.py`](../tests/test_form_login_core.py) | `form_login_core` pure helpers: login-URL builders, AXI-result parsing, public state summary, and submission JavaScript |
| [`test_dashboard.py`](../tests/test_dashboard.py) | Dashboard payloads, read-only artifact inventory, local Learn/Open Subject/Quiz split, graph lanes/flow tables, artifact cards, and browser-facing JS/CSS contracts |
| [`test_dashboard_server.py`](../tests/test_dashboard_server.py) | Local HTTP server routes, host/origin guards, token endpoint behavior, CORS, graceful shutdown, the page Content-Security-Policy (SkillTree origin in `frame-src`, its `ws://` origin in `connect-src`), `?defer_live=1` dropping only the parity round trip, and gzip negotiation that leaves the decoded body byte-identical |
| [`test_dashboard_console.py`](../tests/test_dashboard_console.py) | Browser-console validator allow-lists expected upstream SkillTree noise and surfaces unexpected errors |
| [`test_dashboard_design.py`](../tests/test_dashboard_design.py) | Dashboard design-system token contract against `DESIGN.md` |
| [`test_dashboard_live_validation.py`](../tests/test_dashboard_live_validation.py) | Live dashboard payload/status validation against a real `pytest-httpserver` SkillTree |
| [`test_reset_local_skilltree.py`](../tests/test_reset_local_skilltree.py) | Local `docker compose` reset / strict stack proof helpers (password env, `down -v`, keep-running) |
| [`test_full_app_stack.py`](../tests/test_full_app_stack.py) | Full-app-stack orchestration helpers: postgres-password ensure, compose readiness, redacted proof artifact, and the browser-session probe that restarts a stale automation daemon once before a browser proof |
| [`test_figures.py`](../tests/test_figures.py) | Figure generators write nonblank PNGs; `render_all` emits the registered figures and required semantic metadata; typography checks reject sub-9.5px meaningful chart text outside source/caveat notes |
| [`test_roadmap.py`](../tests/test_roadmap.py) | `tasks.yaml`, generated metrics, live-count literals, generated `TODO.md`, and generated `docs/todo/` handoff pages remain current |
| [`test_docs_inventory.py`](../tests/test_docs_inventory.py) | Documentation-inventory drift checks: docs reference real figures, claims, and inventories |
| [`test_web_math.py`](../tests/test_web_math.py) | Dashboard and rendered HTML math surfaces get MathJax when needed |
| [`test_scripts_smoke.py`](../tests/test_scripts_smoke.py) | Thin-orchestrator scripts run to exit 0: curriculum, scholarship, kernels, course materials/alignment, claim support, manuscript artifacts/variables/language, web math, SkillTree export/seed skip behavior, dashboard check, and live-dashboard validator fixtures |
| [`test_project_paths.py`](../tests/test_project_paths.py) | `project_output_dirs` returns the expected output directory keys |

## Worked test examples

**Pure kernel math** (from `test_kernels_information.py`) — real arrays, analytic assertion:

```python
import numpy as np
from src.kernels.information import entropy

def test_uniform_distribution_matches_log_cardinality() -> None:
    # H(fair n-sided die) = ln(n)
    assert abs(entropy(np.ones(6) / 6) - np.log(6)) < 1e-12
```

**Curriculum DAG invariant** (from `test_curriculum_graph.py`) — a constructed graph,
asserting validation raises on a cycle and names the path:

```python
import pytest
from src.curriculum.model import CurriculumError
from src.curriculum.graph import CurriculumGraph

def test_cycle_raises_with_path() -> None:
    graph = _graph_with_cycle()  # a, b, c where c -> a
    with pytest.raises(CurriculumError, match="cycle detected"):
        graph.validate()
```

**Provenance fail-closed** (from `test_provenance.py`) — the gate must refuse an unbacked
token rather than letting a literal reach a learner:

```python
import pytest
from src.provenance.binding import ProvenanceError, render
from src.provenance.claims import ClaimRegistry

def test_render_unresolved_raises() -> None:
    with pytest.raises(ProvenanceError):
        render("value is {{claim:does_not_exist}}", ClaimRegistry())
```

## Coverage mechanics

`pyproject.toml` measures coverage only on `src/` and enforces the 90% floor:

```toml
[tool.coverage.run]
source = ["src"]

[tool.coverage.report]
fail_under = 90
```

The pyproject also sets `pythonpath = [".", "src"]` and `testpaths = ["tests"]`. Run the
authoritative gate through the single entry point:

```bash
./gates.sh test    # uv run pytest --cov=src --cov-fail-under=90 -q
./gates.sh fast    # the same suite with the `slow`-marked modules deselected
```

Lint and type gates (also part of "done"):

```bash
./gates.sh lint    # uv run ruff check src scripts tests && uv run ruff format --check ...
./gates.sh types   # uv run mypy src
```

Ruff and mypy come from the locked `dev` dependency group, so a local run and a CI run
resolve the same versions; [`gates.md`](gates.md) lists every arm.

## Zero-Mock Checklist

Before submitting any test, verify all boxes:

- [ ] Test uses real `numpy` arrays / real domain objects as inputs.
- [ ] Test calls `src/` functions directly with real data.
- [ ] Test asserts mathematical / structural properties (analytic values, DAG invariants,
      fail-closed errors), not call counts.
- [ ] No `unittest.mock`, `MagicMock`, `@patch`, or mock-framework objects.
- [ ] Any `monkeypatch` is limited to environment/orchestration or explicit failure
      injection and does not replace quantitative or HTTP protocol behavior.
- [ ] HTTP is exercised against `pytest-httpserver` (a real local server), never a mock.
- [ ] Any timing/IO assertion uses bounds, not exact magic values.

## Structural rule: if you need a mock, move the code

- **`src/kernels/*`** — pure math, deterministic, no I/O. Tested directly.
- **`src/curriculum/*`, `src/provenance/*`, `src/skilltree/{model,exporter}.py`,
  `src/figures/plots/`** — pure logic over the domain model / registry. Tested directly.
- **`src/skilltree/{client,seeder}.py`** — the only network boundary; tested against a real
  local HTTP server.
- **`scripts/*.py`** — thin orchestrators; covered by `test_scripts_smoke.py` running them
  to completion.

## Running the gate honestly

A green exit code is **not** proof the suite ran. Confirm **N collected > 0 AND coverage ≥
90%**.

```bash
./gates.sh test
```

## See also

- [`style_guide.md`](style_guide.md) — kernel purity, claim-binding, `src.*` imports
- [`syntax_guide.md`](syntax_guide.md) — the `{{claim:NAME}}` provenance-token system
- [`../AGENTS.md`](../AGENTS.md) — invariants and gates
