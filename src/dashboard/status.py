"""SkillTree service status checks for the local learner dashboard."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from src.net_guard import NonHttpUrlError, require_http_url


def check_skilltree_status(base_url: str, timeout: float = 1.0) -> dict[str, Any]:
    """Probe SkillTree's public status endpoint and return a browser-safe result."""
    status_url = f"{base_url.rstrip('/')}/public/status"
    try:
        require_http_url(status_url, context="SkillTree status check")
    except NonHttpUrlError as exc:
        return {
            "available": False,
            "url": status_url,
            "statusCode": None,
            "message": str(exc),
            "body": "",
        }
    request = urllib.request.Request(
        status_url,
        headers={"Accept": "application/json"},
        method="GET",
    )
    try:
        # require_http_url() above rejects non-http(s) targets.
        with urllib.request.urlopen(request, timeout=timeout) as response:  # nosec B310
            raw = response.read().decode("utf-8", errors="replace")
            status_code = response.status
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        return {
            "available": False,
            "url": status_url,
            "statusCode": exc.code,
            "message": f"SkillTree status endpoint returned HTTP {exc.code}",
            "body": raw[:500],
        }
    except urllib.error.URLError as exc:
        return {
            "available": False,
            "url": status_url,
            "statusCode": None,
            "message": f"SkillTree is not reachable: {exc.reason}",
            "body": "",
        }
    except TimeoutError:
        return {
            "available": False,
            "url": status_url,
            "statusCode": None,
            "message": "SkillTree status check timed out",
            "body": "",
        }

    parsed: Any
    try:
        parsed = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        parsed = raw[:500]
    return {
        "available": 200 <= status_code < 300,
        "url": status_url,
        "statusCode": status_code,
        "message": "SkillTree is reachable",
        "body": parsed,
    }
