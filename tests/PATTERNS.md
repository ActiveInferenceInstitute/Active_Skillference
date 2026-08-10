# Test Patterns Reference

Testing conventions for Active Skillference's zero-mock test suite. Every test exercises
real computation; the single REST boundary is tested against a real local server.

## Zero-Mock Enforcement

The following are **strictly forbidden** anywhere in this project:

- `unittest.mock`, `MagicMock`, `create_autospec`, `@patch`, or any other mock factory
- Synthetic result objects created solely to satisfy a type shape without running the kernel
- Replacing algorithm bodies so a test never runs the real math

Every test must exercise the real algorithm with real data. The one network boundary — the
SkillTree REST client (`src/skilltree/client.py`) and seeder (`src/skilltree/seeder.py`) —
is tested with **`pytest-httpserver`**: a real local HTTP server whose handlers assert the
exact request path, method, headers, and body. The socket boundary is real and the
`requests` client is not patched.

## Imports and fixtures

Imports use the `src.*` namespace, matching `pythonpath = [".", "src"]`:

```python
from src.kernels.information import entropy, kl_divergence
from src.curriculum.graph import CurriculumGraph
from src.provenance.binding import render, ProvenanceError
```

`conftest.py` forces `MPLBACKEND=Agg` (headless figures) and puts `src/` and the repo root
on `sys.path` so the documented `uv run pytest tests/` command works from a clean
environment. Build real fixtures from the catalog/registry, never synthetic collaborators:

```python
from src.curriculum.catalog import build_curriculum
from src.kernels.examples import build_claim_registry

graph = build_curriculum()  # the real validated DAG
registry = build_claim_registry()  # the real claim registry
```

## Asserting kernel identities (real math)

Kernel tests assert closed-form identities and inequalities, not hand-typed expected
numbers. From `test_kernels_information.py`:

```python
import numpy as np
from src.kernels.information import entropy, kl_divergence, cross_entropy

ATOL = 1e-9


def test_uniform_entropy_is_log_cardinality():
    probs = np.full(5, 0.2, dtype=np.float64)
    assert abs(entropy(probs) - np.log(5.0)) < ATOL  # H(uniform_n) = ln n


def test_kl_is_zero_for_identical_distributions():
    p = np.array([0.2, 0.3, 0.5], dtype=np.float64)
    assert abs(kl_divergence(p, p)) < ATOL


def test_kl_is_non_negative():  # Gibbs' inequality
    rng = np.random.default_rng(12345)
    for _ in range(8):
        p = rng.random(4)
        p /= p.sum()
        q = rng.random(4)
        q /= q.sum()
        assert kl_divergence(p, q) >= -ATOL


def test_cross_entropy_equals_entropy_plus_kl():  # H(p,q) = H(p) + KL(p||q)
    p = np.array([0.2, 0.3, 0.5])
    q = np.array([0.1, 0.4, 0.5])
    assert abs(cross_entropy(p, q) - (entropy(p) + kl_divergence(p, q))) < ATOL
```

Prefer identities (`H(uniform)=ln n`, `KL(p‖p)=0`, `KL≥0`, `H(p,q)=H(p)+KL(p‖q)`) over a
literal expected value — they verify the math, not a transcription.

## Tolerances

```python
ATOL = 1e-9  # information-theory identities are exact up to float round-off
```

- Use `abs(value - expected) < ATOL` for scalars and `np.testing.assert_allclose` for arrays.
- The active-inference agent has a deliberately **regime-dependent** epistemic preference;
  assert the property that holds in the tested regime, and have a companion test that shows
  it is *not* a universal law (see `test_kernels_active_inference.py`).

## DAG validation (fail-loud structural tests)

A deliberately malformed graph fixture must raise `CurriculumError`. From
`test_curriculum_graph.py`:

```python
import pytest
from src.curriculum.graph import CurriculumGraph
from src.curriculum.model import CurriculumError


def test_cycle_raises_with_path():
    g = _graph(
        _skill("a", _M, ("c",)), _skill("b", _M, ("a",)), _skill("c", _M, ("b",))
    )  # a → c → b → a
    with pytest.raises(CurriculumError, match="cycle"):
        g.validate()


def test_dangling_prerequisite_raises():
    g = _graph(_skill("a", _M, ("missing",)))
    with pytest.raises(CurriculumError, match="dangling"):
        g.validate()
```

Also assert the positive structural properties: topological order respects prerequisites,
levels increase along a chain, and `is_connected_foundations_to_applications()` is
**fail-closed** (returns `False`, not a vacuous pass, when there are no foundational roots).

## Provenance: render, fail closed, lint

A dangling `{{claim:NAME}}` token must fail closed — never render a placeholder. From
`test_provenance.py`:

```python
from src.provenance.binding import render, find_unbacked_numbers, ProvenanceError
from src.provenance.claims import ClaimRegistry


def test_render_substitutes_a_backed_claim():
    reg = ClaimRegistry()
    reg.register("e", 0.6931, units="nats")
    out = render("entropy is {{claim:e}}.", reg)
    assert "0.6931 nats" in out and "{{claim" not in out


def test_render_fails_closed_on_unbacked_token():
    with pytest.raises(ProvenanceError, match="unresolved"):
        render("value {{claim:ghost}}", ClaimRegistry())


def test_linter_flags_hand_typed_result_number():
    skill = _skill("planted", "The free energy is 1.6094 nats, obviously.")
    violations = find_unbacked_numbers(skill)
    assert [v.value for v in violations] == ["1.6094"]  # bare result number → violation
```

The linter scans every **learner-facing** expository field (name, objective, description,
assessment prompt) plus correct assessment answers, ignores numbers inside `$…$` LaTeX
math and single-decimal parameters like `0.5`, and intentionally ignores hand-authored
wrong distractors. It catches scientific notation and `>=2`-decimal result shapes.
`render_graph` / `validate_curriculum` fail closed on a malformed (`{{claim:}}`) or
unbacked token anywhere in the graph.

## REST boundary: pytest-httpserver

Assert the actual HTTP contract against a real server. From `test_skilltree_client.py`:

```python
from pytest_httpserver import HTTPServer
from src.skilltree.client import SkillTreeClient, SkillTreeClientError


def test_create_project_hits_admin_path_with_bearer(httpserver: HTTPServer):
    client = SkillTreeClient(
        base_url=httpserver.url_for("").rstrip("/"),
        project_id="active_inference",
        token="secret-token",
    )
    httpserver.expect_request(
        "/admin/projects/active_inference",
        method="POST",
        headers={"Authorization": "Bearer secret-token"},
    ).respond_with_json({"ok": True})
    assert client.create_project("Active Inference") == {"ok": True}


def test_non_2xx_raises_client_error(httpserver: HTTPServer):
    httpserver.expect_request(
        "/admin/projects/active_inference", method="POST"
    ).respond_with_data("boom", status=500)
    with pytest.raises(SkillTreeClientError) as exc:
        SkillTreeClient(
            base_url=httpserver.url_for("").rstrip("/"), project_id="active_inference"
        ).create_project("x")
    assert exc.value.status == 500 and exc.value.body == "boom"
```

Use `respond_with_handler` to assert the request body (e.g. `{"userId": "user-42"}` for
`report_skill`). The seeder tests use the same server to assert the **ordering** of calls
(all skills created before dependencies are assigned).

## Test class / function organisation

- Kernel and SkillTree-model tests group methods under `Test{FunctionOrClass}` classes
  (`TestEntropy`, `TestSurprise`, `TestExpectedFreeEnergy`, …).
- Graph, catalog, provenance, and smoke tests use module-level `test_*` functions.
- Each test has a docstring stating the property under test.
- Error-path tests always use `pytest.raises(..., match=...)` to pin the message content.

## Determinism

- **Fixed inputs preferred** — kernels are deterministic; use explicit numpy arrays.
- **Seed any RNG** — Gibbs'-inequality sampling uses `np.random.default_rng(12345)`.
- The claim registry and the SkillTree JSON export are byte-deterministic (sorted keys);
  `test_skilltree_exporter.py` asserts the exact JSON, and `test_kernels_examples.py`
  asserts the registry is reproducible.

## Coverage Verification

```bash
# Enforced gate (floor 90%, from the project root)
uv run pytest tests/ --cov=src --cov-report=term-missing --cov-fail-under=90

# HTML report for local exploration
uv run pytest tests/ --cov=src --cov-report=html
```

Use the coverage command output as the source of truth for current coverage. Do not delete
tests to make a coverage number work — fix the gap.

## See Also

- [README.md](README.md) — test-suite overview and the full file inventory
- [AGENTS.md](AGENTS.md) — agent guide, test inventory diagram, run commands
- [../src/kernels/information.py](../src/kernels/information.py) — information-theory kernels under test
- [../src/provenance/binding.py](../src/provenance/binding.py) — claim-token render/lint gate under test
- [../scripts/build_curriculum.py](../scripts/build_curriculum.py) — curriculum smoke entry in `test_scripts_smoke.py`
- [../scripts/run_kernels.py](../scripts/run_kernels.py) — kernel/claims smoke entry in `test_scripts_smoke.py`
