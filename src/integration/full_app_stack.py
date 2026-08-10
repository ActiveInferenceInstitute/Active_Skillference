from __future__ import annotations

import argparse
import json
import os
import re
import secrets
import shutil
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from src.artifacts.json_io import write_json_artifact
from src.net_guard import NonHttpUrlError, require_http_url

_ROOT = Path(__file__).resolve().parents[2]
_REQUEST_TIMEOUT_SECONDS = 10.0
_FORM_LOGIN_TIMEOUT_SECONDS = 60.0
_DASHBOARD_STOP_SECONDS = 5.0
BROWSER_COMMAND = "chrome-devtools-axi"
_BROWSER_PROBE_TIMEOUT_SECONDS = 25.0
_BROWSER_RESTART_TIMEOUT_SECONDS = 60.0
DASHBOARD_PID_FILE = "dashboard.pid"
DASHBOARD_LOG_FILE = "dashboard.log"
POSTGRES_PASSWORD_FILE = "postgres_password"
POSTGRES_PASSWORD_ENV_VAR = "ACTIVE_SKILLFERENCE_POSTGRES_PASSWORD"
_SENSITIVE_PROOF_KEYS = frozenset(
    {"access_token", "accesstoken", "password", "clientsecret", "secret", "token"}
)
_BEARER_RE = re.compile(r"(?i)(bearer\s+)[A-Za-z0-9._~+/=-]+")


class FullAppStackError(RuntimeError):
    pass


def _tail(text: str, limit: int = 1200) -> str:
    value = text.strip()
    return value[-limit:] if len(value) > limit else value


def _command_text(command: list[str]) -> str:
    return " ".join(command)


def run_checked(
    command: list[str],
    *,
    cwd: Path = _ROOT,
    timeout: float | None = None,
) -> subprocess.CompletedProcess[str]:
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError as exc:
        raise FullAppStackError(f"required command not found: {command[0]}") from exc
    except subprocess.TimeoutExpired as exc:
        raise FullAppStackError(
            f"command timed out after {timeout:g}s: {_command_text(command)}"
        ) from exc
    if result.returncode != 0:
        detail = _tail(result.stderr) or _tail(result.stdout) or "no output"
        raise FullAppStackError(
            f"command failed ({result.returncode}): {_command_text(command)}\n{detail}"
        )
    return result


def require_executable(name: str) -> None:
    if shutil.which(name) is None:
        raise FullAppStackError(f"required command not found on PATH: {name}")


def require_docker_daemon() -> None:
    require_executable("docker")
    try:
        run_checked(["docker", "info"], timeout=30)
    except FullAppStackError as exc:
        raise FullAppStackError(
            "Docker is installed, but the Docker daemon is not reachable. Start "
            "Docker Desktop or Colima, confirm `docker info` succeeds, then rerun "
            "this full-app validator."
        ) from exc


def _browser_probe_ok(*, browser_command: str, timeout: float) -> bool:
    """Return whether the browser CLI answers a cheap, side-effect-free query."""
    try:
        result = subprocess.run(
            [browser_command, "pages"],
            cwd=_ROOT,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except (subprocess.TimeoutExpired, OSError):
        return False
    if result.returncode != 0:
        return False
    return "TIMEOUT" not in (result.stdout + result.stderr)


def ensure_browser_session_responsive(
    *,
    browser_command: str = BROWSER_COMMAND,
    probe_timeout: float = _BROWSER_PROBE_TIMEOUT_SECONDS,
    restart_timeout: float = _BROWSER_RESTART_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    """Make the browser automation daemon answer before any browser proof runs.

    A long-lived ``chrome-devtools-axi`` session can go stale and then answer
    every command with an MCP request timeout. Left unhandled that surfaces as
    an opaque "browser command timed out" failure of the whole live proof, when
    the actual fix is a daemon restart. Probe first, restart once, and only then
    fail — with the remediation named.
    """
    require_executable(browser_command)
    if _browser_probe_ok(browser_command=browser_command, timeout=probe_timeout):
        return {"restarted": False, "reason": "browser session already responsive"}
    subprocess.run(
        [browser_command, "stop"],
        cwd=_ROOT,
        capture_output=True,
        text=True,
        timeout=restart_timeout,
        check=False,
    )
    subprocess.run(
        [browser_command, "start"],
        cwd=_ROOT,
        capture_output=True,
        text=True,
        timeout=restart_timeout,
        check=False,
    )
    if _browser_probe_ok(browser_command=browser_command, timeout=probe_timeout):
        return {"restarted": True, "reason": "stale browser session was restarted"}
    raise FullAppStackError(
        f"{browser_command} is installed but its session is not responding, even "
        f"after a restart. Run `{browser_command} stop && {browser_command} start` "
        "manually, confirm `"
        f"{browser_command} pages` answers, then rerun this validator (or pass "
        "--skip-browser to run without the browser proofs)."
    )


def postgres_password_path(state_dir: str) -> Path:
    path = Path(state_dir)
    if not path.is_absolute():
        path = _ROOT / path
    return path / POSTGRES_PASSWORD_FILE


def ensure_postgres_password(state_dir: str) -> str:
    """Bootstrap ACTIVE_SKILLFERENCE_POSTGRES_PASSWORD the same way scripts/run_skilltree.sh
    does, so `docker compose up` works standalone without a prior manual export."""
    existing = os.environ.get(POSTGRES_PASSWORD_ENV_VAR)
    if existing:
        return existing

    password_path = postgres_password_path(state_dir)
    password_path.parent.mkdir(parents=True, exist_ok=True)
    password_path.parent.chmod(0o700)

    if password_path.is_symlink() or (
        password_path.exists() and not password_path.is_file()
    ):
        raise FullAppStackError(
            f"Postgres password path must be a regular file, not {password_path}"
        )

    stored = (
        password_path.read_text(encoding="utf-8").strip()
        if password_path.exists()
        else ""
    )
    password = stored or secrets.token_urlsafe(32)
    if not stored:
        password_path.write_text(f"{password}\n", encoding="utf-8")
    password_path.chmod(0o600)

    os.environ[POSTGRES_PASSWORD_ENV_VAR] = password
    return password


def regeneration_commands(python: str = "python") -> list[list[str]]:
    return [
        [python, "scripts/build_curriculum.py"],
        [python, "scripts/run_kernels.py"],
        [python, "scripts/export_skilltree.py"],
    ]


def bootstrap_command(
    *,
    python: str = "python",
    skilltree_url: str,
    state_dir: str,
    learner_id: str,
    skip_dependencies: bool = False,
    skip_seed_if_live_counts_ready: bool = False,
) -> list[str]:
    command = [
        python,
        "scripts/bootstrap_local_skilltree.py",
        "--base-url",
        skilltree_url,
        "--state-dir",
        state_dir,
        "--learner-id",
        learner_id,
    ]
    if skip_dependencies:
        command.append("--skip-dependencies")
    if skip_seed_if_live_counts_ready:
        command.append("--skip-seed-if-live-counts-ready")
    return command


def dependency_reconciliation_command(
    *,
    python: str = "python",
    skilltree_url: str,
    state_dir: str,
    timeout: float,
) -> list[str]:
    return [
        python,
        "scripts/reconcile_live_dependencies.py",
        "--skilltree-url",
        skilltree_url,
        "--state-dir",
        state_dir,
        "--timeout",
        str(timeout),
    ]


def dashboard_command(
    *,
    python: str = "python",
    skilltree_url: str,
    host: str,
    port: int,
    state_dir: str,
    learner_id: str,
) -> list[str]:
    return [
        python,
        "scripts/serve_learner_dashboard.py",
        "--skilltree-url",
        skilltree_url,
        "--host",
        host,
        "--port",
        str(port),
        "--local-auth",
        "--local-state-dir",
        state_dir,
        "--learner-id",
        learner_id,
    ]


def live_validation_command(
    *,
    python: str = "python",
    dashboard_url: str,
    skilltree_url: str,
    state_dir: str,
    require_live_dependencies: bool = False,
) -> list[str]:
    command = [
        python,
        "scripts/validate_live_skilltree_dashboard.py",
        "--dashboard-url",
        dashboard_url,
        "--skilltree-url",
        skilltree_url,
        "--project-root",
        str(_ROOT),
        "--local-state-dir",
        state_dir,
        "--timeout",
        str(_REQUEST_TIMEOUT_SECONDS),
        "--require-live-admin",
        "--require-figure-contracts",
    ]
    if require_live_dependencies:
        command.append("--require-live-dependencies")
    return command


def console_validation_command(
    *,
    python: str = "python",
    dashboard_url: str,
) -> list[str]:
    return [
        python,
        "scripts/validate_dashboard_console.py",
        "--dashboard-url",
        dashboard_url,
        "--require-browser",
        "--require-dashboard",
    ]


def form_login_validation_command(
    *,
    python: str = "python",
    skilltree_url: str,
    state_dir: str,
    timeout: float,
) -> list[str]:
    return [
        python,
        "scripts/validate_skilltree_form_login.py",
        "--skilltree-url",
        skilltree_url,
        "--state-dir",
        state_dir,
        "--timeout",
        str(timeout),
    ]


def _fetch_json(url: str, timeout: float) -> dict[str, Any]:
    try:
        require_http_url(url, context="full-app-stack validator")
    except NonHttpUrlError as exc:
        raise FullAppStackError(str(exc)) from exc
    request = urllib.request.Request(url, headers={"Accept": "application/json"})
    # require_http_url() above rejects non-http(s) targets.
    with urllib.request.urlopen(request, timeout=timeout) as response:  # nosec B310
        payload = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload, dict):
        raise FullAppStackError(f"{url} returned JSON that is not an object")
    return payload


def wait_for_json(url: str, *, timeout: float) -> dict[str, Any]:
    deadline = time.monotonic() + timeout
    last_error = "not reached"
    while time.monotonic() < deadline:
        try:
            return _fetch_json(url, timeout=_REQUEST_TIMEOUT_SECONDS)
        except (
            FullAppStackError,
            TimeoutError,
            urllib.error.URLError,
            urllib.error.HTTPError,
            ConnectionError,
            json.JSONDecodeError,
        ) as exc:
            last_error = str(exc)
            time.sleep(2)
    raise FullAppStackError(f"timed out waiting for {url}: {last_error}")


def start_dashboard(
    command: list[str],
    *,
    log_path: Path | None = None,
) -> subprocess.Popen[str]:
    if log_path is not None:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_file = log_path.open("a", encoding="utf-8")
        process = subprocess.Popen(
            command,
            cwd=_ROOT,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            text=True,
            start_new_session=True,
        )
        log_file.close()
        return process
    return subprocess.Popen(
        command,
        cwd=_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def stop_dashboard_process(
    process: subprocess.Popen[str],
    *,
    timeout: float = _DASHBOARD_STOP_SECONDS,
) -> bool:
    if process.poll() is not None:
        return True
    process.terminate()
    try:
        process.wait(timeout=timeout)
        return True
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=timeout)
        return False


def _process_output(process: subprocess.Popen[str]) -> str:
    if process.stdout is None and process.stderr is None:
        return ""
    stdout, stderr = (
        process.communicate(timeout=1) if process.poll() is not None else ("", "")
    )
    return "\n".join(part for part in (stdout, stderr) if part).strip()


def dashboard_runtime_paths(state_dir: str) -> tuple[Path, Path]:
    path = Path(state_dir)
    if not path.is_absolute():
        path = _ROOT / path
    return path / DASHBOARD_PID_FILE, path / DASHBOARD_LOG_FILE


def record_dashboard_process(*, state_dir: str, pid: int) -> tuple[Path, Path]:
    pid_path, log_path = dashboard_runtime_paths(state_dir)
    pid_path.parent.mkdir(parents=True, exist_ok=True)
    pid_path.write_text(f"{pid}\n", encoding="utf-8")
    log_path.touch(exist_ok=True)
    return pid_path, log_path


def wait_for_dashboard(
    process: subprocess.Popen[str],
    *,
    dashboard_url: str,
    timeout: float,
) -> dict[str, Any]:
    health_url = f"{dashboard_url.rstrip('/')}/healthz"
    deadline = time.monotonic() + timeout
    last_error = "not reached"
    while time.monotonic() < deadline:
        if process.poll() is not None:
            output = _tail(_process_output(process)) or "no dashboard output"
            raise FullAppStackError(
                f"dashboard process exited before /healthz became ready\n{output}"
            )
        try:
            return _fetch_json(health_url, timeout=_REQUEST_TIMEOUT_SECONDS)
        except (
            FullAppStackError,
            TimeoutError,
            urllib.error.URLError,
            urllib.error.HTTPError,
            ConnectionError,
            json.JSONDecodeError,
        ) as exc:
            last_error = str(exc)
            time.sleep(1)
    raise FullAppStackError(f"timed out waiting for {health_url}: {last_error}")


def proof_summary(
    *,
    skilltree_url: str,
    dashboard_url: str,
    skilltree_status: dict[str, Any],
    dashboard_health: dict[str, Any],
    live_validation: dict[str, Any],
    browser_console_stdout: str | None,
    raw_skilltree_login: dict[str, Any] | None,
    kept_running: bool,
    dashboard_pid: int | None,
    dashboard_pid_path: Path | None = None,
    dashboard_log_path: Path | None = None,
    dependency_reconciliation: dict[str, Any] | None = None,
    app_ready: bool = False,
) -> dict[str, Any]:
    checks = [live_validation, dashboard_health]
    if raw_skilltree_login is not None:
        checks.append(raw_skilltree_login)
    if dependency_reconciliation is not None:
        checks.append(dependency_reconciliation)
    ok = all(check.get("ok") is not False for check in checks)
    if (
        dependency_reconciliation is not None
        and dependency_reconciliation.get("complete") is False
    ):
        ok = False
    return {
        "ok": ok,
        "skilltreeUrl": skilltree_url,
        "dashboardUrl": dashboard_url,
        "skilltreeStatus": skilltree_status,
        "dashboardHealth": dashboard_health,
        "counts": live_validation.get("counts", {}),
        "artifacts": live_validation.get("artifacts", {}),
        "courseMaterials": live_validation.get("courseMaterials", {}),
        "figureContracts": live_validation.get("figureContracts", {"checked": False}),
        "liveAdminProject": live_validation.get("liveAdminProject", {}),
        "liveDependencies": live_validation.get("liveDependencies", {}),
        "dependencyReconciliation": dependency_reconciliation or {"checked": False},
        "mode": "app-ready" if app_ready else "full-parity",
        "browserConsole": {
            "checked": browser_console_stdout is not None,
            "summary": (browser_console_stdout or "skipped by --skip-browser").strip(),
        },
        "rawSkillTreeLogin": raw_skilltree_login
        if raw_skilltree_login is not None
        else {"checked": False, "reason": "skipped by --skip-browser"},
        "keptRunning": kept_running,
        "dashboardPid": dashboard_pid if kept_running else None,
        "dashboardPidPath": str(dashboard_pid_path)
        if kept_running and dashboard_pid_path
        else None,
        "dashboardLogPath": str(dashboard_log_path)
        if kept_running and dashboard_log_path
        else None,
    }


def write_proof_artifact(proof: dict[str, Any], path: Path) -> Path:
    """Persist a deterministic, redacted full-stack proof for release review."""
    safe = _redact_proof_value(proof)
    if not isinstance(safe, dict):  # pragma: no cover - defensive type narrowing
        raise FullAppStackError("full-app proof must be a JSON object")
    safe["proofVersion"] = 1
    return write_json_artifact(Path(path), safe, ensure_ascii=False)


def _redact_proof_value(value: Any, *, key: str = "") -> Any:
    normalized_key = key.replace("_", "").replace("-", "").lower()
    if normalized_key in _SENSITIVE_PROOF_KEYS:
        return "[REDACTED]"
    if isinstance(value, dict):
        return {
            str(child_key): _redact_proof_value(child_value, key=str(child_key))
            for child_key, child_value in value.items()
        }
    if isinstance(value, list):
        return [_redact_proof_value(item) for item in value]
    if isinstance(value, str):
        return _BEARER_RE.sub(r"\1[REDACTED]", value)
    return value


def _dashboard_url_from_args(args: argparse.Namespace) -> str:
    if args.dashboard_url:
        return args.dashboard_url.rstrip("/")
    return f"http://{args.host}:{args.port}"


def _json_object_from_stdout(
    result: subprocess.CompletedProcess[str], *, label: str
) -> dict[str, Any]:
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise FullAppStackError(
            f"{label} did not emit JSON:\n" + _tail(result.stdout)
        ) from exc
    if not isinstance(payload, dict):
        raise FullAppStackError(f"{label} emitted non-object JSON")
    return payload


def validate_full_app_stack(args: argparse.Namespace) -> dict[str, Any]:
    skilltree_url = args.skilltree_url.rstrip("/")
    dashboard_url = _dashboard_url_from_args(args)
    state_dir = str(Path(args.state_dir))
    proof_path = Path(
        getattr(args, "proof_path", "")
        or (Path(state_dir) / "full_app_stack_proof.json")
    )

    require_executable("uv")
    require_docker_daemon()
    ensure_postgres_password(state_dir)
    run_checked(["docker", "compose", "up", "-d"], timeout=args.timeout)
    skilltree_status = wait_for_json(
        f"{skilltree_url}/public/status",
        timeout=args.timeout,
    )

    if not args.skip_regenerate:
        for command in regeneration_commands():
            run_checked(["uv", "run", *command], timeout=args.timeout)

    run_checked(
        [
            "uv",
            "run",
            *bootstrap_command(
                skilltree_url=skilltree_url,
                state_dir=state_dir,
                learner_id=args.learner_id,
                skip_dependencies=True,
                skip_seed_if_live_counts_ready=True,
            ),
        ],
        timeout=args.timeout,
    )

    dependency_reconciliation: dict[str, Any] | None = None
    if not args.app_ready:
        dependency_result = run_checked(
            [
                "uv",
                "run",
                *dependency_reconciliation_command(
                    skilltree_url=skilltree_url,
                    state_dir=state_dir,
                    timeout=args.timeout,
                ),
            ],
            timeout=args.timeout,
        )
        dependency_reconciliation = _json_object_from_stdout(
            dependency_result, label="dependency reconciler"
        )

    pid_path, log_path = dashboard_runtime_paths(state_dir)
    dashboard = start_dashboard(
        [
            "uv",
            "run",
            *dashboard_command(
                skilltree_url=skilltree_url,
                host=args.host,
                port=args.port,
                state_dir=state_dir,
                learner_id=args.learner_id,
            ),
        ],
        log_path=log_path if args.keep_running else None,
    )
    try:
        dashboard_health = wait_for_dashboard(
            dashboard,
            dashboard_url=dashboard_url,
            timeout=args.timeout,
        )
        live_result = run_checked(
            [
                "uv",
                "run",
                *live_validation_command(
                    dashboard_url=dashboard_url,
                    skilltree_url=skilltree_url,
                    state_dir=state_dir,
                    require_live_dependencies=not args.app_ready,
                ),
            ],
            timeout=args.timeout,
        )
        live_validation = _json_object_from_stdout(
            live_result, label="live dashboard validator"
        )

        browser_stdout: str | None = None
        raw_skilltree_login: dict[str, Any] | None = None
        if not args.skip_browser:
            ensure_browser_session_responsive()
            raw_login_result = run_checked(
                [
                    "uv",
                    "run",
                    *form_login_validation_command(
                        skilltree_url=skilltree_url,
                        state_dir=state_dir,
                        timeout=_FORM_LOGIN_TIMEOUT_SECONDS,
                    ),
                ],
                timeout=args.timeout,
            )
            raw_skilltree_login = _json_object_from_stdout(
                raw_login_result, label="raw SkillTree FORM login validator"
            )
            browser_result = run_checked(
                [
                    "uv",
                    "run",
                    *console_validation_command(dashboard_url=dashboard_url),
                ],
                timeout=args.timeout,
            )
            browser_stdout = browser_result.stdout

        proof = proof_summary(
            skilltree_url=skilltree_url,
            dashboard_url=dashboard_url,
            skilltree_status=skilltree_status,
            dashboard_health=dashboard_health,
            live_validation=live_validation,
            browser_console_stdout=browser_stdout,
            raw_skilltree_login=raw_skilltree_login,
            kept_running=args.keep_running,
            dashboard_pid=dashboard.pid,
            dashboard_pid_path=pid_path,
            dashboard_log_path=log_path,
            dependency_reconciliation=dependency_reconciliation,
            app_ready=args.app_ready,
        )
        if proof["ok"] is not True:
            raise FullAppStackError(
                "full-app validation emitted a non-success proof summary"
            )
        proof["proofPath"] = str(proof_path)
        write_proof_artifact(proof, proof_path)
        return proof
    finally:
        if args.keep_running and dashboard.poll() is None:
            record_dashboard_process(state_dir=state_dir, pid=dashboard.pid)
        elif not args.keep_running:
            stop_dashboard_process(dashboard)
