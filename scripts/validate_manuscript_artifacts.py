#!/usr/bin/env python3
"""Validate manuscript figure labels against generated figures and dashboard artifacts."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "src"))

from src.dashboard.artifacts import ARTIFACTS
from src.manuscript.audit import (
    validate_cover_asset,
    validate_front_matter_visual,
    validate_manuscript_artifacts,
    write_cover_asset_audit,
    write_front_matter_visual_audit,
    write_manuscript_artifact_audit,
)
from src.project_paths import project_output_dirs


def main() -> list[Path]:
    dirs = project_output_dirs()
    dashboard_figure_paths = [
        artifact.relative_path
        for artifact in ARTIFACTS
        if artifact.category == "figures"
    ]
    audit = validate_manuscript_artifacts(
        manuscript_dir=_ROOT / "manuscript",
        figure_registry_path=dirs["figures"] / "figure_registry.json",
        figure_dir=dirs["figures"],
        dashboard_figure_paths=dashboard_figure_paths,
        project_root=_ROOT,
    )
    path = write_manuscript_artifact_audit(
        audit,
        dirs["data"] / "manuscript_artifacts.json",
    )
    cover_audit = validate_cover_asset(
        config_path=_ROOT / "manuscript" / "config.yaml",
        project_root=_ROOT,
        figure_registry_path=dirs["figures"] / "figure_registry.json",
        dashboard_artifacts=ARTIFACTS,
    )
    cover_path = write_cover_asset_audit(
        cover_audit,
        dirs["data"] / "cover_asset_audit.json",
    )
    front_matter_visual_audit = validate_front_matter_visual(
        config_path=_ROOT / "manuscript" / "config.yaml",
        project_root=_ROOT,
        figure_registry_path=dirs["figures"] / "figure_registry.json",
        dashboard_artifacts=ARTIFACTS,
    )
    front_matter_visual_path = write_front_matter_visual_audit(
        front_matter_visual_audit,
        dirs["data"] / "front_matter_visual_audit.json",
    )
    summary = audit.to_dict()["summary"]
    print(
        "manuscript artifacts valid: "
        f"{summary['registeredFigures']} figures, "
        f"{summary['declaredFigureLabels']} declarations, "
        f"{summary['referencedFigureLabels']} references"
    )
    print("cover asset valid: active_skillference_cover.png")
    print("page-two visual valid: active_skillference_skill_atlas.png")
    print(str(path))
    print(str(cover_path))
    print(str(front_matter_visual_path))
    return [path, cover_path, front_matter_visual_path]


if __name__ == "__main__":
    main()
