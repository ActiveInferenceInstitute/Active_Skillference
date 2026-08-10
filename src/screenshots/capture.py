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
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from src.artifacts.json_io import write_json_artifact
from src.net_guard import NonHttpUrlError, require_http_url
from src.screenshots.manifest import (
    SCREENSHOT_PROVENANCE_FILENAME,
    VIEWPORT_HEIGHT,
    VIEWPORT_WIDTH,
    ScreenshotView,
    screenshot_views,
)

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


def _fetch_json(url: str, *, timeout: float) -> dict[str, Any]:
    try:
        require_http_url(url, context="dashboard status read for screenshot capture")
    except NonHttpUrlError as exc:
        raise ScreenshotCaptureError(str(exc)) from exc
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, ValueError) as exc:
        raise ScreenshotCaptureError(f"could not read {url}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ScreenshotCaptureError(f"{url} did not return a JSON object")
    return payload


def capture_context(settings: CaptureSettings) -> dict[str, Any]:
    """Return the system state the capture run is evidence of."""
    status = _fetch_json(
        f"{settings.dashboard_url.rstrip('/')}/api/status",
        timeout=_STATUS_TIMEOUT_SECONDS,
    )
    project_counts = status.get("project", {}).get("counts", {})
    live = status.get("liveSkilltree", {})
    proof_path = (
        settings.project_root
        / ".active_skillference_local"
        / "full_app_stack_proof.json"
    )
    proof_mode = "not recorded"
    if proof_path.is_file():
        try:
            proof = json.loads(proof_path.read_text(encoding="utf-8"))
            proof_mode = str(proof.get("mode", "not recorded"))
        except (OSError, ValueError):
            proof_mode = "unreadable proof artifact"
    return {
        "dashboardUrl": settings.dashboard_url,
        "skilltreeUrl": str(
            status.get("config", {}).get("skilltree", {}).get("url", "")
        ),
        "skilltreeAvailable": bool(status.get("skilltree", {}).get("available")),
        "viewport": {
            "width": settings.viewport_width,
            "height": settings.viewport_height,
        },
        "exportedCounts": {
            "skills": project_counts.get("skills", 0),
            "subjects": project_counts.get("subjects", 0),
            "dependencies": project_counts.get("dependencies", 0),
            "quizzes": project_counts.get("quizzes", 0),
        },
        "liveDependencies": {
            "checked": bool(live.get("checked")),
            "matched": live.get("matchedDependencies"),
            "expected": live.get("expectedDependencies"),
            "complete": bool(live.get("complete")),
        },
        "fullAppStackProofMode": proof_mode,
        "evidenceKind": (
            "captured browser recording of a live system; pixels are not "
            "reproducible byte-for-byte and are not a deterministic render"
        ),
    }


def _capture_one(
    view: ScreenshotView,
    settings: CaptureSettings,
    staging_dir: Path,
) -> dict[str, Any]:
    _run([settings.browser_command, "eval", view.setup_js])
    _run([settings.browser_command, "wait", str(view.settle_ms)])
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
    }


def capture_screenshots(settings: CaptureSettings) -> dict[str, Any]:
    """Capture every manifest view and write the registry plus provenance record."""
    settings.output_dir.mkdir(parents=True, exist_ok=True)
    restarted = ensure_browser_ready(browser_command=settings.browser_command)
    context = capture_context(settings)
    _run(
        [
            settings.browser_command,
            "resize",
            str(settings.viewport_width),
            str(settings.viewport_height),
        ]
    )
    _run([settings.browser_command, "open", settings.dashboard_url])
    # The page defers the live-parity read, so give the swap-in time to land
    # before the first capture claims a parity number.
    _run([settings.browser_command, "wait", "12000"])

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
