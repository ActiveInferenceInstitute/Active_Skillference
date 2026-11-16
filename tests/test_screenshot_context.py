"""Association-level fixtures are not browser proof; HTTP and proof files are real."""

from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from pathlib import Path

import pytest
from pytest_httpserver import HTTPServer

from src.screenshots.capture import (
    CaptureSettings,
    ScreenshotCaptureError,
    _capture_target,
    _capture_url,
    capture_context,
    capture_screenshots,
)


def _case(httpserver, tmp_path: Path):
    url = httpserver.url_for("").rstrip("/")
    digest = hashlib.sha256(b"private-export-fixture").hexdigest()
    instance = "capture-run-fixture"
    status = {
        "instanceId": instance,
        "project": {"exportContentDigest": digest, "counts": {"skills": 1, "subjects": 1, "dependencies": 0, "quizzes": 1}},
        "config": {"project": {"id": "p"}, "skilltree": {"url": url}},
        "skilltree": {"available": True},
        "liveSkilltree": {"checked": True, "complete": True, "expectedDependencies": 0, "matchedDependencies": 0,
                          "content": {"checked": True, "complete": True, "exportContentDigest": digest}},
    }
    httpserver.expect_request("/api/status", method="GET").respond_with_json(status)
    browser = {
        "state": "ready", "url": url, "projectId": "p", "route": "/",
        "dashboardInstanceId": instance, "exportContentDigest": digest,
        "frameUrl": url + "/skills-display/p", "frameVisible": True, "busy": False,
    }
    receipt = {
        "checked": True, "ok": True, "projectId": "p", "dashboardInstanceId": instance,
        "exportContentDigest": digest,
        "views": [{"kind": kind, "route": route, "state": "ready", "visibleContentChecked": True}
                  for kind, route in (("project", "/"), ("subject", "/subjects/s"), ("quiz", "/subjects/s/skills/k/quizzes/q"))],
    }
    proof = {
        "proofVersion": 2, "ok": True, "mode": "full-parity", "dashboardUrl": url, "skilltreeUrl": url,
        "projectId": "p", "runId": instance, "dashboardInstanceId": instance, "exportContentDigest": digest,
        "liveContent": {"checked": True, "complete": True, "exportContentDigest": digest},
        "liveDependencies": {"checked": True, "complete": True}, "browserConsole": receipt,
    }
    path = tmp_path / "explicit-proof.json"
    settings = CaptureSettings(url, tmp_path / "captures", tmp_path, proof_path=path)
    return settings, status, browser, proof


def test_explicit_matching_v2_proof_is_bound_to_real_capture_time_status(httpserver, tmp_path: Path) -> None:
    settings, _status, browser, proof = _case(httpserver, tmp_path)
    settings.proof_path.write_text(json.dumps(proof), encoding="utf-8")
    raw = settings.proof_path.read_bytes()
    context = capture_context(settings, browser_probe=browser)
    association = context["proofAssociation"]
    assert association["checked"] is True and association["mode"] == "full-parity"
    assert association["runId"] == context["dashboardInstanceId"]
    assert association["proofSha256"] == hashlib.sha256(raw).hexdigest()
    assert context["exportContentDigest"] == proof["exportContentDigest"]
    assert settings.proof_path.read_bytes() == raw


@pytest.mark.parametrize("damage", ["failed", "legacy", "url", "skilltree", "project", "digest", "instance", "content", "browser", "dependencies"])
def test_unrelated_or_incomplete_proof_cannot_certify_current_capture(httpserver, tmp_path: Path, damage: str) -> None:
    settings, _status, browser, proof = _case(httpserver, tmp_path)
    if damage == "failed":
        proof["ok"] = False
    elif damage == "legacy":
        proof["proofVersion"] = 1
    elif damage == "url":
        proof["dashboardUrl"] += "/another-dashboard"
    elif damage == "skilltree":
        proof["skilltreeUrl"] = "http://127.0.0.1:1"
    elif damage == "project":
        proof["projectId"] = "other"
    elif damage == "digest":
        proof["exportContentDigest"] = "b" * 64
    elif damage == "instance":
        proof["dashboardInstanceId"] = "different-run"
    elif damage == "content":
        proof["liveContent"]["complete"] = False
    elif damage == "browser":
        proof["browserConsole"]["checked"] = False
    else:
        proof["liveDependencies"]["complete"] = False
    settings.proof_path.write_text(json.dumps(proof), encoding="utf-8")
    before = settings.proof_path.read_bytes()
    context = capture_context(settings, browser_probe=browser)
    assert context["proofAssociation"]["checked"] is False
    assert context["fullAppStackProofMode"] == "not associated"
    assert settings.proof_path.read_bytes() == before


def test_missing_malformed_or_implicit_proof_is_unassociated_without_rewriting_it(httpserver, tmp_path: Path) -> None:
    settings, _status, browser, proof = _case(httpserver, tmp_path)
    assert capture_context(settings, browser_probe=browser)["proofAssociation"]["checked"] is False
    settings.proof_path.write_text("not JSON", encoding="utf-8")
    assert capture_context(settings, browser_probe=browser)["proofAssociation"]["checked"] is False
    assert settings.proof_path.read_text(encoding="utf-8") == "not JSON"
    settings.proof_path.write_text(json.dumps(proof), encoding="utf-8")
    assert capture_context(replace(settings, proof_path=None), browser_probe=browser)["proofAssociation"]["checked"] is False
    assert capture_context(settings)["proofAssociation"]["checked"] is False


@pytest.mark.parametrize("field,value", [("state", "fallback"), ("dashboardInstanceId", "old"), ("exportContentDigest", "c" * 64), ("projectId", "other"), ("url", "not a URL")])
def test_browser_snapshot_must_match_current_status(httpserver, tmp_path: Path, field: str, value: str) -> None:
    settings, _status, browser, _proof = _case(httpserver, tmp_path)
    browser[field] = value
    with pytest.raises(ScreenshotCaptureError, match="does not match"):
        capture_context(settings, browser_probe=browser)
    assert not settings.output_dir.exists()


@pytest.mark.parametrize("url", ["file:///tmp/not-a-dashboard", "https://example.invalid", "http://user:password@127.0.0.1", "http://127.0.0.1/?query=yes", "http://127.0.0.1/#fragment"])
def test_capture_url_admission_is_pure_and_rejects_nonlocal_or_credential_bearing_targets(url: str) -> None:
    with pytest.raises(ScreenshotCaptureError):
        _capture_url(url)


def test_capture_target_comparison_normalizes_origin_and_default_port_without_merging_paths() -> None:
    assert _capture_target("HTTP://LOCALHOST:80/") == _capture_target("http://localhost")
    assert _capture_target("http://localhost/a") != _capture_target("http://localhost/b")


def test_off_origin_loopback_redirect_is_refused_before_browser_or_output_creation(httpserver, tmp_path: Path) -> None:
    unrelated = HTTPServer(host="127.0.0.1", port=0)
    unrelated.start()
    try:
        httpserver.expect_request("/", method="GET").respond_with_data(
            "", status=302, headers={"Location": unrelated.url_for("/")},
        )
        settings = CaptureSettings(httpserver.url_for(""), tmp_path / "captures", tmp_path)
        with pytest.raises(ScreenshotCaptureError, match="changed the requested origin"):
            capture_screenshots(settings)
        assert unrelated.log == []
        assert not settings.output_dir.exists()
    finally:
        unrelated.stop()
