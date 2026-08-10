"""Pure helpers for SkillTree FORM login validation (no browser subprocess I/O)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.skilltree.local_auth import is_browser_login_compatible_username


class SkillTreeFormLoginError(RuntimeError):
    """Raised when browser-based FORM login validation fails."""


def redact(text: str, secrets: tuple[str, ...]) -> str:
    redacted = text
    for secret in secrets:
        if secret:
            redacted = redacted.replace(secret, "[REDACTED]")
    return redacted


def build_login_url(skilltree_url: str) -> str:
    return f"{skilltree_url.rstrip('/')}/skills-login?redirect=/administrator"


def public_state_summary(*, state_dir: Path, state: Any) -> dict[str, object]:
    return {
        "stateDir": str(state_dir),
        "projectId": state.project_id,
        "learnerId": state.learner_id,
        "skilltreeUrl": state.skilltree_url,
        "browserLoginCompatible": is_browser_login_compatible_username(
            state.admin_username
        ),
        "hasAdminPassword": bool(state.admin_password),
        "hasClientSecret": bool(state.client_secret),
    }


def safe_command(command: list[str], secrets: tuple[str, ...]) -> str:
    return redact(" ".join(command), secrets)


def parse_axi_result(stdout: str) -> Any:
    for line in stdout.splitlines():
        if not line.startswith("result: "):
            continue
        raw = line.removeprefix("result: ").strip()
        try:
            value = json.loads(raw)
        except json.JSONDecodeError:
            return raw
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return value
    raise SkillTreeFormLoginError("chrome-devtools-axi eval produced no result line")


def admin_surface_visible(probe: dict[str, Any]) -> bool:
    url = str(probe.get("url", "")).lower()
    title = str(probe.get("title", "")).lower()
    text = str(probe.get("textSample", "")).lower()
    if probe.get("loginFormVisible") or probe.get("hasPasswordField"):
        return False
    if "/administrator" in url:
        return True
    admin_markers = (
        "administrator",
        "project admin",
        "manage projects",
        "my projects",
        "project catalog",
        "skills display",
    )
    return any(marker in title or marker in text for marker in admin_markers)


def login_submission_js(username: str, password_url: str) -> str:
    return f"""async () => {{
  const username = {json.dumps(username)};
  const passwordResponse = await fetch({json.dumps(password_url)}, {{ cache: "no-store" }});
  if (!passwordResponse.ok) {{
    return {{
      submitted: false,
      reason: `password handoff failed: ${{passwordResponse.status}}`,
      url: location.href,
      title: document.title
    }};
  }}
  const password = await passwordResponse.text();
  const inputs = [...document.querySelectorAll("input")];
  const visible = (input) => {{
    const style = window.getComputedStyle(input);
    return !input.disabled && input.type !== "hidden" &&
      style.visibility !== "hidden" && style.display !== "none";
  }};
  const usernameInput =
    document.querySelector('input[name="username"], input#username, input[type="email"], input[autocomplete="username"]') ||
    inputs.find((input) => visible(input) && /user|email|login/i.test(`${{input.name}} ${{input.id}} ${{input.placeholder}} ${{input.getAttribute("aria-label") || ""}}`)) ||
    inputs.find((input) => visible(input) && input.type !== "password" && input.type !== "checkbox" && input.type !== "radio");
  const passwordInput =
    document.querySelector('input[type="password"], input[name="password"], input#password, input[autocomplete="current-password"]') ||
    inputs.find((input) => visible(input) && input.type === "password");
  if (!usernameInput || !passwordInput) {{
    return {{
      submitted: false,
      reason: "login form fields not found",
      inputCount: inputs.length,
      url: location.href,
      title: document.title
    }};
  }}
  const setValue = (input, value) => {{
    input.focus();
    const setter = Object.getOwnPropertyDescriptor(
      window.HTMLInputElement.prototype,
      "value"
    ).set;
    setter.call(input, value);
    input.dispatchEvent(new Event("input", {{ bubbles: true }}));
    input.dispatchEvent(new Event("change", {{ bubbles: true }}));
    input.blur();
  }};
  setValue(usernameInput, username);
  setValue(passwordInput, password);
  const form = passwordInput.form || usernameInput.form || document.querySelector("form");
  let submit = form
    ? form.querySelector('button[type="submit"], input[type="submit"], button')
    : document.querySelector('button[type="submit"], input[type="submit"], button');
  for (let i = 0; i < 50; i += 1) {{
    submit = form
      ? form.querySelector('button[type="submit"], input[type="submit"], button')
      : document.querySelector('button[type="submit"], input[type="submit"], button');
    if (submit && !submit.disabled && submit.getAttribute("aria-disabled") !== "true") {{
      break;
    }}
    await new Promise((resolve) => setTimeout(resolve, 100));
  }}
  if (submit && (submit.disabled || submit.getAttribute("aria-disabled") === "true")) {{
    return {{
      submitted: false,
      reason: "submit control remained disabled after filling credentials",
      inputCount: inputs.length,
      url: location.href,
      title: document.title
    }};
  }}
  if (form && typeof form.requestSubmit === "function") {{
    form.requestSubmit(submit || undefined);
  }} else if (submit) {{
    submit.click();
  }} else if (form) {{
    form.submit();
  }} else {{
    return {{
      submitted: false,
      reason: "submit control not found",
      inputCount: inputs.length,
      url: location.href,
      title: document.title
    }};
  }}
  return {{
    submitted: true,
    url: location.href,
    title: document.title
  }};
}}"""
