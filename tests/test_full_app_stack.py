"""Unit coverage for the strict local full-app validation harness."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from src.integration import full_app_stack as stack

REPO = Path(__file__).resolve().parents[1]


def test_full_app_stack_builds_strict_commands() -> None:
    bootstrap = stack.bootstrap_command(
        python="python",
        skilltree_url="http://localhost:8080",
        state_dir="state",
        learner_id="learner",
        skip_dependencies=True,
        skip_seed_if_live_counts_ready=True,
    )
    dashboard = stack.dashboard_command(
        python="python",
        skilltree_url="http://localhost:8080",
        host="127.0.0.1",
        port=8765,
        state_dir="state",
        learner_id="learner",
    )
    live = stack.live_validation_command(
        python="python",
        dashboard_url="http://127.0.0.1:8765",
        skilltree_url="http://localhost:8080",
        state_dir="state",
        require_live_dependencies=True,
    )
    reconcile = stack.dependency_reconciliation_command(
        python="python",
        skilltree_url="http://localhost:8080",
        state_dir="state",
        timeout=42,
    )
    console = stack.console_validation_command(
        python="python",
        dashboard_url="http://127.0.0.1:8765",
    )
    raw_login = stack.form_login_validation_command(
        python="python",
        skilltree_url="http://localhost:8080",
        state_dir="state",
        timeout=42,
    )

    assert bootstrap[:2] == ["python", "scripts/bootstrap_local_skilltree.py"]
    assert "--learner-id" in bootstrap
    assert "--skip-dependencies" in bootstrap
    assert "--skip-seed-if-live-counts-ready" in bootstrap
    assert dashboard[:2] == ["python", "scripts/serve_learner_dashboard.py"]
    assert "--local-auth" in dashboard
    assert reconcile[:2] == ["python", "scripts/reconcile_live_dependencies.py"]
    assert "--timeout" in reconcile and "42" in reconcile
    assert "--require-live-admin" in live
    assert "--require-live-dependencies" in live
    assert "--require-figure-contracts" in live
    assert "--require-browser" in console
    assert "--require-dashboard" in console
    assert raw_login[:2] == ["python", "scripts/validate_skilltree_form_login.py"]
    assert "--skilltree-url" in raw_login
    assert "--state-dir" in raw_login and "state" in raw_login


def test_full_app_stack_missing_command_error_is_actionable() -> None:
    missing = REPO / "definitely-not-a-real-local-command"
    try:
        stack.run_checked([str(missing)])
    except stack.FullAppStackError as exc:
        assert "required command not found" in str(exc)
    else:  # pragma: no cover - defensive guard for impossible local path collision
        raise AssertionError("missing command unexpectedly succeeded")


def test_full_app_stack_requires_reachable_docker_daemon(monkeypatch) -> None:
    monkeypatch.setattr(stack, "require_executable", lambda _name: None)

    def fail_docker_info(command, *, cwd=stack._ROOT, timeout=None):
        raise stack.FullAppStackError("command failed: docker info")

    monkeypatch.setattr(stack, "run_checked", fail_docker_info)

    try:
        stack.require_docker_daemon()
    except stack.FullAppStackError as exc:
        assert "Docker is installed, but the Docker daemon is not reachable" in str(exc)
    else:
        raise AssertionError("unreachable Docker daemon unexpectedly passed")


def _write_fake_browser_cli(tmp_path: Path, *, recovers: bool) -> Path:
    """Write a real executable that imitates a stale chrome-devtools-axi daemon.

    ``pages`` reports an MCP timeout until ``start`` has run; when ``recovers``
    is false the restart never helps, which is the unrecoverable case.
    """
    state = tmp_path / "session-state"
    log = tmp_path / "calls.log"
    script = tmp_path / "fake-browser-cli"
    script.write_text(
        "#!/usr/bin/env python3\n"
        "import pathlib, sys\n"
        f"state = pathlib.Path({str(state)!r})\n"
        f"log = pathlib.Path({str(log)!r})\n"
        f"recovers = {recovers!r}\n"
        "command = sys.argv[1] if len(sys.argv) > 1 else ''\n"
        "with log.open('a', encoding='utf-8') as handle:\n"
        "    handle.write(command + '\\n')\n"
        "if command == 'start' and recovers:\n"
        "    state.write_text('ready', encoding='utf-8')\n"
        "if command == 'stop':\n"
        "    state.write_text('stopped', encoding='utf-8')\n"
        "if command == 'pages':\n"
        "    if state.exists() and state.read_text(encoding='utf-8') == 'ready':\n"
        "        print('pages: 1')\n"
        "        raise SystemExit(0)\n"
        "    print('code: TIMEOUT')\n"
        "    raise SystemExit(1)\n"
        "raise SystemExit(0)\n",
        encoding="utf-8",
    )
    script.chmod(0o755)
    return script


def test_full_app_stack_restarts_a_stale_browser_session(tmp_path: Path) -> None:
    script = _write_fake_browser_cli(tmp_path, recovers=True)

    result = stack.ensure_browser_session_responsive(
        browser_command=str(script),
        probe_timeout=20,
        restart_timeout=20,
    )

    assert result["restarted"] is True
    calls = (tmp_path / "calls.log").read_text(encoding="utf-8").split()
    assert calls == ["pages", "stop", "start", "pages"]


def test_full_app_stack_browser_probe_skips_restart_when_healthy(
    tmp_path: Path,
) -> None:
    script = _write_fake_browser_cli(tmp_path, recovers=True)
    (tmp_path / "session-state").write_text("ready", encoding="utf-8")

    result = stack.ensure_browser_session_responsive(
        browser_command=str(script),
        probe_timeout=20,
        restart_timeout=20,
    )

    assert result["restarted"] is False
    assert (tmp_path / "calls.log").read_text(encoding="utf-8").split() == ["pages"]


def test_full_app_stack_unrecoverable_browser_session_names_the_remedy(
    tmp_path: Path,
) -> None:
    script = _write_fake_browser_cli(tmp_path, recovers=False)

    try:
        stack.ensure_browser_session_responsive(
            browser_command=str(script),
            probe_timeout=20,
            restart_timeout=20,
        )
    except stack.FullAppStackError as exc:
        message = str(exc)
        assert "session is not responding" in message
        assert "--skip-browser" in message
        assert f"{script} stop && {script} start" in message
    else:
        raise AssertionError("unresponsive browser session unexpectedly passed")


def test_full_app_stack_stops_dashboard_process() -> None:
    process = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(30)"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    stopped_cleanly = stack.stop_dashboard_process(process, timeout=5)

    assert stopped_cleanly is True
    assert process.poll() is not None


def test_full_app_stack_wait_for_dashboard_fails_on_early_process_exit() -> None:
    process = subprocess.Popen(
        [sys.executable, "-c", "print('dashboard boot failed')"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    try:
        stack.wait_for_dashboard(
            process,
            dashboard_url="http://127.0.0.1:1",
            timeout=5,
        )
    except stack.FullAppStackError as exc:
        assert "dashboard process exited before /healthz became ready" in str(exc)
        assert "dashboard boot failed" in str(exc)
    else:
        raise AssertionError("exited dashboard process unexpectedly passed")


def test_full_app_stack_records_keep_running_dashboard_metadata(tmp_path: Path) -> None:
    pid_path, log_path = stack.record_dashboard_process(
        state_dir=str(tmp_path),
        pid=12345,
    )

    assert pid_path == tmp_path / "dashboard.pid"
    assert log_path == tmp_path / "dashboard.log"
    assert pid_path.read_text(encoding="utf-8") == "12345\n"
    assert log_path.exists()


def test_full_app_stack_ensure_postgres_password_generates_and_persists(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.delenv(stack.POSTGRES_PASSWORD_ENV_VAR, raising=False)

    password = stack.ensure_postgres_password(str(tmp_path))

    password_path = tmp_path / "postgres_password"
    assert password_path.read_text(encoding="utf-8").strip() == password
    assert oct(password_path.stat().st_mode)[-3:] == "600"
    assert os.environ[stack.POSTGRES_PASSWORD_ENV_VAR] == password


def test_full_app_stack_ensure_postgres_password_reuses_existing_file(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.delenv(stack.POSTGRES_PASSWORD_ENV_VAR, raising=False)
    password_path = tmp_path / "postgres_password"
    password_path.write_text("existing-local-secret\n", encoding="utf-8")

    password = stack.ensure_postgres_password(str(tmp_path))

    assert password == "existing-local-secret"
    assert password_path.read_text(encoding="utf-8") == "existing-local-secret\n"
    assert oct(password_path.stat().st_mode)[-3:] == "600"


def test_full_app_stack_rejects_password_path_symlink(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.delenv(stack.POSTGRES_PASSWORD_ENV_VAR, raising=False)
    target = tmp_path / "target"
    target.write_text("secret\n", encoding="utf-8")
    password_path = tmp_path / stack.POSTGRES_PASSWORD_FILE
    password_path.symlink_to(target)

    try:
        stack.ensure_postgres_password(str(tmp_path))
    except stack.FullAppStackError as exc:
        assert "regular file" in str(exc)
    else:
        raise AssertionError("password symlink unexpectedly accepted")


def test_full_app_stack_ensure_postgres_password_respects_preset_env(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv(stack.POSTGRES_PASSWORD_ENV_VAR, "operator-supplied-secret")

    password = stack.ensure_postgres_password(str(tmp_path))

    assert password == "operator-supplied-secret"
    assert not (tmp_path / "postgres_password").exists()


def test_full_app_stack_fetch_json_rejects_non_http_scheme() -> None:
    try:
        stack._fetch_json("file:///etc/passwd", timeout=1.0)
    except stack.FullAppStackError as exc:
        assert "only http/https URLs" in str(exc)
    else:
        raise AssertionError("non-http scheme unexpectedly passed _fetch_json")


def test_full_app_stack_starts_keep_running_dashboard_with_log(tmp_path: Path) -> None:
    log_path = tmp_path / "dashboard.log"
    process = stack.start_dashboard(
        [
            sys.executable,
            "-c",
            "import time; print('dashboard started', flush=True); time.sleep(30)",
        ],
        log_path=log_path,
    )
    try:
        assert process.stdout is None
        assert process.stderr is None
        assert log_path.exists()
    finally:
        stack.stop_dashboard_process(process, timeout=5)


def test_full_app_stack_proof_summary_shape() -> None:
    pid_path = Path("/tmp/dashboard.pid")
    log_path = Path("/tmp/dashboard.log")
    proof = stack.proof_summary(
        skilltree_url="http://localhost:8080",
        dashboard_url="http://127.0.0.1:8765",
        skilltree_status={"status": "OK"},
        dashboard_health={"ok": True},
        live_validation={
            "counts": {"skills": 630},
            "artifacts": {"present": 30, "missing": 0},
            "courseMaterials": {"records": 630},
            "figureContracts": {"checked": True, "registered": 19},
            "liveAdminProject": {"checked": True, "skills": 630},
            "liveDependencies": {"checked": True, "expectedDependencies": 1199},
        },
        browser_console_stdout="dashboard console gate OK",
        raw_skilltree_login={"ok": True, "adminSurfaceVisible": True},
        kept_running=True,
        dashboard_pid=12345,
        dashboard_pid_path=pid_path,
        dashboard_log_path=log_path,
        dependency_reconciliation={"ok": True, "missingAfter": 0},
        app_ready=False,
    )

    encoded = json.dumps(proof, sort_keys=True)
    assert proof["ok"] is True
    assert proof["counts"] == {"skills": 630}
    assert proof["browserConsole"]["checked"] is True
    assert proof["rawSkillTreeLogin"] == {"ok": True, "adminSurfaceVisible": True}
    assert proof["figureContracts"] == {"checked": True, "registered": 19}
    assert proof["liveDependencies"] == {
        "checked": True,
        "expectedDependencies": 1199,
    }
    assert proof["dependencyReconciliation"] == {"ok": True, "missingAfter": 0}
    assert proof["mode"] == "full-parity"
    assert proof["dashboardPid"] == 12345
    assert proof["dashboardPidPath"] == str(pid_path)
    assert proof["dashboardLogPath"] == str(log_path)
    assert "dashboard console gate OK" in encoded


def test_full_app_stack_proof_summary_does_not_certify_failed_subproof() -> None:
    proof = stack.proof_summary(
        skilltree_url="http://localhost:8080",
        dashboard_url="http://127.0.0.1:8765",
        skilltree_status={},
        dashboard_health={"ok": True},
        live_validation={"ok": False},
        browser_console_stdout=None,
        raw_skilltree_login=None,
        kept_running=False,
        dashboard_pid=None,
    )

    assert proof["ok"] is False


def test_full_app_stack_writes_redacted_deterministic_proof(tmp_path: Path) -> None:
    proof = {
        "ok": True,
        "browserConsole": {"summary": "Authorization: Bearer super-secret"},
        "token": "super-secret",
        "counts": {"skills": 630},
    }

    path = stack.write_proof_artifact(proof, tmp_path / "proof.json")
    payload = json.loads(path.read_text(encoding="utf-8"))

    assert payload["proofVersion"] == 1
    assert payload["token"] == "[REDACTED]"
    assert "super-secret" not in path.read_text(encoding="utf-8")
    assert payload["counts"] == {"skills": 630}
