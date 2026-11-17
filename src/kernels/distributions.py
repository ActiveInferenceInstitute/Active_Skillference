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
    if values.ndim != 1 or not values.size or not np.all(np.isfinite(values)):
        raise ValueError("values must be a non-empty finite vector")
    if np.any(values < 0.0):
        raise ValueError("values must be non-negative")
    scale = float(np.max(values))
    if scale <= 0.0:
        raise ValueError("values must have a positive sum")
    scaled = values / scale
    return scaled / np.sum(scaled)


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

    if not np.isfinite(precision) or precision <= 0.0:
        raise ValueError("precision must be finite and > 0")
    values = np.asarray(x, dtype=np.float64)
    if values.ndim != 1 or not values.size or not np.all(np.isfinite(values)):
        raise ValueError("scores must be a non-empty finite vector")
    # Scale small precision first so centering cannot erase finite scaled mass.
    # At precision >= 1, center first to avoid overflowing large absolute scores.
    with np.errstate(over="ignore", under="ignore"):
        if precision < 1.0:
            shifted = values * precision
            shifted -= np.max(shifted)
        else:
            shifted = values - np.max(values)
            shifted *= precision
        np.exp(shifted, out=shifted)
    return shifted / np.sum(shifted)


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

    concentration = _concentrations(alpha)
    return normalize(concentration)


def dirichlet_expected_log(alpha: ArrayLike) -> FloatArray:
    """Return `E[log p]` under a Dirichlet distribution.

    Args:
        alpha: Strictly positive concentration parameters.

    Returns:
        Vector `digamma(alpha) - digamma(sum(alpha))`.

    Raises:
        ValueError: If any concentration parameter is non-positive.
    """

    concentration = _concentrations(alpha)
    scale = float(np.max(concentration))
    scaled_total = float(np.sum(concentration / scale))
    if scale > np.finfo(np.float64).max / scaled_total:
        # At this magnitude the digamma asymptotic correction is unrepresentable.
        total_digamma = np.log(scale) + np.log(scaled_total)
    else:
        total_digamma = digamma(scale * scaled_total)
    return digamma(concentration) - total_digamma


def _concentrations(alpha: ArrayLike) -> FloatArray:
    concentration = np.asarray(alpha, dtype=np.float64)
    if (
        concentration.ndim != 1
        or not concentration.size
        or not np.all(np.isfinite(concentration))
        or np.any(concentration <= 0.0)
    ):
        raise ValueError("alpha must be a non-empty vector of finite positive values")
    return concentration


__all__ = [
    "dirichlet_expected",
    "dirichlet_expected_log",
    "log_stable",
    "normalize",
    "softmax",
]
