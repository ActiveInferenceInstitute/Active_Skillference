#!/usr/bin/env python3
# ruff: noqa: N999 - intentional script filename (00_preflight); invoked as a script, never imported.
"""Pre-flight check for manuscript rendering prerequisites."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT))

from infrastructure.rendering.preflight import run_manuscript_preflight


def main() -> int:
    manuscript_dir = Path(__file__).resolve().parent.parent / "manuscript"
    ok, message = run_manuscript_preflight(manuscript_dir)
    if ok:
        return 0
    sys.stderr.write(message)
    return 1


if __name__ == "__main__":
    sys.exit(main())
