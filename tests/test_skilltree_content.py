"""Real loopback regressions for identity/content parity and idempotent quiz seeding."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from pytest_httpserver import HTTPServer

from src.dashboard.artifacts import load_skilltree_project
from src.dashboard.config import DashboardConfig
from src.dashboard.payload import live_skilltree_summary
from src.skilltree.client import SkillTreeClient
from src.skilltree.content import (
    SkillTreeContentError,
    compare_live_content,
    export_content_digest,
)
from src.skilltree.local_auth import (
    LocalSkillTreeState,
    SkillTreeSessionClient,
    ensure_local_skilltree_auth,
    save_local_state,
)
from src.skilltree.local_auth_state import LocalSkillTreeAuthError
from src.skilltree.model import SkillTreeProject


def _compare(httpserver: HTTPServer, project: SkillTreeProject) -> dict:
    client = SkillTreeClient(
        httpserver.url_for(""), project.project_id, token="synthetic-test-token"
    )
    return compare_live_content(
        get=client._get,
        base_url=client.base_url,
        project=project.to_export_dict(),
    )


def test_matching_actual_content_is_digest_bound_and_answer_key_free(
    httpserver: HTTPServer,
    content_project,
    skilltree_admin_content,
) -> None:
    skilltree_admin_content(httpserver, content_project)
    result = _compare(httpserver, content_project)
    assert result["checked"] is True and result["complete"] is True
    assert result["projectId"] == "p"
    assert result["exportContentDigest"] == export_content_digest(
        content_project.to_export_dict()
    )
    assert "isCorrect" not in json.dumps(result)
    assert "synthetic-test-token" not in json.dumps(result)


@pytest.mark.parametrize("change", ["answer", "lesson", "extra_question"])
def test_same_counts_cannot_hide_changed_content(
    httpserver: HTTPServer,
    content_project,
    skilltree_admin_content,
    change: str,
) -> None:
    live = copy.deepcopy(content_project.to_export_dict())
    if change == "answer":
        live["quizzes"][0]["questions"][0]["answers"][0]["isCorrect"] = False
    elif change == "lesson":
        live["subjects"][0]["skills"][0]["description"] = "Different lesson"
    else:
        live["quizzes"][0]["questions"].append(live["quizzes"][0]["questions"][0])
    skilltree_admin_content(httpserver, live)
    result = _compare(httpserver, content_project)
    assert result["checked"] is True and result["complete"] is False
    assert result["changedResources"]
    assert result["subjects"] == 1 and result["skills"] == 1


def test_count_only_admin_response_is_unverifiable(
    httpserver: HTTPServer, content_project
) -> None:
    httpserver.expect_request("/admin/projects/p", method="GET").respond_with_json(
        {"numSkills": 1, "numSubjects": 1}
    )
    with pytest.raises(SkillTreeContentError, match="unverifiable"):
        _compare(httpserver, content_project)


@pytest.mark.parametrize("client_type", [SkillTreeClient, SkillTreeSessionClient])
def test_existing_second_question_does_not_suppress_missing_first(
    httpserver: HTTPServer,
    content_project,
    client_type,
) -> None:
    quiz = content_project.quizzes[0]
    httpserver.expect_request(
        "/admin/quiz-definitions/q", method="POST"
    ).respond_with_json({})
    httpserver.expect_request(
        "/admin/quiz-definitions/q/questions", method="GET"
    ).respond_with_json({"questions": [quiz.questions[1].to_dict()]})
    httpserver.expect_request(
        "/admin/quiz-definitions/q/create-question",
        method="POST",
        json=quiz.questions[0].to_admin_create_payload(),
    ).respond_with_json({"id": 1})
    client = client_type(httpserver.url_for(""), "p")
    client.create_quiz(quiz)
    posted = [
        request.get_json()
        for request, _ in httpserver.log
        if request.path.endswith("/create-question")
    ]
    assert posted == [quiz.questions[0].to_admin_create_payload()]
    httpserver.check_assertions()


@pytest.mark.parametrize("client_type", [SkillTreeClient, SkillTreeSessionClient])
def test_extra_question_occurrence_is_refused_without_any_question_write(
    httpserver: HTTPServer,
    content_project,
    client_type,
) -> None:
    quiz = content_project.quizzes[0]
    questions = [question.to_dict() for question in quiz.questions]
    httpserver.expect_request(
        "/admin/quiz-definitions/q", method="POST"
    ).respond_with_json({})
    httpserver.expect_request(
        "/admin/quiz-definitions/q/questions", method="GET"
    ).respond_with_json({"questions": questions + [questions[0]]})
    with pytest.raises(SkillTreeContentError, match="extra or changed"):
        client_type(httpserver.url_for(""), "p").create_quiz(quiz)
    assert not any(
        request.path.endswith("/create-question") for request, _ in httpserver.log
    )


def test_live_summary_never_sends_stored_credentials_to_second_origin(
    tmp_path: Path,
    httpserver: HTTPServer,
    content_project,
) -> None:
    original = httpserver.url_for("").rstrip("/")
    second = HTTPServer(host="127.0.0.1", port=0)
    second.start()
    try:
        state_dir = tmp_path / "private"
        save_local_state(
            state_dir,
            LocalSkillTreeState(
                admin_username="admin@localhost.invalid",
                admin_password="stored-secret",
                learner_id="learner",
                project_id="p",
                skilltree_url=original,
                client_secret="trusted-secret",
            ),
        )
        config = DashboardConfig(
            project_root=tmp_path,
            project_id="p",
            project_name="Project",
            skilltree_url=second.url_for(""),
            local_auth_enabled=True,
            local_state_dir=state_dir,
        )
        exported = content_project.to_export_dict()
        public = load_skilltree_project(tmp_path, export_payload=exported)
        result = live_skilltree_summary(config, public, export_payload=exported)
        assert result["checked"] is False
        assert "does not match" in result["reason"]
        assert second.log == []
        assert httpserver.log == []
        assert "stored-secret" not in json.dumps(result)
    finally:
        second.stop()


def test_bootstrap_target_mismatch_is_refused_before_any_network(
    tmp_path: Path,
    httpserver: HTTPServer,
    content_project,
) -> None:
    with pytest.raises(LocalSkillTreeAuthError, match="bootstrap target"):
        ensure_local_skilltree_auth(
            base_url=httpserver.url_for(""),
            project_id="different",
            project=content_project,
            state_dir=tmp_path,
        )
    assert httpserver.log == []


@pytest.mark.parametrize("client_type", [SkillTreeClient, SkillTreeSessionClient])
def test_missing_duplicate_question_occurrence_is_created_once(
    httpserver, content_project, client_type
) -> None:
    quiz = content_project.quizzes[0]
    first = copy.deepcopy(quiz.questions[0])
    quiz.questions[:] = [first, copy.deepcopy(first)]
    httpserver.expect_request(
        "/admin/quiz-definitions/q", method="POST"
    ).respond_with_json({})
    httpserver.expect_request(
        "/admin/quiz-definitions/q/questions", method="GET"
    ).respond_with_json({"questions": [first.to_dict()]})
    httpserver.expect_request(
        "/admin/quiz-definitions/q/create-question",
        method="POST",
        json=first.to_admin_create_payload(),
    ).respond_with_json({"id": 2})

    client_type(httpserver.url_for(""), "p").create_quiz(quiz)

    posted = [
        request.get_json()
        for request, _response in httpserver.log
        if request.path.endswith("/create-question")
    ]
    assert posted == [first.to_admin_create_payload()]
    httpserver.check_assertions()


@pytest.mark.parametrize("changed", ["lesson", "answer"])
def test_existing_changed_content_is_refused_before_any_seed_write(
    httpserver,
    content_project,
    skilltree_admin_content,
    changed: str,
) -> None:
    from src.skilltree.local_auth import _seed_project_if_requested

    live = copy.deepcopy(content_project.to_export_dict())
    if changed == "lesson":
        live["subjects"][0]["skills"][0]["description"] = "Different lesson"
    else:
        live["quizzes"][0]["questions"][0]["answers"][0]["isCorrect"] = False
    skilltree_admin_content(httpserver, live)
    client = SkillTreeSessionClient(httpserver.url_for(""), "p")
    with pytest.raises(LocalSkillTreeAuthError, match="not overwritten"):
        _seed_project_if_requested(
            client=client,
            project=content_project,
            seed_project=True,
            seed_dependencies=False,
            skip_seed_if_live_content_ready=True,
            verify_seed=True,
        )
    assert httpserver.log and all(
        request.method == "GET" for request, _response in httpserver.log
    )


@pytest.mark.parametrize(
    ("settings", "complete"),
    [
        ([], True),
        ([{"setting": "quizUserRole", "value": "ROLE_QUIZ_ADMIN"}], True),
        ([{"setting": "quizLength", "value": "-1"}], True),
        ([{"setting": "quizPassingReq", "value": "-1"}], True),
        ([{"setting": "quizPassingReq", "value": "0"}], True),
        ([{"setting": "quizPassingReq", "value": "2"}], True),
        ([{"setting": "quizPassingReq", "value": "1"}], False),
        ([{"setting": "quizLength", "value": "1"}], False),
    ],
)
def test_native_quiz_settings_preserve_full_question_completion(
    httpserver,
    content_project,
    skilltree_admin_content,
    settings,
    complete,
) -> None:
    skilltree_admin_content(
        httpserver,
        content_project,
        quiz_settings={"q": settings},
    )
    result = _compare(httpserver, content_project)
    assert result["complete"] is complete
    assert result["changedResources"] == ([] if complete else ["quiz:q"])
    assert result["missingResources"] == []
    httpserver.check_assertions()


def test_export_percentage_is_compared_with_native_correct_question_count(
    httpserver,
    content_project,
    skilltree_admin_content,
) -> None:
    from dataclasses import replace

    content_project.quizzes[0] = replace(content_project.quizzes[0], passing_percent=50)
    skilltree_admin_content(
        httpserver,
        content_project,
        quiz_settings={"q": [{"setting": "quizPassingReq", "value": "1"}]},
    )
    assert _compare(httpserver, content_project)["complete"] is True


@pytest.mark.parametrize(
    "settings",
    [
        [{"setting": "quizPassingReq", "value": True}],
        [{"setting": "quizPassingReq", "value": "NaN"}],
        [{"setting": "quizPassingReq", "value": "3"}],
        [{"setting": "quizLength", "value": "0"}],
        [{"setting": "quizLength", "value": "-2"}],
        [
            {"setting": "quizPassingReq", "value": "2"},
            {"setting": "quizPassingReq", "value": "1"},
        ],
    ],
)
def test_unverifiable_native_quiz_settings_fail_closed(
    httpserver,
    content_project,
    skilltree_admin_content,
    settings,
) -> None:
    skilltree_admin_content(
        httpserver,
        content_project,
        quiz_settings={"q": settings},
    )
    with pytest.raises(SkillTreeContentError):
        _compare(httpserver, content_project)
    assert all(request.method == "GET" for request, _response in httpserver.log)
