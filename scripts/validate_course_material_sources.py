#!/usr/bin/env python3
"""Validate commit-pinned external course-material source pointers."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "src"))

from src.curriculum.materials import (
    load_material_sources,
    validate_active_skillference_material_contract,
    validate_material_sources,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate course-material source pointer configuration."
    )
    parser.add_argument(
        "--source-config",
        type=Path,
        default=_ROOT / "data" / "course_material_sources.yaml",
        help="Path to the course-material source YAML file.",
    )
    parser.add_argument(
        "--online",
        action="store_true",
        help="Verify GitHub pinned commits, configured path globs, and pointer paths.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=10.0,
        help="Per-source GitHub request timeout in seconds for --online.",
    )
    args = parser.parse_args()

    payload = load_material_sources(args.source_config)
    issues = [
        *validate_material_sources(
            payload,
            online=args.online,
            timeout=args.timeout,
        ),
        *validate_active_skillference_material_contract(payload),
    ]
    if issues:
        for issue in issues:
            print(
                f"{issue.code}: {issue.location}: {issue.message}",
                file=sys.stderr,
            )
        return 1
    mode = "online" if args.online else "offline"
    print(f"course material sources valid ({mode})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
