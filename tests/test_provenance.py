"""Tests for the content-provenance registry and binding gate."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from src.curriculum.graph import CurriculumGraph
from src.curriculum.model import AssessmentQuestion, Skill, Stratum, Subject
from src.provenance.binding import (
    _UNIT_RESULT_RE,
    ProvenanceError,
    find_unbacked_numbers,
    lint_curriculum,
    lint_graph,
    manuscript_claim_tokens,
    render,
    render_graph,
    unbacked_numbers_in_text,
    validate_curriculum,
    validate_manuscript_dir,
    validate_manuscript_text,
    validate_skill,
)
from src.provenance.claims import Claim, ClaimError, ClaimRegistry

_M = Stratum.MATH_FOUNDATIONS


def _q() -> AssessmentQuestion:
    return AssessmentQuestion("Q", ("a", "b"), (0,))


def _skill(sid: str, desc: str) -> Skill:
    return Skill(sid, sid, _M, "obj", desc, (), (_q(),))


# -- ClaimRegistry ---------------------------------------------------------


def test_register_and_get() -> None:
    reg = ClaimRegistry()
    reg.register("x", 1.5, units="nats", source="fn")
    assert reg.has("x") and "x" in reg
    assert reg.value("x") == 1.5
    assert reg.get("x").units == "nats"
    assert len(reg) == 1
    assert reg.names() == ["x"]


def test_register_idempotent_same_value() -> None:
    reg = ClaimRegistry()
    reg.register("x", 1.0)
    reg.register("x", 1.0)  # no raise
    assert len(reg) == 1


def test_register_conflict_raises() -> None:
    reg = ClaimRegistry()
    reg.register("x", 1.0)
    with pytest.raises(ClaimError, match="conflicting"):
        reg.register("x", 2.0)


def test_register_empty_name_raises() -> None:
    reg = ClaimRegistry()
    with pytest.raises(ClaimError):
        reg.register("", 1.0)


def test_get_missing_raises() -> None:
    with pytest.raises(ClaimError):
        ClaimRegistry().get("nope")


def test_claim_rendered_float_and_string() -> None:
    assert Claim("a", 1.6094, "nats").rendered() == "1.6094 nats"
    assert Claim("b", "yes").rendered() == "yes"


def test_string_claim_conflict_detected() -> None:
    reg = ClaimRegistry()
    reg.register("s", "alpha")
    reg.register("s", "alpha")
    with pytest.raises(ClaimError):
        reg.register("s", "beta")


def test_to_json_round_trip(tmp_path) -> None:
    reg = ClaimRegistry()
    reg.register("x", 2.0, units="nats", source="fn", description="d")
    path = reg.to_json(tmp_path / "claims.json")
    loaded = json.loads(path.read_text())
    assert loaded["x"]["value"] == 2.0
    assert loaded["x"]["units"] == "nats"


# -- binding: render -------------------------------------------------------


def test_render_substitutes_claim() -> None:
    reg = ClaimRegistry()
    reg.register("e", 0.6931, units="nats")
    out = render("entropy is {{claim:e}}.", reg)
    assert "0.6931 nats" in out and "{{claim" not in out


def test_render_unresolved_raises() -> None:
    with pytest.raises(ProvenanceError, match="unresolved"):
        render("value {{claim:ghost}}", ClaimRegistry())


def test_validate_skill_passes_and_fails() -> None:
    reg = ClaimRegistry()
    reg.register("e", 1.0)
    validate_skill(_skill("ok", "uses {{claim:e}}"), reg)  # no raise
    with pytest.raises(ProvenanceError):
        validate_skill(_skill("bad", "uses {{claim:missing}}"), reg)


def test_validate_curriculum_fail_closed() -> None:
    reg = ClaimRegistry()
    skills = [_skill("a", "no claims"), _skill("b", "{{claim:missing}}")]
    with pytest.raises(ProvenanceError, match="export refused"):
        validate_curriculum(skills, reg)


# -- binding: numeric-provenance linter ------------------------------------


def test_linter_flags_hand_typed_result_number() -> None:
    # A bare decimal result in prose (not a claim token, not LaTeX math) is a violation.
    skill = _skill("planted", "The free energy is 1.6094 nats, obviously.")
    violations = find_unbacked_numbers(skill)
    assert len(violations) == 1
    assert violations[0].value == "1.6094"
    assert violations[0].skill_id == "planted"


def test_linter_ignores_numbers_inside_math() -> None:
    skill = _skill("mathy", "with prior $p=0.01$ and rate $\\alpha=0.05$ here")
    assert find_unbacked_numbers(skill) == []


def test_linter_ignores_claim_token_values() -> None:
    skill = _skill("bound", "the entropy is {{claim:entropy_fair_coin}} exactly")
    assert find_unbacked_numbers(skill) == []


def test_linter_allowlist_exempts_known_constant() -> None:
    # 3.14 is result-shaped (>=2 decimals) and IS flagged by default ...
    skill = _skill("pi", "the constant is 3.14 here")
    assert len(find_unbacked_numbers(skill)) == 1
    # ... but listing it in `allow` exempts it (negative control: the assertion can fail).
    assert find_unbacked_numbers(skill, allow=("3.14",)) == []


def test_lint_curriculum_aggregates() -> None:
    skills = [_skill("a", "clean"), _skill("b", "bad 3.14159 value")]
    assert len(lint_curriculum(skills)) == 1


# -- binding: render_graph -------------------------------------------------


def test_render_graph_resolves_all_descriptions() -> None:
    reg = ClaimRegistry()
    reg.register("e", 0.6931, units="nats")
    graph = CurriculumGraph(
        [Subject("sub_m", "m", _M, "d", (_skill("a", "h {{claim:e}}"),))]
    )
    rendered = render_graph(graph, reg)
    desc = rendered.subjects[0].skills[0].description
    assert "0.6931 nats" in desc and "{{claim" not in desc


def test_render_graph_fail_closed_on_missing_claim() -> None:
    graph = CurriculumGraph(
        [Subject("sub_m", "m", _M, "d", (_skill("a", "{{claim:ghost}}"),))]
    )
    with pytest.raises(ProvenanceError):
        render_graph(graph, ClaimRegistry())


# -- manuscript-token provenance gate (regression: dead-token-in-prose) -----


def test_manuscript_claim_tokens_extracts_names() -> None:
    text = "F is {{claim:vfe_descent_end}} versus {{claim:vfe_descent_start}}."
    assert manuscript_claim_tokens(text) == ["vfe_descent_end", "vfe_descent_start"]


def test_validate_manuscript_text_passes_when_all_backed() -> None:
    reg = ClaimRegistry()
    reg.register("entropy_fair_coin", 0.693147, units="nats", source="t")
    validate_manuscript_text("H = {{claim:entropy_fair_coin}} nats.", reg)  # no raise


def test_validate_manuscript_text_fails_on_dead_token() -> None:
    reg = ClaimRegistry()
    reg.register("agent_g_sample", 0.55, units="nats", source="t")
    # A token a kernel refactor renamed away (the exact 2026-06-09 defect class).
    with pytest.raises(ProvenanceError, match="agent_g_resolve"):
        validate_manuscript_text("G = {{claim:agent_g_resolve}}.", reg, source="03.md")


def test_real_manuscript_tokens_all_resolve(tmp_path) -> None:
    """Guard: every claim token in the shipped manuscript is backed by a kernel.

    This would have failed on the dead {{claim:agent_g_resolve}}/{{claim:agent_g_stay}}
    tokens left in 03_results.md after the agent example was refactored.
    """
    from src.kernels.examples import build_claim_registry

    manuscript_dir = Path(__file__).resolve().parents[1] / "manuscript"
    reg = build_claim_registry()
    referenced = validate_manuscript_dir(
        manuscript_dir, reg
    )  # raises on any dead token
    # At least the results section references kernel claims.
    assert any(tokens for tokens in referenced.values())


def test_real_manuscript_uses_pandoc_crossrefs() -> None:
    """Authored body sections should not use raw LaTeX figure references."""
    manuscript_dir = Path(__file__).resolve().parents[1] / "manuscript"
    body = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted(manuscript_dir.glob("[0-9][0-9]_*.md"))
    )
    assert r"\ref{" not in body


def test_real_manuscript_citations_have_bib_entries() -> None:
    """Every authored body citation key should exist in references.bib."""
    manuscript_dir = Path(__file__).resolve().parents[1] / "manuscript"
    body = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted(manuscript_dir.glob("[0-9][0-9]_*.md"))
    )
    body = re.sub(r"```.*?```|`[^`\n]*`", " ", body, flags=re.DOTALL)
    citation_keys = {
        key
        for key in re.findall(r"@([A-Za-z0-9_:-]+)", body)
        if not key.startswith(("fig:", "eq:", "sec:"))
    }
    bib = (manuscript_dir / "references.bib").read_text(encoding="utf-8")
    bib_keys = set(re.findall(r"@[A-Za-z]+\{([^,]+),", bib))
    assert citation_keys <= bib_keys


def test_validate_manuscript_dir_catches_planted_dead_token(tmp_path) -> None:
    reg = ClaimRegistry()
    reg.register("entropy_fair_coin", 0.693147, units="nats", source="t")
    (tmp_path / "ok.md").write_text(
        "H = {{claim:entropy_fair_coin}}.", encoding="utf-8"
    )
    (tmp_path / "bad.md").write_text(
        "G = {{claim:nonexistent_claim}}.", encoding="utf-8"
    )
    with pytest.raises(ProvenanceError, match="nonexistent_claim"):
        validate_manuscript_dir(tmp_path, reg)


def test_manuscript_tokens_ignores_code_span_placeholders() -> None:
    # A `{{claim:NAME}}` inside backticks documents the syntax; not a live reference.
    text = (
        "Insert via a `{{claim:NAME}}` token. Entropy is {{claim:entropy_fair_coin}}."
    )
    assert manuscript_claim_tokens(text) == ["entropy_fair_coin"]


# -- linter scope hardening (RedTeam: objective/prompt/sci-notation) --------


def _skill_full(sid, *, name="Name", objective="Obj", description="Desc", prompt="Q"):
    q = AssessmentQuestion(prompt, ("a", "b"), (0,))
    return Skill(sid, name, _M, objective, description, (), (q,))


def test_linter_scans_objective_field() -> None:
    skill = _skill_full("obj", objective="The free energy is 1.6094 nats here.")
    violations = find_unbacked_numbers(skill)
    assert [v.value for v in violations] == ["1.6094"]


def test_linter_scans_assessment_prompt() -> None:
    skill = _skill_full("prm", prompt="Given entropy 0.6931 nats, which holds?")
    violations = find_unbacked_numbers(skill)
    assert [v.value for v in violations] == ["0.6931"]


def test_linter_flags_capitalized_unit_results_without_flagging_bare_counts() -> None:
    skill = _skill_full(
        "caps",
        description=(
            "The entropy is 42 Nats. Surprise was 3 Bits. We launched in 2024 "
            "with 4 questions."
        ),
    )

    violations = find_unbacked_numbers(skill)

    assert [v.value for v in violations] == ["42", "3"]


def test_linter_ignores_wrong_numeric_distractors_by_design() -> None:
    # Distractors are hand-authored wrong answers and legitimately contain numbers.
    q = AssessmentQuestion("clean stem", ("0.4242 is wrong", "right"), (1,))
    skill = Skill("opt", "Name", _M, "Obj", "Desc", (), (q,))
    assert find_unbacked_numbers(skill) == []


def test_linter_flags_correct_numeric_answer_option() -> None:
    q = AssessmentQuestion("clean stem", ("0.6931 nats", "wrong"), (0,))
    skill = Skill("correctnum", "Name", _M, "Obj", "Desc", (), (q,))

    violations = find_unbacked_numbers(skill)

    assert [v.value for v in violations] == ["0.6931"]
    assert violations[0].skill_id == "correctnum"


def test_linter_allows_claim_bound_correct_answer_option() -> None:
    q = AssessmentQuestion("clean stem", ("{{claim:entropy_fair_coin}}", "wrong"), (0,))
    skill = Skill("correctclaim", "Name", _M, "Obj", "Desc", (), (q,))

    assert find_unbacked_numbers(skill) == []


def test_linter_catches_scientific_notation() -> None:
    skill = _skill_full("sci", description="the rate is 1.6e-3 per step")
    violations = find_unbacked_numbers(skill)
    assert [v.value for v in violations] == ["1.6e-3"]


def test_linter_ignores_single_decimal_by_design() -> None:
    # 0.5 is a parameter/probability, not a result shape (>=2 decimals); not flagged.
    skill = _skill_full("half", description="with a fair-coin probability of 0.5 here")
    assert find_unbacked_numbers(skill) == []


def test_linter_flags_unit_bound_integer_and_single_decimal_results_only() -> None:
    skill = _skill_full(
        "units",
        description=(
            "The entropy is exactly 42 nats. In 2024 there are 4 questions. "
            "The claim stays {{claim:vfe_descent_end}} nats. Another estimate is 3.7 bits. "
            "A bare 3.7 remains contextual."
        ),
    )

    violations = find_unbacked_numbers(skill)

    assert [violation.value for violation in violations] == ["42", "3.7"]


def test_unit_result_regex_captures_multi_decimal_values() -> None:
    """Regression: the unit-result regex under-captured multi-decimal values.

    With the old ``\\.\\d`` (exactly one fractional digit) group, "1.60 nats" and
    "2.718 bits" produced NO match at all — the value group could only consume a
    single fractional digit, so the trailing digits broke the required whitespace
    boundary and the whole pattern backtracked to failure. Binding directly to the
    regex (not the public linter) is deliberate: the ``_DECIMAL_RESULT_RE`` path
    already flags any >=2-decimal literal, so a public-function assertion would pass
    regardless of this fix and prove nothing. This test fails on the old regex.
    """
    for text, expected in (("1.60 nats", "1.60"), ("2.718 bits", "2.718")):
        match = _UNIT_RESULT_RE.search(text)
        assert match is not None, f"unit regex failed to match {text!r}"
        assert match.group("value") == expected


def test_linter_flags_multi_decimal_unit_results() -> None:
    """End-to-end: multi-decimal unit results reach the public linter as violations."""
    skill = _skill_full(
        "multi_unit",
        description="Free energy is 1.60 nats and the channel carries 2.718 bits.",
    )
    values = [violation.value for violation in find_unbacked_numbers(skill)]
    assert "1.60" in values
    assert "2.718" in values


def test_lint_graph_catches_subject_description_number() -> None:
    graph = CurriculumGraph(
        [Subject("sub_m", "m", _M, "intro mentions 3.14159 bare", (_skill("a", "ok"),))]
    )
    violations = lint_graph(graph)
    assert any(v.value == "3.14159" for v in violations)


# -- claims.py: string-claim digit anti-laundering (RedTeam: untested) ------


def test_string_claim_with_digit_rejected() -> None:
    reg = ClaimRegistry()
    with pytest.raises(ClaimError, match="digit"):
        reg.register("bad", "result123")


# -- Forge cross-vendor findings: token-coverage + fail-closed (2026-06-09) --


def test_claim_tokens_covers_all_learner_facing_fields() -> None:
    q = AssessmentQuestion("stem {{claim:c}}", ("opt {{claim:d}}", "x"), (0,))
    skill = Skill(
        "s", "n {{claim:a}}", _M, "obj {{claim:b}}", "desc {{claim:e}}", (), (q,)
    )
    assert skill.claim_tokens() == {"a", "b", "c", "d", "e"}


def test_validate_curriculum_catches_token_in_name() -> None:
    q = AssessmentQuestion("Q", ("a", "b"), (0,))
    skill = Skill("s", "Name {{claim:ghost}}", _M, "obj", "desc", (), (q,))
    with pytest.raises(ProvenanceError, match="ghost"):
        validate_curriculum([skill], ClaimRegistry())


def test_validate_curriculum_catches_token_in_assessment_prompt() -> None:
    q = AssessmentQuestion("stem {{claim:ghost}}", ("a", "b"), (0,))
    skill = Skill("s", "Name", _M, "obj", "desc", (), (q,))
    with pytest.raises(ProvenanceError, match="ghost"):
        validate_curriculum([skill], ClaimRegistry())


def test_render_fails_closed_on_empty_claim_token() -> None:
    with pytest.raises(ProvenanceError, match="malformed"):
        render("A {{claim:}} B", ClaimRegistry())


def test_render_graph_renders_every_field() -> None:
    reg = ClaimRegistry()
    reg.register("e", 1.0)
    q = AssessmentQuestion("stem {{claim:e}}", ("opt {{claim:e}}", "x"), (0,))
    skill = Skill(
        "s", "N {{claim:e}}", _M, "obj {{claim:e}}", "d {{claim:e}}", (), (q,)
    )
    graph = CurriculumGraph([Subject("sub_m", "m", _M, "subj {{claim:e}}", (skill,))])
    out = render_graph(graph, reg)
    s = out.subjects[0]
    assert "{{claim" not in s.description
    sk = s.skills[0]
    assert "{{claim" not in sk.name + sk.objective + sk.description
    assert "{{claim" not in sk.assessments[0].prompt
    assert all("{{claim" not in a for a in sk.assessments[0].answers)


def test_render_graph_fail_closed_on_subject_description_token() -> None:
    q = AssessmentQuestion("Q", ("a", "b"), (0,))
    skill = Skill("s", "Name", _M, "obj", "desc", (), (q,))
    graph = CurriculumGraph(
        [Subject("sub_m", "m", _M, "subj {{claim:ghost}}", (skill,))]
    )
    with pytest.raises(ProvenanceError):
        render_graph(graph, ClaimRegistry())


@pytest.mark.parametrize(
    "malformed",
    ["The value is {{ claim:e }} nats.", "x {{claim: e}} y", "z {{ claim:e}} w"],
)
def test_render_fails_closed_on_whitespaced_claim_tokens(malformed: str) -> None:
    """Negative control (ISC-123): malformed claim tokens with interior whitespace once
    bypassed the literal '{{claim:' substring check and reached learner text verbatim."""
    reg = ClaimRegistry()
    reg.register("e", 0.6931)
    with pytest.raises(ProvenanceError, match="malformed"):
        render(malformed, reg)


@pytest.mark.parametrize(
    "zw",
    ["\u200b", "‌", "‍", "⁠", "﻿"],
)
def test_render_neutralizes_zero_width_split_claim_token(zw: str) -> None:
    """Triple-check negative control (CRITICAL): a token split by a zero-width format
    char ({{<ZWSP>claim:e}}) once reached learner text as a LITERAL because neither \\s nor
    \\b match category-Cf chars. The fix strips Cf chars first, so the security property
    holds either way: a registered claim now RESOLVES (no literal token reaches the
    learner) and an unregistered/empty one still RAISES."""
    reg = ClaimRegistry()
    reg.register("e", 0.6931)
    # Registered: resolves cleanly, no literal token survives.
    out = render(f"The value is {{{{{zw}claim:e}}}} nats.", reg)
    assert "{{" not in out and "claim:" not in out and zw not in out
    # Unregistered: still fails closed.
    with pytest.raises(ProvenanceError):
        render(f"The value is {{{{{zw}claim:ghost}}}} nats.", reg)
    # Empty/malformed: still fails closed.
    with pytest.raises(ProvenanceError, match="malformed"):
        render(f"A {{{{{zw}claim:}}}} B", reg)


def test_unbacked_linter_detects_zero_width_split_number() -> None:
    """Triple-check negative control (HIGH): a bare result split by a zero-width char
    ('1<ZWSP>.6094 nats') must still be flagged by the numeric-provenance linter."""
    found = unbacked_numbers_in_text("The entropy is 1\u200b.6094 nats.", label="t")
    assert any("1.6094" in u.value or "6094" in u.value for u in found), found
