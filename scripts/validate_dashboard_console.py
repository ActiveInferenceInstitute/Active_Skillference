#!/usr/bin/env python3
"""Opt-in browser smoke gate: fail on unexpected dashboard console errors.

The server-side dashboard tests cannot see what the learner's browser logs. This gate
drives a real browser (chrome-devtools-axi) against a running dashboard and fails if any
console error appears EXCEPT the one known, cosmetic upstream probe: the
``@skilltree/skills-client-js`` SDK checks service status against SkillTree's built-in
default ``Inception`` project, which returns 401 under our project-scoped authenticator.
That probe is non-blocking (the real ``activeInference`` learner view still renders) and
is not fixable from our configuration, so it is allow-listed and everything else fails.

Requires a running dashboard and the ``chrome-devtools-axi`` CLI. By default, if either
is absent the gate reports ``skipped`` (not ``clean``) and exits 0, matching the project
convention that optional local browser tooling must not break offline checks. Strict
callers can pass ``--require-browser`` and ``--require-dashboard`` to fail closed.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import time
import urllib.error
import urllib.request
from urllib.parse import urlparse

# Console errors that are known, cosmetic, and outside our control are allow-listed here.
_ALLOWED_ERROR_PATTERNS = (
    re.compile(r"projects/Inception/.*token.*401", re.IGNORECASE),
    re.compile(r"Unable to authenticate.*Inception", re.IGNORECASE),
)

# This script deliberately stays import-free from the project's src/ package (no
# sys.path bootstrap), so the http(s)-only guard is inlined rather than shared via
# src.net_guard; keep both checks in sync (see also src/net_guard.py).
_ALLOWED_URL_SCHEMES = frozenset({"http", "https"})


def _dashboard_reachable(url: str, timeout: float) -> bool:
    if urlparse(url).scheme not in _ALLOWED_URL_SCHEMES:
        return False
    try:
        # The scheme check above rejects non-http(s) targets.
        with urllib.request.urlopen(url, timeout=timeout) as response:  # nosec B310
            return 200 <= response.status < 500
    except (urllib.error.URLError, OSError):
        return False


def _console_errors(url: str, settle_seconds: float) -> list[str]:
    subprocess.run(
        ["chrome-devtools-axi", "open", url],
        check=True,
        capture_output=True,
        text=True,
        timeout=60,
    )
    time.sleep(settle_seconds)
    result = subprocess.run(
        ["chrome-devtools-axi", "console", "--type", "error"],
        check=True,
        capture_output=True,
        text=True,
        timeout=60,
    )
    errors: list[str] = []
    for line in result.stdout.splitlines():
        if "[error]" in line:
            errors.append(line.strip())
    return errors


def unexpected_errors(errors: list[str]) -> list[str]:
    """Return console errors that are not on the cosmetic-upstream allow-list."""
    return [
        error
        for error in errors
        if not any(pattern.search(error) for pattern in _ALLOWED_ERROR_PATTERNS)
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dashboard-url", default="http://127.0.0.1:8765/")
    parser.add_argument("--settle-seconds", type=float, default=5.0)
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

    errors = _console_errors(args.dashboard_url, args.settle_seconds)
    unexpected = unexpected_errors(errors)
    if unexpected:
        print("dashboard console gate FAILED — unexpected console errors:")
        for error in unexpected:
            print(f"  - {error}")
        return 1
    allowed = len(errors) - len(unexpected)
    print(
        f"dashboard console gate OK (no unexpected errors; {allowed} known "
        "upstream Inception probe message(s) allow-listed)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
