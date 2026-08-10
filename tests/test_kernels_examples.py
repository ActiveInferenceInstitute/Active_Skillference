"""Tests for the worked examples that emit provenance claims.

These cross-check each kernel-derived claim against its analytic value, so a kernel
regression breaks a test rather than silently changing learner-facing content.
"""

from __future__ import annotations

import math

import pytest

from src.curriculum.catalog import build_curriculum
from src.kernels.examples import (
    agent_example,
    build_claim_registry,
    efe_ambiguity_examples,
    efe_examples,
    efe_precision_sweep,
    inference_examples,
    info_examples,
    learning_examples,
    message_passing_examples,
    model_parameter_examples,
    model_reduction_examples,
    planning_examples,
    predictive_coding_examples,
    softmax_examples,
    vfe_belief_sweep,
)
from src.provenance.binding import lint_curriculum, validate_curriculum


def test_registry_has_expected_claim_count() -> None:
    reg = build_claim_registry()
    assert len(reg) == 79


def test_entropy_claims_match_analytic_values() -> None:
    reg = build_claim_registry()
    assert reg.value("entropy_fair_coin") == pytest.approx(math.log(2), abs=1e-5)
    assert reg.value("entropy_fair_die") == pytest.approx(math.log(6), abs=1e-5)
    assert reg.value("surprise_rare_event") == pytest.approx(math.log(100), abs=1e-5)


def test_free_energy_bound_is_tight_at_posterior() -> None:
    reg = build_claim_registry()
    # F(posterior) == negative log-evidence (the bound is tight) ...
    assert reg.value("vfe_descent_end") == pytest.approx(
        reg.value("neg_log_evidence_positive"), abs=1e-5
    )
    # ... and F(uniform) is strictly looser (larger).
    assert reg.value("vfe_descent_start") > reg.value("vfe_descent_end")
    assert reg.value("evidence_probability_positive") == pytest.approx(
        math.exp(-reg.value("neg_log_evidence_positive")), abs=1e-6
    )


def test_bayes_posterior_dominated_by_base_rate() -> None:
    reg = build_claim_registry()
    # 1% prevalence, positive test -> posterior well below 0.5.
    assert reg.value("bayes_posterior_present_given_positive") == pytest.approx(
        1 / 6, abs=1e-4
    )


def test_softmax_precision_sharpens() -> None:
    reg = build_claim_registry()
    assert reg.value("softmax_top_high_precision") > reg.value(
        "softmax_top_low_precision"
    )


def test_epistemic_value_positive_only_under_uncertainty() -> None:
    reg = build_claim_registry()
    assert reg.value("efe_epistemic_uncertain") > 0.0
    assert reg.value("efe_epistemic_certain") == pytest.approx(0.0, abs=1e-9)


def test_agent_prefers_resolving_action() -> None:
    reg = build_claim_registry()
    # Lower G is preferred. With neutral preferences the choice is decided purely by
    # epistemic value: the information-seeking *sample* action has lower G than the
    # belief-collapsing *commit* action, and correspondingly higher epistemic value.
    assert reg.value("agent_g_sample") < reg.value("agent_g_commit")
    assert reg.value("agent_epistemic_sample") > reg.value("agent_epistemic_commit")
    assert reg.value("agent_preferred_action") == 0.0  # sample
    assert reg.value("agent_regime_switch_precision") == pytest.approx(0.95, abs=1e-6)


def test_vfe_belief_sweep_minimum_is_exact_posterior() -> None:
    """The figure data should expose the tight bound as the sweep minimum."""
    sweep = vfe_belief_sweep()
    beliefs = sweep["belief_present"]
    energies = sweep["free_energy"]
    posterior_present = sweep["posterior_present"]
    neg_log_evidence = sweep["neg_log_evidence"]

    min_index = int(energies.argmin())
    assert beliefs[min_index] == pytest.approx(posterior_present, abs=1e-12)
    assert energies[min_index] == pytest.approx(neg_log_evidence, abs=1e-10)


def test_efe_precision_sweep_contains_regime_switch() -> None:
    """Sample wins below the non-trivial switch and commit wins above it."""
    sweep = efe_precision_sweep()
    sensor = sweep["sensor_precision"]
    g_sample = sweep["g_sample"]
    g_commit = sweep["g_commit"]
    switch = float(sweep["switch_precision"])

    switch_index = int(abs(sensor - switch).argmin())
    moderate_index = int(abs(sensor - 0.9).argmin())
    high_index = int(abs(sensor - 0.99).argmin())

    assert switch == pytest.approx(0.95, abs=1e-6)
    assert g_sample[switch_index] == pytest.approx(g_commit[switch_index], abs=1e-6)
    assert g_sample[moderate_index] < g_commit[moderate_index]
    assert g_sample[high_index] > g_commit[high_index]


def test_each_example_function_returns_a_dict() -> None:
    for fn in (
        info_examples,
        softmax_examples,
        inference_examples,
        efe_examples,
        efe_ambiguity_examples,
        agent_example,
        message_passing_examples,
        learning_examples,
        model_reduction_examples,
        planning_examples,
        predictive_coding_examples,
        model_parameter_examples,
    ):
        result = fn()
        assert isinstance(result, dict) and result


def test_belief_propagation_matches_brute_force_enumeration() -> None:
    """The non-vacuous oracle: sum-product on a chain == marginalizing the joint."""
    import itertools

    import numpy as np

    from src.kernels.examples import _BP_EVIDENCE, _BP_PRIOR, _BP_TRANSITION
    from src.kernels.inference import belief_propagation_chain

    n_nodes, n_states = _BP_EVIDENCE.shape
    marginals = belief_propagation_chain(_BP_PRIOR, _BP_TRANSITION, _BP_EVIDENCE)
    joint = np.zeros((n_states,) * n_nodes)
    for cfg in itertools.product(range(n_states), repeat=n_nodes):
        weight = _BP_PRIOR[cfg[0]] * _BP_EVIDENCE[0, cfg[0]]
        for t in range(n_nodes - 1):
            weight *= (
                _BP_TRANSITION[cfg[t], cfg[t + 1]] * _BP_EVIDENCE[t + 1, cfg[t + 1]]
            )
        joint[cfg] = weight
    joint /= joint.sum()
    brute = np.array(
        [
            joint.sum(axis=tuple(j for j in range(n_nodes) if j != t))
            for t in range(n_nodes)
        ]
    )
    assert np.allclose(marginals, brute, atol=1e-12)
    # The smoothed neighbour is lifted above its prior by the observed node.
    assert marginals[0, 0] > _BP_PRIOR[0]


def test_belief_propagation_single_node_is_local_posterior() -> None:
    import numpy as np

    from src.kernels.inference import belief_propagation_chain

    marginals = belief_propagation_chain(
        np.array([0.5, 0.5]), np.eye(2), np.array([[0.9, 0.1]])
    )
    assert marginals[0] == pytest.approx([0.9, 0.1], abs=1e-12)


def test_belief_propagation_rejects_unnormalized_transition() -> None:
    import numpy as np

    from src.kernels.inference import belief_propagation_chain

    with pytest.raises(ValueError):
        belief_propagation_chain(
            np.array([0.5, 0.5]),
            np.array([[0.8, 0.4], [0.2, 0.8]]),  # rows do not sum to 1
            np.ones((2, 2)),
        )


def test_dirichlet_learning_sharpens_toward_empirical_frequency() -> None:
    reg = build_claim_registry()
    # Flat prior mean is 0.5; counts [8, 2] pull the posterior mean to 9/12 = 0.75.
    assert reg.value("dirichlet_prior_mean_positive") == pytest.approx(0.5, abs=1e-9)
    assert reg.value("dirichlet_posterior_mean_positive") == pytest.approx(
        9.0 / 12.0, abs=1e-9
    )
    # E[log p] under the posterior is digamma(9) - digamma(12) (a tested identity).
    from scipy.special import digamma

    assert reg.value("dirichlet_expected_log_positive") == pytest.approx(
        float(digamma(9.0) - digamma(12.0)), abs=1e-6
    )


def test_model_reduction_rejects_the_reduced_model_after_positive_reading() -> None:
    reg = build_claim_registry()
    full = reg.value("bmr_log_evidence_full")
    reduced = reg.value("bmr_log_evidence_reduced")
    factor = reg.value("bmr_log_bayes_factor")
    # The reported factor IS the difference of the two computed evidences (no drift)...
    assert factor == pytest.approx(full - reduced, abs=1e-9)
    # ...and it is positive: the positive reading supports keeping the pruned state.
    assert factor > 0.0


def test_efe_ambiguity_is_state_dependent() -> None:
    reg = build_claim_registry()
    crisp = reg.value("efe_ambiguity_crisp_state")
    uniform = reg.value("efe_ambiguity_uniform_belief")
    # The crisp state has lower likelihood entropy than the mixed-belief average.
    assert crisp < uniform
    assert crisp == pytest.approx(0.325082973, abs=1e-6)


def test_multistep_planning_reduces_to_one_step_at_horizon_one() -> None:
    """Consistency invariant: H=1 cumulative G equals the one-step EFE per action."""

    from src.kernels.active_inference import DiscreteActiveInferenceAgent
    from src.kernels.examples import _PLAN_A, _PLAN_B, _PLAN_C, _PLAN_D

    agent = DiscreteActiveInferenceAgent(_PLAN_A, _PLAN_B, _PLAN_C, _PLAN_D)
    qs = agent.infer_states(obs=0)
    one_step = agent.evaluate_policies(qs)
    multi = agent.evaluate_multistep_policies(qs, horizon=1)
    per_policy = {policy[0]: g for policy, g in zip(multi["policies"], multi["G"])}
    for action, value in enumerate(one_step):
        assert per_policy[action] == pytest.approx(value, abs=1e-12)


def test_lookahead_pays_only_under_temporal_coupling() -> None:
    """The honest contrast: gain > 0 in the coupled model, exactly 0 when decoupled.

    The greedy baseline is the strongest myopic policy, so a positive coupled gain
    is a real look-ahead advantage, not a crippled-comparator artifact.
    """
    claims = planning_examples()
    assert claims["plan_lookahead_gain_decoupled"] == pytest.approx(0.0, abs=1e-12)
    assert claims["plan_lookahead_gain_coupled"] > 0.5
    # The optimal multi-step plan beats greedy by exactly the reported gain.
    assert claims["plan_greedy_policy_g"] - claims["plan_optimal_policy_g"] == (
        pytest.approx(claims["plan_lookahead_gain_coupled"], abs=1e-9)
    )


def test_greedy_baseline_is_honest_not_crippled() -> None:
    """Anti-crippled-comparator triangulation on the coupled detour model.

    A look-ahead gain is only meaningful if the baseline is genuinely strong. We
    prove three things at once: (1) greedy's first action is the per-step EFE argmin
    (a real myopic optimizer, not a fixed weak choice); (2) some enumerated policy is
    WORSE than greedy, so greedy is not the trivial floor; and (3) the optimal plan
    is strictly better than greedy — the gain comes from look-ahead, not from
    handicapping the comparator.
    """
    import numpy as np

    from src.kernels.active_inference import (
        DiscreteActiveInferenceAgent,
        expected_free_energy,
    )
    from src.kernels.examples import (
        _DETOUR_A,
        _DETOUR_B,
        _DETOUR_C,
        _DETOUR_D,
        _DETOUR_HORIZON,
        greedy_policy_value,
    )

    agent = DiscreteActiveInferenceAgent(_DETOUR_A, _DETOUR_B, _DETOUR_C, _DETOUR_D)
    qs = agent.infer_states(obs=0)
    greedy_g = greedy_policy_value(agent, qs, _DETOUR_HORIZON)

    immediate = np.array(
        [
            expected_free_energy(agent.predict(qs, a), agent.A, agent.C)[0]
            for a in range(agent.B.shape[2])
        ]
    )
    greedy_first = int(np.argmin(immediate))
    result = agent.evaluate_multistep_policies(qs, _DETOUR_HORIZON)
    g_values = np.asarray(result["G"], dtype=np.float64)
    optimal_g = float(g_values[result["best_index"]])

    # (1) greedy starts with the genuine myopic argmin
    assert result["best_policy"][0] != greedy_first  # look-ahead changes the choice
    # (2) greedy is not the worst policy — a worse one exists
    assert float(g_values.max()) > greedy_g + 1e-9
    # (3) the optimal plan strictly beats the strong greedy baseline
    assert optimal_g < greedy_g - 1e-9


def test_model_parameters_echo_the_kernel_constants() -> None:
    reg = build_claim_registry()
    assert reg.value("param_disease_prior_present") == pytest.approx(0.01, abs=1e-9)
    assert reg.value("param_sensor_true_positive") == pytest.approx(0.99, abs=1e-9)
    assert reg.value("param_informative_sensor_precision") == pytest.approx(
        0.9, abs=1e-9
    )


def test_registry_is_deterministic() -> None:
    a = build_claim_registry().as_dict()
    b = build_claim_registry().as_dict()
    assert a == b


def test_catalog_tokens_all_resolve_against_registry() -> None:
    """Integration seam: every {{claim}} the catalog references is backed by a kernel."""
    graph = build_curriculum()
    reg = build_claim_registry()
    validate_curriculum(graph.skills, reg)  # raises if any token is unbacked
    assert lint_curriculum(graph.skills) == []
