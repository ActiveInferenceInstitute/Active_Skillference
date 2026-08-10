"""Course-material records for the local read-only learner dashboard."""

from src.curriculum.source_contracts import GITHUB_COMMIT_RE

from .builders import build_course_material_index, write_course_material_artifacts
from .models import (
    COGNITIVE_KB_PATH_PREFIX,
    COGNITIVE_KB_REPO_URL,
    COGNITIVE_KB_SOURCE_ID,
    DIRECT_SKILL_ROUTE_LIMITATION,
    SOURCE_CONFIG_VERSION,
    CourseMaterialAudit,
    CourseMaterialIndex,
    CourseMaterialIssue,
    CourseMaterialRecord,
    normalize_course_material_index,
)
from .validation import (
    audit_course_material_index,
    load_material_sources,
    summarize_course_material_coverage,
    validate_active_skillference_material_contract,
    validate_material_sources,
)

__all__ = [
    "COGNITIVE_KB_PATH_PREFIX",
    "COGNITIVE_KB_REPO_URL",
    "COGNITIVE_KB_SOURCE_ID",
    "DIRECT_SKILL_ROUTE_LIMITATION",
    "GITHUB_COMMIT_RE",
    "SOURCE_CONFIG_VERSION",
    "CourseMaterialAudit",
    "CourseMaterialIndex",
    "CourseMaterialIssue",
    "CourseMaterialRecord",
    "audit_course_material_index",
    "build_course_material_index",
    "load_material_sources",
    "normalize_course_material_index",
    "summarize_course_material_coverage",
    "validate_active_skillference_material_contract",
    "validate_material_sources",
    "write_course_material_artifacts",
]
