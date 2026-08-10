#!/usr/bin/env python3
"""Validate scholarship source locator health."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "src"))

from src.project_paths import project_output_dirs
from src.scholarship.source_health import (
    SourceHealthError,
    validate_source_health,
    write_source_health_audit,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--online",
        action="store_true",
        help="also attempt DOI/URL reachability checks and record statuses",
    )
    parser.add_argument(
        "--strict-online",
        action="store_true",
        help="fail on hard online reachability errors while tolerating 403 and timeout",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=15.0,
        help="per-locator network timeout for online checks (default: 15 seconds)",
    )
    args = parser.parse_args()
    if args.strict_online and not args.online:
        parser.error("--strict-online requires --online")
    try:
        if args.online:
            audit = validate_source_health(
                _ROOT / "data" / "scholarship_sources.yaml",
                _ROOT / "manuscript" / "references.bib",
                online=True,
                strict_online=args.strict_online,
                timeout=args.timeout,
            )
        else:
            audit = validate_source_health(
                _ROOT / "data" / "scholarship_sources.yaml",
                _ROOT / "manuscript" / "references.bib",
                online=False,
            )
    except SourceHealthError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    out = write_source_health_audit(
        audit,
        project_output_dirs()["data"] / "scholarship_source_health.json",
    )
    print(
        "scholarship source-health valid: "
        f"{audit.source_count} sources, online={audit.checked_online}"
    )
    print(str(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
