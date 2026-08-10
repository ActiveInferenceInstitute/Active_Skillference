#!/usr/bin/env python3
"""Bootstrap local SkillTree FORM auth and seed Active Skillference.

This is a thin orchestrator. It creates/reuses one local root account, seeds the
project through SkillTree's own admin API, stores the project trusted-client
secret in an ignored local state directory, and verifies a proxy token for the
local learner identity.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "src"))

from src.curriculum.catalog import build_curriculum
from src.kernels.examples import build_claim_registry
from src.project_identity import (
    SKILLTREE_PROJECT_ID,
    SKILLTREE_PROJECT_NAME,
)
from src.provenance.binding import render_graph, validate_curriculum
from src.skilltree import export_project
from src.skilltree.client import SkillTreeClientError
from src.skilltree.local_auth import (
    DEFAULT_LOCAL_LEARNER_ID,
    DEFAULT_LOCAL_STATE_DIR,
    LocalSkillTreeAuthError,
    describe_local_auth,
    ensure_local_skilltree_auth,
    is_browser_login_compatible_username,
    load_local_state,
    local_state_path,
)

PROJECT_ID = SKILLTREE_PROJECT_ID
PROJECT_NAME = SKILLTREE_PROJECT_NAME


def build_project():  # type: ignore[no-untyped-def]
    """Build the provenance-rendered SkillTree project (no network)."""
    graph = build_curriculum()
    registry = build_claim_registry()
    validate_curriculum(graph.skills, registry)
    rendered = render_graph(graph, registry)
    return export_project(rendered, PROJECT_ID, PROJECT_NAME)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base-url", default=os.environ.get("SKILLTREE_URL", "http://localhost:8080")
    )
    parser.add_argument(
        "--state-dir",
        default=os.environ.get(
            "ACTIVE_SKILLFERENCE_LOCAL_STATE_DIR", DEFAULT_LOCAL_STATE_DIR
        ),
    )
    parser.add_argument(
        "--learner-id",
        default=os.environ.get(
            "ACTIVE_SKILLFERENCE_LEARNER_ID", DEFAULT_LOCAL_LEARNER_ID
        ),
    )
    parser.add_argument("--project-id", default=PROJECT_ID)
    parser.add_argument("--project-name", default=PROJECT_NAME)
    parser.add_argument(
        "--no-seed",
        action="store_true",
        help="Bootstrap/auth-check only; do not seed the exported curriculum.",
    )
    parser.add_argument(
        "--skip-dependencies",
        action="store_true",
        help=(
            "Seed project/subjects/quizzes/skills but leave prerequisite edges for "
            "scripts/reconcile_live_dependencies.py."
        ),
    )
    parser.add_argument(
        "--skip-seed-if-live-counts-ready",
        action="store_true",
        help=(
            "After login, skip idempotent core seeding when live SkillTree already "
            "reports the exported subject and skill counts."
        ),
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Print browser-safe local auth readiness and exit without network calls.",
    )
    parser.add_argument(
        "--show-local-credentials",
        action="store_true",
        help=(
            "Print the current ignored local SkillTree username/password from "
            "the state file. Does not print trusted-client secrets."
        ),
    )
    args = parser.parse_args()

    state_dir = Path(args.state_dir)
    if not state_dir.is_absolute():
        state_dir = _ROOT / state_dir

    if args.show_local_credentials:
        try:
            state = load_local_state(state_dir)
        except LocalSkillTreeAuthError as exc:
            print(f"ERROR: cannot read local credentials: {exc}", file=sys.stderr)
            return 1
        if state is None:
            print(
                "ERROR: local SkillTree credentials are missing at "
                f"{local_state_path(state_dir)}",
                file=sys.stderr,
            )
            return 1
        print(
            "WARNING: local development credentials only; do not use these defaults "
            "for shared or deployed SkillTree instances.",
            file=sys.stderr,
        )
        browser_login_usable = is_browser_login_compatible_username(
            state.admin_username
        )
        if not browser_login_usable:
            print(
                "WARNING: the stored local username is non-email-shaped. "
                "SkillTree's browser login field rejects that shape; run "
                "`uv run python scripts/reset_local_skilltree.py --confirm-local-reset` "
                "to recreate the local Docker volume with the documented default "
                "email login.",
                file=sys.stderr,
            )
        print(
            json.dumps(
                {
                    "adminUsername": state.admin_username,
                    "adminPassword": state.admin_password,
                    "browserLoginUsable": browser_login_usable,
                    "learnerId": state.learner_id,
                    "projectId": state.project_id,
                    "skilltreeUrl": state.skilltree_url,
                    "statePath": str(local_state_path(state_dir)),
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0

    if args.check:
        print(
            json.dumps(
                describe_local_auth(
                    enabled=True,
                    state_dir=state_dir,
                    learner_id=args.learner_id,
                    project_id=args.project_id,
                ).to_public_dict(),
                indent=2,
                sort_keys=True,
            )
        )
        return 0

    project = None if args.no_seed else build_project()
    try:
        result = ensure_local_skilltree_auth(
            base_url=args.base_url,
            project_id=args.project_id,
            state_dir=state_dir,
            learner_id=args.learner_id,
            project=project,
            seed_project=not args.no_seed,
            seed_dependencies=not args.skip_dependencies,
            skip_seed_if_live_counts_ready=args.skip_seed_if_live_counts_ready,
            verify_token=True,
        )
    except (LocalSkillTreeAuthError, SkillTreeClientError) as exc:
        print(f"ERROR: local SkillTree bootstrap failed: {exc}", file=sys.stderr)
        if isinstance(exc, SkillTreeClientError) and exc.body:
            print(f"SkillTree response body: {exc.body[:500]}", file=sys.stderr)
        return 1

    print(json.dumps(result.to_public_dict(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
