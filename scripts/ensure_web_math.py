#!/usr/bin/env python3
"""Insert MathJax into rendered web HTML files that contain math."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from src.manuscript.web_math import ensure_mathjax_in_web_dir


def main() -> int:
    web_dir = ROOT / "output" / "web"
    try:
        changed = ensure_mathjax_in_web_dir(web_dir)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    if changed:
        print(f"inserted MathJax into {len(changed)} rendered HTML files")
        for path in changed:
            print(path)
    else:
        print("rendered HTML MathJax already current")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
