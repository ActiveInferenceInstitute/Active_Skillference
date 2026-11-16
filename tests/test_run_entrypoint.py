"""Run the real entrypoint without fake uv/docker executables or repository writes."""

from __future__ import annotations

import os
import shutil
import stat
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("argument,code", [("--help", 0), ("--unknown", 2), ("--check", 1), ("--offline", 1)])
@pytest.mark.parametrize("existing", [False, True])
def test_argument_and_prerequisite_exits_do_not_initialize_postgres_state(
    tmp_path: Path, argument: str, code: int, existing: bool,
) -> None:
    bash = shutil.which("bash", path=os.defpath)
    if bash is None:
        pytest.skip("existing bash runtime unavailable")
    script = tmp_path / "run.sh"
    shutil.copyfile(REPO / "run.sh", script)
    programs = tmp_path / "programs"
    programs.mkdir()
    # Real system utilities make the old entropy path observable, but no uv or
    # Docker binary is admitted: --check/--offline must stop at that prerequisite.
    for name in ("dirname", "sed", "mkdir", "cat", "tr", "head", "chmod"):
        source = shutil.which(name, path=os.defpath)
        if source is None:
            pytest.skip(f"existing system utility unavailable: {name}")
        (programs / name).symlink_to(source)
    state = tmp_path / "private-state"
    password = state / "postgres_password"
    before = None
    if existing:
        state.mkdir()
        password.write_text("kept-synthetic-password\n", encoding="utf-8")
        password.chmod(0o600)
        before = (password.read_bytes(), password.stat().st_mtime_ns, stat.S_IMODE(password.stat().st_mode))
    env = {
        key: value for key, value in os.environ.items()
        if key not in {"ACTIVE_SKILLFERENCE_POSTGRES_PASSWORD", "BASH_ENV", "ENV"}
        and not key.startswith("BASH_FUNC_")
    }
    env.update(PATH=str(programs), ACTIVE_SKILLFERENCE_LOCAL_STATE_DIR=str(state))

    result = subprocess.run(
        [bash, str(script), argument], cwd=tmp_path, env=env,
        capture_output=True, text=True, timeout=5, check=False,
    )

    assert result.returncode == code, result.stdout + result.stderr
    if argument in ("--check", "--offline"):
        assert "uv is not installed" in result.stderr
    if existing:
        assert (password.read_bytes(), password.stat().st_mtime_ns, stat.S_IMODE(password.stat().st_mode)) == before
    else:
        assert not state.exists()
