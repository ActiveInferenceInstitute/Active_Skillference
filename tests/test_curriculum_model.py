"""Tests for the typed curriculum model — validation invariants."""

from __future__ import annotations

import pytest

from src.curriculum.model import (
    ALL_STRATA,
    AssessmentQuestion,
    CurriculumError,
    Skill,
    Stratum,
    Subject,
)


def _q() -> AssessmentQuestion:
    return AssessmentQuestion("Pick one", ("a", "b"), (0,))


def test_all_strata_has_eight_members_in_order() -> None:
    assert len(ALL_STRATA) == 8
    assert [s.order for s in ALL_STRATA] == list(range(8))


def test_only_first_two_strata_are_foundational() -> None:
    foundational = [s for s in ALL_STRATA if s.is_foundational]
    assert foundational == [Stratum.MATH_FOUNDATIONS, Stratum.PROBABILITY]


def test_assessment_requires_prompt() -> None:
    with pytest.raises(CurriculumError):
        AssessmentQuestion("   ", ("a",), (0,))


def test_assessment_requires_answers_and_correct() -> None:
    with pytest.raises(CurriculumError):
        AssessmentQuestion("Q", (), (0,))
    with pytest.raises(CurriculumError):
        AssessmentQuestion("Q", ("a",), ())


def test_assessment_correct_index_in_range() -> None:
    with pytest.raises(CurriculumError):
        AssessmentQuestion("Q", ("a", "b"), (5,))


def test_single_choice_needs_exactly_one_correct() -> None:
    with pytest.raises(CurriculumError):
        AssessmentQuestion("Q", ("a", "b"), (0, 1), question_type="SingleChoice")
    # MultipleChoice may have several
    AssessmentQuestion("Q", ("a", "b"), (0, 1), question_type="MultipleChoice")


def test_skill_id_must_be_identifier_like() -> None:
    with pytest.raises(CurriculumError):
        Skill("9bad", "Name", Stratum.MATH_FOUNDATIONS, "obj", "desc", (), (_q(),))


def test_skill_requires_name_and_objective() -> None:
    with pytest.raises(CurriculumError):
        Skill("ok_id", "  ", Stratum.MATH_FOUNDATIONS, "obj", "d", (), (_q(),))
    with pytest.raises(CurriculumError):
        Skill("ok_id", "Name", Stratum.MATH_FOUNDATIONS, "  ", "d", (), (_q(),))


def test_skill_rejects_bad_self_reporting_type() -> None:
    with pytest.raises(CurriculumError):
        Skill(
            "ok",
            "N",
            Stratum.MATH_FOUNDATIONS,
            "o",
            "d",
            (),
            (_q(),),
            self_reporting_type="Telepathy",
        )  # type: ignore[arg-type]


def test_skill_rejects_non_positive_points() -> None:
    with pytest.raises(CurriculumError):
        Skill(
            "ok",
            "N",
            Stratum.MATH_FOUNDATIONS,
            "o",
            "d",
            (),
            (_q(),),
            point_increment=0,
        )
    with pytest.raises(CurriculumError):
        Skill(
            "ok",
            "N",
            Stratum.MATH_FOUNDATIONS,
            "o",
            "d",
            (),
            (_q(),),
            num_perform_to_completion=0,
        )


def test_claim_tokens_parsed_from_description() -> None:
    skill = Skill(
        "ok",
        "N",
        Stratum.INFORMATION_THEORY,
        "o",
        "value is {{claim:entropy_fair_coin}} and {{claim:kl_x}}",
        (),
        (_q(),),
    )
    assert skill.claim_tokens() == {"entropy_fair_coin", "kl_x"}


def test_is_root_when_no_prerequisites() -> None:
    root = Skill("r", "N", Stratum.MATH_FOUNDATIONS, "o", "d", (), (_q(),))
    child = Skill("c", "N", Stratum.MATH_FOUNDATIONS, "o", "d", ("r",), (_q(),))
    assert root.is_root and not child.is_root


def test_subject_rejects_stratum_mismatch() -> None:
    skill = Skill("s1", "N", Stratum.PROBABILITY, "o", "d", (), (_q(),))
    with pytest.raises(CurriculumError):
        Subject("sub", "S", Stratum.MATH_FOUNDATIONS, "d", (skill,))


def test_subject_rejects_bad_id() -> None:
    with pytest.raises(CurriculumError):
        Subject("1bad", "S", Stratum.MATH_FOUNDATIONS, "d", ())
