"""SkillTree-native data model.

These dataclasses mirror the field names of the SkillTree REST API
(https://skilltreeplatform.dev). Python attributes are snake_case while the
serialised payloads (``as_payload`` / ``to_dict`` / ``to_export_dict``) emit
the camelCase keys SkillTree expects.

The model hierarchy mirrors SkillTree's: Project → Subject → Skill, with
learning-path prerequisites expressed as :class:`SkillDependency` edges and
quizzes expressed as standalone :class:`Quiz` definitions.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Literal

# SkillTree skillIds become path segments in the admin REST API
# (e.g. /admin/projects/{id}/subjects/{id}/skills/{skillId}). A slash, space, or other
# non-identifier character would corrupt the endpoint path (path injection / 404), so we
# enforce the same identifier rule the curriculum layer uses: a leading letter followed
# by alphanumerics/underscores. This mirrors src.curriculum.model._SKILL_ID_RE.
_SKILLTREE_ID_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")
MAX_SUBJECT_NAME_LENGTH = 50

SkillTreeSelfReportingType = Literal["HonorSystem", "Approval", "Quiz"]
_VALID_SELF_REPORTING: tuple[str, ...] = ("HonorSystem", "Approval", "Quiz")

SkillTreeQuestionType = Literal["SingleChoice", "MultipleChoice", "TextInput"]
_VALID_QUESTION_TYPES: tuple[str, ...] = ("SingleChoice", "MultipleChoice", "TextInput")


class SkillTreeModelError(ValueError):
    """Raised on a malformed SkillTree model element."""


@dataclass(frozen=True)
class SkillTreeSkill:
    """A SkillTree Skill — the atomic earnable unit (``type == "Skill"``)."""

    skill_id: str
    name: str
    point_increment: int = 100
    num_perform_to_completion: int = 1
    description: str = ""
    help_url: str = ""
    self_reporting_type: SkillTreeSelfReportingType = "HonorSystem"
    quiz_id: str = ""
    type: str = "Skill"

    def __post_init__(self) -> None:
        if not self.skill_id.strip():
            raise SkillTreeModelError("skillId must be non-empty")
        if not _SKILLTREE_ID_RE.match(self.skill_id):
            raise SkillTreeModelError(
                f"skillId {self.skill_id!r} must be a valid identifier "
                "(leading letter, then alphanumerics/underscores) — it becomes a REST "
                "path segment, so slashes/spaces/leading underscores are rejected"
            )
        if not self.name.strip():
            raise SkillTreeModelError(f"skill {self.skill_id} must have a name")
        if self.self_reporting_type not in _VALID_SELF_REPORTING:
            raise SkillTreeModelError(
                f"skill {self.skill_id} selfReportingType "
                f"{self.self_reporting_type!r} invalid (expected one of {_VALID_SELF_REPORTING})"
            )
        if self.point_increment <= 0:
            raise SkillTreeModelError(
                f"skill {self.skill_id} pointIncrement must be positive"
            )
        if self.num_perform_to_completion <= 0:
            raise SkillTreeModelError(
                f"skill {self.skill_id} numPerformToCompletion must be positive"
            )

    def to_dict(self) -> dict[str, Any]:
        """Serialise to a SkillTree-native (camelCase) payload."""
        payload = {
            "skillId": self.skill_id,
            "name": self.name,
            "type": self.type,
            "pointIncrement": self.point_increment,
            "numPerformToCompletion": self.num_perform_to_completion,
            "description": self.description,
            "helpUrl": self.help_url,
            "selfReportingType": self.self_reporting_type,
        }
        if self.quiz_id:
            payload["quizId"] = self.quiz_id
        return payload

    def as_payload(self) -> dict[str, Any]:
        """Alias for :meth:`to_dict` (the request-body form)."""
        return self.to_dict()


@dataclass(frozen=True)
class SkillTreeSubject:
    """A SkillTree Subject — a themed container of skills."""

    subject_id: str
    name: str
    description: str = ""
    skills: list[SkillTreeSkill] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.subject_id.strip():
            raise SkillTreeModelError("subjectId must be non-empty")
        if not self.name.strip():
            raise SkillTreeModelError(f"subject {self.subject_id} must have a name")
        if len(self.name) > MAX_SUBJECT_NAME_LENGTH:
            raise SkillTreeModelError(
                f"subject {self.subject_id} name must not exceed "
                f"{MAX_SUBJECT_NAME_LENGTH} chars"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "subjectId": self.subject_id,
            "name": self.name,
            "description": self.description,
            "skills": [s.to_dict() for s in self.skills],
        }

    def as_payload(self) -> dict[str, Any]:
        return self.to_dict()


@dataclass(frozen=True)
class SkillDependency:
    """A learning-path prerequisite edge: ``skillId`` depends on ``dependsOnSkillId``."""

    skill_id: str
    depends_on_skill_id: str

    def __post_init__(self) -> None:
        if not self.skill_id.strip() or not self.depends_on_skill_id.strip():
            raise SkillTreeModelError(
                "dependency requires non-empty skillId and dependsOnSkillId"
            )
        if self.skill_id == self.depends_on_skill_id:
            raise SkillTreeModelError(f"skill {self.skill_id} cannot depend on itself")

    def to_dict(self) -> dict[str, Any]:
        return {
            "skillId": self.skill_id,
            "dependsOnSkillId": self.depends_on_skill_id,
        }

    def as_payload(self) -> dict[str, Any]:
        return self.to_dict()


@dataclass(frozen=True)
class QuizQuestion:
    """A single quiz question with answer options carrying correctness flags."""

    question: str
    answers: list[dict[str, Any]]
    question_type: SkillTreeQuestionType = "SingleChoice"

    def __post_init__(self) -> None:
        if not self.question.strip():
            raise SkillTreeModelError("quiz question must be non-empty")
        if self.question_type not in _VALID_QUESTION_TYPES:
            raise SkillTreeModelError(
                f"questionType {self.question_type!r} invalid (expected one of {_VALID_QUESTION_TYPES})"
            )
        if not self.answers:
            raise SkillTreeModelError(f"question {self.question!r} must have ≥1 answer")
        for ans in self.answers:
            if "answer" not in ans or "isCorrect" not in ans:
                raise SkillTreeModelError(
                    f"question {self.question!r} answers need 'answer' and 'isCorrect' keys"
                )
        if not any(bool(a["isCorrect"]) for a in self.answers):
            raise SkillTreeModelError(
                f"question {self.question!r} must mark ≥1 answer correct"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "question": self.question,
            "questionType": self.question_type,
            "answers": [
                {"answer": a["answer"], "isCorrect": bool(a["isCorrect"])}
                for a in self.answers
            ],
        }

    def to_admin_create_payload(self) -> dict[str, Any]:
        """Serialise to SkillTree's quiz-question admin-create payload."""
        return {
            "question": self.question,
            "answerHint": "",
            "questionType": self.question_type,
            "questionScale": 5,
            "answers": [
                {"answer": a["answer"], "isCorrect": bool(a["isCorrect"])}
                for a in self.answers
            ],
        }

    def as_payload(self) -> dict[str, Any]:
        return self.to_dict()


@dataclass(frozen=True)
class Quiz:
    """A SkillTree Quiz definition (``type == "Quiz"``)."""

    quiz_id: str
    name: str
    questions: list[QuizQuestion] = field(default_factory=list)
    type: str = "Quiz"
    passing_percent: int = 100

    def __post_init__(self) -> None:
        if not self.quiz_id.strip():
            raise SkillTreeModelError("quizId must be non-empty")
        if not self.name.strip():
            raise SkillTreeModelError(f"quiz {self.quiz_id} must have a name")
        if not 1 <= self.passing_percent <= 100:
            raise SkillTreeModelError(
                f"quiz {self.quiz_id} passingPercent must be in 1..100"
            )

    def to_dict(self) -> dict[str, Any]:
        # numQuestions and passingPercent make the completion contract explicit in the
        # export rather than delegating the pass bar to a SkillTree server default. The
        # default of 100 means every question must be answered correctly to pass.
        return {
            "quizId": self.quiz_id,
            "name": self.name,
            "type": self.type,
            "numQuestions": len(self.questions),
            "passingPercent": self.passing_percent,
            "questions": [q.to_dict() for q in self.questions],
        }

    def as_payload(self) -> dict[str, Any]:
        return self.to_dict()


@dataclass(frozen=True)
class SkillTreeProject:
    """A complete SkillTree Project export."""

    project_id: str
    name: str
    subjects: list[SkillTreeSubject] = field(default_factory=list)
    dependencies: list[SkillDependency] = field(default_factory=list)
    quizzes: list[Quiz] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.project_id.strip():
            raise SkillTreeModelError("projectId must be non-empty")
        if not self.name.strip():
            raise SkillTreeModelError(f"project {self.project_id} must have a name")
        self._validate_quiz_gating()

    def _validate_quiz_gating(self) -> None:
        """Fail closed on UNIVERSAL quiz-gating defects (always wrong, any project):

        (1) a ``Quiz``-typed skill must carry a non-empty ``quiz_id`` (a gate that gates on
        nothing), and (2) any ``quiz_id`` set on a skill must exist in ``quizzes`` (a
        dangling reference that crashes/silently fails at runtime).

        Orphan quizzes (a quiz no skill references) are NOT rejected here: an unused quiz
        pool is a legitimate authoring pattern (staged content, dynamic selection,
        deprecated-but-retained). A project that wants the stricter 1:1 invariant calls
        :meth:`orphan_quiz_ids` at its own export seam — see the exporter.
        """
        quiz_ids = {quiz.quiz_id for quiz in self.quizzes}
        problems: list[str] = []
        for subject in self.subjects:
            for skill in subject.skills:
                if skill.self_reporting_type == "Quiz" and not skill.quiz_id.strip():
                    problems.append(f"{skill.skill_id}: Quiz skill has no quizId")
                if skill.quiz_id and skill.quiz_id not in quiz_ids:
                    problems.append(
                        f"{skill.skill_id}: quizId {skill.quiz_id!r} has no quiz definition"
                    )
        if problems:
            raise SkillTreeModelError(
                "broken quiz gating (export refused):\n  " + "\n  ".join(problems)
            )

    def orphan_quiz_ids(self) -> tuple[str, ...]:
        """Return quiz ids defined but referenced by no skill (sorted).

        Empty for a project with the strict 1:1 skill↔quiz invariant. Exposed as a query
        (not a hard __post_init__ error) so each caller decides whether an unused quiz is
        a defect or an intentional pool.
        """
        referenced = {
            skill.quiz_id
            for subject in self.subjects
            for skill in subject.skills
            if skill.quiz_id
        }
        return tuple(sorted({q.quiz_id for q in self.quizzes} - referenced))

    def to_export_dict(self) -> dict[str, Any]:
        """Produce one JSON-serialisable dict describing the whole project."""
        return {
            "projectId": self.project_id,
            "name": self.name,
            "subjects": [s.to_dict() for s in self.subjects],
            "dependencies": [d.to_dict() for d in self.dependencies],
            "quizzes": [q.to_dict() for q in self.quizzes],
        }
