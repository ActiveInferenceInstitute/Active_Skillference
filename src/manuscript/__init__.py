"""Manuscript artifact validation helpers."""

from src.manuscript.american_english import (
    AmericanEnglishError,
    AmericanEnglishIssue,
    audit_american_english,
    validate_american_english,
)
from src.manuscript.audit import (
    FigureRegistryEntry,
    FrontMatterVisualAudit,
    ManuscriptArtifactAudit,
    ManuscriptArtifactError,
    audit_front_matter_visual,
    audit_manuscript_artifacts,
    extract_declared_figure_labels,
    extract_referenced_figure_labels,
    load_figure_registry,
    validate_front_matter_visual,
    validate_manuscript_artifacts,
    write_front_matter_visual_audit,
    write_manuscript_artifact_audit,
)
from src.manuscript.claim_support import (
    ClaimSupportAudit,
    ClaimSupportError,
    audit_claim_support,
    validate_claim_support,
    write_claim_support_audit,
)

__all__ = [
    "AmericanEnglishError",
    "AmericanEnglishIssue",
    "ClaimSupportAudit",
    "ClaimSupportError",
    "FigureRegistryEntry",
    "FrontMatterVisualAudit",
    "ManuscriptArtifactAudit",
    "ManuscriptArtifactError",
    "audit_american_english",
    "audit_claim_support",
    "audit_front_matter_visual",
    "audit_manuscript_artifacts",
    "extract_declared_figure_labels",
    "extract_referenced_figure_labels",
    "load_figure_registry",
    "validate_american_english",
    "validate_claim_support",
    "validate_front_matter_visual",
    "validate_manuscript_artifacts",
    "write_claim_support_audit",
    "write_front_matter_visual_audit",
    "write_manuscript_artifact_audit",
]
