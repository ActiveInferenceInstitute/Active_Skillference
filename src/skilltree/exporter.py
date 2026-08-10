"""Convert a curriculum graph into SkillTree-native artifacts.

The exporter is a thin field map: curriculum :class:`~curriculum.model.Subject`
→ :class:`~skilltree.model.SkillTreeSubject`, :class:`~curriculum.model.Skill`
→ :class:`~skilltree.model.SkillTreeSkill`, each prerequisite edge →
:class:`~skilltree.model.SkillDependency`, and each ``Quiz``-typed skill's
assessments → a :class:`~skilltree.model.Quiz`.

The curriculum graph is consumed through the :class:`CurriculumGraphLike`
structural protocol so this module does not hard-depend on ``curriculum.graph``
(owned by another author). Any object exposing ``subjects``, ``skills`` and
``prerequisite_edges()`` satisfies it.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Protocol, runtime_checkable

from src.artifacts.json_io import write_json_artifact
from src.curriculum.model import AssessmentQuestion, Skill, Subject
from src.skilltree.model import (
    Quiz,
    QuizQuestion,
    SkillDependency,
    SkillTreeModelError,
    SkillTreeProject,
    SkillTreeSkill,
    SkillTreeSubject,
)
from src.skilltree.summary import validate_export_payload


@runtime_checkable
class CurriculumGraphLike(Protocol):
    """Structural contract for the curriculum graph the exporter consumes."""

    @property
    def subjects(self) -> list[Subject]: ...

    @property
    def skills(self) -> list[Skill]: ...

    def prerequisite_edges(self) -> list[tuple[str, str]]: ...


class ExportError(ValueError):
    """Raised when a curriculum cannot be exported to a valid SkillTree project."""


_AMPERSAND_RE = re.compile(r"\s*&\s*")


def _quiz_display_name(skill_name: str) -> str:
    """Return a SkillTree quiz title that renders cleanly in the official UI."""
    return f"{_AMPERSAND_RE.sub(' and ', skill_name).strip()} Quiz"


def _map_skill(skill: Skill) -> SkillTreeSkill:
    """Map one curriculum Skill onto a SkillTreeSkill (fields straight across)."""
    quiz_id = (
        f"{skill.skill_id}_quiz"
        if skill.self_reporting_type == "Quiz" and skill.assessments
        else ""
    )
    return SkillTreeSkill(
        skill_id=skill.skill_id,
        name=skill.name,
        point_increment=skill.point_increment,
        num_perform_to_completion=skill.num_perform_to_completion,
        description=skill.description,
        help_url=skill.help_url,
        self_reporting_type=skill.self_reporting_type,
        quiz_id=quiz_id,
    )


def _map_subject(subject: Subject) -> SkillTreeSubject:
    return SkillTreeSubject(
        subject_id=subject.subject_id,
        name=subject.name,
        description=subject.description,
        skills=[_map_skill(s) for s in subject.skills],
    )


def _quiz_question(question: AssessmentQuestion) -> QuizQuestion:
    """Map an AssessmentQuestion's correct indices to per-answer isCorrect flags."""
    correct = set(question.correct)
    answers = [
        {"answer": text, "isCorrect": idx in correct}
        for idx, text in enumerate(question.answers)
    ]
    return QuizQuestion(
        question=question.prompt,
        answers=answers,
        question_type=question.question_type,
    )


def _quiz_for_skill(skill: Skill) -> Quiz:
    """Build a SkillTree Quiz for a Quiz-typed skill carrying assessments."""
    return Quiz(
        quiz_id=f"{skill.skill_id}_quiz",
        name=_quiz_display_name(skill.name),
        questions=[_quiz_question(q) for q in skill.assessments],
    )


def export_project(
    graph: CurriculumGraphLike, project_id: str, project_name: str
) -> SkillTreeProject:
    """Export a curriculum graph into a :class:`SkillTreeProject`.

    Guarantees that every ``skillId`` is unique within the project; raises
    :class:`ExportError` on a duplicate.
    """
    subjects: list[SkillTreeSubject] = []
    seen_skill_ids: set[str] = set()

    for subject in graph.subjects:
        st_subject = _map_subject(subject)
        for st_skill in st_subject.skills:
            if st_skill.skill_id in seen_skill_ids:
                raise ExportError(
                    f"duplicate skillId {st_skill.skill_id!r} within project {project_id!r}"
                )
            seen_skill_ids.add(st_skill.skill_id)
        subjects.append(st_subject)

    dependencies: list[SkillDependency] = []
    for prerequisite_id, dependent_id in graph.prerequisite_edges():
        # SkillTree edge semantics: the dependent skill depends on its prerequisite.
        dependencies.append(
            SkillDependency(skill_id=dependent_id, depends_on_skill_id=prerequisite_id)
        )

    quizzes: list[Quiz] = []
    for skill in graph.skills:
        if skill.self_reporting_type == "Quiz" and skill.assessments:
            try:
                quizzes.append(_quiz_for_skill(skill))
            except SkillTreeModelError as exc:  # pragma: no cover - defensive
                raise ExportError(
                    f"skill {skill.skill_id} produced an invalid quiz: {exc}"
                ) from exc

    project = SkillTreeProject(
        project_id=project_id,
        name=project_name,
        subjects=subjects,
        dependencies=dependencies,
        quizzes=quizzes,
    )
    # This curriculum holds a strict 1:1 skill↔quiz invariant (every quiz is generated for
    # exactly one Quiz-typed skill), so an orphan quiz here is a generator defect, not an
    # intentional pool. Enforce that at the export seam — the generic model deliberately
    # leaves orphan-policy to the caller.
    orphans = project.orphan_quiz_ids()
    if orphans:
        raise ExportError(
            f"export defines quizzes referenced by no skill (1:1 invariant broken): "
            f"{', '.join(orphans)}"
        )
    return project


def export_to_json(
    graph: CurriculumGraphLike,
    project_id: str,
    project_name: str,
    path: str | Path,
) -> Path:
    """Export and write deterministic, sorted JSON to ``path``; return the path."""
    project = export_project(graph, project_id, project_name)
    out_path = Path(path)
    payload = project.to_export_dict()
    # Validate the serialized handoff, not only the in-memory model. This keeps
    # the dashboard and live seeder from receiving a structurally plausible but
    # malformed artifact if the export schema changes independently of the model.
    validate_export_payload(payload)
    return write_json_artifact(out_path, payload, ensure_ascii=False)
