from __future__ import annotations

from pathlib import Path
from typing import Any

from src.artifacts.json_io import write_json_artifact
from src.curriculum.diagnostics import curriculum_diagnostic_gap_map
from src.curriculum.graph import CurriculumGraph
from src.scholarship.gap_report import ScholarshipGapReport
from src.scholarship.source_health import SourceHealthAudit

_DENSE_FIGURE_LABELS = (
    "fig:graph_bottlenecks",
    "fig:vfe_efe_skilltree_bridge",
    "fig:scholarship_source_health",
)


def figure_table_companions(
    *,
    graph: CurriculumGraph,
    source_health: SourceHealthAudit,
    gap_report: ScholarshipGapReport,
    diagnostic_gap_map: dict[str, Any] | None = None,
) -> dict[str, Any]:
    diagnostic_gap_map = diagnostic_gap_map or curriculum_diagnostic_gap_map(graph)
    figures: dict[str, dict[str, object]] = {
        "fig:graph_bottlenecks": _graph_bottleneck_companion(diagnostic_gap_map),
        "fig:vfe_efe_skilltree_bridge": _vfe_efe_bridge_companion(graph),
        "fig:scholarship_source_health": _source_health_companion(
            source_health,
            gap_report,
        ),
    }
    total_rows = 0
    for companion in figures.values():
        rows = companion.get("rows", [])
        if isinstance(rows, list):
            total_rows += len(rows)
    return {
        "claimBoundary": (
            "Companion tables expose generated rows behind dense figures; they are "
            "navigation aids, not new analytical claims."
        ),
        "figures": figures,
        "summary": {
            "companionFigures": len(figures),
            "labels": list(_DENSE_FIGURE_LABELS),
            "rows": total_rows,
        },
    }


def write_figure_table_companions(
    payload: dict[str, Any],
    path: Path,
) -> Path:
    return write_json_artifact(Path(path), payload)


def _graph_bottleneck_companion(payload: dict[str, Any]) -> dict[str, object]:
    rows = []
    for row in payload.get("bottlenecks", [])[:8]:
        if not isinstance(row, dict):
            continue
        rows.append(
            {
                "depth": row.get("depth", 0),
                "downstreamDependents": row.get("downstreamDependentCount", 0),
                "rank": row.get("rank", 0),
                "skillId": row.get("skillId", ""),
                "skillName": row.get("name", ""),
                "stratum": row.get("stratum", ""),
                "subject": row.get("subjectName", ""),
            }
        )
    return {
        "columns": [
            "rank",
            "skillId",
            "skillName",
            "stratum",
            "subject",
            "downstreamDependents",
            "depth",
        ],
        "companionId": "companion:graph_bottlenecks",
        "figureLabel": "fig:graph_bottlenecks",
        "rows": rows,
        "title": "Top graph bottlenecks by downstream fan-out",
    }


def _vfe_efe_bridge_companion(graph: CurriculumGraph) -> dict[str, object]:
    levels = graph.levels()
    edge_counts: dict[str, int] = {subject.subject_id: 0 for subject in graph.subjects}
    subject_by_skill = {
        skill.skill_id: subject
        for subject in graph.subjects
        for skill in subject.skills
    }
    for _, dependent in graph.prerequisite_edges():
        subject = subject_by_skill.get(dependent)
        if subject is not None:
            edge_counts[subject.subject_id] = edge_counts.get(subject.subject_id, 0) + 1
    rows: list[dict[str, object]] = []
    for subject in graph.subjects:
        if not _subject_matches_vfe_efe(subject.name, subject.description):
            skill_text = " ".join(
                f"{skill.name} {skill.objective} {skill.description}"
                for skill in subject.skills
            )
            if not _subject_matches_vfe_efe(skill_text, ""):
                continue
        subject_levels = [levels.get(skill.skill_id, 0) for skill in subject.skills]
        sample_skills = [skill.skill_id for skill in subject.skills[:4]]
        rows.append(
            {
                "depthRange": (
                    f"{min(subject_levels)}-{max(subject_levels)}"
                    if subject_levels
                    else "0-0"
                ),
                "prerequisiteEdges": edge_counts.get(subject.subject_id, 0),
                "representativeSkills": ", ".join(sample_skills),
                "skillCount": len(subject.skills),
                "stratum": subject.stratum.value,
                "subjectId": subject.subject_id,
                "subjectName": subject.name,
            }
        )
    if not rows:
        rows = [
            {
                "depthRange": "0-0",
                "prerequisiteEdges": 0,
                "representativeSkills": "",
                "skillCount": 0,
                "stratum": "",
                "subjectId": "not-found",
                "subjectName": "No VFE/EFE subject rows matched the generated graph",
            }
        ]
    rows.sort(key=lambda row: (str(row["stratum"]), str(row["subjectId"])))
    return {
        "columns": [
            "subjectId",
            "subjectName",
            "stratum",
            "skillCount",
            "prerequisiteEdges",
            "depthRange",
            "representativeSkills",
        ],
        "companionId": "companion:vfe_efe_skilltree_bridge",
        "figureLabel": "fig:vfe_efe_skilltree_bridge",
        "rows": rows[:8],
        "title": "VFE/EFE subject rows and route handoff evidence",
    }


def _source_health_companion(
    source_health: SourceHealthAudit,
    gap_report: ScholarshipGapReport,
) -> dict[str, object]:
    rows: list[dict[str, object]] = [
        {
            "code": issue.code,
            "key": issue.key,
            "message": issue.message,
            "status": "review",
        }
        for issue in source_health.issue_list[:12]
    ]
    if not rows:
        summary = gap_report.to_dict().get("summary", {})
        rows.append(
            {
                "code": "pass",
                "key": "all-sources",
                "message": (
                    f"{source_health.source_count} local source rows passed; "
                    f"online checked={source_health.checked_online}; "
                    f"frontier sources={summary.get('frontierSources', 0) if isinstance(summary, dict) else 0}"
                ),
                "status": "pass",
            }
        )
    return {
        "columns": ["status", "key", "code", "message"],
        "companionId": "companion:scholarship_source_health",
        "figureLabel": "fig:scholarship_source_health",
        "rows": rows,
        "title": "Scholarship source-health issue ledger",
    }


def _subject_matches_vfe_efe(text: str, secondary: str) -> bool:
    combined = f"{text} {secondary}".lower()
    needles = (
        "expected free energy",
        "expected-free-energy",
        "variational free energy",
        "variational-free-energy",
        " vfe",
        " efe",
    )
    return any(needle in combined for needle in needles)
