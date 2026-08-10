from __future__ import annotations

import os
import textwrap
from pathlib import Path

import matplotlib
import numpy as np

os.environ.setdefault("MPLBACKEND", "Agg")
matplotlib.use("Agg")

import matplotlib.pyplot as plt

from src.curriculum.graph import CurriculumGraph
from src.curriculum.quality import (
    audit_semantic_prerequisites,
    semantic_prerequisite_coverage,
)

from .style import (
    _ALERT,
    _COLOR_FAMILIES,
    _FONT_SMALL,
    _INK,
    _MUTED,
    _OK,
    _PALETTE,
    _add_axis_subtitle,
    _add_panel_label,
    _prepare_path,
    _save_figure,
    _style_axis,
)


def plot_validation_intent_mismatch_matrix(
    path: Path,
    *,
    figure_count: int,
    include_scholarship: bool,
    include_claim_support: bool,
    include_roadmap: bool,
) -> Path:
    """Render the mismatch classes the validation layer is meant to catch."""
    path = _prepare_path(path)
    rows = [
        (
            "missing registry entry",
            "rendered PNG absent from figure_registry.json",
            (1, 1, 1),
        ),
        (
            "missing figure file",
            "registry filename has no readable PNG output",
            (1, 1, 1),
        ),
        (
            "missing manuscript label",
            "registered label is not declared or referenced",
            (1, 1, 1),
        ),
        (
            "missing dashboard artifact",
            "registered figure is absent from the dashboard roster",
            (1, 1, 1),
        ),
        (
            "missing roadmap metric",
            "tasks.yaml omits a generated live metric",
            (1 if include_roadmap else 0, 1 if include_roadmap else 0, 0),
        ),
        (
            "stale manifest",
            "generated JSON no longer matches its source surface",
            (
                1,
                1 if include_scholarship or include_claim_support else 0,
                1 if include_claim_support else 0,
            ),
        ),
    ]
    columns = ["source-of-truth", "manuscript gate", "dashboard gate"]
    matrix = np.array([row[2] for row in rows], dtype=int)

    fig = plt.figure(figsize=(12.2, 6.2), constrained_layout=True)
    grid = fig.add_gridspec(1, 2, width_ratios=[1.35, 0.9])
    left = fig.add_subplot(grid[0, 0])
    right = fig.add_subplot(grid[0, 1])

    image = left.imshow(matrix, cmap="YlGnBu", vmin=0, vmax=1, aspect="auto")
    left.set_xticks(np.arange(len(columns)))
    left.set_xticklabels(columns, fontsize=_FONT_SMALL)
    left.set_yticks(np.arange(len(rows)))
    left.set_yticklabels([row[0] for row in rows], fontsize=_FONT_SMALL)
    left.set_ylim(len(rows) - 0.5, -1.0)
    left.set_xticks(np.arange(-0.5, len(columns), 1), minor=True)
    left.set_yticks(np.arange(-0.5, len(rows), 1), minor=True)
    left.grid(which="minor", color="white", linewidth=1.1)
    left.tick_params(which="minor", bottom=False, left=False)
    _add_panel_label(left, "A", "Mismatch classes covered by release gates")
    _add_axis_subtitle(
        left,
        "Bound cells indicate the class is checked by the named source or validator.",
    )
    for row_index in range(matrix.shape[0]):
        for col_index in range(matrix.shape[1]):
            value = int(matrix[row_index, col_index])
            left.text(
                col_index,
                row_index,
                "bound" if value else "gap",
                ha="center",
                va="center",
                color="white" if value else _INK,
                fontsize=_FONT_SMALL,
                fontweight="bold" if value else "normal",
            )
    cbar = fig.colorbar(image, ax=left, fraction=0.046, pad=0.02, ticks=[0, 1])
    cbar.ax.set_yticklabels(["gap", "bound"])

    right.axis("off")
    _add_panel_label(right, "B", "Runtime contract")
    summary_rows = [
        ("planned registered figures", str(figure_count)),
        ("scholarship gates", "on" if include_scholarship else "off"),
        ("claim-support gates", "on" if include_claim_support else "off"),
        ("roadmap metric gates", "on" if include_roadmap else "off"),
    ]
    for index, (label, summary_value) in enumerate(summary_rows):
        y0 = 0.78 - index * 0.14
        right.text(
            0.03,
            y0,
            label,
            transform=right.transAxes,
            ha="left",
            va="center",
            fontsize=_FONT_SMALL,
            color=_MUTED,
        )
        right.text(
            0.97,
            y0,
            summary_value,
            transform=right.transAxes,
            ha="right",
            va="center",
            fontsize=10,
            fontweight="bold",
            color=_INK,
        )
    right.text(
        0.03,
        0.13,
        "\n".join(row[1] for row in rows),
        transform=right.transAxes,
        ha="left",
        va="bottom",
        fontsize=_FONT_SMALL,
        color=_MUTED,
        linespacing=1.25,
    )
    return _save_figure(
        fig,
        path,
        note=(
            "Validation-intent view; it enumerates mismatch classes and the gates "
            "expected to catch them before release."
        ),
    )


def plot_semantic_prerequisite_coverage(graph: CurriculumGraph, path: Path) -> Path:
    """Visualise the semantic-prerequisite gate: per load-bearing concept, how many
    skills are assessed on it and how many of those correctly reach the defining skill
    through their prerequisites. A fully green panel is the gate's passing state."""
    path = _prepare_path(path)
    coverage = semantic_prerequisite_coverage(graph)
    violations = len(audit_semantic_prerequisites(graph))

    labels: list[str] = []
    reach_counts: list[int] = []
    assessed_counts: list[int] = []
    for row in coverage:
        labels.append(f"{row.concept}\n({', '.join(row.definers)})")
        reach_counts.append(row.reachable_skills)
        assessed_counts.append(row.assessed_skills)

    fig, ax = plt.subplots(figsize=(11, 6.0), constrained_layout=True)
    y_pos = np.arange(len(labels))
    reach_arr = np.array(reach_counts, dtype=float)
    assessed_arr = np.array(assessed_counts, dtype=float)
    for y, reach, assessed in zip(y_pos, reach_arr, assessed_arr, strict=True):
        ax.plot(
            [0, reach],
            [y, y],
            color=_COLOR_FAMILIES["blue"]["light"],
            linewidth=8,
            solid_capstyle="round",
            zorder=1,
        )
        ax.plot(
            [0, assessed],
            [y, y],
            color=_OK,
            linewidth=3,
            solid_capstyle="round",
            zorder=2,
        )
    ax.scatter(
        reach_arr,
        y_pos,
        s=115,
        facecolors="white",
        edgecolors=_COLOR_FAMILIES["blue"]["dark"],
        linewidths=1.4,
        label="reachable via prerequisite closure",
        zorder=3,
    )
    ax.scatter(
        assessed_arr,
        y_pos,
        s=62,
        color=_OK,
        edgecolors="white",
        linewidths=0.9,
        label="assessed on concept",
        zorder=4,
    )
    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=_FONT_SMALL)
    ax.invert_yaxis()
    ax.set_ylim(len(labels) - 0.5, -1.05)
    ax.set_xlabel("number of skills")
    max_value = float(reach_arr.max()) if reach_arr.size else 0.0
    for i, (reach, assessed) in enumerate(
        zip(reach_counts, assessed_counts, strict=True)
    ):
        ax.text(
            reach + max(0.5, max_value * 0.01),
            i,
            f"{assessed}/{reach} assessed inside reachable set",
            va="center",
            fontsize=_FONT_SMALL,
            color=_INK,
        )
    verdict = (
        "0 violations — every assessed concept is reachable"
        if violations == 0
        else f"{violations} violations"
    )
    _add_axis_subtitle(
        ax,
        f"Source: semantic-prerequisite gate; {verdict}.",
    )
    ax.text(
        1.0,
        1.02,
        verdict,
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=_FONT_SMALL,
        fontweight="bold",
        color=_INK,
        bbox={
            "boxstyle": "round,pad=0.32",
            "facecolor": "white",
            "edgecolor": _OK if violations == 0 else _ALERT,
            "linewidth": 1.0,
        },
    )
    ax.legend(
        loc="upper center",
        bbox_to_anchor=(0.54, -0.12),
        ncol=2,
        fontsize=_FONT_SMALL,
        frameon=False,
    )
    _style_axis(ax, grid_axis="x")
    return _save_figure(
        fig,
        path,
        note="Concept reach and assessment use are computed from the live graph and the "
        "semantic-prerequisite gate's concept map.",
    )


def plot_visual_evidence_contract_ladder(graph: CurriculumGraph, path: Path) -> Path:
    """Render the visual-evidence contract workflow as an annotated ladder."""
    path = _prepare_path(path)
    levels = graph.levels()
    stage_rows = [
        (
            "question contract",
            "vdiag_question_contract",
            "reader question before chart form",
        ),
        (
            "data grain",
            "vdiag_data_grain_audit",
            "claim grain matches source rows",
        ),
        (
            "encoding strength",
            "vdiag_encoding_strength_audit",
            "strong marks carry load-bearing comparisons",
        ),
        (
            "annotation boundary",
            "vdiag_annotation_claim_boundary",
            "caption states what is and is not certified",
        ),
        (
            "static/mobile survival",
            "vdiag_static_mobile_survival",
            "PNG and dashboard card remain readable",
        ),
        (
            "negative control",
            "vdiag_visual_negative_control",
            "stale or missing contract fails closed",
        ),
    ]
    skills = {skill.skill_id: skill for skill in graph.skills}

    fig, ax = plt.subplots(figsize=(13, 5.8), constrained_layout=True)
    ax.set_xlim(-0.6, len(stage_rows) - 0.4)
    ax.set_ylim(-1.0, 2.2)
    ax.axis("off")
    _add_panel_label(ax, "A", "Visual evidence contract ladder")
    _add_axis_subtitle(
        ax,
        "Each rung is a live curriculum skill; the ladder is a static audit path, not a learner-effectiveness claim.",
    )

    for index, (stage, skill_id, chip) in enumerate(stage_rows):
        skill = skills.get(skill_id)
        present = skill is not None
        color = _PALETTE[skill.stratum.order] if skill is not None else _ALERT
        y = 0.72
        ax.scatter(
            [index],
            [y],
            s=900,
            color=color,
            edgecolor="white",
            linewidth=2.0,
            zorder=3,
        )
        ax.text(
            index,
            y,
            str(index + 1),
            ha="center",
            va="center",
            fontsize=13,
            color="white",
            fontweight="bold",
        )
        if index < len(stage_rows) - 1:
            ax.annotate(
                "",
                xy=(index + 0.72, y),
                xytext=(index + 0.28, y),
                arrowprops={"arrowstyle": "->", "color": _MUTED, "lw": 1.7},
            )
        ax.text(
            index,
            1.38,
            stage,
            ha="center",
            va="center",
            fontsize=10,
            fontweight="bold",
            color=_INK,
        )
        ax.text(
            index,
            1.13,
            textwrap.fill(skill_id, width=18),
            ha="center",
            va="center",
            fontsize=_FONT_SMALL,
            color=_MUTED,
            family="monospace",
        )
        ax.text(
            index,
            0.08,
            textwrap.fill(chip, width=24),
            ha="center",
            va="center",
            fontsize=_FONT_SMALL,
            color=_INK,
            bbox={
                "boxstyle": "round,pad=0.36",
                "facecolor": "#F8FAFC",
                "edgecolor": "#CBD5E1",
                "linewidth": 0.9,
            },
        )
        status = "registered" if present else "missing"
        depth = levels.get(skill_id, -1)
        ax.text(
            index,
            -0.48,
            f"{status} · depth {depth if depth >= 0 else 'n/a'}",
            ha="center",
            va="center",
            fontsize=_FONT_SMALL,
            color=_OK if present else _ALERT,
        )

    ax.text(
        0.02,
        0.04,
        "Source: live CurriculumGraph plus figure-registry contract metadata generated in the same render pass.",
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=_FONT_SMALL,
        color=_MUTED,
    )
    ax.text(
        0.98,
        0.04,
        "QA endpoint: missing stage, weak metadata, or stale file must fail before release.",
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=_FONT_SMALL,
        color=_MUTED,
    )
    return _save_figure(
        fig,
        path,
        note=(
            "Visual-evidence contract ladder generated from the live curriculum graph and "
            "the additive chart-contract registry fields."
        ),
    )
