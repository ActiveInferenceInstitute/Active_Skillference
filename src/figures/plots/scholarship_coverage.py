"""Scholarship figure: coverage."""

from __future__ import annotations

import os
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import matplotlib
import numpy as np

os.environ.setdefault("MPLBACKEND", "Agg")
matplotlib.use("Agg")

import matplotlib.pyplot as plt

from src.scholarship.coverage import EXPECTED_LANES

from .registry_helpers import (
    _coerce_int,
    _int_from_mapping,
    _lane_label,
    _section_label,
)
from .style import (
    _ALERT,
    _COLOR_FAMILIES,
    _FONT_SMALL,
    _MUTED,
    _OK,
    _add_panel_label,
    _metric_card,
    _prepare_path,
    _save_figure,
    _short_label,
    _style_axis,
)


def plot_scholarship_coverage(
    audit: Mapping[str, Any],
    path: Path,
) -> Path:
    """Render citation coverage by scholarship lane and manuscript section."""
    path = _prepare_path(path)
    lanes = audit.get("lanes", {})
    sections = audit.get("sections", [])
    summary = audit.get("summary", {})
    if not isinstance(lanes, Mapping):
        lanes = {}
    if not isinstance(sections, list):
        sections = []
    if not isinstance(summary, Mapping):
        summary = {}

    lane_ids = list(EXPECTED_LANES)
    lane_labels = [_lane_label(lane) for lane in lane_ids]
    cited_counts = [
        _int_from_mapping(lanes.get(lane, {}), "citedSources") for lane in lane_ids
    ]
    total_counts = [
        _int_from_mapping(lanes.get(lane, {}), "totalSources") for lane in lane_ids
    ]
    sources = audit.get("sources", {})
    if not isinstance(sources, Mapping):
        sources = {}
    pre1800_by_lane: dict[str, int] = {lane: 0 for lane in lane_ids}
    for source_key, source in sources.items():
        if not isinstance(source, Mapping) or source.get("kind") != "historical":
            continue
        key_text = str(source_key)
        year_match = re.search(r"(?<!\d)(\d{3,4})(?!\d)", key_text)
        is_pre1800 = key_text.startswith(("alhazen", "aristotle_", "quintilian")) or (
            year_match is not None and int(year_match.group(1)) < 1800
        )
        if not is_pre1800:
            continue
        lane = str(source.get("lane", ""))
        if lane in pre1800_by_lane:
            pre1800_by_lane[lane] += 1
    pre1800_counts = [pre1800_by_lane[lane] for lane in lane_ids]
    pre1800_source_count = sum(pre1800_counts)
    pre1800_lane_count = sum(1 for count in pre1800_counts if count > 0)
    cited_source_count = _int_from_mapping(summary, "citedSources")
    matrix_source_count = _int_from_mapping(summary, "matrixSources")
    issue_count = _int_from_mapping(summary, "issueCount")
    unused_count = _int_from_mapping(summary, "unusedMatrixEntries")
    uncited_bib_count = _int_from_mapping(summary, "uncitedBibEntries")
    cited_section_count = _int_from_mapping(summary, "sectionsWithCitations")
    expected_lane_count = _int_from_mapping(summary, "expectedLanes")
    missing_lane_count = _int_from_mapping(summary, "missingLanes")
    invalid_source_count = _int_from_mapping(summary, "invalidSourceRows")
    cited_lane_count = sum(1 for count in cited_counts if count > 0)
    orphan_count = unused_count + uncited_bib_count

    section_labels: list[str] = []
    matrix = np.zeros((len(sections), len(lane_ids)), dtype=int)
    for row, section in enumerate(sections):
        if not isinstance(section, Mapping):
            continue
        section_labels.append(
            _short_label(
                _section_label(str(section.get("section", f"s{row}"))), width=36
            )
        )
        lane_counts = section.get("laneCounts", {})
        if not isinstance(lane_counts, Mapping):
            lane_counts = {}
        for col, lane in enumerate(lane_ids):
            matrix[row, col] = _coerce_int(lane_counts.get(lane))

    fig = plt.figure(figsize=(14.8, 7.2), constrained_layout=True)
    grid = fig.add_gridspec(
        2,
        2,
        height_ratios=[0.34, 1.0],
        width_ratios=[0.95, 1.7],
    )
    summary_ax = fig.add_subplot(grid[0, :])
    left = fig.add_subplot(grid[1, 0])
    right = fig.add_subplot(grid[1, 1])
    summary_ax.set_xlim(0, 1)
    summary_ax.set_ylim(0, 1)
    summary_ax.axis("off")
    summary_ax.set_title(
        "Scholarship coverage is a source-role contract, not a citation count"
    )
    summary_cards = [
        (
            f"{cited_source_count}/{matrix_source_count}",
            "cited and matrixed",
            _COLOR_FAMILIES["blue"]["base"],
        ),
        (
            f"{cited_lane_count}/{expected_lane_count}",
            "lanes represented",
            _OK if missing_lane_count == 0 else _ALERT,
        ),
        (
            str(cited_section_count),
            "sections with citations",
            _COLOR_FAMILIES["sky"]["base"],
        ),
        (
            str(issue_count + invalid_source_count + orphan_count),
            "open audit items",
            _OK if issue_count + invalid_source_count + orphan_count == 0 else _ALERT,
        ),
    ]
    for index, (value, label, color) in enumerate(summary_cards):
        _metric_card(
            summary_ax,
            x=0.02 + index * 0.245,
            y=0.16,
            width=0.22,
            height=0.58,
            value=value,
            label=label,
            color=color,
        )
    summary_ax.text(
        0.02,
        0.05,
        (
            f"{unused_count} unused matrix rows; {uncited_bib_count} uncited BibTeX keys; "
            f"{missing_lane_count} missing lanes."
        ),
        transform=summary_ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=_FONT_SMALL,
        color=_MUTED,
    )
    if pre1800_source_count:
        summary_ax.text(
            0.98,
            0.05,
            f"pre-1800 layer: {pre1800_source_count} sources across {pre1800_lane_count} lanes (ancient/medieval to 18th c.)",
            transform=summary_ax.transAxes,
            ha="right",
            va="bottom",
            fontsize=_FONT_SMALL,
            color=_COLOR_FAMILIES["gold"]["dark"],
            fontweight="bold",
        )

    y_pos = np.arange(len(lane_ids))
    left.barh(
        y_pos,
        total_counts,
        color="#d1d5db",
        height=0.72,
        label="matrixed sources",
    )
    left.barh(
        y_pos,
        cited_counts,
        color="#0072B2",
        height=0.48,
        label="cited in manuscript",
    )
    left.barh(
        y_pos,
        pre1800_counts,
        color=_COLOR_FAMILIES["gold"]["base"],
        height=0.20,
        label="pre-1800 context",
        zorder=3,
    )
    left.set_yticks(y_pos)
    left.set_yticklabels(lane_labels, fontsize=_FONT_SMALL)
    left.invert_yaxis()
    left.set_xlabel("sources")
    _add_panel_label(
        left,
        "A",
        f"Scholarship source coverage by lane ({cited_source_count}/{matrix_source_count})",
    )
    left.legend(
        frameon=False,
        fontsize=_FONT_SMALL,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.16),
        ncol=3,
    )
    max_total = max(total_counts, default=0)
    for y, cited, total, pre1800 in zip(
        y_pos, cited_counts, total_counts, pre1800_counts, strict=True
    ):
        left.text(
            max(total, cited) + max(0.3, max_total * 0.03),
            float(y),
            f"{cited}/{total}",
            va="center",
            fontsize=_FONT_SMALL,
            color="#111827",
        )
        if pre1800:
            left.text(
                max(0.4, pre1800 + max_total * 0.015),
                float(y) + 0.24,
                f"{pre1800} pre-1800",
                va="center",
                fontsize=_FONT_SMALL,
                color=_COLOR_FAMILIES["gold"]["dark"],
                fontweight="bold",
            )
    _style_axis(left, grid_axis="x", hide=("top", "right", "left"))

    if matrix.size:
        image = right.imshow(matrix, cmap="YlGnBu", aspect="auto")
        right.set_xticks(np.arange(len(lane_ids)))
        right.set_xticklabels(
            lane_labels, rotation=45, ha="right", fontsize=_FONT_SMALL
        )
        right.set_yticks(np.arange(len(section_labels)))
        right.set_yticklabels(section_labels, fontsize=_FONT_SMALL)
        _add_panel_label(
            right,
            "B",
            f"Citation lanes by section ({cited_section_count} sections)",
        )
        right.set_xlabel("scholarship lane")
        right.set_ylabel("section")
        right.set_xticks(np.arange(-0.5, len(lane_ids), 1), minor=True)
        right.set_yticks(np.arange(-0.5, len(section_labels), 1), minor=True)
        right.grid(which="minor", color="white", linewidth=1.0)
        right.tick_params(which="minor", bottom=False, left=False)
        max_value = int(matrix.max()) if matrix.size else 0
        for row in range(matrix.shape[0]):
            for col in range(matrix.shape[1]):
                cell_value = int(matrix[row, col])
                if cell_value == 0:
                    continue
                colour = (
                    "white"
                    if max_value and cell_value > max_value * 0.55
                    else "#111827"
                )
                right.text(
                    col,
                    row,
                    str(cell_value),
                    ha="center",
                    va="center",
                    color=colour,
                    fontsize=_FONT_SMALL,
                    fontweight="bold",
                )
        cbar = fig.colorbar(image, ax=right, fraction=0.046, pad=0.02)
        cbar.set_label("citations")
    else:
        right.axis("off")
        right.text(
            0.5,
            0.5,
            "No manuscript citations found\n"
            f"{unused_count} unused matrix rows, {uncited_bib_count} uncited BibTeX keys",
            ha="center",
            va="center",
            fontsize=11,
        )

    return _save_figure(
        fig,
        path,
        note="Scholarship figure is generated from citation, BibTeX and source-role audits.",
    )
