"""Build manuscript variable maps from live project artifacts."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

from src.curriculum.graph import CurriculumGraph
from src.curriculum.quality import MIN_ASSESSMENTS_PER_SKILL
from src.curriculum.vfe_efe_bridge import vfe_efe_bridge_markdown_table
from src.project_identity import SKILLTREE_PROJECT_ID, SKILLTREE_PROJECT_NAME
from src.provenance.claims import ClaimRegistry
from src.scholarship.coverage import EXPECTED_LANES
from src.skilltree.exporter import export_project
from src.skilltree.summary import summarize_project


def build_manuscript_variables(
    *,
    registry: ClaimRegistry,
    graph: CurriculumGraph,
    scholarship_audit: Mapping[str, Any] | None = None,
    figure_count: int = 0,
    config_path: Path | None = None,
    roadmap: Mapping[str, Any] | None = None,
) -> dict[str, str]:
    """Return rendered claim values plus live curriculum/manuscript counts."""
    stats = graph.stats()
    scholarship_summary: Mapping[str, Any] = {}
    if scholarship_audit:
        maybe_summary = scholarship_audit.get("summary")
        if isinstance(maybe_summary, Mapping):
            scholarship_summary = maybe_summary
    config = _load_config(config_path)
    experiment = config.get("experiment", {}) if isinstance(config, dict) else {}
    min_skill_count = experiment.get("min_skill_count", "")
    # M1: the hand-set enumeration floor must never overstate the real curriculum. If it
    # exceeds the actual skill count the manuscript would render a false "achieved" claim,
    # so fail closed at variable-build time instead of shipping a stale floor.
    skill_count = int(str(stats["skills"]))
    if min_skill_count not in ("", None):
        floor = int(min_skill_count)
        if floor > skill_count:
            raise ValueError(
                f"config min_skill_count {floor} exceeds actual skill count "
                f"{skill_count}; update manuscript/config.yaml or the curriculum"
            )
    roadmap_summary = _roadmap_summary(roadmap)
    export_summary = summarize_project(
        export_project(graph, SKILLTREE_PROJECT_ID, SKILLTREE_PROJECT_NAME)
    )

    variables = {name: registry.get(name).rendered() for name in registry.names()}
    variables.update(
        {
            "skill_count": str(export_summary.skills),
            "subject_count": str(export_summary.subjects),
            "edge_count": str(export_summary.dependencies),
            "max_depth": str(stats["max_depth"]),
            "core_max_depth": str(stats["core_max_depth"]),
            "strata_count": str(stats["strata_count"]),
            "failable_floor": str(MIN_ASSESSMENTS_PER_SKILL),
            "quiz_count": str(export_summary.quizzes),
            "assessment_count": str(export_summary.assessments),
            "claim_count": str(len(registry)),
            "figure_count": str(figure_count),
            "citation_count": str(_summary_int(scholarship_summary, "citedSources")),
            "scholarship_source_count": str(
                _summary_int(scholarship_summary, "matrixSources")
            ),
            "scholarship_lane_count": str(
                _summary_int(scholarship_summary, "expectedLanes", len(EXPECTED_LANES))
            ),
            "sections_with_citations": str(
                _summary_int(scholarship_summary, "sectionsWithCitations")
            ),
            "min_skill_count": str(min_skill_count),
            "vfe_efe_skilltree_bridge_table": vfe_efe_bridge_markdown_table(graph),
            **roadmap_summary,
        }
    )
    return variables


def _summary_int(summary: Mapping[str, Any], key: str, default: int = 0) -> int:
    value = summary.get(key, default)
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    return default


def _load_config(config_path: Path | None) -> dict[str, Any]:
    if config_path is None or not config_path.is_file():
        return {}
    payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _roadmap_summary(roadmap: Mapping[str, Any] | None) -> dict[str, str]:
    if not roadmap:
        return {
            "roadmap_completed_count": "0",
            "roadmap_open_count": "0",
            "roadmap_task_count": "0",
            "roadmap_updated": "",
            "roadmap_next_surfaces": "",
        }
    tasks = roadmap.get("tasks")
    task_rows = (
        [task for task in tasks if isinstance(task, Mapping)]
        if isinstance(tasks, list)
        else []
    )
    open_tasks = [
        task
        for task in task_rows
        if str(task.get("status", "")) in {"todo", "in_progress", "blocked"}
    ]
    done_tasks = [task for task in task_rows if str(task.get("status", "")) == "done"]
    project = roadmap.get("project")
    updated = ""
    if isinstance(project, Mapping):
        updated = str(project.get("updated", ""))
    surfaces = sorted(
        {str(task.get("surface", "")) for task in open_tasks if task.get("surface")}
    )
    return {
        "roadmap_completed_count": str(len(done_tasks)),
        "roadmap_open_count": str(len(open_tasks)),
        "roadmap_task_count": str(len(task_rows)),
        "roadmap_updated": updated,
        "roadmap_next_surfaces": ", ".join(surfaces),
    }
