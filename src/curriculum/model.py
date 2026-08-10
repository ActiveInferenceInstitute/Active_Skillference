"""Typed curriculum domain model.

The curriculum is a prerequisite graph of :class:`Skill` nodes grouped into
:class:`Subject` containers, each anchored to one pedagogical :class:`Stratum`.
This model is the shared seam consumed by:

* :mod:`src.curriculum.graph` — DAG validation / topological ordering,
* :mod:`src.provenance.binding` — claim-token rendering,
* :mod:`src.skilltree.exporter` — conversion to SkillTree-native artifacts.

Field names on :class:`Skill` deliberately mirror SkillTree's data model
(``point_increment`` → ``pointIncrement`` etc.) so the exporter is a thin map.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Literal

# ``{{claim:NAME}}`` token used in skill descriptions for provenance-bound values.
CLAIM_TOKEN_RE = re.compile(r"\{\{claim:([A-Za-z0-9_.\-]+)\}\}")

SelfReportingType = Literal["HonorSystem", "Approval", "Quiz"]
_VALID_SELF_REPORTING = ("HonorSystem", "Approval", "Quiz")
QuestionType = Literal["SingleChoice", "MultipleChoice", "TextInput"]


class Stratum(Enum):
    """The eight pedagogical layers, ordered roots → canopy."""

    MATH_FOUNDATIONS = "math_foundations"
    PROBABILITY = "probability"
    INFORMATION_THEORY = "information_theory"
    VARIATIONAL_METHODS = "variational_methods"
    FREE_ENERGY_PRINCIPLE = "free_energy_principle"
    ACTIVE_INFERENCE = "active_inference"
    COMPUTATION = "computation"
    APPLICATIONS = "applications"

    @property
    def order(self) -> int:
        return _STRATUM_ORDER[self]

    @property
    def is_foundational(self) -> bool:
        """Strata whose skills may legitimately have zero prerequisites."""
        return self in (Stratum.MATH_FOUNDATIONS, Stratum.PROBABILITY)


ALL_STRATA: tuple[Stratum, ...] = tuple(Stratum)
_STRATUM_ORDER = {s: i for i, s in enumerate(ALL_STRATA)}


class CurriculumError(ValueError):
    """Raised on a malformed curriculum element."""


@dataclass(frozen=True)
class AssessmentQuestion:
    """A single failable assessment item attached to a skill.

    ``correct`` holds the indices into ``answers`` that are correct. For
    ``TextInput`` questions ``answers`` holds accepted answers and ``correct``
    indexes all of them.
    """

    prompt: str
    answers: tuple[str, ...]
    correct: tuple[int, ...]
    question_type: QuestionType = "SingleChoice"
    # "authored" = a bespoke per-skill domain item; "rubric" = a shared metacognitive
    # template (transfer/misuse/diagnostic/mastery review) deliberately applied across
    # many skills. Internal metadata only — not part of the SkillTree export.
    origin: str = "authored"

    def __post_init__(self) -> None:
        if not self.prompt.strip():
            raise CurriculumError("assessment prompt must be non-empty")
        if not self.answers:
            raise CurriculumError(f"assessment {self.prompt!r} must have ≥1 answer")
        if not self.correct:
            raise CurriculumError(
                f"assessment {self.prompt!r} must mark ≥1 correct answer"
            )
        if any(i < 0 or i >= len(self.answers) for i in self.correct):
            raise CurriculumError(
                f"assessment {self.prompt!r} has out-of-range correct index"
            )
        if self.question_type == "SingleChoice" and len(self.correct) != 1:
            raise CurriculumError(
                f"SingleChoice {self.prompt!r} must have exactly one correct answer"
            )


@dataclass(frozen=True)
class Skill:
    """An atomic learnable unit — one node of the prerequisite graph."""

    skill_id: str
    name: str
    stratum: Stratum
    objective: str
    description: str
    prerequisites: tuple[str, ...] = ()
    assessments: tuple[AssessmentQuestion, ...] = ()
    point_increment: int = 100
    num_perform_to_completion: int = 1
    help_url: str = ""
    self_reporting_type: SelfReportingType = "Quiz"
    tags: tuple[str, ...] = ()
    related: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not _SKILL_ID_RE.match(self.skill_id):
            raise CurriculumError(
                f"skill_id {self.skill_id!r} must be alnum/underscore (SkillTree skillId rule)"
            )
        if not self.name.strip():
            raise CurriculumError(f"skill {self.skill_id} must have a name")
        if not self.objective.strip():
            raise CurriculumError(f"skill {self.skill_id} must have an objective")
        if self.self_reporting_type not in _VALID_SELF_REPORTING:
            raise CurriculumError(
                f"skill {self.skill_id} self_reporting_type {self.self_reporting_type!r} invalid"
            )
        if self.point_increment <= 0:
            raise CurriculumError(
                f"skill {self.skill_id} point_increment must be positive"
            )
        if self.num_perform_to_completion <= 0:
            raise CurriculumError(
                f"skill {self.skill_id} num_perform_to_completion must be positive"
            )

    def claim_tokens(self) -> set[str]:
        """Names of every ``{{claim:NAME}}`` token in any learner-facing field.

        Scans the name, objective, description, and every assessment's prompt and
        answer options — all fields the exporter copies into SkillTree and a learner
        reads. A token anywhere is a binding promise, so validation/rendering must see
        them all (otherwise a token outside ``description`` would export literal).
        """
        texts = [self.name, self.objective, self.description]
        for question in self.assessments:
            texts.append(question.prompt)
            texts.extend(question.answers)
        tokens: set[str] = set()
        for text in texts:
            tokens.update(CLAIM_TOKEN_RE.findall(text))
        return tokens

    @property
    def is_root(self) -> bool:
        return len(self.prerequisites) == 0


_SKILL_ID_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")


@dataclass(frozen=True)
class Subject:
    """A SkillTree Subject — a themed container of skills within one stratum."""

    subject_id: str
    name: str
    stratum: Stratum
    description: str
    skills: tuple[Skill, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not _SKILL_ID_RE.match(self.subject_id):
            raise CurriculumError(
                f"subject_id {self.subject_id!r} must be alnum/underscore"
            )
        for skill in self.skills:
            if skill.stratum is not self.stratum:
                raise CurriculumError(
                    f"skill {skill.skill_id} stratum {skill.stratum} != subject stratum {self.stratum}"
                )
