from __future__ import annotations

from src.curriculum.assessment_normalize import (
    assign_mc_correct_set,
    balance_answer_lengths,
    move_correct_answer,
)
from src.curriculum.authoring import _q
from src.curriculum.model import AssessmentQuestion


def test_move_correct_answer_rotates_single_choice_index() -> None:
    question = _q("Pick one", ["alpha", "beta", "gamma"], 0)
    moved = move_correct_answer(question, 2)
    assert moved.correct == (2,)
    assert moved.answers[2] == "alpha"


def test_move_correct_answer_ignores_multiple_choice() -> None:
    question = AssessmentQuestion(
        prompt="Pick two",
        answers=("a", "b", "c", "d"),
        correct=(0, 2),
        question_type="MultipleChoice",
        origin="test",
    )
    assert move_correct_answer(question, 1) is question


def test_balance_answer_lengths_adds_fillers_without_changing_correct_index() -> None:
    question = _q("Pick one", ["short", "much longer distractor text"], 0)
    balanced = balance_answer_lengths(question, target_rank=0, variation=0)
    assert balanced.correct == question.correct
    assert balanced.answers != question.answers
    assert len(balanced.answers[0]) > len(question.answers[0])


def test_assign_mc_correct_set_reorders_multiple_choice() -> None:
    question = AssessmentQuestion(
        prompt="Pick two",
        answers=("a", "b", "c", "d"),
        correct=(0, 2),
        question_type="MultipleChoice",
        origin="test",
    )
    reassigned = assign_mc_correct_set(question, (1, 3))
    assert reassigned.correct == (1, 3)
    assert set(reassigned.answers) == set(question.answers)
