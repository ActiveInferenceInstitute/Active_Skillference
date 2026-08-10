"""Tests for active inference planning kernels and agent loop."""

from __future__ import annotations

import numpy as np
import pytest
from numpy.testing import assert_allclose

from src.kernels.active_inference import (
    DiscreteActiveInferenceAgent,
    expected_free_energy,
    policy_posterior,
)
from src.kernels.distributions import softmax

ATOL = 1e-9


def _informative_agent() -> DiscreteActiveInferenceAgent:
    """Construct a small agent with informative vs ambiguous successor states."""
    A = np.array(
        [
            [1.0, 0.0, 0.5, 0.5],
            [0.0, 1.0, 0.5, 0.5],
        ],
        dtype=np.float64,
    )
    B = np.zeros((4, 4, 2), dtype=np.float64)
    B[:, :, 0] = np.eye(4, dtype=np.float64)
    B[:, :, 1] = np.array(
        [
            [0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0],
            [1.0, 0.0, 1.0, 0.0],
            [0.0, 1.0, 0.0, 1.0],
        ],
        dtype=np.float64,
    )
    C = np.array([0.5, 0.5], dtype=np.float64)
    D = np.array([0.5, 0.5, 0.0, 0.0], dtype=np.float64)
    return DiscreteActiveInferenceAgent(A=A, B=B, C=C, D=D)


class TestExpectedFreeEnergy:
    """Tests for expected_free_energy()."""

    def test_returns_non_negative_epistemic_value(self) -> None:
        """The epistemic value is an expected KL divergence and must be non-negative."""
        agent = _informative_agent()
        qs = np.array([0.5, 0.5, 0.0, 0.0], dtype=np.float64)
        G, epistemic, pragmatic = expected_free_energy(qs, agent.A, agent.C)
        assert epistemic >= -ATOL
        assert abs(G + epistemic + pragmatic) < ATOL

    def test_epistemic_value_equals_state_observation_mutual_information(self) -> None:
        """Non-vacuous numeric check (ISC-131): with A fully informative over the two
        active states and a uniform belief, observing o perfectly disambiguates the
        state, so the epistemic value equals the mutual information I(s;o) = H(qs) = ln 2.
        A non-negativity assert alone passes by identity; this pins the computed value."""
        agent = _informative_agent()
        qs = np.array([0.5, 0.5, 0.0, 0.0], dtype=np.float64)
        _, epistemic, _ = expected_free_energy(qs, agent.A, agent.C)
        assert epistemic == pytest.approx(float(np.log(2.0)), abs=1e-9)

    def test_normalizes_preferences_defensively(self) -> None:
        """C should be normalized internally before computing pragmatic value."""
        agent = _informative_agent()
        qs = np.array([0.5, 0.5, 0.0, 0.0], dtype=np.float64)
        _, _, pragmatic = expected_free_energy(
            qs, agent.A, np.array([2.0, 2.0], dtype=np.float64)
        )
        assert abs(pragmatic - np.log(0.5)) < ATOL


class TestPolicyPosterior:
    """Tests for policy_posterior()."""

    def test_matches_softmax_of_negative_gamma_times_g(self) -> None:
        """policy_posterior(G) should equal softmax(-gamma * G)."""
        G = np.array([0.1, 0.7, -0.2], dtype=np.float64)
        gamma = 2.5
        assert_allclose(
            policy_posterior(G, gamma=gamma),
            softmax(-gamma * G),
            atol=ATOL,
            rtol=ATOL,
        )

    def test_lower_g_action_gets_higher_probability(self) -> None:
        """Lower expected free energy should imply a higher posterior policy mass."""
        posterior = policy_posterior(np.array([0.2, 1.1], dtype=np.float64))
        assert posterior[0] > posterior[1]


class TestDiscreteActiveInferenceAgent:
    """Tests for the one-step active inference agent."""

    def test_information_seeking_action_has_lower_g_when_uncertain(self) -> None:
        """A more informative action should be preferred under state uncertainty."""
        agent = _informative_agent()
        qs = np.array([0.5, 0.5, 0.0, 0.0], dtype=np.float64)
        G = agent.evaluate_policies(qs)
        assert G[0] < G[1]

    def test_act_is_deterministic_with_seeded_rng(self) -> None:
        """Sampling from the policy posterior should be reproducible with fixed seeds."""
        agent = _informative_agent()
        rng_a = np.random.default_rng(99)
        rng_b = np.random.default_rng(99)
        action_a = agent.act(obs=0, gamma=4.0, rng=rng_a)
        action_b = agent.act(obs=0, gamma=4.0, rng=rng_b)
        assert action_a == action_b

    def test_multistep_rollout_runs_and_returns_a_trajectory(self) -> None:
        """A short closed-loop rollout should execute without errors."""
        agent = _informative_agent()
        rng = np.random.default_rng(7)
        observation = 0
        trajectory: list[dict[str, int | np.ndarray]] = []
        latent_state = 0

        for _ in range(3):
            posterior = agent.infer_states(observation)
            action = agent.act(observation, gamma=3.0, rng=rng)
            predicted = agent.predict(posterior, action)
            latent_transition = agent.B[:, latent_state, action]
            latent_state = int(rng.choice(len(latent_transition), p=latent_transition))
            observation = int(rng.choice(agent.A.shape[0], p=agent.A[:, latent_state]))
            trajectory.append(
                {
                    "observation": observation,
                    "action": action,
                    "latent_state": latent_state,
                    "predicted": predicted,
                }
            )

        assert len(trajectory) == 3
        for step in trajectory:
            assert step["action"] in (0, 1)
            assert_allclose(np.sum(step["predicted"]), 1.0, atol=ATOL)


def _two_action_agent(sensor_p: float) -> DiscreteActiveInferenceAgent:
    """Neutral-preference 2-state agent: action 0 = sample (keep belief), 1 = commit."""
    A = np.array([[sensor_p, 1 - sensor_p], [1 - sensor_p, sensor_p]])
    B = np.zeros((2, 2, 2))
    B[:, :, 0] = np.eye(2)
    B[:, :, 1] = np.array([[0.95, 0.95], [0.05, 0.05]])
    C = np.array([0.5, 0.5])  # neutral: epistemic value alone decides
    D = np.array([0.5, 0.5])
    return DiscreteActiveInferenceAgent(A=A, B=B, C=C, D=D)


def test_epistemic_preference_holds_in_moderate_precision_regime() -> None:
    """Science (falsification): with NEUTRAL preferences, the information-seeking
    'sample' action has lower expected free energy across the moderate-precision
    regime — this is the regime the worked example (p=0.9) sits in."""
    for sensor_p in (0.6, 0.7, 0.8, 0.9):
        agent = _two_action_agent(sensor_p)
        g = agent.evaluate_policies(agent.infer_states(obs=0))
        assert g[0] < g[1], f"expected sample preferred at p={sensor_p}"


def test_epistemic_preference_is_regime_dependent_not_a_universal_law() -> None:
    """Science (honest characterization): the preference is NOT unconditional. At very
    high sensor precision the epistemic advantage of sampling vanishes and the agent
    no longer strictly prefers it — so curriculum content must not claim it 'always'
    prefers information-seeking. Guards against silent over-generalization."""
    g_high = _two_action_agent(0.99).evaluate_policies(
        _two_action_agent(0.99).infer_states(obs=0)
    )
    assert g_high[0] >= g_high[1]  # preference does NOT hold at p=0.99
