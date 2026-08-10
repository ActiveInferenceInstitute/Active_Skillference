#!/usr/bin/env python3
"""Validate that the local dashboard is wired to a live SkillTree service."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "src"))

from src.dashboard.live_validation import (
    LiveSkillTreeDashboardError,
    validate_live_skilltree_dashboard,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dashboard-url", default="http://127.0.0.1:8765")
    parser.add_argument("--skilltree-url", default="http://localhost:8080")
    parser.add_argument("--project-root", default=str(_ROOT))
    parser.add_argument(
        "--local-state-dir",
        default="",
        help=(
            "Directory containing local SkillTree auth state. Defaults to the "
            "project-local state directory."
        ),
    )
    parser.add_argument("--timeout", type=float, default=5.0)
    parser.add_argument(
        "--no-token",
        action="store_true",
        help="Skip the dashboard trusted-client token exchange check.",
    )
    parser.add_argument(
        "--require-live-admin",
        action="store_true",
        help="Require a local-auth admin query proving live SkillTree skill count parity.",
    )
    parser.add_argument(
        "--require-live-dependencies",
        action="store_true",
        help="Require SkillTree's live dependency graph to exactly match the export.",
    )
    parser.add_argument(
        "--require-figure-contracts",
        action="store_true",
        help=(
            "Require figure registry rows, generated PNGs, dashboard artifacts, and "
            "structured chart-contract fields to agree."
        ),
    )
    args = parser.parse_args()

    try:
        project_root = Path(args.project_root)
        local_state_dir = Path(args.local_state_dir) if args.local_state_dir else None
        result = validate_live_skilltree_dashboard(
            dashboard_url=args.dashboard_url,
            skilltree_url=args.skilltree_url,
            project_root=project_root,
            local_state_dir=local_state_dir,
            timeout=args.timeout,
            require_token=not args.no_token,
            require_live_admin=args.require_live_admin,
            require_live_dependencies=args.require_live_dependencies,
            require_figure_contracts=args.require_figure_contracts,
        )
    except LiveSkillTreeDashboardError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
