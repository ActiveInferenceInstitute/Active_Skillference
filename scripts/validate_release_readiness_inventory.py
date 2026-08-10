#!/usr/bin/env python3
"""Validate or refresh the release-readiness inventory."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "src"))

from src.release_readiness import (
    ReleaseReadinessError,
    validate_release_readiness_inventory,
    write_release_readiness_inventory,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--write",
        action="store_true",
        help="rewrite docs/release_readiness_inventory.md from current git state",
    )
    args = parser.parse_args()
    try:
        if args.write:
            write_release_readiness_inventory(_ROOT)
        validate_release_readiness_inventory(_ROOT)
    except ReleaseReadinessError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print("release readiness inventory valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
