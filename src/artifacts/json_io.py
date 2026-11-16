from __future__ import annotations

import json
import os
import stat
import tempfile
from pathlib import Path
from typing import Any, cast


class JsonArtifactError(ValueError):
    pass


def read_json_object(path: Path) -> dict[str, Any]:
    payload = _read_json(path)
    if not isinstance(payload, dict):
        raise JsonArtifactError(f"{path} must contain a JSON object")
    return cast(dict[str, Any], payload)


def read_json_array(path: Path) -> list[Any]:
    payload = _read_json(path)
    if not isinstance(payload, list):
        raise JsonArtifactError(f"{path} must contain a JSON list")
    return cast(list[Any], payload)


def write_json_artifact(
    path: Path,
    payload: object,
    *,
    ensure_ascii: bool = True,
) -> Path:
    path = Path(path)
    content = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=ensure_ascii) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = stat.S_IMODE(path.stat().st_mode) if path.exists() else None
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent,
            prefix=f".{path.name}.", suffix=".tmp", delete=False,
        ) as stream:
            temporary = Path(stream.name)
            stream.write(content)
        if mode is not None:
            temporary.chmod(mode)
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return path


def _read_json(path: Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))
