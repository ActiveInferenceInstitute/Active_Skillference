"""Read-only artifact discovery for the learner dashboard."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.artifacts.json_io import JsonArtifactError, read_json_object
from src.dashboard.artifact_catalog import (
    ARTIFACTS,
    DashboardArtifact,
)
from src.dashboard.figure_metadata import load_figure_metadata as _load_figure_metadata
from src.skilltree.summary import (
    SkillTreeSummaryError,
    summarize_export_payload,
    validate_export_payload,
)


class DashboardArtifactError(ValueError):
    """Raised for an invalid dashboard artifact request."""


# Derived expected artifact count. Roster integrity is guarded by tests for unique ids,
# unique paths, and registry/dashboard parity rather than a stale hand-maintained literal.
EXPECTED_ARTIFACT_COUNT = len(ARTIFACTS)
_ANSWER_KEY_FIELDS = frozenset({"isCorrect"})


def artifact_inventory(project_root: Path) -> list[dict[str, object]]:
    """Return dashboard metadata for known local artifacts."""
    figure_metadata = _load_figure_metadata(project_root)
    rows: list[dict[str, object]] = []
    for artifact in ARTIFACTS:
        row = artifact.to_dict(project_root)
        metadata = figure_metadata.get(artifact.relative_path.name)
        if metadata:
            row["figure"] = metadata
        rows.append(row)
    return rows


def get_artifact(artifact_id: str) -> DashboardArtifact:
    """Return one artifact by stable id, failing closed on unknown ids."""
    for artifact in ARTIFACTS:
        if artifact.artifact_id == artifact_id:
            return artifact
    raise DashboardArtifactError(f"unknown dashboard artifact {artifact_id!r}")


def read_json_file(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    """Read a JSON object from disk, returning an error string instead of raising."""
    if not path.exists():
        return None, f"{path} does not exist"
    try:
        payload = read_json_object(path)
    except (OSError, json.JSONDecodeError, JsonArtifactError) as exc:
        return None, str(exc)
    return payload, None


def redact_skilltree_answer_keys(payload: Any) -> Any:
    """Return a browser-safe SkillTree export projection without quiz answer keys."""
    if isinstance(payload, dict):
        return {
            key: redact_skilltree_answer_keys(value)
            for key, value in payload.items()
            if key not in _ANSWER_KEY_FIELDS
        }
    if isinstance(payload, list):
        return [redact_skilltree_answer_keys(value) for value in payload]
    return payload


def load_redacted_skilltree_export(
    project_root: Path,
) -> tuple[dict[str, Any] | None, str | None]:
    """Load the raw SkillTree export with learner-visible answer keys removed."""
    path = project_root / "output" / "data" / "skilltree_project.json"
    payload, error = read_json_file(path)
    if payload is None:
        return None, error
    try:
        validate_export_payload(payload)
    except SkillTreeSummaryError as exc:
        return None, str(exc)
    redacted = redact_skilltree_answer_keys(payload)
    if not isinstance(redacted, dict):
        return None, "redacted SkillTree export is not a JSON object"
    return redacted, None


def load_skilltree_project(project_root: Path) -> dict[str, Any]:
    """Load the exported SkillTree project, summarized for dashboard use."""
    path = project_root / "output" / "data" / "skilltree_project.json"
    payload, error = read_json_file(path)
    if payload is None:
        return {
            "available": False,
            "error": error,
            "path": path.relative_to(project_root).as_posix(),
            "project": None,
            "subjects": [],
            "dependencies": [],
            "quizzes": [],
            "counts": {"subjects": 0, "skills": 0, "dependencies": 0, "quizzes": 0},
        }

    try:
        validate_export_payload(payload)
        summary = summarize_export_payload(payload)
    except SkillTreeSummaryError as exc:
        return {
            "available": False,
            "error": str(exc),
            "path": path.relative_to(project_root).as_posix(),
            "project": None,
            "subjects": [],
            "dependencies": [],
            "quizzes": [],
            "counts": {"subjects": 0, "skills": 0, "dependencies": 0, "quizzes": 0},
        }
    browser_payload = redact_skilltree_answer_keys(payload)
    if not isinstance(browser_payload, dict):
        browser_payload = {}
    subjects = browser_payload.get("subjects", [])
    dependencies = browser_payload.get("dependencies", [])
    quizzes = browser_payload.get("quizzes", [])
    if not isinstance(subjects, list):
        subjects = []
    if not isinstance(dependencies, list):
        dependencies = []
    if not isinstance(quizzes, list):
        quizzes = []
    return {
        "available": True,
        "error": None,
        "path": path.relative_to(project_root).as_posix(),
        "project": {
            "id": payload.get("projectId"),
            "name": payload.get("name"),
        },
        "subjects": subjects,
        "dependencies": dependencies,
        "quizzes": quizzes,
        "counts": summary.project_counts(),
    }


def load_claims_summary(project_root: Path) -> dict[str, object]:
    """Load provenance-claim metadata without changing the ledger."""
    path = project_root / "output" / "data" / "claims.json"
    payload, error = read_json_file(path)
    if payload is None:
        return {
            "available": False,
            "error": error,
            "path": path.relative_to(project_root).as_posix(),
            "count": 0,
            "claims": [],
        }
    return {
        "available": True,
        "error": None,
        "path": path.relative_to(project_root).as_posix(),
        "count": len(payload),
        "claims": sorted(payload),
    }


def load_curriculum_stats(project_root: Path) -> dict[str, object]:
    """Load curriculum stats, if the build step has produced them."""
    path = project_root / "output" / "data" / "curriculum_stats.json"
    payload, error = read_json_file(path)
    if payload is None:
        return {
            "available": False,
            "error": error,
            "path": path.relative_to(project_root).as_posix(),
            "stats": {},
        }
    return {
        "available": True,
        "error": None,
        "path": path.relative_to(project_root).as_posix(),
        "stats": payload,
    }


def load_curriculum_diagnostics(project_root: Path) -> dict[str, object]:
    path = project_root / "output" / "data" / "curriculum_diagnostic_gap_map.json"
    payload, error = read_json_file(path)
    rel = path.relative_to(project_root).as_posix()
    if payload is None:
        return {
            "available": False,
            "bottlenecks": [],
            "error": error,
            "longChains": [],
            "path": rel,
            "remediationQueue": [],
            "summary": {},
        }
    summary = payload.get("summary")
    if not isinstance(summary, dict) or not summary:
        return {
            "available": False,
            "bottlenecks": [],
            "error": f"{rel} is missing a non-empty 'summary' object",
            "longChains": [],
            "path": rel,
            "remediationQueue": [],
            "summary": {},
        }
    payload["available"] = True
    payload["error"] = None
    payload["path"] = rel
    return payload


def load_scholarship_health_network(project_root: Path) -> dict[str, object]:
    path = project_root / "output" / "data" / "scholarship_source_health_network.json"
    payload, error = read_json_file(path)
    rel = path.relative_to(project_root).as_posix()
    if payload is None:
        return {
            "available": False,
            "botBlocks": [],
            "boundarySources": [],
            "deadLinks": [],
            "error": error,
            "path": rel,
            "roleGaps": [],
            "summary": {},
            "uncitedDrift": {},
        }
    summary = payload.get("summary")
    if not isinstance(summary, dict) or not summary:
        return {
            "available": False,
            "botBlocks": [],
            "boundarySources": [],
            "deadLinks": [],
            "error": f"{rel} is missing a non-empty 'summary' object",
            "path": rel,
            "roleGaps": [],
            "summary": {},
            "uncitedDrift": {},
        }
    payload["available"] = True
    payload["error"] = None
    payload["path"] = rel
    return payload


def load_figure_table_companions(project_root: Path) -> dict[str, object]:
    path = project_root / "output" / "data" / "figure_table_companions.json"
    payload, error = read_json_file(path)
    rel = path.relative_to(project_root).as_posix()
    unavailable: dict[str, object] = {"figures": {}, "summary": {}}
    if payload is None:
        return {"available": False, "error": error, "path": rel, **unavailable}
    figures = payload.get("figures")
    summary = payload.get("summary")
    if not isinstance(figures, dict) or not isinstance(summary, dict) or not summary:
        return {
            "available": False,
            "error": f"{rel} missing/typed-wrong figures or summary",
            "path": rel,
            **unavailable,
        }
    payload["available"] = True
    payload["error"] = None
    payload["path"] = rel
    return payload


def load_course_materials_summary(project_root: Path) -> dict[str, object]:
    """Load generated course-material audit metadata for the dashboard status."""
    path = project_root / "output" / "data" / "course_material_audit.json"
    payload, error = read_json_file(path)
    if payload is None:
        return {
            "available": False,
            "error": error,
            "path": path.relative_to(project_root).as_posix(),
            "summary": {},
            "issues": [],
        }
    issues = payload.get("issues", [])
    if not isinstance(issues, list):
        issues = []
    summary = payload.get("summary", {})
    # Fail closed on a malformed artifact: a present-but-shapeless JSON file (no/typed-wrong
    # `summary`) must read as UNAVAILABLE, not as available-but-silently-empty — otherwise
    # the dashboard would certify a broken artifact as healthy.
    if not isinstance(summary, dict) or not summary:
        rel = path.relative_to(project_root).as_posix()
        return {
            "available": False,
            "error": f"{rel} is missing a non-empty 'summary' object",
            "path": rel,
            "summary": {},
            "issues": issues,
        }
    return {
        "available": True,
        "error": None,
        "path": path.relative_to(project_root).as_posix(),
        "summary": summary,
        "issues": issues,
    }


def load_course_material_index(project_root: Path) -> dict[str, object]:
    """Load the full generated course-material index for the local Learn panel."""
    path = project_root / "output" / "data" / "course_material_index.json"
    rel = path.relative_to(project_root).as_posix()
    unavailable = {
        "summary": {"skills": 0, "externalPointers": 0, "sources": 0},
        "sources": [],
        "skills": {},
    }
    payload, error = read_json_file(path)
    if payload is None:
        return {"available": False, "error": error, "path": rel, **unavailable}
    # Validate the required shape: a valid-JSON file that lacks the index keys is a broken
    # artifact, not a healthy index. Fail closed rather than reporting available=True on it.
    required = {"skills": dict, "sources": list, "summary": dict}
    missing = [
        key for key, typ in required.items() if not isinstance(payload.get(key), typ)
    ]
    if missing:
        return {
            "available": False,
            "error": f"{rel} missing/typed-wrong required key(s): {', '.join(missing)}",
            "path": rel,
            **unavailable,
        }
    payload["available"] = True
    payload["error"] = None
    payload["path"] = rel
    return payload
