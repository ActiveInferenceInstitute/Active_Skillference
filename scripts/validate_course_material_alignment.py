#!/usr/bin/env python3
"""Validate exported skills, local course materials, learning paths, and quizzes."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "src"))

from src.curriculum.alignment import (
    CourseAlignmentError,
    validate_course_material_alignment_files,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--project-path",
        default=str(_ROOT / "output" / "data" / "skilltree_project.json"),
        help="Path to the exported SkillTree project JSON.",
    )
    parser.add_argument(
        "--material-index-path",
        default=str(_ROOT / "output" / "data" / "course_material_index.json"),
        help="Path to the generated course-material index JSON.",
    )
    parser.add_argument(
        "--material-audit-path",
        default=str(_ROOT / "output" / "data" / "course_material_audit.json"),
        help="Path to the generated course-material audit JSON.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the full alignment report as JSON.",
    )
    args = parser.parse_args()

    try:
        report = validate_course_material_alignment_files(
            project_path=Path(args.project_path),
            material_index_path=Path(args.material_index_path),
            material_audit_path=Path(args.material_audit_path),
        )
    except CourseAlignmentError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    if not report.ok:
        for issue in report.issues:
            print(
                f"ERROR: {issue.code} at {issue.location}: {issue.message}",
                file=sys.stderr,
            )
        return 1

    summary = report.summary
    print(
        "course material alignment valid: "
        f"{summary['skills']} skills / "
        f"{summary['materialRecords']} material records / "
        f"{summary['quizzes']} quizzes / "
        f"{summary['externalPointers']} external pointers"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
