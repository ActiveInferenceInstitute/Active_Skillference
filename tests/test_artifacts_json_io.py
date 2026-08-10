from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.artifacts.json_io import (
    JsonArtifactError,
    read_json_array,
    read_json_object,
    write_json_artifact,
)


def test_json_artifact_helpers_round_trip_objects_and_arrays(tmp_path: Path) -> None:
    object_path = write_json_artifact(
        tmp_path / "nested" / "object.json", {"b": 2, "a": 1}
    )
    array_path = write_json_artifact(tmp_path / "array.json", [{"value": "ok"}])

    assert object_path.read_text(encoding="utf-8") == '{\n  "a": 1,\n  "b": 2\n}\n'
    assert read_json_object(object_path) == {"a": 1, "b": 2}
    assert read_json_array(array_path) == [{"value": "ok"}]


def test_json_artifact_helpers_reject_wrong_top_level_shape(tmp_path: Path) -> None:
    object_path = tmp_path / "object.json"
    array_path = tmp_path / "array.json"
    object_path.write_text(json.dumps({"ok": True}), encoding="utf-8")
    array_path.write_text(json.dumps([1, 2, 3]), encoding="utf-8")

    with pytest.raises(JsonArtifactError, match="JSON object"):
        read_json_object(array_path)
    with pytest.raises(JsonArtifactError, match="JSON list"):
        read_json_array(object_path)


def test_json_artifact_helpers_propagate_invalid_json(tmp_path: Path) -> None:
    path = tmp_path / "broken.json"
    path.write_text("{not json", encoding="utf-8")

    with pytest.raises(json.JSONDecodeError):
        read_json_object(path)


def test_json_artifact_writer_can_preserve_non_ascii_text(tmp_path: Path) -> None:
    path = write_json_artifact(
        tmp_path / "unicode.json",
        {"symbol": "∝"},
        ensure_ascii=False,
    )

    assert '"symbol": "∝"' in path.read_text(encoding="utf-8")
