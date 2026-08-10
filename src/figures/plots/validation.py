from __future__ import annotations

import os
import textwrap
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import matplotlib
import numpy as np

os.environ.setdefault("MPLBACKEND", "Agg")
matplotlib.use("Agg")

import matplotlib.pyplot as plt

from src.curriculum.graph import CurriculumGraph
from src.provenance.claims import ClaimRegistry

from .registry_helpers import _int_from_mapping
from .style import (
    _FONT_SMALL,
    _MUTED,
    _add_axis_subtitle,
    _add_panel_label,
    _prepare_path,
    _save_figure,
    _style_axis,
)
from .validation_data import _VALIDATION_SURFACE_BINDINGS, _VALIDATION_SURFACE_COLUMNS


def validation_surface_matrix(
    root: Path | None = None,
) -> tuple[list[str], list[str], np.ndarray]:
    """Derive the validation-surface matrix from real validator/test file existence.

    Returns ``(rows, columns, matrix)`` where ``matrix[r][c]`` is 1 only when every file
    bound to that cell exists under ``root``; ``None`` bindings are 0 (n/a). Deleting a
    bound validator flips its cell, so the rendered figure cannot certify a gate that is
    not there.
    """
    base = root or Path(__file__).resolve().parents[3]
    rows = [label for label, _ in _VALIDATION_SURFACE_BINDINGS]
    grid: list[list[int]] = []
    for _label, cells in _VALIDATION_SURFACE_BINDINGS:
        grid.append(
            [
                1 if cell and all((base / name).is_file() for name in cell) else 0
                for cell in cells
            ]
        )
    return rows, list(_VALIDATION_SURFACE_COLUMNS), np.array(grid, dtype=int)


def plot_validation_surface_matrix(
    graph: CurriculumGraph,
    registry: ClaimRegistry,
    audit: Mapping[str, Any],
    path: Path,
    *,
    figure_count: int,
) -> Path:
    """Render the cross-surface validation matrix and live evidence counts."""
    path = _prepare_path(path)
    summary = audit.get("summary", {})
    if not isinstance(summary, Mapping):
        summary = {}

    rows, columns, matrix = validation_surface_matrix()
    row_totals = matrix.sum(axis=1)
    column_totals = matrix.sum(axis=0)

    live_counts = [
        ("skills", len(graph.skills)),
        ("subjects", len(graph.subjects)),
        ("edges", len(graph.prerequisite_edges())),
        ("questions", sum(len(skill.assessments) for skill in graph.skills)),
        ("claims", len(registry)),
        ("cited sources", _int_from_mapping(summary, "citedSources")),
        ("figures", figure_count),
    ]

    fig, (left, right) = plt.subplots(
        1,
        2,
        figsize=(15.2, 8.2),
        gridspec_kw={"width_ratios": [1.55, 1.0]},
        constrained_layout=True,
    )

    image = left.imshow(matrix, cmap="YlGnBu", vmin=0, vmax=1, aspect="auto")
    left.set_xticks(np.arange(len(columns)))
    left.set_xticklabels(
        [
            f"{textwrap.fill(column, width=11)}\n{int(total)}/{len(rows)}"
            for column, total in zip(columns, column_totals, strict=True)
        ],
        fontsize=_FONT_SMALL,
    )
    left.set_yticks(np.arange(len(rows)))
    left.set_yticklabels(
        [
            f"{row}\n{int(total)}/{len(columns)} bound"
            for row, total in zip(rows, row_totals, strict=True)
        ],
        fontsize=_FONT_SMALL,
    )
    _add_panel_label(left, "A", "Validation gates by artifact/release surface")
    _add_axis_subtitle(
        left,
        textwrap.fill(
            "Bound means the named validator/test file exists; row/column labels show bound totals.",
            width=70,
        ),
        y=-0.2,
    )
    left.set_xticks(np.arange(-0.5, len(columns), 1), minor=True)
    left.set_yticks(np.arange(-0.5, len(rows), 1), minor=True)
    left.grid(which="minor", color="white", linewidth=1.2)
    left.tick_params(which="minor", bottom=False, left=False)
    for row in range(matrix.shape[0]):
        for col in range(matrix.shape[1]):
            value = int(matrix[row, col])
            left.text(
                col,
                row,
                "bound" if value else "n/a",
                ha="center",
                va="center",
                color="white" if value else "#111827",
                fontsize=_FONT_SMALL,
                fontweight="bold" if value else "normal",
            )
    cbar = fig.colorbar(image, ax=left, fraction=0.046, pad=0.02, ticks=[0, 1])
    cbar.ax.set_yticklabels(["n/a", "bound"])
    left.text(
        0.02,
        -0.31,
        textwrap.fill(
            "Legend: blue bound cells are file-backed; white n/a cells are deliberate scope boundaries, not failures.",
            width=82,
        ),
        transform=left.transAxes,
        ha="left",
        va="top",
        fontsize=_FONT_SMALL,
        color=_MUTED,
    )

    labels = [label for label, _ in live_counts]
    counts = np.array([count for _, count in live_counts], dtype=float)
    y_pos = np.arange(len(labels))
    bars = right.barh(y_pos, counts, color="#0072B2")
    right.set_yticks(y_pos)
    right.set_yticklabels(labels, fontsize=_FONT_SMALL)
    right.invert_yaxis()
    right.set_xlabel("live count")
    _add_panel_label(right, "B", "Evidence counts emitted by the build")
    _add_axis_subtitle(
        right,
        textwrap.fill(
            "Counts are live generated totals; they do not certify learner outcomes.",
            width=54,
        ),
        y=-0.16,
    )
    max_count = float(counts.max()) if counts.size else 0.0
    for bar, count in zip(bars, counts, strict=True):
        right.text(
            bar.get_width() + max(1.0, max_count * 0.025),
            bar.get_y() + bar.get_height() / 2,
            f"{int(count)}",
            va="center",
            fontsize=_FONT_SMALL,
        )
    right.set_xlim(0, max_count * 1.22 if max_count else 1)
    _style_axis(right, grid_axis="x", hide=("top", "right", "left"))

    return _save_figure(
        fig,
        path,
        note="Bound cells are derived from real validator/test file presence; n/a is not a failure.",
    )


def plot_scientific_evidence_matrix(
    claim_support_audit: Mapping[str, Any],
    path: Path,
) -> Path:
    """Render anchored manuscript claims by evidence type and required evidence class."""
    path = _prepare_path(path)
    rows = claim_support_audit.get("rows", [])
    if not isinstance(rows, list):
        rows = []
    claim_types = [
        "computed",
        "descriptive_count",
        "simulation",
        "literature",
        "scope_limit",
        "delivery",
        "visual",
    ]
    evidence_classes = [
        "claimTokens",
        "variables",
        "citations",
        "figures",
        "validators",
        "limitationMarkers",
    ]
    matrix = np.zeros((len(claim_types), len(evidence_classes)), dtype=int)
    row_counts = np.zeros(len(claim_types), dtype=int)
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        claim_type = str(row.get("type", ""))
        if claim_type not in claim_types:
            continue
        row_index = claim_types.index(claim_type)
        row_counts[row_index] += 1
        for col_index, evidence_class in enumerate(evidence_classes):
            values = row.get(evidence_class, [])
            if isinstance(values, list) and values:
                matrix[row_index, col_index] += 1

    fig, (left, right) = plt.subplots(
        1,
        2,
        figsize=(12.5, 6.8),
        gridspec_kw={"width_ratios": [1.35, 0.8]},
        constrained_layout=True,
    )
    image = left.imshow(matrix, cmap="YlGnBu", aspect="auto")
    left.set_xticks(np.arange(len(evidence_classes)))
    left.set_xticklabels(
        [
            "claim\ntokens",
            "variables",
            "citations",
            "figures",
            "validators",
            "limit\nmarkers",
        ],
        fontsize=_FONT_SMALL,
    )
    left.set_yticks(np.arange(len(claim_types)))
    left.set_yticklabels(
        [item.replace("_", " ") for item in claim_types], fontsize=_FONT_SMALL
    )
    left.set_ylim(len(claim_types) - 0.5, -0.9)
    _add_panel_label(left, "A", "Scientific claims declare their evidence class")
    left.set_xlabel("required evidence class")
    left.set_ylabel("anchored claim type")
    left.set_xticks(np.arange(-0.5, len(evidence_classes), 1), minor=True)
    left.set_yticks(np.arange(-0.5, len(claim_types), 1), minor=True)
    left.grid(which="minor", color="white", linewidth=1.1)
    left.tick_params(which="minor", bottom=False, left=False)
    max_value = int(matrix.max()) if matrix.size else 0
    for row_index in range(matrix.shape[0]):
        for col_index in range(matrix.shape[1]):
            value = int(matrix[row_index, col_index])
            if value == 0:
                continue
            left.text(
                col_index,
                row_index,
                str(value),
                ha="center",
                va="center",
                color="white" if max_value and value > max_value * 0.55 else "#111827",
                fontsize=_FONT_SMALL,
                fontweight="bold",
            )
    cbar = fig.colorbar(image, ax=left, fraction=0.046, pad=0.02)
    cbar.set_label("anchored claims")

    y_pos = np.arange(len(claim_types))
    bars = right.barh(y_pos, row_counts, color="#0072B2")
    right.set_yticks(y_pos)
    right.set_yticklabels([])
    right.invert_yaxis()
    right.set_xlabel("claims")
    _add_panel_label(right, "B", "Claim-type count")
    max_count = float(row_counts.max()) if row_counts.size else 1.0
    for bar, value in zip(bars, row_counts, strict=True):
        right.text(
            bar.get_width() + max(0.2, max_count * 0.04),
            bar.get_y() + bar.get_height() / 2,
            str(int(value)),
            va="center",
            fontsize=_FONT_SMALL,
        )
    right.set_xlim(0, max(1.0, max_count * 1.35))
    _style_axis(right, grid_axis="x", hide=("top", "right", "left"))
    return _save_figure(
        fig,
        path,
        note="Evidence classes come from claim-support anchors and validator rows.",
    )
