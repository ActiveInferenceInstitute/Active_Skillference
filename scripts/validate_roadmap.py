#!/usr/bin/env python3
"""Validate tasks.yaml and the generated TODO roadmap surface."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "src"))

from src.roadmap import (
    RoadmapError,
    validate_roadmap,
    write_todo_surfaces,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--write-todo",
        action="store_true",
        help="rewrite TODO.md and docs/todo/*.md from tasks.yaml before validating",
    )
    args = parser.parse_args()
    if args.write_todo:
        write_todo_surfaces(_ROOT)
    try:
        validate_roadmap(_ROOT)
    except RoadmapError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print("roadmap validation clean")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
