"""Precision, exploration, and guidance curriculum expansion.

An Active-Inference-stratum subject that unifies the previously scattered treatment
of precision, adds explicit exploration / entropy-regularisation coverage, and
introduces the guidance (risk-sensitive) view of policy selection. Skills anchor on
the existing precision, epistemic-value, and policy skills to keep the DAG connected.
"""

from __future__ import annotations

from src.curriculum._ext_helpers import _AI, _q, _s
from src.curriculum.model import Skill

_PRECISION_EXPLORATION: list[Skill] = [
    _s(
        "pex_precision_unified",
        "Precision as Confidence and Uncertainty Control",
        _AI,
        "Read precision as the inverse-variance weighting that gates every belief update.",
        "Precision is the confidence the agent assigns to a signal: high precision sharpens "
        "a distribution and lets it dominate an update, low precision flattens it and defers "
        "to other evidence. The same construct appears as sensory-precision weighting of "
        "prediction errors and as the policy precision that sharpens action selection, "
        "which is why precision, not a new mechanism each time, unifies attention and "
        "decision confidence.",
        ("ai_precision_gamma", "fep_precision"),
        _q(
            "Raising the precision on a signal makes the agent:",
            [
                "Weight that signal more strongly in its update",
                "Ignore that signal entirely",
                "Replace the signal with a uniform distribution",
            ],
            0,
        ),
        _q(
            "Why is precision described as a unifying construct?",
            [
                "The same inverse-variance weighting governs both attention and action confidence",
                "It only ever applies to motor commands",
                "It is a separate mechanism for each modality",
            ],
            0,
        ),
        tags=("precision", "active-inference", "attention"),
    ),
    _s(
        "pex_entropy_regularization",
        "Entropy Regularisation and Exploration Bonuses",
        _AI,
        "Connect the entropy of the policy posterior to deliberate exploration.",
        "Lowering the policy precision keeps the policy posterior high-entropy, which spreads "
        "probability across actions and produces exploration; raising it concentrates mass on "
        "the lowest-expected-free-energy policy and produces exploitation. Read this way the "
        "precision term plays the role of an entropy regulariser, the active-inference analogue "
        "of an exploration bonus in reinforcement learning.",
        ("pex_precision_unified", "ai_epistemic_value"),
        _q(
            "Decreasing policy precision changes the policy posterior by:",
            [
                "Raising its entropy, spreading probability across more policies",
                "Forcing it onto a single deterministic policy",
                "Making expected free energy irrelevant",
            ],
            0,
        ),
        _q(
            "Entropy regularisation of the policy posterior is the active-inference analogue of:",
            [
                "An exploration bonus in reinforcement learning",
                "A fixed learning-rate schedule",
                "A replay buffer",
            ],
            0,
        ),
        tags=("exploration", "active-inference", "precision"),
    ),
    _s(
        "pex_explore_exploit_frontier",
        "The Exploration–Exploitation Frontier",
        _AI,
        "Trace how the epistemic and pragmatic terms of expected free energy trade off.",
        "Expected free energy already contains both an epistemic term that rewards "
        "uncertainty-reducing actions and a pragmatic term that rewards preferred outcomes, "
        "so an active-inference agent does not need a bolt-on exploration heuristic. The "
        "balance shifts with residual uncertainty: when the world is ambiguous the epistemic "
        "term dominates and the agent gathers information, and as uncertainty resolves the "
        "pragmatic term takes over and the agent pursues its goals.",
        ("pex_entropy_regularization", "ai_explore_exploit"),
        _q(
            "Why does an active-inference agent not need a separate exploration heuristic?",
            [
                "Expected free energy already includes an epistemic, uncertainty-reducing term",
                "It never explores under any circumstances",
                "Exploration is added afterwards as a random tie-breaker",
            ],
            0,
        ),
        _q(
            "As state uncertainty resolves, the agent's behaviour shifts toward:",
            [
                "The pragmatic term, pursuing preferred outcomes",
                "Pure random action",
                "Refusing to act",
            ],
            0,
        ),
        tags=("exploration", "active-inference"),
    ),
    _s(
        "pex_guidance_risk_sensitivity",
        "Guidance Functions and Risk-Sensitive Policies",
        _AI,
        "Distinguish risk (divergence from preferences) from ambiguity in policy scoring.",
        "The guidance view decomposes the pragmatic part of expected free energy into a risk "
        "term, the divergence between predicted and preferred outcomes, and an ambiguity term, "
        "the expected uncertainty of the likelihood. Shaping the preference distribution C is "
        "therefore how a designer steers behaviour: tightening C makes the policy risk-averse "
        "about deviating from goals, while flattening it tolerates a wider band of outcomes.",
        ("pex_explore_exploit_frontier", "ai_risk_ambiguity"),
        _q(
            "In the guidance decomposition, the risk term measures:",
            [
                "Divergence between predicted outcomes and the preference distribution",
                "The wall-clock time to evaluate a policy",
                "The number of policies considered",
            ],
            0,
        ),
        _q(
            "How does tightening the preference distribution C affect a policy?",
            [
                "It makes the policy more risk-averse about deviating from goals",
                "It removes the epistemic term entirely",
                "It makes every policy equally likely",
            ],
            0,
        ),
        tags=("guidance", "active-inference", "policy"),
    ),
    _s(
        "pex_rate_distortion_efe",
        "Rate-Distortion and the Epistemic-Pragmatic Trade-Off",
        _AI,
        "Read expected free energy as a rate-distortion trade-off between information and value.",
        "Rate-distortion theory asks for the least information an agent must keep to hold "
        "expected distortion below a bound; expected free energy makes the mirror trade-off, "
        "balancing the epistemic value of an observation against the pragmatic value of a "
        "preferred outcome. Both say a bounded agent should pay for information only to the "
        "extent it buys reduced cost, which is why precision behaves like the slope that "
        "sets the exchange rate between bits gathered and value pursued.",
        ("ai_expected_free_energy", "im_rate_distortion", "ai_epistemic_value"),
        _q(
            "Expected free energy and rate-distortion theory share which structure?",
            [
                "A trade-off between information kept/gathered and a value/distortion cost",
                "A requirement that the agent ignore all preferences",
                "An assumption that information is free to acquire",
            ],
            0,
        ),
        _q(
            "In this reading, precision plays the role of:",
            [
                "The slope setting the exchange rate between information and value",
                "A fixed constant unrelated to the trade-off",
                "The number of policies considered",
            ],
            0,
        ),
        tags=("guidance", "active-inference", "information-theory"),
    ),
]
