"""The Active Inference / Free Energy Principle curriculum.

``build_curriculum()`` returns the assembled, validated :class:`CurriculumGraph`.
Subject assembly lives in :mod:`src.curriculum.catalog_data.assembly`.
"""

from __future__ import annotations

from .catalog_data.assembly import build_subject_list
from .graph import CurriculumGraph
from .model import CurriculumError
from .quality import validate_curriculum_quality


def build_curriculum() -> CurriculumGraph:
    """Assemble and validate the full Active Inference curriculum DAG.

    Beyond the structural ``validate()`` (acyclic, no dangling/duplicate prerequisites,
    foundational-only roots), this enforces the completeness invariant that every
    applications skill is reachable from a foundational root, so the canopy is never
    disconnected from the foundations.
    """
    graph = CurriculumGraph(subjects=build_subject_list())
    graph.validate()
    if not graph.is_connected_foundations_to_applications():
        raise CurriculumError(
            "curriculum is not connected: an applications skill is unreachable "
            "from any foundational root"
        )
    validate_curriculum_quality(graph)
    return graph
