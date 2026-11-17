"""Drive a real browser to capture learner-dashboard evidence screenshots.

The capture talks to the same ``chrome-devtools-axi`` CLI the live-stack proofs
use, against a dashboard the caller is already running. It is deliberately a
recording, not a render: each image is stamped with the dashboard URL, viewport,
live SkillTree counts, and full-app proof mode in force at capture time, so a
reader can tell which system state the pixels are evidence of.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from src.artifacts.json_io import write_json_artifact
from src.dashboard.browser_validation import (
    BrowserDisplayError,
    browser_receipt_complete,
    display_probe,
    wait_for_official_display,
)
from src.net_guard import NonHttpUrlError, is_loopback_host, require_http_url
from src.screenshots.manifest import (
    SCREENSHOT_PROVENANCE_FILENAME,
    VIEWPORT_HEIGHT,
    VIEWPORT_WIDTH,
    ScreenshotView,
    screenshot_views,
)
from src.skilltree.local_auth_state import LocalSkillTreeAuthError, _skilltree_origin

DEFAULT_BROWSER_COMMAND = "chrome-devtools-axi"
#: The browser automation server writes only inside this root on this platform.
DEFAULT_STAGING_ROOT = "/tmp"
_COMMAND_TIMEOUT_SECONDS = 120.0
_STATUS_TIMEOUT_SECONDS = 60.0


class ScreenshotCaptureError(RuntimeError):
    """Raised when a capture cannot be completed or proven."""


@dataclass(frozen=True)
class CaptureSettings:
    """Inputs for one capture run."""

    dashboard_url: str
    output_dir: Path
    project_root: Path
    browser_command: str = DEFAULT_BROWSER_COMMAND
    viewport_width: int = VIEWPORT_WIDTH
    viewport_height: int = VIEWPORT_HEIGHT
    #: Directory the browser automation server is permitted to write to.
    staging_root: Path = Path(DEFAULT_STAGING_ROOT)
    proof_path: Path | None = None


def _run(
    command: list[str],
    *,
    timeout: float = _COMMAND_TIMEOUT_SECONDS,
) -> subprocess.CompletedProcess[str]:
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError as exc:
        raise ScreenshotCaptureError(
            f"required browser command not found: {command[0]}"
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise ScreenshotCaptureError(
            f"browser command timed out: {' '.join(command)}"
        ) from exc
    combined = f"{result.stdout}\n{result.stderr}"
    if result.returncode != 0 or "code: TIMEOUT" in combined:
        raise ScreenshotCaptureError(
            f"browser command failed ({result.returncode}): {' '.join(command)}\n"
            f"{combined.strip()[-800:]}"
        )
    return result


def ensure_browser_ready(*, browser_command: str) -> bool:
    """Return whether the browser session answered, restarting it once if not.

    A long-lived automation session can go stale and then time out on every
    command. Recovering here keeps a capture run from failing for a reason that
    has nothing to do with the dashboard under test.
    """
    try:
        _run([browser_command, "pages"], timeout=30)
        return False
    except ScreenshotCaptureError:
        pass
    for verb in ("stop", "start"):
        subprocess.run(
            [browser_command, verb],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
    _run([browser_command, "pages"], timeout=30)
    return True


def _capture_url(url: str) -> str:
    try:
        parsed = urllib.parse.urlsplit(url)
    except ValueError as exc:
        raise ScreenshotCaptureError("capture URL is invalid") from exc
    if (
        parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
    ):
        raise ScreenshotCaptureError(
            "capture requires a credential-free dashboard base URL without query or fragment"
        )
    try:
        require_http_url(url, context="screenshot capture")
        port = parsed.port
    except (NonHttpUrlError, ValueError) as exc:
        raise ScreenshotCaptureError(
            "capture requires an absolute loopback HTTP(S) URL"
        ) from exc
    if not parsed.hostname or not is_loopback_host(parsed.hostname):
        raise ScreenshotCaptureError(
            "capture requires an absolute loopback HTTP(S) URL"
        )
    if port is not None and port <= 0:
        raise ScreenshotCaptureError("capture URL port is invalid")
    return url.rstrip("/")


def _capture_target(url: str) -> tuple[tuple[str, str, int], str]:
    normalized = _capture_url(url)
    return _skilltree_origin(normalized), urllib.parse.urlsplit(normalized).path.rstrip(
        "/"
    ) or "/"


class _LoopbackCaptureRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(
        self,
        req: urllib.request.Request,
        fp: Any,
        code: int,
        msg: str,
        headers: Any,
        newurl: str,
    ) -> urllib.request.Request | None:
        _capture_url(newurl)
        if _skilltree_origin(req.full_url) != _skilltree_origin(newurl):
            raise ScreenshotCaptureError(
                "capture redirect changed the requested origin"
            )
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _capture_opener() -> urllib.request.OpenerDirector:
    return urllib.request.build_opener(_LoopbackCaptureRedirect)


def _fetch_json(url: str, *, timeout: float) -> dict[str, Any]:
    _capture_url(url)
    try:
        with _capture_opener().open(url, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, ValueError) as exc:
        raise ScreenshotCaptureError(f"could not read {url}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ScreenshotCaptureError(f"{url} did not return a JSON object")
    return payload


def capture_context(
    settings: CaptureSettings,
    *,
    browser_probe: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Observe current status and associate only an explicit, matching successful proof."""
    dashboard_url = _capture_url(settings.dashboard_url)
    status = _fetch_json(f"{dashboard_url}/api/status", timeout=_STATUS_TIMEOUT_SECONDS)
    project, config, live = (
        status.get("project"),
        status.get("config"),
        status.get("liveSkilltree"),
    )
    service = status.get("skilltree")
    if not (
        isinstance(project, dict)
        and isinstance(config, dict)
        and isinstance(live, dict)
        and isinstance(service, dict)
    ):
        raise ScreenshotCaptureError(
            "dashboard project/config/live state must contain objects"
        )
    project_counts = project.get("counts", {})
    public_project, skilltree = config.get("project", {}), config.get("skilltree", {})
    if not all(
        isinstance(value, dict) for value in (project_counts, public_project, skilltree)
    ):
        raise ScreenshotCaptureError(
            "dashboard project counts/identity/target must contain objects"
        )
    instance_id = status.get("instanceId")
    digest = project.get("exportContentDigest")
    project_id = public_project.get("id")
    skilltree_url = str(skilltree.get("url", ""))
    if browser_probe is not None:
        try:
            browser_matches = _capture_target(
                str(browser_probe.get("url", ""))
            ) == _capture_target(dashboard_url)
        except (ScreenshotCaptureError, LocalSkillTreeAuthError, ValueError):
            browser_matches = False
        if (
            browser_probe.get("state") != "ready"
            or browser_probe.get("dashboardInstanceId") != instance_id
            or browser_probe.get("exportContentDigest") != digest
            or browser_probe.get("projectId") != project_id
            or not browser_matches
        ):
            raise ScreenshotCaptureError(
                "browser capture state does not match current dashboard content"
            )
    association = _proof_association(
        settings,
        instance_id=instance_id,
        digest=digest,
        project_id=project_id,
        skilltree_url=skilltree_url,
        browser_probe=browser_probe,
    )
    content = live.get("content", {})
    return {
        "dashboardUrl": dashboard_url,
        "dashboardInstanceId": instance_id,
        "exportContentDigest": digest,
        "projectId": project_id,
        "skilltreeUrl": skilltree_url,
        "skilltreeAvailable": bool(service.get("available")),
        "viewport": {
            "width": settings.viewport_width,
            "height": settings.viewport_height,
        },
        "exportedCounts": {
            key: project_counts.get(key, 0)
            for key in ("skills", "subjects", "dependencies", "quizzes")
        },
        "liveDependencies": {
            "checked": live.get("checked") is True,
            "matched": live.get("matchedDependencies"),
            "expected": live.get("expectedDependencies"),
            "complete": live.get("complete") is True,
        },
        "liveContent": {
            key: content.get(key)
            for key in ("checked", "complete", "exportContentDigest")
        }
        if isinstance(content, dict)
        else {"checked": False},
        "officialDisplay": {
            key: browser_probe.get(key)
            for key in ("state", "route", "frameUrl", "frameVisible")
        }
        if browser_probe is not None
        else {"state": "unobserved"},
        "proofAssociation": association,
        "fullAppStackProofMode": association.get("mode", "not associated"),
        "evidenceKind": "captured browser recording of a live system; pixels are not reproducible byte-for-byte and are not a deterministic render",
    }


def _proof_association(
    settings: CaptureSettings,
    *,
    instance_id: Any,
    digest: Any,
    project_id: Any,
    skilltree_url: str,
    browser_probe: dict[str, Any] | None,
) -> dict[str, Any]:
    if settings.proof_path is None:
        return {"checked": False, "reason": "no explicit proof path"}
    path = settings.proof_path
    if not path.is_absolute():
        path = settings.project_root / path
    try:
        raw = path.read_bytes()
        proof = json.loads(raw)
    except (OSError, ValueError) as exc:
        return {
            "checked": False,
            "reason": f"proof is unreadable: {type(exc).__name__}",
        }
    if not isinstance(proof, dict) or proof.get("proofVersion") != 2:
        return {
            "checked": False,
            "reason": "historical/unsupported proof schema is unassociated",
        }
    content = proof.get("liveContent", {})
    browser = proof.get("browserConsole", {})
    try:
        same_targets = _capture_target(
            str(proof.get("dashboardUrl", ""))
        ) == _capture_target(settings.dashboard_url) and _skilltree_origin(
            str(proof.get("skilltreeUrl", ""))
        ) == _skilltree_origin(skilltree_url)
    except (ScreenshotCaptureError, LocalSkillTreeAuthError, ValueError):
        same_targets = False
    complete = (
        proof.get("ok") is True
        and same_targets
        and proof.get("mode") in ("app-ready", "full-parity")
        and isinstance(instance_id, str)
        and bool(instance_id)
        and isinstance(digest, str)
        and len(digest) == 64
        and proof.get("runId") == proof.get("dashboardInstanceId") == instance_id
        and proof.get("exportContentDigest") == digest
        and proof.get("projectId") == project_id
        and isinstance(content, dict)
        and content.get("checked") is True
        and content.get("complete") is True
        and content.get("exportContentDigest") == digest
        and browser_probe is not None
        and browser_receipt_complete(browser)
        and browser.get("dashboardInstanceId") == instance_id
        and browser.get("exportContentDigest") == digest
        and browser.get("projectId") == project_id
    )
    if proof.get("mode") == "full-parity":
        dependencies = proof.get("liveDependencies", {})
        complete = (
            complete
            and isinstance(dependencies, dict)
            and dependencies.get("checked") is True
            and dependencies.get("complete") is True
        )
    if not complete:
        return {
            "checked": False,
            "reason": "proof does not match this successful current browser/content/instance state",
        }
    return {
        "checked": True,
        "mode": proof["mode"],
        "runId": proof["runId"],
        "proofSha256": hashlib.sha256(raw).hexdigest(),
        "proofPath": str(path),
    }


def _capture_one(
    view: ScreenshotView,
    settings: CaptureSettings,
    staging_dir: Path,
) -> dict[str, Any]:
    _run([settings.browser_command, "eval", view.setup_js])
    _run([settings.browser_command, "wait", str(view.settle_ms)])
    try:
        probe = display_probe(browser_command=settings.browser_command, timeout=30.0)
    except BrowserDisplayError as exc:
        raise ScreenshotCaptureError(str(exc)) from exc
    context = capture_context(settings, browser_probe=probe)
    # The browser automation server runs under its own filesystem sandbox and
    # silently reports success while writing nothing outside /tmp, so captures
    # are staged there and moved into the tracked tree by this process.
    staged = staging_dir / view.filename
    _run([settings.browser_command, "screenshot", str(staged)])
    if not staged.is_file():
        raise ScreenshotCaptureError(
            f"browser reported success but {staged} was not written; the browser "
            "automation server may not be permitted to write to that directory"
        )
    try:
        after = display_probe(browser_command=settings.browser_command, timeout=30.0)
    except BrowserDisplayError as exc:
        raise ScreenshotCaptureError(str(exc)) from exc
    if any(
        after.get(key) != probe.get(key)
        for key in (
            "state",
            "route",
            "url",
            "dashboardInstanceId",
            "exportContentDigest",
        )
    ):
        raise ScreenshotCaptureError(
            "browser state changed while the screenshot was being recorded"
        )
    target = settings.output_dir / view.filename
    target.write_bytes(staged.read_bytes())
    staged.unlink()
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    return {
        "viewId": view.view_id,
        "label": view.label,
        "filename": view.filename,
        "settleMs": view.settle_ms,
        "sha256": digest,
        "bytes": target.stat().st_size,
        "context": context,
    }


def capture_screenshots(settings: CaptureSettings) -> dict[str, Any]:
    """Capture every manifest view and write the registry plus provenance record."""
    dashboard_url = _capture_url(settings.dashboard_url)
    with _capture_opener().open(
        dashboard_url, timeout=_STATUS_TIMEOUT_SECONDS
    ) as response:
        _capture_url(response.geturl())
    restarted = ensure_browser_ready(browser_command=settings.browser_command)
    _run(
        [
            settings.browser_command,
            "resize",
            str(settings.viewport_width),
            str(settings.viewport_height),
        ]
    )
    _run([settings.browser_command, "open", settings.dashboard_url])
    initial = _fetch_json(
        f"{dashboard_url}/api/status", timeout=_STATUS_TIMEOUT_SECONDS
    )
    try:
        probe = wait_for_official_display(
            browser_command=settings.browser_command,
            dashboard_url=dashboard_url,
            skilltree_url=str(initial["config"]["skilltree"]["url"]),
            project_id=str(initial["config"]["project"]["id"]),
            route="/",
            dashboard_instance_id=str(initial["instanceId"]),
            export_digest=str(initial["project"]["exportContentDigest"]),
            timeout=_STATUS_TIMEOUT_SECONDS,
        )
    except (BrowserDisplayError, KeyError, TypeError) as exc:
        raise ScreenshotCaptureError(
            "official display did not provide capture-ready identity"
        ) from exc
    context = capture_context(settings, browser_probe=probe)
    settings.output_dir.mkdir(parents=True, exist_ok=True)

    staging_dir = Path(settings.staging_root) / f"asf-capture-{os.getpid()}"
    staging_dir.mkdir(parents=True, exist_ok=True)
    try:
        captures = [
            _capture_one(view, settings, staging_dir) for view in screenshot_views()
        ]
    finally:
        shutil.rmtree(staging_dir, ignore_errors=True)

    provenance = {
        "capturedAt": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "browserCommand": settings.browser_command,
        "browserSessionRestarted": restarted,
        "context": context,
        "captures": captures,
    }
    write_json_artifact(
        settings.output_dir / SCREENSHOT_PROVENANCE_FILENAME,
        provenance,
    )
    return provenance
