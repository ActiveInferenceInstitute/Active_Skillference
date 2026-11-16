"""Atomic publication preserves the previous complete artifact after real I/O failure."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from src.artifacts.json_io import write_json_artifact


@pytest.mark.skipif(os.name != "posix", reason="RLIMIT_FSIZE is a POSIX I/O boundary")
def test_failed_write_preserves_existing_bytes_and_cleans_temporary(tmp_path: Path) -> None:
    artifact = tmp_path / "artifact.json"
    original = b'{"generation": "previous"}\n'
    artifact.write_bytes(original)
    program = """
import errno
from pathlib import Path
import resource
import signal
import sys
from src.artifacts.json_io import write_json_artifact
signal.signal(signal.SIGXFSZ, signal.SIG_IGN)
resource.setrlimit(resource.RLIMIT_FSIZE, (1024, 1024))
try:
    write_json_artifact(Path(sys.argv[1]), {"data": "x" * 16384})
except OSError as error:
    if error.errno != errno.EFBIG:
        raise
else:
    raise AssertionError("expected the actual filesystem write to exceed RLIMIT_FSIZE")
"""
    result = subprocess.run(
        [sys.executable, "-B", "-c", program, str(artifact)],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True, text=True, timeout=15, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert artifact.read_bytes() == original
    assert sorted(path.name for path in tmp_path.iterdir()) == [artifact.name]


def test_atomic_replacement_preserves_content_format_and_existing_mode(tmp_path: Path) -> None:
    artifact = tmp_path / "artifact.json"
    artifact.write_text('{"old": true}\n', encoding="utf-8")
    artifact.chmod(0o640)
    write_json_artifact(artifact, {"z": "λ", "a": [1, 2]}, ensure_ascii=False)
    assert artifact.read_text(encoding="utf-8") == json.dumps(
        {"z": "λ", "a": [1, 2]}, indent=2, sort_keys=True, ensure_ascii=False
    ) + "\n"
    assert artifact.stat().st_mode & 0o777 == 0o640
    assert sorted(path.name for path in tmp_path.iterdir()) == [artifact.name]
