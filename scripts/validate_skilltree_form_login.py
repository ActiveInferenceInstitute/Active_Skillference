#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from urllib.parse import urlparse

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "src"))

from src.skilltree import form_login_validation as _form_login_validation
from src.skilltree.form_login_validation import (
    LOGOUT_JS,
    PAGE_PROBE_JS,
    UI_LOGOUT_JS,
    SkillTreeFormLoginError,
    _safe_command,
    admin_surface_visible,
    browser_eval,
    build_login_url,
    force_browser_logout,
    login_submission_js,
    one_shot_secret_url,
    parse_axi_result,
    probe_page,
    public_state_summary,
    redact,
    run_browser_command,
    validate_form_login,
    wait_for_login_form,
)
from src.skilltree.local_auth import DEFAULT_LOCAL_STATE_DIR

subprocess = _form_login_validation.subprocess

__all__ = [
    "LOGOUT_JS",
    "PAGE_PROBE_JS",
    "UI_LOGOUT_JS",
    "SkillTreeFormLoginError",
    "_safe_command",
    "admin_surface_visible",
    "browser_eval",
    "build_login_url",
    "force_browser_logout",
    "login_submission_js",
    "one_shot_secret_url",
    "parse_axi_result",
    "probe_page",
    "public_state_summary",
    "redact",
    "run_browser_command",
    "subprocess",
    "validate_form_login",
    "wait_for_login_form",
]


def resolve_state_dir(value: str) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = _ROOT / path
    return path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skilltree-url", default="http://localhost:8080")
    parser.add_argument("--state-dir", default=DEFAULT_LOCAL_STATE_DIR)
    parser.add_argument("--project-id", default="activeInference")
    parser.add_argument("--browser-command", default="chrome-devtools-axi")
    parser.add_argument("--timeout", type=float, default=60.0)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    state_dir = resolve_state_dir(args.state_dir)
    try:
        result = validate_form_login(
            skilltree_url=args.skilltree_url,
            state_dir=state_dir,
            project_id=args.project_id,
            browser_command=args.browser_command,
            timeout=args.timeout,
        )
    except SkillTreeFormLoginError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    parsed_url = urlparse(str(result.get("finalUrl", "")))
    if parsed_url.username or parsed_url.password:
        print("ERROR: final URL unexpectedly contains credentials", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
