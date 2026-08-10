# Source Code Style Guide

Code style and design conventions for `src/` modules in the Active Skillference platform.

## Pure Kernel Design

Functions in `src/kernels/` must be **side-effect-free** — inputs in, values out,
no I/O, no logging, no printing:

```python
# ✅ CORRECT: Pure function — takes input, returns a value in nats
def entropy(p: ArrayLike) -> float:
    probs = _as_probability_vector(p, name="p")
    mask = probs > 0.0
    return float(-np.sum(probs[mask] * log_stable(probs[mask])))


# ❌ WRONG: Side-effect function — prints, writes files
def entropy(p):
    print(f"Computing entropy of {p}")  # side effect: I/O
    h = -sum(x * math.log(x) for x in p if x > 0)
    Path("entropy.txt").write_text(str(h))  # side effect: file write
    return h
```

File I/O and visualisation belong in `src/figures/` and `scripts/`, not in the kernels.
`src/skilltree/client.py` is the one networked module (REST), and `src/provenance/claims.py`
writes JSON via `to_json` — those are deliberate, documented seams, not kernel behaviour.

## Type Hints

Every public function must have complete type annotations:

```python
def bayes_posterior(prior: ArrayLike, A: ArrayLike, obs: int) -> FloatArray: ...


def expected_free_energy(
    qs: ArrayLike,
    A: ArrayLike,
    C: ArrayLike,
) -> tuple[float, float, float]: ...
```

- Use the `FloatArray`/`ArrayLike` aliases (`from numpy.typing import ArrayLike, NDArray`)
  for array types, not `list` or `array`.
- Use `T | None` (not `Optional[T]`) for optionals — the codebase targets modern Python.
- Use `@dataclass(frozen=True)` for structured, immutable values (`Claim`, `Skill`, the
  SkillTree model types).
- `mypy src` must be clean.

## Docstring Format

Google-style docstrings with Args/Returns/Raises:

```python
def kl_divergence(p: ArrayLike, q: ArrayLike) -> float:
    """Return KL divergence `sum_i p_i log(p_i / q_i)` in nats.

    Zero-mass terms contribute zero, matching the standard discrete convention.

    Args:
        p: Reference probability vector.
        q: Comparison probability vector.

    Returns:
        Non-negative KL divergence `KL(p || q)`.

    Raises:
        ValueError: If either vector is invalid or if `q_i == 0` wherever `p_i > 0`.
    """
```

Units are always stated (the platform works in **nats**).

## Naming Conventions

| Element | Convention | Example |
|---------|-----------|---------|
| Functions | `snake_case` | `bayes_posterior`, `expected_free_energy` |
| Classes | `PascalCase` | `ClaimRegistry`, `CurriculumGraph`, `SkillTreeProject` |
| Constants | `UPPER_SNAKE` | `SEED`, `ALL_STRATA`, `CLAIM_TOKEN_RE` |
| Private | `_leading_underscore` | `_as_probability_vector`, `_map_skill` |
| Parameters | descriptive `snake_case` | `prior`, `obs`, `point_increment` |

SkillTree-facing field names mirror the API: Python attributes are `snake_case`
(`point_increment`), serialised payloads emit camelCase (`pointIncrement`).

## NumPy Idioms

```python
# ✅ Use vectorized operations
qo = likelihood @ state_probs

# ❌ Avoid loops over array elements
qo = np.zeros(n_obs)
for i in range(n_obs):
    qo[i] = sum(likelihood[i, j] * state_probs[j] for j in range(n_states))
```

- Prefer `@` for matrix multiplication.
- Use `np.isclose` / `np.allclose` for floating-point validation (e.g. "sums to 1").
- Mask zero-mass entries before taking logs; use `log_stable` to clip the lower bound.

## Error Handling

```python
def surprise(p: float) -> float:
    if p <= 0.0:
        raise ValueError("probability must be > 0")
    return float(-np.log(p))
```

- Validate inputs at function entry; a malformed distribution must raise, not silently
  produce a plausible-looking number (see `inference._validate_model`).
- Use `ValueError` (or the domain errors `CurriculumError`, `ProvenanceError`,
  `ClaimError`, `SkillTreeModelError`, `ExportError`) for invalid inputs.
- Include actual values in error messages for debuggability.
- Never catch and silently swallow exceptions — the provenance gates are fail-closed.

## Import Discipline (`src.*` namespace)

Every module imports under the `src.*` namespace, and the test config sets
`pythonpath = [".", "src"]`:

```python
# ✅ CORRECT — absolute src.* import
from src.curriculum.model import Skill, Subject
from src.kernels.information import entropy

# within a subpackage, a relative import is fine
from .distributions import log_stable  # inside src/kernels/information.py
```

```python
# ❌ WRONG — bare top-level import
from kernels.information import entropy  # creates a dual module identity
from curriculum.model import Skill
```

Bare imports (`kernels.`/`curriculum.`/`skilltree.`) resolve through the second path
entry and create a **second** copy of the module. The registry, the graph types, and the
SkillTree dataclasses then have two distinct identities, and `isinstance` / equality /
the provenance gate behave inconsistently. Always use `src.*` (or a relative import
inside the same subpackage). Scripts add both paths and then import `src.*` (see
[`../scripts/CONVENTIONS.md`](../scripts/CONVENTIONS.md)).

## Module Exports & Versioning

Each subpackage's `__init__.py` re-exports its public API (see `src/kernels/__init__.py`,
`src/curriculum/__init__.py`, `src/provenance/__init__.py`, `src/skilltree/__init__.py`,
`src/figures/__init__.py`). The top-level `src/__init__.py` is intentionally minimal —
it carries the package docstring and the version, not a re-export barrel:

```python
"""Active Skillference — a high-integrity micro-learning platform for Active Inference.

... (layering description) ...
"""

from __future__ import annotations

__all__ = ["__version__"]

__version__ = "1.0.0"
```

Keep `__version__` in sync with `pyproject.toml`. When you add a public symbol to a
subpackage, add it to that subpackage's `__init__.py.__all__` and reference it via
`from src.<subpackage> import <symbol>`.

## See Also

- [`AGENTS.md`](AGENTS.md) — Layering, invariants, and the module API
- [`README.md`](README.md) — Subpackage overview
- [`../tests/PATTERNS.md`](../tests/PATTERNS.md) — How to test code written here
- [`../scripts/CONVENTIONS.md`](../scripts/CONVENTIONS.md) — How scripts use this code
