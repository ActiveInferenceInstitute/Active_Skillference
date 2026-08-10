from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

from src.curriculum.graph import CurriculumGraph
from src.curriculum.model import ALL_STRATA
from src.curriculum.source_contracts import GITHUB_COMMIT_RE

from .github_sources import _github_repo_parts, _validate_online_trees
from .helpers import (
    _as_pointer_list,
    _audit_handoff,
    _required_string,
    _summarize_course_material_coverage,
    _validate_pointer_sections,
)
from .models import (
    COGNITIVE_KB_PATH_PREFIX,
    COGNITIVE_KB_REPO_URL,
    COGNITIVE_KB_SOURCE_ID,
    SOURCE_CONFIG_VERSION,
    CourseMaterialAudit,
    CourseMaterialIssue,
    normalize_course_material_index,
)


def load_material_sources(path: Path) -> dict[str, Any]:
    """Load the static material-source YAML contract."""
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"{path} must contain a YAML mapping")
    return payload


def validate_material_sources(
    payload: dict[str, Any],
    *,
    online: bool = False,
    timeout: float = 10.0,
) -> list[CourseMaterialIssue]:
    """Validate static source metadata and optionally verify pinned GitHub trees."""
    issues: list[CourseMaterialIssue] = []
    if payload.get("version") != SOURCE_CONFIG_VERSION:
        issues.append(
            CourseMaterialIssue(
                "version",
                "version",
                f"expected version {SOURCE_CONFIG_VERSION}",
            )
        )

    sources = payload.get("sources")
    if not isinstance(sources, list) or not sources:
        issues.append(
            CourseMaterialIssue("sources", "sources", "sources must be a list")
        )
        return issues

    source_index: dict[str, dict[str, Any]] = {}
    for source_idx, raw_source in enumerate(sources):
        location = f"sources[{source_idx}]"
        if not isinstance(raw_source, dict):
            issues.append(
                CourseMaterialIssue("source-type", location, "source must be a mapping")
            )
            continue
        source_id = _required_string(raw_source, "source_id")
        repo_url = _required_string(raw_source, "repo_url")
        commit = _required_string(raw_source, "commit")
        path_globs = raw_source.get("path_globs")
        if not source_id:
            issues.append(
                CourseMaterialIssue("source-id", location, "source_id is required")
            )
        elif source_id in source_index:
            issues.append(
                CourseMaterialIssue(
                    "duplicate-source",
                    location,
                    f"duplicate source_id {source_id!r}",
                )
            )
        else:
            source_index[source_id] = raw_source
        if not _github_repo_parts(repo_url):
            issues.append(
                CourseMaterialIssue(
                    "repo-url",
                    f"{location}.repo_url",
                    "repo_url must be a GitHub repository URL",
                )
            )
        if not GITHUB_COMMIT_RE.match(commit):
            issues.append(
                CourseMaterialIssue(
                    "commit",
                    f"{location}.commit",
                    "commit must be a 40-character lowercase SHA",
                )
            )
        if not isinstance(path_globs, list) or not path_globs:
            issues.append(
                CourseMaterialIssue(
                    "path-globs",
                    f"{location}.path_globs",
                    "path_globs must be a non-empty list",
                )
            )
        elif any(not isinstance(pattern, str) or not pattern for pattern in path_globs):
            issues.append(
                CourseMaterialIssue(
                    "path-globs",
                    f"{location}.path_globs",
                    "every path_glob must be a non-empty string",
                )
            )

    issues.extend(_validate_pointer_sections(payload, source_index))
    if online and source_index:
        issues.extend(_validate_online_trees(source_index, payload, timeout=timeout))
    return issues


def validate_active_skillference_material_contract(
    payload: dict[str, Any],
) -> list[CourseMaterialIssue]:
    """Validate the project-specific AII course/knowledge-base pointer contract."""
    issues: list[CourseMaterialIssue] = []
    sources = payload.get("sources")
    source_index = (
        {
            str(source.get("source_id")): source
            for source in sources
            if isinstance(source, dict) and source.get("source_id")
        }
        if isinstance(sources, list)
        else {}
    )
    kb_source = source_index.get(COGNITIVE_KB_SOURCE_ID)
    if not isinstance(kb_source, dict):
        issues.append(
            CourseMaterialIssue(
                "required-kb-source",
                "sources.aii_cognitive_kb",
                "Active Inference Institute cognitive knowledge-base source is required",
            )
        )
    else:
        if _required_string(kb_source, "repo_url").rstrip("/") != COGNITIVE_KB_REPO_URL:
            issues.append(
                CourseMaterialIssue(
                    "required-kb-repo",
                    "sources.aii_cognitive_kb.repo_url",
                    "cognitive knowledge-base source must point to the AII cognitive repo",
                )
            )
        globs = kb_source.get("path_globs")
        if not isinstance(globs, list) or "knowledge_base/**/*.md" not in globs:
            issues.append(
                CourseMaterialIssue(
                    "required-kb-glob",
                    "sources.aii_cognitive_kb.path_globs",
                    "cognitive knowledge-base source must expose knowledge_base/**/*.md",
                )
            )

    stratum_mappings = payload.get("stratum_mappings")
    if isinstance(stratum_mappings, dict):
        for stratum in ALL_STRATA:
            pointers = _as_pointer_list(stratum_mappings.get(stratum.value))
            if not any(
                _required_string(pointer, "source_id") == COGNITIVE_KB_SOURCE_ID
                and _required_string(pointer, "path").startswith(
                    COGNITIVE_KB_PATH_PREFIX
                )
                for pointer in pointers
            ):
                issues.append(
                    CourseMaterialIssue(
                        "required-kb-stratum-pointer",
                        f"stratum_mappings.{stratum.value}",
                        "each stratum needs a cognitive knowledge-base pointer",
                    )
                )

    topic_mappings = payload.get("topic_mappings")
    kb_topic_pointers = 0
    if isinstance(topic_mappings, list):
        for topic_idx, topic in enumerate(topic_mappings):
            if not isinstance(topic, dict):
                continue
            for pointer in _as_pointer_list(topic.get("pointers")):
                if _required_string(
                    pointer, "source_id"
                ) == COGNITIVE_KB_SOURCE_ID and _required_string(
                    pointer, "path"
                ).startswith(COGNITIVE_KB_PATH_PREFIX):
                    kb_topic_pointers += 1
    if kb_topic_pointers == 0:
        issues.append(
            CourseMaterialIssue(
                "required-kb-topic-pointer",
                "topic_mappings",
                "at least one topic mapping must point into the cognitive knowledge base",
            )
        )
    return issues


def audit_course_material_index(
    index: dict[str, object],
    graph: CurriculumGraph,
) -> CourseMaterialAudit:
    """Check that every skill has non-empty material and external pointers."""
    issues: list[CourseMaterialIssue] = []
    normalized = normalize_course_material_index(index)
    if not normalized.skills_is_mapping:
        issues.append(
            CourseMaterialIssue("skills", "skills", "skills must be a mapping")
        )
    graph_skill_ids = {skill.skill_id for skill in graph.skills}
    material_skill_ids = set(normalized.records)
    missing = sorted(graph_skill_ids - material_skill_ids)
    extra = sorted(material_skill_ids - graph_skill_ids)
    for skill_id in missing:
        issues.append(
            CourseMaterialIssue(
                "missing-record",
                f"skills.{skill_id}",
                "skill is missing a course-material record",
            )
        )
    for skill_id in extra:
        issues.append(
            CourseMaterialIssue(
                "extra-record",
                f"skills.{skill_id}",
                "course-material record does not match a graph skill",
            )
        )

    pointer_count = 0
    section_count = 0
    for skill_id in sorted(graph_skill_ids & material_skill_ids):
        record = normalized.records[skill_id]
        if record.payload is None:
            issues.append(
                CourseMaterialIssue(
                    "record-type",
                    f"skills.{skill_id}",
                    "course-material record must be a mapping",
                )
            )
            continue
        sections = record.sections
        pointers = record.external_pointers
        official = record.official_skilltree
        if not sections:
            issues.append(
                CourseMaterialIssue(
                    "empty-sections",
                    f"skills.{skill_id}.sections",
                    "record must include non-empty modular sections",
                )
            )
        else:
            section_count += len(sections)
            for section_idx, section in enumerate(sections):
                if (
                    not isinstance(section, dict)
                    or not str(section.get("body", "")).strip()
                ):
                    issues.append(
                        CourseMaterialIssue(
                            "empty-section-body",
                            f"skills.{skill_id}.sections[{section_idx}]",
                            "section body must be non-empty",
                        )
                    )
                    continue
                if "{{claim:" in str(section.get("body", "")):
                    issues.append(
                        CourseMaterialIssue(
                            "unresolved-claim-token",
                            f"skills.{skill_id}.sections[{section_idx}]",
                            "section body contains an unresolved claim token",
                        )
                    )
        if not isinstance(pointers, list) or not pointers:
            issues.append(
                CourseMaterialIssue(
                    "missing-pointer",
                    f"skills.{skill_id}.externalPointers",
                    "record must include at least one external pointer",
                )
            )
        else:
            pointer_count += len(pointers)
        if official is None:
            issues.append(
                CourseMaterialIssue(
                    "handoff",
                    f"skills.{skill_id}.officialSkillTree",
                    "officialSkillTree handoff metadata is required",
                )
            )
        else:
            _audit_handoff(skill_id, official, issues)

    coverage = index.get("coverage")
    if not isinstance(coverage, dict):
        coverage = _summarize_course_material_coverage(normalized)
    source_pointer_counts = coverage.get("sourcePointerCounts", {})
    source_skill_counts = coverage.get("sourceSkillCounts", {})
    if not isinstance(source_pointer_counts, dict):
        source_pointer_counts = {}
    if not isinstance(source_skill_counts, dict):
        source_skill_counts = {}
    summary: dict[str, object] = {
        "skills": len(graph_skill_ids),
        "materialRecords": len(material_skill_ids),
        "externalPointers": pointer_count,
        "sections": section_count,
        "ok": not issues,
        "cognitiveKnowledgeBasePointers": source_pointer_counts.get(
            COGNITIVE_KB_SOURCE_ID, 0
        ),
        "cognitiveKnowledgeBaseSkills": source_skill_counts.get(
            COGNITIVE_KB_SOURCE_ID, 0
        ),
        "cognitiveKnowledgeBaseTopicSkills": coverage.get(
            "cognitiveKnowledgeBaseTopicSkills", 0
        ),
        "topicMatchedSkills": coverage.get("topicMatchedSkills", 0),
        "stratumOnlySkills": coverage.get("stratumOnlySkills", 0),
        "unresolvedPointerSkills": coverage.get("unresolvedPointerSkills", 0),
    }
    return CourseMaterialAudit(summary=summary, issues=tuple(issues))


def summarize_course_material_coverage(index: dict[str, object]) -> dict[str, object]:
    """Return coverage counters for a generated course-material index."""
    normalized = normalize_course_material_index(index)
    return _summarize_course_material_coverage(normalized)
