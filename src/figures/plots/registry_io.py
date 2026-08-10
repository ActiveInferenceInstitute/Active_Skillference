from __future__ import annotations

import os
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import matplotlib

from src.artifacts.contracts import (
    ClaimSupportAuditPayload,
    RoadmapAuditPayload,
    ScholarshipAuditPayload,
    SourceHealthAuditPayload,
)

os.environ.setdefault("MPLBACKEND", "Agg")
matplotlib.use("Agg")


from src.artifacts.json_io import (
    write_json_artifact,
)
from src.curriculum.graph import CurriculumGraph
from src.figures.registry import CAPTURED_EVIDENCE, RENDERED_EVIDENCE
from src.figures.registry_manifest import figure_registry_payload
from src.provenance.claims import ClaimRegistry

from .curriculum import (
    plot_assessment_depth_matrix,
    plot_curriculum_dag,
    plot_curriculum_stratum_balance,
    plot_dependency_strata_flow,
)
from .graph_diagnostics import (
    plot_graph_bottlenecks,
    plot_skill_neighborhood_paths,
    plot_vfe_efe_skilltree_bridge,
)
from .kernels import (
    plot_efe_decomposition,
    plot_free_energy_descent,
    plot_kernel_sensitivity_profiles,
    plot_planning_lookahead,
    plot_predictive_coding,
)
from .roadmap import plot_roadmap_risk
from .scholarship import (
    plot_open_science_source_map,
    plot_scholarship_coverage,
    plot_scholarship_source_health,
)
from .style import (
    FigureRegistryError,
)
from .validation import plot_scientific_evidence_matrix, plot_validation_surface_matrix
from .validation_intent import (
    plot_semantic_prerequisite_coverage,
    plot_validation_intent_mismatch_matrix,
    plot_visual_evidence_contract_ladder,
)


@dataclass(frozen=True)
class FigureRenderContext:
    """Optional audit payloads passed into ``render_all``."""

    scholarship_audit: ScholarshipAuditPayload | None = None
    source_health_audit: SourceHealthAuditPayload | None = None
    claim_support_audit: ClaimSupportAuditPayload | None = None
    course_material_index: Mapping[str, Any] | None = None
    course_material_audit: Mapping[str, Any] | None = None
    roadmap: RoadmapAuditPayload | None = None


def render_all(
    graph: CurriculumGraph,
    registry: ClaimRegistry,
    out_dir: Path,
    *,
    context: FigureRenderContext | None = None,
    scholarship_audit: ScholarshipAuditPayload | None = None,
    source_health_audit: SourceHealthAuditPayload | None = None,
    claim_support_audit: ClaimSupportAuditPayload | None = None,
    course_material_index: Mapping[str, Any] | None = None,
    course_material_audit: Mapping[str, Any] | None = None,
    roadmap: RoadmapAuditPayload | None = None,
) -> list[Path]:
    """Render all figures into ``out_dir`` and return their paths."""
    if context is not None:
        scholarship_audit = context.scholarship_audit
        source_health_audit = context.source_health_audit
        claim_support_audit = context.claim_support_audit
        course_material_index = context.course_material_index
        course_material_audit = context.course_material_audit
        roadmap = context.roadmap
    out_dir = Path(out_dir)
    include_scholarship = scholarship_audit is not None
    include_claim_support = claim_support_audit is not None
    include_roadmap = roadmap is not None
    planned_count = planned_figure_count(
        include_scholarship=include_scholarship,
        include_claim_support=include_claim_support,
        include_roadmap=include_roadmap,
    )
    figures = [
        plot_curriculum_dag(graph, out_dir / "curriculum_dag.png"),
        plot_dependency_strata_flow(graph, out_dir / "dependency_strata_flow.png"),
        plot_assessment_depth_matrix(graph, out_dir / "assessment_depth_matrix.png"),
        plot_curriculum_stratum_balance(
            graph, out_dir / "curriculum_stratum_balance.png"
        ),
        plot_free_energy_descent(registry, out_dir / "free_energy_descent.png"),
        plot_efe_decomposition(registry, out_dir / "efe_decomposition.png"),
        plot_planning_lookahead(registry, out_dir / "planning_lookahead.png"),
        plot_predictive_coding(registry, out_dir / "predictive_coding_descent.png"),
        plot_graph_bottlenecks(graph, out_dir / "graph_bottlenecks.png"),
        plot_skill_neighborhood_paths(graph, out_dir / "skill_neighborhood_paths.png"),
        plot_semantic_prerequisite_coverage(
            graph, out_dir / "semantic_prerequisite_coverage.png"
        ),
        plot_visual_evidence_contract_ladder(
            graph, out_dir / "visual_evidence_contract_ladder.png"
        ),
        plot_kernel_sensitivity_profiles(
            registry,
            out_dir / "kernel_sensitivity_profiles.png",
        ),
        plot_vfe_efe_skilltree_bridge(
            graph,
            out_dir / "vfe_efe_skilltree_bridge.png",
        ),
        plot_validation_intent_mismatch_matrix(
            out_dir / "validation_intent_mismatch_matrix.png",
            figure_count=planned_count,
            include_scholarship=include_scholarship,
            include_claim_support=include_claim_support,
            include_roadmap=include_roadmap,
        ),
    ]
    if scholarship_audit is not None:
        figures.append(
            plot_scholarship_coverage(
                scholarship_audit,
                out_dir / "scholarship_coverage.png",
            )
        )
        figures.append(
            plot_open_science_source_map(
                scholarship_audit,
                out_dir / "open_science_source_map.png",
                course_material_index=course_material_index,
                course_material_audit=course_material_audit,
            )
        )
        figures.append(
            plot_scholarship_source_health(
                source_health_audit
                or {
                    "summary": {
                        "issueCount": 0,
                        "onlineCheckedSources": 0,
                        "sources": 0,
                    }
                },
                out_dir / "scholarship_source_health.png",
            )
        )
        figures.append(
            plot_validation_surface_matrix(
                graph,
                registry,
                scholarship_audit,
                out_dir / "validation_surface_matrix.png",
                figure_count=planned_count,
            )
        )
    if claim_support_audit is not None:
        figures.append(
            plot_scientific_evidence_matrix(
                claim_support_audit,
                out_dir / "scientific_evidence_matrix.png",
            )
        )
    if roadmap is not None:
        figures.append(plot_roadmap_risk(roadmap, out_dir / "roadmap_risk.png"))
    _write_figure_registry(
        out_dir,
        include_scholarship=include_scholarship,
        include_claim_support=include_claim_support,
        include_roadmap=include_roadmap,
    )
    _validate_rendered_figure_registry(
        out_dir,
        figures,
        include_scholarship=include_scholarship,
        include_claim_support=include_claim_support,
        include_roadmap=include_roadmap,
    )
    return figures


def planned_figure_registry_entries(
    *,
    include_scholarship: bool = False,
    include_claim_support: bool = False,
    include_roadmap: bool = False,
) -> tuple[dict[str, Any], ...]:
    """Return the canonical *rendered* registry rows for a render configuration.

    Captured browser evidence is excluded: these rows drive ``render_all`` and
    the validation-surface figures, both of which describe the deterministic
    render pipeline. Counting a recording among the things that pipeline
    produces would overstate what it can rebuild from source.
    """
    return tuple(
        dict(entry)
        for entry in figure_registry_payload(
            include_scholarship=include_scholarship,
            include_claim_support=include_claim_support,
            include_roadmap=include_roadmap,
        )
        if str(entry.get("evidence_kind", RENDERED_EVIDENCE)) != CAPTURED_EVIDENCE
    )


def planned_figure_count(
    *,
    include_scholarship: bool = False,
    include_claim_support: bool = False,
    include_roadmap: bool = False,
) -> int:
    """Return the canonical number of registered figures for a render configuration."""
    return len(
        planned_figure_registry_entries(
            include_scholarship=include_scholarship,
            include_claim_support=include_claim_support,
            include_roadmap=include_roadmap,
        )
    )


def _write_figure_registry(
    out_dir: Path,
    *,
    include_scholarship: bool = False,
    include_claim_support: bool = False,
    include_roadmap: bool = False,
) -> Path:
    registry = figure_registry_payload(
        include_scholarship=include_scholarship,
        include_claim_support=include_claim_support,
        include_roadmap=include_roadmap,
    )
    path = out_dir / "figure_registry.json"
    return write_json_artifact(path, registry)


def _validate_rendered_figure_registry(
    out_dir: Path,
    rendered_paths: Iterable[Path],
    *,
    include_scholarship: bool = False,
    include_claim_support: bool = False,
    include_roadmap: bool = False,
) -> None:
    registry = figure_registry_payload(
        include_scholarship=include_scholarship,
        include_claim_support=include_claim_support,
        include_roadmap=include_roadmap,
    )
    # Captured browser evidence is registered alongside the deterministic
    # figures so it carries the same contract, but render_all does not produce
    # it and must not demand it here.
    rendered_registry = [
        entry
        for entry in registry
        if str(entry.get("evidence_kind", RENDERED_EVIDENCE)) != CAPTURED_EVIDENCE
    ]
    registry_names = {str(entry["filename"]) for entry in rendered_registry}
    rendered_names = {Path(path).name for path in rendered_paths}
    if registry_names != rendered_names:
        missing_from_registry = sorted(rendered_names - registry_names)
        missing_from_render = sorted(registry_names - rendered_names)
        raise FigureRegistryError(
            "figure registry/rendered output mismatch: "
            f"missing from registry={missing_from_registry}; "
            f"missing from rendered outputs={missing_from_render}"
        )
    missing_files = sorted(
        name for name in registry_names if not (Path(out_dir) / name).is_file()
    )
    if missing_files:
        raise FigureRegistryError(
            "registered figure files were not written: " + ", ".join(missing_files)
        )
