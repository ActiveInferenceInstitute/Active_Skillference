"""Validate manuscript citation coverage against a source-role matrix.

The provenance layer already prevents numeric claims from drifting away from kernels.
This module gives scholarship a comparable fail-closed contract: every cited BibTeX key
must be mapped to a role, lane, kind, and locator in ``data/scholarship_sources.yaml``;
the reverse alignment is enforced too, so stale bibliography or source-matrix rows cannot
quietly overstate the manuscript's scholarly support.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

from src.artifacts.json_io import write_json_artifact

EXPECTED_LANES: tuple[str, ...] = (
    "perception_as_inference",
    "active_inference_core",
    "mathematical_foundations",
    "pedagogy_and_learning_paths",
    "delivery_and_reporting",
    "applications_and_scope",
)

VALID_KINDS: frozenset[str] = frozenset(
    {
        "documentation",
        "historical",
        "methods",
        "primary",
        "review",
        "software",
        "textbook",
        "tutorial",
    }
)

LANE_ROLE_KEYWORDS: dict[str, frozenset[str]] = {
    "perception_as_inference": frozenset(
        {
            "perception",
            "perceptual",
            "inference",
            "infer",
            "bayesian",
            "brain",
            "bayesian-brain",
            "predictive",
            "prediction",
            "recognition",
            "generative",
            "unconscious",
            "helmholtz",
            "predictive-processing",
            "predictive-coding",
            "helmholtz-machine",
        }
    ),
    "active_inference_core": frozenset(
        {
            "active",
            "inference",
            "active-inference",
            "free-energy",
            "policy",
            "epistemic",
            "expected-free-energy",
            "fep",
            "action",
            "action-oriented",
            "perception",
            "tutorial",
            "discrete",
            "state-space",
            "generative",
            "message-passing",
            "process",
            "curiosity",
            "filtering",
            "predictive-coding",
            "formulation",
            "principle",
            "review",
            "review-level",
            "terminology",
            "software",
            "derivation",
            "model-learning",
            "generalised",
            "generalized",
            "decomposition",
            "policy-selection",
            "discrete-state",
            "formulations",
            "boundaries",
        }
    ),
    "mathematical_foundations": frozenset(
        {
            "entropy",
            "information",
            "information-theory",
            "probabilistic",
            "probability",
            "variational",
            "bayesian",
            "inference",
            "graphical",
            "graph",
            "graph-algorithm",
            "message-passing",
            "elbo",
            "filtering",
            "smoothing",
            "state-space",
            "rate-distortion",
            "bottleneck",
            "approximation",
            "pattern-recognition",
            "dag",
            "topological",
            "distribution",
            "variational-methods",
            "variational-inference",
            "information-bottleneck",
        }
    ),
    "pedagogy_and_learning_paths": frozenset(
        {
            "learning",
            "active",
            "active-learning",
            "learner",
            "pedagogical",
            "pedagogy",
            "prerequisite",
            "assessment",
            "assessment-design",
            "evidence-centered",
            "retrieval",
            "practice",
            "testing",
            "retention",
            "transfer",
            "cognitive",
            "engagement",
            "icap",
            "objectives",
            "learning-objectives",
            "taxonomy",
            "gamification",
            "education",
            "course",
            "curriculum",
            "concept",
            "knowledge",
            "knowledge-space",
            "learning-space",
            "mastery",
            "mastery-state",
            "knowledge-base",
            "ordering",
            "graph",
            "skilltree",
            "quiz",
            "feedback",
            "formative",
            "constructive",
            "alignment",
            "aligned",
            "design-based",
            "evaluation",
            "guidance",
            "open-science",
            "open-source",
            "community",
            "motivation",
            "base-rate",
            "reasoning",
            "bayesian",
            "gamification-in-education",
            "infrastructure",
        }
    ),
    "delivery_and_reporting": frozenset(
        {
            "delivery",
            "reporting",
            "report",
            "dashboard",
            "skilltree",
            "software",
            "scientific-computing",
            "computational",
            "reproducible",
            "reproducibility",
            "reproducible-science",
            "workflow",
            "workflow-capture",
            "version-control",
            "testing",
            "automation",
            "nsa",
            "security",
            "national",
            "agency",
            "zero",
            "trust",
            "supply-chain",
            "supply",
            "chain",
            "provenance",
            "attestation",
            "artifact-signing",
            "signing",
            "transparency-log",
            "transparency",
            "openness",
            "open-science",
            "open-data",
            "fair",
            "data",
            "sbom",
            "bill",
            "materials",
            "adversary",
            "tactics",
            "techniques",
            "threat-model",
            "threat",
            "misuse",
            "alt-text",
            "accessible",
            "accessibility",
            "wcag",
            "web",
            "content",
            "figure",
            "palette",
            "literate",
            "executable",
            "repository",
            "documentation",
            "integration",
            "deployment",
            "secure",
            "development",
            "ssdf",
            "access-control",
            "build-attestation",
            "apt",
            "federal",
            "metadata",
            "skills-service",
            "curriculum-generation",
            "learning-path",
            "integrity",
            "semantic",
        }
    ),
    "applications_and_scope": frozenset(
        {
            "applications",
            "application",
            "scope",
            "biological",
            "self-organisation",
            "self-organization",
            "laplace-approximation",
            "laplace",
            "variational",
            "expectation",
            "maximisation",
            "maximization",
            "hierarchical",
            "predictive-coding",
            "predictive",
            "markov",
            "blanket",
            "blankets",
            "fep",
            "physics",
            "bayesian",
            "mechanics",
            "empirical-status",
            "empirical",
            "reinforcement-learning",
            "reinforcement",
            "embodied",
            "organizational",
            "experimental",
            "validation",
            "critique",
            "scope-boundary",
            "boundary",
            "boundaries",
            "evidence",
            "particular-physics",
            "predictive-processing",
            "distinctive-prediction",
            "bayesian-mechanics",
        }
    ),
}

_CITATION_RE = re.compile(r"@([A-Za-z0-9_:-]+)")
_BIB_KEY_RE = re.compile(r"@[A-Za-z]+\{([^,]+),")
_CODE_RE = re.compile(r"```.*?```|`[^`\n]*`", re.DOTALL)
_ROLE_TOKEN_RE = re.compile(r"[^a-z0-9-]+")


class ScholarshipError(ValueError):
    """Raised when scholarship coverage is incomplete or malformed."""


@dataclass(frozen=True)
class ScholarshipSource:
    """One cited source mapped to a manuscript support role."""

    key: str
    lane: str
    kind: str
    role: str
    locator: str

    def to_dict(self) -> dict[str, str]:
        """Return a deterministic JSON-serializable representation."""
        return {
            "key": self.key,
            "kind": self.kind,
            "lane": self.lane,
            "locator": self.locator,
            "role": self.role,
        }


@dataclass(frozen=True)
class ScholarshipAudit:
    """Computed scholarship coverage for the current manuscript."""

    sources: dict[str, ScholarshipSource]
    bib_keys: frozenset[str]
    section_citations: dict[str, tuple[str, ...]]
    missing_matrix_entries: tuple[str, ...]
    missing_bib_entries: tuple[str, ...]
    matrix_entries_missing_bib: tuple[str, ...]
    invalid_sources: tuple[str, ...]
    unused_matrix_entries: tuple[str, ...]
    uncited_bib_entries: tuple[str, ...]
    missing_lanes: tuple[str, ...]

    def issues(self) -> tuple[str, ...]:
        """Return human-readable failure messages."""
        messages: list[str] = []
        if self.missing_matrix_entries:
            messages.append(
                "cited keys missing from scholarship matrix: "
                + ", ".join(self.missing_matrix_entries)
            )
        if self.missing_bib_entries:
            messages.append(
                "cited keys missing from references.bib: "
                + ", ".join(self.missing_bib_entries)
            )
        if self.matrix_entries_missing_bib:
            messages.append(
                "matrix keys missing from references.bib: "
                + ", ".join(self.matrix_entries_missing_bib)
            )
        if self.unused_matrix_entries:
            messages.append(
                "scholarship matrix keys not cited in manuscript: "
                + ", ".join(self.unused_matrix_entries)
            )
        if self.uncited_bib_entries:
            messages.append(
                "references.bib keys not cited in manuscript: "
                + ", ".join(self.uncited_bib_entries)
            )
        if self.invalid_sources:
            messages.append("invalid source rows: " + "; ".join(self.invalid_sources))
        if self.missing_lanes:
            messages.append(
                "expected lanes not cited in manuscript: "
                + ", ".join(self.missing_lanes)
            )
        return tuple(messages)

    def to_dict(self) -> dict[str, Any]:
        """Return deterministic audit data for JSON output and plotting."""
        cited_keys = sorted(
            {
                key
                for citations in self.section_citations.values()
                for key in citations
                if key in self.sources
            }
        )
        lane_data: dict[str, dict[str, Any]] = {}
        for lane in EXPECTED_LANES:
            lane_sources = sorted(
                source.key for source in self.sources.values() if source.lane == lane
            )
            cited_in_lane = [
                key for key in cited_keys if self.sources[key].lane == lane
            ]
            sections = sorted(
                section
                for section, citations in self.section_citations.items()
                if any(
                    key in self.sources and self.sources[key].lane == lane
                    for key in citations
                )
            )
            lane_data[lane] = {
                "citedSources": len(cited_in_lane),
                "sections": sections,
                "sources": lane_sources,
                "totalSources": len(lane_sources),
            }

        section_data: list[dict[str, Any]] = []
        for section, citations in sorted(self.section_citations.items()):
            lane_counts = {lane: 0 for lane in EXPECTED_LANES}
            for key in citations:
                source = self.sources.get(key)
                if source is not None:
                    lane_counts[source.lane] += 1
            section_data.append(
                {
                    "citations": list(citations),
                    "laneCounts": lane_counts,
                    "section": section,
                }
            )

        return {
            "issues": list(self.issues()),
            "lanes": lane_data,
            "sections": section_data,
            "sources": {
                key: self.sources[key].to_dict() for key in sorted(self.sources)
            },
            "summary": {
                "bibEntries": len(self.bib_keys),
                "citedSources": len(cited_keys),
                "expectedLanes": len(EXPECTED_LANES),
                "invalidSourceRows": len(self.invalid_sources),
                "issueCount": len(self.issues()),
                "matrixSources": len(self.sources),
                "missingBibEntries": len(self.missing_bib_entries),
                "missingLanes": len(self.missing_lanes),
                "missingMatrixEntries": len(self.missing_matrix_entries),
                "sectionsWithCitations": sum(
                    1 for citations in self.section_citations.values() if citations
                ),
                "uncitedBibEntries": len(self.uncited_bib_entries),
                "unusedMatrixEntries": len(self.unused_matrix_entries),
            },
        }


def parse_bib_keys(text: str) -> frozenset[str]:
    """Extract BibTeX entry keys from raw bibliography text."""
    return frozenset(_BIB_KEY_RE.findall(text))


def role_is_claim_specific(lane: str, role: str) -> bool:
    """Return whether a role names enough lane-relevant content to resist stuffing.

    A role must contain at least two distinct normalized tokens drawn from the lane's
    curated keyword set (unioned with the lane-name tokens). This blocks generic
    sentences that stuff one bare lane keyword into otherwise content-free prose while
    still accepting the real source matrix, whose descriptive roles carry at least two
    lane-relevant concepts once the curated keyword sets cover their legitimate terms.
    """
    tokens = frozenset(_normalize_role_tokens(role))
    curated = LANE_ROLE_KEYWORDS.get(lane, frozenset())
    lane_name_tokens = frozenset(
        token for token in re.split(r"[_-]+", lane.lower()) if token
    )
    # Lane-NAME tokens alone are vacuous padding: a role of "Delivery and Reporting here."
    # echoes the lane id 'delivery_and_reporting' and would clear a count that unioned both
    # sets. Require ≥2 CURATED keywords (real content), counting lane-name tokens only as a
    # fallback when a lane has no curated set yet.
    if curated:
        return len(tokens & curated) >= 2
    return len(tokens & lane_name_tokens) >= 2


def extract_manuscript_citations(manuscript_dir: Path) -> dict[str, tuple[str, ...]]:
    """Return section filename to sorted citation keys for authored manuscript files."""
    citations: dict[str, tuple[str, ...]] = {}
    for path in sorted(Path(manuscript_dir).glob("[0-9][0-9]*_*.md")):
        body = _CODE_RE.sub(" ", path.read_text(encoding="utf-8"))
        keys = {
            key
            for key in _CITATION_RE.findall(body)
            if not key.startswith(("fig:", "eq:", "sec:"))
        }
        citations[path.name] = tuple(sorted(keys))
    return citations


def load_source_matrix(path: Path) -> dict[str, ScholarshipSource]:
    """Load the static scholarship source matrix."""
    payload = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("sources"), list):
        raise ScholarshipError(
            "scholarship matrix must contain a top-level sources list"
        )

    sources: dict[str, ScholarshipSource] = {}
    duplicates: list[str] = []
    for index, row in enumerate(payload["sources"], start=1):
        if not isinstance(row, dict):
            raise ScholarshipError(f"sources[{index}] must be a mapping")
        key = _string_field(row, "key", index)
        source = ScholarshipSource(
            key=key,
            kind=_string_field(row, "kind", index),
            lane=_string_field(row, "lane", index),
            locator=_string_field(row, "locator", index),
            role=_string_field(row, "role", index),
        )
        if key in sources:
            duplicates.append(key)
        sources[key] = source
    if duplicates:
        raise ScholarshipError(
            "duplicate scholarship matrix keys: " + ", ".join(sorted(duplicates))
        )
    return sources


def audit_scholarship(
    manuscript_dir: Path,
    matrix_path: Path,
    bib_path: Path,
) -> ScholarshipAudit:
    """Compute scholarship coverage and return all issues without raising."""
    sources = load_source_matrix(matrix_path)
    section_citations = extract_manuscript_citations(manuscript_dir)
    cited_keys = frozenset(
        key for citations in section_citations.values() for key in citations
    )
    bib_keys = parse_bib_keys(Path(bib_path).read_text(encoding="utf-8"))

    invalid_sources: list[str] = []
    for source in sources.values():
        if source.lane not in EXPECTED_LANES:
            invalid_sources.append(f"{source.key}: unknown lane {source.lane!r}")
        if source.kind not in VALID_KINDS:
            invalid_sources.append(f"{source.key}: unknown kind {source.kind!r}")
        if not role_is_claim_specific(source.lane, source.role):
            invalid_sources.append(
                f"{source.key}: role is not claim-specific "
                "(needs at least two lane-relevant content tokens)"
            )
        if not _locator_has_authority(source.locator):
            invalid_sources.append(
                f"{source.key}: locator lacks DOI, URL, ISBN, or book id"
            )

    cited_source_lanes = {
        sources[key].lane for key in cited_keys if key in sources and sources[key].lane
    }
    missing_lanes = tuple(
        lane for lane in EXPECTED_LANES if lane not in cited_source_lanes
    )
    return ScholarshipAudit(
        sources=sources,
        bib_keys=bib_keys,
        section_citations=section_citations,
        missing_matrix_entries=tuple(sorted(cited_keys - sources.keys())),
        missing_bib_entries=tuple(sorted(cited_keys - bib_keys)),
        matrix_entries_missing_bib=tuple(sorted(sources.keys() - bib_keys)),
        invalid_sources=tuple(sorted(invalid_sources)),
        unused_matrix_entries=tuple(sorted(sources.keys() - cited_keys)),
        uncited_bib_entries=tuple(sorted(bib_keys - cited_keys)),
        missing_lanes=missing_lanes,
    )


def validate_scholarship(
    manuscript_dir: Path,
    matrix_path: Path,
    bib_path: Path,
) -> ScholarshipAudit:
    """Validate scholarship coverage, raising if any coverage contract fails."""
    audit = audit_scholarship(manuscript_dir, matrix_path, bib_path)
    issues = audit.issues()
    if issues:
        raise ScholarshipError("; ".join(issues))
    return audit


def write_scholarship_audit(audit: ScholarshipAudit, path: Path) -> Path:
    """Write the deterministic scholarship audit JSON artifact."""
    return write_json_artifact(Path(path), audit.to_dict())


def _string_field(row: dict[str, Any], field: str, index: int) -> str:
    value = row.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ScholarshipError(f"sources[{index}].{field} must be a non-empty string")
    return value.strip()


def _normalize_role_tokens(role: str) -> list[str]:
    """Normalize role text to lowercase content tokens with punctuation removed."""
    tokens: list[str] = []
    for raw_token in role.split():
        token = _ROLE_TOKEN_RE.sub("", raw_token.lower())
        if token:
            tokens.append(token)
    return tokens


def _locator_has_authority(locator: str) -> bool:
    lower = locator.lower()
    return any(
        marker in lower
        for marker in (
            "arxiv:",
            "book:",
            "doi:",
            "isbn:",
            "jstor:",
            "url:",
        )
    )
