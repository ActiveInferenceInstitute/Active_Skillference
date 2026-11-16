from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from src.pipeline.generated_outputs import (
    GeneratedOutputBundle,
    build_generated_outputs,
)

REPO = Path(__file__).resolve().parents[1]


@pytest.mark.slow
def test_build_generated_outputs_returns_existing_artifact_bundle(
    tmp_path: Path,
) -> None:
    root = tmp_path / "project"
    shutil.copytree(
        REPO,
        root,
        ignore=shutil.ignore_patterns(
            ".git",
            ".venv",
            ".local",
            "__pycache__",
            ".pytest_cache",
            ".mypy_cache",
            ".ruff_cache",
            "node_modules",
        ),
    )
    bundle = build_generated_outputs(root)

    assert isinstance(bundle, GeneratedOutputBundle)
    assert bundle.provenance_claims == 79
    assert bundle.cited_sources == 188
    assert bundle.registered_figures == 26
    assert bundle.claim_rows == 74
    assert bundle.frontier_sources == 45
    assert bundle.material_records == 630
    assert (root / "output" / "data" / "claims.json") in bundle.paths
    assert (
        root / "output" / "data" / "curriculum_diagnostic_gap_map.json"
    ) in bundle.paths
    assert (root / "output" / "data" / "manuscript_variables.json") in bundle.paths
    assert (
        root / "output" / "data" / "scholarship_source_health_network.json"
    ) in bundle.paths
    assert (root / "output" / "data" / "figure_table_companions.json") in bundle.paths
    assert (root / "output" / "data" / "course_material_index.json") in bundle.paths
    assert (
        root / "output" / "figures" / "active_skillference_cover.png"
    ) in bundle.paths
    assert (
        root / "output" / "figures" / "active_skillference_skill_atlas.png"
    ) in bundle.paths
    assert all(path.exists() for path in bundle.paths)
    variables = json.loads(
        (root / "output" / "data" / "manuscript_variables.json").read_text()
    )
    registered = json.loads(
        (root / "output" / "figures" / "figure_registry.json").read_text()
    )
    assert (
        int(variables["figure_count"]) == len(registered) == bundle.registered_figures
    )


def test_importable_builder_raises_package_error_for_endorsement_overreach(
    tmp_path: Path,
) -> None:
    manuscript = tmp_path / "manuscript"
    manuscript.mkdir()
    (manuscript / "00_fixture.md").write_text(
        "The platform is NSA approved for all learners.",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="endorsement-overreach"):
        build_generated_outputs(tmp_path)
