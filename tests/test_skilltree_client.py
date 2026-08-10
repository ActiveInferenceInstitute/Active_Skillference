"""Tests for SkillTreeClient against a real local HTTP server."""

from __future__ import annotations

import json
import threading
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
from pytest_httpserver import HTTPServer

from src.skilltree.client import (
    SkillTreeClient,
    SkillTreeClientError,
    quiz_question_count,
)
from src.skilltree.model import (
    Quiz,
    QuizQuestion,
    SkillDependency,
    SkillTreeSkill,
    SkillTreeSubject,
)

PROJECT_ID = "active_inference"


@pytest.fixture
def client(httpserver: HTTPServer) -> SkillTreeClient:
    return SkillTreeClient(
        base_url=httpserver.url_for("").rstrip("/"),
        project_id=PROJECT_ID,
        token="secret-token",
    )


def test_create_project_hits_admin_path(
    httpserver: HTTPServer, client: SkillTreeClient
) -> None:
    httpserver.expect_request(
        f"/admin/projects/{PROJECT_ID}", method="POST"
    ).respond_with_json({"projectId": PROJECT_ID, "created": True})

    result = client.create_project("Active Inference")
    assert result == {"projectId": PROJECT_ID, "created": True}


def test_create_project_sends_bearer_token(
    httpserver: HTTPServer, client: SkillTreeClient
) -> None:
    httpserver.expect_request(
        f"/admin/projects/{PROJECT_ID}",
        method="POST",
        headers={"Authorization": "Bearer secret-token"},
    ).respond_with_json({"ok": True})
    assert client.create_project("Active Inference") == {"ok": True}


def test_create_subject_hits_subject_path(
    httpserver: HTTPServer, client: SkillTreeClient
) -> None:
    subject = SkillTreeSubject(subject_id="prob", name="Probability")
    httpserver.expect_request(
        f"/admin/projects/{PROJECT_ID}/subjects/prob", method="POST"
    ).respond_with_json({"subjectId": "prob"})
    assert client.create_subject(subject) == {"subjectId": "prob"}


def test_create_skill_hits_skill_path(
    httpserver: HTTPServer, client: SkillTreeClient
) -> None:
    skill = SkillTreeSkill(skill_id="bayes", name="Bayes Rule")
    httpserver.expect_request(
        f"/admin/projects/{PROJECT_ID}/subjects/prob/skills/bayes", method="POST"
    ).respond_with_json({"skillId": "bayes"})
    assert client.create_skill("prob", skill) == {"skillId": "bayes"}


def test_assign_dependency_hits_prerequisite_path(
    httpserver: HTTPServer, client: SkillTreeClient
) -> None:
    dep = SkillDependency(skill_id="bayes", depends_on_skill_id="addition")
    httpserver.expect_request(
        f"/admin/projects/{PROJECT_ID}/bayes/prerequisite/{PROJECT_ID}/addition",
        method="POST",
    ).respond_with_json({"ok": True})
    assert client.assign_dependency(dep) == {"ok": True}


def test_create_quiz_hits_quiz_definitions_path(
    httpserver: HTTPServer, client: SkillTreeClient
) -> None:
    quiz = Quiz(
        quiz_id="bayes_quiz",
        name="Bayes Quiz",
        questions=[
            QuizQuestion(question="q?", answers=[{"answer": "a", "isCorrect": True}])
        ],
    )
    httpserver.expect_request(
        "/admin/quiz-definitions/bayes_quiz", method="POST"
    ).respond_with_json({"quizId": "bayes_quiz"})
    httpserver.expect_request(
        "/admin/quiz-definitions/bayes_quiz/questions", method="GET"
    ).respond_with_json({"quizType": "Quiz", "questions": []})
    httpserver.expect_request(
        "/admin/quiz-definitions/bayes_quiz/create-question",
        method="POST",
        json={
            "question": "q?",
            "answerHint": "",
            "questionType": "SingleChoice",
            "questionScale": 5,
            "answers": [{"answer": "a", "isCorrect": True}],
        },
    ).respond_with_json({"id": 123})
    assert client.create_quiz(quiz) == {"quizId": "bayes_quiz"}


def test_create_quiz_does_not_duplicate_existing_questions(
    httpserver: HTTPServer, client: SkillTreeClient
) -> None:
    quiz = Quiz(
        quiz_id="bayes_quiz",
        name="Bayes Quiz",
        questions=[
            QuizQuestion(question="q?", answers=[{"answer": "a", "isCorrect": True}])
        ],
    )
    httpserver.expect_request(
        "/admin/quiz-definitions/bayes_quiz", method="POST"
    ).respond_with_json({"quizId": "bayes_quiz"})
    httpserver.expect_request(
        "/admin/quiz-definitions/bayes_quiz/questions", method="GET"
    ).respond_with_json({"quizType": "Quiz", "questions": [{"id": 1}]})

    assert client.create_quiz(quiz) == {"quizId": "bayes_quiz"}


def test_create_quiz_appends_missing_question_suffix(
    httpserver: HTTPServer, client: SkillTreeClient
) -> None:
    quiz = Quiz(
        quiz_id="bayes_quiz",
        name="Bayes Quiz",
        questions=[
            QuizQuestion(question="q1?", answers=[{"answer": "a", "isCorrect": True}]),
            QuizQuestion(question="q2?", answers=[{"answer": "b", "isCorrect": True}]),
        ],
    )
    httpserver.expect_request(
        "/admin/quiz-definitions/bayes_quiz", method="POST"
    ).respond_with_json({"quizId": "bayes_quiz"})
    httpserver.expect_request(
        "/admin/quiz-definitions/bayes_quiz/questions", method="GET"
    ).respond_with_json({"quizType": "Quiz", "questions": [{"id": 1}]})
    httpserver.expect_request(
        "/admin/quiz-definitions/bayes_quiz/create-question",
        method="POST",
        json={
            "question": "q2?",
            "answerHint": "",
            "questionType": "SingleChoice",
            "questionScale": 5,
            "answers": [{"answer": "b", "isCorrect": True}],
        },
    ).respond_with_json({"id": 2})

    assert client.create_quiz(quiz) == {"quizId": "bayes_quiz"}


def test_quiz_question_count_accepts_skilltree_envelopes() -> None:
    assert quiz_question_count({"questions": [{"id": 1}]}) == 1
    assert quiz_question_count({"data": {"questions": [{"id": 1}, {"id": 2}]}}) == 2
    assert quiz_question_count({"numQuestions": 3}) == 3
    assert quiz_question_count([]) == 0
    # Negative control (convergence #3): a negative numQuestions is malformed, not a
    # real count — it must not propagate upward (falls through to 0).
    assert quiz_question_count({"numQuestions": -5}) == 0


def test_report_skill_hits_api_path_and_sends_user_id(
    httpserver: HTTPServer, client: SkillTreeClient
) -> None:
    def handler(request):  # type: ignore[no-untyped-def]
        from werkzeug.wrappers import Response

        body = json.loads(request.get_data())
        assert body == {"userId": "user-42"}
        return Response(json.dumps({"reported": True}), content_type="application/json")

    httpserver.expect_request(
        f"/api/projects/{PROJECT_ID}/skills/bayes", method="POST"
    ).respond_with_handler(handler)

    assert client.report_skill("bayes", "user-42") == {"reported": True}


def test_non_2xx_raises_client_error(
    httpserver: HTTPServer, client: SkillTreeClient
) -> None:
    httpserver.expect_request(
        f"/admin/projects/{PROJECT_ID}", method="POST"
    ).respond_with_data("boom", status=500)

    with pytest.raises(SkillTreeClientError) as exc_info:
        client.create_project("Active Inference")
    assert exc_info.value.status == 500
    assert exc_info.value.body == "boom"


def test_404_raises_client_error(
    httpserver: HTTPServer, client: SkillTreeClient
) -> None:
    httpserver.expect_request(
        f"/admin/projects/{PROJECT_ID}/subjects/missing", method="POST"
    ).respond_with_data("nope", status=404)
    with pytest.raises(SkillTreeClientError) as exc_info:
        client.create_subject(SkillTreeSubject(subject_id="missing", name="Missing"))
    assert exc_info.value.status == 404


def test_empty_2xx_body_returns_empty_dict(
    httpserver: HTTPServer, client: SkillTreeClient
) -> None:
    httpserver.expect_request(
        f"/admin/projects/{PROJECT_ID}", method="POST"
    ).respond_with_data("", status=204)
    assert client.create_project("Active Inference") == {}


def test_client_without_token_omits_authorization() -> None:
    # No server call — just verify token-less construction is valid.
    c = SkillTreeClient(base_url="http://localhost:1/", project_id="p")
    assert c.token is None
    assert c.base_url == "http://localhost:1"


def test_client_rejects_empty_project_id() -> None:
    with pytest.raises(ValueError, match="project_id must be non-empty"):
        SkillTreeClient(base_url="http://x", project_id="  ")


def test_client_rejects_empty_base_url() -> None:
    with pytest.raises(ValueError, match="base_url must be non-empty"):
        SkillTreeClient(base_url="", project_id="p")


def test_client_rejects_non_http_base_url() -> None:
    with pytest.raises(ValueError, match="only http/https URLs"):
        SkillTreeClient(base_url="file:///tmp/skilltree", project_id="p")


def test_admin_paths_encode_identifier_boundaries() -> None:
    from src.skilltree.admin_ops import skill_create_path

    assert skill_create_path("project/x", "subject y", "skill?z") == (
        "/admin/projects/project%2Fx/subjects/subject%20y/skills/skill%3Fz"
    )


def test_authorized_request_blocks_cross_origin_redirect() -> None:
    redirected_authorization: list[str | None] = []

    class TargetHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            redirected_authorization.append(self.headers.get("Authorization"))
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b"{}")

        def do_POST(self) -> None:
            self.do_GET()

        def log_message(self, format: str, *args: object) -> None:
            return

    target = ThreadingHTTPServer(("127.0.0.1", 0), TargetHandler)
    target_thread = threading.Thread(target=target.serve_forever, daemon=True)
    target_thread.start()

    class RedirectHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            host, port = target.server_address
            self.send_response(HTTPStatus.FOUND)
            self.send_header("Location", f"http://{host}:{port}/capture")
            self.end_headers()

        def log_message(self, format: str, *args: object) -> None:
            return

    redirector = ThreadingHTTPServer(("127.0.0.1", 0), RedirectHandler)
    redirect_thread = threading.Thread(target=redirector.serve_forever, daemon=True)
    redirect_thread.start()
    try:
        host, port = redirector.server_address
        client = SkillTreeClient(
            base_url=f"http://{host}:{port}",
            project_id=PROJECT_ID,
            token="sentinel-token",
        )
        with pytest.raises(SkillTreeClientError) as exc_info:
            client._get("/redirect-me")
    finally:
        redirector.shutdown()
        target.shutdown()
        redirector.server_close()
        target.server_close()
        redirect_thread.join(timeout=2)
        target_thread.join(timeout=2)

    assert exc_info.value.status == HTTPStatus.FOUND
    assert redirected_authorization == []
