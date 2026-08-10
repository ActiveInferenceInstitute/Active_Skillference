"""Scholarship figure: source map."""

from __future__ import annotations

import os
import textwrap
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import matplotlib

os.environ.setdefault("MPLBACKEND", "Agg")
matplotlib.use("Agg")

import matplotlib.pyplot as plt

from .registry_helpers import (
    _lane_label,
)
from .style import (
    _COLOR_FAMILIES,
    _FONT_SMALL,
    _INK,
    _LINE,
    _MUTED,
    _PANEL,
    _SURFACE,
    _add_axis_subtitle,
    _prepare_path,
    _save_figure,
)


def plot_open_science_source_map(
    audit: Mapping[str, Any],
    path: Path,
    *,
    course_material_index: Mapping[str, Any] | None = None,
    course_material_audit: Mapping[str, Any] | None = None,
) -> Path:
    """Render cited and linked Active Inference Institute learning sources."""
    path = _prepare_path(path)
    sources = audit.get("sources", {})
    if not isinstance(sources, Mapping):
        sources = {}
    scholarship_rows: dict[str, dict[str, str]] = {}
    keys = [
        key for key in sorted(sources) if key.startswith("activeinferenceinstitute")
    ]
    for key in keys:
        row = sources[key] if isinstance(sources[key], Mapping) else {}
        lane = str(row.get("lane", "unknown"))
        role = str(row.get("role", "support role not declared"))
        locator = str(row.get("locator", "locator missing"))
        source_label = key.replace("activeinferenceinstitute2026", "") or key
        scholarship_rows[source_label] = {
            "label": source_label,
            "lane": lane,
            "role": role,
            "locator": locator.removeprefix("url:").removeprefix("doi:"),
        }

    material_summary = (
        course_material_audit.get("summary", {})
        if isinstance(course_material_audit, Mapping)
        else {}
    )
    if not isinstance(material_summary, Mapping):
        material_summary = {}
    index_summary = (
        course_material_index.get("summary", {})
        if isinstance(course_material_index, Mapping)
        else {}
    )
    if not isinstance(index_summary, Mapping):
        index_summary = {}
    coverage = (
        course_material_index.get("coverage", {})
        if isinstance(course_material_index, Mapping)
        else {}
    )
    if not isinstance(coverage, Mapping):
        coverage = {}
    source_pointer_counts = coverage.get("sourcePointerCounts", {})
    source_skill_counts = coverage.get("sourceSkillCounts", {})
    if not isinstance(source_pointer_counts, Mapping):
        source_pointer_counts = {}
    if not isinstance(source_skill_counts, Mapping):
        source_skill_counts = {}
    material_sources = (
        course_material_index.get("sources", [])
        if isinstance(course_material_index, Mapping)
        else []
    )
    if not isinstance(material_sources, list):
        material_sources = []

    rows: list[dict[str, str]] = []
    for source in material_sources:
        if not isinstance(source, Mapping):
            continue
        source_id = str(source.get("sourceId", ""))
        title = str(source.get("title", source_id))
        repo_url = str(source.get("repoUrl", ""))
        pointer_count = int(source_pointer_counts.get(source_id, 0))
        skill_count = int(source_skill_counts.get(source_id, 0))
        if source_id == "aii_cognitive_kb":
            role = (
                f"{pointer_count:,} pinned KB pointers · {skill_count:,} skills · "
                f"{int(coverage.get('cognitiveKnowledgeBaseTopicSkills', 0)):,} "
                "topic-matched skills"
            )
            badge = "course-material KB"
            row_type = "knowledge base"
        else:
            role = f"{pointer_count:,} pinned course pointers · {skill_count:,} skills"
            badge = "course modules"
            row_type = "course source"
        if source_id == "aii_courses" and "courses" in scholarship_rows:
            lane = _lane_label(scholarship_rows["courses"]["lane"]).replace("\n", " ")
            role = f"{role}; cited lane: {lane}"
        rows.append(
            {
                "label": title.replace("Active Inference Institute ", ""),
                "lane": badge,
                "role": role,
                "locator": repo_url,
                "type": row_type,
            }
        )
    for label in ("home", "start", "website"):
        if label in scholarship_rows:
            row = scholarship_rows[label]
            rows.append(
                {
                    "label": row["label"],
                    "lane": _lane_label(row["lane"]).replace("\n", " "),
                    "role": row["role"],
                    "locator": row["locator"],
                    "type": "community row"
                    if label == "website"
                    else "scholarship row",
                }
            )

    fig, ax = plt.subplots(figsize=(12.6, 6.7), constrained_layout=True)
    ax.set_xlim(0, 1)
    ax.set_ylim(-0.75, max(4.6, len(rows) + 1.55))
    ax.axis("off")
    ax.set_title(
        "Open-science learning sources are linked, cited, and role-bounded", pad=14
    )
    _add_axis_subtitle(
        ax,
        "Ledger rows combine scholarship support with course-material pointers; counts are links, not quality scores.",
        y=0.955,
    )
    card_values = [
        (
            "material records",
            int(
                material_summary.get("materialRecords", index_summary.get("skills", 0))
            ),
        ),
        (
            "external pointers",
            int(
                material_summary.get(
                    "externalPointers", index_summary.get("externalPointers", 0)
                )
            ),
        ),
        ("KB pointers", int(source_pointer_counts.get("aii_cognitive_kb", 0))),
        ("KB topic skills", int(coverage.get("cognitiveKnowledgeBaseTopicSkills", 0))),
    ]
    card_y = len(rows) + 0.68
    for index, (label, value) in enumerate(card_values):
        x = 0.02 + index * 0.235
        ax.add_patch(
            plt.Rectangle(
                (x, card_y - 0.28),
                0.21,
                0.55,
                facecolor=_SURFACE,
                edgecolor=_LINE,
                linewidth=0.9,
            )
        )
        ax.text(x + 0.018, card_y + 0.07, f"{value:,}", fontsize=12, fontweight="bold")
        ax.text(x + 0.018, card_y - 0.13, label, fontsize=_FONT_SMALL, color=_MUTED)
    if rows:
        row_styles = {
            "knowledge base": (_COLOR_FAMILIES["olive"]["base"], "///"),
            "course source": (_COLOR_FAMILIES["blue"]["base"], "..."),
            "scholarship row": (_COLOR_FAMILIES["pink"]["base"], "\\\\\\"),
            "community row": (_COLOR_FAMILIES["gold"]["base"], "---"),
        }
        for index, row in enumerate(rows):
            y = len(rows) - index - 1
            color, hatch = row_styles.get(row["type"], (_MUTED, ""))
            ax.add_patch(
                plt.Rectangle(
                    (0.02, y - 0.34),
                    0.96,
                    0.70,
                    facecolor=_PANEL,
                    edgecolor=_LINE,
                    linewidth=0.9,
                    zorder=0,
                )
            )
            ax.add_patch(
                plt.Rectangle(
                    (0.02, y - 0.34),
                    0.018,
                    0.70,
                    facecolor=color,
                    edgecolor=color,
                    hatch=hatch,
                    linewidth=0.9,
                    zorder=1,
                )
            )
            ax.text(
                0.055,
                y + 0.13,
                row["label"],
                ha="left",
                va="center",
                fontsize=10.5,
                fontweight="bold",
            )
            ax.text(
                0.055,
                y - 0.13,
                textwrap.shorten(row["locator"], width=70, placeholder="..."),
                ha="left",
                va="center",
                fontsize=_FONT_SMALL,
                color=_MUTED,
            )
            ax.text(
                0.43,
                y + 0.13,
                row["lane"],
                ha="left",
                va="center",
                fontsize=_FONT_SMALL,
                color=_INK,
                bbox={
                    "boxstyle": "round,pad=0.22",
                    "facecolor": _SURFACE,
                    "edgecolor": _LINE,
                    "linewidth": 0.7,
                },
            )
            ax.text(
                0.43,
                y - 0.13,
                textwrap.shorten(row["role"], width=92, placeholder="..."),
                ha="left",
                va="center",
                fontsize=_FONT_SMALL,
                color=_MUTED,
            )
    else:
        ax.text(
            0.5,
            0.5,
            "No Active Inference Institute learning sources available",
            ha="center",
            va="center",
        )
    return _save_figure(
        fig,
        path,
        note=(
            "Rows are cited support pointers and pinned course-material links; no "
            "external prose is copied."
        ),
    )
