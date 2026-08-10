#!/usr/bin/env python3
"""Serve the local Active Skillference learner dashboard."""

from __future__ import annotations

import argparse
import json
import os
import socket
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "src"))

from src.dashboard import make_dashboard_config, run_dashboard_server
from src.dashboard.server import dashboard_payload
from src.skilltree.local_auth import (
    DEFAULT_LOCAL_LEARNER_ID,
    DEFAULT_LOCAL_STATE_DIR,
)


def _env_flag(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skilltree-url", default="http://localhost:8080")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument(
        "--authenticator",
        default=os.environ.get("SKILLTREE_AUTHENTICATOR", ""),
        help=(
            "SkillTree client authenticator. Leave empty for the no-login local shell; "
            "set to pki or a trusted-client token endpoint only when that auth mode is configured."
        ),
    )
    parser.set_defaults(
        local_auth_enabled=_env_flag("ACTIVE_SKILLFERENCE_LOCAL_AUTH", False)
    )
    parser.add_argument(
        "--local-auth",
        dest="local_auth_enabled",
        action="store_true",
        help="Use the local trusted-client token endpoint when bootstrapped.",
    )
    parser.add_argument(
        "--no-local-auth",
        dest="local_auth_enabled",
        action="store_false",
        help="Disable the local trusted-client token endpoint.",
    )
    parser.add_argument(
        "--local-state-dir",
        default=os.environ.get(
            "ACTIVE_SKILLFERENCE_LOCAL_STATE_DIR", DEFAULT_LOCAL_STATE_DIR
        ),
        help="Directory containing ignored local SkillTree bootstrap credentials.",
    )
    parser.add_argument(
        "--learner-id",
        default=os.environ.get(
            "ACTIVE_SKILLFERENCE_LEARNER_ID", DEFAULT_LOCAL_LEARNER_ID
        ),
        help="Local learner identity proxied through SkillTree.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Print dashboard status JSON and exit without starting the server.",
    )
    args = parser.parse_args()

    config = make_dashboard_config(
        project_root=_ROOT,
        skilltree_url=args.skilltree_url,
        host=args.host,
        port=args.port,
        authenticator=args.authenticator,
        local_auth_enabled=args.local_auth_enabled,
        local_state_dir=Path(args.local_state_dir),
        learner_id=args.learner_id,
    )
    if args.check:
        print(json.dumps(dashboard_payload(config), indent=2, sort_keys=True))
        return 0
    try:
        run_dashboard_server(config)
    except OSError as exc:
        if exc.errno in {48, 98, 10048}:
            print(
                f"ERROR: cannot bind learner dashboard to {config.dashboard_url}; "
                "the port is already in use.",
                file=sys.stderr,
            )
            return 1
        raise
    except socket.gaierror as exc:
        print(f"ERROR: invalid dashboard host {config.host!r}: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
