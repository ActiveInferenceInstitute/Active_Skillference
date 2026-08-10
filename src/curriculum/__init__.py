"""Curriculum model, prerequisite-DAG engine, and the Active Inference catalog."""

from __future__ import annotations

from .catalog import build_curriculum
from .graph import CurriculumGraph
from .model import (
    ALL_STRATA,
    AssessmentQuestion,
    CurriculumError,
    Skill,
    Stratum,
    Subject,
)
from .quality import (
    CurriculumQualityIssue,
    audit_curriculum_quality,
    validate_curriculum_quality,
)

__all__ = [
    "ALL_STRATA",
    "AssessmentQuestion",
    "CurriculumError",
    "CurriculumGraph",
    "CurriculumQualityIssue",
    "Skill",
    "Stratum",
    "Subject",
    "audit_curriculum_quality",
    "build_curriculum",
    "validate_curriculum_quality",
]
