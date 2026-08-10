#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "src"))

from src.integration.full_app_stack import (
    FullAppStackError,
    validate_full_app_stack,
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Strict local full-stack validation for SkillTree plus the learner dashboard."
    )
    parser.add_argument("--skilltree-url", default="http://localhost:8080")
    parser.add_argument("--dashboard-url", default="")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--state-dir", default=".active_skillference_local")
    parser.add_argument(
        "--proof-path",
        default="",
        help="write a redacted JSON proof artifact here (default: <state-dir>/full_app_stack_proof.json)",
    )
    parser.add_argument("--learner-id", default="local-learner")
    parser.add_argument(
        "--timeout",
        type=float,
        default=1200.0,
        help="seconds to wait for Docker, SkillTree, dashboard, and validation commands",
    )
    parser.add_argument(
        "--skip-regenerate",
        action="store_true",
        help="use existing output artifacts instead of rerunning build/kernels/export",
    )
    parser.add_argument(
        "--skip-browser",
        action="store_true",
        help="skip strict chrome-devtools-axi browser console proof",
    )
    parser.add_argument(
        "--app-ready",
        action="store_true",
        help=(
            "Run the fast local usability proof without requiring full live "
            "dependency parity. The JSON mode is app-ready, not full-parity."
        ),
    )
    parser.add_argument(
        "--keep-running",
        action="store_true",
        help="leave the dashboard server process running after validation succeeds",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        result = validate_full_app_stack(args)
    except FullAppStackError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
