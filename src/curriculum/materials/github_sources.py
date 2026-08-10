from __future__ import annotations

import fnmatch
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from src.net_guard import require_http_url

from .models import CourseMaterialIssue


def _required_string(mapping: dict[str, Any], key: str) -> str:
    value = mapping.get(key)
    return value if isinstance(value, str) else ""


def _as_pointer_list(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _iter_configured_pointers(
    payload: dict[str, Any],
) -> list[tuple[str, dict[str, Any]]]:
    pointers: list[tuple[str, dict[str, Any]]] = []
    stratum_mappings = payload.get("stratum_mappings")
    if isinstance(stratum_mappings, dict):
        for stratum_key, raw in stratum_mappings.items():
            for pointer in _as_pointer_list(raw):
                pointers.append((f"stratum_mappings.{stratum_key}", pointer))
    topic_mappings = payload.get("topic_mappings")
    if isinstance(topic_mappings, list):
        for topic_idx, topic in enumerate(topic_mappings):
            if not isinstance(topic, dict):
                continue
            for pointer in _as_pointer_list(topic.get("pointers")):
                pointers.append((f"topic_mappings[{topic_idx}].pointers", pointer))
    return pointers


def _validate_online_trees(
    source_index: dict[str, dict[str, Any]],
    payload: dict[str, Any],
    *,
    timeout: float,
) -> list[CourseMaterialIssue]:
    issues: list[CourseMaterialIssue] = []
    tree_paths_by_source: dict[str, set[str]] = {}
    for source_id, source in source_index.items():
        repo_url = _required_string(source, "repo_url")
        commit = _required_string(source, "commit")
        parts = _github_repo_parts(repo_url)
        if parts is None:
            continue
        try:
            tree_paths = _fetch_github_tree_paths(parts[0], parts[1], commit, timeout)
        except (OSError, urllib.error.URLError, ValueError) as exc:
            issues.append(
                CourseMaterialIssue(
                    "github-tree",
                    f"sources.{source_id}",
                    f"could not fetch pinned GitHub tree: {exc}",
                )
            )
            continue
        tree_paths_by_source[source_id] = tree_paths
        for pattern in source.get("path_globs", []):
            if isinstance(pattern, str) and not any(
                fnmatch.fnmatch(path, pattern) for path in tree_paths
            ):
                issues.append(
                    CourseMaterialIssue(
                        "path-glob",
                        f"sources.{source_id}.path_globs",
                        f"glob {pattern!r} matched no files at pinned commit",
                    )
                )

    for pointer_location, pointer in _iter_configured_pointers(payload):
        source_id = _required_string(pointer, "source_id")
        pointer_path = _required_string(pointer, "path")
        source_paths = tree_paths_by_source.get(source_id)
        if source_paths is not None and pointer_path not in source_paths:
            issues.append(
                CourseMaterialIssue(
                    "pointer-path",
                    f"{pointer_location}.path",
                    f"{pointer_path!r} is not present at the pinned source commit",
                )
            )
    return issues


def _github_tree_payload(
    request: urllib.request.Request,
    *,
    timeout: float,
    attempts: int = 3,
    base_delay: float = 0.5,
) -> dict[str, Any]:
    """Fetch the GitHub tree JSON with bounded retry/backoff on transient failures.

    Network hiccups and 5xx responses are retried with exponential backoff so that
    flaky runs do not produce non-deterministic red proof results. Permanent 4xx
    client errors (e.g. a genuinely missing commit) raise immediately without a
    retry, because re-sending them can never succeed.
    """
    last_exc: Exception | None = None
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
            if not isinstance(payload, dict):
                raise TypeError("GitHub response was not a JSON object")
            return payload
        except urllib.error.HTTPError as exc:
            last_exc = exc
            if exc.code < 500:
                raise
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_exc = exc
        if attempt + 1 < attempts:
            time.sleep(base_delay * (2**attempt))
    if last_exc is not None:
        raise last_exc
    payload = {}
    return payload  # pragma: no cover - unreachable


def _fetch_github_tree_paths(
    owner: str,
    repo: str,
    commit: str,
    timeout: float,
) -> set[str]:
    # Base is env-overridable so the online path can be exercised against a local
    # local test server without reaching the external GitHub API.
    base = os.environ.get("ASF_GITHUB_API_BASE", "https://api.github.com").rstrip("/")
    url = f"{base}/repos/{owner}/{repo}/git/trees/{commit}?recursive=1"
    # `base` is env-overridable (see comment above); assert the invariant at this
    # call site rather than relying only on _github_repo_parts()'s check of repo_url.
    require_http_url(url, context="GitHub tree fetch")
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "Active-Skillference-course-material-validator",
        },
    )
    payload = _github_tree_payload(request, timeout=timeout)
    tree = payload.get("tree") if isinstance(payload, dict) else None
    if not isinstance(tree, list):
        raise TypeError("GitHub response did not include a tree")
    return {
        str(item.get("path"))
        for item in tree
        if isinstance(item, dict) and item.get("type") == "blob" and item.get("path")
    }


def _github_repo_parts(repo_url: str) -> tuple[str, str] | None:
    parsed = urllib.parse.urlparse(repo_url)
    if parsed.scheme not in {"http", "https"} or parsed.netloc != "github.com":
        return None
    parts = [part for part in parsed.path.strip("/").split("/") if part]
    if len(parts) != 2:
        return None
    return parts[0], parts[1].removesuffix(".git")
