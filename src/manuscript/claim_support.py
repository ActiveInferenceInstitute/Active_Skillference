"""Validate manuscript scientific claims against declared evidence support."""

from __future__ import annotations

import re
import unicodedata
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

from src.artifacts.json_io import write_json_artifact
from src.provenance.binding import unbacked_numbers_in_text
from src.scholarship.coverage import load_source_matrix, parse_bib_keys


class ClaimSupportError(ValueError):
    """Raised when manuscript claim-support anchors are incomplete or stale."""


VALID_CLAIM_TYPES: frozenset[str] = frozenset(
    {
        "computed",
        "descriptive_count",
        "simulation",
        "literature",
        "scope_limit",
        "delivery",
        "visual",
    }
)

STRONG_WORDS: tuple[str, ...] = (
    "secure",
    "prove",
    "proves",
    "proved",
    "proof",
    "empirical",
    "universal",
    "guarantee",
    "guarantees",
    "guaranteed",
    "significant",
    "validated",
    "statistically",
)
STRONG_PHRASES: tuple[str, ...] = (
    "national-security grade",
    "national security grade",
    "government validated",
    "government-validated",
    "nsa approved",
    "nsa-approved",
)

# A validator entry that is a repo-relative source path (vs. a shell command such as
# "uv run pytest --cov=src"). Only path-shaped entries are checked for on-disk existence;
# command-style entries are left to the build to run.
_VALIDATOR_PATH_RE = re.compile(r"^(?:scripts|src|tests)/[\w./-]+\.py$")

_ANCHOR_RE = re.compile(r"<!--\s*claim-support:([A-Za-z0-9_-]+)\s*-->")
_CLAIM_TOKEN_RE = re.compile(r"\{\{claim:([A-Za-z0-9_.:-]+)\}\}")
_VARIABLE_RE = re.compile(r"\{\{([A-Za-z][A-Za-z0-9_]*)\}\}")
_CITATION_RE = re.compile(r"@([A-Za-z0-9_:-]+)")
_FIGURE_REF_RE = re.compile(r"@fig:([A-Za-z0-9_:-]+)")
_CODE_RE = re.compile(r"```.*?```|`[^`\n]*`", re.DOTALL)
_STRONG_WORD_RE = re.compile(
    r"\b(" + "|".join(re.escape(word) for word in STRONG_WORDS) + r")\b",
    re.IGNORECASE,
)


def _flexible_phrase_pattern(phrase: str) -> str:
    """Match a banned phrase across whitespace/hyphen variants between its words.

    "nsa approved" must also catch "nsa-approved", "nsa  approved", a line break, or
    an NBSP between the words — otherwise an irregular separator silently evades the
    blocklist (the same evasion class as zero-width characters).
    """

    words = re.split(r"[\s\-]+", phrase.strip())
    return r"[\s\- ]+".join(re.escape(word) for word in words if word)


_STRONG_PHRASE_RE = re.compile(
    "|".join(_flexible_phrase_pattern(phrase) for phrase in STRONG_PHRASES),
    re.IGNORECASE,
)


_CODE_SPAN_RE = re.compile(r"```.*?```|`[^`\n]*`", re.DOTALL)


def find_banned_phrases(text: str) -> list[str]:
    """Return any endorsement-overreach phrases (e.g. "NSA approved") found in ``text``.

    Reusable so the same blocklist that guards manuscript prose can also guard the
    learner-facing curriculum and quiz content (the published SkillTree surface), not
    just the manuscript anchors. The text is NFKC-normalized and category-Cf
    (zero-width) characters are stripped first so unicode separators cannot evade the
    blocklist.
    """
    normalized = unicodedata.normalize(
        "NFKC", "".join(ch for ch in text if unicodedata.category(ch) != "Cf")
    )
    return [match.group(0) for match in _STRONG_PHRASE_RE.finditer(normalized)]


def audit_manuscript_banned_phrases(manuscript_dir: Path) -> dict[str, list[str]]:
    """Scan every manuscript ``.md`` file for endorsement-overreach phrases.

    The per-anchor strong-word audit only inspects claim-support paragraphs; this
    closes the gap by scanning the WHOLE manuscript prose surface for the endorsement
    blocklist (the same one that guards the learner-facing curriculum). Returns a
    mapping of filename -> matched phrases for any file with a hit (empty when clean).
    Inline code spans are stripped first so a phrase quoted as code is not flagged.
    """

    findings: dict[str, list[str]] = {}
    for path in sorted(Path(manuscript_dir).glob("*.md")):
        text = _CODE_SPAN_RE.sub(" ", path.read_text(encoding="utf-8"))
        hits = find_banned_phrases(text)
        if hits:
            findings[path.name] = hits
    return findings


_DEFAULT_LIMIT_MARKERS = (
    "not",
    "scope",
    "limit",
    "boundary",
    "future",
    "remain",
    "rather than",
    "out of scope",
)


@dataclass(frozen=True)
class ClaimSupportRow:
    """One expected scientific claim support record."""

    claim_id: str
    claim_type: str
    summary: str
    section: str
    claim_tokens: tuple[str, ...]
    variables: tuple[str, ...]
    citations: tuple[str, ...]
    figures: tuple[str, ...]
    validators: tuple[str, ...]
    limitation_markers: tuple[str, ...]
    allow_strong_words: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        """Return deterministic JSON data for generated evidence audits."""
        return {
            "allowStrongWords": list(self.allow_strong_words),
            "citations": list(self.citations),
            "claimTokens": list(self.claim_tokens),
            "figures": list(self.figures),
            "id": self.claim_id,
            "limitationMarkers": list(self.limitation_markers),
            "section": self.section,
            "summary": self.summary,
            "type": self.claim_type,
            "validators": list(self.validators),
            "variables": list(self.variables),
        }


@dataclass(frozen=True)
class ClaimAnchorContext:
    """One manuscript claim-support anchor and the paragraph it governs."""

    claim_id: str
    section: str
    line: int
    text: str
    evidence_text: str = ""

    def location(self) -> str:
        """Return a compact manuscript location."""
        return f"{self.section}:{self.line}"

    def evidence_scope(self) -> str:
        return self.evidence_text or self.text


@dataclass(frozen=True)
class ClaimSupportAudit:
    """Computed support audit for manuscript scientific claim anchors."""

    rows: tuple[ClaimSupportRow, ...]
    anchors: tuple[ClaimAnchorContext, ...]
    issues_found: tuple[str, ...]

    def issues(self) -> tuple[str, ...]:
        """Return human-readable issues."""
        return self.issues_found

    def to_dict(self) -> dict[str, Any]:
        """Return deterministic JSON evidence taxonomy data."""
        type_counts = Counter(row.claim_type for row in self.rows)
        anchored_counts = Counter(anchor.claim_id for anchor in self.anchors)
        evidence_classes = {
            "citations": sum(bool(row.citations) for row in self.rows),
            "claimTokens": sum(bool(row.claim_tokens) for row in self.rows),
            "figures": sum(bool(row.figures) for row in self.rows),
            "limitationMarkers": sum(bool(row.limitation_markers) for row in self.rows),
            "validators": sum(bool(row.validators) for row in self.rows),
            "variables": sum(bool(row.variables) for row in self.rows),
        }
        return {
            "anchors": [
                {
                    "id": anchor.claim_id,
                    "line": anchor.line,
                    "section": anchor.section,
                }
                for anchor in self.anchors
            ],
            "issues": list(self.issues()),
            "rows": [row.to_dict() for row in self.rows],
            "summary": {
                "anchors": len(self.anchors),
                "claimRows": len(self.rows),
                "evidenceClasses": evidence_classes,
                "issueCount": len(self.issues()),
                "typeCounts": dict(sorted(type_counts.items())),
                "uniqueAnchoredClaims": len(anchored_counts),
            },
        }


def load_claim_support(path: Path) -> tuple[ClaimSupportRow, ...]:
    """Load and validate the manuscript claim-support declaration file."""
    payload = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("claims"), list):
        raise ClaimSupportError("claim-support file must contain a claims list")
    rows: list[ClaimSupportRow] = []
    seen: set[str] = set()
    for index, raw in enumerate(payload["claims"], start=1):
        if not isinstance(raw, dict):
            raise ClaimSupportError(f"claim-support row {index} must be an object")
        claim_id = _string_field(raw, "id", index)
        if claim_id in seen:
            raise ClaimSupportError(f"duplicate claim-support id: {claim_id}")
        seen.add(claim_id)
        claim_type = _string_field(raw, "type", index)
        if claim_type not in VALID_CLAIM_TYPES:
            raise ClaimSupportError(
                f"claim-support row {index}.type must be one of "
                + ", ".join(sorted(VALID_CLAIM_TYPES))
            )
        rows.append(
            ClaimSupportRow(
                claim_id=claim_id,
                claim_type=claim_type,
                summary=_string_field(raw, "summary", index),
                section=_optional_string(raw, "section"),
                claim_tokens=_string_tuple(raw, "claim_tokens", index),
                variables=_string_tuple(raw, "variables", index),
                citations=_string_tuple(raw, "citations", index),
                figures=tuple(
                    _normalize_figure_id(item)
                    for item in _string_tuple(raw, "figures", index)
                ),
                validators=_string_tuple(raw, "validators", index),
                limitation_markers=_string_tuple(raw, "limitation_markers", index),
                allow_strong_words=tuple(
                    word.lower()
                    for word in _string_tuple(raw, "allow_strong_words", index)
                ),
            )
        )
    return tuple(rows)


def audit_claim_support(
    *,
    manuscript_dir: Path,
    support_path: Path,
    source_matrix_path: Path,
    bib_path: Path,
    registry_claim_ids: Iterable[str] | None = None,
    project_root: Path | None = None,
) -> ClaimSupportAudit:
    """Audit claim-support anchors against manuscript paragraphs and evidence classes.

    When ``registry_claim_ids`` is supplied, every ``claim_tokens`` entry a row declares
    must name a real kernel-registered claim — closing the drift where a row's declared
    token is renamed or deleted in the kernels but lingers in the YAML (and is otherwise
    only text-checked for ``computed``/``simulation`` rows, never for the others). When
    ``project_root`` is supplied, every path-shaped ``validators`` entry must exist on
    disk, so a typo'd or deleted validator script cannot pass as a declared delivery
    check. Both default to ``None`` (skip) for callers that do not need the optional
    checks; the production orchestrator (``scripts/run_kernels.py``) passes both, so the
    build path is strict.
    """
    rows = load_claim_support(support_path)
    rows_by_id = {row.claim_id: row for row in rows}
    anchors = extract_claim_anchor_contexts(manuscript_dir)
    source_keys = set(load_source_matrix(source_matrix_path))
    bib_keys = set(parse_bib_keys(Path(bib_path).read_text(encoding="utf-8")))
    issues: list[str] = []

    if registry_claim_ids is not None:
        known_claims = set(registry_claim_ids)
        for decl_row in rows:
            for token in sorted(set(decl_row.claim_tokens) - known_claims):
                issues.append(
                    f"{decl_row.claim_id} declares claim token {token!r} that is absent "
                    "from the kernel claim registry"
                )
    if project_root is not None:
        for decl_row in rows:
            for validator in decl_row.validators:
                if (
                    _VALIDATOR_PATH_RE.match(validator)
                    and not (Path(project_root) / validator).is_file()
                ):
                    issues.append(
                        f"{decl_row.claim_id} declares validator path {validator!r} "
                        "that does not exist"
                    )

    anchored_ids = [anchor.claim_id for anchor in anchors]
    duplicated_anchor_ids = sorted(
        claim_id for claim_id, count in Counter(anchored_ids).items() if count > 1
    )
    if duplicated_anchor_ids:
        issues.append(
            "duplicate claim-support anchors: " + ", ".join(duplicated_anchor_ids)
        )

    missing_rows = sorted(set(anchored_ids) - set(rows_by_id))
    if missing_rows:
        issues.append("claim-support anchors missing rows: " + ", ".join(missing_rows))

    unused_rows = sorted(set(rows_by_id) - set(anchored_ids))
    if unused_rows:
        issues.append(
            "claim-support rows not anchored in manuscript: " + ", ".join(unused_rows)
        )

    for anchor in anchors:
        row = rows_by_id.get(anchor.claim_id)
        if row is None:
            continue
        if row.section and row.section != anchor.section:
            issues.append(
                f"{anchor.location()}: row section {row.section} does not match anchor"
            )
        issues.extend(_audit_evidence(row, anchor, source_keys, bib_keys))
        issues.extend(_audit_strong_words(row, anchor))

    return ClaimSupportAudit(rows=rows, anchors=anchors, issues_found=tuple(issues))


def validate_claim_support(
    *,
    manuscript_dir: Path,
    support_path: Path,
    source_matrix_path: Path,
    bib_path: Path,
    registry_claim_ids: Iterable[str] | None = None,
    project_root: Path | None = None,
) -> ClaimSupportAudit:
    """Validate manuscript claim-support rows, raising on incomplete evidence."""
    audit = audit_claim_support(
        manuscript_dir=manuscript_dir,
        support_path=support_path,
        source_matrix_path=source_matrix_path,
        bib_path=bib_path,
        registry_claim_ids=registry_claim_ids,
        project_root=project_root,
    )
    if audit.issues():
        raise ClaimSupportError(
            "manuscript claim-support validation failed:\n  "
            + "\n  ".join(audit.issues())
        )
    return audit


def write_claim_support_audit(audit: ClaimSupportAudit, path: Path) -> Path:
    """Write deterministic claim-support audit JSON."""
    return write_json_artifact(Path(path), audit.to_dict())


def extract_claim_anchor_contexts(
    manuscript_dir: Path,
) -> tuple[ClaimAnchorContext, ...]:
    """Return claim-support anchors and their governed paragraphs."""
    contexts: list[ClaimAnchorContext] = []
    for path in sorted(Path(manuscript_dir).glob("[0-9][0-9]*_*.md")):
        text = _CODE_RE.sub(" ", path.read_text(encoding="utf-8"))
        paragraphs = _paragraphs_with_lines(text)
        for index, (line, paragraph) in enumerate(paragraphs):
            ids = _ANCHOR_RE.findall(paragraph)
            if not ids:
                continue
            body = _ANCHOR_RE.sub("", paragraph).strip()
            if not body and index + 1 < len(paragraphs):
                body = paragraphs[index + 1][1].strip()
            elif index + 1 < len(paragraphs) and len(body.split()) < 8:
                body = f"{body}\n\n{paragraphs[index + 1][1].strip()}"
            for claim_id in ids:
                contexts.append(
                    ClaimAnchorContext(
                        claim_id=claim_id,
                        section=path.name,
                        line=line,
                        text=body,
                        evidence_text=_governed_anchor_block(text, line),
                    )
                )
    return tuple(contexts)


def _audit_evidence(
    row: ClaimSupportRow,
    anchor: ClaimAnchorContext,
    source_keys: set[str],
    bib_keys: set[str],
) -> list[str]:
    text = anchor.evidence_scope()
    issues: list[str] = []
    location = anchor.location()
    claim_tokens = set(_CLAIM_TOKEN_RE.findall(text))
    variables = set(_VARIABLE_RE.findall(text)) - {"claim"}
    citations = set(_CITATION_RE.findall(text))
    figures = {"fig:" + figure for figure in _FIGURE_REF_RE.findall(text)}

    issues.extend(
        _missing_items(
            location, row.claim_id, "claim token", row.claim_tokens, claim_tokens
        )
    )
    issues.extend(
        _missing_items(
            location, row.claim_id, "manuscript variable", row.variables, variables
        )
    )
    issues.extend(
        _missing_items(location, row.claim_id, "citation", row.citations, citations)
    )
    issues.extend(
        _missing_items(location, row.claim_id, "figure", row.figures, figures)
    )
    for citation in row.citations:
        if citation not in source_keys:
            issues.append(
                f"{location}: {row.claim_id} citation {citation} missing from source matrix"
            )
        if citation not in bib_keys:
            issues.append(
                f"{location}: {row.claim_id} citation {citation} missing from references.bib"
            )

    if row.claim_type == "computed":
        # A computed claim with NO declared claim_tokens makes _missing_items vacuous
        # (empty - anything == empty), so a bare hand-typed result number in prose would
        # pass unbacked. Require at least one declared+present claim token.
        if not row.claim_tokens:
            issues.append(
                f"{location}: {row.claim_id} computed row needs ≥1 claim_token "
                f"(bare result numbers must resolve to a tested kernel claim)"
            )
        issues.extend(_unbacked_number_issues(location, row.claim_id, text))
    elif row.claim_type == "descriptive_count":
        if not row.variables:
            issues.append(
                f"{location}: {row.claim_id} descriptive_count row needs variables"
            )
    elif row.claim_type == "simulation":
        if not row.claim_tokens and not row.figures:
            issues.append(
                f"{location}: {row.claim_id} simulation row needs claim_tokens or figures"
            )
        issues.extend(_unbacked_number_issues(location, row.claim_id, text))
    elif row.claim_type == "literature":
        if not row.citations:
            issues.append(f"{location}: {row.claim_id} literature row needs citations")
    elif row.claim_type == "scope_limit":
        markers = row.limitation_markers or _DEFAULT_LIMIT_MARKERS
        lowered = text.lower()
        if not any(marker.lower() in lowered for marker in markers):
            issues.append(
                f"{location}: {row.claim_id} scope_limit lacks limitation marker"
            )
    elif row.claim_type == "delivery" and not row.validators:
        issues.append(f"{location}: {row.claim_id} delivery row needs validators")
    elif row.claim_type == "visual" and not row.figures:
        issues.append(f"{location}: {row.claim_id} visual row needs figures")
    return issues


def _audit_strong_words(row: ClaimSupportRow, anchor: ClaimAnchorContext) -> list[str]:
    allowed = set(row.allow_strong_words)
    issues: list[str] = []
    for match in _STRONG_WORD_RE.finditer(anchor.text):
        word = match.group(1).lower()
        if word not in allowed:
            issues.append(
                f"{anchor.location()}: {row.claim_id} uses unsupported strong word {word!r}"
            )
    for match in _STRONG_PHRASE_RE.finditer(anchor.text):
        phrase = match.group(0).lower()
        if phrase not in allowed:
            issues.append(
                f"{anchor.location()}: {row.claim_id} uses unsupported strong phrase {phrase!r}"
            )
    return issues


def _missing_items(
    location: str,
    claim_id: str,
    label: str,
    required: Iterable[str],
    found: set[str],
) -> list[str]:
    missing = sorted(set(required) - found)
    return [f"{location}: {claim_id} missing {label} {item}" for item in missing]


def _unbacked_number_issues(location: str, claim_id: str, text: str) -> list[str]:
    """Reject bare hand-typed result numbers in a computed/simulation claim's prose.

    Declaring claim_tokens proves a binding *exists*; this proves no result number
    *bypassed* it. Math spans and ``{{claim:NAME}}`` tokens are stripped first, so only
    drift-prone hand-typed literals are reported.
    """
    return [
        f"{location}: {claim_id} hand-typed result {unbacked.value!r} "
        f"(must resolve through a {{{{claim:...}}}} token): ...{unbacked.context}..."
        for unbacked in unbacked_numbers_in_text(text, label=claim_id)
    ]


def _paragraphs_with_lines(text: str) -> list[tuple[int, str]]:
    paragraphs: list[tuple[int, str]] = []
    current: list[str] = []
    start = 1
    for lineno, line in enumerate(text.splitlines(), start=1):
        if line.strip():
            if not current:
                start = lineno
            current.append(line)
        elif current:
            paragraphs.append((start, "\n".join(current)))
            current = []
    if current:
        paragraphs.append((start, "\n".join(current)))
    return paragraphs


def _governed_anchor_block(text: str, start_line: int) -> str:
    lines = text.splitlines()
    start = max(0, start_line - 1)
    block: list[str] = []
    for index in range(start, len(lines)):
        line = lines[index]
        if index > start and (_ANCHOR_RE.search(line) or _is_heading(line)):
            break
        block.append(_ANCHOR_RE.sub("", line))
    return "\n".join(block).strip()


def _is_heading(line: str) -> bool:
    return bool(re.match(r"^#{1,6}\s+", line))


def _string_field(row: dict[str, Any], field: str, index: int) -> str:
    value = row.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ClaimSupportError(f"claim-support row {index}.{field} must be a string")
    return value.strip()


def _optional_string(row: dict[str, Any], field: str) -> str:
    value = row.get(field, "")
    return value.strip() if isinstance(value, str) else ""


def _string_tuple(row: dict[str, Any], field: str, index: int) -> tuple[str, ...]:
    value = row.get(field)
    if value in (None, ""):
        return ()
    if not isinstance(value, list) or not all(
        isinstance(item, str) and item.strip() for item in value
    ):
        raise ClaimSupportError(
            f"claim-support row {index}.{field} must be a list of strings"
        )
    return tuple(item.strip() for item in value)


def _normalize_figure_id(value: str) -> str:
    return value if value.startswith("fig:") else f"fig:{value}"
