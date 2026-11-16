"""Active inference planning helpers for discrete-state models."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from typing import TypeAlias

import numpy as np
from numpy.typing import ArrayLike, NDArray

from .distributions import log_stable, normalize, softmax
from .inference import _as_probability_vector, _validate_model, bayes_posterior
from .information import kl_divergence

FloatArray: TypeAlias = NDArray[np.float64]


def expected_free_energy(
    qs: ArrayLike,
    A: ArrayLike,
    C: ArrayLike,
) -> tuple[float, float, float]:
    """Return expected free energy and its epistemic/pragmatic components.

    Sign convention: the agent minimizes `G = -(epistemic + pragmatic)`.
    Under this convention, higher epistemic value and higher pragmatic value
    both make `G` smaller and therefore more attractive.

    Args:
        qs: Predicted state distribution.
        A: Likelihood matrix `P(o | s)` with shape `(n_obs, n_states)`.
        C: Observation preferences, normalized defensively to probabilities.

    Returns:
        Tuple `(G, epistemic, pragmatic)` in nats.
    """

    state_probs = _as_probability_vector(qs, name="qs")
    likelihood = np.asarray(A, dtype=np.float64)
    _validate_model(state_probs, likelihood, 0)
    preferences = normalize(C)
    if preferences.shape != (likelihood.shape[0],):
        raise ValueError("C length must match the number of observations")

    qo = likelihood @ state_probs
    pragmatic = float(np.dot(qo, log_stable(preferences)))

    epistemic = 0.0
    for state_index, state_mass in enumerate(state_probs):
        if state_mass <= 0.0:
            continue
        epistemic += float(state_mass) * kl_divergence(likelihood[:, state_index], qo)

    G = -(epistemic + pragmatic)
    return float(G), float(epistemic), float(pragmatic)


def policy_posterior(G: ArrayLike, gamma: float = 1.0) -> FloatArray:
    """Return a posterior over policies favoring lower expected free energy.

    Args:
        G: Expected free energies for each policy.
        gamma: Positive precision over policy values.

    Returns:
        Posterior policy distribution `softmax(-gamma * G)`.
    """

    return softmax(-np.asarray(G, dtype=np.float64), precision=gamma)


@dataclass
class DiscreteActiveInferenceAgent:
    """One-step discrete active inference agent."""

    A: FloatArray
    B: FloatArray
    C: FloatArray
    D: FloatArray

    def __post_init__(self) -> None:
        """Coerce and validate the existing probability-weight model contract."""

        self.A = np.asarray(self.A, dtype=np.float64)
        self.B = np.asarray(self.B, dtype=np.float64)
        self.C = np.asarray(self.C, dtype=np.float64)
        self.D = _as_probability_vector(self.D, name="D")
        _validate_model(self.D, self.A, 0)
        n_states = self.D.size
        if (
            self.B.ndim != 3
            or self.B.shape[:2] != (n_states, n_states)
            or self.B.shape[2] == 0
            or not np.all(np.isfinite(self.B))
            or np.any(self.B < 0.0)
            or not np.allclose(self.B.sum(axis=0), 1.0, atol=1e-9, rtol=0.0)
        ):
            raise ValueError("B must contain finite non-negative column-stochastic state transitions")
        if normalize(self.C).shape != (self.A.shape[0],):
            raise ValueError("C length must match the number of observations")

    def infer_states(self, obs: int) -> FloatArray:
        """Infer the posterior state distribution for an observation."""

        return bayes_posterior(self.D, self.A, obs)

    def predict(self, qs: ArrayLike, action: int) -> FloatArray:
        """Predict the next-state distribution under an action."""

        state_probs = _as_probability_vector(qs, name="qs")
        if state_probs.shape != self.D.shape:
            raise ValueError("qs length must match the model state dimension")
        if not isinstance(action, (int, np.integer)) or isinstance(action, (bool, np.bool_)):
            raise ValueError("action must be an integer index")
        if action < 0 or action >= self.B.shape[2]:
            raise ValueError("action index out of range")
        return self.B[:, :, action] @ state_probs

    def evaluate_policies(self, qs: ArrayLike) -> FloatArray:
        """Evaluate one-step policies from a current state posterior.

        Each policy is scored using the predicted post-transition state
        distribution, so informative transitions can lower expected free energy.
        """

        state_probs = np.asarray(qs, dtype=np.float64)
        n_actions = self.B.shape[2]
        values = np.empty(n_actions, dtype=np.float64)
        for action in range(n_actions):
            predicted = self.predict(state_probs, action)
            values[action] = expected_free_energy(predicted, self.A, self.C)[0]
        return values

    def enumerate_policies(self, horizon: int) -> list[tuple[int, ...]]:
        """Return every length-``horizon`` action sequence over the action set.

        A *policy* in active inference is a candidate sequence of future actions,
        not a single action. With ``n_actions`` actions and a planning horizon
        ``H`` there are ``n_actions ** H`` policies.
        """

        if horizon < 1:
            raise ValueError("horizon must be at least 1")
        n_actions = self.B.shape[2]
        return [tuple(policy) for policy in product(range(n_actions), repeat=horizon)]

    def evaluate_multistep_policies(
        self, qs: ArrayLike, horizon: int, gamma: float = 1.0
    ) -> dict[str, object]:
        """Score multi-step policies by their cumulative expected free energy.

        Each policy :math:`\\pi = (a_1, \\dots, a_H)` is rolled forward from the
        current state posterior, accumulating the expected free energy of every
        predicted future state: :math:`G_\\pi = \\sum_{t=1}^{H} G(s_t)`. The
        posterior over policies is :math:`\\sigma(-\\gamma G_\\pi)`. This is the
        temporal generalization of :meth:`evaluate_policies`: at ``horizon == 1``
        the per-policy values reduce *exactly* to the one-step result (a
        consistency invariant asserted in the tests).

        Args:
            qs: Current state posterior, shape ``(K,)``.
            horizon: Number of future steps planned over (``H >= 1``).
            gamma: Positive precision over policy expected free energy.

        Returns:
            Mapping with ``policies`` (list of action tuples), ``G`` (cumulative
            expected free energy per policy), ``posterior`` (policy posterior),
            ``best_index`` (argmin G), and ``best_policy``.
        """

        state_probs = np.asarray(qs, dtype=np.float64)
        policies = self.enumerate_policies(horizon)
        values = np.empty(len(policies), dtype=np.float64)
        for index, policy in enumerate(policies):
            predicted = state_probs
            cumulative = 0.0
            for action in policy:
                predicted = self.predict(predicted, action)
                cumulative += expected_free_energy(predicted, self.A, self.C)[0]
            values[index] = cumulative
        posterior = policy_posterior(values, gamma=gamma)
        best_index = int(np.argmin(values))
        return {
            "policies": policies,
            "G": values,
            "posterior": posterior,
            "best_index": best_index,
            "best_policy": policies[best_index],
        }

    def act(
        self, obs: int, gamma: float = 1.0, rng: np.random.Generator | None = None
    ) -> int:
        """Sample an action from the posterior over one-step policies.

        Args:
            obs: Current observation index.
            gamma: Precision over policy expected free energy.
            rng: Optional NumPy random generator for deterministic sampling.

        Returns:
            Sampled action index.
        """

        generator = rng if rng is not None else np.random.default_rng()
        qs = self.infer_states(obs)
        G = self.evaluate_policies(qs)
        posterior = policy_posterior(G, gamma=gamma)
        return int(generator.choice(len(posterior), p=posterior))


__all__ = [
    "DiscreteActiveInferenceAgent",
    "expected_free_energy",
    "policy_posterior",
]
