#!/usr/bin/env python3
"""Validate that every Docker Compose image reference is pinned by digest."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_IMAGE_RE = re.compile(r"^\s*image:\s*(?P<image>[^#\n]+?)\s*(?:#.*)?$")
_DIGEST_RE = re.compile(r"@sha256:[0-9a-f]{64}$")


def image_lines_without_digest(text: str) -> list[str]:
    """Return Compose image references that are missing a valid sha256 digest pin."""
    missing: list[str] = []
    for line in text.splitlines():
        match = _IMAGE_RE.match(line)
        if match is None:
            continue
        image = match.group("image").strip().strip("\"'")
        if not _DIGEST_RE.search(image):
            missing.append(image)
    return missing


def main() -> int:
    """Validate the target Compose file and exit non-zero on mutable image tags."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--file",
        type=Path,
        default=_ROOT / "docker-compose.yml",
        help="compose file to validate (default: repo docker-compose.yml)",
    )
    args = parser.parse_args()

    missing = image_lines_without_digest(args.file.read_text(encoding="utf-8"))
    if missing:
        print(
            "docker image references missing sha256 digests: " + ", ".join(missing),
            file=sys.stderr,
        )
        return 1

    print(f"docker image digest pins valid: {args.file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
