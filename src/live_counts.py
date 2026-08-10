"""Repository-wide live-count drift audit.

The manuscript variable validator protects rendered manuscript sections. This module
extends the same idea to authored project surfaces that often carry release claims:
roadmap, docs, manuscript sources, and publication metadata.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.artifacts.json_io import JsonArtifactError, read_json_array
from src.curriculum.catalog import build_curriculum
from src.kernels.examples import build_claim_registry
from src.project_identity import SKILLTREE_PROJECT_ID, SKILLTREE_PROJECT_NAME
from src.scholarship.coverage import validate_scholarship
from src.skilltree.exporter import export_project
from src.skilltree.summary import summarize_project


@dataclass(frozen=True)
class LiveCount:
    """One generated count and the nouns that may refer to it."""

    key: str
    value: int
    nouns: tuple[str, ...]
    yaml_keys: tuple[str, ...]


@dataclass(frozen=True)
class LiveCountIssue:
    """A stale count literal found in an authored project surface."""

    path: Path
    line: int
    key: str
    found: int
    expected: int
    excerpt: str

    def __str__(self) -> str:
        return (
            f"{self.path}:{self.line}: {self.key} literal {self.found} "
            f"should be {self.expected}: {self.excerpt}"
        )


class LiveCountError(ValueError):
    """Raised when an authored surface hard-codes a stale generated count."""


_CODE_BLOCK_RE = re.compile(r"```.*?```", re.DOTALL)


def build_live_counts(root: Path) -> dict[str, LiveCount]:
    """Derive current project counts from source-of-truth builders/artifacts."""
    root = Path(root)
    graph = build_curriculum()
    registry = build_claim_registry()
    export_summary = summarize_project(
        export_project(graph, SKILLTREE_PROJECT_ID, SKILLTREE_PROJECT_NAME)
    )
    scholarship = validate_scholarship(
        root / "manuscript",
        root / "data" / "scholarship_sources.yaml",
        root / "manuscript" / "references.bib",
    )
    figure_count = _figure_registry_count(root)

    counts = (
        LiveCount(
            "skill_count",
            export_summary.skills,
            ("skills", "skill"),
            ("skills", "skill", "skill_count", "min_skill_count"),
        ),
        LiveCount(
            "subject_count",
            export_summary.subjects,
            ("subjects", "subject"),
            ("subjects", "subject", "subject_count"),
        ),
        LiveCount(
            "edge_count",
            export_summary.dependencies,
            ("edges", "edge", "dependencies", "dependency"),
            (
                "prerequisite_edges",
                "edges",
                "edge",
                "dependencies",
                "dependency",
                "edge_count",
            ),
        ),
        LiveCount(
            "quiz_count",
            export_summary.quizzes,
            ("quizzes", "quiz"),
            ("quizzes", "quiz", "quiz_count"),
        ),
        LiveCount(
            "assessment_count",
            export_summary.assessments,
            ("assessment questions", "quiz questions"),
            ("assessments", "assessment_count"),
        ),
        LiveCount(
            "claim_count",
            len(registry),
            ("claims", "claim"),
            ("claims", "claim", "claim_count"),
        ),
        LiveCount(
            "figure_count",
            figure_count,
            ("figures", "figure"),
            ("figures", "figure", "figure_count"),
        ),
        LiveCount(
            "citation_count",
            _as_int(scholarship.to_dict()["summary"]["citedSources"]),
            ("cited sources", "sources", "source"),
            ("cited_sources", "citation_count"),
        ),
        LiveCount(
            "max_depth",
            _as_int(graph.stats()["max_depth"]),
            ("max depth",),
            ("max_depth",),
        ),
    )
    return {count.key: count for count in counts}


def audited_count_paths(root: Path) -> tuple[Path, ...]:
    """Return authored files where live count literals are not allowed to drift."""
    root = Path(root)
    paths: list[Path] = [
        root / "tasks.yaml",
        root / "TODO.md",
        root / "README.md",
        root / "CITATION.cff",
        root / ".zenodo.json",
        root / "codemeta.json",
    ]
    for folder in (root / "docs", root / "manuscript"):
        if folder.exists():
            paths.extend(sorted(folder.rglob("*.md")))
            paths.extend(sorted(folder.rglob("*.yaml")))
    return tuple(path for path in paths if path.exists())


def audit_live_count_literals(root: Path) -> list[LiveCountIssue]:
    """Find stale hard-coded count+noun literals in authored project surfaces."""
    root = Path(root)
    counts = build_live_counts(root)
    patterns = _count_patterns(counts)
    issues: list[LiveCountIssue] = []

    for path in audited_count_paths(root):
        rel = path.relative_to(root)
        text = _CODE_BLOCK_RE.sub("", path.read_text(encoding="utf-8"))
        for line_number, line in enumerate(text.splitlines(), start=1):
            for key, pattern in patterns.items():
                expected = counts[key].value
                for match in pattern.finditer(line):
                    group = "prose" if match.group("prose") is not None else "yaml"
                    found = int(match.group(group))
                    if found != expected:
                        issues.append(
                            LiveCountIssue(
                                path=rel,
                                line=line_number,
                                key=key,
                                found=found,
                                expected=expected,
                                excerpt=line.strip(),
                            )
                        )
    return issues


def validate_live_count_literals(root: Path) -> None:
    """Raise when an authored surface contains stale generated counts."""
    issues = audit_live_count_literals(root)
    if issues:
        raise LiveCountError(
            "stale live-count literals found:\n  "
            + "\n  ".join(str(issue) for issue in issues)
        )


def _figure_registry_count(root: Path) -> int:
    registry_path = root / "output" / "figures" / "figure_registry.json"
    try:
        payload = read_json_array(registry_path)
    except FileNotFoundError as exc:
        raise LiveCountError(f"figure registry is missing: {registry_path}") from exc
    except json.JSONDecodeError as exc:
        raise LiveCountError(
            f"figure registry is not valid JSON: {registry_path}"
        ) from exc
    except JsonArtifactError as exc:
        raise LiveCountError(
            f"figure registry must be a JSON list: {registry_path}"
        ) from exc
    seen: set[str] = set()
    missing_files: list[str] = []
    for index, row in enumerate(payload, start=1):
        if not isinstance(row, dict):
            raise LiveCountError(f"figure registry row {index} must be an object")
        filename = row.get("filename")
        if not isinstance(filename, str) or not filename.endswith(".png"):
            raise LiveCountError(
                f"figure registry row {index} filename must be a PNG string"
            )
        if filename in seen:
            raise LiveCountError(f"duplicate figure registry filename {filename!r}")
        seen.add(filename)
        # Captured browser evidence declares a tracked asset root instead of
        # living beside the generated figures, so resolve each row where it says
        # it is rather than assuming the registry's own directory.
        asset_root = row.get("asset_root")
        if isinstance(asset_root, str) and asset_root.strip():
            resolved = root / asset_root / filename
        else:
            resolved = registry_path.parent / filename
        if not resolved.is_file():
            missing_files.append(filename)
    if missing_files:
        raise LiveCountError(
            "figure registry references missing files: " + ", ".join(missing_files)
        )
    return len(payload)


def _count_patterns(counts: dict[str, LiveCount]) -> dict[str, re.Pattern[str]]:
    patterns: dict[str, re.Pattern[str]] = {}
    for key, count in counts.items():
        nouns = "|".join(
            re.escape(noun) for noun in sorted(count.nouns, key=len, reverse=True)
        )
        yaml_keys = "|".join(
            re.escape(yaml_key)
            for yaml_key in sorted(count.yaml_keys, key=len, reverse=True)
        )
        prose_pattern = (
            r"\bmax(?:imum)?\s+depth\s+(?P<prose>\d+)\b"
            if key == "max_depth"
            else rf"\b(?P<prose>\d+)\s+(?:{nouns})\b"
        )
        # The YAML key is anchored to a full key token (leading indentation, the exact
        # key, then a colon), so substrings like ``max_prior_releases`` never match the
        # ``skills``/``edges`` keys and unmapped keys like ``kernel_seed`` are ignored.
        yaml_pattern = rf"^\s*(?:{yaml_keys}):\s*(?P<yaml>\d+)\b"
        # Prose and YAML alternatives use distinct group names because a single Python
        # pattern cannot reuse one named group across both branches.
        patterns[key] = re.compile(
            rf"(?:{prose_pattern})|(?:{yaml_pattern})", re.IGNORECASE
        )
    return patterns


def _as_int(value: Any) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        return int(value)
    raise TypeError(f"expected numeric count value, got {type(value).__name__}")
