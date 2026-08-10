"""Reusable live SkillTree/dashboard validation helpers."""

from __future__ import annotations

import http.client
import json
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from src.artifacts.json_io import JsonArtifactError, read_json_object
from src.figures.registry import (
    FIGURE_CONTRACT_FIELDS,
    FigureRegistryError,
    load_figure_registry_rows,
)
from src.net_guard import NonHttpUrlError, require_http_url
from src.project_identity import SKILLTREE_PROJECT_ID, SKILLTREE_PROJECT_NAME
from src.skilltree.summary import SkillTreeSummaryError, summarize_export_payload


class LiveSkillTreeDashboardError(RuntimeError):
    """Raised when the live SkillTree/dashboard handoff is not publication-ready."""


def _fetch_json(url: str, timeout: float) -> dict[str, Any]:
    try:
        require_http_url(url, context="live dashboard validator")
    except NonHttpUrlError as exc:
        raise LiveSkillTreeDashboardError(str(exc)) from exc
    request = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        # require_http_url() above rejects non-http(s) targets.
        with urllib.request.urlopen(request, timeout=timeout) as response:  # nosec B310
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")[:500]
        raise LiveSkillTreeDashboardError(
            f"{url} returned HTTP {exc.code}: {body}"
        ) from exc
    except urllib.error.URLError as exc:
        raise LiveSkillTreeDashboardError(
            f"{url} is not reachable: {exc.reason}"
        ) from exc
    except (ConnectionResetError, http.client.RemoteDisconnected) as exc:
        raise LiveSkillTreeDashboardError(f"{url} closed the connection") from exc
    except TimeoutError as exc:
        raise LiveSkillTreeDashboardError(f"{url} timed out") from exc
    except json.JSONDecodeError as exc:
        raise LiveSkillTreeDashboardError(f"{url} did not return JSON") from exc
    if not isinstance(payload, dict):
        raise LiveSkillTreeDashboardError(f"{url} returned JSON that is not an object")
    return payload


def _count_exported_project(project_path: Path) -> dict[str, int]:
    try:
        payload = read_json_object(project_path)
    except FileNotFoundError as exc:
        raise LiveSkillTreeDashboardError(
            f"project export is missing: {project_path}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise LiveSkillTreeDashboardError(
            f"project export is not valid JSON: {project_path}"
        ) from exc
    except JsonArtifactError as exc:
        raise LiveSkillTreeDashboardError(str(exc)) from exc
    try:
        return summarize_export_payload(payload).project_counts()
    except SkillTreeSummaryError as exc:
        raise LiveSkillTreeDashboardError(str(exc)) from exc


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise LiveSkillTreeDashboardError(message)


def _figure_filename(row: dict[str, Any]) -> str:
    for key in ("filename", "file", "path"):
        value = row.get(key)
        if isinstance(value, str) and value.strip():
            return Path(value).name
    return ""


def _load_figure_registry(project_root: Path) -> list[dict[str, Any]]:
    path = project_root / "output" / "figures" / "figure_registry.json"
    try:
        return [entry.to_dict() for entry in load_figure_registry_rows(path)]
    except FileNotFoundError as exc:
        raise LiveSkillTreeDashboardError(
            f"figure registry is missing: {path}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise LiveSkillTreeDashboardError(
            f"figure registry is not valid JSON: {path}"
        ) from exc
    except FigureRegistryError as exc:
        raise LiveSkillTreeDashboardError(str(exc)) from exc


def _require_structured_fields(row: dict[str, Any], *, source: str) -> None:
    missing = []
    for field in FIGURE_CONTRACT_FIELDS:
        value = row.get(field)
        if isinstance(value, str) and value.strip():
            continue
        if (
            field in {"data_sources", "palette_roots"}
            and isinstance(value, list)
            and value
        ):
            continue
        missing.append(field)
    _require(
        not missing, f"{source} missing structured chart-contract fields: {missing}"
    )


def _validate_figure_contracts(
    *,
    project_root: Path,
    artifacts: list[Any],
) -> dict[str, Any]:
    rows = _load_figure_registry(project_root)
    registry_by_file: dict[str, dict[str, Any]] = {}
    for row in rows:
        filename = _figure_filename(row)
        _require(bool(filename), "figure registry row is missing a filename/path")
        _require(
            filename not in registry_by_file,
            f"duplicate figure registry filename: {filename}",
        )
        _require_structured_fields(row, source=f"registry row {filename}")
        figure_path = project_root / "output" / "figures" / filename
        _require(
            figure_path.is_file(),
            f"registered figure file is missing: {figure_path.relative_to(project_root)}",
        )
        registry_by_file[filename] = row

    dashboard_by_file: dict[str, dict[str, Any]] = {}
    for artifact in artifacts:
        if not isinstance(artifact, dict):
            continue
        figure = artifact.get("figure")
        if not isinstance(figure, dict):
            continue
        path = artifact.get("path")
        if not isinstance(path, str) or not path.strip():
            raise LiveSkillTreeDashboardError(
                "dashboard figure artifact is missing a path"
            )
        filename = Path(path).name
        dashboard_by_file[filename] = artifact

    registry_files = set(registry_by_file)
    dashboard_files = set(dashboard_by_file)
    missing_dashboard = sorted(registry_files - dashboard_files)
    extra_dashboard = sorted(dashboard_files - registry_files)
    _require(
        not missing_dashboard,
        f"registered figures missing from dashboard artifacts: {missing_dashboard}",
    )
    _require(
        not extra_dashboard,
        f"dashboard figure artifacts absent from registry: {extra_dashboard}",
    )

    for filename, artifact in dashboard_by_file.items():
        _require(
            artifact.get("exists") is True, f"dashboard figure is missing: {filename}"
        )
        figure = artifact.get("figure")
        if not isinstance(figure, dict):
            raise LiveSkillTreeDashboardError(
                f"dashboard figure metadata missing: {filename}"
            )
        _require_structured_fields(figure, source=f"dashboard figure {filename}")

    manuscript_labels = _validate_manuscript_label_parity(
        project_root=project_root,
        artifacts=artifacts,
    )

    return {
        "checked": True,
        "registered": len(registry_by_file),
        "dashboard": len(dashboard_by_file),
        "fields": list(FIGURE_CONTRACT_FIELDS),
        "manuscriptLabels": manuscript_labels,
    }


def _validate_manuscript_label_parity(
    *,
    project_root: Path,
    artifacts: list[Any],
) -> dict[str, Any]:
    """Require the served manuscript artifact audit to report no label drift.

    Registry/manuscript label drift used to be invisible from the dashboard
    side: the dashboard checked that every registered figure was in its roster,
    but nothing stopped it serving a manuscript audit that was itself failing.
    The audit is already a dashboard artifact, so the running surface can be
    held to it — a dashboard shipping a figure the manuscript never declares is
    exactly the false-certification this gate exists to catch.
    """
    audit_path = project_root / "output" / "data" / "manuscript_artifacts.json"
    _require(
        audit_path.is_file(),
        f"manuscript artifact audit is missing: {audit_path.relative_to(project_root)}",
    )
    served = any(
        isinstance(artifact, dict)
        and Path(str(artifact.get("path", ""))).name == audit_path.name
        for artifact in artifacts
    )
    _require(
        served,
        "manuscript artifact audit is not exposed as a dashboard artifact",
    )
    try:
        audit = json.loads(audit_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise LiveSkillTreeDashboardError(
            f"manuscript artifact audit is not readable: {exc}"
        ) from exc
    if not isinstance(audit, dict):
        raise LiveSkillTreeDashboardError(
            "manuscript artifact audit must be a JSON object"
        )
    issues = audit.get("issues") or []
    _require(
        not issues,
        f"served manuscript artifact audit reports issues: {issues}",
    )
    summary = audit.get("summary") or {}
    if not isinstance(summary, dict):
        raise LiveSkillTreeDashboardError(
            "manuscript artifact audit summary must be an object"
        )
    registered = int(summary.get("registeredFigures", -1))
    declared = int(summary.get("declaredFigureLabels", -1))
    referenced = int(summary.get("referencedFigureLabels", -1))
    _require(
        registered >= 0 and declared == registered,
        "manuscript declares "
        f"{declared} figure labels for {registered} registered figures",
    )
    _require(
        referenced == registered,
        "manuscript cross-references "
        f"{referenced} figure labels for {registered} registered figures",
    )
    return {
        "checked": True,
        "registeredFigures": registered,
        "declaredLabels": declared,
        "referencedLabels": referenced,
    }


def validate_live_skilltree_dashboard(
    *,
    dashboard_url: str,
    skilltree_url: str,
    project_root: Path,
    local_state_dir: Path | None = None,
    timeout: float = 5.0,
    require_token: bool = True,
    require_live_admin: bool = False,
    require_live_dependencies: bool = False,
    require_figure_contracts: bool = False,
) -> dict[str, Any]:
    """Return a browser-safe summary if live SkillTree/dashboard wiring is healthy."""
    dashboard_url = dashboard_url.rstrip("/")
    skilltree_url = skilltree_url.rstrip("/")
    skilltree_status = _fetch_json(f"{skilltree_url}/public/status", timeout)
    dashboard_status = _fetch_json(f"{dashboard_url}/api/status", timeout)
    material_index = _fetch_json(f"{dashboard_url}/api/course-materials", timeout)

    project_path = project_root / "output" / "data" / "skilltree_project.json"
    exported_counts = _count_exported_project(project_path)
    project = dashboard_status.get("project", {})
    config = dashboard_status.get("config", {})
    dashboard_skilltree = dashboard_status.get("skilltree", {})
    course_materials = dashboard_status.get("courseMaterials", {})
    artifacts = dashboard_status.get("artifacts", [])

    _require(isinstance(project, dict), "dashboard project payload is not an object")
    _require(isinstance(config, dict), "dashboard config payload is not an object")
    _require(
        isinstance(dashboard_skilltree, dict),
        "dashboard SkillTree status is not an object",
    )
    _require(
        isinstance(course_materials, dict),
        "dashboard course-material status is not an object",
    )
    _require(isinstance(artifacts, list), "dashboard artifacts payload is not a list")

    counts = project.get("counts", {})
    _require(isinstance(counts, dict), "dashboard project counts are not an object")
    _require(
        counts == exported_counts,
        f"dashboard counts {counts!r} != export {exported_counts!r}",
    )
    public_project = config.get("project", {})
    _require(isinstance(public_project, dict), "public project config is not an object")
    project_id = project.get("projectId") or public_project.get("id")
    project_name = project.get("name") or public_project.get("name")
    _require(
        project_id == SKILLTREE_PROJECT_ID,
        "dashboard project id mismatch",
    )
    _require(project_name == SKILLTREE_PROJECT_NAME, "dashboard project name mismatch")
    _require(
        dashboard_skilltree.get("available") is True,
        "dashboard reports SkillTree offline",
    )
    _require(
        dashboard_skilltree.get("statusCode") == 200,
        "dashboard SkillTree status endpoint did not return HTTP 200",
    )

    public_skilltree = config.get("skilltree", {})
    _require(
        isinstance(public_skilltree, dict), "public SkillTree config is not an object"
    )
    _require(
        public_skilltree.get("url") == skilltree_url, "dashboard SkillTree URL mismatch"
    )
    _require(
        public_skilltree.get("authenticatorConfigured") is True,
        "dashboard has no configured SkillTree authenticator",
    )
    local_auth = public_skilltree.get("localAuth", {})
    _require(isinstance(local_auth, dict), "local auth payload is not an object")
    _require(local_auth.get("ready") is True, "local SkillTree auth is not ready")
    _require(
        course_materials.get("available") is True,
        "dashboard course-material audit is unavailable",
    )
    course_summary = course_materials.get("summary", {})
    _require(
        isinstance(course_summary, dict),
        "dashboard course-material summary is not an object",
    )
    _require(
        course_summary.get("materialRecords") == exported_counts["skills"],
        "dashboard course-material record count does not match exported skills",
    )
    _require(
        int(course_summary.get("externalPointers", 0)) >= exported_counts["skills"],
        "dashboard course-material pointers are incomplete",
    )
    _require(
        material_index.get("available") is True,
        "dashboard course-material index endpoint is unavailable",
    )
    material_skills = material_index.get("skills", {})
    _require(
        isinstance(material_skills, dict),
        "dashboard course-material index skills payload is not an object",
    )
    _require(
        len(material_skills) == exported_counts["skills"],
        "dashboard course-material index skill count does not match exported skills",
    )
    _require(
        "{{claim:" not in json.dumps(material_index),
        "dashboard course-material index contains unresolved claim tokens",
    )
    missing_material_pointers = [
        skill_id
        for skill_id, record in material_skills.items()
        if not (
            isinstance(record, dict)
            and isinstance(record.get("externalPointers"), list)
            and record.get("externalPointers")
        )
    ]
    _require(
        not missing_material_pointers,
        f"dashboard material records lack external pointers: {missing_material_pointers[:8]!r}",
    )

    missing = [
        artifact
        for artifact in artifacts
        if isinstance(artifact, dict) and not artifact.get("exists")
    ]
    _require(not missing, f"dashboard has missing artifacts: {missing!r}")

    from src.dashboard.artifacts import EXPECTED_ARTIFACT_COUNT

    _require(
        len(artifacts) == EXPECTED_ARTIFACT_COUNT,
        f"dashboard served {len(artifacts)} artifacts, expected "
        f"{EXPECTED_ARTIFACT_COUNT}",
    )

    token_keys: list[str] = []
    if require_token:
        token = _fetch_json(f"{dashboard_url}/api/skilltree/token", timeout)
        token_keys = sorted(token.keys())
        _require(
            "access_token" in token or "accessToken" in token,
            "SkillTree token exchange returned no token",
        )
        token_text = json.dumps(token)
        for forbidden in (
            "client_secret",
            "clientSecret",
            "admin_password",
            "adminPassword",
        ):
            _require(forbidden not in token_text, f"token exchange exposed {forbidden}")

    live_admin = _validate_live_admin_count(
        skilltree_url=skilltree_url,
        project_root=project_root,
        project_id=str(project_id),
        expected_skills=exported_counts["skills"],
        local_state_dir=local_state_dir,
        timeout=timeout,
        required=require_live_admin,
    )
    live_dependencies = _validate_live_dependencies(
        skilltree_url=skilltree_url,
        project_root=project_root,
        project_id=str(project_id),
        exported_dependencies=project.get("dependencies", []),
        local_state_dir=local_state_dir,
        timeout=timeout,
        required=require_live_dependencies,
    )
    figure_contracts = (
        _validate_figure_contracts(project_root=project_root, artifacts=artifacts)
        if require_figure_contracts
        else {"checked": False}
    )

    return {
        "ok": True,
        "skilltreeStatus": skilltree_status,
        "dashboardUrl": dashboard_url,
        "skilltreeUrl": skilltree_url,
        "counts": exported_counts,
        "artifacts": {"present": len(artifacts), "missing": 0},
        "courseMaterials": {
            "records": course_summary.get("materialRecords"),
            "externalPointers": course_summary.get("externalPointers"),
        },
        "figureContracts": figure_contracts,
        "liveAdminProject": live_admin,
        "liveDependencies": live_dependencies,
        "tokenKeys": token_keys,
    }


def _validate_live_dependencies(
    *,
    skilltree_url: str,
    project_root: Path,
    project_id: str,
    exported_dependencies: Any,
    local_state_dir: Path | None,
    timeout: float,
    required: bool,
) -> dict[str, Any]:
    """Optionally verify live SkillTree dependency graph parity."""
    from src.skilltree.client import SkillTreeClientError
    from src.skilltree.dependency_reconciler import (
        dependency_pairs_from_payload,
        summarize_dependency_parity,
    )
    from src.skilltree.local_auth import (
        DEFAULT_LOCAL_STATE_DIR,
        LocalSkillTreeAuthError,
        SkillTreeSessionClient,
        load_local_state,
    )

    _require(
        isinstance(exported_dependencies, list),
        "exported project dependencies payload is not a list",
    )
    expected_pairs = dependency_pairs_from_payload(exported_dependencies, strict=True)
    state_dir = local_state_dir or project_root / DEFAULT_LOCAL_STATE_DIR
    state = load_local_state(state_dir)
    if state is None:
        _require(not required, f"local SkillTree auth state not found at {state_dir}")
        return {
            "checked": False,
            "reason": "local SkillTree auth state not found",
            "expectedDependencies": len(expected_pairs),
        }
    _require(
        state.project_id == project_id,
        f"local SkillTree auth state is for {state.project_id!r}, not {project_id!r}",
    )
    _require(
        state.skilltree_url.rstrip("/") == skilltree_url.rstrip("/"),
        "local SkillTree auth state URL does not match the validated SkillTree URL",
    )
    client = SkillTreeSessionClient(
        skilltree_url,
        project_id,
        timeout=max(timeout, 30.0),
    )
    try:
        client.login(state.admin_username, state.admin_password)
        live_pairs = client.live_dependency_pairs()
    except (LocalSkillTreeAuthError, SkillTreeClientError) as exc:
        _require(not required, f"live SkillTree dependency check failed: {exc}")
        return {
            "checked": False,
            "reason": str(exc),
            "expectedDependencies": len(expected_pairs),
        }
    summary = summarize_dependency_parity(
        expected_pairs=expected_pairs,
        live_pairs=live_pairs,
    )
    _require(
        not required or summary["complete"],
        "live SkillTree dependency parity failed: "
        f"{summary['matchedDependencies']}/{summary['expectedDependencies']} "
        "exported dependencies are live; "
        f"missing={summary['missingDependencies']}, "
        f"extra={summary['extraDependencies']}; "
        f"examples={summary['missingDependencyExamples']}",
    )
    return summary


def _validate_live_admin_count(
    *,
    skilltree_url: str,
    project_root: Path,
    project_id: str,
    expected_skills: int,
    local_state_dir: Path | None,
    timeout: float,
    required: bool,
) -> dict[str, Any]:
    """Optionally verify the live SkillTree admin project count."""
    from src.skilltree.client import SkillTreeClientError
    from src.skilltree.local_auth import (
        DEFAULT_LOCAL_STATE_DIR,
        LocalSkillTreeAuthError,
        SkillTreeSessionClient,
        load_local_state,
    )

    state_dir = local_state_dir or project_root / DEFAULT_LOCAL_STATE_DIR
    state = load_local_state(state_dir)
    if state is None:
        _require(
            not required,
            f"local SkillTree auth state not found at {state_dir}",
        )
        return {
            "checked": False,
            "reason": "local SkillTree auth state not found",
        }
    _require(
        state.project_id == project_id,
        f"local SkillTree auth state is for {state.project_id!r}, not {project_id!r}",
    )
    _require(
        state.skilltree_url.rstrip("/") == skilltree_url.rstrip("/"),
        "local SkillTree auth state URL does not match the validated SkillTree URL",
    )
    client = SkillTreeSessionClient(
        skilltree_url,
        project_id,
        timeout=max(timeout, 30.0),
    )
    try:
        client.login(state.admin_username, state.admin_password)
        live_skills = client.live_skill_count()
    except (LocalSkillTreeAuthError, SkillTreeClientError) as exc:
        _require(not required, f"live SkillTree admin count check failed: {exc}")
        return {
            "checked": False,
            "reason": str(exc),
        }
    _require(
        live_skills == expected_skills,
        f"live SkillTree reports {live_skills} skills but export defines "
        f"{expected_skills}",
    )
    return {
        "checked": True,
        "skills": live_skills,
    }
