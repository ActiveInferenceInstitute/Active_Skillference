"""Content-provenance claim registry.

The high-integrity guarantee of this platform: every quantitative value shown to
a learner in skill content was *computed by a tested kernel*, never hand-typed.

Kernels register named :class:`Claim` objects into a :class:`ClaimRegistry`.
Skill descriptions reference those values only through ``{{claim:NAME}}`` tokens
(see :mod:`src.provenance.binding`). At build time the tokens are substituted with
the registered values; an unresolved token, or a bare result number that bypassed
the registry, is a build failure.

This module is deliberately dependency-free so the kernels (:mod:`src.kernels`) can
import it without pulling in the curriculum or SkillTree layers.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

ClaimValue = int | float | str


class ClaimError(ValueError):
    """Raised on a provenance violation (duplicate, missing, or inconsistent claim)."""


@dataclass(frozen=True)
class Claim:
    """A single quantitative fact emitted by a tested kernel.

    Attributes:
        name: Stable token name referenced by skill content as ``{{claim:name}}``.
        value: The computed value (number or short string).
        units: Physical/semantic units (``""`` when dimensionless, e.g. nats).
        source: Fully-qualified name of the kernel function that produced the value.
        description: Human-readable note on what the value represents.
    """

    name: str
    value: ClaimValue
    units: str = ""
    source: str = ""
    description: str = ""

    def rendered(self) -> str:
        """Return the learner-facing string form of the value (with units if any)."""
        if isinstance(self.value, float):
            text = f"{self.value:.6g}"
        else:
            text = str(self.value)
        return f"{text} {self.units}".strip()


@dataclass
class ClaimRegistry:
    """An append-only registry of kernel-derived claims.

    Re-registering the same name with an equal value is idempotent (deterministic
    re-runs are expected). Re-registering with a *different* value raises
    :class:`ClaimError` — a non-deterministic kernel is a defect.
    """

    _claims: dict[str, Claim] = field(default_factory=dict)

    def register(
        self,
        name: str,
        value: ClaimValue,
        *,
        units: str = "",
        source: str = "",
        description: str = "",
    ) -> Claim:
        """Register a claim. Idempotent only for an *identical* re-registration.

        Two anti-laundering guards:

        * A **string** claim value may not contain a digit — numeric results must be
          numeric claims, so a hand-typed number cannot ride in as a label string.
        * Re-registration that changes the value **or the provenance metadata**
          (``source``/``units``/``description``) is rejected, so the audit trail of
          which kernel produced a value cannot be silently overwritten.
        """
        if not name:
            raise ClaimError("claim name must be non-empty")
        if isinstance(value, str) and any(ch.isdigit() for ch in value):
            raise ClaimError(
                f"string claim {name!r} value {value!r} contains a digit — numeric "
                "results must be registered as numeric claims, not embedded in a string"
            )
        claim = Claim(
            name=name, value=value, units=units, source=source, description=description
        )
        existing = self._claims.get(name)
        if existing is not None and not _claims_consistent(existing, claim):
            raise ClaimError(
                f"claim {name!r} re-registered with conflicting value/provenance: "
                f"{existing!r} != {claim!r}"
            )
        self._claims[name] = claim
        return claim

    def has(self, name: str) -> bool:
        return name in self._claims

    def get(self, name: str) -> Claim:
        try:
            return self._claims[name]
        except KeyError as exc:
            raise ClaimError(f"no registered claim named {name!r}") from exc

    def value(self, name: str) -> ClaimValue:
        return self.get(name).value

    def names(self) -> list[str]:
        return sorted(self._claims)

    def __len__(self) -> int:
        return len(self._claims)

    def __contains__(self, name: object) -> bool:
        return name in self._claims

    def as_dict(self) -> dict[str, dict[str, object]]:
        """Serialise to a plain dict suitable for JSON."""
        return {
            name: {
                "value": c.value,
                "units": c.units,
                "source": c.source,
                "description": c.description,
            }
            for name, c in sorted(self._claims.items())
        }

    def to_json(self, path: Path) -> Path:
        """Write the registry to ``path`` as deterministic, sorted JSON."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(self.as_dict(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return path


def _values_equal(a: ClaimValue, b: ClaimValue) -> bool:
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(float(a) - float(b)) <= 1e-12 + 1e-9 * abs(float(b))
    return a == b


def _claims_consistent(existing: Claim, new: Claim) -> bool:
    """A re-registration is allowed only when value AND provenance metadata match."""
    return (
        _values_equal(existing.value, new.value)
        and existing.source == new.source
        and existing.units == new.units
        and existing.description == new.description
    )
