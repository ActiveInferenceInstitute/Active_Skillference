"""Hardening tests for the dashboard HTTP server (POST/OPTIONS, error paths).

Complements tests/test_dashboard.py: that file covers the happy-path GET routes
and the token success path; this one covers the remaining handler branches —
POST/OPTIONS routing, token-endpoint failure modes, media types, build_server,
and a real SIGINT shutdown of run_dashboard_server in a subprocess.
"""

from __future__ import annotations

import gzip
import json
import signal
import socket
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

from pytest_httpserver import HTTPServer

from src.dashboard.config import DashboardConfig, make_dashboard_config
from src.dashboard.server import (
    ARTIFACT_HTML_CSP,
    BASE_SECURITY_HEADERS,
    build_server,
    make_dashboard_handler,
)
from src.dashboard.status import check_skilltree_status
from src.skilltree.local_auth import LocalSkillTreeState, save_local_state

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _write_local_auth_state(
    path: Path,
    client_secret: str = "trusted-secret",
    skilltree_url: str = "http://localhost:8080",
) -> None:
    save_local_state(
        path,
        LocalSkillTreeState(
            admin_username="active_skillference_admin",
            admin_password="admin-password",
            learner_id="local-learner",
            project_id="activeInference",
            skilltree_url=skilltree_url,
            client_secret=client_secret,
        ),
    )


class _DashboardServer:
    def __init__(self, config: DashboardConfig) -> None:
        self.server = ThreadingHTTPServer(
            ("127.0.0.1", 0), make_dashboard_handler(config)
        )
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    def __enter__(self) -> str:
        self.thread.start()
        port = self.server.server_address[1]
        return f"http://127.0.0.1:{port}"

    def __exit__(self, *args: object) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)


def _request(
    url: str,
    *,
    method: str = "GET",
    origin: str | None = None,
    headers: dict[str, str] | None = None,
) -> tuple[int, dict[str, str], bytes]:
    request_headers = dict(headers or {})
    if origin:
        request_headers["Origin"] = origin
    request = urllib.request.Request(url, method=method, headers=request_headers)
    with urllib.request.urlopen(request, timeout=2) as response:
        return response.status, dict(response.headers.items()), response.read()


def test_post_token_endpoint_returns_token(
    tmp_path: Path, httpserver: HTTPServer
) -> None:
    state_dir = tmp_path / "state"
    skilltree_url = httpserver.url_for("").rstrip("/")
    _write_local_auth_state(state_dir, skilltree_url=skilltree_url)
    httpserver.expect_request("/oauth/token", method="POST").respond_with_json(
        {"access_token": "post-token", "token_type": "Bearer"}
    )
    config = make_dashboard_config(
        project_root=tmp_path,
        skilltree_url=skilltree_url,
        local_auth_enabled=True,
        local_state_dir=state_dir,
    )
    with _DashboardServer(config) as base_url:
        status, _, body = _request(
            f"{base_url}/api/skilltree/token",
            method="POST",
            origin=config.dashboard_url,
        )
    assert status == 200
    assert json.loads(body.decode("utf-8"))["access_token"] == "post-token"


def test_post_and_options_unknown_routes_return_404(tmp_path: Path) -> None:
    config = make_dashboard_config(
        project_root=tmp_path, skilltree_url="http://127.0.0.1:9"
    )
    with _DashboardServer(config) as base_url:
        for method in ("POST", "OPTIONS"):
            try:
                _request(f"{base_url}/api/other", method=method)
            except urllib.error.HTTPError as exc:
                assert exc.code == 404
            else:
                raise AssertionError(f"{method} /api/other unexpectedly succeeded")


def test_recommendations_route_fails_closed_without_export(tmp_path: Path) -> None:
    config = make_dashboard_config(
        project_root=tmp_path, skilltree_url="http://127.0.0.1:9"
    )
    with _DashboardServer(config) as base_url:
        status, headers, body = _request(f"{base_url}/api/recommendations")

    payload = json.loads(body.decode("utf-8"))
    assert status == 200
    assert headers["Content-Type"].startswith("application/json")
    assert payload["available"] is False
    assert payload["recommendations"] == []


def test_token_endpoint_maps_auth_error_to_503(
    tmp_path: Path, httpserver: HTTPServer
) -> None:
    # State is ready, but the token endpoint returns non-object JSON, which
    # surfaces as LocalSkillTreeAuthError inside the exchange.
    state_dir = tmp_path / "state"
    skilltree_url = httpserver.url_for("").rstrip("/")
    _write_local_auth_state(state_dir, skilltree_url=skilltree_url)
    httpserver.expect_request("/oauth/token", method="POST").respond_with_json([1, 2])
    config = make_dashboard_config(
        project_root=tmp_path,
        skilltree_url=skilltree_url,
        local_auth_enabled=True,
        local_state_dir=state_dir,
    )
    with _DashboardServer(config) as base_url:
        try:
            _request(f"{base_url}/api/skilltree/token")
        except urllib.error.HTTPError as exc:
            body = json.loads(exc.read().decode("utf-8"))
            assert exc.code == 503
            assert body["error"] == "local SkillTree auth failed"
        else:
            raise AssertionError("non-object token payload did not 503")


def test_token_endpoint_maps_skilltree_failure_to_502(
    tmp_path: Path, httpserver: HTTPServer
) -> None:
    state_dir = tmp_path / "state"
    skilltree_url = httpserver.url_for("").rstrip("/")
    _write_local_auth_state(state_dir, skilltree_url=skilltree_url)
    httpserver.expect_request("/oauth/token", method="POST").respond_with_json(
        {"error": "server exploded"}, status=500
    )
    config = make_dashboard_config(
        project_root=tmp_path,
        skilltree_url=skilltree_url,
        local_auth_enabled=True,
        local_state_dir=state_dir,
    )
    with _DashboardServer(config) as base_url:
        try:
            _request(f"{base_url}/api/skilltree/token")
        except urllib.error.HTTPError as exc:
            body = json.loads(exc.read().decode("utf-8"))
            assert exc.code == 502
            assert body["error"] == "SkillTree token exchange failed"
            assert body["status"] == 500
        else:
            raise AssertionError("SkillTree 500 did not 502")


def test_cors_foreign_origin_gets_no_allow_header(tmp_path: Path) -> None:
    config = make_dashboard_config(
        project_root=tmp_path, skilltree_url="http://127.0.0.1:9"
    )
    with _DashboardServer(config) as base_url:
        status, headers, _ = _request(
            f"{base_url}/healthz", origin="http://evil.example"
        )
    assert status == 200
    assert "Access-Control-Allow-Origin" not in headers


def test_guess_media_type_matrix(tmp_path: Path) -> None:
    handler = make_dashboard_handler(make_dashboard_config(project_root=tmp_path))
    cases = {
        "index.html": "text/html; charset=utf-8",
        "styles.css": "text/css; charset=utf-8",
        "app.js": "application/javascript; charset=utf-8",
        "data.json": "application/json; charset=utf-8",
        "figure.png": "image/png",
        "paper.pdf": "application/pdf",
        "archive.tar.gz": "application/octet-stream",
    }
    for name, expected in cases.items():
        assert handler._guess_media_type(Path(name)) == expected


def test_html_artifact_responses_carry_restrictive_csp(tmp_path: Path) -> None:
    web_dir = tmp_path / "output" / "web"
    web_dir.mkdir(parents=True)
    (web_dir / "index.html").write_text(
        "<!doctype html><html><body>\\(F\\)</body></html>",
        encoding="utf-8",
    )
    config = make_dashboard_config(
        project_root=tmp_path,
        skilltree_url="http://127.0.0.1:9",
    )

    with _DashboardServer(config) as base_url:
        status, headers, body = _request(f"{base_url}/artifacts/manuscript_web")

    assert status == 200
    assert body
    assert headers["Content-Security-Policy"] == ARTIFACT_HTML_CSP
    assert "connect-src 'none'" in headers["Content-Security-Policy"]


def test_dashboard_responses_carry_baseline_security_headers(tmp_path: Path) -> None:
    config = make_dashboard_config(
        project_root=tmp_path,
        skilltree_url="http://127.0.0.1:8080",
    )

    with _DashboardServer(config) as base_url:
        _, page_headers, _ = _request(f"{base_url}/")
        _, api_headers, _ = _request(f"{base_url}/healthz")

    for name, expected in BASE_SECURITY_HEADERS.items():
        assert page_headers[name] == expected
        assert api_headers[name] == expected
    csp = page_headers["Content-Security-Policy"]
    assert "frame-ancestors 'none'" in csp
    assert "connect-src 'self' http://127.0.0.1:8080" in csp
    assert "Content-Security-Policy" not in api_headers


def test_dashboard_csp_admits_the_official_skilltree_frame_and_socket(
    tmp_path: Path,
) -> None:
    """The official skills-client iframe and its live socket must not be blocked.

    Without an explicit ``frame-src`` the ``default-src 'none'`` fallback blocks
    the SkillTree learner iframe outright, and without the ``ws:`` origin the
    client's progress socket is refused; both were observed as real browser
    console errors against the live local stack.
    """
    config = make_dashboard_config(
        project_root=tmp_path,
        skilltree_url="http://127.0.0.1:8080",
    )

    with _DashboardServer(config) as base_url:
        _, page_headers, _ = _request(f"{base_url}/")

    csp = page_headers["Content-Security-Policy"]
    assert "frame-src http://127.0.0.1:8080" in csp
    assert "connect-src 'self' http://127.0.0.1:8080 ws://127.0.0.1:8080" in csp


def test_status_defer_live_skips_only_the_live_parity_check(tmp_path: Path) -> None:
    """`defer_live` must drop the live round trip and nothing else.

    The live parity call logs into SkillTree and pulls the whole dependency
    graph, which blocked every dashboard panel on first paint.
    """
    config = make_dashboard_config(
        project_root=PROJECT_ROOT,
        skilltree_url="http://127.0.0.1:9",
    )

    with _DashboardServer(config) as base_url:
        _, _, deferred_body = _request(f"{base_url}/api/status?defer_live=1")
        _, _, checked_body = _request(f"{base_url}/api/status")

    deferred = json.loads(deferred_body)
    checked = json.loads(checked_body)
    assert deferred["liveSkilltree"]["deferred"] is True
    assert deferred["liveSkilltree"]["checked"] is False
    assert "deferred" not in checked["liveSkilltree"]
    assert (
        deferred["liveSkilltree"]["expectedDependencies"]
        == (checked["liveSkilltree"]["expectedDependencies"])
    )
    for key in ("project", "graphAnalysis", "artifacts", "curriculum", "claims"):
        assert deferred[key] == checked[key]


def test_dashboard_compresses_large_json_only_for_gzip_clients(
    tmp_path: Path,
) -> None:
    """Large status payloads must ship compressed when the browser asks.

    ``/api/status`` carries the whole exported project; uncompressed that is a
    multi-megabyte first paint on every dashboard load.
    """
    config = make_dashboard_config(
        project_root=PROJECT_ROOT,
        skilltree_url="http://127.0.0.1:9",
    )

    with _DashboardServer(config) as base_url:
        plain_status, plain_headers, plain_body = _request(f"{base_url}/api/project")
        request = urllib.request.Request(
            f"{base_url}/api/project",
            headers={"Accept-Encoding": "gzip"},
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            gzip_headers = dict(response.headers)
            gzip_body = response.read()

    assert plain_status == 200
    assert "Content-Encoding" not in plain_headers
    assert gzip_headers["Content-Encoding"] == "gzip"
    assert gzip_headers["Vary"] == "Accept-Encoding"
    assert gzip.decompress(gzip_body) == plain_body
    assert len(gzip_body) < len(plain_body) / 2


def test_dashboard_leaves_small_json_uncompressed(tmp_path: Path) -> None:
    config = make_dashboard_config(
        project_root=tmp_path,
        skilltree_url="http://127.0.0.1:9",
    )

    with _DashboardServer(config) as base_url:
        request = urllib.request.Request(
            f"{base_url}/healthz",
            headers={"Accept-Encoding": "gzip"},
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            headers = dict(response.headers)
            body = response.read()

    assert "Content-Encoding" not in headers
    assert json.loads(body)["ok"] is True


def test_dashboard_honors_gzip_refusal(tmp_path: Path) -> None:
    config = make_dashboard_config(
        project_root=PROJECT_ROOT,
        skilltree_url="http://127.0.0.1:9",
    )

    with _DashboardServer(config) as base_url:
        request = urllib.request.Request(
            f"{base_url}/api/project",
            headers={"Accept-Encoding": "gzip;q=0"},
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            headers = dict(response.headers)

    assert "Content-Encoding" not in headers


def test_dashboard_csp_uses_wss_for_https_skilltree(tmp_path: Path) -> None:
    config = make_dashboard_config(
        project_root=tmp_path,
        skilltree_url="https://skilltree.example.org",
    )

    with _DashboardServer(config) as base_url:
        _, page_headers, _ = _request(f"{base_url}/")

    csp = page_headers["Content-Security-Policy"]
    assert "wss://skilltree.example.org" in csp
    assert "ws://skilltree.example.org" not in csp


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


def test_build_server_binds_configured_address(tmp_path: Path) -> None:
    port = _free_port()
    config = make_dashboard_config(project_root=tmp_path, host="127.0.0.1", port=port)
    server = build_server(config)
    try:
        assert server.server_address[:2] == ("127.0.0.1", port)
    finally:
        server.server_close()


def test_run_dashboard_server_stops_cleanly_on_sigint(tmp_path: Path) -> None:
    """Run the real blocking entrypoint in a subprocess and SIGINT it."""
    code = (
        "import sys; sys.path.insert(0, sys.argv[1]);\n"
        "from pathlib import Path\n"
        "from src.dashboard.config import make_dashboard_config\n"
        "from src.dashboard.server import run_dashboard_server\n"
        "config = make_dashboard_config(\n"
        "    project_root=Path(sys.argv[2]), port=int(sys.argv[3])\n"
        ")\n"
        "run_dashboard_server(config)\n"
    )
    process = subprocess.Popen(
        [
            sys.executable,
            "-c",
            code,
            str(PROJECT_ROOT),
            str(tmp_path),
            str(_free_port()),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        time.sleep(1.0)
        process.send_signal(signal.SIGINT)
        stdout, _ = process.communicate(timeout=5)
    finally:
        if process.poll() is None:
            process.kill()
    assert "learner dashboard:" in stdout
    assert "learner dashboard stopped" in stdout
    assert process.returncode == 0


def test_skilltree_status_non_json_body_is_truncated_text(
    httpserver: HTTPServer,
) -> None:
    httpserver.expect_request("/public/status").respond_with_data(
        "plain text status", content_type="text/plain"
    )
    status = check_skilltree_status(httpserver.url_for("/"))
    assert status["available"] is True
    assert status["body"] == "plain text status"


def test_skilltree_status_read_timeout_reports_unavailable(
    httpserver: HTTPServer,
) -> None:
    """A stalled response body must surface as a clean unavailable result."""

    def slow_handler(request):  # type: ignore[no-untyped-def]
        def stalled_body():
            yield b"{"
            time.sleep(0.6)
            yield b"}"

        from werkzeug.wrappers import Response

        return Response(stalled_body(), content_type="application/json")

    httpserver.expect_request("/public/status").respond_with_handler(slow_handler)
    status = check_skilltree_status(httpserver.url_for("/"), timeout=0.1)
    assert status["available"] is False
    assert status["statusCode"] is None
    assert "timed out" in status["message"] or "not reachable" in status["message"]


# --------------------------------------------------------------------------- #
# Token-endpoint caller authentication (RedTeam + Advisor 2026-06-10):
# the bridge must not dispense bearer tokens to foreign Host / cross-site /
# foreign-Origin callers. These are negative assertions — a passing coverage
# number hides exactly this class of bypass, so each must FAIL closed.
# --------------------------------------------------------------------------- #


def _ready_token_config(tmp_path: Path, httpserver: HTTPServer) -> DashboardConfig:
    state_dir = tmp_path / "state"
    skilltree_url = httpserver.url_for("").rstrip("/")
    _write_local_auth_state(state_dir, skilltree_url=skilltree_url)
    httpserver.expect_request("/oauth/token", method="POST").respond_with_json(
        {"access_token": "learner-token", "token_type": "Bearer"}
    )
    return make_dashboard_config(
        project_root=tmp_path,
        skilltree_url=skilltree_url,
        local_auth_enabled=True,
        local_state_dir=state_dir,
    )


def test_foreign_host_header_is_rejected(tmp_path: Path) -> None:
    config = make_dashboard_config(
        project_root=tmp_path, skilltree_url="http://127.0.0.1:9"
    )
    with _DashboardServer(config) as base_url:
        try:
            _request(f"{base_url}/healthz", headers={"Host": "attacker.example"})
        except urllib.error.HTTPError as exc:
            assert exc.code == 403
        else:
            raise AssertionError("foreign Host header was accepted (DNS-rebind risk)")


def test_token_endpoint_rejects_foreign_host(
    tmp_path: Path, httpserver: HTTPServer
) -> None:
    config = _ready_token_config(tmp_path, httpserver)
    with _DashboardServer(config) as base_url:
        try:
            _request(
                f"{base_url}/api/skilltree/token",
                headers={"Host": "attacker.example"},
            )
        except urllib.error.HTTPError as exc:
            assert exc.code == 403
        else:
            raise AssertionError("token issued to a foreign-Host caller")


def test_token_endpoint_rejects_cross_site_fetch(
    tmp_path: Path, httpserver: HTTPServer
) -> None:
    config = _ready_token_config(tmp_path, httpserver)
    with _DashboardServer(config) as base_url:
        try:
            _request(
                f"{base_url}/api/skilltree/token",
                headers={"Sec-Fetch-Site": "cross-site"},
            )
        except urllib.error.HTTPError as exc:
            body = json.loads(exc.read().decode("utf-8"))
            assert exc.code == 403
            assert body["error"] == "forbidden caller"
        else:
            raise AssertionError("token issued to a cross-site caller")


def test_token_endpoint_rejects_foreign_origin(
    tmp_path: Path, httpserver: HTTPServer
) -> None:
    config = _ready_token_config(tmp_path, httpserver)
    with _DashboardServer(config) as base_url:
        try:
            _request(
                f"{base_url}/api/skilltree/token",
                origin="http://evil.example",
            )
        except urllib.error.HTTPError as exc:
            assert exc.code == 403
        else:
            raise AssertionError("token issued to a foreign-Origin caller")


def test_token_endpoint_rejects_origin_less_post(
    tmp_path: Path, httpserver: HTTPServer
) -> None:
    """A CSRF-capable POST without an allowed Origin is refused."""
    config = _ready_token_config(tmp_path, httpserver)
    with _DashboardServer(config) as base_url:
        try:
            _request(f"{base_url}/api/skilltree/token", method="POST")
        except urllib.error.HTTPError as exc:
            assert exc.code == 403
        else:
            raise AssertionError("token issued to an Origin-less POST")


def test_token_endpoint_allows_same_origin_fetch(
    tmp_path: Path, httpserver: HTTPServer
) -> None:
    config = _ready_token_config(tmp_path, httpserver)
    with _DashboardServer(config) as base_url:
        status, _, body = _request(
            f"{base_url}/api/skilltree/token",
            headers={"Sec-Fetch-Site": "same-origin"},
            origin=config.dashboard_url,
        )
    assert status == 200
    assert json.loads(body.decode("utf-8"))["access_token"] == "learner-token"


def test_host_header_hostname_parsing() -> None:
    from src.dashboard.server import _allowed_hostnames, _host_header_hostname

    assert _host_header_hostname("127.0.0.1:8765") == "127.0.0.1"
    assert _host_header_hostname("LOCALHOST:8765") == "localhost"
    assert _host_header_hostname("[::1]:8765") == "::1"
    assert _host_header_hostname("localhost") == "localhost"
    allowed = _allowed_hostnames(make_dashboard_config(project_root=Path.cwd()))
    assert "localhost" in allowed and "127.0.0.1" in allowed


def test_foreign_host_rejected_on_post_and_options(
    tmp_path: Path, httpserver: HTTPServer
) -> None:
    config = _ready_token_config(tmp_path, httpserver)
    with _DashboardServer(config) as base_url:
        for method in ("POST", "OPTIONS"):
            try:
                _request(
                    f"{base_url}/api/skilltree/token",
                    method=method,
                    headers={"Host": "attacker.example"},
                )
            except urllib.error.HTTPError as exc:
                assert exc.code == 403
            else:
                raise AssertionError(f"{method} accepted a foreign Host header")


def test_request_without_host_header_is_allowed(tmp_path: Path) -> None:
    """An HTTP/1.0 client may omit Host; that is not a rebinding vector."""
    config = make_dashboard_config(
        project_root=tmp_path, skilltree_url="http://127.0.0.1:9"
    )
    with _DashboardServer(config) as base_url:
        host_port = base_url.removeprefix("http://")
        host, port = host_port.split(":")
        with socket.create_connection((host, int(port)), timeout=2) as sock:
            sock.sendall(b"GET /healthz HTTP/1.0\r\n\r\n")
            raw = b""
            while True:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                raw += chunk
    status_line = raw.split(b"\r\n", 1)[0].decode("ascii")
    assert "200" in status_line
    assert b'"ok": true' in raw
