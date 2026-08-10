from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.validation.finding import Finding

DIRECT_SKILL_ROUTE_LIMITATION = (
    "Direct SkillTree skill-detail routes are intentionally not used for Learn "
    "actions; local validation found that subject and quiz handoff routes are the "
    "stable official SkillTree surfaces for this dashboard."
)
SOURCE_CONFIG_VERSION = 1
COGNITIVE_KB_SOURCE_ID = "aii_cognitive_kb"
COGNITIVE_KB_REPO_URL = "https://github.com/ActiveInferenceInstitute/cognitive"
COGNITIVE_KB_PATH_PREFIX = "knowledge_base/"


@dataclass(frozen=True)
class CourseMaterialIssue(Finding):
    """A validation finding for material sources or generated records."""

    def to_dict(self) -> dict[str, str]:
        return {
            "code": self.code,
            "location": self.location,
            "message": self.message,
        }


@dataclass(frozen=True)
class CourseMaterialAudit:
    """Summary and issues for the generated material index."""

    summary: dict[str, object]
    issues: tuple[CourseMaterialIssue, ...]

    @property
    def ok(self) -> bool:
        return not self.issues

    def to_dict(self) -> dict[str, object]:
        return {
            "summary": self.summary,
            "issues": [issue.to_dict() for issue in self.issues],
        }


@dataclass(frozen=True)
class CourseMaterialRecord:
    skill_id: str
    payload: dict[str, Any] | None

    @property
    def sections(self) -> list[Any] | None:
        if self.payload is None:
            return None
        value = self.payload.get("sections")
        return value if isinstance(value, list) else None

    @property
    def external_pointers(self) -> list[Any] | None:
        if self.payload is None:
            return None
        value = self.payload.get("externalPointers")
        return value if isinstance(value, list) else None

    @property
    def official_skilltree(self) -> dict[str, Any] | None:
        if self.payload is None:
            return None
        value = self.payload.get("officialSkillTree")
        return value if isinstance(value, dict) else None


@dataclass(frozen=True)
class CourseMaterialIndex:
    records: dict[str, CourseMaterialRecord]
    source_ids: frozenset[str]
    skills_is_mapping: bool


def normalize_course_material_index(index: dict[str, object]) -> CourseMaterialIndex:
    skills = index.get("skills")
    records: dict[str, CourseMaterialRecord] = {}
    if isinstance(skills, dict):
        records = {
            str(skill_id): CourseMaterialRecord(
                skill_id=str(skill_id),
                payload=record if isinstance(record, dict) else None,
            )
            for skill_id, record in skills.items()
        }
    sources = index.get("sources")
    source_rows = sources if isinstance(sources, list) else []
    source_ids = frozenset(
        str(source.get("sourceId"))
        for source in source_rows
        if isinstance(source, dict) and source.get("sourceId")
    )
    return CourseMaterialIndex(
        records=records,
        source_ids=source_ids,
        skills_is_mapping=isinstance(skills, dict),
    )
