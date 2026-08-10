"""Typed contracts for stable JSON audit payloads consumed by figures and dashboard."""

from __future__ import annotations

from typing import TypedDict


class ScholarshipAuditSummary(TypedDict, total=False):
    citedSources: int
    matrixSources: int
    issueCount: int
    unusedMatrixEntries: int
    uncitedBibEntries: int
    sectionsWithCitations: int
    expectedLanes: int
    missingLanes: int
    invalidSourceRows: int


class ScholarshipAuditPayload(TypedDict, total=False):
    summary: ScholarshipAuditSummary
    lanes: dict[str, ScholarshipAuditSummary]


class SourceHealthSummary(TypedDict, total=False):
    sources: int
    issueCount: int
    onlineCheckedSources: int


class SourceHealthAuditPayload(TypedDict, total=False):
    summary: SourceHealthSummary


class RoadmapTaskPayload(TypedDict, total=False):
    id: str
    status: str
    priority: str


class RoadmapAuditPayload(TypedDict, total=False):
    tasks: list[RoadmapTaskPayload]
    summary: dict[str, object]


class ClaimSupportAuditPayload(TypedDict, total=False):
    summary: dict[str, object]
    issues: list[dict[str, object]]
