#!/usr/bin/env python3
"""Capture learner-dashboard evidence screenshots from a running local stack.

Unlike the deterministic figures, these images cannot be rebuilt from project
data, so they are version-controlled under ``manuscript/assets/screenshots/``
and refreshed only by running this script against a live dashboard. It requires
a running SkillTree stack, a running dashboard, and the browser automation CLI.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "src"))

from src.figures.registry import CAPTURED_ASSET_ROOT
from src.screenshots.capture import (
    DEFAULT_BROWSER_COMMAND,
    CaptureSettings,
    ScreenshotCaptureError,
    capture_screenshots,
)
from src.screenshots.manifest import VIEWPORT_HEIGHT, VIEWPORT_WIDTH


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dashboard-url", default="http://127.0.0.1:8765")
    parser.add_argument(
        "--output-dir",
        default=str(_ROOT / CAPTURED_ASSET_ROOT),
        help="tracked directory receiving the captured PNGs and provenance record",
    )
    parser.add_argument("--browser-command", default=DEFAULT_BROWSER_COMMAND)
    parser.add_argument("--viewport-width", type=int, default=VIEWPORT_WIDTH)
    parser.add_argument("--viewport-height", type=int, default=VIEWPORT_HEIGHT)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    settings = CaptureSettings(
        dashboard_url=args.dashboard_url.rstrip("/"),
        output_dir=Path(args.output_dir),
        project_root=_ROOT,
        browser_command=args.browser_command,
        viewport_width=args.viewport_width,
        viewport_height=args.viewport_height,
    )
    try:
        provenance = capture_screenshots(settings)
    except ScreenshotCaptureError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(provenance, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
