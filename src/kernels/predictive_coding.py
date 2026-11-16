"""Continuous-state predictive coding: gradient descent on a Gaussian free energy.

Predictive coding is the continuous-state face of the Free Energy Principle. A
single hierarchical level holds a Gaussian prior over a latent cause and a Gaussian
likelihood for the sensory observation; inference *descends* the free energy by
following precision-weighted prediction errors until they balance. For the linear
Gaussian case the descent has an exact fixed point — the analytic posterior mean —
so the iterative estimate can be cross-checked against a closed form (the
non-vacuous oracle the tests assert).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

FloatArray = NDArray[np.float64]


def gaussian_posterior_mean(
    observation: float,
    prior_mean: float,
    prior_variance: float,
    obs_variance: float,
) -> float:
    """Return the exact Gaussian posterior mean (precision-weighted combination).

    For ``x ~ N(prior_mean, prior_variance)`` and ``y | x ~ N(x, obs_variance)`` the
    posterior over ``x`` is Gaussian with mean
    ``(y/obs_variance + prior_mean/prior_variance) / (1/obs_variance + 1/prior_variance)``
    — each source weighted by its precision (inverse variance). This is the fixed
    point predictive-coding descent converges to.
    """

    if prior_variance <= 0.0 or obs_variance <= 0.0:
        raise ValueError("variances must be strictly positive")
    obs_precision = 1.0 / obs_variance
    prior_precision = 1.0 / prior_variance
    return (observation * obs_precision + prior_mean * prior_precision) / (
        obs_precision + prior_precision
    )


@dataclass(frozen=True)
class PredictiveCodingResult:
    """Outcome of a predictive-coding descent."""

    trajectory: FloatArray  # estimate at each step (length steps + 1)
    free_energy: FloatArray  # free energy at each step
    estimate: float  # final estimate
    sensory_prediction_error: float  # y - final estimate
    prior_prediction_error: float  # final estimate - prior_mean
    steps_to_converge: int  # first update <= tolerance, or steps if none qualifies


def gaussian_free_energy(
    estimate: float,
    observation: float,
    prior_mean: float,
    prior_variance: float,
    obs_variance: float,
) -> float:
    """Return the (variational) free energy of a point estimate, in nats.

    ``F = 0.5 * [ (y - x)^2 / obs_variance + (x - prior_mean)^2 / prior_variance ]``
    plus a constant that is dropped (it does not affect the descent or the minimizer).
    """

    sensory = (observation - estimate) ** 2 / obs_variance
    prior = (estimate - prior_mean) ** 2 / prior_variance
    return 0.5 * float(sensory + prior)


def predictive_coding_descent(
    observation: float,
    prior_mean: float,
    prior_variance: float,
    obs_variance: float,
    *,
    rate: float = 0.1,
    steps: int = 200,
    tolerance: float = 1e-6,
    start: float | None = None,
) -> PredictiveCodingResult:
    """Minimize the Gaussian free energy by precision-weighted prediction-error descent.

    The update follows the negative gradient
    ``dF/dx = -(y - x)/obs_variance + (x - prior_mean)/prior_variance``:

        x <- x + rate * [ (y - x)/obs_variance - (x - prior_mean)/prior_variance ]

    which is exactly "settle the latent estimate by balancing the sensory prediction
    error against the prior prediction error, each weighted by its precision". The
    fixed point is the analytic posterior mean (asserted in the tests).

    Args:
        observation: The sensory observation ``y``.
        prior_mean: Prior expectation of the latent cause.
        prior_variance: Prior variance (inverse prior precision), > 0.
        obs_variance: Observation variance (inverse sensory precision), > 0.
        rate: Positive learning rate for the gradient step.
        steps: Number of descent steps.
        tolerance: Threshold on absolute update magnitude, not fixed-point distance.
        start: Initial estimate (defaults to the prior mean).

    Returns:
        A :class:`PredictiveCodingResult` with all ``steps + 1`` trajectory and
        free-energy samples, the final estimate and prediction errors, and the
        first step whose absolute update is at most ``tolerance``. If no update
        qualifies, ``steps_to_converge`` is ``steps``; the trajectory is never
        truncated when the threshold is reached.
    """

    if prior_variance <= 0.0 or obs_variance <= 0.0:
        raise ValueError("variances must be strictly positive")
    if rate <= 0.0:
        raise ValueError("rate must be > 0")
    if steps < 1:
        raise ValueError("steps must be at least 1")

    estimate = prior_mean if start is None else float(start)
    trajectory = np.empty(steps + 1, dtype=np.float64)
    free_energy = np.empty(steps + 1, dtype=np.float64)
    trajectory[0] = estimate
    free_energy[0] = gaussian_free_energy(
        estimate, observation, prior_mean, prior_variance, obs_variance
    )
    steps_to_converge = steps
    # This update-magnitude diagnostic is independent of the analytic target.
    # It records the first qualifying step but does not stop the trajectory.
    converged = False
    for step in range(1, steps + 1):
        sensory_error = (observation - estimate) / obs_variance
        prior_error = (estimate - prior_mean) / prior_variance
        update = rate * (sensory_error - prior_error)
        estimate = estimate + update
        trajectory[step] = estimate
        free_energy[step] = gaussian_free_energy(
            estimate, observation, prior_mean, prior_variance, obs_variance
        )
        if not converged and abs(update) <= tolerance:
            steps_to_converge = step
            converged = True

    return PredictiveCodingResult(
        trajectory=trajectory,
        free_energy=free_energy,
        estimate=float(estimate),
        sensory_prediction_error=float(observation - estimate),
        prior_prediction_error=float(estimate - prior_mean),
        steps_to_converge=steps_to_converge,
    )


__all__ = [
    "PredictiveCodingResult",
    "gaussian_free_energy",
    "gaussian_posterior_mean",
    "predictive_coding_descent",
]
