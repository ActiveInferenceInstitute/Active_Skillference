#!/usr/bin/env python3
"""Validate manuscript scholarship coverage and render its audit artifacts."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "src"))

from src.curriculum.catalog import build_curriculum
from src.curriculum.materials import (
    audit_course_material_index,
    build_course_material_index,
    load_material_sources,
)
from src.figures.plots import (
    plot_open_science_source_map,
    plot_scholarship_coverage,
    plot_scholarship_source_health,
)
from src.kernels.examples import build_claim_registry
from src.manuscript.claim_support import validate_claim_support
from src.project_paths import project_output_dirs
from src.scholarship.coverage import (
    validate_scholarship,
    write_scholarship_audit,
)
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


def main() -> list[Path]:
    dirs = project_output_dirs()
    audit = validate_scholarship(
        _ROOT / "manuscript",
        _ROOT / "data" / "scholarship_sources.yaml",
        _ROOT / "manuscript" / "references.bib",
    )
    data_path = write_scholarship_audit(
        audit,
        dirs["data"] / "scholarship_coverage.json",
    )
    figure_path = plot_scholarship_coverage(
        audit.to_dict(),
        dirs["figures"] / "scholarship_coverage.png",
    )
    graph = build_curriculum()
    registry = build_claim_registry()
    material_sources = load_material_sources(
        _ROOT / "data" / "course_material_sources.yaml"
    )
    course_material_index = build_course_material_index(
        graph,
        material_sources,
        registry=registry,
    )
    course_material_audit = audit_course_material_index(
        course_material_index,
        graph,
    )
    open_science_path = plot_open_science_source_map(
        audit.to_dict(),
        dirs["figures"] / "open_science_source_map.png",
        course_material_index=course_material_index,
        course_material_audit=course_material_audit.to_dict(),
    )
    health = validate_source_health(
        _ROOT / "data" / "scholarship_sources.yaml",
        _ROOT / "manuscript" / "references.bib",
    )
    health_path = write_source_health_audit(
        health,
        dirs["data"] / "scholarship_source_health.json",
    )
    health_figure_path = plot_scholarship_source_health(
        health.to_dict(),
        dirs["figures"] / "scholarship_source_health.png",
    )
    claim_support = validate_claim_support(
        manuscript_dir=_ROOT / "manuscript",
        support_path=_ROOT / "data" / "manuscript_claim_support.yaml",
        source_matrix_path=_ROOT / "data" / "scholarship_sources.yaml",
        bib_path=_ROOT / "manuscript" / "references.bib",
        registry_claim_ids=registry.names(),
        project_root=_ROOT,
    )
    gap_report = validate_scholarship_gaps(
        audit,
        claim_support,
        _ROOT / "manuscript" / "references.bib",
    )
    gap_path = write_scholarship_gap_report(
        gap_report,
        dirs["data"] / "scholarship_gap_report.json",
    )
    health_network = scholarship_source_health_network(
        scholarship=audit,
        source_health=health,
        gap_report=gap_report,
    )
    health_network_path = write_scholarship_source_health_network(
        health_network,
        dirs["data"] / "scholarship_source_health_network.json",
    )
    summary = audit.to_dict()["summary"]
    print(
        "scholarship coverage valid: "
        f"{summary['citedSources']} cited sources across "
        f"{summary['expectedLanes']} lanes"
    )
    print(
        "scholarship gap report valid: "
        f"{gap_report.to_dict()['summary']['frontierSources']} frontier sources"
    )
    print(str(data_path))
    print(str(figure_path))
    print(str(open_science_path))
    print(str(health_path))
    print(str(health_figure_path))
    print(str(gap_path))
    print(str(health_network_path))
    return [
        data_path,
        figure_path,
        open_science_path,
        health_path,
        health_figure_path,
        gap_path,
        health_network_path,
    ]


if __name__ == "__main__":
    main()
