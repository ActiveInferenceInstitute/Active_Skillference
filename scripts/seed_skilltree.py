#!/usr/bin/env python3
"""Seed a live SkillTree instance with the Active Inference curriculum.

Usage:
    uv run python scripts/seed_skilltree.py --base-url http://localhost:8080 [--token TOKEN]

Thin orchestrator: builds + provenance-renders the curriculum, exports the SkillTree
project, then drives ``src.skilltree.seed`` to create it over REST in dependency-safe
order. During generic render/analysis runs, exits successfully with a skip message when
no SkillTree server is listening. Use ``--require-live`` for strict live bring-up.
"""

from __future__ import annotations

import argparse
import os
import socket
import sys
from pathlib import Path
from urllib.parse import urlparse

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
from src.skilltree import (
    SkillTreeClient,
    SkillTreeClientError,
    export_project,
    seed,
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


def _server_accepts_connections(base_url: str, timeout: float = 1.0) -> bool:
    parsed = urlparse(base_url)
    if parsed.hostname is None:
        return False
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    try:
        with socket.create_connection((parsed.hostname, port), timeout=timeout):
            return True
    except OSError:
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://localhost:8080")
    parser.add_argument(
        "--token",
        default=os.environ.get("SKILLTREE_TOKEN"),
        help="Bearer token for SkillTree admin endpoints; defaults to SKILLTREE_TOKEN.",
    )
    parser.add_argument(
        "--require-live",
        action="store_true",
        help="Fail instead of skipping when the SkillTree service is unreachable.",
    )
    args = parser.parse_args()

    project = build_project()
    if not _server_accepts_connections(args.base_url):
        message = (
            f"live SkillTree seed skipped: no service is accepting connections at "
            f"{args.base_url}"
        )
        if args.require_live:
            print(f"ERROR: {message}", file=sys.stderr)
            return 1
        print(message)
        return 0

    client = SkillTreeClient(args.base_url, PROJECT_ID, token=args.token)
    try:
        summary = seed(client, project)
    except SkillTreeClientError as exc:
        if exc.status in {401, 403}:
            print(
                "ERROR: live SkillTree seed requires admin authentication. "
                "Provide a valid bearer token with --token or SKILLTREE_TOKEN; "
                "the local learner dashboard deliberately does not implement login.",
                file=sys.stderr,
            )
        else:
            print(f"ERROR: live SkillTree seed failed: {exc}", file=sys.stderr)
        if exc.body:
            print(f"SkillTree response body: {exc.body[:500]}", file=sys.stderr)
        return 1
    print(f"seeded SkillTree @ {args.base_url}: {summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
