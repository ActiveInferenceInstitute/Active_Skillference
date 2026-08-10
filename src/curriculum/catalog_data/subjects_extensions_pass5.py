"""Pass-5 and depth-expansion extension subjects."""

from __future__ import annotations

from .._ext_cogsec_collective import (
    _NEW_COGSEC,
    _NEW_COLLECTIVE,
)
from .._ext_continuous_time_aif import _CONTINUOUS_TIME_AIF
from .._ext_dynamical_geometry import (
    _NEW_DYNAMICAL,
    _NEW_GEOMETRY,
)
from .._ext_info_implementation import (
    _NEW_IMPLEMENTATION,
    _NEW_INFO_MEASURES,
)
from .._ext_learning_hierarchical import (
    _NEW_HIERARCHICAL,
    _NEW_LEARNING,
)
from .._ext_message_passing import _MESSAGE_PASSING
from .._ext_model_reduction import _MODEL_REDUCTION
from .._ext_precision_exploration import _PRECISION_EXPLORATION
from ..authoring import (
    _AI,
    _APP,
    _C,
    _IT,
    _M,
    _VM,
)
from ..model import Subject


def pass5_extension_subjects() -> list[Subject]:
    return [
        Subject(
            "sub_dynamical",
            "Dynamical Systems & Stochastic Calculus",
            _M,
            "Flows, stability, SDEs, Fokker-Planck and the NESS the FEP rests on.",
            tuple(_NEW_DYNAMICAL),
        ),
        Subject(
            "sub_geometry",
            "Information Geometry & Natural Gradient",
            _M,
            "Statistical manifolds, the Fisher metric, dual flatness and natural-gradient inference.",
            tuple(_NEW_GEOMETRY),
        ),
        Subject(
            "sub_info_measures",
            "Advanced Information Measures",
            _IT,
            "AEP, capacity, rate-distortion, Fisher, transfer entropy, empowerment and Landauer.",
            tuple(_NEW_INFO_MEASURES),
        ),
        Subject(
            "sub_learning",
            "Learning, Novelty & Structure Learning",
            _AI,
            "Dirichlet parameter learning, novelty, model reduction and structure learning.",
            tuple(_NEW_LEARNING),
        ),
        Subject(
            "sub_hierarchical",
            "Hierarchical, Deep & Mixed Models",
            _AI,
            "Empirical priors, deep temporal and hybrid models, attention as precision.",
            tuple(_NEW_HIERARCHICAL),
        ),
        Subject(
            "sub_implementation",
            "Implementation, Simulation & Scaling",
            _C,
            "Vectorised updates, logsumexp, sampling, amortised inference and reproducibility.",
            tuple(_NEW_IMPLEMENTATION),
        ),
        Subject(
            "sub_cogsec",
            "Cognitive Security & Information Ecosystems",
            _APP,
            "Shared generative models, precision attacks, trust, resilience and epistemic health.",
            tuple(_NEW_COGSEC),
        ),
        Subject(
            "sub_collective",
            "Collective Behaviour & Multi-Agent Inference",
            _APP,
            "Stigmergy, swarm inference, shared blankets, niche construction and synchrony.",
            tuple(_NEW_COLLECTIVE),
        ),
        Subject(
            "sub_message_passing",
            "Message Passing on Factor Graphs",
            _C,
            "Factor graphs, sum-product, belief propagation, variational message "
            "passing and loopy propagation as one connected computational ladder.",
            tuple(_MESSAGE_PASSING),
        ),
        Subject(
            "sub_precision_exploration",
            "Precision, Exploration and Guidance",
            _AI,
            "Precision as unified confidence control, entropy-regularised exploration, "
            "the explore-exploit frontier, and risk-sensitive guidance functions.",
            tuple(_PRECISION_EXPLORATION),
        ),
        Subject(
            "sub_model_reduction",
            "Model Reduction, Structure and Bound Tightness",
            _VM,
            "Bayesian model reduction, structured vs mean-field approximations, sparse "
            "transition structure, and the exact VFE / log-evidence bound gap.",
            tuple(_MODEL_REDUCTION),
        ),
        Subject(
            "sub_continuous_time_aif",
            "Continuous-Time and Generalized-Coordinate AIF",
            _AI,
            "Generalized coordinates of motion, embedding discrete decisions in "
            "continuous dynamics, and multi-scale temporal hierarchies.",
            tuple(_CONTINUOUS_TIME_AIF),
        ),
    ]
