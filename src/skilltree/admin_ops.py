"""Canonical SkillTree admin endpoint paths and request bodies."""

from __future__ import annotations

from typing import Any
from urllib.parse import quote

from src.skilltree.model import (
    QuizQuestion,
    SkillDependency,
    SkillTreeSkill,
    SkillTreeSubject,
)


def _path_segment(value: str, *, field: str) -> str:
    """Encode one identifier before placing it in an admin URL path."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be non-empty")
    if any(ord(char) < 0x20 or ord(char) == 0x7F for char in value):
        raise ValueError(f"{field} must not contain control characters")
    return quote(value, safe="-._~")


def project_create_path(project_id: str) -> str:
    return f"/admin/projects/{_path_segment(project_id, field='project_id')}"


def project_create_body(project_id: str, name: str) -> dict[str, Any]:
    return {"projectId": project_id, "name": name}


def subject_create_path(project_id: str, subject_id: str) -> str:
    return (
        f"/admin/projects/{_path_segment(project_id, field='project_id')}"
        f"/subjects/{_path_segment(subject_id, field='subject_id')}"
    )


def skill_create_path(project_id: str, subject_id: str, skill_id: str) -> str:
    return (
        f"/admin/projects/{_path_segment(project_id, field='project_id')}"
        f"/subjects/{_path_segment(subject_id, field='subject_id')}"
        f"/skills/{_path_segment(skill_id, field='skill_id')}"
    )


def dependency_assign_path(project_id: str, dep: SkillDependency) -> str:
    return (
        f"/admin/projects/{_path_segment(project_id, field='project_id')}"
        f"/{_path_segment(dep.skill_id, field='skill_id')}"
        f"/prerequisite/{_path_segment(project_id, field='project_id')}"
        f"/{_path_segment(dep.depends_on_skill_id, field='depends_on_skill_id')}"
    )


def quiz_definition_path(quiz_id: str) -> str:
    return f"/admin/quiz-definitions/{_path_segment(quiz_id, field='quiz_id')}"


def quiz_questions_path(quiz_id: str) -> str:
    return (
        f"/admin/quiz-definitions/{_path_segment(quiz_id, field='quiz_id')}/questions"
    )


def quiz_question_create_path(quiz_id: str) -> str:
    return (
        f"/admin/quiz-definitions/{_path_segment(quiz_id, field='quiz_id')}"
        "/create-question"
    )


def report_skill_path(project_id: str, skill_id: str) -> str:
    return (
        f"/api/projects/{_path_segment(project_id, field='project_id')}"
        f"/skills/{_path_segment(skill_id, field='skill_id')}"
    )


def subject_payload(subject: SkillTreeSubject) -> dict[str, Any]:
    return subject.to_dict()


def skill_payload(skill: SkillTreeSkill) -> dict[str, Any]:
    return skill.to_dict()


def dependency_payload(dep: SkillDependency) -> dict[str, Any]:
    return dep.to_dict()


def quiz_question_payload(question: QuizQuestion) -> dict[str, Any]:
    return question.to_admin_create_payload()
