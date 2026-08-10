"""Continuous-time and generalized-coordinate active inference expansion.

An Active-Inference-stratum subject closing the triple-check content gaps on generalized
coordinates, discrete-continuous embedding, and multi-scale temporal hierarchies. Skills
anchor on existing state-estimation, derivative, and hierarchical-depth skills so the DAG
stays connected and acyclic.
"""

from __future__ import annotations

from src.curriculum._ext_helpers import _AI, _q, _s
from src.curriculum.model import Skill

_CONTINUOUS_TIME_AIF: list[Skill] = [
    _s(
        "ai_generalized_coordinates",
        "Generalized Coordinates of Motion",
        _AI,
        "Represent a continuous state by stacking it with its successive time-derivatives.",
        "In continuous-time active inference a state is tracked together with its velocity, "
        "acceleration, and higher derivatives — a point in generalized coordinates of "
        "motion. Beliefs become trajectories rather than instantaneous estimates, and "
        "prediction errors are computed at each order, which is what lets a predictive-"
        "coding agent anticipate smooth dynamics instead of reacting to samples one at a time. "
        "Even at a single order the mechanism is exact for the linear-Gaussian case: descending "
        "the free energy along precision-weighted prediction errors settles the estimate at "
        "{{claim:pc_posterior_estimate}}, the analytic posterior mean, where the sensory error "
        "{{claim:pc_sensory_prediction_error}} and the prior error {{claim:pc_prior_prediction_error}} "
        "balance once weighted by their precisions.",
        ("ai_state_estimation", "m_derivative"),
        _q(
            "A state in generalized coordinates of motion is represented by:",
            [
                "The state stacked with its successive time-derivatives",
                "A single instantaneous value with no dynamics",
                "Only the second derivative, discarding position",
            ],
            0,
        ),
        _q(
            "Why do generalized coordinates help a continuous-time agent?",
            [
                "Beliefs become trajectories, so the agent can anticipate smooth dynamics",
                "They remove the need for any generative model",
                "They make the state discrete and finite",
            ],
            0,
        ),
        tags=("continuous-time", "active-inference", "predictive-coding"),
    ),
    _s(
        "ai_discrete_continuous_embedding",
        "Embedding Discrete Decisions in Continuous Dynamics",
        _AI,
        "Bridge a discrete policy layer to a continuous state-space it sets points for.",
        "Mixed models couple a discrete active-inference layer that selects policies to a "
        "continuous layer that realises them: the discrete outcome supplies a prior over "
        "continuous setpoints, and the continuous layer's evidence feeds back as a "
        "likelihood for the discrete states. The interface is the place where symbolic "
        "decisions and smooth control have to agree on a shared free-energy accounting.",
        ("ai_generalized_coordinates", "ai_state_estimation"),
        _q(
            "In a mixed discrete-continuous model, the discrete layer supplies the "
            "continuous layer with:",
            [
                "A prior over continuous setpoints to realise",
                "The raw sensory data stream",
                "Its own optimiser, bypassing free energy",
            ],
            0,
        ),
        tags=("continuous-time", "active-inference"),
    ),
    _s(
        "ai_multi_scale_temporal_hierarchies",
        "Multi-Scale Temporal Hierarchies",
        _AI,
        "Let slow high-level beliefs supply priors for fast low-level updates across timescales.",
        "Deep temporal models separate timescales: a high level that changes slowly supplies "
        "empirical priors to a faster low level, so context set higher up constrains moment-"
        "to-moment inference below. Free energy decomposes across levels and timescales, and "
        "the same minimisation that updates a fast percept also slowly revises the context "
        "that framed it — the structural basis of planning over nested horizons.",
        ("ai_generalized_coordinates", "hier_temporal_depth_policies"),
        _q(
            "In a multi-scale temporal hierarchy, the slow high level mainly provides:",
            [
                "Empirical priors that constrain the faster low level",
                "The fastest sensory sampling clock",
                "A replacement for the low-level likelihood",
            ],
            0,
        ),
        tags=("continuous-time", "active-inference", "hierarchical"),
    ),
]
