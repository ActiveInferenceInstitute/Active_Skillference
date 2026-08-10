"""Seed a SkillTree instance from an exported :class:`SkillTreeProject`.

Creation order matters: project → subjects → quizzes → skills → dependencies.
Quiz definitions must exist before quiz-gated skills are created. Dependencies
are assigned LAST among the structural creates so both endpoints of every
prerequisite edge already exist before the edge is wired.
"""

from __future__ import annotations

from typing import Any, Protocol

from src.skilltree.model import SkillTreeProject


class SeedClient(Protocol):
    """Minimal admin client protocol used by the seeder."""

    def create_project(self, name: str) -> Any: ...

    def create_subject(self, subject: Any) -> Any: ...

    def create_skill(self, subject_id: str, skill: Any) -> Any: ...

    def assign_dependency(self, dep: Any) -> Any: ...

    def create_quiz(self, quiz: Any) -> Any: ...


def seed(
    client: SeedClient,
    project: SkillTreeProject,
    *,
    include_dependencies: bool = True,
) -> dict[str, int]:
    """Create the whole project on the SkillTree instance behind ``client``.

    Returns a summary count dict::

        {"projects": 1, "subjects": N, "skills": M, "dependencies": E, "quizzes": Q}
    """
    client.create_project(project.name)

    subject_count = 0
    for subject in project.subjects:
        client.create_subject(subject)
        subject_count += 1

    quiz_count = 0
    for quiz in project.quizzes:
        client.create_quiz(quiz)
        quiz_count += 1

    skill_count = 0
    for subject in project.subjects:
        for skill in subject.skills:
            client.create_skill(subject.subject_id, skill)
            skill_count += 1

    dependency_count = 0
    if include_dependencies:
        # Dependencies LAST (after every skill endpoint exists).
        for dep in project.dependencies:
            client.assign_dependency(dep)
            dependency_count += 1

    summary: dict[str, int] = {
        "projects": 1,
        "subjects": subject_count,
        "skills": skill_count,
        "dependencies": dependency_count,
        "quizzes": quiz_count,
    }
    return summary
