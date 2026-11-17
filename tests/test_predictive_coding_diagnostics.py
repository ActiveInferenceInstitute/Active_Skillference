"""The update-threshold diagnostic does not certify distance to the fixed point."""

import numpy as np
import pytest

from src.kernels.predictive_coding import (
    gaussian_posterior_mean,
    predictive_coding_descent,
)


def test_small_update_can_qualify_far_from_the_analytic_target() -> None:
    result = predictive_coding_descent(
        observation=10.0,
        prior_mean=0.0,
        prior_variance=1.0,
        obs_variance=1.0,
        rate=1e-9,
        steps=3,
        tolerance=1e-6,
    )
    target = gaussian_posterior_mean(10.0, 0.0, 1.0, 1.0)
    assert target == pytest.approx(5.0)
    assert result.steps_to_converge == 1
    assert abs(result.estimate - target) > 4.0
    assert result.trajectory.shape == (4,)
    assert result.estimate == result.trajectory[-1]
    assert np.all(np.diff(result.trajectory) > 0.0)


def test_no_qualifying_update_retains_steps_sentinel_and_full_trajectory() -> None:
    result = predictive_coding_descent(
        observation=10.0,
        prior_mean=0.0,
        prior_variance=1.0,
        obs_variance=1.0,
        rate=0.1,
        steps=2,
        tolerance=1e-12,
    )
    np.testing.assert_allclose(result.trajectory, [0.0, 1.0, 1.8])
    assert result.steps_to_converge == 2
    assert result.estimate == pytest.approx(1.8)
