"""Tests for discrete Bayesian and variational inference kernels."""

from __future__ import annotations

import numpy as np
import pytest
from numpy.testing import assert_allclose

from src.kernels.inference import (
    bayes_posterior,
    elbo,
    log_evidence,
    variational_free_energy,
)

ATOL = 1e-9


def _example_model() -> tuple[np.ndarray, np.ndarray]:
    """Return a small likelihood matrix and prior for exact checks."""
    A = np.array(
        [
            [0.9, 0.2],
            [0.1, 0.8],
        ],
        dtype=np.float64,
    )
    prior = np.array([0.6, 0.4], dtype=np.float64)
    return A, prior


class TestBayesPosterior:
    """Tests for bayes_posterior()."""

    def test_matches_manual_bayes_rule(self) -> None:
        """The posterior should match exact Bayes normalization."""
        A, prior = _example_model()
        posterior = bayes_posterior(prior, A, obs=0)
        expected = np.array([0.9 * 0.6, 0.2 * 0.4], dtype=np.float64)
        expected = expected / expected.sum()
        assert_allclose(posterior, expected, atol=ATOL, rtol=ATOL)

    def test_rejects_out_of_range_observation_index(self) -> None:
        """Observation indices must be within the rows of A."""
        A, prior = _example_model()
        with pytest.raises(ValueError, match="obs index"):
            bayes_posterior(prior, A, obs=3)


class TestVariationalBounds:
    """Tests for variational_free_energy(), log_evidence(), and elbo()."""

    def test_free_energy_is_tight_at_exact_posterior(self) -> None:
        """F(q*) should equal -log evidence at the exact posterior."""
        A, prior = _example_model()
        posterior = bayes_posterior(prior, A, obs=1)
        free_energy = variational_free_energy(posterior, A, obs=1, prior=prior)
        evidence = log_evidence(A, obs=1, prior=prior)
        assert abs(free_energy + evidence) < ATOL

    def test_free_energy_upper_bounds_surprise_for_random_q(self) -> None:
        """F(q) should be at least the observation surprise for arbitrary q."""
        A, prior = _example_model()
        evidence = log_evidence(A, obs=0, prior=prior)
        rng = np.random.default_rng(20240609)
        for _ in range(8):
            q = rng.random(2)
            q = q / q.sum()
            free_energy = variational_free_energy(q, A, obs=0, prior=prior)
            assert free_energy + evidence >= -ATOL

    def test_elbo_lower_bounds_log_evidence_for_random_q(self) -> None:
        """ELBO(q) should not exceed log evidence."""
        A, prior = _example_model()
        evidence = log_evidence(A, obs=1, prior=prior)
        rng = np.random.default_rng(314159)
        for _ in range(8):
            q = rng.random(2)
            q = q / q.sum()
            assert elbo(q, A, obs=1, prior=prior) <= evidence + ATOL

    def test_elbo_is_negative_free_energy(self) -> None:
        """ELBO should be the negative variational free energy."""
        A, prior = _example_model()
        q = np.array([0.7, 0.3], dtype=np.float64)
        free_energy = variational_free_energy(q, A, obs=0, prior=prior)
        assert abs(elbo(q, A, obs=0, prior=prior) + free_energy) < ATOL

    def test_rejects_invalid_probability_vector_inputs(self) -> None:
        """Inference functions should reject malformed priors or q vectors."""
        A, prior = _example_model()
        with pytest.raises(ValueError, match="sum to 1"):
            bayes_posterior(np.array([0.8, 0.8], dtype=np.float64), A, obs=0)
        with pytest.raises(ValueError, match="sum to 1"):
            variational_free_energy(
                np.array([0.2, 0.2], dtype=np.float64),
                A,
                obs=0,
                prior=prior,
            )


class TestModelInputGuards:
    """Tests for the shared model-shape and probability-vector validation."""

    def test_rejects_non_vector_prior(self) -> None:
        """A multi-dimensional prior should be rejected as not 1D."""
        A, _ = _example_model()
        with pytest.raises(ValueError, match="1D probability vector"):
            bayes_posterior(np.array([[0.6, 0.4]], dtype=np.float64), A, obs=0)

    def test_rejects_negative_prior_mass(self) -> None:
        """A prior with negative mass should be rejected."""
        A, _ = _example_model()
        with pytest.raises(ValueError, match="non-negative"):
            bayes_posterior(np.array([1.4, -0.4], dtype=np.float64), A, obs=0)

    def test_rejects_non_matrix_likelihood(self) -> None:
        """A non-2D likelihood matrix should be rejected."""
        _, prior = _example_model()
        flat_likelihood = np.array([0.9, 0.1], dtype=np.float64)
        with pytest.raises(ValueError, match="2D likelihood matrix"):
            bayes_posterior(prior, flat_likelihood, obs=0)

    def test_rejects_prior_length_mismatch(self) -> None:
        """A prior whose length differs from A's state count is rejected."""
        A, _ = _example_model()
        bad_prior = np.array([0.3, 0.3, 0.4], dtype=np.float64)
        with pytest.raises(ValueError, match="prior length must match"):
            bayes_posterior(bad_prior, A, obs=0)

    def test_rejects_q_length_mismatch(self) -> None:
        """A q vector whose length differs from the prior length is rejected."""
        A, prior = _example_model()
        bad_q = np.array([0.2, 0.3, 0.5], dtype=np.float64)
        with pytest.raises(ValueError, match="q length must match"):
            variational_free_energy(bad_q, A, obs=0, prior=prior)


def test_validate_model_rejects_negative_likelihood() -> None:
    import numpy as np
    import pytest

    from src.kernels.inference import variational_free_energy

    with pytest.raises(ValueError, match="non-negative"):
        variational_free_energy(
            np.array([0.5, 0.5]),
            np.array([[-1.0, 0.2], [2.0, 0.8]]),
            0,
            np.array([0.5, 0.5]),
        )


def test_validate_model_rejects_unnormalized_columns() -> None:
    import numpy as np
    import pytest

    from src.kernels.inference import log_evidence

    with pytest.raises(ValueError, match="sum to 1"):
        log_evidence(np.array([[0.9, 0.9], [0.9, 0.9]]), 0, np.array([0.5, 0.5]))
