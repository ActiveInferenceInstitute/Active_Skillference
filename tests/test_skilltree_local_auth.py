"""Tests for local-only SkillTree FORM auth bootstrap helpers."""

from __future__ import annotations

import base64
import json
import stat
from pathlib import Path

import pytest
from pytest_httpserver import HTTPServer
from werkzeug.wrappers import Response

from src.skilltree.client import SkillTreeClientError
from src.skilltree.local_auth import (
    DEFAULT_LOCAL_ADMIN_PASSWORD,
    DEFAULT_LOCAL_ADMIN_USERNAME,
    DEFAULT_LOCAL_LEARNER_ID,
    LOCAL_TOKEN_ENDPOINT,
    BootstrapResult,
    LocalSkillTreeAuthError,
    LocalSkillTreeState,
    SkillTreeSessionClient,
    _is_existing_resource_error,
    _parse_dependency_graph,
    _parse_secret_response,
    _refuse_default_password_off_loopback,
    default_local_request_timeout,
    describe_local_auth,
    ensure_local_skilltree_auth,
    exchange_trusted_client_token,
    fetch_local_skilltree_token,
    is_browser_login_compatible_username,
    load_local_state,
    new_local_state,
    root_account_payload,
    save_local_state,
    verify_seed_landed,
)
from src.skilltree.model import (
    Quiz,
    QuizQuestion,
    SkillDependency,
    SkillTreeProject,
    SkillTreeSkill,
    SkillTreeSubject,
)


def _state(
    client_secret: str = "trusted-secret",
    skilltree_url: str = "http://skilltree.local",
) -> LocalSkillTreeState:
    return LocalSkillTreeState(
        admin_username="active_skillference_admin",
        admin_password="admin-password",
        learner_id=DEFAULT_LOCAL_LEARNER_ID,
        project_id="activeInference",
        skilltree_url=skilltree_url,
        client_secret=client_secret,
    )


def test_local_state_round_trips_private_file(tmp_path: Path) -> None:
    state = _state()
    save_local_state(tmp_path, state)
    loaded = load_local_state(tmp_path)
    assert loaded == state
    assert (tmp_path / "skilltree_auth.json").exists()


def test_root_account_payload_matches_skilltree_user_info_shape() -> None:
    payload = root_account_payload(_state())
    assert payload["username"] == "active_skillference_admin"
    assert payload["password"] == "admin-password"
    assert payload["emailVerified"] is True
    assert payload["accountNonLocked"] is True


def test_create_root_account_sends_json_and_xsrf_header(
    httpserver: HTTPServer,
) -> None:
    def root_handler(request):  # type: ignore[no-untyped-def]
        body = json.loads(request.get_data())
        assert request.headers["X-XSRF-TOKEN"] == "csrf-token"
        assert body["username"] == "active_skillference_admin"
        assert body["password"] == "admin-password"
        return Response("{}", content_type="application/json")

    httpserver.expect_request("/", method="GET").respond_with_data(
        "<html></html>",
        headers={"Set-Cookie": "XSRF-TOKEN=csrf-token; Path=/"},
        content_type="text/html",
    )
    httpserver.expect_request("/createRootAccount", method="PUT").respond_with_handler(
        root_handler
    )

    client = SkillTreeSessionClient(
        httpserver.url_for("").rstrip("/"), "activeInference"
    )
    client.create_root_account(_state())


def test_login_posts_form_credentials_with_xsrf(httpserver: HTTPServer) -> None:
    def login_handler(request):  # type: ignore[no-untyped-def]
        form = request.form
        assert request.headers["X-XSRF-TOKEN"] == "csrf-token"
        assert form["username"] == "admin"
        assert form["password"] == "pw"
        return Response("{}", content_type="application/json")

    httpserver.expect_request("/", method="GET").respond_with_data(
        "<html></html>",
        headers={"Set-Cookie": "XSRF-TOKEN=csrf-token; Path=/"},
        content_type="text/html",
    )
    httpserver.expect_request("/performLogin", method="POST").respond_with_handler(
        login_handler
    )

    client = SkillTreeSessionClient(
        httpserver.url_for("").rstrip("/"), "activeInference"
    )
    client.login("admin", "pw")


def test_session_client_treats_existing_learning_path_as_idempotent(
    httpserver: HTTPServer,
) -> None:
    httpserver.expect_request(
        "/admin/projects/activeInference/m_vectors/prerequisite/activeInference/m_sets",
        method="POST",
    ).respond_with_json(
        {
            "explanation": "Learning path from [Sets] to [Vectors] already exists.",
            "errorCode": "FailedToAssignDependency",
            "success": False,
        },
        status=400,
    )

    client = SkillTreeSessionClient(
        httpserver.url_for("").rstrip("/"), "activeInference"
    )
    response = client.request_json_allowing_existing(
        "POST",
        "/admin/projects/activeInference/m_vectors/prerequisite/activeInference/m_sets",
        json_body={"skillId": "m_vectors", "dependsOnSkillId": "m_sets"},
    )

    assert response == {"success": True, "alreadyExisted": True}


def test_assign_dependency_skips_existing_live_learning_path(
    httpserver: HTTPServer,
) -> None:
    httpserver.expect_request(
        "/admin/projects/activeInference/dependency/graph", method="GET"
    ).respond_with_json(
        {
            "nodes": [
                {"id": 1, "skillId": "m_sets"},
                {"id": 2, "skillId": "m_vectors"},
            ],
            "edges": [{"fromId": 2, "toId": 1}],
        }
    )
    client = SkillTreeSessionClient(
        httpserver.url_for("").rstrip("/"), "activeInference"
    )

    response = client.assign_dependency(
        SkillDependency(skill_id="m_vectors", depends_on_skill_id="m_sets")
    )

    assert response == {"success": True, "alreadyExisted": True}
    httpserver.check_assertions()


def test_assign_dependency_reconciles_stale_reverse_learning_path(
    httpserver: HTTPServer,
) -> None:
    order: list[str] = []

    def record(request):  # type: ignore[no-untyped-def]
        order.append(f"{request.method} {request.path}")
        return Response("{}", content_type="application/json")

    httpserver.expect_request(
        "/admin/projects/activeInference/dependency/graph", method="GET"
    ).respond_with_json(
        {
            "nodes": [
                {"id": 1, "skillId": "m_sets"},
                {"id": 2, "skillId": "m_vectors"},
            ],
            "edges": [{"fromId": 1, "toId": 2}],
        }
    )
    httpserver.expect_request(
        "/admin/projects/activeInference/m_sets/prerequisite/activeInference/m_vectors",
        method="DELETE",
    ).respond_with_handler(record)
    httpserver.expect_request(
        "/admin/projects/activeInference/m_vectors/prerequisite/activeInference/m_sets",
        method="POST",
    ).respond_with_handler(record)
    client = SkillTreeSessionClient(
        httpserver.url_for("").rstrip("/"), "activeInference"
    )

    response = client.assign_dependency(
        SkillDependency(skill_id="m_vectors", depends_on_skill_id="m_sets")
    )

    assert response == {}
    assert order == [
        "DELETE /admin/projects/activeInference/m_sets/prerequisite/activeInference/m_vectors",
        "POST /admin/projects/activeInference/m_vectors/prerequisite/activeInference/m_sets",
    ]
    httpserver.check_assertions()


def test_assign_dependency_confirms_edge_after_timeout(
    httpserver: HTTPServer,
) -> None:
    class ConfirmingDependencyClient(SkillTreeSessionClient):
        def __init__(self) -> None:
            super().__init__(httpserver.url_for("").rstrip("/"), "activeInference")
            self.graph_reads = 0

        def live_dependency_pairs(self) -> set[tuple[str, str]]:
            self.graph_reads += 1
            if self.graph_reads == 1:
                return set()
            return {("m_vectors", "m_sets")}

        def request_json_allowing_existing(
            self,
            method: str,
            path: str,
            *,
            json_body: dict[str, object] | None = None,
        ) -> object:
            _ = (method, path, json_body)
            raise SkillTreeClientError(
                "POST dependency timed out after 120s", status=None
            )

    client = ConfirmingDependencyClient()

    response = client.assign_dependency(
        SkillDependency(skill_id="m_vectors", depends_on_skill_id="m_sets")
    )

    assert response == {
        "success": True,
        "alreadyExisted": True,
        "confirmedAfterError": True,
    }


def test_parse_dependency_graph_rejects_missing_graph_lists() -> None:
    try:
        _parse_dependency_graph({"nodes": []})
    except LocalSkillTreeAuthError as exc:
        assert "nodes/edges lists" in str(exc)
    else:
        raise AssertionError("malformed dependency graph accepted")


def test_exchange_trusted_client_token_uses_basic_auth_and_proxy_user(
    httpserver: HTTPServer,
) -> None:
    def token_handler(request):  # type: ignore[no-untyped-def]
        scheme, encoded = request.headers["Authorization"].split(" ", 1)
        assert scheme == "Basic"
        assert base64.b64decode(encoded).decode("utf-8") == "activeInference:secret"
        assert request.form["grant_type"] == "client_credentials"
        assert request.form["proxy_user"] == "local-learner"
        return Response(
            json.dumps({"access_token": "token", "token_type": "Bearer"}),
            content_type="application/json",
        )

    httpserver.expect_request("/oauth/token", method="POST").respond_with_handler(
        token_handler
    )

    token = exchange_trusted_client_token(
        base_url=httpserver.url_for("").rstrip("/"),
        project_id="activeInference",
        client_secret="secret",
        learner_id="local-learner",
    )
    assert token["access_token"] == "token"


def test_fetch_local_skilltree_token_uses_stored_secret(
    tmp_path: Path,
    httpserver: HTTPServer,
) -> None:
    base_url = httpserver.url_for("").rstrip("/")
    save_local_state(
        tmp_path,
        _state(client_secret="stored-secret", skilltree_url=base_url),
    )
    httpserver.expect_request("/oauth/token", method="POST").respond_with_json(
        {"access_token": "token", "expires_in": 3600}
    )

    token = fetch_local_skilltree_token(
        base_url=base_url,
        state_dir=tmp_path,
        project_id="activeInference",
        learner_id="local-learner",
    )
    assert token["access_token"] == "token"


def test_fetch_local_skilltree_token_rejects_state_url_mismatch(
    tmp_path: Path,
) -> None:
    save_local_state(
        tmp_path,
        _state(
            client_secret="stored-secret",
            skilltree_url="http://original.local:8080",
        ),
    )

    with pytest.raises(LocalSkillTreeAuthError, match="does not match"):
        fetch_local_skilltree_token(
            base_url="http://capture.local:8080",
            state_dir=tmp_path,
            project_id="activeInference",
            learner_id="local-learner",
        )


def test_describe_local_auth_ready_never_exposes_secret(tmp_path: Path) -> None:
    save_local_state(tmp_path, _state(client_secret="do-not-leak"))
    status = describe_local_auth(
        enabled=True,
        state_dir=tmp_path,
        learner_id="local-learner",
        project_id="activeInference",
    ).to_public_dict()
    text = json.dumps(status)
    assert status["ready"] is True
    assert status["tokenEndpoint"] == LOCAL_TOKEN_ENDPOINT
    assert "do-not-leak" not in text
    assert "admin-password" not in text


def test_describe_local_auth_reports_incomplete_state(tmp_path: Path) -> None:
    save_local_state(tmp_path, _state(client_secret=""))
    status = describe_local_auth(
        enabled=True,
        state_dir=tmp_path,
        learner_id="local-learner",
        project_id="activeInference",
    ).to_public_dict()
    assert status["ready"] is False
    assert "trusted-client secret" in str(status["message"])


def test_new_local_state_uses_documented_default_credentials() -> None:
    state = new_local_state(
        skilltree_url="http://localhost:8080",
        project_id="activeInference",
        learner_id="local-learner",
    )
    assert state.admin_username == DEFAULT_LOCAL_ADMIN_USERNAME
    assert state.admin_password == DEFAULT_LOCAL_ADMIN_PASSWORD
    assert is_browser_login_compatible_username(state.admin_username) is True


def test_refuse_default_password_off_loopback_allows_loopback_targets() -> None:
    for base_url in (
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://[::1]:8080",
    ):
        _refuse_default_password_off_loopback(base_url, DEFAULT_LOCAL_ADMIN_PASSWORD)


def test_refuse_default_password_off_loopback_allows_overridden_password() -> None:
    _refuse_default_password_off_loopback(
        "http://skilltree.example.com", "an-operator-chosen-secret"
    )


def test_refuse_default_password_off_loopback_rejects_default_off_loopback() -> None:
    with pytest.raises(LocalSkillTreeAuthError, match="non-loopback SkillTree target"):
        _refuse_default_password_off_loopback(
            "http://skilltree.example.com", DEFAULT_LOCAL_ADMIN_PASSWORD
        )


def test_browser_login_username_rejects_non_email_state() -> None:
    assert is_browser_login_compatible_username(
        "active-skillference-admin@localhost.invalid"
    )
    assert not is_browser_login_compatible_username("active_skillference_admin")
    assert not is_browser_login_compatible_username("active skillference admin")


def test_new_local_state_accepts_env_credential_overrides(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "ACTIVE_SKILLFERENCE_LOCAL_ADMIN_USERNAME",
        "custom-admin@localhost.invalid",
    )
    monkeypatch.setenv("ACTIVE_SKILLFERENCE_LOCAL_ADMIN_PASSWORD", "custom-password")

    state = new_local_state(
        skilltree_url="http://localhost:8080",
        project_id="activeInference",
        learner_id="local-learner",
    )

    assert state.admin_username == "custom-admin@localhost.invalid"
    assert state.admin_password == "custom-password"


def test_local_request_timeout_accepts_positive_env_override(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ACTIVE_SKILLFERENCE_SKILLTREE_REQUEST_TIMEOUT", "42.5")
    assert default_local_request_timeout() == 42.5


def test_local_request_timeout_rejects_invalid_env_override(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for value in ("0", "-1", "not-a-number"):
        monkeypatch.setenv("ACTIVE_SKILLFERENCE_SKILLTREE_REQUEST_TIMEOUT", value)
        with pytest.raises(LocalSkillTreeAuthError, match="positive number"):
            default_local_request_timeout()


def test_existing_local_state_remains_authoritative(tmp_path: Path) -> None:
    existing = _state(client_secret="existing-secret")
    save_local_state(tmp_path, existing)

    assert load_local_state(tmp_path) == existing


# --------------------------------------------------------------------------- #
# Hardening tests (2026-06-10): error paths, full bootstrap flow, permissions.
# --------------------------------------------------------------------------- #


def test_state_file_is_owner_only_and_dir_private(tmp_path: Path) -> None:
    state_dir = tmp_path / "private"
    save_local_state(state_dir, _state())
    dir_mode = stat.S_IMODE(state_dir.stat().st_mode)
    file_mode = stat.S_IMODE((state_dir / "skilltree_auth.json").stat().st_mode)
    assert dir_mode == 0o700
    assert file_mode == 0o600


def test_save_local_state_fails_closed_when_permissions_cannot_be_restricted(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_chmod(self: Path, mode: int) -> None:
        _ = (self, mode)
        raise OSError("permission change refused")

    monkeypatch.setattr(Path, "chmod", fail_chmod)

    with pytest.raises(LocalSkillTreeAuthError, match="restrict local SkillTree"):
        save_local_state(tmp_path / "private", _state())


def test_from_private_dict_rejects_missing_required_fields() -> None:
    try:
        LocalSkillTreeState.from_private_dict({"adminUsername": "a"})
    except LocalSkillTreeAuthError as exc:
        assert "missing required fields" in str(exc)
        assert "adminPassword" in str(exc)
    else:
        raise AssertionError("missing-field state was accepted")


def test_load_local_state_rejects_invalid_json_and_non_object(tmp_path: Path) -> None:
    path = tmp_path / "skilltree_auth.json"
    path.write_text("{not json", encoding="utf-8")
    try:
        load_local_state(tmp_path)
    except LocalSkillTreeAuthError as exc:
        assert "not valid JSON" in str(exc)
    else:
        raise AssertionError("invalid JSON state was accepted")

    path.write_text("[1, 2, 3]", encoding="utf-8")
    try:
        load_local_state(tmp_path)
    except LocalSkillTreeAuthError as exc:
        assert "JSON object" in str(exc)
    else:
        raise AssertionError("non-object state was accepted")


def test_load_local_state_returns_none_when_absent(tmp_path: Path) -> None:
    assert load_local_state(tmp_path / "nope") is None


def test_describe_local_auth_branches_never_leak_secrets(tmp_path: Path) -> None:
    secret_markers = ("admin-password", "trusted-secret")

    disabled = describe_local_auth(
        enabled=False, state_dir=tmp_path, learner_id="l", project_id="p"
    ).to_public_dict()
    assert disabled["enabled"] is False and disabled["ready"] is False

    absent = describe_local_auth(
        enabled=True, state_dir=tmp_path / "missing", learner_id="l", project_id="p"
    ).to_public_dict()
    assert absent["ready"] is False
    assert "not been bootstrapped" in str(absent["message"])

    corrupt_dir = tmp_path / "corrupt"
    corrupt_dir.mkdir()
    (corrupt_dir / "skilltree_auth.json").write_text("{bad", encoding="utf-8")
    corrupt = describe_local_auth(
        enabled=True, state_dir=corrupt_dir, learner_id="l", project_id="p"
    ).to_public_dict()
    assert corrupt["ready"] is False
    assert "not valid JSON" in str(corrupt["message"])

    mismatch_dir = tmp_path / "mismatch"
    save_local_state(mismatch_dir, _state())
    mismatch = describe_local_auth(
        enabled=True,
        state_dir=mismatch_dir,
        learner_id="l",
        project_id="otherProject",
    ).to_public_dict()
    assert mismatch["ready"] is False
    assert "activeInference" in str(mismatch["message"])

    for payload in (disabled, absent, corrupt, mismatch):
        text = json.dumps(payload)
        for marker in secret_markers:
            assert marker not in text


def test_bootstrap_result_public_dict_never_leaks_secrets() -> None:
    result = BootstrapResult(
        state=_state(),
        created_root=True,
        seeded=True,
        seed_summary={"projects": 1},
        token_verified=True,
    )
    text = json.dumps(result.to_public_dict())
    assert "admin-password" not in text
    assert "trusted-secret" not in text
    assert result.to_public_dict()["tokenEndpoint"] == LOCAL_TOKEN_ENDPOINT


def test_session_client_rejects_empty_base_url_and_project_id() -> None:
    for base_url, project_id in (("", "p"), ("http://x", " ")):
        try:
            SkillTreeSessionClient(base_url, project_id)
        except ValueError:
            continue
        raise AssertionError(
            f"accepted base_url={base_url!r} project_id={project_id!r}"
        )


def test_request_raw_rejects_json_and_form_together() -> None:
    client = SkillTreeSessionClient("http://skilltree.local", "p")
    try:
        client.request_raw("POST", "/x", json_body={}, form_body={})
    except ValueError as exc:
        assert "mutually exclusive" in str(exc)
    else:
        raise AssertionError("json_body+form_body accepted together")


def test_xsrf_token_empty_without_cookie() -> None:
    client = SkillTreeSessionClient("http://skilltree.local", "p")
    assert client.xsrf_token == ""


def test_prime_session_falls_back_to_public_config(httpserver: HTTPServer) -> None:
    httpserver.expect_request("/", method="GET").respond_with_data("boom", status=500)
    httpserver.expect_request("/public/config", method="GET").respond_with_json({})
    client = SkillTreeSessionClient(httpserver.url_for("").rstrip("/"), "p")
    client.prime_session()


def test_public_config_rejects_non_object_json(httpserver: HTTPServer) -> None:
    httpserver.expect_request("/public/config", method="GET").respond_with_json([1])
    client = SkillTreeSessionClient(httpserver.url_for("").rstrip("/"), "p")
    try:
        client.public_config()
    except LocalSkillTreeAuthError as exc:
        assert "non-object JSON" in str(exc)
    else:
        raise AssertionError("non-object /public/config accepted")


def test_get_and_reset_project_client_secret_variants(httpserver: HTTPServer) -> None:
    httpserver.expect_ordered_request(
        "/admin/projects/p/clientSecret", method="GET"
    ).respond_with_data('"quoted-secret"', content_type="application/json")
    client = SkillTreeSessionClient(httpserver.url_for("").rstrip("/"), "p")
    assert client.get_project_client_secret() == "quoted-secret"

    httpserver.expect_ordered_request(
        "/admin/projects/p/resetClientSecret", method="POST"
    ).respond_with_json({"data": {"clientSecret": "nested-secret"}})
    assert client.reset_project_client_secret() == "nested-secret"

    httpserver.expect_ordered_request(
        "/admin/projects/p/resetClientSecret", method="POST"
    ).respond_with_json({"clientSecret": "flat-secret"})
    assert client.reset_project_client_secret() == "flat-secret"

    # Empty reset payload falls back to a GET of the current secret.
    httpserver.expect_ordered_request(
        "/admin/projects/p/resetClientSecret", method="POST"
    ).respond_with_json({})
    httpserver.expect_ordered_request(
        "/admin/projects/p/clientSecret", method="GET"
    ).respond_with_data("fallback-secret", content_type="text/plain")
    assert client.reset_project_client_secret() == "fallback-secret"


def test_request_json_allowing_existing_reraises_non_duplicate(
    httpserver: HTTPServer,
) -> None:
    httpserver.expect_request("/admin/projects/p", method="POST").respond_with_json(
        {"explanation": "validation failed", "success": False}, status=400
    )
    client = SkillTreeSessionClient(httpserver.url_for("").rstrip("/"), "p")
    try:
        client.request_json_allowing_existing(
            "POST", "/admin/projects/p", json_body={"projectId": "p"}
        )
    except SkillTreeClientError as exc:
        assert exc.status == 400
    else:
        raise AssertionError("non-duplicate 400 treated as idempotent")


def test_admin_create_methods_hit_expected_paths(httpserver: HTTPServer) -> None:
    base = httpserver.url_for("").rstrip("/")
    client = SkillTreeSessionClient(base, "activeInference")
    subject = SkillTreeSubject(subject_id="sub_math", name="Math")
    skill = SkillTreeSkill(
        skill_id="m_sets",
        name="Sets",
        point_increment=100,
        num_perform_to_completion=1,
        description="Sets",
    )
    dep = SkillDependency(skill_id="m_vectors", depends_on_skill_id="m_sets")
    quiz = Quiz(quiz_id="m_sets_quiz", name="Sets Quiz")

    httpserver.expect_request(
        "/admin/projects/activeInference", method="POST"
    ).respond_with_json({})
    httpserver.expect_request(
        "/admin/projects/activeInference/subjects/sub_math", method="POST"
    ).respond_with_json({})
    httpserver.expect_request(
        "/admin/projects/activeInference/subjects/sub_math/skills/m_sets",
        method="POST",
    ).respond_with_json({})
    httpserver.expect_request(
        "/admin/projects/activeInference/m_vectors/prerequisite/activeInference/m_sets",
        method="POST",
    ).respond_with_json({})
    httpserver.expect_request(
        "/admin/projects/activeInference/dependency/graph", method="GET"
    ).respond_with_json({"nodes": [], "edges": []})
    httpserver.expect_request(
        "/admin/quiz-definitions/m_sets_quiz", method="POST"
    ).respond_with_json({})

    client.create_project("Active Inference")
    client.create_subject(subject)
    client.create_skill("sub_math", skill)
    client.assign_dependency(dep)
    client.create_quiz(quiz)
    httpserver.check_assertions()


def test_admin_create_quiz_adds_missing_questions(httpserver: HTTPServer) -> None:
    base = httpserver.url_for("").rstrip("/")
    client = SkillTreeSessionClient(base, "activeInference")
    quiz = Quiz(
        quiz_id="m_sets_quiz",
        name="Sets Quiz",
        questions=[
            QuizQuestion(question="q?", answers=[{"answer": "a", "isCorrect": True}])
        ],
    )
    httpserver.expect_request(
        "/admin/quiz-definitions/m_sets_quiz", method="POST"
    ).respond_with_json({})
    httpserver.expect_request(
        "/admin/quiz-definitions/m_sets_quiz/questions", method="GET"
    ).respond_with_json({"quizType": "Quiz", "questions": []})
    httpserver.expect_request(
        "/admin/quiz-definitions/m_sets_quiz/create-question",
        method="POST",
        json={
            "question": "q?",
            "answerHint": "",
            "questionType": "SingleChoice",
            "questionScale": 5,
            "answers": [{"answer": "a", "isCorrect": True}],
        },
    ).respond_with_json({"id": 1})

    client.create_quiz(quiz)
    httpserver.check_assertions()


def test_admin_create_quiz_appends_missing_question_suffix(
    httpserver: HTTPServer,
) -> None:
    base = httpserver.url_for("").rstrip("/")
    client = SkillTreeSessionClient(base, "activeInference")
    quiz = Quiz(
        quiz_id="m_sets_quiz",
        name="Sets Quiz",
        questions=[
            QuizQuestion(question="q1?", answers=[{"answer": "a", "isCorrect": True}]),
            QuizQuestion(question="q2?", answers=[{"answer": "b", "isCorrect": True}]),
        ],
    )
    httpserver.expect_request(
        "/admin/quiz-definitions/m_sets_quiz", method="POST"
    ).respond_with_json({})
    httpserver.expect_request(
        "/admin/quiz-definitions/m_sets_quiz/questions", method="GET"
    ).respond_with_json({"quizType": "Quiz", "questions": [{"id": 1}]})
    httpserver.expect_request(
        "/admin/quiz-definitions/m_sets_quiz/create-question",
        method="POST",
        json={
            "question": "q2?",
            "answerHint": "",
            "questionType": "SingleChoice",
            "questionScale": 5,
            "answers": [{"answer": "b", "isCorrect": True}],
        },
    ).respond_with_json({"id": 2})

    client.create_quiz(quiz)
    httpserver.check_assertions()


def _bootstrap_httpserver_expectations(
    httpserver: HTTPServer, *, needs_bootstrap: bool
) -> None:
    httpserver.expect_request("/public/config", method="GET").respond_with_json(
        {"needToBootstrap": needs_bootstrap}
    )
    httpserver.expect_request("/", method="GET").respond_with_data(
        "<html></html>",
        headers={"Set-Cookie": "XSRF-TOKEN=csrf-token; Path=/"},
        content_type="text/html",
    )
    httpserver.expect_request("/createRootAccount", method="PUT").respond_with_json({})
    httpserver.expect_request("/performLogin", method="POST").respond_with_json({})
    httpserver.expect_request(
        "/admin/projects/activeInference", method="POST"
    ).respond_with_json({})
    httpserver.expect_request(
        "/admin/projects/activeInference/subjects/sub_math", method="POST"
    ).respond_with_json({})
    httpserver.expect_request(
        "/admin/projects/activeInference/subjects/sub_math/skills/m_sets",
        method="POST",
    ).respond_with_json({})
    httpserver.expect_request(
        "/admin/quiz-definitions/m_sets_quiz", method="POST"
    ).respond_with_json({})
    # Post-seed verification (verify_seed_landed) reads the live skill count; the
    # tiny project defines exactly 1 skill, so report 1 to confirm the seed landed.
    httpserver.expect_request(
        "/admin/projects/activeInference", method="GET"
    ).respond_with_json({"numSkills": 1, "numSubjects": 1})
    httpserver.expect_request(
        "/admin/projects/activeInference/clientSecret", method="GET"
    ).respond_with_data("bootstrap-secret", content_type="text/plain")
    httpserver.expect_request("/oauth/token", method="POST").respond_with_json(
        {"access_token": "learner-token", "token_type": "Bearer"}
    )


def _tiny_project() -> SkillTreeProject:
    return SkillTreeProject(
        project_id="activeInference",
        name="Active Inference",
        subjects=[
            SkillTreeSubject(
                subject_id="sub_math",
                name="Math",
                skills=[
                    SkillTreeSkill(
                        skill_id="m_sets",
                        name="Sets",
                        point_increment=100,
                        num_perform_to_completion=1,
                        description="Sets",
                        self_reporting_type="Quiz",
                        quiz_id="m_sets_quiz",
                    )
                ],
            )
        ],
        dependencies=[],
        quizzes=[Quiz(quiz_id="m_sets_quiz", name="Sets Quiz")],
    )


def test_ensure_local_skilltree_auth_full_first_bootstrap(
    tmp_path: Path, httpserver: HTTPServer
) -> None:
    _bootstrap_httpserver_expectations(httpserver, needs_bootstrap=True)
    base = httpserver.url_for("").rstrip("/")

    result = ensure_local_skilltree_auth(
        base_url=base,
        project_id="activeInference",
        state_dir=tmp_path,
        project=_tiny_project(),
    )

    assert result.created_root is True
    assert result.seeded is True
    assert result.seed_summary == {
        "projects": 1,
        "subjects": 1,
        "skills": 1,
        "dependencies": 0,
        "quizzes": 1,
    }
    assert result.token_verified is True
    stored = load_local_state(tmp_path)
    assert stored is not None
    assert stored.client_secret == "bootstrap-secret"
    assert stored.skilltree_url == base


def test_ensure_local_skilltree_auth_reuses_existing_state(
    tmp_path: Path, httpserver: HTTPServer
) -> None:
    base = httpserver.url_for("").rstrip("/")
    save_local_state(
        tmp_path,
        LocalSkillTreeState(
            admin_username="active_skillference_admin",
            admin_password="admin-password",
            learner_id="local-learner",
            project_id="activeInference",
            skilltree_url=base,
        ),
    )
    httpserver.expect_request("/public/config", method="GET").respond_with_json(
        {"needToBootstrap": False}
    )
    httpserver.expect_request("/", method="GET").respond_with_data(
        "<html></html>",
        headers={"Set-Cookie": "XSRF-TOKEN=csrf-token; Path=/"},
        content_type="text/html",
    )
    httpserver.expect_request("/performLogin", method="POST").respond_with_json({})
    httpserver.expect_request(
        "/admin/projects/activeInference/clientSecret", method="GET"
    ).respond_with_data("kept-secret", content_type="text/plain")

    result = ensure_local_skilltree_auth(
        base_url=base,
        project_id="activeInference",
        state_dir=tmp_path,
        seed_project=False,
        verify_token=False,
    )

    assert result.created_root is False
    assert result.seeded is False
    assert result.token_verified is False
    stored = load_local_state(tmp_path)
    assert stored is not None and stored.client_secret == "kept-secret"


def test_ensure_local_skilltree_auth_rejects_state_url_mismatch_before_login(
    tmp_path: Path,
    httpserver: HTTPServer,
) -> None:
    save_local_state(
        tmp_path,
        LocalSkillTreeState(
            admin_username="active-skillference-admin@localhost.invalid",
            admin_password="stored-admin-secret",
            learner_id="local-learner",
            project_id="activeInference",
            skilltree_url="http://original.local:8080",
            client_secret="trusted-secret",
        ),
    )
    httpserver.expect_request("/public/config", method="GET").respond_with_json(
        {"needToBootstrap": False}
    )

    with pytest.raises(LocalSkillTreeAuthError, match="does not match"):
        ensure_local_skilltree_auth(
            base_url=httpserver.url_for("").rstrip("/"),
            project_id="activeInference",
            state_dir=tmp_path,
            seed_project=False,
            verify_token=False,
        )

    httpserver.check_assertions()


def test_ensure_local_skilltree_auth_skips_seed_when_live_counts_ready(
    tmp_path: Path, httpserver: HTTPServer
) -> None:
    base = httpserver.url_for("").rstrip("/")
    save_local_state(
        tmp_path,
        LocalSkillTreeState(
            admin_username="active-skillference-admin@localhost.invalid",
            admin_password="active-skillference-local",
            learner_id=DEFAULT_LOCAL_LEARNER_ID,
            project_id="activeInference",
            skilltree_url=base,
            client_secret="trusted-secret",
        ),
    )
    httpserver.expect_request("/public/config", method="GET").respond_with_json(
        {"needToBootstrap": False}
    )
    httpserver.expect_request("/", method="GET").respond_with_data(
        "<html></html>",
        headers={"Set-Cookie": "XSRF-TOKEN=csrf-token; Path=/"},
        content_type="text/html",
    )
    httpserver.expect_request("/performLogin", method="POST").respond_with_json({})
    httpserver.expect_request(
        "/admin/projects/activeInference", method="GET"
    ).respond_with_json({"numSkills": 1, "numSubjects": 1})
    httpserver.expect_request(
        "/admin/projects/activeInference/clientSecret", method="GET"
    ).respond_with_data("trusted-secret", content_type="text/plain")

    result = ensure_local_skilltree_auth(
        base_url=base,
        project_id="activeInference",
        state_dir=tmp_path,
        project=_tiny_project(),
        seed_project=True,
        skip_seed_if_live_counts_ready=True,
        verify_token=False,
    )

    assert result.created_root is False
    assert result.seeded is False
    assert result.seed_summary is None


def test_ensure_local_skilltree_auth_refuses_root_without_local_state(
    tmp_path: Path, httpserver: HTTPServer
) -> None:
    httpserver.expect_request("/public/config", method="GET").respond_with_json(
        {"needToBootstrap": False}
    )
    try:
        ensure_local_skilltree_auth(
            base_url=httpserver.url_for("").rstrip("/"),
            project_id="activeInference",
            state_dir=tmp_path,
        )
    except LocalSkillTreeAuthError as exc:
        assert "no local credentials exist" in str(exc)
    else:
        raise AssertionError("bootstrap proceeded without credentials")


def test_fetch_local_skilltree_token_error_paths(tmp_path: Path) -> None:
    try:
        fetch_local_skilltree_token(
            base_url="http://skilltree.local",
            state_dir=tmp_path / "missing",
            project_id="p",
            learner_id="l",
        )
    except LocalSkillTreeAuthError as exc:
        assert "not been bootstrapped" in str(exc)
    else:
        raise AssertionError("missing state accepted")

    save_local_state(tmp_path, _state())
    try:
        fetch_local_skilltree_token(
            base_url="http://skilltree.local",
            state_dir=tmp_path,
            project_id="otherProject",
            learner_id="l",
        )
    except LocalSkillTreeAuthError as exc:
        assert "otherProject" in str(exc)
    else:
        raise AssertionError("project mismatch accepted")

    save_local_state(tmp_path, _state(client_secret=""))
    try:
        fetch_local_skilltree_token(
            base_url="http://skilltree.local",
            state_dir=tmp_path,
            project_id="activeInference",
            learner_id="l",
        )
    except LocalSkillTreeAuthError as exc:
        assert "secret is missing" in str(exc)
    else:
        raise AssertionError("missing secret accepted")


def test_exchange_trusted_client_token_error_paths(httpserver: HTTPServer) -> None:
    try:
        exchange_trusted_client_token(
            base_url="http://skilltree.local",
            project_id="p",
            client_secret="  ",
            learner_id="l",
        )
    except LocalSkillTreeAuthError as exc:
        assert "non-empty" in str(exc)
    else:
        raise AssertionError("empty secret accepted")

    httpserver.expect_ordered_request("/oauth/token", method="POST").respond_with_json(
        {"error": "invalid_client"}, status=401
    )
    base = httpserver.url_for("").rstrip("/")
    try:
        exchange_trusted_client_token(
            base_url=base, project_id="p", client_secret="s", learner_id="l"
        )
    except SkillTreeClientError as exc:
        assert exc.status == 401
    else:
        raise AssertionError("401 token exchange did not raise")

    httpserver.expect_ordered_request("/oauth/token", method="POST").respond_with_json(
        [1, 2]
    )
    try:
        exchange_trusted_client_token(
            base_url=base, project_id="p", client_secret="s", learner_id="l"
        )
    except LocalSkillTreeAuthError as exc:
        assert "non-object JSON" in str(exc)
    else:
        raise AssertionError("non-object token payload accepted")

    httpserver.expect_ordered_request("/oauth/token", method="POST").respond_with_data(
        "",
        status=302,
        headers={"Location": "http://example.invalid/oauth/token"},
    )
    try:
        exchange_trusted_client_token(
            base_url=base, project_id="p", client_secret="s", learner_id="l"
        )
    except SkillTreeClientError as exc:
        assert exc.status == 302
    else:
        raise AssertionError("redirecting token endpoint did not fail closed")


def test_parse_secret_response_variants() -> None:
    assert _parse_secret_response("") == ""
    assert _parse_secret_response("plain-secret") == "plain-secret"
    assert _parse_secret_response('"json-string-secret"') == "json-string-secret"
    assert _parse_secret_response('{"data": {"clientSecret": "nested"}}') == "nested"
    assert _parse_secret_response('{"clientSecret": "flat"}') == "flat"
    # Plain text/plain secret (JSON parse fails) is the documented success shape.
    assert _parse_secret_response("not json {") == "not json {"
    # Negative control (convergence #4): a structured JSON response that carries NO
    # clientSecret must NOT be laundered into a "secret" — it has none, so return "".
    assert _parse_secret_response('{"unrelated": true}') == ""
    assert _parse_secret_response("[1, 2, 3]") == ""


def test_is_existing_resource_error_matrix() -> None:
    dup = SkillTreeClientError("x", status=400, body="Learning path already exists")
    other_400 = SkillTreeClientError("x", status=400, body="validation failed")
    server_err = SkillTreeClientError("x", status=500, body="already exists")
    empty_body = SkillTreeClientError("x", status=409, body="")
    conflict = SkillTreeClientError("x", status=409, body="Duplicate skillId")
    assert _is_existing_resource_error(dup) is True
    assert _is_existing_resource_error(other_400) is False
    assert _is_existing_resource_error(server_err) is False
    assert _is_existing_resource_error(empty_body) is False
    assert _is_existing_resource_error(conflict) is True


def test_ensure_local_skilltree_auth_falls_back_to_reset_secret(
    tmp_path: Path, httpserver: HTTPServer
) -> None:
    base = httpserver.url_for("").rstrip("/")
    save_local_state(
        tmp_path,
        LocalSkillTreeState(
            admin_username="active_skillference_admin",
            admin_password="admin-password",
            learner_id="local-learner",
            project_id="activeInference",
            skilltree_url=base,
        ),
    )
    httpserver.expect_request("/public/config", method="GET").respond_with_json(
        {"needToBootstrap": False}
    )
    httpserver.expect_request("/", method="GET").respond_with_data(
        "<html></html>",
        headers={"Set-Cookie": "XSRF-TOKEN=csrf-token; Path=/"},
        content_type="text/html",
    )
    httpserver.expect_request("/performLogin", method="POST").respond_with_json({})
    httpserver.expect_request(
        "/admin/projects/activeInference/clientSecret", method="GET"
    ).respond_with_data("", content_type="text/plain")
    httpserver.expect_request(
        "/admin/projects/activeInference/resetClientSecret", method="POST"
    ).respond_with_json({"clientSecret": "reset-secret"})

    result = ensure_local_skilltree_auth(
        base_url=base,
        project_id="activeInference",
        state_dir=tmp_path,
        seed_project=False,
        verify_token=False,
    )
    assert result.state.client_secret == "reset-secret"


def test_ensure_local_skilltree_auth_does_not_store_unverified_secret(
    tmp_path: Path, httpserver: HTTPServer
) -> None:
    base = httpserver.url_for("").rstrip("/")
    save_local_state(
        tmp_path,
        LocalSkillTreeState(
            admin_username="active_skillference_admin",
            admin_password="admin-password",
            learner_id="local-learner",
            project_id="activeInference",
            skilltree_url=base,
        ),
    )
    httpserver.expect_request("/public/config", method="GET").respond_with_json(
        {"needToBootstrap": False}
    )
    httpserver.expect_request("/", method="GET").respond_with_data(
        "<html></html>",
        headers={"Set-Cookie": "XSRF-TOKEN=csrf-token; Path=/"},
        content_type="text/html",
    )
    httpserver.expect_request("/performLogin", method="POST").respond_with_json({})
    httpserver.expect_request(
        "/admin/projects/activeInference/clientSecret", method="GET"
    ).respond_with_data("unverified-secret", content_type="text/plain")
    httpserver.expect_request("/oauth/token", method="POST").respond_with_json(
        {"token_type": "bearer"}
    )

    with pytest.raises(LocalSkillTreeAuthError, match="no access_token"):
        ensure_local_skilltree_auth(
            base_url=base,
            project_id="activeInference",
            state_dir=tmp_path,
            seed_project=False,
            verify_token=True,
        )

    stored = load_local_state(tmp_path)
    assert stored is not None
    assert stored.client_secret == ""


def test_ensure_local_skilltree_auth_raises_when_no_secret_obtainable(
    tmp_path: Path, httpserver: HTTPServer
) -> None:
    base = httpserver.url_for("").rstrip("/")
    save_local_state(
        tmp_path,
        LocalSkillTreeState(
            admin_username="active_skillference_admin",
            admin_password="admin-password",
            learner_id="local-learner",
            project_id="activeInference",
            skilltree_url=base,
        ),
    )
    httpserver.expect_request("/public/config", method="GET").respond_with_json(
        {"needToBootstrap": False}
    )
    httpserver.expect_request("/", method="GET").respond_with_data(
        "<html></html>", content_type="text/html"
    )
    httpserver.expect_request("/performLogin", method="POST").respond_with_json({})
    httpserver.expect_request(
        "/admin/projects/activeInference/clientSecret", method="GET"
    ).respond_with_data("", content_type="text/plain")
    httpserver.expect_request(
        "/admin/projects/activeInference/resetClientSecret", method="POST"
    ).respond_with_json({})

    try:
        ensure_local_skilltree_auth(
            base_url=base,
            project_id="activeInference",
            state_dir=tmp_path,
            seed_project=False,
            verify_token=False,
        )
    except LocalSkillTreeAuthError as exc:
        assert "did not return a trusted-client secret" in str(exc)
    else:
        raise AssertionError("missing secret did not raise")


def _two_skill_project() -> SkillTreeProject:
    return SkillTreeProject(
        project_id="p",
        name="Project",
        subjects=[
            SkillTreeSubject(
                subject_id="sub",
                name="Subject",
                skills=[
                    SkillTreeSkill(skill_id="a", name="Skill A"),
                    SkillTreeSkill(skill_id="b", name="Skill B"),
                ],
            )
        ],
    )


def test_live_skill_count_reads_num_skills_flat_and_wrapped(
    httpserver: HTTPServer,
) -> None:
    httpserver.expect_ordered_request(
        "/admin/projects/p", method="GET"
    ).respond_with_json({"numSkills": 208})
    httpserver.expect_ordered_request(
        "/admin/projects/p", method="GET"
    ).respond_with_json({"data": {"numSkills": 32}})
    client = SkillTreeSessionClient(httpserver.url_for("/"), "p")
    assert client.live_skill_count() == 208  # flat shape
    assert client.live_skill_count() == 32  # {"data": {...}} shape


def test_live_skill_count_rejects_missing_num_skills(httpserver: HTTPServer) -> None:
    httpserver.expect_request("/admin/projects/p", method="GET").respond_with_json(
        {"name": "Project"}
    )
    client = SkillTreeSessionClient(httpserver.url_for("/"), "p")
    try:
        client.live_skill_count()
    except LocalSkillTreeAuthError as exc:
        assert "numSkills" in str(exc)
    else:
        raise AssertionError("missing numSkills did not raise")


def test_verify_seed_landed_passes_when_live_matches(httpserver: HTTPServer) -> None:
    httpserver.expect_request("/admin/projects/p", method="GET").respond_with_json(
        {"numSkills": 2, "numSubjects": 1}
    )
    client = SkillTreeSessionClient(httpserver.url_for("/"), "p")
    # Exactly-equal live count must not raise.
    verify_seed_landed(client, _two_skill_project())


def test_verify_seed_landed_raises_on_silent_shortfall(httpserver: HTTPServer) -> None:
    # The export defines 2 skills but the server only has 1 — exactly the
    # swallowed-creation corruption (e.g. a duplicate-name skill never created).
    httpserver.expect_request("/admin/projects/p", method="GET").respond_with_json(
        {"numSkills": 1, "numSubjects": 1}
    )
    client = SkillTreeSessionClient(httpserver.url_for("/"), "p")
    try:
        verify_seed_landed(client, _two_skill_project())
    except LocalSkillTreeAuthError as exc:
        message = str(exc)
        assert "seed verification failed" in message
        assert "silently dropped" in message
    else:
        raise AssertionError("silent seed shortfall did not raise")


def test_verify_seed_landed_raises_on_subject_shortfall(httpserver: HTTPServer) -> None:
    """Negative control (convergence #2): a dropped SUBJECT (skills still summed into the
    skill count) must now be caught — the prior skill-only check was vacuous for it."""
    httpserver.expect_request("/admin/projects/p", method="GET").respond_with_json(
        {"numSkills": 2, "numSubjects": 0}
    )
    client = SkillTreeSessionClient(httpserver.url_for("/"), "p")
    with pytest.raises(LocalSkillTreeAuthError, match="subjects vs"):
        verify_seed_landed(client, _two_skill_project())


def test_exchange_token_fails_closed_on_empty_response(httpserver: HTTPServer) -> None:
    """Negative control (convergence #1 HIGH security): an HTTP 200 with an empty body is
    NOT a successful exchange — it must raise, not silently return {} (which let the caller
    set token_verified=True with no token)."""
    httpserver.expect_request("/oauth/token", method="POST").respond_with_data(
        "", status=200
    )
    with pytest.raises(LocalSkillTreeAuthError, match="empty response"):
        exchange_trusted_client_token(
            base_url=httpserver.url_for("").rstrip("/"),
            project_id="activeInference",
            client_secret="secret",
            learner_id="local-learner",
        )


def test_exchange_token_fails_closed_without_access_token(
    httpserver: HTTPServer,
) -> None:
    """Negative control (#1): a 200 JSON body lacking access_token must fail closed."""
    httpserver.expect_request("/oauth/token", method="POST").respond_with_json(
        {"token_type": "bearer"}
    )
    with pytest.raises(LocalSkillTreeAuthError, match="no access_token"):
        exchange_trusted_client_token(
            base_url=httpserver.url_for("").rstrip("/"),
            project_id="activeInference",
            client_secret="secret",
            learner_id="local-learner",
        )


def test_exchange_token_returns_payload_with_access_token(
    httpserver: HTTPServer,
) -> None:
    """Positive control: a well-formed token response resolves."""
    httpserver.expect_request("/oauth/token", method="POST").respond_with_json(
        {"access_token": "abc123", "token_type": "bearer"}
    )
    out = exchange_trusted_client_token(
        base_url=httpserver.url_for("").rstrip("/"),
        project_id="activeInference",
        client_secret="secret",
        learner_id="local-learner",
    )
    assert out["access_token"] == "abc123"
