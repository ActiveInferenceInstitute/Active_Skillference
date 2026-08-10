"""Unit tests for the dashboard console smoke-gate allow-list logic (H10)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

import validate_dashboard_console as gate

_INCEPTION = (
    "msgid=89 [error] Error getting service status Error: SkillTree: Unable to "
    "authenticate using [/app/projects/Inception/users/local-learner/token] endpoint. "
    "Response Code=[401]."
)


def test_known_inception_probe_is_allow_listed() -> None:
    assert gate.unexpected_errors([_INCEPTION]) == []


def test_unexpected_error_is_surfaced() -> None:
    other = "msgid=12 [error] Uncaught TypeError: cannot read property 'x' of undefined"
    unexpected = gate.unexpected_errors([_INCEPTION, other])
    # The cosmetic probe is filtered; a real error must remain so the gate fails on it.
    assert unexpected == [other]


def test_inception_allow_list_does_not_swallow_other_401s() -> None:
    # A 401 against the real project (not the Inception probe) must NOT be allow-listed.
    real_401 = (
        "[error] Unable to authenticate using "
        "[/app/projects/activeInference/users/local-learner/token] Response Code=[401]."
    )
    assert gate.unexpected_errors([real_401]) == [real_401]


def test_dashboard_reachable_rejects_non_http_scheme() -> None:
    assert gate._dashboard_reachable("file:///etc/passwd", timeout=1.0) is False


def test_missing_browser_remains_optional_by_default(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(gate.shutil, "which", lambda _name: None)
    monkeypatch.setattr(sys, "argv", ["validate_dashboard_console.py"])

    assert gate.main() == 0
    assert "skipped (chrome-devtools-axi not installed)" in capsys.readouterr().out


def test_missing_browser_fails_when_required(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(gate.shutil, "which", lambda _name: None)
    monkeypatch.setattr(
        sys,
        "argv",
        ["validate_dashboard_console.py", "--require-browser"],
    )

    assert gate.main() == 1
    assert "FAILED (chrome-devtools-axi not installed)" in capsys.readouterr().out


def test_missing_dashboard_fails_only_when_required(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(gate.shutil, "which", lambda _name: "/bin/chrome-devtools-axi")
    monkeypatch.setattr(gate, "_dashboard_reachable", lambda _url, timeout: False)
    monkeypatch.setattr(sys, "argv", ["validate_dashboard_console.py"])

    assert gate.main() == 0
    assert "skipped (no dashboard" in capsys.readouterr().out

    monkeypatch.setattr(
        sys,
        "argv",
        ["validate_dashboard_console.py", "--require-dashboard"],
    )
    assert gate.main() == 1
    assert "FAILED (no dashboard" in capsys.readouterr().out
