"""Information-theoretic primitives for discrete probability distributions."""

from __future__ import annotations

from typing import TypeAlias

import numpy as np
from numpy.typing import ArrayLike, NDArray

from .distributions import log_stable

FloatArray: TypeAlias = NDArray[np.float64]
_PROB_TOL = 1e-9


def _as_probability_vector(x: ArrayLike, *, name: str) -> FloatArray:
    """Validate and return a one-dimensional probability vector."""

    values = np.asarray(x, dtype=np.float64)
    if values.ndim != 1:
        raise ValueError(f"{name} must be a 1D probability vector")
    if np.any(values < 0.0):
        raise ValueError(f"{name} must be non-negative and sum to 1")
    if not np.isclose(np.sum(values), 1.0, atol=_PROB_TOL, rtol=0.0):
        raise ValueError(f"{name} must sum to 1")
    return values


def _as_nonneg_vector(x: ArrayLike, *, name: str) -> FloatArray:
    """Validate and return a 1D non-negative vector that need NOT sum to one.

    Cross-entropy ``-Σ p_i ln q_i`` is well-defined for any non-negative ``q`` — the
    second argument is the *candidate* against which ``p`` is scored, e.g. a likelihood
    column ``A[obs, :]`` that legitimately does not normalize. Forcing ``q`` to sum to 1
    was an over-restriction that rejected this standard usage.
    """

    values = np.asarray(x, dtype=np.float64)
    if values.ndim != 1:
        raise ValueError(f"{name} must be a 1D vector")
    if np.any(values < 0.0):
        raise ValueError(f"{name} must be non-negative")
    return values


def surprise(p: float) -> float:
    """Return surprisal `-ln(p)` in nats.

    Args:
        p: Strictly positive probability.

    Returns:
        The surprisal associated with `p`.

    Raises:
        ValueError: If `p` is not strictly positive.
    """

    if p <= 0.0:
        raise ValueError("probability must be > 0")
    return float(-np.log(p))


def entropy(p: ArrayLike) -> float:
    """Return Shannon entropy in nats.

    Args:
        p: Probability vector summing to one.

    Returns:
        Shannon entropy `-sum_i p_i log p_i`.

    Raises:
        ValueError: If `p` is not a valid probability vector.
    """

    probs = _as_probability_vector(p, name="p")
    mask = probs > 0.0
    return float(-np.sum(probs[mask] * log_stable(probs[mask])))


def cross_entropy(p: ArrayLike, q: ArrayLike) -> float:
    """Return cross-entropy `-sum_i p_i log q_i` in nats.

    Args:
        p: Reference probability vector (must be a valid distribution).
        q: Candidate non-negative vector. It need NOT sum to one — e.g. a likelihood
            column ``A[obs, :]`` — only be positive wherever ``p`` has mass.

    Returns:
        Cross-entropy of `p` under `q`.

    Raises:
        ValueError: If `p` is not a valid distribution, `q` is negative, shapes
            differ, or `q_i == 0` for any component where `p_i > 0`.
    """

    probs = _as_probability_vector(p, name="p")
    q_probs = _as_nonneg_vector(q, name="q")
    if probs.shape != q_probs.shape:
        raise ValueError("p and q must have matching shapes")

    problematic = (probs > 0.0) & (q_probs <= 0.0)
    if np.any(problematic):
        raise ValueError("q must be strictly positive where p has positive mass")

    mask = probs > 0.0
    return float(-np.sum(probs[mask] * log_stable(q_probs[mask])))


def kl_divergence(p: ArrayLike, q: ArrayLike) -> float:
    """Return KL divergence `sum_i p_i log(p_i / q_i)` in nats.

    Zero-mass terms contribute zero, matching the standard discrete
    convention.

    Args:
        p: Reference probability vector.
        q: Comparison probability vector.

    Returns:
        Non-negative KL divergence `KL(p || q)`.

    Raises:
        ValueError: If either vector is invalid or if `q_i == 0` wherever
            `p_i > 0`.
    """

    probs = _as_probability_vector(p, name="p")
    q_probs = _as_probability_vector(q, name="q")
    if probs.shape != q_probs.shape:
        raise ValueError("p and q must have matching shapes")

    problematic = (probs > 0.0) & (q_probs <= 0.0)
    if np.any(problematic):
        raise ValueError("q must be strictly positive where p has positive mass")

    mask = probs > 0.0
    return float(
        np.sum(probs[mask] * (log_stable(probs[mask]) - log_stable(q_probs[mask])))
    )


def mutual_information(joint: ArrayLike) -> float:
    """Return mutual information for a discrete joint distribution.

    Args:
        joint: Two-dimensional probability matrix `P(x, y)` summing to one.

    Returns:
        Mutual information `I(X; Y)` in nats.

    Raises:
        ValueError: If `joint` is not a valid 2D probability matrix.
    """

    joint_probs = np.asarray(joint, dtype=np.float64)
    if joint_probs.ndim != 2:
        raise ValueError("joint must be a 2D probability matrix")
    if np.any(joint_probs < 0.0):
        raise ValueError("joint must be non-negative and sum to 1")
    if not np.isclose(np.sum(joint_probs), 1.0, atol=_PROB_TOL, rtol=0.0):
        raise ValueError("joint must sum to 1")

    px = np.sum(joint_probs, axis=1, keepdims=True)
    py = np.sum(joint_probs, axis=0, keepdims=True)
    denominator = px * py
    mask = joint_probs > 0.0
    return float(
        np.sum(
            joint_probs[mask]
            * (log_stable(joint_probs[mask]) - log_stable(denominator[mask]))
        )
    )


__all__ = [
    "cross_entropy",
    "entropy",
    "kl_divergence",
    "mutual_information",
    "surprise",
]
