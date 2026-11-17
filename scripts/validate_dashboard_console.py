#!/usr/bin/env python3
"""Opt-in real-browser proof of official project, subject and quiz views.

The gate waits for the official SDK's actual route callback, a visible frame
on the configured SkillTree origin, and matching browser-visible content.
Fallback and unresolved pending states fail even when the console is empty.
Only the established cosmetic upstream Inception probe is allow-listed.
Absent tooling/dashboard remains an explicit optional skip unless required.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

_ALLOWED_URL_SCHEMES = frozenset({"http", "https"})

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

from src.dashboard.browser_validation import (
    BrowserDisplayError,
    validate_dashboard_browser,
)


def _dashboard_reachable(url: str, timeout: float) -> bool:
    if urlparse(url).scheme not in _ALLOWED_URL_SCHEMES:
        return False
    try:
        # The scheme check above rejects non-http(s) targets.
        with urllib.request.urlopen(url, timeout=timeout) as response:  # nosec B310
            return 200 <= response.status < 500
    except (urllib.error.URLError, OSError):
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dashboard-url", default="http://127.0.0.1:8765/")
    parser.add_argument("--settle-seconds", type=float, default=5.0)
    parser.add_argument("--timeout", type=float, default=45.0)
    parser.add_argument(
        "--json", action="store_true", help="Emit the structured browser proof."
    )
    parser.add_argument(
        "--require-browser",
        action="store_true",
        help="Fail instead of skipping when chrome-devtools-axi is unavailable.",
    )
    parser.add_argument(
        "--require-dashboard",
        action="store_true",
        help="Fail instead of skipping when the dashboard URL is unavailable.",
    )
    args = parser.parse_args()

    if shutil.which("chrome-devtools-axi") is None:
        message = "dashboard console gate: skipped (chrome-devtools-axi not installed)"
        if args.require_browser:
            print(message.replace("skipped", "FAILED"))
            return 1
        print(message)
        return 0
    if not _dashboard_reachable(args.dashboard_url, timeout=5.0):
        message = (
            f"dashboard console gate: skipped (no dashboard at {args.dashboard_url})"
        )
        if args.require_dashboard:
            print(message.replace("skipped", "FAILED"))
            return 1
        print(message)
        return 0

    try:
        summary = validate_dashboard_browser(
            args.dashboard_url,
            timeout=args.timeout,
            settle_seconds=args.settle_seconds,
        )
    except BrowserDisplayError as exc:
        if args.json:
            print(json.dumps({"ok": False, "checked": False, "error": str(exc)}))
        else:
            print(f"dashboard console gate FAILED: {exc}")
        return 1
    if args.json:
        print(json.dumps(summary, sort_keys=True))
    else:
        print(
            "dashboard console gate OK (official project, subject and quiz views ready)"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
