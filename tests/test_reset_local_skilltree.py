"""Unit coverage for the explicit local SkillTree reset orchestrator."""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path
from types import ModuleType

REPO = Path(__file__).resolve().parents[1]


def _load_reset_module() -> ModuleType:
    script_path = REPO / "scripts" / "reset_local_skilltree.py"
    spec = importlib.util.spec_from_file_location("reset_local_skilltree", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_reset_local_skilltree_refuses_without_confirmation() -> None:
    module = _load_reset_module()
    args = module.parse_args([])

    try:
        module.reset_local_skilltree(args)
    except module.LocalSkillTreeResetError as exc:
        assert "--confirm-local-reset" in str(exc)
    else:
        raise AssertionError("local reset proceeded without explicit confirmation")


def test_reset_local_skilltree_backs_up_and_removes_auth_state(tmp_path: Path) -> None:
    module = _load_reset_module()
    state_file = tmp_path / "skilltree_auth.json"
    state_file.write_text('{"adminUsername": "historical"}\n', encoding="utf-8")

    backup = module.backup_auth_state(tmp_path, backup_stamp="20260618T000000Z")
    removed = module.remove_auth_state(tmp_path)

    assert backup == tmp_path / "skilltree_auth.json.bak.20260618T000000Z"
    assert backup.read_text(encoding="utf-8") == '{"adminUsername": "historical"}\n'
    assert removed is True
    assert not state_file.exists()


def test_reset_local_skilltree_command_shapes() -> None:
    module = _load_reset_module()
    restart = module.full_stack_restart_command(
        state_dir=".state",
        skilltree_url="http://localhost:8080",
        host="127.0.0.1",
        port=8765,
        learner_id="local-learner",
        timeout=42.0,
        skip_regenerate=True,
        require_live_dependencies=False,
    )
    strict_restart = module.full_stack_restart_command(
        state_dir=".state",
        skilltree_url="http://localhost:8080",
        host="127.0.0.1",
        port=8765,
        learner_id="local-learner",
        timeout=42.0,
        skip_regenerate=True,
        require_live_dependencies=True,
    )

    assert module.docker_reset_command() == ["docker", "compose", "down", "-v"]
    assert restart[:4] == ["uv", "run", "python", "scripts/validate_full_app_stack.py"]
    assert "--keep-running" in restart
    assert "--app-ready" in restart
    assert "--skip-regenerate" in restart
    assert "--state-dir" in restart and ".state" in restart
    assert "--app-ready" not in strict_restart


def test_reset_local_skilltree_sets_postgres_password_before_docker_reset(
    tmp_path: Path, monkeypatch
) -> None:
    """`docker compose down -v` interpolates the compose file, so the password env
    var must already be set before the reset command runs (regression: it previously
    was not, so a fresh checkout's first reset failed on missing interpolation)."""
    module = _load_reset_module()
    monkeypatch.delenv("ACTIVE_SKILLFERENCE_POSTGRES_PASSWORD", raising=False)

    seen_password_at_call: list[str | None] = []

    class _CommandResultFixture:
        stdout = "{}"

    def run_checked_probe(command, timeout=None):  # type: ignore[no-untyped-def]
        seen_password_at_call.append(
            os.environ.get("ACTIVE_SKILLFERENCE_POSTGRES_PASSWORD")
        )
        return _CommandResultFixture()

    monkeypatch.setattr(module, "run_checked", run_checked_probe)
    args = module.parse_args(["--confirm-local-reset", "--state-dir", str(tmp_path)])

    module.reset_local_skilltree(args)

    assert seen_password_at_call
    assert all(value for value in seen_password_at_call)
    assert (tmp_path / "postgres_password").exists()


def test_reset_local_skilltree_invalid_pid_file_is_cleaned(tmp_path: Path) -> None:
    module = _load_reset_module()
    pid_file = tmp_path / "dashboard.pid"
    pid_file.write_text("not-a-pid\n", encoding="utf-8")

    status = module.stop_dashboard_from_pid_file(tmp_path)

    assert "invalid dashboard pid file" in status
    assert not pid_file.exists()
