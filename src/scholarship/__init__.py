"""Scholarship coverage validation for manuscript sources."""

from src.scholarship.coverage import (
    EXPECTED_LANES,
    ScholarshipAudit,
    ScholarshipError,
    ScholarshipSource,
    audit_scholarship,
    extract_manuscript_citations,
    load_source_matrix,
    parse_bib_keys,
    validate_scholarship,
    write_scholarship_audit,
)
from src.scholarship.gap_report import (
    FRONTIER_SOURCE_CONTRACTS,
    ScholarshipGapError,
    ScholarshipGapReport,
    audit_scholarship_gaps,
    validate_scholarship_gaps,
    write_scholarship_gap_report,
)

__all__ = [
    "EXPECTED_LANES",
    "FRONTIER_SOURCE_CONTRACTS",
    "ScholarshipAudit",
    "ScholarshipError",
    "ScholarshipGapError",
    "ScholarshipGapReport",
    "ScholarshipSource",
    "audit_scholarship",
    "audit_scholarship_gaps",
    "extract_manuscript_citations",
    "load_source_matrix",
    "parse_bib_keys",
    "validate_scholarship",
    "validate_scholarship_gaps",
    "write_scholarship_audit",
    "write_scholarship_gap_report",
]
