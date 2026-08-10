#!/usr/bin/env python3
"""Fail if the rendered manuscript is stale versus the current artifacts.

The publication surface lives in ``output/manuscript/`` and the PDF is built from it.
Count-bearing prose is substituted from ``output/data/manuscript_variables.json`` at
render time, so if the curriculum is regenerated but the manuscript is not re-rendered,
the rendered ``.md`` (and the PDF) silently keep stale numbers while every other gate
stays green. This gate re-renders each source file from the *current* variables and
asserts the committed rendered copy is byte-identical, catching exactly that drift.
"""

from __future__ import annotations

import html
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import z_generate_manuscript_variables as zg

ROADMAP_OPEN_RE = re.compile(
    r"(?P<count>\d+)\s+open items across\s+(?P<surfaces>[^.]+)",
    re.IGNORECASE,
)
TEXT_ARTIFACT_SUFFIXES = {".html", ".md", ".tex", ".txt", ".xhtml", ".xml"}
ZIP_TEXT_ARTIFACT_SUFFIXES = {".docx", ".epub", ".pptx"}


def check_artifact_counts_match_graph() -> list[str]:
    """Return drift between committed manuscript_variables.json counts and the LIVE graph.

    The render freshness check only proves the rendered manuscript matches the committed
    ``manuscript_variables.json``; it cannot tell whether that JSON is itself stale versus
    the curriculum. This re-derives the count-bearing fields directly from
    ``build_curriculum()`` and fails if the committed JSON disagrees, so a drifted JSON
    cannot publish a false headline count while every other gate stays green.
    """
    from src.curriculum.catalog import build_curriculum

    variables = zg._variables()
    graph = build_curriculum()
    stats = graph.stats()
    expected = {
        "skill_count": str(stats["skills"]),
        "subject_count": str(stats["subjects"]),
        "edge_count": str(stats["prerequisite_edges"]),
        "max_depth": str(stats["max_depth"]),
        "core_max_depth": str(stats["core_max_depth"]),
        "quiz_count": str(
            sum(1 for s in graph.skills if s.self_reporting_type == "Quiz")
        ),
        "assessment_count": str(sum(len(s.assessments) for s in graph.skills)),
    }
    drift: list[str] = []
    for key, want in expected.items():
        got = variables.get(key)
        if got != want:
            drift.append(
                f"manuscript_variables.json[{key}]={got!r} but live graph says {want!r}"
            )
    return drift


def check_rendered_freshness() -> list[str]:
    """Return a list of stale/missing rendered manuscript files (empty == fresh)."""
    variables = zg._variables()
    stale: list[str] = []
    for source in sorted(zg.MANUSCRIPT.glob("*.md")):
        if source.name in zg.RENDER_SKIP:
            continue
        expected = zg._render_markdown(source.read_text(encoding="utf-8"), variables)
        rendered_path = zg.OUTPUT_MANUSCRIPT / source.name
        if not rendered_path.is_file():
            stale.append(f"{source.name}: no rendered output (run z_generate)")
            continue
        if rendered_path.read_text(encoding="utf-8") != expected:
            stale.append(
                f"{source.name}: rendered output is stale vs current artifacts"
            )
    return stale


def check_publication_bundle_roadmap_freshness(root: Path = ROOT) -> list[str]:
    """Return stale roadmap-open-count prose in rendered publication artifacts."""
    current_path = root / "output" / "manuscript" / "04_conclusion.md"
    if not current_path.is_file():
        return [f"{current_path.relative_to(root)}: missing rendered conclusion"]
    current_text = current_path.read_text(encoding="utf-8")
    current = ROADMAP_OPEN_RE.search(current_text)
    if current is None:
        return [
            f"{current_path.relative_to(root)}: missing current roadmap open-count text"
        ]
    expected = _normalize_roadmap_phrase(current.group(0))
    issues: list[str] = []
    for artifact in _publication_text_artifacts(root):
        text = _read_publication_artifact_text(artifact)
        if "open items across" not in text:
            continue
        phrases = {
            _normalize_roadmap_phrase(match.group(0))
            for match in ROADMAP_OPEN_RE.finditer(text)
        }
        if phrases and phrases != {expected}:
            found = ", ".join(sorted(phrases))
            issues.append(
                f"{artifact.relative_to(root)}: stale roadmap text "
                f"({found}; expected {expected})"
            )
    return issues


def _normalize_roadmap_phrase(text: str) -> str:
    return " ".join(text.rstrip(".").split())


def _publication_text_artifacts(root: Path) -> list[Path]:
    candidates: list[Path] = []
    for dirname in ("pdf", "web", "docx", "epub", "slides"):
        base = root / "output" / dirname
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if not path.is_file():
                continue
            suffix = path.suffix.lower()
            if suffix in TEXT_ARTIFACT_SUFFIXES | ZIP_TEXT_ARTIFACT_SUFFIXES:
                candidates.append(path)
    return sorted(candidates)


def _read_publication_artifact_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in ZIP_TEXT_ARTIFACT_SUFFIXES:
        try:
            with zipfile.ZipFile(path) as archive:
                chunks = [
                    _xmlish_to_text(archive.read(name).decode("utf-8", errors="ignore"))
                    for name in archive.namelist()
                    if Path(name).suffix.lower() in TEXT_ARTIFACT_SUFFIXES
                ]
        except zipfile.BadZipFile:
            return ""
        return "\n".join(chunks)
    return _xmlish_to_text(path.read_text(encoding="utf-8", errors="ignore"))


def _xmlish_to_text(text: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", " ", text))


def main() -> int:
    if not zg.OUTPUT_MANUSCRIPT.exists():
        print(
            "rendered manuscript freshness FAILED: output/manuscript/ does not exist; "
            "run scripts/z_generate_manuscript_variables.py"
        )
        return 1
    drift = check_artifact_counts_match_graph()
    if drift:
        print("artifact freshness FAILED: manuscript_variables.json is stale vs graph:")
        for item in drift:
            print(f"  - {item}")
        return 1
    stale = check_rendered_freshness()
    if stale:
        print("rendered manuscript freshness FAILED (re-render before publishing):")
        for item in stale:
            print(f"  - {item}")
        return 1
    bundle_stale = check_publication_bundle_roadmap_freshness()
    if bundle_stale:
        print("publication bundle freshness FAILED (re-render before publishing):")
        for item in bundle_stale:
            print(f"  - {item}")
        return 1
    rendered = sorted(zg.OUTPUT_MANUSCRIPT.glob("*.md"))
    print(
        f"rendered manuscript freshness OK ({len(rendered)} files match current "
        "artifacts; publication roadmap text matches)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
