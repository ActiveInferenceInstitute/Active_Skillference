#!/usr/bin/env python3
"""Reconcile live SkillTree prerequisite edges against the exported project JSON."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "src"))

from src.skilltree.client import SkillTreeClientError
from src.skilltree.dependency_reconciler import (
    DependencyReconciliationError,
    DependencyReconciliationSummary,
    load_exported_dependencies,
    reconcile_live_dependencies,
    refresh_reconciliation_progress,
)
from src.skilltree.local_auth import (
    DEFAULT_LOCAL_STATE_DIR,
    LocalSkillTreeAuthError,
    SkillTreeSessionClient,
    default_local_request_timeout,
    load_local_state,
    local_state_path,
)


def _resolve(path: str) -> Path:
    value = Path(path)
    return value if value.is_absolute() else _ROOT / value


def _progress_line(summary: DependencyReconciliationSummary) -> None:
    print(
        "dependency reconciliation: "
        f"attempted={summary.attempted}, "
        f"matched={summary.matched_dependencies_after}/"
        f"{summary.expected_dependencies}, "
        f"missing={summary.missing_after}, extra={summary.extra_after}, "
        f"stopped={summary.stopped_reason or 'no'}",
        file=sys.stderr,
        flush=True,
    )


def _heartbeat_line(event: dict[str, object]) -> None:
    print(
        "dependency heartbeat: "
        f"phase={event.get('phase')}, "
        f"edge={event.get('skillId')}->{event.get('dependsOnSkillId')}, "
        f"attempted={event.get('attempted')}, "
        f"matched={event.get('matchedDependencies')}, "
        f"missing={event.get('missingDependencies')}, "
        f"elapsed={event.get('elapsedSeconds')}s",
        file=sys.stderr,
        flush=True,
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skilltree-url", default="http://localhost:8080")
    parser.add_argument(
        "--project-path",
        default=str(_ROOT / "output" / "data" / "skilltree_project.json"),
    )
    parser.add_argument("--state-dir", default=DEFAULT_LOCAL_STATE_DIR)
    parser.add_argument(
        "--progress-path",
        default=str(_ROOT / DEFAULT_LOCAL_STATE_DIR / "dependency_seed_progress.json"),
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=default_local_request_timeout(),
        help="SkillTree request timeout in seconds.",
    )
    parser.add_argument(
        "--poll-after-timeout",
        type=float,
        default=120.0,
        help="seconds to poll the live graph after a dependency POST timeout",
    )
    parser.add_argument(
        "--poll-interval",
        type=float,
        default=5.0,
        help="seconds between post-timeout graph polls",
    )
    parser.add_argument(
        "--attempts-per-edge",
        type=int,
        default=2,
        help=(
            "how many times one edge may be posted before the run fails; a slow "
            "emulated-Docker write can exceed the client timeout and succeed on "
            "the next attempt (use 1 to fail on the first error)"
        ),
    )
    parser.add_argument(
        "--max-edges",
        type=int,
        default=None,
        help="optional cap for chunked local reconciliation runs",
    )
    parser.add_argument(
        "--max-runtime-seconds",
        type=float,
        default=None,
        help="optional wall-clock cap for chunked local reconciliation runs",
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="refresh/report live dependency parity without writing missing edges",
    )
    parser.add_argument(
        "--quiet-progress",
        action="store_true",
        help=(
            "suppress progress and heartbeat lines on stderr; final JSON still "
            "prints to stdout"
        ),
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    project_path = _resolve(args.project_path)
    state_dir = _resolve(args.state_dir)
    progress_path = _resolve(args.progress_path)
    try:
        exported = load_exported_dependencies(project_path)
        state = load_local_state(state_dir)
        if state is None:
            raise DependencyReconciliationError(
                f"local SkillTree auth state not found at {local_state_path(state_dir)}"
            )
        if state.project_id != exported.project_id:
            raise DependencyReconciliationError(
                f"local SkillTree state project {state.project_id!r} does not match "
                f"export project {exported.project_id!r}"
            )
        if state.skilltree_url and state.skilltree_url.rstrip(
            "/"
        ) != args.skilltree_url.rstrip("/"):
            raise DependencyReconciliationError(
                "local SkillTree state URL does not match --skilltree-url"
            )
        client = SkillTreeSessionClient(
            args.skilltree_url,
            exported.project_id,
            timeout=max(args.timeout, 30.0),
        )
        client.login(state.admin_username, state.admin_password)
        progress_callback = None if args.quiet_progress else _progress_line
        if args.check_only:
            summary = refresh_reconciliation_progress(
                client=client,
                project_id=exported.project_id,
                dependencies=exported.dependencies,
                progress_path=progress_path,
                progress_callback=progress_callback,
            )
        else:
            summary = reconcile_live_dependencies(
                client=client,
                project_id=exported.project_id,
                dependencies=exported.dependencies,
                progress_path=progress_path,
                max_edges=args.max_edges,
                max_runtime_seconds=args.max_runtime_seconds,
                poll_after_timeout=args.poll_after_timeout,
                poll_interval=args.poll_interval,
                attempts_per_edge=args.attempts_per_edge,
                progress_callback=progress_callback,
                heartbeat_callback=None if args.quiet_progress else _heartbeat_line,
            )
    except (
        DependencyReconciliationError,
        LocalSkillTreeAuthError,
        SkillTreeClientError,
    ) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    result = {
        "ok": summary.complete,
        "projectId": exported.project_id,
        "progressPath": str(progress_path),
        **summary.to_dict(),
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    if args.check_only:
        return 0
    if summary.stopped_reason == "interrupted":
        return 130
    return 0 if summary.complete else 1


if __name__ == "__main__":
    raise SystemExit(main())
