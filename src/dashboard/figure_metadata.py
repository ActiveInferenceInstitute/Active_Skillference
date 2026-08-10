from __future__ import annotations

import json
from pathlib import Path

from src.artifacts.json_io import JsonArtifactError, read_json_array


def load_figure_metadata(project_root: Path) -> dict[str, dict[str, object]]:
    """Return registry metadata keyed by local figure filename, tolerating stale output."""
    path = project_root / "output" / "figures" / "figure_registry.json"
    if not path.exists():
        return {}
    try:
        payload = read_json_array(path)
    except (OSError, json.JSONDecodeError, JsonArtifactError):
        return {}
    metadata: dict[str, dict[str, object]] = {}
    allowed_fields = {
        "accessibility_note",
        "alt_text",
        "caption",
        "chart_family",
        "claim_tokens",
        "data_grain",
        "data_source",
        "data_sources",
        "encoding",
        "false_certification_risk",
        "failure_mode",
        "generated_by",
        "interpretation_boundary",
        "label",
        "mobile_note",
        "mobile_read",
        "non_color_encoding",
        "palette_policy",
        "palette_roots",
        "qa_role",
        "question",
        "subtitle",
        "static_read",
        "table_companion_id",
        "takeaway",
        "visual_grammar",
    }
    for row in payload:
        if not isinstance(row, dict):
            continue
        filename = row.get("filename")
        if not isinstance(filename, str) or not filename.endswith(".png"):
            continue
        metadata[filename] = {
            key: value for key, value in row.items() if key in allowed_fields
        }
    return metadata
