#!/usr/bin/env python3
"""Validate math-rendering support on generated web and dashboard surfaces."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from src.manuscript.web_math import (
    html_has_math,
    html_has_mathjax,
    html_has_secure_mathjax,
)

WEB = ROOT / "output" / "web"
DASHBOARD_INDEX = ROOT / "src" / "dashboard" / "assets" / "index.html"
DASHBOARD_APP = ROOT / "src" / "dashboard" / "assets" / "app.js"


def _issues() -> list[str]:
    issues: list[str] = []
    if not DASHBOARD_INDEX.is_file():
        issues.append(f"missing dashboard index: {DASHBOARD_INDEX.relative_to(ROOT)}")
    else:
        index = DASHBOARD_INDEX.read_text(encoding="utf-8")
        if not html_has_mathjax(index):
            issues.append("dashboard index does not load MathJax")
        if not html_has_secure_mathjax(index):
            issues.append("dashboard index MathJax lacks pinned SRI metadata")
    if not DASHBOARD_APP.is_file():
        issues.append(f"missing dashboard app: {DASHBOARD_APP.relative_to(ROOT)}")
    else:
        app = DASHBOARD_APP.read_text(encoding="utf-8")
        for required in ("renderRichText", "typesetMath", "MathJax.typesetPromise"):
            if required not in app:
                issues.append(f"dashboard app missing {required}")

    if not WEB.is_dir():
        issues.append("output/web is missing; render the manuscript web output first")
        return issues
    if not (WEB / "index.html").is_file():
        issues.append(
            "output/web/index.html is missing; render the combined manuscript web output first"
        )
    html_files = sorted(WEB.glob("*.html"))
    if not html_files:
        issues.append("output/web contains no HTML files")
        return issues
    for path in html_files:
        text = path.read_text(encoding="utf-8")
        if html_has_math(text) and not html_has_mathjax(text):
            issues.append(f"{path.relative_to(ROOT)} contains math but lacks MathJax")
        if html_has_math(text) and not html_has_secure_mathjax(text):
            issues.append(f"{path.relative_to(ROOT)} MathJax lacks pinned SRI metadata")
    return issues


def main() -> int:
    issues = _issues()
    if issues:
        print("web math validation failed:", file=sys.stderr)
        for issue in issues:
            print(f"  {issue}", file=sys.stderr)
        return 1
    print("web math validation clean: dashboard and rendered HTML expose MathJax")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
