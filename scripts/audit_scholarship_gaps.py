#!/usr/bin/env python3
"""Validate and write the scholarship frontier gap report."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "src"))

from src.kernels.examples import build_claim_registry
from src.manuscript.claim_support import validate_claim_support
from src.project_paths import project_output_dirs
from src.scholarship.coverage import validate_scholarship
from src.scholarship.gap_report import (
    ScholarshipGapError,
    validate_scholarship_gaps,
    write_scholarship_gap_report,
)


def main() -> int:
    manuscript_dir = _ROOT / "manuscript"
    bib_path = manuscript_dir / "references.bib"
    matrix_path = _ROOT / "data" / "scholarship_sources.yaml"
    scholarship = validate_scholarship(manuscript_dir, matrix_path, bib_path)
    registry = build_claim_registry()
    claim_support = validate_claim_support(
        manuscript_dir=manuscript_dir,
        support_path=_ROOT / "data" / "manuscript_claim_support.yaml",
        source_matrix_path=matrix_path,
        bib_path=bib_path,
        registry_claim_ids=registry.names(),
        project_root=_ROOT,
    )
    try:
        report = validate_scholarship_gaps(scholarship, claim_support, bib_path)
    except ScholarshipGapError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    out = write_scholarship_gap_report(
        report,
        project_output_dirs()["data"] / "scholarship_gap_report.json",
    )
    print(
        "scholarship gap report valid: "
        f"{report.to_dict()['summary']['frontierSources']} frontier sources"
    )
    print(str(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
