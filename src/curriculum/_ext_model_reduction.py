"""Model-reduction, structured-approximation, and bound-tightness expansion.

A Variational-Methods-stratum subject closing the triple-check content gaps on Bayesian
model reduction, structured vs mean-field approximations, sparse transition structure,
and the exact VFE / log-evidence bound gap. Skills anchor on the existing ELBO, mean-field,
free-energy, and KL skills so the prerequisite DAG stays connected and acyclic.
"""

from __future__ import annotations

from src.curriculum._ext_helpers import _VM, _q, _s
from src.curriculum.model import Skill

_MODEL_REDUCTION: list[Skill] = [
    _s(
        "vm_bayesian_model_reduction",
        "Bayesian Model Reduction",
        _VM,
        "Compare nested models by re-scoring a fitted posterior under simpler priors.",
        "Bayesian model reduction evaluates how the free energy of an already-fitted model "
        "would change under a simpler (more precise or zeroed) prior, without re-fitting. "
        "Because the likelihood is unchanged, the evidence difference is a closed-form "
        "function of the posterior and the two priors, so many candidate reductions can be "
        "scored cheaply to prune redundant parameters and recover a sparser model.",
        ("vm_elbo", "vm_free_energy"),
        _q(
            "Bayesian model reduction re-scores evidence under a simpler prior by reusing:",
            [
                "The already-fitted posterior, without re-running inference",
                "A fresh fit of every candidate model from scratch",
                "Only the raw data, ignoring the fitted posterior",
            ],
            0,
        ),
        _q(
            "What stays fixed across the models compared in Bayesian model reduction?",
            [
                "The likelihood; only the prior changes",
                "The prior; only the likelihood changes",
                "Both the prior and the likelihood change",
            ],
            0,
        ),
        tags=("model-reduction", "variational", "sparsity"),
    ),
    _s(
        "vm_structured_approximations",
        "Structured vs Mean-Field Approximations",
        _VM,
        "Trade approximation accuracy for tractability by keeping selected posterior couplings.",
        "A mean-field posterior factorises completely and so cannot represent correlations "
        "between latent variables; a structured (or marginal) approximation keeps chosen "
        "dependency edges, reducing the bound gap where those correlations matter at the "
        "cost of more expensive updates. Choosing the factorisation is itself a modelling "
        "decision about which posterior couplings are worth paying for.",
        ("vm_mean_field", "vm_bayesian_model_reduction"),
        _q(
            "What can a fully mean-field posterior NOT represent?",
            [
                "Correlations between latent variables",
                "The marginal of any single variable",
                "A Gaussian over one variable",
            ],
            0,
        ),
        tags=("model-reduction", "variational"),
    ),
    _s(
        "vm_sparse_transition_structure",
        "Sparse and Factorised Transition Structure",
        _VM,
        "Exploit conditional independence so inference scales with structure, not state count.",
        "When a transition model factorises across hidden-state factors, the joint update "
        "decomposes into smaller per-factor updates, and zeros in the dependency structure "
        "remove terms from the variational objective entirely. Sparsity is therefore not "
        "just a storage saving: it is the conditional-independence structure that makes "
        "message passing and model reduction tractable at scale.",
        ("vm_structured_approximations",),
        _q(
            "A sparse, factorised transition structure makes inference cheaper because:",
            [
                "Conditional independence decomposes the update into smaller per-factor terms",
                "It increases the number of coupled variables to track",
                "It forces every variable to depend on every other",
            ],
            0,
        ),
        tags=("model-reduction", "variational", "sparsity"),
    ),
    _s(
        "vm_bound_tightness",
        "Bound Tightness: the VFE–Evidence Gap",
        _VM,
        "Quantify exactly how far variational free energy sits above the negative log-evidence.",
        "The gap between variational free energy and the negative log-evidence is exactly "
        "the divergence between the approximate posterior and the true posterior, so the "
        "bound is tight precisely when that divergence vanishes. Tracking the gap turns "
        "'is my approximation good enough?' into a measurable quantity: a structured "
        "approximation earns its cost only if it shrinks this gap where it matters.",
        ("vm_elbo", "it_kl"),
        _q(
            "The gap between variational free energy and the negative log-evidence equals:",
            [
                "The divergence between the approximate and the true posterior",
                "The entropy of the prior",
                "A constant independent of the approximation",
            ],
            0,
        ),
        _q(
            "The variational bound is tight exactly when:",
            [
                "The approximate posterior equals the true posterior",
                "The prior is uniform",
                "The likelihood is deterministic",
            ],
            0,
        ),
        tags=("model-reduction", "variational"),
    ),
]
