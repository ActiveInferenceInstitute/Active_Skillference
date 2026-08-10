"""HTTP server for the local Active Skillference learner dashboard."""

from __future__ import annotations

import gzip
import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse

from src.curriculum.recommendations import recommend_next_skills
from src.dashboard.artifacts import (
    DashboardArtifactError,
    artifact_inventory,
    get_artifact,
    load_claims_summary,
    load_course_material_index,
    load_redacted_skilltree_export,
    load_skilltree_project,
)
from src.dashboard.config import DashboardConfig
from src.dashboard.payload import (
    dashboard_payload,
)
from src.skilltree.client import SkillTreeClientError
from src.skilltree.local_auth import (
    LocalSkillTreeAuthError,
    fetch_local_skilltree_token,
)


def dashboard_recommendations(config: DashboardConfig) -> dict[str, Any]:
    """Return the read-only path prototype for the current exported project."""
    return recommend_next_skills(load_skilltree_project(config.project_root))


ASSETS_ROOT = Path(__file__).resolve().parent / "assets"
# Below this size compression costs more than it saves on a loopback socket.
GZIP_MIN_BYTES = 4096
# MathJax is loaded from cdn.jsdelivr.net; its CHTML output fetches webfonts
# from the same CDN, so font-src must allow it or the console gate fails.
ARTIFACT_HTML_CSP = (
    "default-src 'none'; "
    "base-uri 'none'; "
    "connect-src 'none'; "
    "font-src 'self' data: https://cdn.jsdelivr.net; "  # MathJax CHTML webfonts
    "form-action 'none'; "
    "frame-ancestors 'none'; "
    "img-src 'self' data:; "
    "object-src 'none'; "
    "script-src 'self' https://cdn.jsdelivr.net 'unsafe-inline'; "
    "style-src 'self' 'unsafe-inline'"
)
BASE_SECURITY_HEADERS = {
    "Cross-Origin-Opener-Policy": "same-origin",
    "Permissions-Policy": "camera=(), geolocation=(), microphone=()",
    "Referrer-Policy": "no-referrer",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
}


def _json_bytes(payload: object) -> bytes:
    return json.dumps(payload, indent=2, sort_keys=True).encode("utf-8") + b"\n"


def _query_flag(query: dict[str, list[str]], name: str) -> bool:
    """Return whether a bare or truthy query flag is present."""
    values = query.get(name)
    if values is None:
        return False
    return all(
        value.strip().lower() in {"", "1", "true", "yes", "on"} for value in values
    )


def _accepts_gzip(accept_encoding: str) -> bool:
    """Return whether a client advertised gzip without explicitly refusing it."""
    for raw in accept_encoding.split(","):
        token, _, params = raw.strip().partition(";")
        if token.strip().lower() != "gzip":
            continue
        quality = params.strip().lower()
        if not quality.startswith("q="):
            return True
        try:
            # A malformed q-value is a client error, not a reason to 500 the route.
            weight = float(quality[2:] or 1)
        except ValueError:
            return False
        return weight != 0
    return False


def _origin(url: str) -> str:
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"


def _allowed_cors_origins(config: DashboardConfig) -> set[str]:
    return {_origin(config.skilltree_url), _origin(config.dashboard_url)}


def _allowed_hostnames(config: DashboardConfig) -> set[str]:
    """Hostnames the dashboard answers to (anti-DNS-rebinding).

    Only the hostname is pinned, not the port: the rebinding vector is the
    name (``attacker.com`` rebinding to 127.0.0.1), and the listening port is
    fixed by the server, so matching the host portion alone is the standard,
    ephemeral-port-robust check.
    """
    return {config.host.lower(), "localhost", "127.0.0.1"}


def _websocket_origin(url: str) -> str:
    """Return the WebSocket origin matching an HTTP(S) origin.

    ``skills-client-js`` opens a SockJS/STOMP connection to the SkillTree
    service for live progress events. The browser matches that request against
    ``connect-src`` using the ``ws:``/``wss:`` scheme, not the ``http:``/
    ``https:`` origin the page was configured with, so the WebSocket origin has
    to be allowed explicitly or every live update is blocked.
    """
    parsed = urlparse(url)
    scheme = "wss" if parsed.scheme == "https" else "ws"
    return f"{scheme}://{parsed.netloc}"


def _dashboard_csp(config: DashboardConfig) -> str:
    """Return the CSP for the interactive local dashboard shell.

    The official SkillTree learner display is an iframe owned by
    ``skills-client-js``; without an explicit ``frame-src`` for the SkillTree
    origin the ``default-src 'none'`` fallback blocks it and the Official
    Display panel renders as an empty box.
    """
    skilltree_origin = _origin(config.skilltree_url)
    skilltree_ws_origin = _websocket_origin(config.skilltree_url)
    return (
        "default-src 'none'; "
        "base-uri 'none'; "
        f"connect-src 'self' {skilltree_origin} {skilltree_ws_origin}; "
        "font-src 'self' data: https://cdn.jsdelivr.net; "  # MathJax CHTML webfonts
        "form-action 'none'; "
        "frame-ancestors 'none'; "
        f"frame-src {skilltree_origin}; "  # official skills-client-js learner iframe
        "img-src 'self' data:; "
        "object-src 'none'; "
        "script-src 'self' https://cdn.jsdelivr.net 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'"
    )


def _host_header_hostname(host_header: str) -> str:
    """Return the lowercased hostname portion of a Host header (drop port)."""
    value = host_header.strip().lower()
    if value.startswith("[") and "]" in value:  # IPv6 literal: [::1]:8765
        return value[1 : value.index("]")]
    return value.rsplit(":", 1)[0] if ":" in value else value


def make_dashboard_handler(config: DashboardConfig) -> type[BaseHTTPRequestHandler]:
    """Create a request handler bound to one immutable dashboard config."""

    class DashboardRequestHandler(BaseHTTPRequestHandler):
        server_version = "ActiveSkillferenceDashboard/1.0"

        def end_headers(self) -> None:
            """Attach baseline browser hardening to success and error responses."""
            for name, value in BASE_SECURITY_HEADERS.items():
                self.send_header(name, value)
            super().end_headers()

        def _host_allowed(self) -> bool:
            """Reject foreign Host headers — defeats DNS-rebinding token theft.

            A page on attacker.com that rebinds its DNS to 127.0.0.1 would
            otherwise reach this server as "same-origin" from the browser's
            view and read the response. Pinning the Host header to the known
            local names breaks that path for every route.
            """
            host = self.headers.get("Host", "")
            if not host:
                return True  # HTTP/1.0 clients may omit Host; not a rebind vector
            return _host_header_hostname(host) in _allowed_hostnames(config)

        def _token_caller_allowed(self) -> bool:
            """Gate token issuance to same-origin (or non-browser) callers.

            The official skills-client runs in the dashboard page and calls the
            authenticator same-origin, so browsers send ``Sec-Fetch-Site:
            same-origin``. A cross-site page, or a foreign ``Origin``, is refused —
            the token endpoint is not a public credential dispenser. For the
            CSRF-capable ``POST`` method we additionally require an allowed
            ``Origin`` (browsers always attach ``Origin`` to a POST), which closes
            the Origin-less-caller gap for POSTs. ``GET`` fetches may legitimately
            omit ``Origin`` on a same-origin request, so those accept absent-or-allowed.
            """
            fetch_site = self.headers.get("Sec-Fetch-Site")
            if fetch_site is not None and fetch_site not in {"same-origin", "none"}:
                return False
            origin = self.headers.get("Origin")
            if self.command == "POST":
                return bool(origin) and origin in _allowed_cors_origins(config)
            return (not origin) or origin in _allowed_cors_origins(config)

        def _reject_forbidden_host(self) -> bool:
            if self._host_allowed():
                return False
            self.send_error(HTTPStatus.FORBIDDEN, "host not allowed")
            return True

        def do_GET(self) -> None:
            if self._reject_forbidden_host():
                return
            parsed = urlparse(self.path)
            path = parsed.path
            if path in {"/", "/index.html"}:
                self._send_static_file(ASSETS_ROOT / "index.html")
                return
            if path.startswith("/assets/"):
                self._send_asset(path)
                return
            if path == "/healthz":
                self._send_json(
                    {
                        "ok": True,
                        "projectId": config.project_id,
                        "skilltreeUrl": config.skilltree_url,
                    }
                )
                return
            if path == "/api/config":
                self._send_json(config.to_public_dict())
                return
            if path == "/api/status":
                query = parse_qs(parsed.query)
                self._send_json(
                    dashboard_payload(
                        config,
                        defer_live=_query_flag(query, "defer_live"),
                    )
                )
                return
            if path == "/api/recommendations":
                self._send_json(dashboard_recommendations(config))
                return
            if path == "/api/skilltree/token":
                self._send_skilltree_token()
                return
            if path == "/api/project":
                self._send_json(load_skilltree_project(config.project_root))
                return
            if path == "/api/claims":
                self._send_json(load_claims_summary(config.project_root))
                return
            if path == "/api/artifacts":
                self._send_json(artifact_inventory(config.project_root))
                return
            if path == "/api/course-materials":
                self._send_json(load_course_material_index(config.project_root))
                return
            if path.startswith("/artifacts/"):
                self._send_artifact(path)
                return
            self.send_error(HTTPStatus.NOT_FOUND, "dashboard route not found")

        def do_POST(self) -> None:
            if self._reject_forbidden_host():
                return
            parsed = urlparse(self.path)
            if parsed.path == "/api/skilltree/token":
                self._send_skilltree_token()
                return
            self.send_error(HTTPStatus.NOT_FOUND, "dashboard route not found")

        def do_OPTIONS(self) -> None:
            if self._reject_forbidden_host():
                return
            parsed = urlparse(self.path)
            if parsed.path == "/api/skilltree/token":
                self.send_response(HTTPStatus.NO_CONTENT)
                self._send_cors_headers()
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            self.send_error(HTTPStatus.NOT_FOUND, "dashboard route not found")

        def log_message(self, format: str, *args: Any) -> None:
            """Keep routine local dashboard requests out of test output."""

        def _send_json(
            self, payload: object, status: HTTPStatus = HTTPStatus.OK
        ) -> None:
            body = _json_bytes(payload)
            # /api/status carries the whole exported project and graph analysis —
            # several megabytes of highly repetitive JSON. Compressing it when the
            # browser asks turns the dashboard's first paint from a multi-megabyte
            # transfer into a few hundred kilobytes.
            encoding: str | None = None
            if len(body) >= GZIP_MIN_BYTES and _accepts_gzip(
                self.headers.get("Accept-Encoding", "")
            ):
                body = gzip.compress(body, compresslevel=6, mtime=0)
                encoding = "gzip"
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            if encoding:
                self.send_header("Content-Encoding", encoding)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("Vary", "Accept-Encoding")
            self._send_cors_headers()
            self.end_headers()
            self.wfile.write(body)

        def _send_cors_headers(self) -> None:
            origin = self.headers.get("Origin", "")
            if origin not in _allowed_cors_origins(config):
                return
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header(
                "Access-Control-Allow-Headers", "Content-Type, Authorization"
            )
            self.send_header("Access-Control-Max-Age", "600")
            self.send_header("Vary", "Origin")

        def _send_skilltree_token(self) -> None:
            if not self._token_caller_allowed():
                self._send_json(
                    {
                        "error": "forbidden caller",
                        "message": (
                            "token issuance is restricted to same-origin dashboard "
                            "requests"
                        ),
                    },
                    status=HTTPStatus.FORBIDDEN,
                )
                return
            local_auth = config.local_auth
            if not (local_auth["enabled"] and local_auth["ready"]):
                self._send_json(
                    {
                        "error": "local SkillTree auth is not ready",
                        "message": local_auth["message"],
                    },
                    status=HTTPStatus.SERVICE_UNAVAILABLE,
                )
                return
            try:
                token = fetch_local_skilltree_token(
                    base_url=config.skilltree_url,
                    state_dir=config.local_state_dir
                    or config.project_root / ".active_skillference_local",
                    project_id=config.project_id,
                    learner_id=config.learner_id,
                )
            except LocalSkillTreeAuthError:
                self._send_json(
                    {
                        "error": "local SkillTree auth failed",
                        "message": "local SkillTree authentication or token retrieval failed",
                    },
                    status=HTTPStatus.SERVICE_UNAVAILABLE,
                )
                return
            except SkillTreeClientError as exc:
                self._send_json(
                    {
                        "error": "SkillTree token exchange failed",
                        "message": "SkillTree token exchange endpoint returned an error",
                        "status": exc.status,
                    },
                    status=HTTPStatus.BAD_GATEWAY,
                )
                return
            self._send_json(token)

        def _send_asset(self, request_path: str) -> None:
            asset_name = unquote(request_path.removeprefix("/assets/"))
            if not asset_name or any(
                part in {"", ".", ".."} or part.startswith(".")
                for part in Path(asset_name).parts
            ):
                self.send_error(HTTPStatus.BAD_REQUEST, "invalid asset path")
                return
            assets_root = ASSETS_ROOT.resolve()
            asset_path = (assets_root / asset_name).resolve()
            try:
                asset_path.relative_to(assets_root)
            except ValueError:
                self.send_error(HTTPStatus.BAD_REQUEST, "invalid asset path")
                return
            self._send_static_file(asset_path)

        def _send_artifact(self, request_path: str) -> None:
            artifact_id = unquote(request_path.removeprefix("/artifacts/"))
            try:
                artifact = get_artifact(artifact_id)
            except DashboardArtifactError:
                self.send_error(HTTPStatus.NOT_FOUND, "unknown artifact")
                return
            if artifact.artifact_id == "skilltree_project":
                payload, error = load_redacted_skilltree_export(config.project_root)
                if payload is None:
                    self.send_error(HTTPStatus.NOT_FOUND, error or "file not found")
                    return
                self._send_json(payload)
                return
            self._send_static_file(
                artifact.path(config.project_root),
                media_type=artifact.media_type,
                artifact_response=True,
            )

        def _send_static_file(
            self,
            path: Path,
            media_type: str | None = None,
            artifact_response: bool = False,
        ) -> None:
            if not path.exists() or not path.is_file():
                self.send_error(HTTPStatus.NOT_FOUND, "file not found")
                return
            body = path.read_bytes()
            self.send_response(HTTPStatus.OK)
            self.send_header(
                "Content-Type",
                media_type or self._guess_media_type(path),
            )
            self.send_header("Content-Length", str(len(body)))
            content_type = media_type or self._guess_media_type(path)
            if artifact_response and content_type.startswith("text/html"):
                self.send_header("Content-Security-Policy", ARTIFACT_HTML_CSP)
            elif path == ASSETS_ROOT / "index.html":
                self.send_header("Content-Security-Policy", _dashboard_csp(config))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        @staticmethod
        def _guess_media_type(path: Path) -> str:
            if path.suffix == ".html":
                return "text/html; charset=utf-8"
            if path.suffix == ".css":
                return "text/css; charset=utf-8"
            if path.suffix == ".js":
                return "application/javascript; charset=utf-8"
            if path.suffix == ".json":
                return "application/json; charset=utf-8"
            if path.suffix == ".png":
                return "image/png"
            if path.suffix == ".pdf":
                return "application/pdf"
            return "application/octet-stream"

    return DashboardRequestHandler


def build_server(config: DashboardConfig) -> ThreadingHTTPServer:
    """Build the bound dashboard HTTP server without starting it."""
    handler = make_dashboard_handler(config)
    return ThreadingHTTPServer((config.host, config.port), handler)


def run_dashboard_server(config: DashboardConfig) -> None:
    """Serve the dashboard until interrupted."""
    server = build_server(config)
    try:
        print(f"learner dashboard: {config.dashboard_url}")
        print(f"SkillTree service: {config.skilltree_url}")
        server.serve_forever()  # pragma: no cover - blocking loop; behavior proven by the SIGINT subprocess test
    except KeyboardInterrupt:
        print("\nlearner dashboard stopped")
    finally:
        server.server_close()
