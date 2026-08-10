#!/usr/bin/env python3
"""Reset the local SkillTree Docker volume and restart the full local app stack.

This is intentionally explicit and local-destructive. It backs up ignored local auth
state, removes the Docker Compose volume, and reruns the strict full-stack harness so
fresh bootstraps use the documented local email/password defaults.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "src"))

from src.integration.full_app_stack import ensure_postgres_password

LOCAL_STATE_FILE = "skilltree_auth.json"
DASHBOARD_PID_FILE = "dashboard.pid"
DEFAULT_STATE_DIR = ".active_skillference_local"
DEFAULT_RESET_TIMEOUT_SECONDS = 7200.0


class LocalSkillTreeResetError(RuntimeError):
    """Raised when the local reset cannot complete safely."""


def _command_text(command: list[str]) -> str:
    return " ".join(command)


def _tail(text: str, limit: int = 1200) -> str:
    value = text.strip()
    return value[-limit:] if len(value) > limit else value


def resolve_state_dir(value: str) -> Path:
    """Resolve a state directory relative to the project root."""
    path = Path(value)
    if not path.is_absolute():
        path = _ROOT / path
    return path


def auth_state_path(state_dir: Path) -> Path:
    """Return the local SkillTree auth-state file path."""
    return state_dir / LOCAL_STATE_FILE


def dashboard_pid_path(state_dir: Path) -> Path:
    """Return the detached dashboard PID file path."""
    return state_dir / DASHBOARD_PID_FILE


def timestamp() -> str:
    """Return a compact UTC timestamp for backup filenames."""
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def backup_auth_state(
    state_dir: Path, *, backup_stamp: str | None = None
) -> Path | None:
    """Back up existing ignored local credentials, returning the backup path."""
    source = auth_state_path(state_dir)
    if not source.exists():
        return None
    stamp = backup_stamp or timestamp()
    backup = source.with_name(f"{source.name}.bak.{stamp}")
    backup.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, backup)
    return backup


def remove_auth_state(state_dir: Path) -> bool:
    """Remove stale local auth state after it has been backed up."""
    path = auth_state_path(state_dir)
    if not path.exists():
        return False
    path.unlink()
    return True


def _pid_running(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def stop_dashboard_from_pid_file(state_dir: Path, *, timeout: float = 5.0) -> str:
    """Stop a detached dashboard process if a PID file exists."""
    pid_file = dashboard_pid_path(state_dir)
    if not pid_file.exists():
        return "no dashboard pid file"
    raw = pid_file.read_text(encoding="utf-8").strip()
    try:
        pid = int(raw)
    except ValueError:
        pid_file.unlink(missing_ok=True)
        return f"removed invalid dashboard pid file: {raw!r}"
    if not _pid_running(pid):
        pid_file.unlink(missing_ok=True)
        return f"removed stale dashboard pid file for pid {pid}"

    os.kill(pid, signal.SIGTERM)
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if not _pid_running(pid):
            pid_file.unlink(missing_ok=True)
            return f"stopped dashboard pid {pid}"
        time.sleep(0.1)

    os.kill(pid, signal.SIGKILL)
    pid_file.unlink(missing_ok=True)
    return f"killed dashboard pid {pid} after timeout"


def run_checked(
    command: list[str], *, timeout: float
) -> subprocess.CompletedProcess[str]:
    """Run a command from the repo root and raise with actionable output on failure."""
    try:
        result = subprocess.run(
            command,
            cwd=_ROOT,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError as exc:
        raise LocalSkillTreeResetError(
            f"required command not found: {command[0]}"
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise LocalSkillTreeResetError(
            f"command timed out after {timeout:g}s: {_command_text(command)}"
        ) from exc
    if result.returncode != 0:
        detail = _tail(result.stderr) or _tail(result.stdout) or "no output"
        raise LocalSkillTreeResetError(
            f"command failed ({result.returncode}): {_command_text(command)}\n{detail}"
        )
    return result


def docker_reset_command() -> list[str]:
    """Return the Docker Compose local-volume reset command."""
    return ["docker", "compose", "down", "-v"]


def full_stack_restart_command(
    *,
    state_dir: str,
    skilltree_url: str,
    host: str,
    port: int,
    learner_id: str,
    timeout: float,
    skip_regenerate: bool,
    require_live_dependencies: bool,
) -> list[str]:
    """Return the strict full-app restart/proof command used after reset."""
    command = [
        "uv",
        "run",
        "python",
        "scripts/validate_full_app_stack.py",
        "--skilltree-url",
        skilltree_url,
        "--host",
        host,
        "--port",
        str(port),
        "--state-dir",
        state_dir,
        "--learner-id",
        learner_id,
        "--timeout",
        str(timeout),
        "--keep-running",
    ]
    if not require_live_dependencies:
        command.append("--app-ready")
    if skip_regenerate:
        command.append("--skip-regenerate")
    return command


def reset_local_skilltree(args: argparse.Namespace) -> dict[str, Any]:
    """Perform the explicit local reset and restart sequence."""
    if not args.confirm_local_reset:
        raise LocalSkillTreeResetError(
            "refusing to reset local SkillTree without --confirm-local-reset"
        )

    state_dir = resolve_state_dir(args.state_dir)
    stop_status = stop_dashboard_from_pid_file(state_dir, timeout=5.0)
    backup = backup_auth_state(state_dir)
    removed_state = remove_auth_state(state_dir)

    ensure_postgres_password(args.state_dir)
    run_checked(docker_reset_command(), timeout=args.timeout)
    restart_command = full_stack_restart_command(
        state_dir=args.state_dir,
        skilltree_url=args.skilltree_url,
        host=args.host,
        port=args.port,
        learner_id=args.learner_id,
        timeout=args.timeout,
        skip_regenerate=not args.regenerate,
        require_live_dependencies=args.require_live_dependencies,
    )
    proof_result = run_checked(restart_command, timeout=args.timeout)
    try:
        proof: object = json.loads(proof_result.stdout)
    except json.JSONDecodeError:
        proof = {"raw": proof_result.stdout.strip()}

    return {
        "ok": True,
        "dashboardStop": stop_status,
        "authStateBackup": str(backup) if backup else None,
        "removedAuthState": removed_state,
        "dockerResetCommand": docker_reset_command(),
        "restartCommand": restart_command,
        "fullDependencyParityCommand": (
            "uv run python scripts/reconcile_live_dependencies.py && "
            "uv run python scripts/validate_full_app_stack.py "
            "--skip-regenerate --keep-running"
        ),
        "proof": proof,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--confirm-local-reset",
        action="store_true",
        help="required: acknowledge that the local SkillTree Docker volume is deleted",
    )
    parser.add_argument("--skilltree-url", default="http://localhost:8080")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--state-dir", default=DEFAULT_STATE_DIR)
    parser.add_argument("--learner-id", default="local-learner")
    parser.add_argument("--timeout", type=float, default=DEFAULT_RESET_TIMEOUT_SECONDS)
    parser.add_argument(
        "--regenerate",
        action="store_true",
        help="rerun build/kernels/export during restart instead of --skip-regenerate",
    )
    parser.add_argument(
        "--require-live-dependencies",
        action="store_true",
        help="wait for full live SkillTree dependency parity during reset/restart",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        result = reset_local_skilltree(args)
    except LocalSkillTreeResetError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
