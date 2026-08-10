from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path
from types import ModuleType

import pytest

from src.skilltree import form_login_validation as flv
from src.skilltree.local_auth import LocalSkillTreeState

REPO = Path(__file__).resolve().parents[1]


def _load_module() -> ModuleType:
    script_path = REPO / "scripts" / "validate_skilltree_form_login.py"
    spec = importlib.util.spec_from_file_location(
        "validate_skilltree_form_login", script_path
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _state() -> LocalSkillTreeState:
    return LocalSkillTreeState(
        admin_username="active-skillference-admin@localhost.invalid",
        admin_password="admin-password",
        learner_id="local-learner",
        project_id="activeInference",
        skilltree_url="http://localhost:8080",
        client_secret="trusted-secret",
    )


def test_build_login_url_targets_administrator_redirect() -> None:
    module = _load_module()

    assert (
        module.build_login_url("http://localhost:8080/")
        == "http://localhost:8080/skills-login?redirect=/administrator"
    )


def test_parse_axi_result_decodes_double_encoded_objects() -> None:
    module = _load_module()
    payload = '{"ok": true, "title": "SkillTree"}'

    assert module.parse_axi_result(
        f"result: {json.dumps(payload)}\nhelp[1]: ignored"
    ) == {
        "ok": True,
        "title": "SkillTree",
    }


def test_public_state_summary_never_contains_secrets(tmp_path: Path) -> None:
    module = _load_module()
    summary = module.public_state_summary(state_dir=tmp_path, state=_state())
    encoded = str(summary)

    assert summary["browserLoginCompatible"] is True
    assert summary["hasAdminPassword"] is True
    assert summary["hasClientSecret"] is True
    assert "admin-password" not in encoded
    assert "trusted-secret" not in encoded


def test_admin_surface_detection_rejects_visible_login_form() -> None:
    module = _load_module()

    assert (
        module.admin_surface_visible(
            {
                "url": "http://localhost:8080/administrator",
                "title": "SkillTree",
                "textSample": "Project Admin",
                "loginFormVisible": True,
                "hasPasswordField": True,
            }
        )
        is False
    )
    assert (
        module.admin_surface_visible(
            {
                "url": "http://localhost:8080/administrator",
                "title": "SkillTree",
                "textSample": "Project Admin",
                "loginFormVisible": False,
                "hasPasswordField": False,
            }
        )
        is True
    )


@pytest.mark.requires_browser
def test_browser_command_failures_are_redacted(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    module = _load_module()

    def run_probe(*args, **kwargs):  # type: ignore[no-untyped-def]
        return subprocess.CompletedProcess(
            args=args[0],
            returncode=1,
            stdout="admin-password",
            stderr="trusted-secret",
        )

    monkeypatch.setattr(module.subprocess, "run", run_probe)

    try:
        module.run_browser_command(
            ["chrome-devtools-axi", "eval", "admin-password"],
            timeout=1,
            secrets=("admin-password", "trusted-secret"),
        )
    except module.SkillTreeFormLoginError as exc:
        message = str(exc)
        assert "admin-password" not in message
        assert "trusted-secret" not in message
        assert "[REDACTED]" in message
    else:
        raise AssertionError("failed browser command was accepted")


def test_login_submission_js_uses_supplied_credentials() -> None:
    module = _load_module()
    js = module.login_submission_js("user@example.test", "pw")

    assert "user@example.test" in js
    assert '"pw"' in js
    assert "HTMLInputElement.prototype" in js
    assert "requestSubmit" in js
    assert "submit control remained disabled" in js


def test_logout_js_posts_to_skilltree_logout_with_xsrf() -> None:
    module = _load_module()

    assert 'fetch("/logout"' in module.LOGOUT_JS
    assert 'method: "POST"' in module.LOGOUT_JS
    assert "X-XSRF-TOKEN" in module.LOGOUT_JS
    assert 'localStorage.removeItem("localAuth")' in module.LOGOUT_JS
    assert "sessionStorage.clear()" in module.LOGOUT_JS
    assert "User Settings" not in module.LOGOUT_JS
    assert "user settings" in module.UI_LOGOUT_JS
    assert "log out|logout|sign out" in module.UI_LOGOUT_JS
    assert 'method: "ui-menu"' in module.UI_LOGOUT_JS


# --------------------------------------------------------------------------- #
# form_login_validation guard branches (no browser required)
# --------------------------------------------------------------------------- #


def test_run_browser_command_raises_on_missing_executable(monkeypatch) -> None:
    def missing(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise FileNotFoundError()

    monkeypatch.setattr(flv.subprocess, "run", missing)
    with pytest.raises(
        flv.SkillTreeFormLoginError, match="required browser command not found"
    ):
        flv.run_browser_command(["chrome-devtools-axi"], timeout=1)


def test_run_browser_command_raises_and_redacts_on_timeout(monkeypatch) -> None:
    def timed_out(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise subprocess.TimeoutExpired(cmd=args[0], timeout=float(kwargs["timeout"]))

    monkeypatch.setattr(flv.subprocess, "run", timed_out)
    with pytest.raises(flv.SkillTreeFormLoginError, match="timed out") as exc_info:
        flv.run_browser_command(
            ["chrome-devtools-axi", "eval", "admin-password"],
            timeout=1,
            secrets=("admin-password",),
        )
    assert "admin-password" not in str(exc_info.value)


def _guard_state(
    *, project_id: str = "activeInference", url: str = "http://localhost:8080"
) -> LocalSkillTreeState:
    return LocalSkillTreeState(
        admin_username="active-skillference-admin@localhost.invalid",
        admin_password="admin-password",
        learner_id="local-learner",
        project_id=project_id,
        skilltree_url=url,
        client_secret="trusted-secret",
    )


def test_validate_form_login_missing_browser_command(monkeypatch) -> None:
    monkeypatch.setattr(flv.shutil, "which", lambda _command: None)
    with pytest.raises(
        flv.SkillTreeFormLoginError, match="required browser command not found"
    ):
        flv.validate_form_login(
            skilltree_url="http://localhost:8080",
            state_dir=Path("/x"),
            project_id="activeInference",
            timeout=1,
        )


def test_validate_form_login_missing_state(monkeypatch) -> None:
    monkeypatch.setattr(flv.shutil, "which", lambda _command: "/usr/bin/true")
    monkeypatch.setattr(flv, "load_local_state", lambda _state_dir: None)
    with pytest.raises(flv.SkillTreeFormLoginError, match="auth state not found"):
        flv.validate_form_login(
            skilltree_url="http://localhost:8080",
            state_dir=Path("/x"),
            project_id="activeInference",
            timeout=1,
        )


def test_validate_form_login_rejects_project_id_mismatch(monkeypatch) -> None:
    monkeypatch.setattr(flv.shutil, "which", lambda _command: "/usr/bin/true")
    monkeypatch.setattr(
        flv, "load_local_state", lambda _state_dir: _guard_state(project_id="other")
    )
    with pytest.raises(flv.SkillTreeFormLoginError, match="state is for 'other'"):
        flv.validate_form_login(
            skilltree_url="http://localhost:8080",
            state_dir=Path("/x"),
            project_id="activeInference",
            timeout=1,
        )


def test_validate_form_login_rejects_url_mismatch(monkeypatch) -> None:
    monkeypatch.setattr(flv.shutil, "which", lambda _command: "/usr/bin/true")
    monkeypatch.setattr(
        flv,
        "load_local_state",
        lambda _state_dir: _guard_state(url="http://elsewhere:9000"),
    )
    with pytest.raises(
        flv.SkillTreeFormLoginError, match="does not match the requested SkillTree URL"
    ):
        flv.validate_form_login(
            skilltree_url="http://localhost:8080",
            state_dir=Path("/x"),
            project_id="activeInference",
            timeout=1,
        )


def test_validate_form_login_wraps_local_auth_error(monkeypatch) -> None:
    monkeypatch.setattr(flv.shutil, "which", lambda _command: "/usr/bin/true")

    def raise_local_auth(_state_dir):
        raise flv.LocalSkillTreeAuthError("stored state is corrupt")

    monkeypatch.setattr(flv, "load_local_state", raise_local_auth)
    with pytest.raises(flv.SkillTreeFormLoginError, match="stored state is corrupt"):
        flv.validate_form_login(
            skilltree_url="http://localhost:8080",
            state_dir=Path("/x"),
            project_id="activeInference",
            timeout=1,
        )


def test_validate_form_login_rejects_non_email_username(monkeypatch) -> None:
    state = _guard_state()
    state = LocalSkillTreeState(
        admin_username="legacy_admin",
        admin_password=state.admin_password,
        learner_id=state.learner_id,
        project_id=state.project_id,
        skilltree_url=state.skilltree_url,
        client_secret=state.client_secret,
    )
    monkeypatch.setattr(flv.shutil, "which", lambda _command: "/usr/bin/true")
    monkeypatch.setattr(flv, "load_local_state", lambda _state_dir: state)
    with pytest.raises(
        flv.SkillTreeFormLoginError,
        match="not compatible with the browser login form",
    ):
        flv.validate_form_login(
            skilltree_url="http://localhost:8080",
            state_dir=Path("/x"),
            project_id="activeInference",
            timeout=1,
        )
