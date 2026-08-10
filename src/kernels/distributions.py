"""Distribution helpers for discrete probabilistic kernels."""

from __future__ import annotations

from typing import TypeAlias

import numpy as np
from numpy.typing import ArrayLike, NDArray
from scipy.special import digamma

FloatArray: TypeAlias = NDArray[np.float64]


def normalize(x: ArrayLike) -> FloatArray:
    """Normalize a non-negative vector into a probability vector.

    Args:
        x: Non-negative vector of unnormalized mass values.

    Returns:
        Normalized probability vector whose entries sum to one.

    Raises:
        ValueError: If any entry is negative or the sum is not strictly positive.
    """

    values = np.asarray(x, dtype=np.float64)
    if np.any(values < 0.0):
        raise ValueError("values must be non-negative")

    total = float(np.sum(values))
    if total <= 0.0:
        raise ValueError("values must have a positive sum")

    return values / total


def softmax(x: ArrayLike, precision: float = 1.0) -> FloatArray:
    """Return a numerically stable softmax distribution.

    `precision` is the inverse temperature: higher values make the posterior
    sharper around the largest entry of `x`.

    Args:
        x: Input score vector.
        precision: Positive inverse-temperature scaling.

    Returns:
        Softmax probabilities over the entries of `x`.

    Raises:
        ValueError: If precision is not strictly positive.
    """

    if precision <= 0.0:
        raise ValueError("precision must be > 0")

    values = np.asarray(x, dtype=np.float64)
    scaled = precision * values
    shifted = scaled - np.max(scaled)
    exp_shifted = np.exp(shifted)
    return exp_shifted / np.sum(exp_shifted)


def log_stable(x: ArrayLike, eps: float = 1e-16) -> FloatArray:
    """Return elementwise logs after clipping the lower bound to `eps`.

    Args:
        x: Array-like input values.
        eps: Positive lower clip bound.

    Returns:
        Elementwise natural logarithm of `clip(x, eps, None)`.
    """

    values = np.asarray(x, dtype=np.float64)
    clipped = np.clip(values, eps, None)
    return np.log(clipped)


def dirichlet_expected(alpha: ArrayLike) -> FloatArray:
    """Return the mean of a Dirichlet distribution.

    Args:
        alpha: Strictly positive concentration parameters.

    Returns:
        Mean probability vector `alpha / sum(alpha)`.

    Raises:
        ValueError: If any concentration parameter is non-positive.
    """

    concentration = np.asarray(alpha, dtype=np.float64)
    if np.any(concentration <= 0.0):
        raise ValueError("alpha must be strictly positive")
    return concentration / np.sum(concentration)


def dirichlet_expected_log(alpha: ArrayLike) -> FloatArray:
    """Return `E[log p]` under a Dirichlet distribution.

    Args:
        alpha: Strictly positive concentration parameters.

    Returns:
        Vector `digamma(alpha) - digamma(sum(alpha))`.

    Raises:
        ValueError: If any concentration parameter is non-positive.
    """

    concentration = np.asarray(alpha, dtype=np.float64)
    if np.any(concentration <= 0.0):
        raise ValueError("alpha must be strictly positive")
    return digamma(concentration) - digamma(np.sum(concentration))


__all__ = [
    "dirichlet_expected",
    "dirichlet_expected_log",
    "log_stable",
    "normalize",
    "softmax",
]
