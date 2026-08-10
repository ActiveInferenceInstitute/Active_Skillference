#!/usr/bin/env python3
"""Validate manuscript scientific claim-support anchors."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "src"))

from src.kernels.examples import build_claim_registry
from src.manuscript.claim_support import (
    validate_claim_support,
    write_claim_support_audit,
)
from src.project_paths import project_output_dirs


def main() -> Path:
    manuscript_dir = _ROOT / "manuscript"
    audit = validate_claim_support(
        manuscript_dir=manuscript_dir,
        support_path=_ROOT / "data" / "manuscript_claim_support.yaml",
        source_matrix_path=_ROOT / "data" / "scholarship_sources.yaml",
        bib_path=manuscript_dir / "references.bib",
        registry_claim_ids=build_claim_registry().names(),
        project_root=_ROOT,
    )
    path = write_claim_support_audit(
        audit,
        project_output_dirs()["data"] / "manuscript_claim_support.json",
    )
    print(
        "validated manuscript claim support: "
        f"{audit.to_dict()['summary']['claimRows']} claims"
    )
    print(path)
    return path


if __name__ == "__main__":
    main()
