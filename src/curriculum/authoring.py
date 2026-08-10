"""Shared skill/question constructors and stratum shorthands for curriculum data."""

from __future__ import annotations

from .model import AssessmentQuestion, Skill, Stratum


def _q(
    prompt: str, answers: list[str], correct: int, origin: str = "authored"
) -> AssessmentQuestion:
    """A single-choice assessment question (``correct`` is the index of the right answer)."""
    return AssessmentQuestion(
        prompt=prompt, answers=tuple(answers), correct=(correct,), origin=origin
    )


def _s(
    skill_id: str,
    name: str,
    stratum: Stratum,
    objective: str,
    description: str,
    prerequisites: tuple[str, ...],
    *questions: AssessmentQuestion,
    self_reporting_type: str = "Quiz",
    tags: tuple[str, ...] = (),
    related: tuple[str, ...] = (),
) -> Skill:
    return Skill(
        skill_id=skill_id,
        name=name,
        stratum=stratum,
        objective=objective,
        description=description,
        prerequisites=prerequisites,
        assessments=tuple(questions),
        self_reporting_type=self_reporting_type,  # type: ignore[arg-type]
        tags=tags,
        related=related,
    )


# Shorthands for strata.
_M = Stratum.MATH_FOUNDATIONS
_P = Stratum.PROBABILITY
_IT = Stratum.INFORMATION_THEORY
_VM = Stratum.VARIATIONAL_METHODS
_FEP = Stratum.FREE_ENERGY_PRINCIPLE
_AI = Stratum.ACTIVE_INFERENCE
_C = Stratum.COMPUTATION
_APP = Stratum.APPLICATIONS
