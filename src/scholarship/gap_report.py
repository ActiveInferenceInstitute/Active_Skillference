"""Scholarship frontier gap reporting.

The core scholarship validator proves that cited keys, BibTeX entries, and
source-role rows agree. This module adds a small frontier contract over that
clean surface: selected high-value source areas must be present, cited, and
bound to declared claim-support rows so scholarship upgrades improve argument
quality rather than only increasing bibliography size.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.artifacts.json_io import write_json_artifact
from src.manuscript.claim_support import ClaimSupportAudit
from src.scholarship.coverage import EXPECTED_LANES, ScholarshipAudit
from src.scholarship.frontier_sources import (
    FRONTIER_SOURCE_CONTRACTS,
)


class ScholarshipGapError(ValueError):
    """Raised when the scholarship frontier contract is incomplete."""


_ENTRY_RE = re.compile(r"@\w+\{([^,]+),([\s\S]*?)(?=\n@\w+\{|$)")
_YEAR_RE = re.compile(r"\byear\s*=\s*\{(\d{4})\}", re.IGNORECASE)


@dataclass(frozen=True)
class ScholarshipGapReport:
    """Computed scholarship frontier report."""

    issues_found: tuple[str, ...]
    payload: dict[str, Any]

    def issues(self) -> tuple[str, ...]:
        """Return human-readable blocking issues."""
        return self.issues_found

    def to_dict(self) -> dict[str, Any]:
        """Return deterministic JSON output."""
        return self.payload | {"issues": list(self.issues_found)}


def audit_scholarship_gaps(
    scholarship: ScholarshipAudit,
    claim_support: ClaimSupportAudit,
    bib_path: Path,
) -> ScholarshipGapReport:
    """Return a source-quality report for high-value scholarship frontiers."""
    bib_years = _parse_bib_years(Path(bib_path).read_text(encoding="utf-8"))
    section_sources = _source_sections(scholarship)
    support_rows_by_source = _claim_support_rows_by_source(claim_support)
    issues: list[str] = []
    frontier_rows: list[dict[str, object]] = []

    for contract in FRONTIER_SOURCE_CONTRACTS:
        source = scholarship.sources.get(contract.source_key)
        support_rows = support_rows_by_source.get(contract.source_key, ())
        support_types = tuple(sorted({row["type"] for row in support_rows}))
        present_in_matrix = source is not None
        cited_in_manuscript = bool(section_sources.get(contract.source_key))
        present_in_bib = contract.source_key in scholarship.bib_keys
        supported_by_claim = any(
            row["type"] in contract.required_claim_support_types for row in support_rows
        )
        boundary_supported = not contract.requires_boundary or any(
            row["hasBoundary"] for row in support_rows
        )
        row = {
            **contract.to_dict(),
            "boundarySupported": boundary_supported,
            "citedInManuscript": cited_in_manuscript,
            "lane": source.lane if source else "",
            "presentInBib": present_in_bib,
            "presentInMatrix": present_in_matrix,
            "sections": list(section_sources.get(contract.source_key, ())),
            "supportRows": [row["id"] for row in support_rows],
            "supportTypes": list(support_types),
            "year": bib_years.get(contract.source_key),
        }
        frontier_rows.append(row)
        if not present_in_matrix:
            issues.append(
                f"{contract.area}: missing source matrix row {contract.source_key}"
            )
        if not present_in_bib:
            issues.append(
                f"{contract.area}: missing BibTeX entry {contract.source_key}"
            )
        if not cited_in_manuscript:
            issues.append(f"{contract.area}: source is not cited in manuscript")
        if not supported_by_claim:
            issues.append(
                f"{contract.area}: source is not bound to required claim-support type "
                + "/".join(contract.required_claim_support_types)
            )
        if not boundary_supported:
            issues.append(f"{contract.area}: missing explicit boundary support")

    cited_keys = frozenset(section_sources)
    lane_counts = Counter(
        scholarship.sources[key].lane
        for key in cited_keys
        if key in scholarship.sources
    )
    kind_counts = Counter(
        scholarship.sources[key].kind
        for key in cited_keys
        if key in scholarship.sources
    )
    cited_years = [
        year for key in cited_keys if (year := bib_years.get(key)) is not None
    ]
    single_section_low_support = [
        key
        for key, sections in sorted(section_sources.items())
        if len(sections) == 1 and key not in support_rows_by_source
    ]
    underweighted_lanes = [
        lane
        for lane in EXPECTED_LANES
        if lane_counts.get(lane, 0) < _median_count(lane_counts.values())
    ]
    payload = {
        "advisories": {
            "singleSectionWithoutClaimSupport": single_section_low_support,
            "underweightedLanes": underweighted_lanes,
        },
        "frontierSources": frontier_rows,
        "kindBalance": dict(sorted(kind_counts.items())),
        "laneBalance": {lane: lane_counts.get(lane, 0) for lane in EXPECTED_LANES},
        "recentness": {
            "latestYear": max(cited_years) if cited_years else None,
            "sourcesSince2024": sum(1 for year in cited_years if year >= 2024),
            "yearKnownSources": len(cited_years),
        },
        "summary": {
            "blockingIssues": len(issues),
            "claimSupportRows": len(claim_support.rows),
            "frontierSources": len(FRONTIER_SOURCE_CONTRACTS),
            "singleSectionWithoutClaimSupport": len(single_section_low_support),
            "sources": len(cited_keys),
            "underweightedLanes": len(underweighted_lanes),
        },
    }
    return ScholarshipGapReport(
        issues_found=tuple(sorted(issues)),
        payload=payload,
    )


def validate_scholarship_gaps(
    scholarship: ScholarshipAudit,
    claim_support: ClaimSupportAudit,
    bib_path: Path,
) -> ScholarshipGapReport:
    """Raise if the scholarship frontier report has blocking issues."""
    report = audit_scholarship_gaps(scholarship, claim_support, bib_path)
    if report.issues():
        raise ScholarshipGapError(
            "scholarship gap report validation failed:\n  "
            + "\n  ".join(report.issues())
        )
    return report


def write_scholarship_gap_report(report: ScholarshipGapReport, path: Path) -> Path:
    """Write the deterministic scholarship gap report JSON."""
    return write_json_artifact(Path(path), report.to_dict())


def _parse_bib_years(text: str) -> dict[str, int]:
    years: dict[str, int] = {}
    for key, body in _ENTRY_RE.findall(text):
        match = _YEAR_RE.search(body)
        if match:
            years[key] = int(match.group(1))
    return years


def _source_sections(audit: ScholarshipAudit) -> dict[str, tuple[str, ...]]:
    sections_by_source: dict[str, list[str]] = {}
    for section, citations in audit.section_citations.items():
        for key in citations:
            if key in audit.sources:
                sections_by_source.setdefault(key, []).append(section)
    return {
        key: tuple(sorted(sections))
        for key, sections in sorted(sections_by_source.items())
    }


def _claim_support_rows_by_source(
    claim_support: ClaimSupportAudit,
) -> dict[str, tuple[dict[str, Any], ...]]:
    rows: dict[str, list[dict[str, Any]]] = {}
    for row in claim_support.rows:
        serialized: dict[str, Any] = {
            "hasBoundary": row.claim_type == "scope_limit"
            or bool(row.limitation_markers),
            "id": row.claim_id,
            "type": row.claim_type,
        }
        for key in row.citations:
            rows.setdefault(key, []).append(serialized)
    return {key: tuple(value) for key, value in sorted(rows.items())}


def _median_count(values: Any) -> float:
    ordered = sorted(values)
    if not ordered:
        return 0.0
    midpoint = len(ordered) // 2
    if len(ordered) % 2:
        return float(ordered[midpoint])
    return (ordered[midpoint - 1] + ordered[midpoint]) / 2
