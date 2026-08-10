from __future__ import annotations

from pathlib import Path
from typing import Any

from src.curriculum.graph import CurriculumGraph
from src.provenance.claims import ClaimRegistry

from .helpers import (
    _assessment_summary,
    _downstream_map,
    _pointers_for_skill,
    _provenance_note,
    _related_skills,
    _render_text,
    _sections_for_skill,
    _skill_ref,
    _source_summaries,
    _subject_by_skill,
    _summarize_course_material_coverage,
    _write_json,
)
from .models import (
    COGNITIVE_KB_SOURCE_ID,
    DIRECT_SKILL_ROUTE_LIMITATION,
    CourseMaterialAudit,
    normalize_course_material_index,
)
from .validation import (
    audit_course_material_index,
    load_material_sources,
    validate_active_skillference_material_contract,
    validate_material_sources,
)


def build_course_material_index(
    graph: CurriculumGraph,
    source_payload: dict[str, Any],
    registry: ClaimRegistry | None = None,
) -> dict[str, object]:
    """Build one modular material record per skill in the curriculum graph."""
    source_index = {
        str(source["source_id"]): source
        for source in source_payload.get("sources", [])
        if isinstance(source, dict) and source.get("source_id")
    }
    subject_by_skill = _subject_by_skill(graph.subjects)
    skill_by_id = {skill.skill_id: skill for skill in graph.skills}
    downstream = _downstream_map(graph)
    levels = graph.levels()
    skills: dict[str, object] = {}

    for skill in graph.topological_order():
        subject = subject_by_skill[skill.skill_id]
        pointers = _pointers_for_skill(skill, source_payload, source_index)
        prerequisites = [
            _skill_ref(skill_by_id[prereq], subject_by_skill[prereq], levels[prereq])
            for prereq in skill.prerequisites
        ]
        dependents = [
            _skill_ref(
                skill_by_id[dependent], subject_by_skill[dependent], levels[dependent]
            )
            for dependent in downstream.get(skill.skill_id, ())
        ]
        quiz_route = (
            f"/subjects/{subject.subject_id}/skills/{skill.skill_id}/quizzes/"
            f"{skill.skill_id}_quiz"
            if skill.assessments
            else ""
        )
        skills[skill.skill_id] = {
            "skillId": skill.skill_id,
            "name": skill.name,
            "subjectId": subject.subject_id,
            "subjectName": subject.name,
            "stratum": skill.stratum.value,
            "depth": levels[skill.skill_id],
            "objective": _render_text(skill.objective, registry),
            "sections": _sections_for_skill(
                skill,
                prerequisites,
                dependents,
                pointers,
                registry,
            ),
            "prerequisites": prerequisites,
            "relatedSkills": _related_skills(
                skill, skill_by_id, subject_by_skill, levels
            ),
            "downstreamSkills": dependents,
            "assessmentSummary": _assessment_summary(skill),
            "provenance": _provenance_note(skill),
            "externalPointers": pointers,
            "officialSkillTree": {
                "subjectRoute": f"/subjects/{subject.subject_id}",
                "quizRoute": quiz_route,
                "unsafeDirectSkillRoute": "",
                "routePolicy": DIRECT_SKILL_ROUTE_LIMITATION,
            },
        }

    payload: dict[str, object] = {
        "version": 1,
        "policy": {
            "learnSurface": "local-read-only-material",
            "officialSkillTreeHandoff": "subject-and-quiz-routes",
            "directSkillRoutePolicy": DIRECT_SKILL_ROUTE_LIMITATION,
            "externalMaterialPolicy": source_payload.get("policy", {}),
        },
        "summary": {},
        "sources": _source_summaries(source_index),
        "skills": skills,
    }
    normalized = normalize_course_material_index(payload)
    pointer_count = sum(
        len(record.external_pointers or ()) for record in normalized.records.values()
    )
    summary: dict[str, object] = {
        "skills": len(normalized.records),
        "externalPointers": pointer_count,
        "sources": len(source_index),
    }
    payload["summary"] = summary
    coverage = _summarize_course_material_coverage(normalized)
    payload["coverage"] = coverage
    source_pointer_counts = coverage.get("sourcePointerCounts", {})
    source_skill_counts = coverage.get("sourceSkillCounts", {})
    if not isinstance(source_pointer_counts, dict):
        source_pointer_counts = {}
    if not isinstance(source_skill_counts, dict):
        source_skill_counts = {}
    summary.update(
        {
            "cognitiveKnowledgeBasePointers": source_pointer_counts.get(
                COGNITIVE_KB_SOURCE_ID, 0
            ),
            "cognitiveKnowledgeBaseSkills": source_skill_counts.get(
                COGNITIVE_KB_SOURCE_ID, 0
            ),
            "topicMatchedSkills": coverage.get("topicMatchedSkills", 0),
            "stratumOnlySkills": coverage.get("stratumOnlySkills", 0),
        }
    )
    return payload


def write_course_material_artifacts(
    graph: CurriculumGraph,
    *,
    source_path: Path,
    output_dir: Path,
    registry: ClaimRegistry | None = None,
) -> tuple[Path, Path, CourseMaterialAudit]:
    """Write the deterministic material index and audit JSON artifacts."""
    source_payload = load_material_sources(source_path)
    source_issues = [
        *validate_material_sources(source_payload),
        *validate_active_skillference_material_contract(source_payload),
    ]
    if source_issues:
        details = "; ".join(
            f"{issue.location}: {issue.message}" for issue in source_issues
        )
        raise ValueError(f"course material source validation failed: {details}")
    index = build_course_material_index(graph, source_payload, registry=registry)
    audit = audit_course_material_index(index, graph)
    if not audit.ok:
        details = "; ".join(
            f"{issue.location}: {issue.message}" for issue in audit.issues
        )
        raise ValueError(f"course material index validation failed: {details}")
    output_dir.mkdir(parents=True, exist_ok=True)
    index_path = output_dir / "course_material_index.json"
    audit_path = output_dir / "course_material_audit.json"
    _write_json(index_path, index)
    _write_json(audit_path, audit.to_dict())
    return index_path, audit_path, audit
