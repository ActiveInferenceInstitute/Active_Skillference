"""Discrete probabilistic kernels for information and active inference."""

from __future__ import annotations

from .active_inference import (
    DiscreteActiveInferenceAgent,
    expected_free_energy,
    policy_posterior,
)
from .distributions import (
    dirichlet_expected,
    dirichlet_expected_log,
    log_stable,
    normalize,
    softmax,
)
from .inference import bayes_posterior, elbo, log_evidence, variational_free_energy
from .information import (
    cross_entropy,
    entropy,
    kl_divergence,
    mutual_information,
    surprise,
)

__all__ = [
    "DiscreteActiveInferenceAgent",
    "bayes_posterior",
    "cross_entropy",
    "dirichlet_expected",
    "dirichlet_expected_log",
    "elbo",
    "entropy",
    "expected_free_energy",
    "kl_divergence",
    "log_evidence",
    "log_stable",
    "mutual_information",
    "normalize",
    "policy_posterior",
    "softmax",
    "surprise",
    "variational_free_energy",
]
