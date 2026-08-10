from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from src.skilltree.model import SkillTreeProject


class SkillTreeSummaryError(ValueError):
    pass


def validate_export_payload(payload: Mapping[str, Any]) -> None:
    """Validate the structural integrity of a serialized SkillTree project.

    ``summarize_export_payload(strict=False)`` is intentionally permissive for
    reporting partial diagnostic payloads. That is useful for diagnostics, but
    unsafe at a browser or live-proof boundary: a malformed export could be
    presented as an available project with zero counts.  This validator is the
    fail-closed boundary for generated exports and checks the relationships that
    a count-only summary cannot see.
    """
    _required_text(payload.get("projectId"), "projectId")
    _required_text(payload.get("name"), "name")
    subjects = _required_collection(payload, "subjects")
    dependencies = _required_collection(payload, "dependencies")
    quizzes = _required_collection(payload, "quizzes")

    subject_ids: set[str] = set()
    skill_ids: set[str] = set()
    skill_quiz_ids: dict[str, str] = {}
    for subject_index, subject in enumerate(subjects, start=1):
        if not isinstance(subject, Mapping):
            raise SkillTreeSummaryError(
                f"SkillTree project subject {subject_index} is not an object"
            )
        subject_id = _required_text(
            subject.get("subjectId"),
            f"subject {subject_index} subjectId",
        )
        if subject_id in subject_ids:
            raise SkillTreeSummaryError(
                f"SkillTree project contains duplicate subjectId {subject_id!r}"
            )
        subject_ids.add(subject_id)
        skills = _subject_skills(subject, index=subject_index, strict=True)
        for skill_index, skill in enumerate(skills, start=1):
            if not isinstance(skill, Mapping):
                raise SkillTreeSummaryError(
                    f"SkillTree project subject {subject_index} skill {skill_index} "
                    "is not an object"
                )
            skill_id = _required_text(
                skill.get("skillId"),
                f"subject {subject_index} skill {skill_index} skillId",
            )
            if skill_id in skill_ids:
                raise SkillTreeSummaryError(
                    f"SkillTree project contains duplicate skillId {skill_id!r}"
                )
            skill_ids.add(skill_id)
            quiz_id = _optional_text(
                skill.get("quizId"),
                f"skill {skill_id} quizId",
            )
            report_type = skill.get("selfReportingType")
            if report_type is not None and not isinstance(report_type, str):
                raise SkillTreeSummaryError(
                    f"SkillTree skill {skill_id!r} selfReportingType must be text"
                )
            if str(report_type or "").strip() == "Quiz" and not quiz_id:
                raise SkillTreeSummaryError(
                    f"SkillTree quiz-gated skill {skill_id!r} is missing quizId"
                )
            if quiz_id:
                skill_quiz_ids[skill_id] = quiz_id

    _validate_dependencies(dependencies, skill_ids)

    quiz_ids: set[str] = set()
    for quiz_index, quiz in enumerate(quizzes, start=1):
        if not isinstance(quiz, Mapping):
            raise SkillTreeSummaryError(
                f"SkillTree project quiz {quiz_index} is not an object"
            )
        quiz_id = _required_text(
            quiz.get("quizId"),
            f"quiz {quiz_index} quizId",
        )
        if quiz_id in quiz_ids:
            raise SkillTreeSummaryError(
                f"SkillTree project contains duplicate quizId {quiz_id!r}"
            )
        quiz_ids.add(quiz_id)
        questions = _quiz_questions(quiz, index=quiz_index, strict=True)
        for question_index, question in enumerate(questions, start=1):
            if not isinstance(question, Mapping):
                raise SkillTreeSummaryError(
                    f"SkillTree project quiz {quiz_index} question {question_index} "
                    "is not an object"
                )
            _required_text(
                question.get("question"),
                f"quiz {quiz_index} question {question_index} question",
            )
            answers = question.get("answers", [])
            if not isinstance(answers, list):
                raise SkillTreeSummaryError(
                    f"SkillTree project quiz {quiz_index} question {question_index} "
                    "answers must be a list"
                )
            if not answers:
                raise SkillTreeSummaryError(
                    f"SkillTree project quiz {quiz_index} question {question_index} "
                    "must contain at least one answer"
                )
            has_correct = False
            for answer_index, answer in enumerate(answers, start=1):
                if not isinstance(answer, Mapping):
                    raise SkillTreeSummaryError(
                        f"SkillTree project quiz {quiz_index} question {question_index} "
                        f"answer {answer_index} is not an object"
                    )
                _required_text(
                    answer.get("answer"),
                    f"quiz {quiz_index} question {question_index} answer {answer_index}",
                )
                is_correct = answer.get("isCorrect")
                if not isinstance(is_correct, bool):
                    raise SkillTreeSummaryError(
                        f"SkillTree project quiz {quiz_index} question {question_index} "
                        f"answer {answer_index} isCorrect must be boolean"
                    )
                has_correct = has_correct or is_correct
            if not has_correct:
                raise SkillTreeSummaryError(
                    f"SkillTree project quiz {quiz_index} question {question_index} "
                    "must mark at least one answer correct"
                )

    for skill_id, quiz_id in sorted(skill_quiz_ids.items()):
        if quiz_id not in quiz_ids:
            raise SkillTreeSummaryError(
                f"SkillTree skill {skill_id!r} references missing quiz {quiz_id!r}"
            )


def _validate_dependencies(dependencies: list[Any], skill_ids: set[str]) -> None:
    edges: set[tuple[str, str]] = set()
    dependents: dict[str, set[str]] = {skill_id: set() for skill_id in skill_ids}
    indegree = {skill_id: 0 for skill_id in skill_ids}
    for index, dependency in enumerate(dependencies, start=1):
        if not isinstance(dependency, Mapping):
            raise SkillTreeSummaryError(
                f"SkillTree project dependency {index} is not an object"
            )
        skill_id = _required_text(
            dependency.get("skillId"),
            f"dependency {index} skillId",
        )
        prerequisite_id = _required_text(
            dependency.get("dependsOnSkillId"),
            f"dependency {index} dependsOnSkillId",
        )
        if skill_id == prerequisite_id:
            raise SkillTreeSummaryError(
                f"SkillTree project dependency {index} is a self-loop"
            )
        if skill_id not in skill_ids or prerequisite_id not in skill_ids:
            raise SkillTreeSummaryError(
                f"SkillTree project dependency {index} references an unknown skill"
            )
        edge = (skill_id, prerequisite_id)
        if edge in edges:
            raise SkillTreeSummaryError(
                f"SkillTree project contains duplicate dependency {edge!r}"
            )
        edges.add(edge)
        if skill_id not in dependents[prerequisite_id]:
            dependents[prerequisite_id].add(skill_id)
            indegree[skill_id] += 1

    queue = sorted(skill_id for skill_id, degree in indegree.items() if degree == 0)
    visited = 0
    while queue:
        current = queue.pop(0)
        visited += 1
        for dependent in sorted(dependents[current]):
            indegree[dependent] -= 1
            if indegree[dependent] == 0:
                queue.append(dependent)
                queue.sort()
    if visited != len(skill_ids):
        raise SkillTreeSummaryError("SkillTree project dependencies contain a cycle")


@dataclass(frozen=True)
class ExportSummary:
    subjects: int
    skills: int
    dependencies: int
    quizzes: int
    assessments: int

    def project_counts(self) -> dict[str, int]:
        return {
            "subjects": self.subjects,
            "skills": self.skills,
            "dependencies": self.dependencies,
            "quizzes": self.quizzes,
        }


def summarize_project(project: SkillTreeProject) -> ExportSummary:
    return ExportSummary(
        subjects=len(project.subjects),
        skills=sum(len(subject.skills) for subject in project.subjects),
        dependencies=len(project.dependencies),
        quizzes=len(project.quizzes),
        assessments=sum(len(quiz.questions) for quiz in project.quizzes),
    )


def summarize_export_payload(
    payload: Mapping[str, Any], *, strict: bool = True
) -> ExportSummary:
    subjects = _collection(payload, "subjects", strict=strict)
    dependencies = _collection(payload, "dependencies", strict=strict)
    quizzes = _collection(payload, "quizzes", strict=strict)
    return ExportSummary(
        subjects=len(subjects),
        skills=sum(
            len(skills)
            for index, subject in enumerate(subjects, start=1)
            for skills in [_subject_skills(subject, index=index, strict=strict)]
        ),
        dependencies=len(dependencies),
        quizzes=len(quizzes),
        assessments=sum(
            len(questions)
            for index, quiz in enumerate(quizzes, start=1)
            for questions in [_quiz_questions(quiz, index=index, strict=strict)]
        ),
    )


def _collection(payload: Mapping[str, Any], key: str, *, strict: bool) -> list[Any]:
    value = payload.get(key, [])
    if isinstance(value, list):
        return value
    if strict:
        raise SkillTreeSummaryError(f"SkillTree project {key} must be a list")
    return []


def _required_collection(payload: Mapping[str, Any], key: str) -> list[Any]:
    if key not in payload:
        raise SkillTreeSummaryError(f"SkillTree project requires {key} collection")
    return _collection(payload, key, strict=True)


def _required_text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SkillTreeSummaryError(f"SkillTree project {label} must be non-empty text")
    return value.strip()


def _optional_text(value: Any, label: str) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        raise SkillTreeSummaryError(f"SkillTree project {label} must be text")
    return value.strip()


def _subject_skills(subject: Any, *, index: int, strict: bool) -> list[Any]:
    if not isinstance(subject, Mapping):
        if strict:
            raise SkillTreeSummaryError(
                f"SkillTree project subject {index} is not an object"
            )
        return []
    skills = subject.get("skills", [])
    if isinstance(skills, list):
        return skills
    if strict:
        raise SkillTreeSummaryError(
            f"SkillTree project subject {index} skills must be a list"
        )
    return []


def _quiz_questions(quiz: Any, *, index: int, strict: bool) -> list[Any]:
    if not isinstance(quiz, Mapping):
        if strict:
            raise SkillTreeSummaryError(
                f"SkillTree project quiz {index} is not an object"
            )
        return []
    questions = quiz.get("questions", [])
    if isinstance(questions, list):
        return questions
    if strict:
        raise SkillTreeSummaryError(
            f"SkillTree project quiz {index} questions must be a list"
        )
    return []
