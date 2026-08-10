"""Tests for distribution helpers used by the kernels package."""

from __future__ import annotations

import numpy as np
import pytest
from numpy.testing import assert_allclose
from scipy.special import digamma

from src.kernels.distributions import (
    dirichlet_expected,
    dirichlet_expected_log,
    log_stable,
    normalize,
    softmax,
)

ATOL = 1e-9


class TestNormalize:
    """Tests for normalize()."""

    def test_returns_probability_vector(self) -> None:
        """normalize() should return a non-negative vector summing to one."""
        probs = normalize(np.array([2.0, 3.0, 5.0], dtype=np.float64))
        assert_allclose(probs.sum(), 1.0, atol=ATOL)
        assert np.all(probs >= 0.0)

    def test_rejects_negative_entries(self) -> None:
        """normalize() should reject vectors with negative mass."""
        with pytest.raises(ValueError, match="non-negative"):
            normalize(np.array([0.2, -0.1, 0.9], dtype=np.float64))

    def test_rejects_zero_sum_vector(self) -> None:
        """normalize() should reject all-zero vectors."""
        with pytest.raises(ValueError, match="positive sum"):
            normalize(np.zeros(3, dtype=np.float64))


class TestSoftmax:
    """Tests for softmax()."""

    def test_sums_to_one(self) -> None:
        """softmax() should return a normalized categorical distribution."""
        probs = softmax(np.array([-2.0, 0.0, 3.0], dtype=np.float64))
        assert_allclose(probs.sum(), 1.0, atol=ATOL)

    def test_is_shift_invariant(self) -> None:
        """softmax(x) should equal softmax(x + c)."""
        x = np.array([-1.5, 0.2, 3.1], dtype=np.float64)
        assert_allclose(softmax(x), softmax(x + 17.0), atol=ATOL, rtol=ATOL)

    def test_higher_precision_sharpens_the_distribution(self) -> None:
        """Increasing precision should increase mass on the argmax entry."""
        x = np.array([-1.0, 0.0, 2.0], dtype=np.float64)
        low_precision = softmax(x, precision=0.5)
        high_precision = softmax(x, precision=4.0)
        assert np.argmax(low_precision) == np.argmax(high_precision) == 2
        assert high_precision[2] > low_precision[2]

    def test_rejects_non_positive_precision(self) -> None:
        """softmax() requires a positive inverse temperature."""
        with pytest.raises(ValueError, match="precision must be > 0"):
            softmax(np.array([1.0, 2.0], dtype=np.float64), precision=0.0)


class TestLogStable:
    """Tests for log_stable()."""

    def test_clips_zero_to_finite_log(self) -> None:
        """log_stable() should avoid -inf for zero probabilities."""
        logged = log_stable(np.array([0.0, 0.5, 1.0], dtype=np.float64))
        assert np.isfinite(logged).all()
        assert logged[0] == pytest.approx(np.log(1e-16), abs=ATOL)


class TestDirichletHelpers:
    """Tests for Dirichlet expectations."""

    def test_dirichlet_expected_sums_to_one(self) -> None:
        """The Dirichlet mean should be a normalized probability vector."""
        alpha = np.array([1.5, 2.5, 4.0], dtype=np.float64)
        expected = dirichlet_expected(alpha)
        assert_allclose(expected.sum(), 1.0, atol=ATOL)
        assert np.all(expected > 0.0)

    def test_dirichlet_expected_log_matches_digamma_identity(self) -> None:
        """E[log p_i] should match digamma(alpha_i) - digamma(sum alpha)."""
        alpha = np.array([1.5, 2.5, 4.0], dtype=np.float64)
        expected = digamma(alpha) - digamma(np.sum(alpha))
        assert_allclose(dirichlet_expected_log(alpha), expected, atol=ATOL, rtol=ATOL)

    def test_dirichlet_helpers_reject_non_positive_concentrations(self) -> None:
        """Dirichlet expectations require strictly positive concentration parameters."""
        alpha = np.array([1.0, 0.0, 2.0], dtype=np.float64)
        with pytest.raises(ValueError, match="strictly positive"):
            dirichlet_expected(alpha)
        with pytest.raises(ValueError, match="strictly positive"):
            dirichlet_expected_log(alpha)
