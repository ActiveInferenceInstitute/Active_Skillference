from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.dashboard.artifacts import EXPECTED_ARTIFACT_COUNT
from src.dashboard.live_validation import (
    LiveSkillTreeDashboardError,
    _fetch_json,
    validate_live_skilltree_dashboard,
)
from src.project_identity import SKILLTREE_PROJECT_ID, SKILLTREE_PROJECT_NAME


def _write_project_export(project_root: Path, payload: object | None = None) -> Path:
    project_path = project_root / "output" / "data" / "skilltree_project.json"
    project_path.parent.mkdir(parents=True, exist_ok=True)
    export = (
        payload
        if payload is not None
        else {
            "projectId": SKILLTREE_PROJECT_ID,
            "name": SKILLTREE_PROJECT_NAME,
            "subjects": [
                {
                    "subjectId": "sub_live_validation",
                    "name": "Live Validation",
                    "skills": [{"skillId": "live_validation_01"}],
                }
            ],
            "dependencies": [],
            "quizzes": [],
        }
    )
    project_path.write_text(json.dumps(export), encoding="utf-8")
    return project_path


def _serve_dashboard_payloads(
    httpserver,  # type: ignore[no-untyped-def]
    *,
    counts: dict[str, int] | None = None,
    token_payload: dict[str, object] | None = None,
) -> str:
    base_url = httpserver.url_for("").rstrip("/")
    project_counts = counts or {
        "subjects": 1,
        "skills": 1,
        "dependencies": 0,
        "quizzes": 0,
    }
    httpserver.expect_request("/public/status").respond_with_json({"status": "OK"})
    httpserver.expect_request("/api/status").respond_with_json(
        {
            "project": {
                "projectId": SKILLTREE_PROJECT_ID,
                "name": SKILLTREE_PROJECT_NAME,
                "dependencies": [],
                "counts": project_counts,
            },
            "config": {
                "skilltree": {
                    "url": base_url,
                    "authenticatorConfigured": True,
                    "localAuth": {"ready": True},
                }
            },
            "skilltree": {"available": True, "statusCode": 200},
            "courseMaterials": {
                "available": True,
                "summary": {"materialRecords": 1, "externalPointers": 1},
            },
            "artifacts": [
                {"id": f"artifact_{index}", "exists": True}
                for index in range(EXPECTED_ARTIFACT_COUNT)
            ],
        }
    )
    httpserver.expect_request("/api/course-materials").respond_with_json(
        {
            "available": True,
            "skills": {
                "live_validation_01": {
                    "externalPointers": [{"url": "https://example.test/material"}]
                }
            },
        }
    )
    if token_payload is not None:
        httpserver.expect_request("/api/skilltree/token").respond_with_json(
            token_payload
        )
    return base_url


def test_live_validator_rejects_non_object_skilltree_status(
    tmp_path: Path,
    httpserver,  # type: ignore[no-untyped-def]
) -> None:
    _write_project_export(tmp_path)
    base_url = httpserver.url_for("").rstrip("/")
    httpserver.expect_request("/public/status").respond_with_json(["not", "object"])

    with pytest.raises(LiveSkillTreeDashboardError, match="not an object"):
        validate_live_skilltree_dashboard(
            dashboard_url=base_url,
            skilltree_url=base_url,
            project_root=tmp_path,
            require_token=False,
        )


def test_live_validator_rejects_missing_project_export(
    tmp_path: Path,
    httpserver,  # type: ignore[no-untyped-def]
) -> None:
    base_url = _serve_dashboard_payloads(httpserver)

    with pytest.raises(LiveSkillTreeDashboardError, match="project export is missing"):
        validate_live_skilltree_dashboard(
            dashboard_url=base_url,
            skilltree_url=base_url,
            project_root=tmp_path,
            require_token=False,
        )


def test_live_validator_rejects_malformed_project_export_shape(
    tmp_path: Path,
    httpserver,  # type: ignore[no-untyped-def]
) -> None:
    _write_project_export(tmp_path, {"subjects": {"not": "a list"}})
    base_url = _serve_dashboard_payloads(httpserver)

    with pytest.raises(
        LiveSkillTreeDashboardError,
        match="SkillTree project subjects must be a list",
    ):
        validate_live_skilltree_dashboard(
            dashboard_url=base_url,
            skilltree_url=base_url,
            project_root=tmp_path,
            require_token=False,
        )


def test_live_validator_rejects_token_secret_leak(
    tmp_path: Path,
    httpserver,  # type: ignore[no-untyped-def]
) -> None:
    _write_project_export(tmp_path)
    base_url = _serve_dashboard_payloads(
        httpserver,
        token_payload={
            "access_token": "opaque-token",
            "client_secret": "do-not-expose",
        },
    )

    with pytest.raises(
        LiveSkillTreeDashboardError,
        match="token exchange exposed client_secret",
    ):
        validate_live_skilltree_dashboard(
            dashboard_url=base_url,
            skilltree_url=base_url,
            project_root=tmp_path,
        )


def test_fetch_json_rejects_non_http_scheme() -> None:
    with pytest.raises(LiveSkillTreeDashboardError, match="only http/https URLs"):
        _fetch_json("file:///etc/passwd", timeout=1.0)
