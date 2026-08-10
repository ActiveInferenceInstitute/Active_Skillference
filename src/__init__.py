"""Active Skillference — a high-integrity micro-learning platform for Active Inference.

The package is layered:

* :mod:`src.kernels` — tested computational kernels (information theory, distributions,
  Bayesian/variational inference, active inference) that produce every quantitative claim.
* :mod:`src.provenance` — the claim registry and the content-provenance binding gate.
* :mod:`src.curriculum` — the typed skill model, the prerequisite-DAG engine, and the catalog.
* :mod:`src.skilltree` — conversion of the curriculum into the NSA SkillTree data model + a
  REST client/seeder for a live instance.

Nothing here re-implements an algorithm: scripts orchestrate, these modules compute.
"""

from __future__ import annotations

__all__ = ["__version__"]

__version__ = "1.0.0"
