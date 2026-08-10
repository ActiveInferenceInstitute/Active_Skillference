#!/usr/bin/env python3
"""Build deterministic dashboard course-material artifacts."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "src"))

from src.curriculum.catalog import build_curriculum
from src.curriculum.materials import write_course_material_artifacts
from src.kernels.examples import build_claim_registry
from src.project_paths import project_output_dirs


def main() -> list[Path]:
    graph = build_curriculum()
    registry = build_claim_registry()
    dirs = project_output_dirs()
    index_path, audit_path, audit = write_course_material_artifacts(
        graph,
        source_path=_ROOT / "data" / "course_material_sources.yaml",
        output_dir=dirs["data"],
        registry=registry,
    )
    summary = audit.to_dict()["summary"]
    print(
        "course materials valid: "
        f"{summary['materialRecords']} skills / "
        f"{summary['externalPointers']} external pointers"
    )
    print(str(index_path))
    print(str(audit_path))
    return [index_path, audit_path]


if __name__ == "__main__":
    main()
