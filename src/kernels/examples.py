"""Worked examples that drive the kernels and emit provenance claims.

Every quantitative value shown anywhere in the curriculum originates here: each
function runs a tested kernel on a fixed, documented input and returns the result,
and :func:`build_claim_registry` registers them all into a
:class:`~src.provenance.claims.ClaimRegistry` under the exact ``{{claim:NAME}}`` names
the curriculum catalog references.

Because the values are *computed* (not typed), a kernel change that alters a result
will change the claim, the rendered skill content, and the figures together — there is
no place for a number to drift out of sync.
"""

from __future__ import annotations

from typing import cast

import numpy as np
from numpy.typing import ArrayLike, NDArray

from src.kernels.active_inference import (
    DiscreteActiveInferenceAgent,
    expected_free_energy,
    policy_posterior,
)
from src.kernels.distributions import (
    dirichlet_expected,
    dirichlet_expected_log,
    softmax,
)
from src.kernels.inference import (
    bayes_posterior,
    belief_propagation_chain,
    elbo,
    log_evidence,
    variational_free_energy,
)
from src.kernels.information import (
    cross_entropy,
    entropy,
    kl_divergence,
    mutual_information,
    surprise,
)
from src.kernels.predictive_coding import (
    gaussian_posterior_mean,
    predictive_coding_descent,
)
from src.provenance.claims import ClaimRegistry

# Fixed seed for any stochastic example — determinism is a tested invariant (ISC-15).
SEED = 20260609

# A canonical noisy-sensor model reused across inference examples:
# states = {present, absent}; observations = {positive, negative}.
# A[obs, state] = P(obs | state).
_DISEASE_PRIOR = np.array([0.01, 0.99])  # P(present), P(absent)
_DISEASE_A = np.array(
    [
        [0.99, 0.05],  # P(positive | present), P(positive | absent)
        [0.01, 0.95],  # P(negative | present), P(negative | absent)
    ]
)

# The canonical *informative* sensor (symmetric, precision 0.9) shared by the EFE
# decomposition, the planning models, and the registered model parameter — a single
# source of truth so the 05_experimental_setup binding cannot drift from the kernel.
_INFORMATIVE_SENSOR_A = np.array([[0.9, 0.1], [0.1, 0.9]])

FloatArray = NDArray[np.float64]


def info_examples() -> dict[str, float]:
    """Shannon information quantities (nats)."""
    correlated_joint = np.array([[0.4, 0.1], [0.1, 0.4]])
    return {
        "entropy_fair_coin": entropy([0.5, 0.5]),
        "entropy_fair_die": entropy(np.ones(6) / 6),
        "entropy_biased_coin": entropy([0.9, 0.1]),
        "surprise_rare_event": surprise(0.01),
        "kl_biased_vs_fair": kl_divergence([0.9, 0.1], [0.5, 0.5]),
        "mutual_info_correlated": mutual_information(correlated_joint),
    }


def softmax_examples() -> dict[str, float]:
    """Precision (inverse temperature) sharpens a softmax."""
    x = [1.0, 2.0, 3.0]
    return {
        "softmax_top_low_precision": float(softmax(x, precision=1.0)[-1]),
        "softmax_top_high_precision": float(softmax(x, precision=3.0)[-1]),
    }


def inference_examples() -> dict[str, float]:
    """Exact Bayes + the variational free-energy bound on a noisy-sensor model.

    The free-energy *descent* claims show F at a poor (uniform) belief vs F at the
    true posterior: F decreases to exactly the negative log-evidence (surprise), so
    the variational bound is tight at the posterior.
    """
    obs = 0  # observed: positive
    posterior = bayes_posterior(_DISEASE_PRIOR, _DISEASE_A, obs)
    evidence_probability = float(np.exp(log_evidence(_DISEASE_A, obs, _DISEASE_PRIOR)))
    neg_log_ev = -log_evidence(_DISEASE_A, obs, _DISEASE_PRIOR)
    f_posterior = variational_free_energy(posterior, _DISEASE_A, obs, _DISEASE_PRIOR)
    f_uniform = variational_free_energy(
        np.array([0.5, 0.5]), _DISEASE_A, obs, _DISEASE_PRIOR
    )
    return {
        "bayes_posterior_present_given_positive": float(posterior[0]),
        "evidence_probability_positive": evidence_probability,
        "neg_log_evidence_positive": float(neg_log_ev),
        "vfe_descent_end": float(f_posterior),  # == surprise (tight)
        "vfe_descent_start": float(f_uniform),  # > surprise (loose)
    }


def vfe_belief_sweep(samples: int = 201) -> dict[str, FloatArray | float]:
    """Evaluate VFE across beliefs over the canonical noisy-sensor model.

    The returned arrays are figure data only; all values are computed by the same
    inference kernels that emit the scalar manuscript claims.
    """

    if samples < 5:
        raise ValueError("samples must be at least 5")
    obs = 0
    posterior = bayes_posterior(_DISEASE_PRIOR, _DISEASE_A, obs)
    posterior_present = float(posterior[0])
    belief_values = np.unique(
        np.concatenate(
            [
                np.linspace(0.001, 0.999, samples, dtype=np.float64),
                np.array([posterior_present, 0.5], dtype=np.float64),
            ]
        )
    )
    free_energy_values = np.array(
        [
            variational_free_energy(
                np.array([belief, 1.0 - belief], dtype=np.float64),
                _DISEASE_A,
                obs,
                _DISEASE_PRIOR,
            )
            for belief in belief_values
        ],
        dtype=np.float64,
    )
    return {
        "belief_present": belief_values,
        "free_energy": free_energy_values,
        "posterior_present": posterior_present,
        "neg_log_evidence": -log_evidence(_DISEASE_A, obs, _DISEASE_PRIOR),
    }


def efe_examples() -> dict[str, float]:
    """Expected-free-energy decomposition into epistemic + pragmatic value.

    An *uncertain* belief over states with an informative likelihood carries positive
    epistemic value (information to be gained); a *certain* belief carries none.
    """
    likelihood = _INFORMATIVE_SENSOR_A  # informative sensor (shared constant)
    preference = np.array([0.9, 0.1])  # prefers observation 0
    _, epi_uncertain, _ = expected_free_energy([0.5, 0.5], likelihood, preference)
    _, epi_certain, prag_certain = expected_free_energy(
        [1.0, 0.0], likelihood, preference
    )
    return {
        "efe_epistemic_uncertain": float(epi_uncertain),
        "efe_epistemic_certain": float(epi_certain),
        "efe_pragmatic_certain": float(prag_certain),
    }


def agent_example() -> dict[str, float]:
    """A deterministic one-step active-inference agent driven by epistemic value.

    Preferences are **neutral** (``C`` uniform), so the pragmatic term is identical for
    both actions and the choice is decided purely by epistemic value (expected
    information gain). The ``sample`` action keeps the informative belief spread (high
    epistemic value); the ``commit`` action collapses it (low epistemic value). The
    agent correctly prefers ``sample`` — the genuinely information-seeking choice — and
    the result is reproducible under a fixed seed (ISC-15).
    """
    likelihood = _INFORMATIVE_SENSOR_A  # informative sensor (shared constant)
    # action 0 = sample (identity: preserve the informative belief, high epistemic);
    # action 1 = commit (collapse toward state 0, low epistemic).
    transitions = np.zeros((2, 2, 2))
    transitions[:, :, 0] = np.eye(2)
    transitions[:, :, 1] = np.array([[0.95, 0.95], [0.05, 0.05]])
    preference = np.array([0.5, 0.5])  # NEUTRAL: pragmatic value equal for both actions
    prior = np.array([0.5, 0.5])
    agent = DiscreteActiveInferenceAgent(likelihood, transitions, preference, prior)
    qs = agent.infer_states(obs=0)
    g_values = agent.evaluate_policies(qs)
    epistemic = [
        expected_free_energy(agent.predict(qs, a), likelihood, preference)[1]
        for a in range(2)
    ]
    chosen = int(np.argmin(g_values))
    return {
        "agent_preferred_action": float(chosen),
        "agent_g_sample": float(g_values[0]),
        "agent_g_commit": float(g_values[1]),
        "agent_epistemic_sample": float(epistemic[0]),
        "agent_epistemic_commit": float(epistemic[1]),
        "agent_regime_switch_precision": agent_regime_switch_precision(),
    }


def two_action_regime_agent(sensor_precision: float) -> DiscreteActiveInferenceAgent:
    """Return the neutral-preference sample/commit agent used for regime sweeps."""

    if sensor_precision < 0.5 or sensor_precision >= 1.0:
        raise ValueError("sensor_precision must be in [0.5, 1.0)")
    likelihood = np.array(
        [
            [sensor_precision, 1.0 - sensor_precision],
            [1.0 - sensor_precision, sensor_precision],
        ],
        dtype=np.float64,
    )
    transitions = np.zeros((2, 2, 2), dtype=np.float64)
    transitions[:, :, 0] = np.eye(2)
    transitions[:, :, 1] = np.array([[0.95, 0.95], [0.05, 0.05]])
    preference = np.array([0.5, 0.5], dtype=np.float64)
    prior = np.array([0.5, 0.5], dtype=np.float64)
    return DiscreteActiveInferenceAgent(likelihood, transitions, preference, prior)


def agent_regime_switch_precision() -> float:
    """Return the non-trivial sensor precision where sample and commit tie."""

    low = 0.90
    high = 0.99
    for _ in range(64):
        mid = (low + high) / 2.0
        agent = two_action_regime_agent(mid)
        g_values = agent.evaluate_policies(agent.infer_states(obs=0))
        difference = float(g_values[0] - g_values[1])
        if difference < 0.0:
            low = mid
        else:
            high = mid
    return (low + high) / 2.0


# A canonical homogeneous two-state chain reused by the belief-propagation example:
# a "sticky" latent process (states tend to persist) observed through a single
# informative reading at the middle node. Smoothing should pull the neighbours
# toward the observed state — that pull is exactly what sum-product computes.
_BP_PRIOR = np.array([0.5, 0.5])
_BP_TRANSITION = np.array([[0.8, 0.2], [0.2, 0.8]])  # sticky: 80% persistence
_BP_EVIDENCE = np.array(
    [
        [1.0, 1.0],  # node 0: unobserved (flat potential)
        [0.9, 0.1],  # node 1: a reading favouring state 0 (informative sensor)
        [1.0, 1.0],  # node 2: unobserved
    ]
)


def message_passing_examples() -> dict[str, float]:
    """Exact node marginals on a 3-node chain via sum-product belief propagation.

    A single informative reading at the middle node propagates to its unobserved
    neighbours through the sticky transition: the smoothed marginals at nodes 0 and
    2 shift above the 0.5 prior even though those nodes were never observed. Because
    a chain is a tree, these marginals are *exact* (the tests assert equality with a
    brute-force enumeration of the full joint).
    """

    marginals = belief_propagation_chain(_BP_PRIOR, _BP_TRANSITION, _BP_EVIDENCE)
    return {
        "bp_marginal_observed_node_state0": float(marginals[1, 0]),
        "bp_marginal_neighbor_node_state0": float(marginals[0, 0]),
        "bp_smoothing_lift_over_prior": float(marginals[0, 0] - _BP_PRIOR[0]),
    }


# Parameter learning: a flat Dirichlet belief over one sensor column,
# P(reading | state=present), updated by a fixed observed count vector. The mean
# sharpens from the uninformative 0.5 toward the empirical frequency as evidence
# arrives — conjugate Bayesian learning of a model parameter.
_DIRICHLET_PRIOR_ALPHA = np.array([1.0, 1.0])  # flat Beta(1, 1)
_DIRICHLET_COUNTS = np.array([8.0, 2.0])  # observed 8 positive, 2 negative


def learning_examples() -> dict[str, float]:
    """Dirichlet-conjugate learning of a sensor parameter from observed counts."""

    posterior_alpha = _DIRICHLET_PRIOR_ALPHA + _DIRICHLET_COUNTS
    prior_mean = dirichlet_expected(_DIRICHLET_PRIOR_ALPHA)
    posterior_mean = dirichlet_expected(posterior_alpha)
    expected_log = dirichlet_expected_log(posterior_alpha)
    return {
        "dirichlet_prior_mean_positive": float(prior_mean[0]),
        "dirichlet_posterior_mean_positive": float(posterior_mean[0]),
        "dirichlet_expected_log_positive": float(expected_log[0]),
    }


def model_reduction_examples() -> dict[str, float]:
    """Bayesian model reduction on the noisy-sensor model after a positive reading.

    A full model keeps both latent states; a reduced model prunes the ``present``
    state to near-zero prior mass. The log Bayes factor ``log P(o | full) - log P(o
    | reduced)`` measures whether the data *require* the pruned structure. After a
    positive reading the factor is positive — the structure is supported, so the
    reduction is rejected. Both terms are exact log evidences (the test pins the
    factor to the difference of the two computed evidences and checks its sign).
    """

    obs = 0  # positive reading
    reduced_prior = normalize_pruned(_DISEASE_PRIOR, prune_index=0)
    log_ev_full = log_evidence(_DISEASE_A, obs, _DISEASE_PRIOR)
    log_ev_reduced = log_evidence(_DISEASE_A, obs, reduced_prior)
    return {
        "bmr_log_evidence_full": float(log_ev_full),
        "bmr_log_evidence_reduced": float(log_ev_reduced),
        "bmr_log_bayes_factor": float(log_ev_full - log_ev_reduced),
    }


def normalize_pruned(prior: FloatArray, prune_index: int) -> FloatArray:
    """Return a copy of ``prior`` with one state pruned to negligible mass.

    The pruned mass is set to a tiny floor (not exactly zero, so the log evidence
    stays finite) and the vector is renormalized — the reduced structural model.
    """

    reduced = np.array(prior, dtype=np.float64)
    if not 0 <= prune_index < reduced.shape[0]:
        raise ValueError("prune_index out of range")
    reduced[prune_index] = 1e-6
    return reduced / float(np.sum(reduced))


# Ambiguity decomposition: the expected entropy of the likelihood columns, a
# state-dependent quantity, using an ASYMMETRIC sensor so the two states differ in
# how ambiguous their readings are. Ambiguity is the "how noisy is what I will see"
# term; epistemic value is the "how much will I learn" term.
_AMBIGUITY_A = np.array(
    [[0.9, 0.5], [0.1, 0.5]]
)  # state 0 crisp, state 1 maximally noisy


def efe_ambiguity_examples() -> dict[str, float]:
    """State-dependent ambiguity = expected likelihood entropy under the belief."""

    column_entropies = np.array(
        [entropy(_AMBIGUITY_A[:, s]) for s in range(_AMBIGUITY_A.shape[1])]
    )
    ambiguity_uniform = float(np.array([0.5, 0.5]) @ column_entropies)
    ambiguity_crisp_state = float(column_entropies[0])
    return {
        "efe_ambiguity_uniform_belief": ambiguity_uniform,
        "efe_ambiguity_crisp_state": ambiguity_crisp_state,
    }


# Multi-step planning, two contrasting models that isolate WHEN look-ahead pays.
#
# DECOUPLED model (sample/commit): an informative sensor with an observation
# preference. Step values ARE temporally coupled here (the commit action collapses
# the belief, changing later expected free energy), but the myopically-best first
# action already steers the agent onto the globally optimal trajectory, so greedy
# attains the optimum and look-ahead adds nothing — an honest null arising from
# aligned myopic/long-run optima, not from value-independence.
_PLAN_A = _INFORMATIVE_SENSOR_A  # informative sensor (shared constant)
_PLAN_B = np.zeros((2, 2, 2))
_PLAN_B[:, :, 0] = np.eye(2)  # action 0 = sample (preserve belief)
_PLAN_B[:, :, 1] = np.array(
    [[0.95, 0.95], [0.05, 0.05]]
)  # action 1 = commit (collapse)
_PLAN_C = np.array([0.9, 0.1])  # prefers observation 0
_PLAN_D = np.array([0.5, 0.5])
_PLAN_GAMMA = 4.0

# COUPLED model (investment / detour): a 4-state task — start, comfort, goal,
# climb. The likelihood is the identity (no ambiguity; pure pragmatic value), so
# G(state) = -log preference. Preferences are calibrated so that the comfort state
# is MYOPICALLY better than the climb state (greedy takes comfort first), yet only
# the climb path reaches the high-value goal, and over the horizon it wins
# (C_goal * C_climb > C_comfort^2). Greedy gets stuck at comfort; the planner pays
# a worse first step to unlock the goal. The greedy baseline is the STRONGEST
# myopic policy, so the measured gain is honest, not a crippled-comparator artifact.
_DETOUR_A = np.eye(4)
_DETOUR_C = np.array([0.03, 0.22, 0.55, 0.20])  # start, comfort, goal, climb
_DETOUR_B = np.zeros((4, 4, 2))
# action 0 "comfort": start->comfort; comfort/goal/climb absorbing.
_DETOUR_B[:, 0, 0] = [0, 1, 0, 0]
_DETOUR_B[:, 1, 0] = [0, 1, 0, 0]
_DETOUR_B[:, 2, 0] = [0, 0, 1, 0]
_DETOUR_B[:, 3, 0] = [0, 0, 0, 1]
# action 1 "climb": start->climb; climb->goal; comfort/goal absorbing.
_DETOUR_B[:, 0, 1] = [0, 0, 0, 1]
_DETOUR_B[:, 1, 1] = [0, 1, 0, 0]
_DETOUR_B[:, 2, 1] = [0, 0, 1, 0]
_DETOUR_B[:, 3, 1] = [0, 0, 1, 0]
_DETOUR_D = np.array([1.0, 0.0, 0.0, 0.0])
_DETOUR_HORIZON = 2


def greedy_policy_value(
    agent: DiscreteActiveInferenceAgent, qs: ArrayLike, horizon: int
) -> float:
    """Cumulative G of the myopic baseline: pick the lowest-G action each step.

    This is the *strongest honest* one-step-greedy comparator — at every step it
    chooses the action that minimizes the immediate expected free energy and rolls
    that choice forward, with no look-ahead. Comparing the optimal multi-step plan
    against this (not against a deliberately weak policy) is what makes the measured
    look-ahead gain a fair number rather than a rigged win.
    """

    predicted = np.asarray(qs, dtype=np.float64)
    cumulative = 0.0
    n_actions = agent.B.shape[2]
    for _ in range(horizon):
        immediate = np.array(
            [
                expected_free_energy(agent.predict(predicted, a), agent.A, agent.C)[0]
                for a in range(n_actions)
            ]
        )
        action = int(np.argmin(immediate))
        predicted = agent.predict(predicted, action)
        cumulative += float(immediate[action])
    return cumulative


def _lookahead_gain(
    agent: DiscreteActiveInferenceAgent, horizon: int, gamma: float
) -> tuple[float, float, float, float]:
    """Return (optimal_g, greedy_g, gain, best_policy_posterior) for one model."""

    qs = agent.infer_states(obs=0)
    result = agent.evaluate_multistep_policies(qs, horizon, gamma=gamma)
    optimal_g = float(result["G"][result["best_index"]])  # type: ignore[index]
    greedy_g = greedy_policy_value(agent, qs, horizon)
    posterior = np.asarray(result["posterior"], dtype=np.float64)
    return optimal_g, greedy_g, greedy_g - optimal_g, float(np.max(posterior))


def planning_examples() -> dict[str, float]:
    """Multi-step policy posterior and a measured greedy-vs-optimal look-ahead gain.

    The agent plans over every length-``H`` action sequence, accumulating expected
    free energy across the rolled-forward future, then forms a posterior over
    policies. Two contrasting models isolate exactly when look-ahead is worth its
    cost: the decoupled sample/commit model where the optimal plan equals the greedy
    policy (gain = 0), and the coupled investment model where paying a worse first
    step unlocks the goal (gain > 0). The lesson is first-principles, not assumed:
    look-ahead pays only when immediate and long-run value diverge.
    """

    coupled = DiscreteActiveInferenceAgent(_DETOUR_A, _DETOUR_B, _DETOUR_C, _DETOUR_D)
    decoupled = DiscreteActiveInferenceAgent(_PLAN_A, _PLAN_B, _PLAN_C, _PLAN_D)
    opt_c, greedy_c, gain_c, best_post = _lookahead_gain(
        coupled, _DETOUR_HORIZON, _PLAN_GAMMA
    )
    _, _, gain_d, _ = _lookahead_gain(decoupled, _DETOUR_HORIZON, _PLAN_GAMMA)
    return {
        "plan_optimal_policy_g": opt_c,
        "plan_greedy_policy_g": greedy_c,
        "plan_lookahead_gain_coupled": gain_c,
        "plan_lookahead_gain_decoupled": gain_d,
        "plan_best_policy_posterior": best_post,
    }


def planning_lookahead_data() -> dict[str, object]:
    """Return figure data for the multi-step planning look-ahead comparison.

    All values are produced by the same planning kernel that emits the scalar
    claims, so the figure cannot drift from the manuscript numbers.
    """

    coupled = DiscreteActiveInferenceAgent(_DETOUR_A, _DETOUR_B, _DETOUR_C, _DETOUR_D)
    qs = coupled.infer_states(obs=0)
    result = coupled.evaluate_multistep_policies(qs, _DETOUR_HORIZON, gamma=_PLAN_GAMMA)
    policies = cast("list[tuple[int, ...]]", result["policies"])
    g_values = np.asarray(result["G"], dtype=np.float64)
    best_index = int(cast(int, result["best_index"]))

    # Recover the greedy policy's index among the enumerated policies.
    predicted = qs
    greedy_actions: list[int] = []
    for _ in range(_DETOUR_HORIZON):
        immediate = np.array(
            [
                expected_free_energy(
                    coupled.predict(predicted, a), _DETOUR_A, _DETOUR_C
                )[0]
                for a in range(_DETOUR_B.shape[2])
            ]
        )
        action = int(np.argmin(immediate))
        predicted = coupled.predict(predicted, action)
        greedy_actions.append(action)
    greedy_index = list(policies).index(tuple(greedy_actions))

    action_names = {0: "comfort", 1: "climb"}
    labels = ["→".join(action_names[a] for a in policy) for policy in policies]
    decoupled = DiscreteActiveInferenceAgent(_PLAN_A, _PLAN_B, _PLAN_C, _PLAN_D)
    _, _, gain_d, _ = _lookahead_gain(decoupled, _DETOUR_HORIZON, _PLAN_GAMMA)
    _, _, gain_c, _ = _lookahead_gain(coupled, _DETOUR_HORIZON, _PLAN_GAMMA)
    return {
        "policy_labels": labels,
        "policy_g": g_values,
        "greedy_index": greedy_index,
        "optimal_index": best_index,
        "gain_coupled": float(gain_c),
        "gain_decoupled": float(gain_d),
    }


# Canonical predictive-coding example: a vague unit-variance prior centred at zero
# meets a more precise sensory reading (y = 2, half the prior variance). The latent
# estimate settles at the precision-weighted posterior mean, where the sensory and
# prior prediction errors balance (epsilon_o / var_o == epsilon_p / var_p).
_PC_PRIOR_MEAN = 0.0
_PC_PRIOR_VARIANCE = 1.0
_PC_OBSERVATION = 2.0
_PC_OBS_VARIANCE = 0.5


def predictive_coding_examples() -> dict[str, float]:
    """Continuous-state predictive coding settling to the analytic Gaussian posterior."""

    result = predictive_coding_descent(
        _PC_OBSERVATION,
        _PC_PRIOR_MEAN,
        _PC_PRIOR_VARIANCE,
        _PC_OBS_VARIANCE,
        rate=0.1,
        steps=400,
    )
    return {
        "pc_observation": _PC_OBSERVATION,
        "pc_posterior_estimate": result.estimate,
        "pc_sensory_prediction_error": result.sensory_prediction_error,
        "pc_prior_prediction_error": result.prior_prediction_error,
    }


def predictive_coding_data() -> dict[str, object]:
    """Return figure data for the predictive-coding descent (trajectory + errors)."""

    result = predictive_coding_descent(
        _PC_OBSERVATION,
        _PC_PRIOR_MEAN,
        _PC_PRIOR_VARIANCE,
        _PC_OBS_VARIANCE,
        rate=0.1,
        steps=400,
    )
    target = gaussian_posterior_mean(
        _PC_OBSERVATION, _PC_PRIOR_MEAN, _PC_PRIOR_VARIANCE, _PC_OBS_VARIANCE
    )
    steps = np.arange(result.trajectory.shape[0])
    return {
        "steps": steps,
        "trajectory": result.trajectory,
        "free_energy": result.free_energy,
        "analytic_posterior_mean": float(target),
        "observation": _PC_OBSERVATION,
        "prior_mean": _PC_PRIOR_MEAN,
        "steps_to_converge": result.steps_to_converge,
    }


def model_parameter_examples() -> dict[str, float]:
    """Echo the canonical kernel input parameters as claims.

    These are the *inputs* to the worked examples (the disease prior, the sensor
    likelihood entries, the informative-sensor precision, the points-per-skill
    increment). Registering them as claims lets the manuscript reference the exact
    model definition through ``{{claim:...}}`` tokens instead of re-typing numbers
    that could silently drift from the kernel constants.
    """

    return {
        "param_disease_prior_present": float(_DISEASE_PRIOR[0]),
        "param_disease_prior_absent": float(_DISEASE_PRIOR[1]),
        "param_sensor_true_positive": float(_DISEASE_A[0, 0]),
        "param_sensor_false_positive": float(_DISEASE_A[0, 1]),
        "param_informative_sensor_precision": float(_INFORMATIVE_SENSOR_A[0, 0]),
    }


def efe_precision_sweep(samples: int = 101) -> dict[str, FloatArray | float]:
    """Evaluate sample/commit expected free energy across sensor precision."""

    if samples < 5:
        raise ValueError("samples must be at least 5")
    switch = agent_regime_switch_precision()
    sensor_values = np.unique(
        np.concatenate(
            [
                np.linspace(0.5, 0.99, samples, dtype=np.float64),
                np.array([0.9, switch], dtype=np.float64),
            ]
        )
    )
    sample_values: list[float] = []
    commit_values: list[float] = []
    for sensor_precision in sensor_values:
        agent = two_action_regime_agent(float(sensor_precision))
        g_values = agent.evaluate_policies(agent.infer_states(obs=0))
        sample_values.append(float(g_values[0]))
        commit_values.append(float(g_values[1]))
    return {
        "sensor_precision": sensor_values,
        "g_sample": np.array(sample_values, dtype=np.float64),
        "g_commit": np.array(commit_values, dtype=np.float64),
        "switch_precision": switch,
    }


# Units + provenance metadata for each claim name.
_UNITS = {
    "entropy_fair_coin": "nats",
    "entropy_fair_die": "nats",
    "entropy_biased_coin": "nats",
    "surprise_rare_event": "nats",
    "kl_biased_vs_fair": "nats",
    "mutual_info_correlated": "nats",
    "neg_log_evidence_positive": "nats",
    "evidence_probability_positive": "",
    "vfe_descent_end": "nats",
    "vfe_descent_start": "nats",
    "efe_epistemic_uncertain": "nats",
    "efe_epistemic_certain": "nats",
    "efe_pragmatic_certain": "nats",
    "agent_g_sample": "nats",
    "agent_g_commit": "nats",
    "agent_epistemic_sample": "nats",
    "agent_epistemic_commit": "nats",
    "agent_regime_switch_precision": "",
    "bp_marginal_observed_node_state0": "",
    "bp_marginal_neighbor_node_state0": "",
    "bp_smoothing_lift_over_prior": "",
    "dirichlet_prior_mean_positive": "",
    "dirichlet_posterior_mean_positive": "",
    "dirichlet_expected_log_positive": "nats",
    "bmr_log_evidence_full": "nats",
    "bmr_log_evidence_reduced": "nats",
    "bmr_log_bayes_factor": "nats",
    "efe_ambiguity_uniform_belief": "nats",
    "efe_ambiguity_crisp_state": "nats",
    "plan_optimal_policy_g": "nats",
    "plan_greedy_policy_g": "nats",
    "plan_lookahead_gain_coupled": "nats",
    "plan_lookahead_gain_decoupled": "nats",
    "plan_best_policy_posterior": "",
    "pc_observation": "",
    "pc_posterior_estimate": "",
    "pc_sensory_prediction_error": "",
    "pc_prior_prediction_error": "",
    "param_disease_prior_present": "",
    "param_disease_prior_absent": "",
    "param_sensor_true_positive": "",
    "param_sensor_false_positive": "",
    "param_informative_sensor_precision": "",
}


def information_bound_examples() -> dict[str, float]:
    """Bounds that make information quantities checkable rather than asserted.

    Each value here is one side of an inequality the curriculum states in prose,
    so a learner can see the bound hold on a concrete distribution instead of
    taking the inequality on faith:

    * cross-entropy decomposes as entropy plus KL, so the gap between them *is*
      the divergence;
    * entropy is maximal at the uniform distribution over the same support;
    * mutual information is zero exactly when the joint factorizes;
    * KL is asymmetric, which is why direction has to be stated every time.
    """
    biased = [0.9, 0.1]
    fair = [0.5, 0.5]
    independent_joint = np.array([[0.25, 0.25], [0.25, 0.25]])
    skewed_joint = np.array([[0.5, 0.2], [0.2, 0.1]])
    return {
        "cross_entropy_biased_under_fair": cross_entropy(biased, fair),
        "cross_entropy_gap_equals_kl": (cross_entropy(biased, fair) - entropy(biased)),
        "entropy_max_two_state": entropy(fair),
        "entropy_deficit_biased": entropy(fair) - entropy(biased),
        "mutual_info_independent": mutual_information(independent_joint),
        "mutual_info_skewed": mutual_information(skewed_joint),
        "kl_fair_vs_biased": kl_divergence(fair, biased),
        "kl_asymmetry_gap": (kl_divergence(fair, biased) - kl_divergence(biased, fair)),
    }


def dirichlet_examples() -> dict[str, float]:
    """Why a Dirichlet expectation and its log-expectation are not the same number.

    Learners routinely substitute one for the other. Registering both for the
    same concentration vector makes Jensen's gap a value on the page rather than
    a warning in prose, and shows the gap shrinking as evidence accumulates.
    """
    sparse = np.array([1.0, 1.0, 2.0])
    dense = np.array([10.0, 10.0, 20.0])
    sparse_expected = float(dirichlet_expected(sparse)[-1])
    sparse_log = float(dirichlet_expected_log(sparse)[-1])
    dense_expected = float(dirichlet_expected(dense)[-1])
    dense_log = float(dirichlet_expected_log(dense)[-1])
    return {
        "dirichlet_expected_sparse": sparse_expected,
        "dirichlet_expected_log_sparse": sparse_log,
        "dirichlet_jensen_gap_sparse": float(np.log(sparse_expected)) - sparse_log,
        "dirichlet_expected_dense": dense_expected,
        "dirichlet_jensen_gap_dense": float(np.log(dense_expected)) - dense_log,
    }


def evidence_bound_examples() -> dict[str, float]:
    """The ELBO/free-energy bound stated as a gap that closes at the posterior.

    The supplement argues that variational free energy upper-bounds surprise and
    is tight at the exact posterior. These claims quantify the slack at a
    deliberately poor belief and at the posterior, so tightness is observable.
    """
    obs = 0
    posterior = bayes_posterior(_DISEASE_PRIOR, _DISEASE_A, obs)
    uniform = np.ones(len(_DISEASE_PRIOR)) / len(_DISEASE_PRIOR)
    negative_log_evidence = -log_evidence(_DISEASE_A, obs, _DISEASE_PRIOR)
    free_energy_uniform = variational_free_energy(
        uniform, _DISEASE_A, obs, _DISEASE_PRIOR
    )
    free_energy_posterior = variational_free_energy(
        posterior, _DISEASE_A, obs, _DISEASE_PRIOR
    )
    return {
        "evidence_bound_slack_uniform": free_energy_uniform - negative_log_evidence,
        "evidence_bound_slack_posterior": (
            free_energy_posterior - negative_log_evidence
        ),
        "elbo_posterior": elbo(posterior, _DISEASE_A, obs, _DISEASE_PRIOR),
        "elbo_uniform": elbo(uniform, _DISEASE_A, obs, _DISEASE_PRIOR),
    }


def policy_precision_examples() -> dict[str, float]:
    """What the precision parameter over policies actually does.

    Learners are told precision "controls exploration" without seeing the limit
    behavior. Registering the entropy of the policy posterior at low, reference
    and high precision makes both limits observable: as precision falls the
    posterior approaches the uniform distribution (maximum entropy for three
    policies, $\\ln 3$), and as it rises the posterior concentrates on the
    lowest-expected-free-energy policy and entropy approaches zero.
    """
    policy_values = np.array([0.20, 0.55, 1.40])
    uniform_entropy = float(np.log(len(policy_values)))
    low = policy_posterior(policy_values, gamma=0.05)
    reference = policy_posterior(policy_values, gamma=1.0)
    high = policy_posterior(policy_values, gamma=24.0)
    return {
        "policy_entropy_low_precision": entropy(low),
        "policy_entropy_reference_precision": entropy(reference),
        "policy_entropy_high_precision": entropy(high),
        "policy_entropy_uniform_ceiling": uniform_entropy,
        "policy_entropy_low_precision_deficit": uniform_entropy - entropy(low),
        "policy_best_mass_high_precision": float(high[int(np.argmin(policy_values))]),
    }


def efe_decomposition_examples() -> dict[str, float]:
    """Expected free energy is exactly its two components, not approximately.

    The supplement states $G = -(\\text{epistemic} + \\text{pragmatic})$. Registering
    the residual of that identity turns a stated decomposition into a checked
    one: if a future refactor changes the sign convention or drops a term, the
    residual stops being zero and the claim ledger says so.
    """
    predicted_states = np.array([0.62, 0.38])
    total, epistemic, pragmatic = expected_free_energy(
        predicted_states, _INFORMATIVE_SENSOR_A, np.array([0.9, 0.1])
    )
    return {
        "efe_identity_total": total,
        "efe_identity_epistemic": epistemic,
        "efe_identity_pragmatic": pragmatic,
        "efe_identity_residual": total + (epistemic + pragmatic),
    }


def precision_weighting_examples() -> dict[str, float]:
    """Precision weighting is literally a weighted average of two sources.

    The Gaussian posterior mean sits between the prior mean and the observation,
    at a position set by the two precisions. Registering the analytic mixing
    weight next to the residual against the kernel's own result shows the
    combination is exact, and shows the mean moving toward whichever source is
    more precise rather than toward whichever is louder.
    """
    observation = 4.0
    prior_mean = 1.0
    confident_prior = gaussian_posterior_mean(observation, prior_mean, 0.25, 4.0)
    confident_sensor = gaussian_posterior_mean(observation, prior_mean, 4.0, 0.25)
    obs_weight = (1.0 / 4.0) / ((1.0 / 4.0) + (1.0 / 0.25))
    analytic_confident_prior = prior_mean + obs_weight * (observation - prior_mean)
    return {
        "precision_weight_on_observation": obs_weight,
        "posterior_mean_confident_prior": confident_prior,
        "posterior_mean_confident_sensor": confident_sensor,
        "posterior_mean_analytic_residual": (
            confident_prior - analytic_confident_prior
        ),
        "posterior_mean_precision_shift": confident_sensor - confident_prior,
    }


def build_claim_registry() -> ClaimRegistry:
    """Run every worked example and register all claims (the curriculum's source of truth)."""
    registry = ClaimRegistry()
    producers = {
        "info_examples": info_examples,
        "softmax_examples": softmax_examples,
        "inference_examples": inference_examples,
        "efe_examples": efe_examples,
        "efe_ambiguity_examples": efe_ambiguity_examples,
        "agent_example": agent_example,
        "message_passing_examples": message_passing_examples,
        "learning_examples": learning_examples,
        "model_reduction_examples": model_reduction_examples,
        "planning_examples": planning_examples,
        "predictive_coding_examples": predictive_coding_examples,
        "model_parameter_examples": model_parameter_examples,
        "information_bound_examples": information_bound_examples,
        "dirichlet_examples": dirichlet_examples,
        "evidence_bound_examples": evidence_bound_examples,
        "policy_precision_examples": policy_precision_examples,
        "efe_decomposition_examples": efe_decomposition_examples,
        "precision_weighting_examples": precision_weighting_examples,
    }
    for source, fn in producers.items():
        for name, value in fn().items():
            registry.register(
                name,
                round(float(value), 6),
                units=_UNITS.get(name, ""),
                source=f"src.kernels.examples.{source}",
            )
    return registry
