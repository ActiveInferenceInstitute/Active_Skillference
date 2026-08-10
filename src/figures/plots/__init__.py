"""Deterministic figures for the platform.

Figures are driven entirely by validated data from :class:`~src.curriculum.graph.CurriculumGraph`,
:class:`~src.provenance.claims.ClaimRegistry`, and scholarship audit payloads.
``matplotlib`` uses the headless ``Agg`` backend.
"""

from __future__ import annotations

from .curriculum import (
    plot_assessment_depth_matrix,
    plot_curriculum_dag,
    plot_curriculum_stratum_balance,
    plot_dependency_strata_flow,
)
from .front_matter import (
    _skill_name_atlas_payload,
    plot_active_skillference_cover,
    plot_skill_name_atlas,
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
from .registry_io import (
    FigureRenderContext,
    planned_figure_count,
    planned_figure_registry_entries,
    render_all,
)
from .roadmap import plot_roadmap_risk
from .scholarship import (
    plot_open_science_source_map,
    plot_scholarship_coverage,
    plot_scholarship_source_health,
)
from .style import FigureRegistryError
from .validation import (
    plot_scientific_evidence_matrix,
    plot_validation_surface_matrix,
    validation_surface_matrix,
)
from .validation_intent import (
    plot_semantic_prerequisite_coverage,
    plot_validation_intent_mismatch_matrix,
    plot_visual_evidence_contract_ladder,
)

__all__ = [
    "FigureRegistryError",
    "FigureRenderContext",
    "_skill_name_atlas_payload",
    "planned_figure_count",
    "planned_figure_registry_entries",
    "plot_active_skillference_cover",
    "plot_assessment_depth_matrix",
    "plot_curriculum_dag",
    "plot_curriculum_stratum_balance",
    "plot_dependency_strata_flow",
    "plot_efe_decomposition",
    "plot_free_energy_descent",
    "plot_graph_bottlenecks",
    "plot_kernel_sensitivity_profiles",
    "plot_open_science_source_map",
    "plot_planning_lookahead",
    "plot_predictive_coding",
    "plot_roadmap_risk",
    "plot_scholarship_coverage",
    "plot_scholarship_source_health",
    "plot_scientific_evidence_matrix",
    "plot_semantic_prerequisite_coverage",
    "plot_skill_name_atlas",
    "plot_skill_neighborhood_paths",
    "plot_validation_intent_mismatch_matrix",
    "plot_validation_surface_matrix",
    "plot_vfe_efe_skilltree_bridge",
    "plot_visual_evidence_contract_ladder",
    "render_all",
    "validation_surface_matrix",
]
