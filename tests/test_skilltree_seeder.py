"""Tests for the seeder against a real local HTTP server.

Ordering is asserted via the recorded request order on the httpserver: the
seeder creates quizzes before quiz-gated skills, then issues dependency edges
only AFTER every skill endpoint exists.
"""

from __future__ import annotations

import re

from pytest_httpserver import HTTPServer
from werkzeug.wrappers import Response

from src.skilltree.client import SkillTreeClient
from src.skilltree.model import (
    Quiz,
    QuizQuestion,
    SkillDependency,
    SkillTreeProject,
    SkillTreeSkill,
    SkillTreeSubject,
)
from src.skilltree.seeder import seed

PROJECT_ID = "active_inference"


def _project() -> SkillTreeProject:
    return SkillTreeProject(
        project_id=PROJECT_ID,
        name="Active Inference",
        subjects=[
            SkillTreeSubject(
                subject_id="math",
                name="Math",
                skills=[
                    SkillTreeSkill(skill_id="counting", name="Counting"),
                    SkillTreeSkill(skill_id="addition", name="Addition"),
                ],
            ),
            SkillTreeSubject(
                subject_id="prob",
                name="Probability",
                skills=[SkillTreeSkill(skill_id="bayes", name="Bayes")],
            ),
        ],
        dependencies=[
            SkillDependency(skill_id="addition", depends_on_skill_id="counting"),
            SkillDependency(skill_id="bayes", depends_on_skill_id="addition"),
        ],
        quizzes=[
            Quiz(
                quiz_id="bayes_quiz",
                name="Bayes Quiz",
                questions=[
                    QuizQuestion(
                        question="q?", answers=[{"answer": "a", "isCorrect": True}]
                    )
                ],
            )
        ],
    )


def test_seed_returns_correct_summary(httpserver: HTTPServer) -> None:
    order: list[str] = []

    def handler(request):  # type: ignore[no-untyped-def]
        order.append(request.path)
        return Response("{}", content_type="application/json", status=200)

    httpserver.expect_request(re.compile(r"^/.*$")).respond_with_handler(handler)

    client = SkillTreeClient(
        base_url=httpserver.url_for("").rstrip("/"), project_id=PROJECT_ID
    )
    summary = seed(client, _project())

    assert summary == {
        "projects": 1,
        "subjects": 2,
        "skills": 3,
        "dependencies": 2,
        "quizzes": 1,
    }


def test_seed_issues_dependencies_after_all_skills(httpserver: HTTPServer) -> None:
    order: list[str] = []

    def handler(request):  # type: ignore[no-untyped-def]
        order.append(request.path)
        return Response("{}", content_type="application/json", status=200)

    httpserver.expect_request(re.compile(r"^/.*$")).respond_with_handler(handler)

    client = SkillTreeClient(
        base_url=httpserver.url_for("").rstrip("/"), project_id=PROJECT_ID
    )
    seed(client, _project())

    # Index of each request category in the recorded order.
    project_idx = next(
        i for i, p in enumerate(order) if p == f"/admin/projects/{PROJECT_ID}"
    )
    subject_indices = [
        i for i, p in enumerate(order) if "/subjects/" in p and "/skills/" not in p
    ]
    skill_indices = [
        i for i, p in enumerate(order) if "/subjects/" in p and "/skills/" in p
    ]
    dep_indices = [i for i, p in enumerate(order) if "/prerequisite/" in p]
    quiz_indices = [i for i, p in enumerate(order) if "/quiz-definitions/" in p]

    # project first
    assert project_idx == 0
    # subjects before their skills are created (first subject before first skill)
    assert min(subject_indices) < min(skill_indices)
    # quizzes before skills because live SkillTree validates quizId at skill create.
    assert max(quiz_indices) < min(skill_indices)
    # EVERY dependency comes AFTER EVERY skill create.
    assert min(dep_indices) > max(skill_indices)


def test_seed_full_path_ordering_exact(httpserver: HTTPServer) -> None:
    order: list[str] = []

    def handler(request):  # type: ignore[no-untyped-def]
        order.append(f"{request.method} {request.path}")
        return Response("{}", content_type="application/json", status=200)

    httpserver.expect_request(re.compile(r"^/.*$")).respond_with_handler(handler)

    client = SkillTreeClient(
        base_url=httpserver.url_for("").rstrip("/"), project_id=PROJECT_ID
    )
    seed(client, _project())

    assert order == [
        f"POST /admin/projects/{PROJECT_ID}",
        f"POST /admin/projects/{PROJECT_ID}/subjects/math",
        f"POST /admin/projects/{PROJECT_ID}/subjects/prob",
        "POST /admin/quiz-definitions/bayes_quiz",
        "GET /admin/quiz-definitions/bayes_quiz/questions",
        "POST /admin/quiz-definitions/bayes_quiz/create-question",
        f"POST /admin/projects/{PROJECT_ID}/subjects/math/skills/counting",
        f"POST /admin/projects/{PROJECT_ID}/subjects/math/skills/addition",
        f"POST /admin/projects/{PROJECT_ID}/subjects/prob/skills/bayes",
        f"POST /admin/projects/{PROJECT_ID}/addition/prerequisite/{PROJECT_ID}/counting",
        f"POST /admin/projects/{PROJECT_ID}/bayes/prerequisite/{PROJECT_ID}/addition",
    ]


def test_seed_can_defer_dependencies_for_dedicated_reconciler(
    httpserver: HTTPServer,
) -> None:
    order: list[str] = []

    def handler(request):  # type: ignore[no-untyped-def]
        order.append(f"{request.method} {request.path}")
        return Response("{}", content_type="application/json", status=200)

    httpserver.expect_request(re.compile(r"^/.*$")).respond_with_handler(handler)
    client = SkillTreeClient(
        base_url=httpserver.url_for("").rstrip("/"), project_id=PROJECT_ID
    )

    summary = seed(client, _project(), include_dependencies=False)

    assert summary["dependencies"] == 0
    assert not any("/prerequisite/" in path for path in order)
