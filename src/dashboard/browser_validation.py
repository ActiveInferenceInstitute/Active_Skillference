"""Real-browser proof of official SkillTree routes, not merely an empty console."""

from __future__ import annotations

import html
import math
import re
import time
from collections.abc import Mapping
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from src.dashboard.live_validation import LiveSkillTreeDashboardError, _fetch_json
from src.skilltree.form_login_core import SkillTreeFormLoginError, parse_axi_result
from src.skilltree.form_login_validation import run_browser_command
from src.skilltree.local_auth_state import LocalSkillTreeAuthError, _skilltree_origin

_ALLOWED_ERROR_PATTERNS = (
    re.compile(r"projects/Inception/.*token.*401", re.IGNORECASE),
    re.compile(r"Unable to authenticate.*Inception", re.IGNORECASE),
)

DISPLAY_PROBE_JS = r"""(activate = false) => {
  const container = document.getElementById('skills-client-container');
  if (!container) return {state: 'pending', url: location.href};
  const panel = container.closest('.panel');
  const tab = panel && [...document.querySelectorAll('.tab')].find(item => item.dataset.panel === panel.id);
  if (activate && tab) tab.click();
  const frame = container.querySelector('iframe');
  const bounds = frame && frame.getBoundingClientRect();
  return {
    state: container.dataset.mountState || 'pending',
    url: location.href,
    projectId: container.dataset.projectId || '',
    route: container.dataset.route || '',
    dashboardInstanceId: container.dataset.instanceId || '',
    exportContentDigest: container.dataset.exportContentDigest || '',
    frameUrl: frame ? frame.src : '',
    frameVisible: !!bounds && bounds.width > 0 && bounds.height > 0,
    busy: container.getAttribute('aria-busy') === 'true'
  };
}"""


class BrowserDisplayError(RuntimeError):
    """The real official frame could not prove the requested learner view."""


def unexpected_errors(errors: list[str]) -> list[str]:
    return [
        error
        for error in errors
        if not any(pattern.search(error) for pattern in _ALLOWED_ERROR_PATTERNS)
    ]


def browser_output(
    arguments: list[str], *, browser_command: str, timeout: float
) -> str:
    try:
        result = run_browser_command([browser_command, *arguments], timeout=timeout)
    except SkillTreeFormLoginError as exc:
        raise BrowserDisplayError(str(exc)) from exc
    if re.search(
        r"(?im)^\s*(?:code:\s*(?:TIMEOUT|ERROR)|isError:\s*true)\s*$", result.stdout
    ):
        raise BrowserDisplayError("browser command returned an explicit tool failure")
    return result.stdout


def display_probe(
    *,
    browser_command: str,
    timeout: float,
    activate: bool = False,
) -> dict[str, Any]:
    script = f"() => ({DISPLAY_PROBE_JS})({'true' if activate else 'false'})"
    stdout = browser_output(
        ["eval", script], browser_command=browser_command, timeout=timeout
    )
    try:
        value = parse_axi_result(stdout)
    except SkillTreeFormLoginError as exc:
        raise BrowserDisplayError(str(exc)) from exc
    if not isinstance(value, dict) or value.get("isError") is True:
        raise BrowserDisplayError("browser display probe returned no state object")
    return value


def wait_for_official_display(
    *,
    browser_command: str,
    dashboard_url: str,
    skilltree_url: str,
    project_id: str,
    route: str,
    timeout: float = 45.0,
    dashboard_instance_id: str | None = None,
    export_digest: str | None = None,
) -> dict[str, Any]:
    if not math.isfinite(timeout) or timeout <= 0:
        raise BrowserDisplayError(
            "browser readiness timeout must be finite and positive"
        )
    deadline = time.monotonic() + timeout
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise BrowserDisplayError(
                f"official SkillTree display did not reach ready route {route!r}"
            )
        probe = display_probe(
            browser_command=browser_command,
            timeout=min(remaining, 30.0),
            activate=True,
        )
        if _origin(str(probe.get("url", ""))) != _origin(dashboard_url):
            raise BrowserDisplayError(
                "browser navigated away from the requested dashboard origin"
            )
        if probe.get("state") == "fallback":
            raise BrowserDisplayError(
                "official SkillTree display is in fallback, not mounted"
            )
        if probe.get("state") == "ready" and probe.get("route") == route:
            if (
                probe.get("projectId") != project_id
                or _origin(str(probe.get("frameUrl", ""))) != _origin(skilltree_url)
                or (
                    dashboard_instance_id is not None
                    and probe.get("dashboardInstanceId") != dashboard_instance_id
                )
                or (
                    export_digest is not None
                    and probe.get("exportContentDigest") != export_digest
                )
            ):
                raise BrowserDisplayError(
                    "official frame identity or export association is invalid"
                )
            if probe.get("busy") is False and probe.get("frameVisible") is True:
                return probe
        time.sleep(min(0.25, max(0.0, deadline - time.monotonic())))


def _view_contracts(status: Mapping[str, Any]) -> tuple[str, str, list[dict[str, str]]]:
    config = status.get("config", {})
    project = status.get("project", {})
    if (
        not isinstance(config, Mapping)
        or not isinstance(project, Mapping)
        or not project.get("available")
    ):
        raise BrowserDisplayError("dashboard has no available exported project")
    identity = config.get("project", {})
    if not isinstance(identity, Mapping) or not isinstance(identity.get("id"), str):
        raise BrowserDisplayError("dashboard project identity is unavailable")
    project_id = identity["id"]
    skilltree = config.get("skilltree", {})
    if not isinstance(skilltree, Mapping) or not isinstance(skilltree.get("url"), str):
        raise BrowserDisplayError("SkillTree target is unavailable")
    quizzes = {
        quiz["quizId"]: quiz
        for quiz in project.get("quizzes", [])
        if isinstance(quiz, Mapping) and isinstance(quiz.get("quizId"), str)
    }
    for subject in project.get("subjects", []):
        if not isinstance(subject, Mapping):
            continue
        for skill in subject.get("skills", []):
            if not isinstance(skill, Mapping) or skill.get("quizId") not in quizzes:
                continue
            quiz = quizzes[skill["quizId"]]
            views = [
                {
                    "kind": "project",
                    "route": "/",
                    "visibleText": str(identity.get("name", "")),
                },
                {
                    "kind": "subject",
                    "route": f"/subjects/{subject['subjectId']}",
                    "visibleText": str(subject.get("name", "")),
                },
                {
                    "kind": "quiz",
                    "route": f"/subjects/{subject['subjectId']}/skills/{skill['skillId']}/quizzes/{quiz['quizId']}",
                    "visibleText": str(quiz.get("name", "")),
                },
            ]
            if any(not view["visibleText"].strip() for view in views):
                raise BrowserDisplayError("official view contract lacks a display name")
            return project_id, skilltree["url"], views
    raise BrowserDisplayError(
        "export has no quiz-gated skill for the required official quiz proof"
    )


def validate_dashboard_browser(
    dashboard_url: str,
    *,
    browser_command: str = "chrome-devtools-axi",
    timeout: float = 45.0,
    settle_seconds: float = 5.0,
) -> dict[str, Any]:
    if not math.isfinite(timeout) or timeout <= 0:
        raise BrowserDisplayError("timeout must be finite and positive")
    if not math.isfinite(settle_seconds) or settle_seconds < 0:
        raise BrowserDisplayError("settle_seconds must be finite and non-negative")
    parsed = urlsplit(dashboard_url)
    base = urlunsplit((parsed.scheme, parsed.netloc, parsed.path.rstrip("/"), "", ""))
    try:
        status = _fetch_json(f"{base}/api/status?defer_live=1", min(timeout, 30.0))
    except LiveSkillTreeDashboardError as exc:
        raise BrowserDisplayError(str(exc)) from exc
    project_id, skilltree_url, views = _view_contracts(status)
    instance_id = status.get("instanceId")
    digest = status.get("project", {}).get("exportContentDigest")
    if (
        not isinstance(instance_id, str)
        or not instance_id
        or not isinstance(digest, str)
        or len(digest) != 64
    ):
        raise BrowserDisplayError("dashboard instance/export identity is missing")
    allowed_count = 0
    results = []
    for view in views:
        query = dict(parse_qsl(parsed.query))
        query["skillsClientDisplayPath"] = view["route"]
        url = urlunsplit(
            (parsed.scheme, parsed.netloc, parsed.path or "/", urlencode(query), "")
        )
        browser_output(["open", url], browser_command=browser_command, timeout=60.0)
        probe = wait_for_official_display(
            browser_command=browser_command,
            dashboard_url=dashboard_url,
            skilltree_url=skilltree_url,
            project_id=project_id,
            route=view["route"],
            timeout=timeout,
            dashboard_instance_id=instance_id,
            export_digest=digest,
        )
        if settle_seconds:
            time.sleep(settle_seconds)
        snapshot = browser_output(
            ["snapshot"], browser_command=browser_command, timeout=30.0
        )
        visible = " ".join(html.unescape(snapshot).split()).casefold()
        expected = " ".join(html.unescape(view["visibleText"]).split()).casefold()
        if expected not in visible:
            raise BrowserDisplayError(
                f"official {view['kind']} view lacks its expected visible content"
            )
        console = browser_output(
            ["console", "--type", "error"],
            browser_command=browser_command,
            timeout=30.0,
        )
        errors = [line.strip() for line in console.splitlines() if "[error]" in line]
        if unexpected_errors(errors):
            raise BrowserDisplayError("dashboard has unexpected browser console errors")
        allowed_count += len(errors)
        results.append(
            {
                "kind": view["kind"],
                "route": probe["route"],
                "state": "ready",
                "visibleContentChecked": True,
            }
        )
    return {
        "ok": True,
        "checked": True,
        "projectId": project_id,
        "dashboardInstanceId": instance_id,
        "exportContentDigest": digest,
        "views": results,
        "allowedConsoleErrors": allowed_count,
        "evidenceKind": "real official SDK route, visible frame and browser accessibility content",
    }


def _origin(url: str) -> tuple[str, str, int]:
    try:
        return _skilltree_origin(url)
    except LocalSkillTreeAuthError as exc:
        raise BrowserDisplayError("browser/configured origin is invalid") from exc


def browser_receipt_complete(payload: object) -> bool:
    """Require all actual official view observations; an empty console is insufficient."""
    if (
        not isinstance(payload, Mapping)
        or payload.get("ok") is not True
        or payload.get("checked") is not True
    ):
        return False
    if (
        not isinstance(payload.get("projectId"), str)
        or not payload["projectId"]
        or not isinstance(payload.get("dashboardInstanceId"), str)
        or not payload["dashboardInstanceId"]
        or not isinstance(payload.get("exportContentDigest"), str)
        or len(payload["exportContentDigest"]) != 64
    ):
        return False
    views = payload.get("views")
    if not isinstance(views, list) or len(views) != 3:
        return False
    kinds: set[str] = set()
    for view in views:
        if not isinstance(view, Mapping):
            return False
        kind, route = view.get("kind"), view.get("route")
        if (
            not isinstance(kind, str)
            or kind not in {"project", "subject", "quiz"}
            or kind in kinds
            or not isinstance(route, str)
            or view.get("state") != "ready"
            or view.get("visibleContentChecked") is not True
        ):
            return False
        if kind == "project" and route != "/":
            return False
        if kind == "subject" and not route.startswith("/subjects/"):
            return False
        if kind == "quiz" and "/quizzes/" not in route:
            return False
        kinds.add(kind)
    return kinds == {"project", "subject", "quiz"}
