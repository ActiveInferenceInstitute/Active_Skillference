#!/usr/bin/env python3
"""Fail on a relative Markdown link or image that does not resolve on disk.

The documentation surface is a gate, not prose: a relative link that points at a
renamed file silently misdirects every reader after the rename. This check walks
the authored Markdown in the repository, strips fenced and inline code so shell
examples are not parsed as links, and verifies that every relative target exists.

Anchor-only targets (``#section``) need no file, and fragment suffixes
(``other.md#section``) are checked for the file only — heading anchors are not
resolved here. Absolute URLs are out of scope; the scholarship and course-material
validators own external locators.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Authored Markdown surfaces. Generated trees (output/, docs/todo/ pages are
# generated but still shipped) are listed explicitly so a generated page cannot
# carry a dangling link into the published tree.
SCAN_ROOTS = (
    "docs",
    "manuscript",
    "scripts",
    "src",
    "tests",
    "data",
    "gnn",
    "vendor",
    ".github",
)
SCAN_FILES = (
    "README.md",
    "AGENTS.md",
    "CLAUDE.md",
    "DESIGN.md",
    "ISA.md",
    "THIRD_PARTY_NOTICES.md",
    "TODO.md",
    "vendor/README.md",
)
SKIP_DIR_NAMES = {".git", ".venv", "__pycache__", "node_modules"}

FENCE_RE = re.compile(r"```.*?```|~~~.*?~~~", re.DOTALL)
INLINE_CODE_RE = re.compile(r"`[^`\n]*`")
LINK_RE = re.compile(r"!?\[[^\]\n]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
REFERENCE_DEF_RE = re.compile(r"^\[[^\]\n]+\]:\s*(\S+)", re.MULTILINE)


def _markdown_files() -> list[Path]:
    files: set[Path] = set()
    for name in SCAN_FILES:
        path = ROOT / name
        if path.is_file():
            files.add(path)
    for entry in SCAN_ROOTS:
        base = ROOT / entry
        if not base.exists():
            continue
        for path in base.rglob("*.md"):
            if SKIP_DIR_NAMES & set(path.parts):
                continue
            files.add(path)
    return sorted(files)


def _targets(text: str) -> list[str]:
    stripped = FENCE_RE.sub("", text)
    stripped = INLINE_CODE_RE.sub("", stripped)
    found = LINK_RE.findall(stripped) + REFERENCE_DEF_RE.findall(stripped)
    return found


def _is_out_of_scope(target: str) -> bool:
    if not target or target.startswith("#"):
        return True
    lowered = target.lower()
    if lowered.startswith(("http://", "https://", "mailto:", "tel:", "ftp://")):
        return True
    # Template placeholders and shell-substituted paths are not links.
    return "{{" in target or "$" in target or target.startswith("<")


def _unresolved(path: Path, target: str) -> bool:
    file_part = target.split("#", 1)[0]
    if not file_part:
        return False
    if file_part.startswith("/"):
        return not (ROOT / file_part.lstrip("/")).exists()
    return not (path.parent / file_part).exists()


def check() -> list[str]:
    issues: list[str] = []
    for path in _markdown_files():
        for target in _targets(path.read_text(encoding="utf-8")):
            if _is_out_of_scope(target):
                continue
            if _unresolved(path, target):
                issues.append(f"{path.relative_to(ROOT)}: unresolved link -> {target}")
    return sorted(set(issues))


def main() -> int:
    issues = check()
    if issues:
        for issue in issues:
            print(issue, file=sys.stderr)
        print(f"\n{len(issues)} unresolved relative link(s)", file=sys.stderr)
        return 1
    print(f"checked {len(_markdown_files())} Markdown files: relative links resolve")
    return 0


if __name__ == "__main__":
    sys.exit(main())
