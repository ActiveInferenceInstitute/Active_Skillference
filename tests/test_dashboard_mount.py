"""Opt-in actual-browser acceptance; never substitutes a fake SDK or CLI result."""

from __future__ import annotations

import json
import os
import shutil
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path

import pytest

from src.dashboard.browser_validation import (
    BrowserDisplayError,
    browser_receipt_complete,
    display_probe,
    validate_dashboard_browser,
)
from src.dashboard.config import make_dashboard_config
from src.dashboard.server import make_dashboard_handler


@pytest.fixture
def authorized_browser():
    url = os.environ.get("ASF_TEST_DASHBOARD_URL", "")
    if not url:
        pytest.skip(
            "set ASF_TEST_DASHBOARD_URL only after live browser acceptance is authorized"
        )
    command = os.environ.get("ASF_TEST_BROWSER_COMMAND", "chrome-devtools-axi")
    if shutil.which(command) is None:
        pytest.skip(f"existing browser CLI unavailable: {command}")
    return url, command


@pytest.mark.requires_browser
def test_actual_official_project_subject_and_quiz_are_mounted(
    authorized_browser,
) -> None:
    url, command = authorized_browser
    receipt = validate_dashboard_browser(
        url, browser_command=command, timeout=60, settle_seconds=1
    )
    assert browser_receipt_complete(receipt)
    quiz = next(view for view in receipt["views"] if view["kind"] == "quiz")
    observed = display_probe(browser_command=command, timeout=10)
    assert observed["state"] == "ready" and observed["route"] == quiz["route"]
    assert observed["frameVisible"] is True and observed["busy"] is False
    assert observed["projectId"] == receipt["projectId"]
    assert observed["dashboardInstanceId"] == receipt["dashboardInstanceId"]
    assert observed["exportContentDigest"] == receipt["exportContentDigest"]


@pytest.mark.requires_browser
def test_real_dashboard_fallback_cannot_pass_mounted_view_proof(
    tmp_path: Path,
    httpserver,
    content_project,
    authorized_browser,
) -> None:
    _authorized_url, command = authorized_browser
    export = tmp_path / "output" / "data" / "skilltree_project.json"
    export.parent.mkdir(parents=True)
    export.write_text(json.dumps(content_project.to_export_dict()), encoding="utf-8")
    httpserver.expect_request("/public/status").respond_with_json({"status": "OK"})
    config = make_dashboard_config(
        project_root=tmp_path,
        skilltree_url=httpserver.url_for(""),
        project_id="p",
        project_name="Project",
        host="127.0.0.1",
        port=8765,
        skills_client_module_url="/assets/missing-official-module.js",
        local_auth_enabled=False,
    )
    server = ThreadingHTTPServer(("127.0.0.1", 0), make_dashboard_handler(config))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    url = f"http://127.0.0.1:{server.server_address[1]}"
    try:
        with pytest.raises(BrowserDisplayError, match="fallback|did not reach ready"):
            validate_dashboard_browser(
                url, browser_command=command, timeout=15, settle_seconds=0
            )
        observed = display_probe(browser_command=command, timeout=5)
        assert observed["state"] != "ready"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


@pytest.mark.parametrize("timeout", [0.0, -1.0, float("nan"), float("inf")])
def test_invalid_browser_timeout_is_rejected_before_network_or_cli(
    timeout: float,
) -> None:
    with pytest.raises(BrowserDisplayError, match="finite and positive"):
        validate_dashboard_browser("not a URL", timeout=timeout)
