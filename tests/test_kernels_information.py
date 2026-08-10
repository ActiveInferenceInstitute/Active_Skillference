"""Tests for information-theoretic kernel primitives."""

from __future__ import annotations

import numpy as np
import pytest

from src.kernels.information import (
    cross_entropy,
    entropy,
    kl_divergence,
    mutual_information,
    surprise,
)

ATOL = 1e-9


class TestSurprise:
    """Tests for surprise()."""

    def test_matches_negative_log_probability(self) -> None:
        """surprise(p) should equal -ln(p) in nats."""
        assert abs(surprise(0.25) - np.log(4.0)) < ATOL

    @pytest.mark.parametrize("probability", [0.0, -1e-6])
    def test_raises_for_non_positive_probability(self, probability: float) -> None:
        """surprise() should reject non-positive probabilities."""
        with pytest.raises(ValueError, match="probability must be > 0"):
            surprise(probability)


class TestEntropy:
    """Tests for entropy()."""

    def test_uniform_distribution_matches_log_cardinality(self) -> None:
        """A uniform categorical distribution has entropy ln(n)."""
        probs = np.full(5, 0.2, dtype=np.float64)
        assert abs(entropy(probs) - np.log(5.0)) < ATOL

    def test_rejects_non_normalized_probability_vector(self) -> None:
        """entropy() should reject vectors that do not sum to one."""
        with pytest.raises(ValueError, match="sum to 1"):
            entropy(np.array([0.2, 0.2, 0.2], dtype=np.float64))


class TestCrossEntropyAndKl:
    """Tests for cross_entropy() and kl_divergence()."""

    def test_cross_entropy_equals_entropy_plus_kl(self) -> None:
        """cross_entropy(p, q) should equal H(p) + KL(p || q)."""
        p = np.array([0.2, 0.3, 0.5], dtype=np.float64)
        q = np.array([0.1, 0.4, 0.5], dtype=np.float64)
        lhs = cross_entropy(p, q)
        rhs = entropy(p) + kl_divergence(p, q)
        assert abs(lhs - rhs) < ATOL

    def test_kl_is_zero_for_identical_distributions(self) -> None:
        """KL divergence should be exactly zero when p == q."""
        p = np.array([0.2, 0.3, 0.5], dtype=np.float64)
        assert abs(kl_divergence(p, p)) < ATOL

    def test_kl_is_non_negative_for_random_probability_vectors(self) -> None:
        """KL divergence should satisfy Gibbs' inequality."""
        rng = np.random.default_rng(12345)
        for _ in range(8):
            p = rng.random(4)
            q = rng.random(4)
            p = p / p.sum()
            q = q / q.sum()
            assert kl_divergence(p, q) >= -ATOL

    def test_cross_entropy_rejects_distribution_with_zero_mass_where_p_positive(
        self,
    ) -> None:
        """cross_entropy() should reject q entries that would imply log(0)."""
        p = np.array([0.5, 0.5], dtype=np.float64)
        q = np.array([1.0, 0.0], dtype=np.float64)
        with pytest.raises(ValueError, match="strictly positive"):
            cross_entropy(p, q)


class TestMutualInformation:
    """Tests for mutual_information()."""

    def test_is_zero_for_independent_joint_distribution(self) -> None:
        """Independent variables should have zero mutual information."""
        px = np.array([0.25, 0.75], dtype=np.float64)
        py = np.array([0.6, 0.4], dtype=np.float64)
        joint = np.outer(px, py)
        assert abs(mutual_information(joint)) < ATOL

    def test_is_non_negative_for_correlated_joint_distribution(self) -> None:
        """Mutual information should be non-negative."""
        joint = np.array([[0.45, 0.05], [0.05, 0.45]], dtype=np.float64)
        assert mutual_information(joint) >= -ATOL

    def test_rejects_non_matrix_input(self) -> None:
        """mutual_information() requires a 2D probability matrix."""
        with pytest.raises(ValueError, match="2D"):
            mutual_information(np.array([0.5, 0.5], dtype=np.float64))

    def test_rejects_negative_joint_mass(self) -> None:
        """mutual_information() requires a non-negative joint matrix."""
        joint = np.array([[0.6, -0.1], [0.2, 0.3]], dtype=np.float64)
        with pytest.raises(ValueError, match="non-negative"):
            mutual_information(joint)

    def test_rejects_unnormalized_joint(self) -> None:
        """mutual_information() requires the joint matrix to sum to one."""
        joint = np.array([[0.3, 0.3], [0.3, 0.3]], dtype=np.float64)
        with pytest.raises(ValueError, match="sum to 1"):
            mutual_information(joint)


class TestProbabilityVectorGuards:
    """Tests for the shared 1D probability-vector validation."""

    def test_entropy_rejects_non_vector_input(self) -> None:
        """entropy() requires a one-dimensional probability vector."""
        with pytest.raises(ValueError, match="1D probability vector"):
            entropy(np.array([[0.5, 0.5], [0.5, 0.5]], dtype=np.float64))

    def test_entropy_rejects_negative_mass(self) -> None:
        """entropy() requires non-negative probability mass."""
        with pytest.raises(ValueError, match="non-negative"):
            entropy(np.array([1.2, -0.2], dtype=np.float64))

    def test_cross_entropy_rejects_shape_mismatch(self) -> None:
        """cross_entropy() requires p and q to share a shape."""
        p = np.array([0.5, 0.5], dtype=np.float64)
        q = np.array([0.2, 0.3, 0.5], dtype=np.float64)
        with pytest.raises(ValueError, match="matching shapes"):
            cross_entropy(p, q)

    def test_kl_rejects_shape_mismatch(self) -> None:
        """kl_divergence() requires p and q to share a shape."""
        p = np.array([0.5, 0.5], dtype=np.float64)
        q = np.array([0.2, 0.3, 0.5], dtype=np.float64)
        with pytest.raises(ValueError, match="matching shapes"):
            kl_divergence(p, q)

    def test_kl_rejects_zero_mass_where_p_positive(self) -> None:
        """kl_divergence() rejects q entries that would imply log(0)."""
        p = np.array([0.5, 0.5], dtype=np.float64)
        q = np.array([1.0, 0.0], dtype=np.float64)
        with pytest.raises(ValueError, match="strictly positive"):
            kl_divergence(p, q)


class TestNumericComputationNotIdentity:
    """Non-vacuous numeric checks: verify the COMPUTED value against an independent
    re-derivation, not a mathematical identity that holds by construction (ISC-131)."""

    def test_kl_matches_independent_sum(self) -> None:
        p = np.array([0.9, 0.1], dtype=np.float64)
        q = np.array([0.5, 0.5], dtype=np.float64)
        expected = float(np.sum(p * np.log(p / q)))  # independent of the kernel
        assert kl_divergence(p, q) == pytest.approx(expected, abs=1e-12)
        assert kl_divergence(p, q) == pytest.approx(0.3680642, abs=1e-6)

    def test_mutual_information_matches_independent_sum(self) -> None:
        joint = np.array([[0.4, 0.1], [0.1, 0.4]], dtype=np.float64)
        px = joint.sum(axis=1)
        py = joint.sum(axis=0)
        expected = float(
            sum(
                joint[i, j] * np.log(joint[i, j] / (px[i] * py[j]))
                for i in range(2)
                for j in range(2)
            )
        )
        assert mutual_information(joint) == pytest.approx(expected, abs=1e-12)
        assert mutual_information(joint) > 0.0  # correlated → strictly positive

    def test_cross_entropy_accepts_non_normalized_q(self) -> None:
        """ISC-130: q is a candidate (e.g. a likelihood column A[obs,:]) and need not
        sum to one. The old gate rejected this standard usage."""
        p = np.array([0.5, 0.5], dtype=np.float64)
        q = np.array([0.8, 0.3], dtype=np.float64)  # sums to 1.1, not a distribution
        expected = float(-np.sum(p * np.log(q)))
        assert cross_entropy(p, q) == pytest.approx(expected, abs=1e-12)

    def test_cross_entropy_still_rejects_negative_q(self) -> None:
        p = np.array([0.5, 0.5], dtype=np.float64)
        q = np.array([1.2, -0.2], dtype=np.float64)
        with pytest.raises(ValueError, match="non-negative"):
            cross_entropy(p, q)


class TestCrossEntropyPosteriorArgStaysStrict:
    """Advisor guard: relaxing q (the candidate) must NOT relax p (the reference/posterior
    position). An un-normalized p must still be rejected so the relaxation cannot leak into
    a posterior-expecting use."""

    def test_cross_entropy_rejects_unnormalized_p(self) -> None:
        p = np.array([0.8, 0.8], dtype=np.float64)  # sums to 1.6, not a distribution
        q = np.array([0.5, 0.5], dtype=np.float64)
        with pytest.raises(ValueError, match="sum to 1"):
            cross_entropy(p, q)
