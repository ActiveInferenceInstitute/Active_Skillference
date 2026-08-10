"""Source-health checks for the scholarship source matrix."""

from __future__ import annotations

import re
import urllib.request  # noqa: F401 - module-level urlopen patch target
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.artifacts.json_io import write_json_artifact
from src.scholarship.coverage import (
    load_source_matrix,
    parse_bib_keys,
    role_is_claim_specific,
)
from src.scholarship.source_health_network import (
    _BROWSER_USER_AGENT,
    _LOCAL_HOSTNAMES,
    _ORIGINAL_URLOPEN,
    _PUBLIC_URL_OPENER,
    _check_url,
    _check_url_get,
    _forbidden_ip_address,
    _locator_url,
    _open_url,
    _public_http_url_block_status,
    _PublicOnlyRedirectHandler,
)

# These network-helper names are intentionally re-exported so downstream callers
# (and the test suite) can reach them as module attributes of source_health (e.g.
# source_health._check_url_get). Declared in __all__ so the linter treats them as
# the deliberate module-level API rather than unused imports.
__all__ = [
    "_BROWSER_USER_AGENT",
    "_LOCAL_HOSTNAMES",
    "_ORIGINAL_URLOPEN",
    "_PUBLIC_URL_OPENER",
    "_PublicOnlyRedirectHandler",
    "_check_url",
    "_check_url_get",
    "_forbidden_ip_address",
    "_locator_url",
    "_open_url",
    "_public_http_url_block_status",
]


class SourceHealthError(ValueError):
    """Raised when scholarship source-health checks fail."""


@dataclass(frozen=True)
class SourceHealthIssue:
    """One source-health issue."""

    key: str
    code: str
    message: str

    def __str__(self) -> str:
        return f"{self.key}: {self.code}: {self.message}"


@dataclass(frozen=True)
class SourceHealthAudit:
    """Source-health audit result."""

    issue_list: tuple[SourceHealthIssue, ...]
    checked_online: bool
    online_results: dict[str, str]
    source_count: int

    def issues(self) -> tuple[str, ...]:
        return tuple(str(issue) for issue in self.issue_list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "checkedOnline": self.checked_online,
            "issues": self.issues(),
            "onlineResults": self.online_results,
            "summary": {
                "issueCount": len(self.issue_list),
                "onlineCheckedSources": len(self.online_results),
                "sources": self.source_count,
            },
        }


_DOI_RE = re.compile(r"^doi:10\.\S+/\S+$", re.IGNORECASE)
_URL_RE = re.compile(r"^url:https?://\S+$", re.IGNORECASE)
_ISBN_RE = re.compile(r"^isbn:[0-9Xx -]{10,}$")
_BOOK_RE = re.compile(r"^(book|jstor):\S+", re.IGNORECASE)
_STRICT_ONLINE_FATAL_CODES = frozenset({"forbidden_locator", "unreachable"})


def audit_source_health(
    matrix_path: Path,
    bib_path: Path,
    *,
    online: bool = False,
    timeout: float = 5.0,
    allow_private: bool = False,
) -> SourceHealthAudit:
    """Validate source locator quality and, optionally, URL/DOI reachability."""
    sources = load_source_matrix(matrix_path)
    bib_keys = parse_bib_keys(Path(bib_path).read_text(encoding="utf-8"))
    issues: list[SourceHealthIssue] = []
    online_results: dict[str, str] = {}

    for source in sources.values():
        if source.key not in bib_keys:
            issues.append(
                SourceHealthIssue(
                    source.key, "missing_bib", "source key is not in references.bib"
                )
            )
        if not _locator_is_specific(source.locator):
            issues.append(
                SourceHealthIssue(
                    source.key,
                    "weak_locator",
                    "locator must be a DOI, URL, ISBN, book id, or JSTOR id",
                )
            )
        if not role_is_claim_specific(source.lane, source.role):
            issues.append(
                SourceHealthIssue(
                    source.key,
                    "terse_role",
                    "role is not claim-specific "
                    "(needs at least two lane-relevant content tokens)",
                )
            )
        if source.kind == "documentation" and not source.locator.startswith("url:"):
            issues.append(
                SourceHealthIssue(
                    source.key,
                    "documentation_locator",
                    "documentation sources should use a URL locator",
                )
            )
        if online and source.locator.startswith(("doi:", "url:")):
            url = _locator_url(source.locator)
            status = _check_url(url, timeout=timeout, allow_private=allow_private)
            online_results[source.key] = status
            issue = _online_issue_for_status(source.key, status)
            if issue is not None:
                issues.append(issue)

    return SourceHealthAudit(
        issue_list=tuple(sorted(issues, key=lambda issue: (issue.key, issue.code))),
        checked_online=online,
        online_results=online_results,
        source_count=len(sources),
    )


def validate_source_health(
    matrix_path: Path,
    bib_path: Path,
    *,
    online: bool = False,
    strict_online: bool = False,
    timeout: float = 5.0,
    allow_private: bool = False,
) -> SourceHealthAudit:
    """Raise if source-health checks find issues.

    ``allow_private`` mirrors :func:`audit_source_health`: it defaults to ``False``
    so every real caller keeps the SSRF/loopback guard, and is only set ``True`` by
    tests that point the audit at a local pytest-httpserver endpoint.
    """
    if strict_online and not online:
        raise ValueError("strict_online requires online=True")
    audit = audit_source_health(
        matrix_path,
        bib_path,
        online=online,
        timeout=timeout,
        allow_private=allow_private,
    )
    issues = audit.issue_list
    if online:
        issues = tuple(
            issue
            for issue in audit.issue_list
            if issue.code in _STRICT_ONLINE_FATAL_CODES
            or issue.code not in {"blocked", "unreachable_timeout"}
        )
    if issues:
        raise SourceHealthError(
            "scholarship source-health validation failed:\n  "
            + "\n  ".join(str(issue) for issue in issues)
        )
    return audit


def write_source_health_audit(audit: SourceHealthAudit, path: Path) -> Path:
    """Write source-health audit JSON."""
    return write_json_artifact(Path(path), audit.to_dict())


def _locator_is_specific(locator: str) -> bool:
    return any(
        pattern.match(locator) for pattern in (_DOI_RE, _URL_RE, _ISBN_RE, _BOOK_RE)
    )


def _online_issue_for_status(key: str, status: str) -> SourceHealthIssue | None:
    if status.startswith("ok:"):
        return None
    if status.startswith("blocked_url:"):
        return SourceHealthIssue(
            key,
            "forbidden_locator",
            status,
        )
    if status.startswith("http_error:403"):
        return SourceHealthIssue(
            key,
            "blocked",
            status,
        )
    if status.startswith("timeout:"):
        return SourceHealthIssue(
            key,
            "unreachable_timeout",
            status,
        )
    if status.startswith(
        ("http_error:4", "http_error:5", "url_error:", "os_error:", "tls_error:")
    ):
        return SourceHealthIssue(
            key,
            "unreachable",
            status,
        )
    return SourceHealthIssue(key, "unreachable", status)
