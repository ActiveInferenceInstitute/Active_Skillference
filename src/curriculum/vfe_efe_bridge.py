"""Generated VFE/EFE bridge rows from the validated curriculum graph."""

from __future__ import annotations

from dataclasses import dataclass

from src.curriculum.graph import CurriculumGraph

VFE_EFE_BRIDGE_SUBJECT_IDS: tuple[str, ...] = (
    "sub_free_energy",
    "sub_efe",
    "sub_scientific_supplement_variational",
    "sub_scientific_supplement_active_inference",
    "sub_skilltree_mastery_variational",
    "sub_skilltree_mastery_active_inference",
)

_ROLES: dict[str, str] = {
    "sub_free_energy": "VFE core",
    "sub_efe": "EFE core",
    "sub_scientific_supplement_variational": "VFE supplement",
    "sub_scientific_supplement_active_inference": "EFE supplement",
    "sub_skilltree_mastery_variational": "VFE mastery",
    "sub_skilltree_mastery_active_inference": "EFE mastery",
}


@dataclass(frozen=True)
class VfeEfeBridgeRow:
    """One real SkillTree subject row in the VFE/EFE supplement bridge."""

    role: str
    subject_id: str
    subject_name: str
    skill_count: int
    prerequisite_edges: int
    internal_edges: int
    downstream_edges: int
    min_depth: int
    max_depth: int
    representative_skill_ids: tuple[str, ...]
    representative_quiz_ids: tuple[str, ...]
    learn_route: str
    quiz_route: str


def build_vfe_efe_bridge_rows(graph: CurriculumGraph) -> tuple[VfeEfeBridgeRow, ...]:
    """Return VFE/EFE bridge rows from real subjects, skills and edges."""
    by_subject_id = {subject.subject_id: subject for subject in graph.subjects}
    missing = [
        subject_id
        for subject_id in VFE_EFE_BRIDGE_SUBJECT_IDS
        if subject_id not in by_subject_id
    ]
    if missing:
        raise ValueError("missing VFE/EFE bridge subjects: " + ", ".join(missing))

    levels = graph.levels()
    edges = graph.prerequisite_edges()
    rows: list[VfeEfeBridgeRow] = []
    for subject_id in VFE_EFE_BRIDGE_SUBJECT_IDS:
        subject = by_subject_id[subject_id]
        skill_ids = tuple(skill.skill_id for skill in subject.skills)
        skill_set = set(skill_ids)
        inbound = [(pre, dep) for pre, dep in edges if dep in skill_set]
        internal = [(pre, dep) for pre, dep in inbound if pre in skill_set]
        downstream = [
            (pre, dep)
            for pre, dep in edges
            if pre in skill_set and dep not in skill_set
        ]
        depth_values = [levels[skill_id] for skill_id in skill_ids]
        representatives = _representative_skill_ids(skill_ids)
        representative_quiz_ids = tuple(
            f"{skill_id}_quiz" for skill_id in representatives
        )
        quiz_skill_id = representatives[-1]
        rows.append(
            VfeEfeBridgeRow(
                role=_ROLES[subject_id],
                subject_id=subject.subject_id,
                subject_name=subject.name,
                skill_count=len(skill_ids),
                prerequisite_edges=len(inbound),
                internal_edges=len(internal),
                downstream_edges=len(downstream),
                min_depth=min(depth_values),
                max_depth=max(depth_values),
                representative_skill_ids=representatives,
                representative_quiz_ids=representative_quiz_ids,
                learn_route=f"/subjects/{subject.subject_id}",
                quiz_route=(
                    f"/subjects/{subject.subject_id}/skills/{quiz_skill_id}/quizzes/"
                    f"{quiz_skill_id}_quiz"
                ),
            )
        )
    return tuple(rows)


def vfe_efe_bridge_markdown_table(graph: CurriculumGraph) -> str:
    """Render a Markdown table from the same bridge rows used for the figure."""
    rows = build_vfe_efe_bridge_rows(graph)
    lines = [
        "| Layer | Skills | Prerequisite edges | Depth | Representative IDs | Learn route | Quiz route |",
        "| --- | --- | ---: | ---: | ---: | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                (
                    row.role,
                    str(row.skill_count),
                    f"{row.prerequisite_edges} total; {row.internal_edges} internal",
                    f"{row.min_depth}-{row.max_depth}",
                    "<br>".join(
                        f"`{skill_id}`" for skill_id in row.representative_skill_ids
                    ),
                    f"`{row.learn_route}`",
                    f"`{row.quiz_route}`",
                )
            )
            + " |"
        )
    return "\n".join(lines)


def _representative_skill_ids(skill_ids: tuple[str, ...]) -> tuple[str, ...]:
    if len(skill_ids) <= 3:
        return skill_ids
    indexes = (0, len(skill_ids) // 2, len(skill_ids) - 1)
    seen: set[str] = set()
    out: list[str] = []
    for index in indexes:
        skill_id = skill_ids[index]
        if skill_id not in seen:
            seen.add(skill_id)
            out.append(skill_id)
    return tuple(out)
