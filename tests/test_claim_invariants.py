"""Invariants the registered claims must satisfy.

Registering a number is not the same as registering a true number. Each test
here restates an identity or limit the curriculum asserts in prose and checks
the claim ledger against the mathematics rather than against itself.
"""

from __future__ import annotations


def test_registered_information_bounds_hold_as_stated() -> None:
    """The new bound claims must satisfy the inequalities the curriculum states.

    Registering a number is not the same as registering a true number. Each of
    these is one side of an identity or inequality the prose asserts, so the
    claim ledger is checked against the mathematics rather than only against
    itself.
    """
    import pytest

    from src.kernels.examples import build_claim_registry

    registry = build_claim_registry()
    values = {
        name: registry.get(name).value
        for name in (
            "cross_entropy_gap_equals_kl",
            "kl_biased_vs_fair",
            "entropy_max_two_state",
            "entropy_biased_coin",
            "entropy_deficit_biased",
            "mutual_info_independent",
            "mutual_info_skewed",
            "kl_asymmetry_gap",
            "kl_fair_vs_biased",
            "evidence_bound_slack_uniform",
            "evidence_bound_slack_posterior",
            "dirichlet_jensen_gap_sparse",
            "dirichlet_jensen_gap_dense",
        )
    }

    # Cross-entropy decomposes as entropy plus divergence.
    assert values["cross_entropy_gap_equals_kl"] == pytest.approx(
        values["kl_biased_vs_fair"], abs=1e-6
    )
    # Uniform maximizes entropy over a fixed support.
    assert values["entropy_max_two_state"] > values["entropy_biased_coin"]
    assert values["entropy_deficit_biased"] == pytest.approx(
        values["entropy_max_two_state"] - values["entropy_biased_coin"], abs=1e-6
    )
    # Mutual information vanishes exactly when the joint factorizes.
    assert values["mutual_info_independent"] == pytest.approx(0.0, abs=1e-9)
    assert values["mutual_info_skewed"] > 0.0
    # KL is asymmetric, so direction must always be stated.
    # Each claim is registered rounded to six decimals, so a difference of two
    # registered values can disagree with the registered difference by one unit
    # in the last place. Two ULPs is the honest tolerance for that comparison.
    assert values["kl_asymmetry_gap"] == pytest.approx(
        values["kl_fair_vs_biased"] - values["kl_biased_vs_fair"], abs=2e-6
    )
    assert values["kl_asymmetry_gap"] != pytest.approx(0.0, abs=1e-6)
    # Free energy upper-bounds surprise and the bound is tight at the posterior.
    assert values["evidence_bound_slack_uniform"] > 0.0
    assert values["evidence_bound_slack_posterior"] == pytest.approx(0.0, abs=1e-9)
    # Jensen's gap is positive and shrinks as concentration grows.
    assert values["dirichlet_jensen_gap_dense"] > 0.0
    assert values["dirichlet_jensen_gap_sparse"] > values["dirichlet_jensen_gap_dense"]


def test_registered_control_and_precision_claims_hold_as_stated() -> None:
    """Policy precision, the EFE decomposition, and precision weighting.

    Each of these is an identity or a limit the curriculum asserts in prose.
    Registering the residual, rather than only the quantity, is what makes the
    assertion falsifiable by the claim ledger itself.
    """
    import pytest

    from src.kernels.examples import build_claim_registry

    registry = build_claim_registry()
    value = {name: registry.get(name).value for name in registry.names()}

    # Expected free energy equals its two components exactly, not approximately.
    assert value["efe_identity_residual"] == pytest.approx(0.0, abs=1e-6)

    # Precision drives the policy posterior between the two limits: uniform at
    # low precision, one-hot on the best policy at high precision.
    assert (
        value["policy_entropy_low_precision"] < value["policy_entropy_uniform_ceiling"]
    )
    assert value["policy_entropy_low_precision_deficit"] > 0.0
    assert value["policy_entropy_low_precision_deficit"] < 0.01
    assert (
        value["policy_entropy_high_precision"]
        < value["policy_entropy_reference_precision"]
        < value["policy_entropy_low_precision"]
    )
    assert value["policy_best_mass_high_precision"] > 0.99

    # The Gaussian posterior mean is the analytic precision-weighted combination,
    # and it moves toward whichever source carries more precision.
    assert value["posterior_mean_analytic_residual"] == pytest.approx(0.0, abs=1e-6)
    assert 0.0 < value["precision_weight_on_observation"] < 1.0
    assert value["posterior_mean_precision_shift"] > 0.0
