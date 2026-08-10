from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from src.artifacts.json_io import write_json_artifact
from src.scholarship.coverage import ScholarshipAudit
from src.scholarship.gap_report import ScholarshipGapReport
from src.scholarship.source_health import SourceHealthAudit, SourceHealthIssue

_DEAD_LINK_CODES = frozenset({"unreachable", "unreachable_timeout"})
_BOT_BLOCK_CODES = frozenset({"blocked"})
_ROLE_GAP_CODES = frozenset({"terse_role"})
_METADATA_CODES = frozenset(
    {"documentation_locator", "forbidden_locator", "missing_bib", "weak_locator"}
)


def scholarship_source_health_network(
    *,
    scholarship: ScholarshipAudit,
    source_health: SourceHealthAudit,
    gap_report: ScholarshipGapReport,
) -> dict[str, Any]:
    gap_payload = gap_report.to_dict()
    frontier_sources = gap_payload.get("frontierSources", [])
    advisories = gap_payload.get("advisories", {})
    boundary_sources = [
        _boundary_source_row(row)
        for row in frontier_sources
        if isinstance(row, dict) and row.get("requiresBoundary") is True
    ]
    dead_links = _issue_rows(source_health.issue_list, _DEAD_LINK_CODES)
    bot_blocks = _issue_rows(source_health.issue_list, _BOT_BLOCK_CODES)
    role_gaps = _issue_rows(source_health.issue_list, _ROLE_GAP_CODES)
    metadata_issues = _issue_rows(source_health.issue_list, _METADATA_CODES)
    bot_blocks.extend(_online_status_rows(source_health, "http_error:403"))
    dead_links.extend(_online_status_rows(source_health, "url_error:"))
    dead_links.extend(_online_status_rows(source_health, "timeout:"))
    dead_links.extend(_online_status_rows(source_health, "tls_error:"))
    drift = {
        "singleSectionWithoutClaimSupport": list(
            advisories.get("singleSectionWithoutClaimSupport", [])
            if isinstance(advisories, dict)
            else []
        ),
        "uncitedBibEntries": list(scholarship.uncited_bib_entries),
        "underweightedLanes": list(
            advisories.get("underweightedLanes", [])
            if isinstance(advisories, dict)
            else []
        ),
        "unusedMatrixEntries": list(scholarship.unused_matrix_entries),
    }
    issue_counts = Counter(issue.code for issue in source_health.issue_list)
    uncited_drift_count = sum(
        len(value) for value in drift.values() if isinstance(value, list)
    )
    return {
        "botBlocks": sorted(bot_blocks, key=_row_key),
        "boundarySources": sorted(boundary_sources, key=_row_key),
        "claimBoundary": (
            "Source-health network separates local metadata, optional online reachability "
            "and manuscript boundary support; it does not certify source truth."
        ),
        "deadLinks": sorted(dead_links, key=_row_key),
        "metadataIssues": sorted(metadata_issues, key=_row_key),
        "roleGaps": sorted(role_gaps, key=_row_key),
        "statusBuckets": dict(sorted(issue_counts.items())),
        "summary": {
            "botBlocks": len(bot_blocks),
            "boundarySources": len(boundary_sources),
            "checkedOnline": source_health.checked_online,
            "deadLinks": len(dead_links),
            "frontierSources": gap_payload.get("summary", {}).get("frontierSources", 0)
            if isinstance(gap_payload.get("summary"), dict)
            else 0,
            "metadataIssues": len(metadata_issues),
            "roleGaps": len(role_gaps),
            "sourceHealthIssues": len(source_health.issue_list),
            "sources": source_health.source_count,
            "uncitedDrift": uncited_drift_count,
        },
        "uncitedDrift": drift,
    }


def write_scholarship_source_health_network(
    payload: dict[str, Any],
    path: Path,
) -> Path:
    return write_json_artifact(Path(path), payload)


def _issue_rows(
    issues: tuple[SourceHealthIssue, ...],
    codes: frozenset[str],
) -> list[dict[str, object]]:
    return [
        {"code": issue.code, "key": issue.key, "message": issue.message}
        for issue in issues
        if issue.code in codes
    ]


def _online_status_rows(
    audit: SourceHealthAudit,
    prefix: str,
) -> list[dict[str, object]]:
    return [
        {"code": "online_status", "key": key, "message": status}
        for key, status in audit.online_results.items()
        if status.startswith(prefix)
    ]


def _boundary_source_row(row: dict[str, Any]) -> dict[str, object]:
    return {
        "area": str(row.get("area", "")),
        "boundarySupported": row.get("boundarySupported") is True,
        "citedInManuscript": row.get("citedInManuscript") is True,
        "lane": str(row.get("lane", "")),
        "requiresBoundary": row.get("requiresBoundary") is True,
        "sourceKey": str(row.get("sourceKey", "")),
        "supportRows": [
            str(item) for item in row.get("supportRows", []) if isinstance(item, str)
        ],
    }


def _row_key(row: dict[str, object]) -> tuple[str, str]:
    return str(row.get("key") or row.get("sourceKey") or ""), str(row.get("code", ""))
