#!/usr/bin/env python3
"""Fail if authored manuscript prose uses British spelling variants."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "src"))

from src.manuscript.american_english import audit_american_english


def main() -> int:
    issues = audit_american_english(_ROOT / "manuscript")
    if issues:
        print("British spelling variants found in manuscript prose:", file=sys.stderr)
        for issue in issues:
            print(f"  {issue}", file=sys.stderr)
        return 1
    print("American English audit clean")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
