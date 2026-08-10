"""Message-passing curriculum expansion.

A connected Computation-stratum ladder that deepens the previously shallow
message-passing coverage: factor graphs, the sum-product algorithm, belief
propagation on trees, variational message passing, and loopy belief propagation.
Each skill anchors on existing graphical-model and variational skills so the
prerequisite DAG stays connected and acyclic.
"""

from __future__ import annotations

from src.curriculum._ext_helpers import _C, _q, _s
from src.curriculum.model import Skill

_MESSAGE_PASSING: list[Skill] = [
    _s(
        "mp_factor_graphs",
        "Factor Graphs and Conditional Independence",
        _C,
        "Read a factorised joint distribution as a bipartite factor graph.",
        "A factor graph draws variables and factors as two kinds of nodes, with an edge "
        "wherever a factor depends on a variable. It makes the conditional-independence "
        "structure of a model explicit: the absence of an edge is a modelling commitment "
        "that two quantities interact only through the variables they share.",
        ("front_prob_graphical_models", "vm_message_passing"),
        _q(
            "In a factor graph, a missing edge between a factor and a variable encodes:",
            [
                "That the factor does not depend on that variable",
                "That the variable is unobserved",
                "That the variable has the largest domain",
            ],
            0,
        ),
        _q(
            "Why represent a model as a factor graph before inference?",
            [
                "It exposes the conditional-independence structure inference exploits",
                "It guarantees the model is linear",
                "It removes the need to specify any factors",
            ],
            0,
        ),
        tags=("message-passing", "computation", "graphical-models"),
    ),
    _s(
        "mp_sum_product",
        "The Sum-Product Algorithm",
        _C,
        "Compute marginals by passing and multiplying local messages.",
        "Sum-product computes a variable's marginal as the product of incoming messages "
        "from its neighbouring factors, where each factor message sums out the other "
        "variables it touches. On a tree the schedule is exact and each message is reused "
        "by every marginal that needs it, turning a global sum into local work.",
        ("mp_factor_graphs",),
        _q(
            "A factor-to-variable message in sum-product is formed by:",
            [
                "Summing the factor over its other variables, weighted by their messages",
                "Taking the maximum incoming message unchanged",
                "Ignoring the other variables the factor touches",
            ],
            0,
        ),
        _q(
            "On a tree-structured graph, the sum-product marginals are:",
            ["Exact", "Always approximate", "Undefined"],
            0,
        ),
        tags=("message-passing", "computation"),
    ),
    _s(
        "mp_belief_propagation",
        "Belief Propagation on Trees",
        _C,
        "Schedule sum-product messages to obtain every marginal in two sweeps.",
        "Belief propagation is sum-product organised as a leaf-to-root then root-to-leaf "
        "sweep, so a single pass in each direction yields every variable's marginal. The "
        "belief at a node is its local evidence times the product of stabilised incoming "
        "messages, which is why the schedule terminates exactly on an acyclic graph. On a "
        "worked three-node sticky chain, a single informative reading at the middle node "
        "(posterior {{claim:bp_marginal_observed_node_state0}}) propagates outward and "
        "lifts each unobserved neighbour to {{claim:bp_marginal_neighbor_node_state0}}, a "
        "smoothing lift of {{claim:bp_smoothing_lift_over_prior}} above an even prior — "
        "and these marginals match a brute-force enumeration of the full joint exactly.",
        ("mp_sum_product", "comp_belief_update"),
        _q(
            "Why do two message sweeps suffice for all marginals on a tree?",
            [
                "Each edge carries one converged message in each direction",
                "Trees have no factors to evaluate",
                "Marginals on a tree are always uniform",
            ],
            0,
        ),
        tags=("message-passing", "computation"),
    ),
    _s(
        "mp_variational_message_passing",
        "Variational Message Passing",
        _C,
        "Turn coordinate-ascent on a mean-field bound into local message updates.",
        "Variational message passing recasts mean-field coordinate ascent as messages: "
        "each factor sends expected sufficient statistics to its neighbours, and a "
        "variable updates its approximate posterior from the messages it receives. It "
        "extends exact propagation to intractable models by optimising a bound instead of "
        "computing exact marginals.",
        ("mp_belief_propagation", "vm_mean_field"),
        _q(
            "What does a variational message carry between factors and variables?",
            [
                "Expected sufficient statistics under the current approximate posterior",
                "The exact joint distribution over all variables",
                "A random sample drawn from the prior",
            ],
            0,
        ),
        tags=("message-passing", "computation", "variational"),
    ),
    _s(
        "mp_loopy_belief_propagation",
        "Loopy Belief Propagation and Convergence",
        _C,
        "Apply message passing to graphs with cycles and reason about its fixed points.",
        "Running belief propagation on a graph with cycles drops the exactness guarantee: "
        "messages may oscillate or settle on an approximate fixed point that corresponds "
        "to a stationary point of the Bethe free energy. Practitioners damp updates and "
        "monitor convergence rather than assuming the returned beliefs are true marginals.",
        ("mp_variational_message_passing", "impl_scaling_tradeoffs"),
        _q(
            "On a graph with cycles, the beliefs returned by loopy propagation are:",
            [
                "Approximate fixed points, not guaranteed to be the true marginals",
                "Always the exact marginals",
                "Guaranteed to converge in two sweeps",
            ],
            0,
        ),
        _q(
            "A common remedy when loopy messages oscillate is to:",
            [
                "Damp the message updates and monitor convergence",
                "Delete every factor with more than one variable",
                "Assume convergence after the first sweep",
            ],
            0,
        ),
        tags=("message-passing", "computation"),
    ),
]
