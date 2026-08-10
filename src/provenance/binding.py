"""Bind skill content to kernel-derived claims.

This is the gate that makes the platform *high-integrity*: a skill description may
only show a quantitative result through a ``{{claim:NAME}}`` token that resolves to a
value some tested kernel registered in a :class:`~src.provenance.claims.ClaimRegistry`.

Three operations:

* :func:`render` — substitute every claim token with its registered value.
* :func:`validate_skill` / :func:`validate_curriculum` — fail closed if any token has
  no backing claim (so a typo or a deleted kernel breaks the build, not the learner).
* :func:`find_unbacked_numbers` — the numeric-provenance linter: flag decimal *result*
  numbers that were hand-typed into prose instead of arriving through a claim token.

The linter intentionally errs toward catching laundered numbers: any literal with two
or more decimal places that sits in plain prose (not inside ``$…$`` LaTeX math, not
inside a ``{{claim:…}}`` token, not in the allowlist) is reported.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, replace
from pathlib import Path

from src.curriculum.graph import CurriculumGraph
from src.curriculum.model import CLAIM_TOKEN_RE, Skill, Subject
from src.provenance.claims import ClaimRegistry

# The shape a computed *result* takes: either a decimal with >=2 fractional digits
# (e.g. 1.6094) or scientific notation (e.g. 1.6e-3, 5E10). Integers, years, and
# single-decimal counts (0.5, version 4.2) are deliberately NOT flagged — they are
# almost always parameters/probabilities/versions, not derived results, and flagging
# them would drown real laundering in false positives.
_DECIMAL_RESULT_RE = re.compile(
    r"(?<![\w.])\d+(?:\.\d+)?[eE][+-]?\d+(?![\w])"  # scientific notation
    r"|(?<![\w.])\d+\.\d{2,}(?![\w])"  # >=2-decimal result
)
_UNIT_RESULT_RE = re.compile(
    # ``\.\d+`` (one-or-more fractional digits), not ``\.\d`` (exactly one): a
    # multi-decimal unit value such as "1.60 nats" or "2.718 bits" must be captured
    # in full, otherwise the value group backtracks to empty and the whole match
    # fails, silently letting a hand-typed unit result slip past the linter.
    r"(?P<value>(?<![\w.])\d+(?:\.\d+)?)\s+(?:nats?|bits?)\b",
    re.IGNORECASE,
)
# Inline/﻿block LaTeX math spans, where coefficients legitimately live.
_MATH_SPAN_RE = re.compile(r"\$\$.*?\$\$|\$.*?\$", re.DOTALL)
# Any ``{{``-opened placeholder mentioning ``claim`` (whitespace-tolerant). Used only as a
# fail-closed leftover detector after a well-formed render: catches malformed/whitespaced
# tokens (``{{ claim:e }}``) that the strict ``CLAIM_TOKEN_RE`` never substituted.
_MALFORMED_CLAIM_RE = re.compile(r"\{\{\s*claim\b", re.IGNORECASE)


class ProvenanceError(ValueError):
    """Raised when skill content references a claim with no backing kernel value."""


@dataclass(frozen=True)
class UnbackedNumber:
    """A hand-typed decimal result found in prose with no provenance."""

    skill_id: str
    value: str
    context: str


def _strip_format_chars(text: str) -> str:
    """Remove Unicode *format* characters (category Cf: zero-width space U+200B,
    ZWJ/ZWNJ, BOM, word-joiner, …).

    These are invisible and neither ``\\s`` nor ``\\b`` match them, so a token or number
    split by one (``{{<ZWSP>claim:e}}``, ``1<ZWSP>.6094``) would slip past both the
    malformed-token check and the unbacked-number linter. Stripping them before any
    integrity scan closes that bypass class; they have no legitimate place in curriculum
    prose, so removal is safe and makes the gates see the real glyph sequence.
    """
    return "".join(ch for ch in text if unicodedata.category(ch) != "Cf")


def render(text: str, registry: ClaimRegistry) -> str:
    """Replace every ``{{claim:NAME}}`` with its rendered value.

    Raises :class:`ProvenanceError` if a referenced claim is not registered.
    """
    text = _strip_format_chars(text)

    def _sub(match: re.Match[str]) -> str:
        name = match.group(1)
        if not registry.has(name):
            raise ProvenanceError(f"unresolved claim token {{{{claim:{name}}}}}")
        return registry.get(name).rendered()

    rendered = CLAIM_TOKEN_RE.sub(_sub, text)
    # Fail closed on malformed leftovers: a well-formed token always substitutes, so any
    # residual ``{{``-opened claim placeholder is malformed/empty/whitespaced (e.g.
    # ``{{claim:}}``, ``{{ claim:e }}``, ``{{claim: e}}``) and would otherwise reach
    # learner-facing text literally. Match the CLASS (whitespace-tolerant), not the exact
    # ``{{claim:`` literal — a substring check missed ``{{ claim:e }}`` (interior spaces).
    if _MALFORMED_CLAIM_RE.search(rendered):
        raise ProvenanceError(f"malformed claim token left unrendered in: {text!r}")
    return rendered


def validate_skill(skill: Skill, registry: ClaimRegistry) -> None:
    """Raise if any claim token in the skill is unbacked."""
    missing = sorted(t for t in skill.claim_tokens() if not registry.has(t))
    if missing:
        raise ProvenanceError(
            f"skill {skill.skill_id!r} references unbacked claims: {', '.join(missing)}"
        )


def validate_curriculum(skills: list[Skill], registry: ClaimRegistry) -> None:
    """Fail closed if ANY skill references an unbacked claim. Used by the exporter."""
    problems: list[str] = []
    for skill in skills:
        missing = sorted(t for t in skill.claim_tokens() if not registry.has(t))
        if missing:
            problems.append(f"{skill.skill_id}: {', '.join(missing)}")
    if problems:
        raise ProvenanceError(
            "unbacked claim tokens (export refused):\n  " + "\n  ".join(problems)
        )


def render_graph(graph: CurriculumGraph, registry: ClaimRegistry) -> CurriculumGraph:
    """Return a copy of the graph with every claim token resolved in EVERY learner-facing
    field: subject description, skill name/objective/description, and each assessment's
    prompt and answer options.

    Fails closed: :func:`render` raises :class:`ProvenanceError` on any unbacked OR
    malformed token, so an unresolved/literal claim cannot reach the SkillTree export
    through any field — not just ``description``.
    """

    def _render(text: str) -> str:
        return render(text, registry)

    new_subjects: list[Subject] = []
    for subject in graph.subjects:
        rendered_skills = tuple(
            replace(
                skill,
                name=_render(skill.name),
                objective=_render(skill.objective),
                description=_render(skill.description),
                assessments=tuple(
                    replace(
                        q,
                        prompt=_render(q.prompt),
                        answers=tuple(_render(a) for a in q.answers),
                    )
                    for q in skill.assessments
                ),
            )
            for skill in subject.skills
        )
        new_subjects.append(
            replace(
                subject,
                description=_render(subject.description),
                skills=rendered_skills,
            )
        )
    return CurriculumGraph(subjects=new_subjects)


def _strip_protected(text: str) -> str:
    """Remove LaTeX math spans and claim tokens before scanning prose for numbers."""
    # Drop zero-width/format chars first so "1<ZWSP>.6094" cannot hide from the linter.
    without_format = _strip_format_chars(text)
    without_math = _MATH_SPAN_RE.sub(" ", without_format)
    return CLAIM_TOKEN_RE.sub(" ", without_math)


def _scan_text(text: str, label: str, allow: tuple[str, ...]) -> list[UnbackedNumber]:
    prose = _strip_protected(text)
    found: list[UnbackedNumber] = []
    reported_spans: list[tuple[int, int]] = []
    for match in _DECIMAL_RESULT_RE.finditer(prose):
        literal = match.group(0)
        if literal in allow:
            continue
        reported_spans.append(match.span())
        found.append(_issue_from_match(prose, label, literal, match.span()))
    for match in _UNIT_RESULT_RE.finditer(prose):
        literal = match.group("value")
        span = match.span("value")
        if literal in allow or _overlaps_reported_span(span, reported_spans):
            continue
        reported_spans.append(span)
        found.append(_issue_from_match(prose, label, literal, span))
    return found


def _issue_from_match(
    prose: str, label: str, literal: str, span: tuple[int, int]
) -> UnbackedNumber:
    start = max(0, span[0] - 25)
    end = min(len(prose), span[1] + 25)
    return UnbackedNumber(
        skill_id=label, value=literal, context=prose[start:end].strip()
    )


def _overlaps_reported_span(
    candidate: tuple[int, int], reported: list[tuple[int, int]]
) -> bool:
    for start, end in reported:
        if candidate[0] < end and start < candidate[1]:
            return True
    return False


def unbacked_numbers_in_text(
    text: str, *, label: str = "text", allow: tuple[str, ...] = ()
) -> list[UnbackedNumber]:
    """Return hand-typed decimal/unit result numbers in arbitrary prose.

    Math spans and ``{{claim:NAME}}`` tokens are stripped first, so only bare results
    that bypassed the provenance binding are reported. Used by the manuscript
    claim-support audit to enforce that ``computed``/``simulation`` claims show numbers
    only through resolved claim tokens — not as drift-prone hand-typed literals.
    """
    return _scan_text(text, label, allow)


def find_unbacked_numbers(
    skill: Skill, *, allow: tuple[str, ...] = ()
) -> list[UnbackedNumber]:
    """Return decimal result numbers hand-typed into a skill's learner-facing prose.

    Scans every **expository** free-text field a learner reads and that is meant to
    carry derived results: the skill **name**, **objective**, **description**, and each
    assessment question **prompt** (stem). A hand-typed result in any of these is a
    provenance defect.

    Wrong assessment answer options are intentionally out of scope: distractors are
    hand-authored wrong answers that legitimately contain arbitrary numbers. Correct
    answer options are scanned because a derived numeric value can otherwise bypass the
    provenance gate by living only in the answer key. ``allow`` lists literal numeric
    strings that are legitimately prose constants.
    """
    found = _scan_text(skill.name, skill.skill_id, allow)
    found += _scan_text(skill.objective, skill.skill_id, allow)
    found += _scan_text(skill.description, skill.skill_id, allow)
    for question in skill.assessments:
        found += _scan_text(question.prompt, skill.skill_id, allow)
        for index in question.correct:
            found += _scan_text(question.answers[index], skill.skill_id, allow)
    return found


def lint_curriculum(
    skills: list[Skill], *, allow: tuple[str, ...] = ()
) -> list[UnbackedNumber]:
    """Run the bare-number linter across all skills' names + descriptions."""
    violations: list[UnbackedNumber] = []
    for skill in skills:
        violations.extend(find_unbacked_numbers(skill, allow=allow))
    return violations


def lint_graph(
    graph: CurriculumGraph, *, allow: tuple[str, ...] = ()
) -> list[UnbackedNumber]:
    """Lint every learner-facing free-text field in the graph: subject descriptions,
    skill names, and skill descriptions. Empty list == clean."""
    violations = lint_curriculum(graph.skills, allow=allow)
    for subject in graph.subjects:
        violations.extend(_scan_text(subject.description, subject.subject_id, allow))
    return violations


# Fenced ```...``` blocks and inline `...` code spans, where a `{{claim:NAME}}` token is
# documentation about the syntax (an illustrative placeholder), not a live reference.
_CODE_SPAN_RE = re.compile(r"```.*?```|`[^`\n]*`", re.DOTALL)


def manuscript_claim_tokens(text: str) -> list[str]:
    """Return every claim name *referenced* via ``{{claim:NAME}}`` in manuscript prose.

    The manuscript is rendered to PDF with these tokens substituted from
    ``manuscript_variables.json`` (built from the same kernel-emitted
    :class:`ClaimRegistry`). A token with no backing claim would render literally into
    the published PDF — so the manuscript is a learner-facing provenance surface exactly
    like skill content, and must be validated the same way.

    Tokens inside code spans/fences (e.g. a ``\\`{{claim:NAME}}\\``` literal documenting
    the token syntax) are illustrative, not live references, and are excluded — mirroring
    how the number linter excludes LaTeX math spans.
    """
    prose = _CODE_SPAN_RE.sub(" ", text)
    return [m.group(1) for m in CLAIM_TOKEN_RE.finditer(prose)]


def validate_manuscript_text(
    text: str, registry: ClaimRegistry, *, source: str = "manuscript"
) -> None:
    """Fail closed if any ``{{claim:NAME}}`` in manuscript prose is unbacked.

    Closes the provenance gap whereby manuscript prose could reference a claim token
    that no kernel emits (e.g. after a kernel refactor renames a claim), letting a dead
    token render literally into the published PDF undetected by the skill-only gate.
    """
    missing = sorted({t for t in manuscript_claim_tokens(text) if not registry.has(t)})
    if missing:
        raise ProvenanceError(
            f"{source} references unbacked claim tokens: {', '.join(missing)}"
        )


def validate_manuscript_dir(
    manuscript_dir: Path, registry: ClaimRegistry
) -> dict[str, list[str]]:
    """Validate every ``*.md`` under ``manuscript_dir`` against the registry.

    Returns a mapping of filename → referenced claim names (for reporting). Raises
    :class:`ProvenanceError` on the first file that references an unbacked token, so a
    dead manuscript claim token is a build failure, not a silent literal in the PDF.
    """
    referenced: dict[str, list[str]] = {}
    for md_path in sorted(Path(manuscript_dir).glob("*.md")):
        text = md_path.read_text(encoding="utf-8")
        tokens = manuscript_claim_tokens(text)
        if tokens:
            referenced[md_path.name] = tokens
            validate_manuscript_text(text, registry, source=md_path.name)
    return referenced
