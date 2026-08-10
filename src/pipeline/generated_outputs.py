from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import cast

from src.artifacts.contracts import (
    ClaimSupportAuditPayload,
    RoadmapAuditPayload,
    ScholarshipAuditPayload,
    SourceHealthAuditPayload,
)
from src.artifacts.json_io import read_json_object, write_json_artifact
from src.curriculum.catalog import build_curriculum
from src.curriculum.diagnostics import curriculum_diagnostic_gap_map
from src.curriculum.materials import write_course_material_artifacts
from src.dashboard.artifacts import ARTIFACTS
from src.figures.plots import (
    FigureRenderContext,
    planned_figure_count,
    plot_active_skillference_cover,
    plot_skill_name_atlas,
    render_all,
)
from src.figures.table_companions import (
    figure_table_companions,
    write_figure_table_companions,
)
from src.kernels.examples import build_claim_registry
from src.manuscript.american_english import validate_american_english
from src.manuscript.audit import (
    validate_cover_asset,
    validate_front_matter_visual,
    validate_manuscript_artifacts,
    write_cover_asset_audit,
    write_front_matter_visual_audit,
    write_manuscript_artifact_audit,
)
from src.manuscript.claim_support import (
    audit_manuscript_banned_phrases,
    validate_claim_support,
    write_claim_support_audit,
)
from src.manuscript.variables import build_manuscript_variables
from src.project_paths import project_output_dirs
from src.provenance.binding import validate_curriculum, validate_manuscript_dir
from src.roadmap import load_roadmap
from src.scholarship.coverage import validate_scholarship, write_scholarship_audit
from src.scholarship.gap_report import (
    validate_scholarship_gaps,
    write_scholarship_gap_report,
)
from src.scholarship.source_health import (
    validate_source_health,
    write_source_health_audit,
)
from src.scholarship.source_health_report import (
    scholarship_source_health_network,
    write_scholarship_source_health_network,
)
from src.screenshots.staging import stage_captured_evidence


@dataclass(frozen=True)
class GeneratedOutputBundle:
    paths: tuple[Path, ...]
    provenance_claims: int
    cited_sources: int
    registered_figures: int
    claim_rows: int
    frontier_sources: int
    material_records: int


def build_generated_outputs(project_root: Path | None = None) -> GeneratedOutputBundle:
    root = (
        Path(project_root)
        if project_root is not None
        else Path(__file__).resolve().parents[2]
    )
    registry = build_claim_registry()
    graph = build_curriculum()
    dirs = project_output_dirs(root)
    data_dir = dirs["data"]
    fig_dir = dirs["figures"]
    data_dir.mkdir(parents=True, exist_ok=True)

    validate_curriculum(graph.skills, registry)
    diagnostic_gap_map = curriculum_diagnostic_gap_map(graph)
    diagnostic_gap_path = write_json_artifact(
        data_dir / "curriculum_diagnostic_gap_map.json",
        diagnostic_gap_map,
    )
    manuscript_dir = root / "manuscript"
    if manuscript_dir.is_dir():
        validate_manuscript_dir(manuscript_dir, registry)
        validate_american_english(manuscript_dir)
        banned = audit_manuscript_banned_phrases(manuscript_dir)
        if banned:
            detail = "; ".join(f"{name}: {hits}" for name, hits in banned.items())
            raise SystemExit(
                f"manuscript endorsement-overreach phrases found: {detail}"
            )
    scholarship_audit = validate_scholarship(
        manuscript_dir,
        root / "data" / "scholarship_sources.yaml",
        manuscript_dir / "references.bib",
    )

    claims_path = registry.to_json(data_dir / "claims.json")
    scholarship_path = write_scholarship_audit(
        scholarship_audit,
        data_dir / "scholarship_coverage.json",
    )
    source_health_audit = validate_source_health(
        root / "data" / "scholarship_sources.yaml",
        manuscript_dir / "references.bib",
    )
    source_health_path = write_source_health_audit(
        source_health_audit,
        data_dir / "scholarship_source_health.json",
    )
    claim_support_audit = validate_claim_support(
        manuscript_dir=manuscript_dir,
        support_path=root / "data" / "manuscript_claim_support.yaml",
        source_matrix_path=root / "data" / "scholarship_sources.yaml",
        bib_path=manuscript_dir / "references.bib",
        registry_claim_ids=registry.names(),
        project_root=root,
    )
    claim_support_path = write_claim_support_audit(
        claim_support_audit,
        data_dir / "manuscript_claim_support.json",
    )
    scholarship_gap_report = validate_scholarship_gaps(
        scholarship_audit,
        claim_support_audit,
        manuscript_dir / "references.bib",
    )
    scholarship_gap_path = write_scholarship_gap_report(
        scholarship_gap_report,
        data_dir / "scholarship_gap_report.json",
    )
    source_health_network_path = write_scholarship_source_health_network(
        scholarship_source_health_network(
            scholarship=scholarship_audit,
            source_health=source_health_audit,
            gap_report=scholarship_gap_report,
        ),
        data_dir / "scholarship_source_health_network.json",
    )
    roadmap = load_roadmap(root / "tasks.yaml")
    course_material_index_path, course_material_audit_path, course_material_audit = (
        write_course_material_artifacts(
            graph,
            source_path=root / "data" / "course_material_sources.yaml",
            output_dir=data_dir,
            registry=registry,
        )
    )
    course_material_index = read_json_object(course_material_index_path)
    planned_registered_figures = planned_figure_count(
        include_scholarship=True,
        include_claim_support=True,
        include_roadmap=True,
    )
    cover_path = plot_active_skillference_cover(
        graph,
        registry,
        roadmap,
        fig_dir / "active_skillference_cover.png",
        figure_count=planned_registered_figures,
    )
    skill_atlas_path = plot_skill_name_atlas(
        graph,
        fig_dir / "active_skillference_skill_atlas.png",
    )
    figures = render_all(
        graph,
        registry,
        fig_dir,
        context=FigureRenderContext(
            scholarship_audit=cast(
                ScholarshipAuditPayload, scholarship_audit.to_dict()
            ),
            source_health_audit=cast(
                SourceHealthAuditPayload, source_health_audit.to_dict()
            ),
            claim_support_audit=cast(
                ClaimSupportAuditPayload, claim_support_audit.to_dict()
            ),
            course_material_index=course_material_index,
            course_material_audit=course_material_audit.to_dict(),
            roadmap=cast(RoadmapAuditPayload, roadmap),
        ),
    )
    stage_captured_evidence(project_root=root, figure_dir=fig_dir)
    figure_companion_path = write_figure_table_companions(
        figure_table_companions(
            graph=graph,
            source_health=source_health_audit,
            gap_report=scholarship_gap_report,
            diagnostic_gap_map=diagnostic_gap_map,
        ),
        data_dir / "figure_table_companions.json",
    )
    variables = build_manuscript_variables(
        registry=registry,
        graph=graph,
        scholarship_audit=scholarship_audit.to_dict(),
        figure_count=planned_registered_figures,
        config_path=manuscript_dir / "config.yaml",
        roadmap=roadmap,
    )
    vars_path = data_dir / "manuscript_variables.json"
    write_json_artifact(vars_path, variables)
    dashboard_figure_paths = [
        artifact.relative_path
        for artifact in ARTIFACTS
        if artifact.category == "figures"
    ]
    manuscript_artifact_audit = validate_manuscript_artifacts(
        manuscript_dir=manuscript_dir,
        figure_registry_path=fig_dir / "figure_registry.json",
        figure_dir=fig_dir,
        dashboard_figure_paths=dashboard_figure_paths,
        project_root=root,
    )
    manuscript_artifact_path = write_manuscript_artifact_audit(
        manuscript_artifact_audit,
        data_dir / "manuscript_artifacts.json",
    )
    cover_audit = validate_cover_asset(
        config_path=manuscript_dir / "config.yaml",
        project_root=root,
        figure_registry_path=fig_dir / "figure_registry.json",
        dashboard_artifacts=ARTIFACTS,
    )
    cover_audit_path = write_cover_asset_audit(
        cover_audit,
        data_dir / "cover_asset_audit.json",
    )
    front_matter_visual_audit = validate_front_matter_visual(
        config_path=manuscript_dir / "config.yaml",
        project_root=root,
        figure_registry_path=fig_dir / "figure_registry.json",
        dashboard_artifacts=ARTIFACTS,
    )
    front_matter_visual_audit_path = write_front_matter_visual_audit(
        front_matter_visual_audit,
        data_dir / "front_matter_visual_audit.json",
    )
    paths = (
        claims_path,
        diagnostic_gap_path,
        vars_path,
        scholarship_path,
        source_health_path,
        source_health_network_path,
        claim_support_path,
        scholarship_gap_path,
        figure_companion_path,
        manuscript_artifact_path,
        cover_audit_path,
        front_matter_visual_audit_path,
        course_material_index_path,
        course_material_audit_path,
        cover_path,
        skill_atlas_path,
        *figures,
    )
    material_records = course_material_audit.summary["materialRecords"]
    if not isinstance(material_records, int):
        material_records = int(str(material_records))
    return GeneratedOutputBundle(
        paths=paths,
        provenance_claims=len(registry),
        cited_sources=int(scholarship_audit.to_dict()["summary"]["citedSources"]),
        registered_figures=int(
            manuscript_artifact_audit.to_dict()["summary"]["registeredFigures"]
        ),
        claim_rows=int(claim_support_audit.to_dict()["summary"]["claimRows"]),
        frontier_sources=int(
            scholarship_gap_report.to_dict()["summary"]["frontierSources"]
        ),
        material_records=material_records,
    )
