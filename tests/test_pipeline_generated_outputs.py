from __future__ import annotations

from pathlib import Path

from src.pipeline.generated_outputs import (
    GeneratedOutputBundle,
    build_generated_outputs,
)

REPO = Path(__file__).resolve().parents[1]


def test_build_generated_outputs_returns_existing_artifact_bundle() -> None:
    bundle = build_generated_outputs(REPO)

    assert isinstance(bundle, GeneratedOutputBundle)
    assert bundle.provenance_claims == 79
    assert bundle.cited_sources == 188
    assert bundle.registered_figures == 26
    assert bundle.claim_rows == 74
    assert bundle.frontier_sources == 45
    assert bundle.material_records == 630
    assert (REPO / "output" / "data" / "claims.json") in bundle.paths
    assert (
        REPO / "output" / "data" / "curriculum_diagnostic_gap_map.json"
    ) in bundle.paths
    assert (REPO / "output" / "data" / "manuscript_variables.json") in bundle.paths
    assert (
        REPO / "output" / "data" / "scholarship_source_health_network.json"
    ) in bundle.paths
    assert (REPO / "output" / "data" / "figure_table_companions.json") in bundle.paths
    assert (REPO / "output" / "data" / "course_material_index.json") in bundle.paths
    assert (
        REPO / "output" / "figures" / "active_skillference_cover.png"
    ) in bundle.paths
    assert (
        REPO / "output" / "figures" / "active_skillference_skill_atlas.png"
    ) in bundle.paths
    assert all(path.exists() for path in bundle.paths)
