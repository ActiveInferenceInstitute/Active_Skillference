"""Malformed JSON and real socket stalls stay inside the SkillTree error contract."""

from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor

import pytest
from pytest_httpserver import HTTPServer
from werkzeug.wrappers import Response

from src.skilltree.client import SkillTreeClient, SkillTreeClientError
from src.skilltree.local_auth import (
    LocalSkillTreeAuthError,
    SkillTreeSessionClient,
    exchange_trusted_client_token,
)


@pytest.mark.parametrize("method", ["GET", "POST"])
def test_bearer_read_timeout_is_bounded_and_domain_typed(
    httpserver: HTTPServer, method: str
) -> None:
    release = threading.Event()

    def stalled_body():
        yield b"{"
        release.wait()
        yield b"}"

    httpserver.expect_request("/slow", method=method).respond_with_handler(
        lambda request: Response(stalled_body(), content_type="application/json")
    )
    client = SkillTreeClient(
        httpserver.url_for(""), "p", token="private-token", timeout=0.05
    )
    operation = client._get if method == "GET" else client._post
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(operation, "/slow")
        try:
            with pytest.raises(SkillTreeClientError, match="timed out") as error:
                future.result(timeout=5)
            assert "private-token" not in str(error.value)
        finally:
            release.set()


@pytest.mark.parametrize("timeout", [0.0, -1.0, float("inf"), float("nan")])
def test_bearer_timeout_must_be_finite_and_positive(timeout: float) -> None:
    with pytest.raises(ValueError, match="finite and positive"):
        SkillTreeClient("http://127.0.0.1:1", "p", timeout=timeout)


def test_session_malformed_json_is_domain_typed_and_secret_safe(
    httpserver: HTTPServer,
) -> None:
    httpserver.expect_request("/broken", method="GET").respond_with_data(
        '{"secret": "private-response-fragment"',
        content_type="application/json",
    )
    client = SkillTreeSessionClient(httpserver.url_for(""), "p")
    with pytest.raises(SkillTreeClientError, match="malformed JSON") as error:
        client.request_json("GET", "/broken")
    assert "private-response-fragment" not in str(error.value)


def test_token_malformed_json_is_auth_domain_error(httpserver: HTTPServer) -> None:
    httpserver.expect_request("/oauth/token", method="POST").respond_with_data(
        '{"access_token": "private-fragment"',
        content_type="application/json",
    )
    with pytest.raises(LocalSkillTreeAuthError, match="malformed JSON") as error:
        exchange_trusted_client_token(
            base_url=httpserver.url_for(""),
            project_id="p",
            client_secret="private-secret",
            learner_id="learner",
        )
    assert "private-fragment" not in str(error.value)
    assert "private-secret" not in str(error.value)


def test_token_socket_timeout_is_domain_typed(httpserver: HTTPServer) -> None:
    release = threading.Event()

    def stalled_body():
        yield b"{"
        release.wait()
        yield b"}"

    httpserver.expect_request("/oauth/token", method="POST").respond_with_handler(
        lambda request: Response(stalled_body(), content_type="application/json")
    )
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(
            exchange_trusted_client_token,
            base_url=httpserver.url_for(""),
            project_id="p",
            client_secret="synthetic-secret",
            learner_id="learner",
            timeout=0.05,
        )
        try:
            with pytest.raises(SkillTreeClientError, match="timed out"):
                future.result(timeout=5)
        finally:
            release.set()
