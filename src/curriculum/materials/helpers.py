from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from src.artifacts.json_io import write_json_artifact
from src.curriculum.graph import CurriculumGraph
from src.curriculum.model import ALL_STRATA, Skill, Subject
from src.provenance.binding import render
from src.provenance.claims import ClaimRegistry

from .models import (
    COGNITIVE_KB_SOURCE_ID,
    CourseMaterialIndex,
    CourseMaterialIssue,
)


def _summarize_course_material_coverage(
    normalized: CourseMaterialIndex,
) -> dict[str, object]:
    source_pointer_counts: Counter[str] = Counter()
    role_pointer_counts: Counter[str] = Counter()
    match_scope_pointer_counts: Counter[str] = Counter()
    source_skill_counts: defaultdict[str, set[str]] = defaultdict(set)
    role_skill_counts: defaultdict[str, set[str]] = defaultdict(set)
    topic_skill_ids: set[str] = set()
    stratum_skill_ids: set[str] = set()
    cognitive_topic_skill_ids: set[str] = set()
    stratum_only_skill_ids: list[str] = []
    unresolved_skill_ids: set[str] = set()

    for skill_id, record in normalized.records.items():
        pointers = record.external_pointers
        if not pointers:
            unresolved_skill_ids.add(skill_id)
            continue
        has_topic = False
        has_stratum = False
        for pointer in pointers:
            if not isinstance(pointer, dict):
                unresolved_skill_ids.add(skill_id)
                continue
            source_id = str(pointer.get("sourceId", "")).strip()
            role = str(pointer.get("role", "")).strip()
            scopes = pointer.get("matchScopes")
            if not isinstance(scopes, list) or not scopes:
                scopes = ["unspecified"]
            if not source_id or source_id not in normalized.source_ids:
                unresolved_skill_ids.add(skill_id)
            if source_id:
                source_pointer_counts[source_id] += 1
                source_skill_counts[source_id].add(skill_id)
            if role:
                role_pointer_counts[role] += 1
                role_skill_counts[role].add(skill_id)
            for scope in scopes:
                scope_text = str(scope).strip() or "unspecified"
                match_scope_pointer_counts[scope_text] += 1
                has_topic = has_topic or scope_text == "topic"
                has_stratum = has_stratum or scope_text == "stratum"
            if source_id == COGNITIVE_KB_SOURCE_ID and "topic" in scopes:
                cognitive_topic_skill_ids.add(skill_id)
        if has_topic:
            topic_skill_ids.add(skill_id)
        if has_stratum:
            stratum_skill_ids.add(skill_id)
        if has_stratum and not has_topic:
            stratum_only_skill_ids.append(skill_id)

    return {
        "skills": len(normalized.records),
        "sourcePointerCounts": dict(sorted(source_pointer_counts.items())),
        "sourceSkillCounts": {
            key: len(value) for key, value in sorted(source_skill_counts.items())
        },
        "rolePointerCounts": dict(sorted(role_pointer_counts.items())),
        "roleSkillCounts": {
            key: len(value) for key, value in sorted(role_skill_counts.items())
        },
        "matchScopePointerCounts": dict(sorted(match_scope_pointer_counts.items())),
        "topicMatchedSkills": len(topic_skill_ids),
        "stratumFallbackSkills": len(stratum_skill_ids),
        "stratumOnlySkills": len(stratum_only_skill_ids),
        "stratumOnlySkillIds": sorted(stratum_only_skill_ids),
        "cognitiveKnowledgeBaseTopicSkills": len(cognitive_topic_skill_ids),
        "unresolvedPointerSkills": len(unresolved_skill_ids),
        "unresolvedPointerSkillIds": sorted(unresolved_skill_ids),
    }


def _validate_pointer_sections(
    payload: dict[str, Any],
    source_index: dict[str, dict[str, Any]],
) -> list[CourseMaterialIssue]:
    issues: list[CourseMaterialIssue] = []
    stratum_mappings = payload.get("stratum_mappings")
    if not isinstance(stratum_mappings, dict):
        return [
            CourseMaterialIssue(
                "stratum-mappings",
                "stratum_mappings",
                "stratum_mappings must be a mapping",
            )
        ]
    for stratum in ALL_STRATA:
        pointers = stratum_mappings.get(stratum.value)
        if not isinstance(pointers, list) or not pointers:
            issues.append(
                CourseMaterialIssue(
                    "missing-stratum",
                    f"stratum_mappings.{stratum.value}",
                    "each curriculum stratum needs at least one pointer",
                )
            )
            continue
        issues.extend(
            _validate_pointer_list(
                pointers,
                source_index,
                f"stratum_mappings.{stratum.value}",
            )
        )

    topic_mappings = payload.get("topic_mappings", [])
    if not isinstance(topic_mappings, list):
        issues.append(
            CourseMaterialIssue(
                "topic-mappings",
                "topic_mappings",
                "topic_mappings must be a list when present",
            )
        )
        return issues
    for idx, topic in enumerate(topic_mappings):
        location = f"topic_mappings[{idx}]"
        if not isinstance(topic, dict):
            issues.append(
                CourseMaterialIssue(
                    "topic-type", location, "topic row must be a mapping"
                )
            )
            continue
        matches = topic.get("match")
        pointers = topic.get("pointers")
        if not isinstance(matches, list) or not all(
            isinstance(item, str) and item.strip() for item in matches
        ):
            issues.append(
                CourseMaterialIssue(
                    "topic-match",
                    f"{location}.match",
                    "match must be a list of non-empty strings",
                )
            )
        if not isinstance(pointers, list) or not pointers:
            issues.append(
                CourseMaterialIssue(
                    "topic-pointers",
                    f"{location}.pointers",
                    "topic pointers must be a non-empty list",
                )
            )
            continue
        issues.extend(_validate_pointer_list(pointers, source_index, location))
    return issues


def _validate_pointer_list(
    pointers: list[Any],
    source_index: dict[str, dict[str, Any]],
    location: str,
) -> list[CourseMaterialIssue]:
    issues: list[CourseMaterialIssue] = []
    for pointer_idx, pointer in enumerate(pointers):
        pointer_location = f"{location}[{pointer_idx}]"
        if not isinstance(pointer, dict):
            issues.append(
                CourseMaterialIssue(
                    "pointer-type",
                    pointer_location,
                    "pointer must be a mapping",
                )
            )
            continue
        source_id = _required_string(pointer, "source_id")
        for field in ("title", "path", "role"):
            if not _required_string(pointer, field):
                issues.append(
                    CourseMaterialIssue(
                        f"pointer-{field}",
                        f"{pointer_location}.{field}",
                        f"{field} is required",
                    )
                )
        if source_id not in source_index:
            issues.append(
                CourseMaterialIssue(
                    "pointer-source",
                    f"{pointer_location}.source_id",
                    f"unknown source_id {source_id!r}",
                )
            )
    return issues


def _pointers_for_skill(
    skill: Skill,
    payload: dict[str, Any],
    source_index: dict[str, dict[str, Any]],
) -> list[dict[str, object]]:
    raw_pointers: list[tuple[dict[str, Any], str, tuple[str, ...]]] = []
    stratum_mappings = payload.get("stratum_mappings", {})
    if isinstance(stratum_mappings, dict):
        raw_pointers.extend(
            (pointer, "stratum", ())
            for pointer in _as_pointer_list(stratum_mappings.get(skill.stratum.value))
        )
    skill_text = (
        f"{skill.skill_id} {skill.name} {skill.objective} {skill.description} "
        f"{' '.join(skill.tags)}"
    ).lower()
    topic_mappings = payload.get("topic_mappings", [])
    if isinstance(topic_mappings, list):
        for topic in topic_mappings:
            if not isinstance(topic, dict):
                continue
            matches = [
                str(match).lower()
                for match in topic.get("match", [])
                if isinstance(match, str)
            ]
            matched_terms = tuple(match for match in matches if match in skill_text)
            if matched_terms:
                raw_pointers.extend(
                    (pointer, "topic", matched_terms)
                    for pointer in _as_pointer_list(topic.get("pointers"))
                )

    merged: dict[tuple[str, str, str], dict[str, object]] = {}
    scope_sets: defaultdict[tuple[str, str, str], set[str]] = defaultdict(set)
    term_sets: defaultdict[tuple[str, str, str], set[str]] = defaultdict(set)
    for pointer, match_scope, matched_terms in raw_pointers:
        source_id = _required_string(pointer, "source_id")
        path = _required_string(pointer, "path")
        role = _required_string(pointer, "role")
        key = (source_id, path, role)
        source = source_index.get(source_id)
        if source is None:
            continue
        if key not in merged:
            commit = _required_string(source, "commit")
            repo_url = _required_string(source, "repo_url").rstrip("/")
            merged[key] = {
                "sourceId": source_id,
                "sourceTitle": _required_string(source, "title"),
                "title": _required_string(pointer, "title"),
                "role": role,
                "path": path,
                "commit": commit,
                "url": f"{repo_url}/blob/{commit}/{path}",
                "licenseStatus": _required_string(source, "license_status"),
            }
        scope_sets[key].add(match_scope)
        term_sets[key].update(matched_terms)
    pointers: list[dict[str, object]] = []
    for key, pointer in merged.items():
        pointer["matchScopes"] = sorted(scope_sets[key])
        pointer["matchTerms"] = sorted(term_sets[key])
        pointers.append(pointer)
    return pointers


def _sections_for_skill(
    skill: Skill,
    prerequisites: list[dict[str, object]],
    dependents: list[dict[str, object]],
    pointers: list[dict[str, object]],
    registry: ClaimRegistry | None,
) -> list[dict[str, str]]:
    prereq_body = (
        "This root skill can be entered without a prior local prerequisite."
        if not prerequisites
        else "Start from "
        + ", ".join(f"{item['name']} ({item['skillId']})" for item in prerequisites[:6])
        + "."
    )
    downstream_body = (
        "This skill currently functions as a terminal review or application point."
        if not dependents
        else "It prepares learners for "
        + ", ".join(f"{item['name']} ({item['skillId']})" for item in dependents[:6])
        + "."
    )
    pointer_body = (
        f"External material is linked through {len(pointers)} pinned pointer"
        f"{'' if len(pointers) == 1 else 's'}; upstream prose remains in the source repositories."
    )
    return [
        {
            "heading": "Concept",
            "body": _render_text(skill.description, registry),
        },
        {
            "heading": "Objective",
            "body": _render_text(skill.objective, registry),
        },
        {
            "heading": "Prerequisite Context",
            "body": prereq_body,
        },
        {
            "heading": "Downstream Role",
            "body": downstream_body,
        },
        {
            "heading": "Assessment Contract",
            "body": str(_assessment_summary(skill)["summary"]),
        },
        {
            "heading": "Provenance Note",
            "body": str(_provenance_note(skill)["summary"]),
        },
        {
            "heading": "External Pointers",
            "body": pointer_body,
        },
    ]


def _assessment_summary(skill: Skill) -> dict[str, object]:
    types = sorted({question.question_type for question in skill.assessments})
    return {
        "questionCount": len(skill.assessments),
        "questionTypes": types,
        "summary": (
            f"{len(skill.assessments)} assessment item"
            f"{'' if len(skill.assessments) == 1 else 's'} gate completion; "
            "answers remain in the generated SkillTree quiz artifact."
        ),
    }


def _provenance_note(skill: Skill) -> dict[str, object]:
    tokens = sorted(skill.claim_tokens())
    if tokens:
        summary = (
            "Quantitative learner-facing values are claim-token backed by tested "
            f"kernels: {', '.join(tokens)}."
        )
    else:
        summary = (
            "This lesson record contains no kernel claim token; any quantitative "
            "examples must still enter through the provenance registry before export."
        )
    return {
        "claimTokens": tokens,
        "summary": summary,
        "hasClaimTokens": bool(tokens),
    }


def _related_skills(
    skill: Skill,
    skill_by_id: dict[str, Skill],
    subject_by_skill: dict[str, Subject],
    levels: dict[str, int],
) -> list[dict[str, object]]:
    related_ids = list(skill.related)
    for prereq in skill.prerequisites:
        if prereq not in related_ids:
            related_ids.append(prereq)
    rows: list[dict[str, object]] = []
    for related_id in related_ids[:8]:
        related_skill = skill_by_id.get(related_id)
        if related_skill is None:
            continue
        rows.append(
            _skill_ref(
                related_skill,
                subject_by_skill[related_skill.skill_id],
                levels[related_skill.skill_id],
            )
        )
    return rows


def _skill_ref(skill: Skill, subject: Subject, depth: int) -> dict[str, object]:
    return {
        "skillId": skill.skill_id,
        "name": skill.name,
        "subjectId": subject.subject_id,
        "subjectName": subject.name,
        "stratum": skill.stratum.value,
        "depth": depth,
    }


def _subject_by_skill(subjects: list[Subject]) -> dict[str, Subject]:
    return {skill.skill_id: subject for subject in subjects for skill in subject.skills}


def _downstream_map(graph: CurriculumGraph) -> dict[str, tuple[str, ...]]:
    rows: dict[str, list[str]] = {skill.skill_id: [] for skill in graph.skills}
    for prereq, dependent in graph.prerequisite_edges():
        rows.setdefault(prereq, []).append(dependent)
    return {
        skill_id: tuple(sorted(dependents)) for skill_id, dependents in rows.items()
    }


def _source_summaries(source_index: dict[str, dict[str, Any]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for source_id in sorted(source_index):
        source = source_index[source_id]
        rows.append(
            {
                "sourceId": source_id,
                "title": _required_string(source, "title"),
                "repoUrl": _required_string(source, "repo_url"),
                "commit": _required_string(source, "commit"),
                "licenseStatus": _required_string(source, "license_status"),
                "statusNote": _required_string(source, "status_note"),
            }
        )
    return rows


def _audit_handoff(
    skill_id: str,
    official: dict[str, Any],
    issues: list[CourseMaterialIssue],
) -> None:
    subject_route = str(official.get("subjectRoute", ""))
    quiz_route = str(official.get("quizRoute", ""))
    unsafe_route = str(official.get("unsafeDirectSkillRoute", ""))
    if "/skills/" in subject_route:
        issues.append(
            CourseMaterialIssue(
                "subject-route",
                f"skills.{skill_id}.officialSkillTree.subjectRoute",
                "subject route must not include a direct skill-detail path",
            )
        )
    if unsafe_route:
        issues.append(
            CourseMaterialIssue(
                "unsafe-route",
                f"skills.{skill_id}.officialSkillTree.unsafeDirectSkillRoute",
                "unsafe direct skill-detail routes must not be emitted",
            )
        )
    if quiz_route and ("/skills/" not in quiz_route or "/quizzes/" not in quiz_route):
        issues.append(
            CourseMaterialIssue(
                "quiz-route",
                f"skills.{skill_id}.officialSkillTree.quizRoute",
                "quiz route must use the official SkillTree quiz path",
            )
        )


def _iter_configured_pointers(
    payload: dict[str, Any],
) -> list[tuple[str, dict[str, Any]]]:
    pointers: list[tuple[str, dict[str, Any]]] = []
    stratum_mappings = payload.get("stratum_mappings", {})
    if isinstance(stratum_mappings, dict):
        for stratum, rows in stratum_mappings.items():
            for idx, pointer in enumerate(_as_pointer_list(rows)):
                pointers.append((f"stratum_mappings.{stratum}[{idx}]", pointer))
    topic_mappings = payload.get("topic_mappings", [])
    if isinstance(topic_mappings, list):
        for topic_idx, topic in enumerate(topic_mappings):
            if not isinstance(topic, dict):
                continue
            for pointer_idx, pointer in enumerate(
                _as_pointer_list(topic.get("pointers"))
            ):
                pointers.append(
                    (
                        f"topic_mappings[{topic_idx}].pointers[{pointer_idx}]",
                        pointer,
                    )
                )
    return pointers


def _as_pointer_list(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _required_string(mapping: dict[str, Any], key: str) -> str:
    value = mapping.get(key)
    return value.strip() if isinstance(value, str) else ""


def _write_json(path: Path, payload: object) -> None:
    write_json_artifact(path, payload)


def _render_text(text: str, registry: ClaimRegistry | None) -> str:
    return render(text, registry) if registry is not None else text
