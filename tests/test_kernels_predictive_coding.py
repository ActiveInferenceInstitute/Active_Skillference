"""Tests for the continuous-state predictive-coding kernel.

The non-vacuous oracle is the closed-form Gaussian posterior: the iterative
prediction-error descent must converge to the analytic precision-weighted mean, so
a descent bug (wrong gradient, wrong precision weighting) breaks a test rather than
silently shifting a learner-facing claim.
"""

from __future__ import annotations

import numpy as np
import pytest

from src.kernels.predictive_coding import (
    gaussian_free_energy,
    gaussian_posterior_mean,
    predictive_coding_descent,
)


def test_posterior_mean_is_precision_weighted_combination() -> None:
    # y=2 (var 0.5, precision 2), prior mean 0 (var 1, precision 1):
    # (2*2 + 0*1) / (2 + 1) = 4/3.
    assert gaussian_posterior_mean(2.0, 0.0, 1.0, 0.5) == pytest.approx(4.0 / 3.0)
    # A flat (very vague) prior leaves the estimate at the observation.
    assert gaussian_posterior_mean(5.0, 0.0, 1e9, 0.5) == pytest.approx(5.0, abs=1e-6)
    # A razor-sharp prior pins the estimate at the prior mean.
    assert gaussian_posterior_mean(5.0, 1.0, 1e-9, 0.5) == pytest.approx(1.0, abs=1e-6)


def test_descent_converges_to_analytic_posterior() -> None:
    result = predictive_coding_descent(2.0, 0.0, 1.0, 0.5, rate=0.1, steps=400)
    analytic = gaussian_posterior_mean(2.0, 0.0, 1.0, 0.5)
    assert result.estimate == pytest.approx(analytic, abs=1e-6)
    assert 0 < result.steps_to_converge < 400


def test_free_energy_descends_monotonically() -> None:
    result = predictive_coding_descent(2.0, 0.0, 1.0, 0.5, rate=0.1, steps=200)
    diffs = np.diff(result.free_energy)
    assert np.all(diffs <= 1e-12)
    # The free energy at the converged estimate is the analytic minimum.
    analytic = gaussian_posterior_mean(2.0, 0.0, 1.0, 0.5)
    fmin = gaussian_free_energy(analytic, 2.0, 0.0, 1.0, 0.5)
    assert result.free_energy[-1] == pytest.approx(fmin, abs=1e-6)


def test_prediction_errors_balance_at_convergence() -> None:
    """At the fixed point the precision-weighted errors are equal (the descent's stop)."""
    result = predictive_coding_descent(2.0, 0.0, 1.0, 0.5, rate=0.1, steps=400)
    # epsilon_o / obs_variance == epsilon_p / prior_variance.
    assert result.sensory_prediction_error / 0.5 == pytest.approx(
        result.prior_prediction_error / 1.0, abs=1e-5
    )


def test_descent_converges_from_any_start() -> None:
    analytic = gaussian_posterior_mean(2.0, 0.0, 1.0, 0.5)
    for start in (-10.0, 0.0, 10.0):
        result = predictive_coding_descent(
            2.0, 0.0, 1.0, 0.5, rate=0.1, steps=500, start=start
        )
        assert result.estimate == pytest.approx(analytic, abs=1e-6), start


def test_rejects_nonpositive_variance_and_rate() -> None:
    with pytest.raises(ValueError):
        gaussian_posterior_mean(2.0, 0.0, 0.0, 0.5)
    with pytest.raises(ValueError):
        predictive_coding_descent(2.0, 0.0, 1.0, 0.5, rate=0.0)
    with pytest.raises(ValueError):
        predictive_coding_descent(2.0, 0.0, -1.0, 0.5)


def test_registry_exposes_predictive_coding_claims() -> None:
    from src.kernels.examples import build_claim_registry

    reg = build_claim_registry()
    assert reg.value("pc_posterior_estimate") == pytest.approx(4.0 / 3.0, abs=1e-5)
    assert reg.value("pc_observation") == pytest.approx(2.0)
    # The two prediction errors are the residuals against observation and prior.
    assert reg.value("pc_sensory_prediction_error") == pytest.approx(
        2.0 / 3.0, abs=1e-5
    )
    assert reg.value("pc_prior_prediction_error") == pytest.approx(4.0 / 3.0, abs=1e-5)
