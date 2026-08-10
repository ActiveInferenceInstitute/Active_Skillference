from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from src.artifacts.json_io import JsonArtifactError, read_json_array

from .style import FigureRegistryError


def _lane_label(lane: str) -> str:
    words = lane.replace("_", " ").split()
    if len(words) <= 2:
        return " ".join(words)
    return " ".join(words[:2]) + "\n" + " ".join(words[2:])


def _section_label(filename: str) -> str:
    stem = Path(filename).stem
    if len(stem) > 3 and stem[:2].isdigit() and stem[2] == "_":
        stem = stem[3:]
    return stem.replace("_", " ")


def _int_from_mapping(value: object, key: str) -> int:
    if not isinstance(value, Mapping):
        return 0
    return _coerce_int(value.get(key))


def _resolve_cover_figure_count(
    roadmap_metrics: Mapping[str, Any],
    *,
    figure_count: int | None,
    figure_registry_path: Path | None,
) -> int:
    if figure_registry_path is not None:
        registry_count = _figure_registry_file_count(figure_registry_path)
        if figure_count is not None and figure_count != registry_count:
            raise FigureRegistryError(
                "cover figure count disagrees with figure registry: "
                f"{figure_count} != {registry_count}"
            )
        return registry_count
    if figure_count is not None:
        return _require_positive_int(figure_count, "figure_count")
    if "figures" not in roadmap_metrics:
        raise FigureRegistryError(
            "cover figure count requires project.live_metrics.figures or a registry path"
        )
    return _require_positive_int(
        roadmap_metrics["figures"], "project.live_metrics.figures"
    )


def _figure_registry_file_count(path: Path) -> int:
    path = Path(path)
    try:
        payload = read_json_array(path)
    except FileNotFoundError as exc:
        raise FigureRegistryError(f"figure registry is missing: {path}") from exc
    except json.JSONDecodeError as exc:
        raise FigureRegistryError(f"figure registry is not valid JSON: {path}") from exc
    except JsonArtifactError as exc:
        raise FigureRegistryError(
            f"figure registry must be a JSON list: {path}"
        ) from exc
    missing_files: list[str] = []
    seen: set[str] = set()
    for index, row in enumerate(payload, start=1):
        if not isinstance(row, Mapping):
            raise FigureRegistryError(f"figure registry row {index} must be an object")
        filename = row.get("filename")
        if not isinstance(filename, str) or not filename.endswith(".png"):
            raise FigureRegistryError(
                f"figure registry row {index} filename must be a PNG string"
            )
        if filename in seen:
            raise FigureRegistryError(
                f"duplicate figure registry filename {filename!r}"
            )
        seen.add(filename)
        if not (path.parent / filename).is_file():
            missing_files.append(filename)
    if missing_files:
        raise FigureRegistryError(
            "figure registry references missing files: " + ", ".join(missing_files)
        )
    return len(payload)


def _require_positive_int(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise FigureRegistryError(f"{name} must be a positive integer")
    return value


def _coerce_int(value: object) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    return 0
