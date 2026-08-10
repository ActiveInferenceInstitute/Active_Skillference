#!/usr/bin/env python3
"""Fail if authored repo surfaces hard-code stale generated counts."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "src"))

from src.live_counts import LiveCountError, audit_live_count_literals


def main() -> int:
    try:
        issues = audit_live_count_literals(_ROOT)
    except LiveCountError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    if issues:
        print("stale live-count literals found:", file=sys.stderr)
        for issue in issues:
            print(f"  {issue}", file=sys.stderr)
        return 1
    print("live-count audit clean")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
