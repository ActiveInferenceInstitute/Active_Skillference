from __future__ import annotations

import json
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
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
            ensure_ascii=ensure_ascii,
        )
        + "\n",
        encoding="utf-8",
    )
    return path


def _read_json(path: Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))
