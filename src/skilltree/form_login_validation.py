from __future__ import annotations

import secrets as secrets_module
import shutil
import subprocess
import threading
import time
from contextlib import contextmanager
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from src.skilltree.form_login_core import (
    SkillTreeFormLoginError,
    admin_surface_visible,
    build_login_url,
    login_submission_js,
    parse_axi_result,
    public_state_summary,
    redact,
)
from src.skilltree.form_login_core import (
    safe_command as _safe_command,
)
from src.skilltree.local_auth import (
    LocalSkillTreeAuthError,
    is_browser_login_compatible_username,
    load_local_state,
)


def _page_origin(url: str) -> str:
    """Return the ``scheme://netloc`` origin of a URL, for CORS matching."""
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"


def run_browser_command(
    command: list[str],
    *,
    timeout: float,
    secrets: tuple[str, ...] = (),
) -> subprocess.CompletedProcess[str]:
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError as exc:
        raise SkillTreeFormLoginError(
            f"required browser command not found: {command[0]}"
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise SkillTreeFormLoginError(
            "browser command timed out: " + _safe_command(command, secrets)
        ) from exc
    if result.returncode != 0:
        detail = redact(
            (result.stderr.strip() or result.stdout.strip() or "no output"),
            secrets,
        )
        raise SkillTreeFormLoginError(
            "browser command failed "
            f"({result.returncode}): {_safe_command(command, secrets)}\n{detail}"
        )
    return result


@contextmanager
def one_shot_secret_url(
    secret: str,
    *,
    allowed_origin: str | None = None,
) -> Any:
    """Yield a single-use loopback URL that serves ``secret`` once, then 404s.

    The URL is high-entropy and read-once, so it is safe to put in a browser command
    line (the current value is never the live secret for the browser, but rather a
    fetchable handoff). ``allowed_origin``, when set, restricts the CORS ``Origin``
    that may read the secret, so a cross-site page that somehow obtains the URL cannot
    read its body; plain (non-browser) clients without an ``Origin`` header are still
    allowed so CLI tooling keeps working.
    """

    token = secrets_module.token_urlsafe(24)
    consumed = False

    class SecretHandler(BaseHTTPRequestHandler):
        def _cors_headers(self) -> None:
            origin = self.headers.get("Origin")
            if origin and allowed_origin and origin == allowed_origin:
                self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")

        def do_OPTIONS(self) -> None:
            self.send_response(HTTPStatus.NO_CONTENT)
            self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self._cors_headers()
            self.send_header("Content-Length", "0")
            self.end_headers()

        def do_GET(self) -> None:
            nonlocal consumed
            if self.path != f"/secret/{token}" or consumed:
                self.send_error(HTTPStatus.NOT_FOUND, "secret not found")
                return
            origin = self.headers.get("Origin")
            if origin and not (allowed_origin and origin == allowed_origin):
                self.send_error(HTTPStatus.FORBIDDEN, "origin not allowed")
                return
            consumed = True
            body = secret.encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self._cors_headers()
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args: Any) -> None:
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), SecretHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        address = server.server_address
        host = str(address[0])
        port = int(address[1])
        yield f"http://{host}:{port}/secret/{token}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def browser_eval(
    script: str,
    *,
    browser_command: str,
    timeout: float,
    secrets: tuple[str, ...] = (),
) -> Any:
    result = run_browser_command(
        [browser_command, "eval", script],
        timeout=timeout,
        secrets=secrets,
    )
    return parse_axi_result(result.stdout)


PAGE_PROBE_JS = r"""() => {
  const body = document.body;
  const text = body ? body.innerText || "" : "";
  const inputs = [...document.querySelectorAll("input")];
  const passwordFields = inputs.filter((input) => input.type === "password");
  const submitControls = [
    ...document.querySelectorAll("button, input[type=submit], input[type=button]")
  ].map((node) => (node.innerText || node.value || node.getAttribute("aria-label") || "").trim());
  const lowerText = text.toLowerCase();
  return {
    url: location.href,
    title: document.title,
    textSample: text.slice(0, 600),
    hasPasswordField: passwordFields.length > 0,
    loginFormVisible: passwordFields.some((input) => {
      const style = window.getComputedStyle(input);
      return !input.disabled && style.visibility !== "hidden" && style.display !== "none";
    }),
    authFailure: /invalid|incorrect|failed|bad credentials|try again|unable to authenticate/.test(lowerText),
    submitControls
  };
}"""


LOGOUT_JS = r"""() => {
  localStorage.removeItem("localAuth");
  localStorage.removeItem("oAuthAuth");
  sessionStorage.clear();
  const cookie = Object.fromEntries(document.cookie.split(";").map((part) => {
    const [key, ...value] = part.trim().split("=");
    return [key, decodeURIComponent(value.join("="))];
  }).filter(([key]) => key));
  return fetch("/logout", {
    method: "POST",
    credentials: "include",
    headers: {
      "X-XSRF-TOKEN": cookie["XSRF-TOKEN"] || ""
    }
  }).then((response) => ({
    ok: response.ok,
    status: response.status,
    redirected: response.redirected,
    url: response.url
  })).catch((error) => ({
    ok: false,
    status: 0,
    error: String(error)
  }));
}"""


UI_LOGOUT_JS = r"""async () => {
  const label = (node) => [
    node.innerText || "",
    node.textContent || "",
    node.getAttribute("aria-label") || "",
    node.getAttribute("title") || ""
  ].join(" ").trim();
  const click = (node) => {
    node.dispatchEvent(new MouseEvent("mousedown", { bubbles: true }));
    node.dispatchEvent(new MouseEvent("mouseup", { bubbles: true }));
    node.click();
  };
  const settings = [...document.querySelectorAll("button, [role=button]")]
    .find((node) => /user settings|account|profile/i.test(label(node)));
  if (!settings) {
    return {
      ok: false,
      reason: "user settings control not found",
      url: location.href,
      title: document.title
    };
  }
  click(settings);
  for (let i = 0; i < 20; i += 1) {
    await new Promise((resolve) => setTimeout(resolve, 100));
    const logout = [...document.querySelectorAll("[role=menuitem], button, a")]
      .find((node) => /log out|logout|sign out/i.test(label(node)));
    if (logout) {
      click(logout);
      return {
        ok: true,
        method: "ui-menu",
        url: location.href,
        title: document.title
      };
    }
  }
  return {
    ok: false,
    reason: "logout menu item not found",
    url: location.href,
    title: document.title
  };
}"""


def probe_page(
    *,
    browser_command: str,
    timeout: float,
    secrets: tuple[str, ...] = (),
) -> dict[str, Any]:
    payload = browser_eval(
        PAGE_PROBE_JS,
        browser_command=browser_command,
        timeout=timeout,
        secrets=secrets,
    )
    if not isinstance(payload, dict):
        raise SkillTreeFormLoginError("browser page probe returned non-object payload")
    return payload


def force_browser_logout(
    *,
    skilltree_url: str,
    browser_command: str,
    timeout: float,
    secrets: tuple[str, ...] = (),
) -> dict[str, Any]:
    run_browser_command(
        [
            browser_command,
            "open",
            f"{skilltree_url.rstrip('/')}/administrator",
            "--full",
        ],
        timeout=timeout,
        secrets=secrets,
    )
    before_probe = probe_page(
        browser_command=browser_command,
        timeout=timeout,
        secrets=secrets,
    )
    if not admin_surface_visible(before_probe):
        return {
            "ok": True,
            "method": "already-logged-out",
            "status": None,
            "url": before_probe.get("url", ""),
        }
    ui_payload = browser_eval(
        UI_LOGOUT_JS,
        browser_command=browser_command,
        timeout=timeout,
        secrets=secrets,
    )
    if isinstance(ui_payload, dict) and ui_payload.get("ok"):
        run_browser_command(
            [browser_command, "wait", "1500"],
            timeout=max(2.0, min(timeout, 10.0)),
            secrets=secrets,
        )
        after_probe = probe_page(
            browser_command=browser_command,
            timeout=timeout,
            secrets=secrets,
        )
        if not admin_surface_visible(after_probe):
            return {
                "ok": True,
                "method": ui_payload.get("method", "ui-menu"),
                "status": None,
                "url": after_probe.get("url", ""),
            }
    payload = browser_eval(
        LOGOUT_JS,
        browser_command=browser_command,
        timeout=timeout,
        secrets=secrets,
    )
    if not isinstance(payload, dict):
        raise SkillTreeFormLoginError("SkillTree logout returned non-object payload")
    if not payload.get("ok"):
        raise SkillTreeFormLoginError(
            "SkillTree browser logout failed before raw FORM login proof"
        )
    return {
        "ok": bool(payload.get("ok")),
        "method": "post-logout",
        "status": payload.get("status"),
        "url": payload.get("url", ""),
    }


def wait_for_login_form(
    *,
    browser_command: str,
    timeout: float,
    secrets: tuple[str, ...] = (),
) -> dict[str, Any]:
    deadline = time.monotonic() + timeout
    last_probe: dict[str, Any] | None = None
    while time.monotonic() < deadline:
        last_probe = probe_page(
            browser_command=browser_command,
            timeout=timeout,
            secrets=secrets,
        )
        if last_probe.get("loginFormVisible") or admin_surface_visible(last_probe):
            return last_probe
        run_browser_command(
            [browser_command, "wait", "1000"],
            timeout=max(2.0, min(timeout, 10.0)),
            secrets=secrets,
        )
    raise SkillTreeFormLoginError(
        "SkillTree login form was not visible after opening login page; "
        f"last_url={(last_probe or {}).get('url', '')!r}, "
        f"title={(last_probe or {}).get('title', '')!r}"
    )


def validate_form_login(
    *,
    skilltree_url: str,
    state_dir: Path,
    project_id: str,
    browser_command: str = "chrome-devtools-axi",
    timeout: float = 60.0,
) -> dict[str, object]:
    if shutil.which(browser_command) is None:
        raise SkillTreeFormLoginError(
            f"required browser command not found on PATH: {browser_command}"
        )
    try:
        state = load_local_state(state_dir)
    except LocalSkillTreeAuthError as exc:
        raise SkillTreeFormLoginError(str(exc)) from exc
    if state is None:
        raise SkillTreeFormLoginError(
            f"local SkillTree auth state not found at {state_dir}"
        )
    if state.project_id != project_id:
        raise SkillTreeFormLoginError(
            f"local SkillTree auth state is for {state.project_id!r}, not {project_id!r}"
        )
    if state.skilltree_url and state.skilltree_url.rstrip("/") != skilltree_url.rstrip(
        "/"
    ):
        raise SkillTreeFormLoginError(
            "local SkillTree auth state URL does not match the requested SkillTree URL"
        )
    if not is_browser_login_compatible_username(state.admin_username):
        raise SkillTreeFormLoginError(
            "stored local SkillTree username is not compatible with the browser login form"
        )

    secrets = (state.admin_password, state.client_secret)
    login_url = build_login_url(skilltree_url)
    logout_result: dict[str, Any] | None = None
    initial_probe: dict[str, Any] | None = None
    for attempt in range(1, 3):
        logout_result = force_browser_logout(
            skilltree_url=skilltree_url,
            browser_command=browser_command,
            timeout=timeout,
            secrets=secrets,
        )
        logout_result["attempt"] = attempt
        run_browser_command(
            [browser_command, "open", login_url, "--full"],
            timeout=timeout,
            secrets=secrets,
        )
        initial_probe = wait_for_login_form(
            browser_command=browser_command,
            timeout=timeout,
            secrets=secrets,
        )
        if not admin_surface_visible(initial_probe):
            break
        run_browser_command(
            [browser_command, "wait", "1000"],
            timeout=max(2.0, min(timeout, 10.0)),
            secrets=secrets,
        )
    if initial_probe is None or logout_result is None:
        raise SkillTreeFormLoginError("SkillTree login verifier did not run")
    submitted = False
    if admin_surface_visible(initial_probe):
        raise SkillTreeFormLoginError(
            "SkillTree admin surface was still authenticated after logout; "
            "raw FORM login was not proven"
        )
    with one_shot_secret_url(
        state.admin_password,
        allowed_origin=_page_origin(skilltree_url),
    ) as password_url:
        submit_payload = browser_eval(
            login_submission_js(state.admin_username, password_url),
            browser_command=browser_command,
            timeout=timeout,
            secrets=secrets,
        )
    if not isinstance(submit_payload, dict) or not submit_payload.get("submitted"):
        reason = (
            submit_payload.get("reason")
            if isinstance(submit_payload, dict)
            else "non-object submit payload"
        )
        raise SkillTreeFormLoginError(
            f"SkillTree login form was not submitted: {reason}"
        )
    submitted = True

    deadline = time.monotonic() + timeout
    last_probe = initial_probe
    while time.monotonic() < deadline:
        run_browser_command(
            [browser_command, "wait", "1000"],
            timeout=max(2.0, min(timeout, 10.0)),
            secrets=secrets,
        )
        last_probe = probe_page(
            browser_command=browser_command,
            timeout=timeout,
            secrets=secrets,
        )
        if admin_surface_visible(last_probe):
            return {
                "ok": True,
                "mode": "raw-skilltree-form-login",
                "skilltreeUrl": skilltree_url.rstrip("/"),
                "loginUrl": login_url,
                "finalUrl": last_probe.get("url", ""),
                "title": last_probe.get("title", ""),
                "submittedLoginForm": submitted,
                "adminSurfaceVisible": True,
                "logoutBeforeLogin": logout_result,
                "state": public_state_summary(state_dir=state_dir, state=state),
            }
        if submitted and last_probe.get("authFailure"):
            raise SkillTreeFormLoginError(
                "SkillTree login submitted but the page reported an authentication failure"
            )

    raise SkillTreeFormLoginError(
        "SkillTree login did not reach an authenticated admin surface; "
        f"last_url={last_probe.get('url', '')!r}, title={last_probe.get('title', '')!r}"
    )
