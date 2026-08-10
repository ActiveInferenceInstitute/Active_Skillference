from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DashboardArtifact:
    """A local file the dashboard may expose read-only."""

    artifact_id: str
    title: str
    relative_path: Path
    media_type: str
    category: str

    def path(self, project_root: Path) -> Path:
        return project_root / self.relative_path

    def to_dict(self, project_root: Path) -> dict[str, object]:
        path = self.path(project_root)
        exists = path.exists()
        stat = path.stat() if exists else None
        return {
            "id": self.artifact_id,
            "title": self.title,
            "category": self.category,
            "path": self.relative_path.as_posix(),
            "url": f"/artifacts/{self.artifact_id}",
            "mediaType": self.media_type,
            "exists": exists,
            "bytes": stat.st_size if stat is not None else 0,
            "modified": stat.st_mtime if stat is not None else None,
        }


ARTIFACTS: tuple[DashboardArtifact, ...] = (
    DashboardArtifact(
        "readme",
        "Project README",
        Path("README.md"),
        "text/markdown; charset=utf-8",
        "docs",
    ),
    DashboardArtifact(
        "quickstart",
        "Quick Start",
        Path("docs/quickstart.md"),
        "text/markdown; charset=utf-8",
        "docs",
    ),
    DashboardArtifact(
        "rendering_pipeline",
        "Rendering Pipeline",
        Path("docs/rendering_pipeline.md"),
        "text/markdown; charset=utf-8",
        "docs",
    ),
    DashboardArtifact(
        "skilltree_project",
        "SkillTree Project JSON",
        Path("output/data/skilltree_project.json"),
        "application/json; charset=utf-8",
        "data",
    ),
    DashboardArtifact(
        "claims",
        "Provenance Claims",
        Path("output/data/claims.json"),
        "application/json; charset=utf-8",
        "data",
    ),
    DashboardArtifact(
        "curriculum_stats",
        "Curriculum Stats",
        Path("output/data/curriculum_stats.json"),
        "application/json; charset=utf-8",
        "data",
    ),
    DashboardArtifact(
        "curriculum_diagnostic_gap_map",
        "Curriculum Diagnostic Gap Map",
        Path("output/data/curriculum_diagnostic_gap_map.json"),
        "application/json; charset=utf-8",
        "data",
    ),
    DashboardArtifact(
        "manuscript_variables",
        "Manuscript Variables",
        Path("output/data/manuscript_variables.json"),
        "application/json; charset=utf-8",
        "data",
    ),
    DashboardArtifact(
        "scholarship_coverage_data",
        "Scholarship Coverage JSON",
        Path("output/data/scholarship_coverage.json"),
        "application/json; charset=utf-8",
        "data",
    ),
    DashboardArtifact(
        "scholarship_source_health_data",
        "Scholarship Source Health JSON",
        Path("output/data/scholarship_source_health.json"),
        "application/json; charset=utf-8",
        "data",
    ),
    DashboardArtifact(
        "scholarship_source_health_network",
        "Scholarship Source Health Network",
        Path("output/data/scholarship_source_health_network.json"),
        "application/json; charset=utf-8",
        "data",
    ),
    DashboardArtifact(
        "manuscript_artifacts",
        "Manuscript Artifact Audit",
        Path("output/data/manuscript_artifacts.json"),
        "application/json; charset=utf-8",
        "data",
    ),
    DashboardArtifact(
        "manuscript_claim_support",
        "Manuscript Claim Support",
        Path("output/data/manuscript_claim_support.json"),
        "application/json; charset=utf-8",
        "data",
    ),
    DashboardArtifact(
        "course_material_index",
        "Course Material Index",
        Path("output/data/course_material_index.json"),
        "application/json; charset=utf-8",
        "data",
    ),
    DashboardArtifact(
        "course_material_audit",
        "Course Material Audit",
        Path("output/data/course_material_audit.json"),
        "application/json; charset=utf-8",
        "data",
    ),
    DashboardArtifact(
        "figure_registry",
        "Figure Registry",
        Path("output/figures/figure_registry.json"),
        "application/json; charset=utf-8",
        "data",
    ),
    DashboardArtifact(
        "figure_table_companions",
        "Figure Table Companions",
        Path("output/data/figure_table_companions.json"),
        "application/json; charset=utf-8",
        "data",
    ),
    DashboardArtifact(
        "active_skillference_cover",
        "Active Skillference Cover",
        Path("output/figures/active_skillference_cover.png"),
        "image/png",
        "cover",
    ),
    DashboardArtifact(
        "active_skillference_skill_atlas",
        "Named Skill Atlas",
        Path("output/figures/active_skillference_skill_atlas.png"),
        "image/png",
        "cover",
    ),
    DashboardArtifact(
        "curriculum_dag",
        "Curriculum DAG Figure",
        Path("output/figures/curriculum_dag.png"),
        "image/png",
        "figures",
    ),
    DashboardArtifact(
        "dependency_strata_flow",
        "Dependency Strata Flow Figure",
        Path("output/figures/dependency_strata_flow.png"),
        "image/png",
        "figures",
    ),
    DashboardArtifact(
        "assessment_depth_matrix",
        "Assessment Depth Matrix",
        Path("output/figures/assessment_depth_matrix.png"),
        "image/png",
        "figures",
    ),
    DashboardArtifact(
        "curriculum_stratum_balance",
        "Curriculum Stratum Balance",
        Path("output/figures/curriculum_stratum_balance.png"),
        "image/png",
        "figures",
    ),
    DashboardArtifact(
        "free_energy_descent",
        "Supplemental VFE Figure",
        Path("output/figures/free_energy_descent.png"),
        "image/png",
        "figures",
    ),
    DashboardArtifact(
        "efe_decomposition",
        "Supplemental EFE Figure",
        Path("output/figures/efe_decomposition.png"),
        "image/png",
        "figures",
    ),
    DashboardArtifact(
        "planning_lookahead",
        "Multi-Step Planning Look-Ahead",
        Path("output/figures/planning_lookahead.png"),
        "image/png",
        "figures",
    ),
    DashboardArtifact(
        "predictive_coding_descent",
        "Predictive Coding Descent",
        Path("output/figures/predictive_coding_descent.png"),
        "image/png",
        "figures",
    ),
    DashboardArtifact(
        "kernel_sensitivity_profiles",
        "Kernel Sensitivity Profiles",
        Path("output/figures/kernel_sensitivity_profiles.png"),
        "image/png",
        "figures",
    ),
    DashboardArtifact(
        "vfe_efe_skilltree_bridge",
        "VFE/EFE SkillTree Bridge",
        Path("output/figures/vfe_efe_skilltree_bridge.png"),
        "image/png",
        "figures",
    ),
    DashboardArtifact(
        "scholarship_coverage",
        "Scholarship Coverage Figure",
        Path("output/figures/scholarship_coverage.png"),
        "image/png",
        "figures",
    ),
    DashboardArtifact(
        "open_science_source_map",
        "Open Science Source Map",
        Path("output/figures/open_science_source_map.png"),
        "image/png",
        "figures",
    ),
    DashboardArtifact(
        "scholarship_source_health",
        "Scholarship Source Health",
        Path("output/figures/scholarship_source_health.png"),
        "image/png",
        "figures",
    ),
    DashboardArtifact(
        "scientific_evidence_matrix",
        "Scientific Evidence Matrix",
        Path("output/figures/scientific_evidence_matrix.png"),
        "image/png",
        "figures",
    ),
    DashboardArtifact(
        "graph_bottlenecks",
        "Graph Bottlenecks",
        Path("output/figures/graph_bottlenecks.png"),
        "image/png",
        "figures",
    ),
    DashboardArtifact(
        "skill_neighborhood_paths",
        "Skill Neighborhood Paths",
        Path("output/figures/skill_neighborhood_paths.png"),
        "image/png",
        "figures",
    ),
    DashboardArtifact(
        "semantic_prerequisite_coverage",
        "Semantic Prerequisite Coverage",
        Path("output/figures/semantic_prerequisite_coverage.png"),
        "image/png",
        "figures",
    ),
    DashboardArtifact(
        "validation_intent_mismatch_matrix",
        "Validation Intent Mismatch Matrix",
        Path("output/figures/validation_intent_mismatch_matrix.png"),
        "image/png",
        "figures",
    ),
    DashboardArtifact(
        "visual_evidence_contract_ladder",
        "Visual Evidence Contract Ladder",
        Path("output/figures/visual_evidence_contract_ladder.png"),
        "image/png",
        "figures",
    ),
    DashboardArtifact(
        "validation_surface_matrix",
        "Validation Surface Matrix",
        Path("output/figures/validation_surface_matrix.png"),
        "image/png",
        "figures",
    ),
    DashboardArtifact(
        "roadmap_risk",
        "Roadmap Risk",
        Path("output/figures/roadmap_risk.png"),
        "image/png",
        "figures",
    ),
    DashboardArtifact(
        "manuscript_pdf",
        "Combined Manuscript PDF",
        Path("output/pdf/Active_Skillference_combined.pdf"),
        "application/pdf",
        "manuscript",
    ),
    DashboardArtifact(
        "manuscript_web",
        "Rendered Web Manuscript",
        Path("output/web/index.html"),
        "text/html; charset=utf-8",
        "manuscript",
    ),
    # Captured browser evidence. These are version-controlled rather than
    # generated, because a recording of the running application cannot be
    # rebuilt from project data the way a plot can.
    DashboardArtifact(
        "app_operational_snapshot",
        "Captured: Operational Snapshot",
        Path("manuscript/assets/screenshots/app_operational_snapshot.png"),
        "image/png",
        "figures",
    ),
    DashboardArtifact(
        "app_official_learner_view",
        "Captured: Official SkillTree Learner View",
        Path("manuscript/assets/screenshots/app_official_learner_view.png"),
        "image/png",
        "figures",
    ),
    DashboardArtifact(
        "app_curriculum_learn_material",
        "Captured: Curriculum Explorer Lesson Record",
        Path("manuscript/assets/screenshots/app_curriculum_learn_material.png"),
        "image/png",
        "figures",
    ),
    DashboardArtifact(
        "app_dependency_graph",
        "Captured: Dependency Graph and Flow Table",
        Path("manuscript/assets/screenshots/app_dependency_graph.png"),
        "image/png",
        "figures",
    ),
    DashboardArtifact(
        "app_runtime_deployment_matrix",
        "Captured: Runtime Deployment Matrix",
        Path("manuscript/assets/screenshots/app_runtime_deployment_matrix.png"),
        "image/png",
        "figures",
    ),
    DashboardArtifact(
        "screenshot_provenance",
        "Captured Screenshot Provenance",
        Path("manuscript/assets/screenshots/screenshot_provenance.json"),
        "application/json; charset=utf-8",
        "data",
    ),
)
