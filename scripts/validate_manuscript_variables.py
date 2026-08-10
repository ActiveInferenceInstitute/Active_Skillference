#!/usr/bin/env python3
"""Fail if authored manuscript prose hard-codes live generated counts."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from src.artifacts.json_io import read_json_object

MANUSCRIPT = ROOT / "manuscript"
VARIABLES = ROOT / "output" / "data" / "manuscript_variables.json"
CODE_SPAN_RE = re.compile(r"```.*?```|`[^`\n]*`", re.DOTALL)

COUNT_PATTERNS = {
    "skill_count": r"skills?",
    "subject_count": r"subjects?",
    "edge_count": r"(?:prerequisite\s+)?(?:edges?|dependencies)",
    "quiz_count": r"quizzes?",
    "assessment_count": r"(?:assessment|quiz)\s+questions?",
    "claim_count": r"claims?",
    "figure_count": r"figures?",
    "citation_count": r"(?:cited\s+)?sources?",
    "scholarship_source_count": r"(?:matrix\s+)?sources?",
    "max_depth": r"(?:max(?:imum)?\s+)?depth",
    "min_skill_count": r"skills?",
}


def _load_variables() -> dict[str, str]:
    payload = read_json_object(VARIABLES)
    return {str(key): str(value) for key, value in payload.items()}


def _issues(variables: dict[str, str]) -> list[str]:
    issues: list[str] = []
    # Glob the same surface claim_support audits: BOTH the numbered carrier files
    # (NN_*.md) AND the lettered subsection files (NNx_*.md) where the result and
    # methodology prose actually lives after the manuscript modularization. The older
    # `[0-9][0-9]_*.md` glob matched only the thin spine carriers, so a hand-typed
    # live count in 03a_results... silently bypassed this anti-hard-coding gate.
    for path in sorted(MANUSCRIPT.glob("[0-9][0-9]*_*.md")):
        text = CODE_SPAN_RE.sub(" ", path.read_text(encoding="utf-8"))
        for key, noun_pattern in COUNT_PATTERNS.items():
            value = variables.get(key, "")
            if not value or not value.isdigit():
                continue
            token = "{{" + key + "}}"
            # Trailing \b so a noun stem (e.g. "skills?") does not match inside a longer
            # word ("601 skilled volunteers" must not read as a hard-coded skill_count).
            pattern = re.compile(
                rf"\b{re.escape(value)}\b\s+(?:{noun_pattern})\b", re.IGNORECASE
            )
            for match in pattern.finditer(text):
                window_start = max(0, match.start() - 12)
                window_end = min(len(text), match.end() + 12)
                window = text[window_start:window_end]
                if token in window:
                    continue
                issues.append(
                    f"{path.relative_to(ROOT)} hard-codes {key} as {match.group(0)!r}; use {token}"
                )
    return issues


def main() -> int:
    variables = _load_variables()
    missing = sorted(set(COUNT_PATTERNS) - set(variables))
    if missing:
        print(
            "manuscript variable map missing keys: " + ", ".join(missing),
            file=sys.stderr,
        )
        return 1
    issues = _issues(variables)
    if issues:
        print("hard-coded live manuscript variables found:", file=sys.stderr)
        for issue in issues:
            print(f"  {issue}", file=sys.stderr)
        return 1
    print(f"manuscript variable audit clean: {len(COUNT_PATTERNS)} live keys checked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
