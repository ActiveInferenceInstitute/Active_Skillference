from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.skilltree.form_login_core import (
    SkillTreeFormLoginError,
    admin_surface_visible,
    build_login_url,
    login_submission_js,
    parse_axi_result,
    public_state_summary,
    redact,
    safe_command,
)
from src.skilltree.local_auth import LocalSkillTreeState


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
    assert (
        build_login_url("http://localhost:8080/")
        == "http://localhost:8080/skills-login?redirect=/administrator"
    )


def test_public_state_summary_never_contains_secrets(tmp_path: Path) -> None:
    summary = public_state_summary(state_dir=tmp_path, state=_state())
    encoded = str(summary)
    assert summary["browserLoginCompatible"] is True
    assert "admin-password" not in encoded
    assert "trusted-secret" not in encoded


def test_redact_and_safe_command_strip_secrets() -> None:
    secrets = ("secret-token",)
    assert redact("password=secret-token", secrets) == "password=[REDACTED]"
    assert (
        safe_command(["axi", "eval", "secret-token"], secrets) == "axi eval [REDACTED]"
    )


def test_parse_axi_result_decodes_double_encoded_objects() -> None:
    payload = {"ok": True, "title": "SkillTree"}
    stdout = f"result: {json.dumps(payload)}\nhelp[1]: ignored"
    assert parse_axi_result(stdout) == payload


def test_parse_axi_result_raises_when_missing_result_line() -> None:
    with pytest.raises(SkillTreeFormLoginError, match="no result line"):
        parse_axi_result("help[1]: ignored\n")


def test_admin_surface_visible_rejects_login_form() -> None:
    assert (
        admin_surface_visible(
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


def test_admin_surface_visible_accepts_title_markers() -> None:
    assert admin_surface_visible(
        {
            "url": "http://localhost:8080/",
            "title": "Project Admin",
            "textSample": "",
            "loginFormVisible": False,
            "hasPasswordField": False,
        }
    )


def test_login_submission_js_fetches_password_from_handoff_url() -> None:
    script = login_submission_js("admin@example.test", "http://127.0.0.1:8765/secret/x")
    assert "admin@example.test" in script
    assert "http://127.0.0.1:8765/secret/x" in script
    assert "fetch(" in script
