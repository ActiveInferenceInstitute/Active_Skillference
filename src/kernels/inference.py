"""Discrete Bayesian and variational inference helpers."""

from __future__ import annotations

from typing import TypeAlias

import numpy as np
from numpy.typing import ArrayLike, NDArray
from scipy.special import logsumexp

from .distributions import log_stable, normalize

FloatArray: TypeAlias = NDArray[np.float64]
_PROB_TOL = 1e-9


def _as_probability_vector(x: ArrayLike, *, name: str) -> FloatArray:
    """Validate and return a one-dimensional probability vector."""

    values = np.asarray(x, dtype=np.float64)
    if values.ndim != 1:
        raise ValueError(f"{name} must be a 1D probability vector")
    if np.any(values < 0.0):
        raise ValueError(f"{name} must be non-negative and sum to 1")
    if not np.isclose(np.sum(values), 1.0, atol=_PROB_TOL, rtol=0.0):
        raise ValueError(f"{name} must sum to 1")
    return values


def _validate_model(prior: FloatArray, A: FloatArray, obs: int) -> None:
    """Validate shared discrete-state model inputs.

    A likelihood ``A[o, s] = P(o | s)`` must be a proper conditional distribution: every
    entry non-negative and every COLUMN (the distribution over observations for a fixed
    state) summing to 1. Without this, a malformed matrix (negative entries, unnormalized
    columns) produces a finite, plausible-looking free energy / log-evidence with no error
    — exactly the silent-garbage path a high-integrity teaching kernel must refuse.
    """

    if A.ndim != 2:
        raise ValueError("A must be a 2D likelihood matrix")
    if prior.shape[0] != A.shape[1]:
        raise ValueError("prior length must match the number of states in A")
    if obs < 0 or obs >= A.shape[0]:
        raise ValueError("obs index out of range for A")
    if np.any(A < 0.0):
        raise ValueError("A must be non-negative (it is a likelihood P(o|s))")
    if not np.allclose(np.sum(A, axis=0), 1.0, atol=_PROB_TOL, rtol=0.0):
        raise ValueError("each column of A (P(o|s) for fixed state s) must sum to 1")


def bayes_posterior(prior: ArrayLike, A: ArrayLike, obs: int) -> FloatArray:
    """Return the exact posterior over states for a discrete observation model.

    Args:
        prior: Prior state distribution over latent states.
        A: Likelihood matrix `P(o | s)` with shape `(n_obs, n_states)`.
        obs: Observed row index into `A`.

    Returns:
        Exact posterior distribution `P(s | o)`.

    Raises:
        ValueError: If the prior is invalid or `obs` is outside the rows of `A`.
    """

    prior_probs = _as_probability_vector(prior, name="prior")
    likelihood = np.asarray(A, dtype=np.float64)
    _validate_model(prior_probs, likelihood, obs)
    posterior_unnormalized = likelihood[obs, :] * prior_probs
    return normalize(posterior_unnormalized)


def variational_free_energy(
    q: ArrayLike,
    A: ArrayLike,
    obs: int,
    prior: ArrayLike,
) -> float:
    """Return variational free energy for a discrete latent-state model.

    The convention used here is
    `F(q) = KL[q || prior] - E_q[log P(o | s)]`, measured in nats.

    Args:
        q: Approximate posterior over states.
        A: Likelihood matrix `P(o | s)` with shape `(n_obs, n_states)`.
        obs: Observed row index into `A`.
        prior: Prior state distribution.

    Returns:
        Variational free energy in nats.

    Raises:
        ValueError: If `q` or `prior` is invalid or if `obs` is out of range.
    """

    q_probs = _as_probability_vector(q, name="q")
    prior_probs = _as_probability_vector(prior, name="prior")
    likelihood = np.asarray(A, dtype=np.float64)
    _validate_model(prior_probs, likelihood, obs)
    if q_probs.shape[0] != prior_probs.shape[0]:
        raise ValueError("q length must match prior length")

    mask = q_probs > 0.0
    energy = np.sum(
        q_probs[mask] * (log_stable(q_probs[mask]) - log_stable(prior_probs[mask]))
    )
    accuracy_cost = np.sum(q_probs[mask] * log_stable(likelihood[obs, mask]))
    return float(energy - accuracy_cost)


def log_evidence(A: ArrayLike, obs: int, prior: ArrayLike) -> float:
    """Return log model evidence `log P(o)` for a discrete observation.

    Args:
        A: Likelihood matrix `P(o | s)` with shape `(n_obs, n_states)`.
        obs: Observed row index into `A`.
        prior: Prior state distribution.

    Returns:
        Log evidence in nats.

    Raises:
        ValueError: If the prior is invalid or `obs` is outside the rows of `A`.
    """

    prior_probs = _as_probability_vector(prior, name="prior")
    likelihood = np.asarray(A, dtype=np.float64)
    _validate_model(prior_probs, likelihood, obs)
    return float(logsumexp(log_stable(likelihood[obs, :]) + log_stable(prior_probs)))


def belief_propagation_chain(
    prior: ArrayLike,
    transitions: ArrayLike,
    evidence: ArrayLike,
) -> FloatArray:
    """Return exact per-node marginals on a discrete chain via sum-product.

    This is the forward-backward (belief propagation) algorithm on a linear
    factor graph ``s_0 - s_1 - ... - s_{N-1}`` with a Markov transition factor on
    each edge and a local evidence (observation) potential on each node. On a tree
    — and a chain is a tree — sum-product returns the *exact* node marginals, so
    the result is identical to brute-force enumeration of the joint (the natural
    non-vacuous oracle, asserted in the tests).

    Args:
        prior: Prior distribution over the first node's state, shape ``(K,)``.
        transitions: Row-stochastic transition matrices, one per edge. Either a
            single ``(K, K)`` matrix reused on every edge, or an ``(N-1, K, K)``
            stack. ``transitions[t][i, j] = P(s_{t+1}=j | s_t=i)``.
        evidence: Non-negative per-node evidence potentials, shape ``(N, K)``.
            ``evidence[t]`` is the local likelihood ``P(o_t | s_t)`` for the
            observation seen at node ``t`` (use all-ones for an unobserved node).

    Returns:
        Array of shape ``(N, K)`` whose row ``t`` is the exact posterior marginal
        ``P(s_t | o_{0:N-1})``.

    Raises:
        ValueError: If the shapes are inconsistent, the prior is not a probability
            vector, the transition rows are not normalized, or evidence is negative.
    """

    prior_probs = _as_probability_vector(prior, name="prior")
    evidence_potentials = np.asarray(evidence, dtype=np.float64)
    if evidence_potentials.ndim != 2:
        raise ValueError("evidence must be a 2D (N, K) array of node potentials")
    n_nodes, n_states = evidence_potentials.shape
    if n_nodes < 1:
        raise ValueError("chain must have at least one node")
    if n_states != prior_probs.shape[0]:
        raise ValueError("evidence state dimension must match the prior")
    if np.any(evidence_potentials < 0.0):
        raise ValueError("evidence potentials must be non-negative")

    transition_stack = np.asarray(transitions, dtype=np.float64)
    if transition_stack.ndim == 2:
        transition_stack = np.repeat(
            transition_stack[None, :, :], max(n_nodes - 1, 0), axis=0
        )
    if n_nodes > 1:
        if transition_stack.shape != (n_nodes - 1, n_states, n_states):
            raise ValueError("transitions must be (K, K) or (N-1, K, K)")
        if np.any(transition_stack < 0.0) or not np.allclose(
            transition_stack.sum(axis=2), 1.0, atol=_PROB_TOL, rtol=0.0
        ):
            raise ValueError("each transition row must be a normalized distribution")

    # Forward pass: alpha[t] propto P(s_t, o_{0:t}).
    forward = np.empty((n_nodes, n_states), dtype=np.float64)
    forward[0] = normalize(prior_probs * evidence_potentials[0])
    for t in range(1, n_nodes):
        predicted = forward[t - 1] @ transition_stack[t - 1]
        forward[t] = normalize(predicted * evidence_potentials[t])

    # Backward pass: beta[t] propto P(o_{t+1:N-1} | s_t).
    backward = np.ones((n_nodes, n_states), dtype=np.float64)
    for t in range(n_nodes - 2, -1, -1):
        message = transition_stack[t] @ (backward[t + 1] * evidence_potentials[t + 1])
        backward[t] = message / max(float(np.max(message)), 1e-300)

    marginals = np.empty((n_nodes, n_states), dtype=np.float64)
    for t in range(n_nodes):
        marginals[t] = normalize(forward[t] * backward[t])
    return marginals


def elbo(q: ArrayLike, A: ArrayLike, obs: int, prior: ArrayLike) -> float:
    """Return the evidence lower bound for a discrete observation model.

    Args:
        q: Approximate posterior over states.
        A: Likelihood matrix `P(o | s)` with shape `(n_obs, n_states)`.
        obs: Observed row index into `A`.
        prior: Prior state distribution.

    Returns:
        Evidence lower bound in nats.
    """

    return -variational_free_energy(q, A, obs, prior)


__all__ = [
    "bayes_posterior",
    "belief_propagation_chain",
    "elbo",
    "log_evidence",
    "variational_free_energy",
]
