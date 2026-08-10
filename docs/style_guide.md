# Style Guide

This document defines the coding and content style for Active Skillference. Every rule has
a concrete consequence for test correctness, reproducibility, or the platform's
defining guarantee: **provenance over assertion** — every quantitative result is produced
by a tested kernel and bound through a `{{claim:NAME}}` token, never hand-typed.

---

## 1. Kernel purity (the source of every number)

The numeric primitives in [`src/kernels/`](../src/kernels/) are the **only** place
quantitative values may be computed. They are pure, deterministic, side-effect-free
functions over discrete probability distributions, in nats:

- [`information.py`](../src/kernels/information.py) — `surprise`, `entropy`,
  `cross_entropy`, `kl_divergence`, `mutual_information`
- [`distributions.py`](../src/kernels/distributions.py) — `normalize`, `softmax`,
  `log_stable`, `dirichlet_expected`, `dirichlet_expected_log`
- [`inference.py`](../src/kernels/inference.py) — `bayes_posterior`, `log_evidence`,
  `variational_free_energy`, `elbo`
- [`active_inference.py`](../src/kernels/active_inference.py) — `expected_free_energy`,
  `policy_posterior`, `DiscreteActiveInferenceAgent`

A kernel must not do I/O, read configuration, or import the curriculum, SkillTree, or
figures layers. (**Exception:** `examples.py` imports `src.provenance.claims` only, to
register claims — kernel modules themselves stay dependency-free apart from numpy.) If a
function needs any of that, it is not a kernel — it
belongs in [`src/kernels/examples.py`](../src/kernels/examples.py) (worked examples that
*drive* the kernels) or in `scripts/` (orchestration).

**Verify kernel purity** (kernels never import the higher layers):

```bash
grep -rn "from src.curriculum\|from src.skilltree\|from src.figures" src/kernels/ \
  && echo "IMPURE KERNEL" || echo "clean"
```

---

## 2. Numbers must be claim-bound — never hand-typed

A bare result number in learner-facing prose is a provenance defect. The flow is fixed:

1. Compute the value in a kernel.
2. Emit it from a worked example in `src/kernels/examples.py` and register it in
   `build_claim_registry()`.
3. Reference it in skill content / the manuscript as `{{claim:NAME}}`.

**Forbidden** — a result typed directly into a skill description:

```python
# BAD — a laundered number; find_unbacked_numbers() flags it
Skill(
    skill_id="entropy_intro",
    description="A fair coin has entropy 0.6931 nats.",
    ...
)
```

**Correct** — the value arrives through a claim token:

```python
# GOOD — the value is bound to a tested kernel via the registry
Skill(
    skill_id="entropy_intro",
    description="A fair coin has entropy {{claim:entropy_fair_coin}}.",
    ...
)
```

…backed by an example that computes it:

```python
# src/kernels/examples.py
def info_examples() -> dict[str, float]:
    return {"entropy_fair_coin": entropy([0.5, 0.5]), ...}
```

Input numbers and parameters in prose go inside `$…$` LaTeX math (the linter excludes math
spans). Integers, years, and single-decimal probabilities are not flagged. See
[`syntax_guide.md`](syntax_guide.md)
for the precise rules.

**Verify no laundered numbers** (the export script also runs this and refuses to write):

```bash
uv run python scripts/export_skilltree.py   # runs lint_graph + render_graph, fail-closed
```

---

## 3. `src.*` imports only — no dual module identities

The project's `pyproject.toml` sets `pythonpath = [".", "src"]`, so `src/` is importable
both as the `src.*` package and (because `src` itself is on the path) as bare
`kernels.`/`curriculum.`/`skilltree.` modules. Importing the same module under two names
creates two distinct module objects — duplicate registries, broken `isinstance`, subtle
state bugs.

**Always** import under the `src.*` namespace:

```python
# GOOD
from src.curriculum.model import Skill, Subject, Stratum
from src.kernels.information import entropy
from src.provenance.claims import ClaimRegistry
```

**Forbidden**:

```python
# BAD — bare top-level import creates a second module identity
from curriculum.model import Skill
from kernels.information import entropy
```

**Verify** (no bare imports of the internal packages):

```bash
grep -rn "^from \(kernels\|curriculum\|skilltree\|provenance\|figures\)\." src scripts tests \
  && echo "BARE IMPORT" || echo "clean"
```

---

## 4. The thin-orchestrator pattern

All logic lives in `src/`; files in [`scripts/`](../scripts/) only coordinate I/O. A script
may build the registry/graph, write JSON, and render figures, but must not re-implement any
math, DAG validation, or provenance rule that belongs in `src/`.

**Forbidden** — recomputing a kernel result inside a script:

```python
# BAD — math belongs in src/kernels, not in a script
import numpy as np
entropy_value = -sum(p * np.log(p) for p in [0.5, 0.5])
```

**Correct** — the script calls the tested kernel/registry:

```python
# GOOD — import and call the tested function (see scripts/run_kernels.py)
from src.kernels.examples import build_claim_registry
registry = build_claim_registry()
value = registry.value("entropy_fair_coin")
```

**Decision rule**: if a line in a `scripts/` file computes a value that ends up in
learner-facing content, move it into `src/kernels/` (and register a claim) and write a
test for it.

---

## 5. Zero-mock policy

Mock frameworks are forbidden anywhere in [`tests/`](../tests/). The kernels are pure, so you can
always test them with real numpy arrays and real analytic results — a test that needs a
mock is testing the wrong thing (that one function *calls* another, not that the math is
correct).

**Forbidden** — `unittest.mock`, `MagicMock`, `@patch`, fabricated kernel results, or
patched HTTP transports. Narrow `pytest.monkeypatch` use is permitted for environment
isolation and explicit OS/subprocess failure branches, but it is not integration proof.

**Correct** — assert real mathematical properties (from
[`tests/test_kernels_information.py`](../tests/test_kernels_information.py)):

```python
import numpy as np
from src.kernels.information import entropy

def test_uniform_distribution_matches_log_cardinality() -> None:
    # entropy of a fair n-sided die is ln(n)
    assert abs(entropy(np.ones(6) / 6) - np.log(6)) < 1e-12
```

HTTP (the SkillTree REST client/seeder) is tested against a real local server with
`pytest-httpserver`, never a mock — see
[`tests/test_skilltree_client.py`](../tests/test_skilltree_client.py) and
[`tests/test_skilltree_seeder.py`](../tests/test_skilltree_seeder.py).

**Verify cleanliness**:

```bash
grep -rn "unittest.mock\|MagicMock\|@patch" tests/ && echo "MOCK FOUND" || echo "clean"
```

See [`testing_philosophy.md`](testing_philosophy.md) for the full standard.

---

## 6. Typed APIs and dataclasses

Follow the patterns established in [`src/curriculum/model.py`](../src/curriculum/model.py)
and [`src/provenance/claims.py`](../src/provenance/claims.py):

- `from __future__ import annotations` at the top of every module.
- Python 3.10+ union syntax: `list[float] | None`, not `Optional[List[float]]`.
- Domain objects are frozen dataclasses with validation in `__post_init__` (e.g. `Skill`,
  `Subject`, `AssessmentQuestion`, `Claim`).
- Complete type annotations on every public parameter and return value; `uv run mypy src`
  must stay clean.

**Example** (following `Claim`):

```python
@dataclass(frozen=True)
class Claim:
    name: str
    value: ClaimValue
    units: str = ""
    source: str = ""
    description: str = ""
```

---

## 7. Error messages carry the offending value

Every `ValueError` / domain error must include the problematic value so a reader can
diagnose without opening the source.

**Forbidden**:

```python
raise CurriculumError("invalid skill id")
raise ValueError("bad probability vector")
```

**Correct** (following `src/curriculum/model.py` and `src/kernels/information.py`):

```python
raise CurriculumError(
    f"skill_id {self.skill_id!r} must be alnum/underscore (SkillTree skillId rule)"
)
raise ValueError(f"{name} must be a 1D probability vector")
```

---

## 8. Repository-root anchors

When referring to files in logs, comments, or docs, use the path relative to this
project's root so the same filename in different layers is unambiguous:

| Short name | Path (from project root) |
|---|---|
| information kernel | `src/kernels/information.py` |
| active-inference kernel | `src/kernels/active_inference.py` |
| worked examples / claim registry | `src/kernels/examples.py` |
| claim registry type | `src/provenance/claims.py` |
| provenance binding + linter | `src/provenance/binding.py` |
| curriculum model | `src/curriculum/model.py` |
| DAG engine | `src/curriculum/graph.py` |
| Active Inference catalog | `src/curriculum/catalog_data/` |
| SkillTree exporter | `src/skilltree/exporter.py` |
| figures | `src/figures/plots/` |
| kernel runner (claims + figures) | `scripts/run_kernels.py` |
| curriculum builder | `scripts/build_curriculum.py` |
| SkillTree export | `scripts/export_skilltree.py` |
| manuscript config | `manuscript/config.yaml` |
| provenance ledger | `output/data/claims.json` |
| final PDF | `output/pdf/Active_Skillference_combined.pdf` |

---

## See also

- [`syntax_guide.md`](syntax_guide.md) — authoring syntax and the `{{claim:NAME}}` system
- [`testing_philosophy.md`](testing_philosophy.md) — the no-mocks testing standard
- [`rendering_pipeline.md`](rendering_pipeline.md) — manuscript → PDF flow
- [`../AGENTS.md`](../AGENTS.md) — invariants and the provenance chain
