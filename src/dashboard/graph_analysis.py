"""Graph diagnostics over the exported SkillTree project JSON."""

from __future__ import annotations

from collections import Counter, defaultdict, deque
from collections.abc import Mapping
from typing import Any


def analyze_project_graph(project: dict[str, Any]) -> dict[str, Any]:
    """Return dependency diagnostics from ``load_skilltree_project`` output."""
    if not project.get("available"):
        return {
            "available": False,
            "bottlenecks": [],
            "isolatedRisks": [],
            "longestPaths": [],
            "neighborhoods": {},
            "subjectLayout": [],
            "subjectFlows": [],
            "summary": {
                "skills": 0,
                "dependencies": 0,
                "subjectLanes": 0,
                "subjectFlows": 0,
            },
        }

    subjects = project.get("subjects", [])
    dependencies = project.get("dependencies", [])
    skill_index: dict[str, dict[str, str]] = {}
    subject_index: dict[str, dict[str, str]] = {}
    subject_order: dict[str, int] = {}
    subject_skill_counts: dict[str, int] = {}
    for subject in subjects if isinstance(subjects, list) else []:
        if not isinstance(subject, dict):
            continue
        subject_id = str(subject.get("subjectId", ""))
        subject_name = str(subject.get("name", subject_id))
        subject_order[subject_id] = len(subject_order)
        subject_skills = subject.get("skills", [])
        subject_skill_counts[subject_id] = (
            len(subject_skills) if isinstance(subject_skills, list) else 0
        )
        subject_index[subject_id] = {"subjectId": subject_id, "name": subject_name}
        for skill in subject_skills if isinstance(subject_skills, list) else []:
            if not isinstance(skill, dict):
                continue
            skill_id = str(skill.get("skillId", ""))
            if not skill_id:
                continue
            skill_index[skill_id] = {
                "skillId": skill_id,
                "name": str(skill.get("name", skill_id)),
                "subjectId": subject_id,
                "subjectName": subject_name,
                "quizId": str(skill.get("quizId", "")),
            }

    prereqs: dict[str, list[str]] = defaultdict(list)
    dependents: dict[str, list[str]] = defaultdict(list)
    subject_flows: Counter[tuple[str, str]] = Counter()
    missing_refs: list[dict[str, str]] = []

    for dependency in dependencies if isinstance(dependencies, list) else []:
        if not isinstance(dependency, dict):
            continue
        skill_id = str(dependency.get("skillId", ""))
        prereq_id = str(dependency.get("dependsOnSkillId", ""))
        if skill_id not in skill_index or prereq_id not in skill_index:
            missing_refs.append({"skillId": skill_id, "dependsOnSkillId": prereq_id})
            continue
        prereqs[skill_id].append(prereq_id)
        dependents[prereq_id].append(skill_id)
        source_subject = skill_index[prereq_id]["subjectId"]
        target_subject = skill_index[skill_id]["subjectId"]
        if source_subject != target_subject:
            subject_flows[(source_subject, target_subject)] += 1

    depths = _dependency_depths(skill_index, prereqs, dependents)
    bottlenecks = sorted(
        (
            {
                **skill_index[skill_id],
                "dependentCount": len(dependents.get(skill_id, [])),
                "prerequisiteCount": len(prereqs.get(skill_id, [])),
                "depth": depths.get(skill_id, 0),
            }
            for skill_id in skill_index
        ),
        key=lambda row: (
            -_row_int(row, "dependentCount"),
            -_row_int(row, "depth"),
            str(row["skillId"]),
        ),
    )[:16]

    neighborhoods = {
        skill_id: {
            **skill_index[skill_id],
            "depth": depths.get(skill_id, 0),
            "prerequisites": _skill_rows(prereqs.get(skill_id, []), skill_index),
            "dependents": _skill_rows(dependents.get(skill_id, []), skill_index),
        }
        for skill_id in sorted(skill_index)
    }
    longest_paths = sorted(
        (
            {
                **skill_index[skill_id],
                "depth": depths.get(skill_id, 0),
                "prerequisiteCount": len(prereqs.get(skill_id, [])),
                "dependentCount": len(dependents.get(skill_id, [])),
            }
            for skill_id in skill_index
        ),
        key=lambda row: (-_row_int(row, "depth"), str(row["skillId"])),
    )[:16]
    roots = [skill_id for skill_id in skill_index if not prereqs.get(skill_id)]
    leaves = [skill_id for skill_id in skill_index if not dependents.get(skill_id)]
    subject_layout, subject_lane_count = _subject_layout(
        subject_index=subject_index,
        subject_order=subject_order,
        subject_skill_counts=subject_skill_counts,
        subject_flows=subject_flows,
    )

    return {
        "available": True,
        "bottlenecks": bottlenecks,
        "isolatedRisks": {
            "missingDependencyReferences": missing_refs,
            "roots": _skill_rows(roots, skill_index),
            "leaves": _skill_rows(leaves, skill_index),
        },
        "longestPaths": longest_paths,
        "neighborhoods": neighborhoods,
        "subjectLayout": subject_layout,
        "subjectFlows": [
            {
                "sourceSubjectId": source,
                "sourceSubjectName": subject_index.get(source, {}).get("name", source),
                "targetSubjectId": target,
                "targetSubjectName": subject_index.get(target, {}).get("name", target),
                "count": count,
            }
            for (source, target), count in sorted(
                subject_flows.items(),
                key=lambda item: (-item[1], item[0][0], item[0][1]),
            )
        ],
        "summary": {
            "dependencies": sum(len(items) for items in prereqs.values()),
            "leaves": len(leaves),
            "maxDepth": max(depths.values()) if depths else 0,
            "missingDependencyReferences": len(missing_refs),
            "roots": len(roots),
            "skills": len(skill_index),
            "subjectLanes": subject_lane_count,
            "subjectFlows": len(subject_flows),
        },
    }


def _subject_layout(
    *,
    subject_index: dict[str, dict[str, str]],
    subject_order: dict[str, int],
    subject_skill_counts: dict[str, int],
    subject_flows: Counter[tuple[str, str]],
) -> tuple[list[dict[str, object]], int]:
    """Return ordered subject-lane metadata for the dashboard SVG graph."""
    if not subject_index:
        return [], 0
    lane_count = min(8, max(1, round(len(subject_index) ** 0.5)))
    lane_size = max(1, (len(subject_index) + lane_count - 1) // lane_count)
    incoming: Counter[str] = Counter()
    outgoing: Counter[str] = Counter()
    incoming_partners: dict[str, list[tuple[str, int]]] = defaultdict(list)
    outgoing_partners: dict[str, list[tuple[str, int]]] = defaultdict(list)
    for (source, target), count in subject_flows.items():
        outgoing[source] += count
        incoming[target] += count
        outgoing_partners[source].append((target, count))
        incoming_partners[target].append((source, count))
    layout = []
    for subject_id, order in sorted(subject_order.items(), key=lambda item: item[1]):
        lane = min(lane_count - 1, order // lane_size)
        position = order % lane_size
        subject = subject_index.get(
            subject_id, {"subjectId": subject_id, "name": subject_id}
        )
        layout.append(
            {
                "incomingFlowCount": incoming.get(subject_id, 0),
                "incomingSubjectCount": len(incoming_partners.get(subject_id, [])),
                "lane": lane,
                "name": subject["name"],
                "order": order,
                "outgoingFlowCount": outgoing.get(subject_id, 0),
                "outgoingSubjectCount": len(outgoing_partners.get(subject_id, [])),
                "position": position,
                "skillCount": subject_skill_counts.get(subject_id, 0),
                "subjectId": subject_id,
                "topIncomingFlow": _subject_flow_summary(
                    incoming_partners.get(subject_id, []), subject_index
                ),
                "topOutgoingFlow": _subject_flow_summary(
                    outgoing_partners.get(subject_id, []), subject_index
                ),
            }
        )
    return layout, lane_count


def _subject_flow_summary(
    flows: list[tuple[str, int]],
    subject_index: dict[str, dict[str, str]],
) -> dict[str, object] | None:
    """Return the largest partner flow for one dashboard subject node."""
    if not flows:
        return None
    partner_id, count = max(flows, key=lambda item: (item[1], item[0]))
    subject = subject_index.get(
        partner_id, {"subjectId": partner_id, "name": partner_id}
    )
    return {
        "count": count,
        "subjectId": partner_id,
        "subjectName": subject["name"],
    }


def _dependency_depths(
    skill_index: dict[str, dict[str, str]],
    prereqs: dict[str, list[str]],
    dependents: dict[str, list[str]],
) -> dict[str, int]:
    indegree = {skill_id: len(prereqs.get(skill_id, [])) for skill_id in skill_index}
    depths = {skill_id: 0 for skill_id in skill_index}
    queue: deque[str] = deque(
        sorted(skill_id for skill_id, degree in indegree.items() if degree == 0)
    )
    while queue:
        current = queue.popleft()
        for dependent in sorted(dependents.get(current, [])):
            depths[dependent] = max(depths[dependent], depths[current] + 1)
            indegree[dependent] -= 1
            if indegree[dependent] == 0:
                queue.append(dependent)
    return depths


def _skill_rows(
    skill_ids: list[str],
    skill_index: dict[str, dict[str, str]],
) -> list[dict[str, str]]:
    return [
        skill_index[skill_id]
        for skill_id in sorted(skill_ids)
        if skill_id in skill_index
    ]


def _row_int(row: Mapping[str, object], key: str) -> int:
    value = row.get(key, 0)
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        return int(value)
    return 0
