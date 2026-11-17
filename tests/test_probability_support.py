"""Exact support and magnitude-independent probability boundary contracts."""

from __future__ import annotations

import numpy as np
import pytest

from src.kernels.active_inference import (
    DiscreteActiveInferenceAgent,
    expected_free_energy,
    policy_posterior,
)
from src.kernels.distributions import (
    dirichlet_expected,
    dirichlet_expected_log,
    normalize,
    softmax,
)
from src.kernels.inference import elbo, log_evidence, variational_free_energy


def test_impossible_observation_retains_exact_zero_support() -> None:
    likelihood = np.eye(2)
    assert log_evidence(likelihood, 1, [1.0, 0.0]) == -np.inf
    assert variational_free_energy([0.0, 1.0], likelihood, 1, [1.0, 0.0]) == np.inf
    assert elbo([0.0, 1.0], likelihood, 1, [1.0, 0.0]) == -np.inf
    assert variational_free_energy([1.0, 0.0], likelihood, 0, [1.0, 0.0]) == 0.0


def test_small_nonzero_evidence_is_not_epsilon_regularized() -> None:
    mass = 1e-30
    expected = np.log(mass)
    assert log_evidence(np.eye(2), 0, [mass, 1.0 - mass]) == pytest.approx(expected)
    assert variational_free_energy(
        [1.0, 0.0], np.eye(2), 0, [mass, 1.0 - mass]
    ) == pytest.approx(-expected)


def test_extreme_masses_and_policy_scores_preserve_normalization() -> None:
    np.testing.assert_allclose(normalize([1e308, 1e308]), [0.5, 0.5])
    np.testing.assert_allclose(dirichlet_expected([1e308, 1e308]), [0.5, 0.5])
    np.testing.assert_allclose(
        dirichlet_expected_log([1e308, 1e308]),
        [-np.log(2.0)] * 2,
        atol=1e-12,
        rtol=0.0,
    )
    np.testing.assert_allclose(softmax([1e308, 1e308], precision=2.0), [0.5, 0.5])
    np.testing.assert_allclose(
        policy_posterior([-1e308, -1e308], gamma=2.0), [0.5, 0.5]
    )
    np.testing.assert_allclose(softmax([-1e308, 1e308], precision=2.0), [0.0, 1.0])


@pytest.mark.parametrize("bad", [np.nan, np.inf, -np.inf])
@pytest.mark.parametrize(
    "function", [normalize, dirichlet_expected, dirichlet_expected_log]
)
def test_nonfinite_masses_are_rejected(function, bad: float) -> None:
    with pytest.raises(ValueError):
        function([bad, 1.0])


@pytest.mark.parametrize("gamma", [-1.0, 0.0, np.inf, np.nan])
def test_invalid_policy_precision_is_rejected(gamma: float) -> None:
    with pytest.raises(ValueError):
        policy_posterior([0.0, 1.0], gamma=gamma)


@pytest.mark.parametrize("belief", [[-1.0, 2.0], [0.2, 0.2], [np.nan, 1.0]])
def test_planning_rejects_invalid_state_beliefs(belief: list[float]) -> None:
    with pytest.raises(ValueError):
        expected_free_energy(belief, np.full((2, 2), 0.5), [0.5, 0.5])


def test_agent_rejects_invalid_transition_at_its_owning_boundary() -> None:
    with pytest.raises(ValueError, match="B"):
        DiscreteActiveInferenceAgent(
            A=np.eye(2),
            B=np.array([[[-1.0], [-1.0]], [[2.0], [2.0]]]),
            C=np.array([0.5, 0.5]),
            D=np.array([0.5, 0.5]),
        )


def test_prediction_rejects_out_of_range_actions_and_wrong_belief_dimension() -> None:
    agent = DiscreteActiveInferenceAgent(
        A=np.eye(2),
        B=np.eye(2)[:, :, None],
        C=np.array([0.5, 0.5]),
        D=np.array([0.5, 0.5]),
    )
    with pytest.raises(ValueError, match="action"):
        agent.predict([0.5, 0.5], -1)
    with pytest.raises(ValueError, match="dimension"):
        agent.predict([1.0], 0)
    np.testing.assert_allclose(agent.predict([0.25, 0.75], 0), [0.25, 0.75])


@pytest.mark.parametrize("action", [True, np.bool_(False), 0.5, "0", None])
def test_prediction_rejects_noninteger_action_types(action) -> None:
    agent = DiscreteActiveInferenceAgent(
        A=np.eye(2),
        B=np.eye(2)[:, :, None],
        C=np.array([0.5, 0.5]),
        D=np.array([0.5, 0.5]),
    )
    with pytest.raises(TypeError, match="action"):
        agent.predict([0.5, 0.5], action)
