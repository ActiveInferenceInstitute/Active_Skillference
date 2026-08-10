from __future__ import annotations

import os
import textwrap
from collections import Counter
from pathlib import Path

import matplotlib
import numpy as np

os.environ.setdefault("MPLBACKEND", "Agg")
matplotlib.use("Agg")

import matplotlib.pyplot as plt

from src.curriculum.graph import CurriculumGraph
from src.curriculum.model import ALL_STRATA
from src.curriculum.vfe_efe_bridge import build_vfe_efe_bridge_rows

from .style import (
    _BOUND,
    _COLOR_FAMILIES,
    _FONT_LABEL,
    _FONT_SMALL,
    _GRID,
    _INK,
    _LINE,
    _MUTED,
    _PALETTE,
    _PALETTE_LIGHT,
    _SURFACE,
    _add_badge,
    _prepare_path,
    _save_figure,
    _short_label,
    _style_axis,
)


def plot_vfe_efe_skilltree_bridge(graph: CurriculumGraph, path: Path) -> Path:
    """Render the real SkillTree bridge for VFE/EFE supplement subjects."""
    path = _prepare_path(path)
    rows = build_vfe_efe_bridge_rows(graph)
    max_skill_count = max(row.skill_count for row in rows)
    max_edge_count = max(row.prerequisite_edges for row in rows)

    fig, ax = plt.subplots(figsize=(17.8, 9.0), constrained_layout=True)
    ax.set_xlim(0, 1)
    ax.set_ylim(-0.08, len(rows) + 1.35)
    ax.axis("off")
    ax.text(
        0.02,
        len(rows) + 1.05,
        "VFE/EFE supplement bridge to SkillTree subjects (validator-checked wiring)",
        ha="left",
        va="center",
        fontsize=17,
        fontweight="bold",
        color=_INK,
    )
    ax.text(
        0.02,
        len(rows) + 0.72,
        "Generated from the current curriculum graph: subjects, skills, prerequisite edges, quiz ids, learn routes, and quiz routes.",
        ha="left",
        va="center",
        fontsize=10,
        color=_MUTED,
    )
    ax.text(
        0.98,
        len(rows) + 1.05,
        "distinct learn + quiz routes",
        ha="right",
        va="center",
        fontsize=_FONT_SMALL,
        fontweight="bold",
        color=_MUTED,
        bbox={
            "boxstyle": "round,pad=0.35",
            "facecolor": "white",
            "edgecolor": _LINE,
        },
    )

    headers = (
        (0.025, "Layer"),
        (0.17, "SkillTree subject"),
        (0.405, "Skills / edges"),
        (0.565, "Depth"),
        (0.66, "Representative skills"),
        (0.79, "Learn + quiz routes"),
    )
    for x, label in headers:
        ax.text(
            x,
            len(rows) + 0.25,
            label,
            ha="left",
            va="center",
            fontsize=_FONT_SMALL,
            fontweight="bold",
            color="#374151",
        )

    for index, row in enumerate(rows):
        y = len(rows) - index - 0.35
        band = "#f8fafc" if index % 2 == 0 else "#ffffff"
        accent = _PALETTE[0] if row.role.startswith("VFE") else _PALETTE[2]
        ax.add_patch(
            plt.Rectangle(
                (0.015, y - 0.42),
                0.97,
                0.78,
                facecolor=band,
                edgecolor=_GRID,
                linewidth=0.8,
            )
        )
        ax.add_patch(
            plt.Rectangle(
                (0.015, y - 0.42),
                0.008,
                0.78,
                facecolor=accent,
                edgecolor=accent,
            )
        )
        ax.text(
            0.025,
            y,
            row.role,
            ha="left",
            va="center",
            fontsize=10,
            fontweight="bold",
            color=_INK,
        )
        ax.text(
            0.18,
            y + 0.13,
            textwrap.fill(row.subject_name, width=31),
            ha="left",
            va="center",
            fontsize=_FONT_SMALL,
            color=_INK,
        )
        ax.text(
            0.17,
            y - 0.18,
            textwrap.fill(row.subject_id, width=31),
            ha="left",
            va="center",
            fontsize=_FONT_SMALL,
            color=_MUTED,
        )

        skill_width = 0.085 * (row.skill_count / max_skill_count)
        edge_width = 0.085 * (row.prerequisite_edges / max_edge_count)
        ax.add_patch(
            plt.Rectangle(
                (0.405, y + 0.08),
                skill_width,
                0.12,
                facecolor=_PALETTE[1],
                edgecolor="none",
            )
        )
        ax.add_patch(
            plt.Rectangle(
                (0.405, y - 0.16),
                edge_width,
                0.12,
                facecolor=_PALETTE[4],
                edgecolor="none",
            )
        )
        ax.text(
            0.505,
            y + 0.14,
            f"{row.skill_count} skills",
            ha="left",
            va="center",
            fontsize=_FONT_SMALL,
            color=_INK,
        )
        ax.text(
            0.505,
            y - 0.10,
            f"{row.prerequisite_edges} prereqs; {row.internal_edges} internal",
            ha="left",
            va="center",
            fontsize=_FONT_SMALL,
            color=_INK,
        )
        ax.text(
            0.565,
            y,
            f"{row.min_depth}-{row.max_depth}",
            ha="left",
            va="center",
            fontsize=10,
            fontweight="bold",
            color=_INK,
        )
        ax.text(
            0.66,
            y,
            "\n".join(row.representative_skill_ids),
            ha="left",
            va="center",
            fontsize=_FONT_SMALL,
            color="#111827",
            linespacing=1.35,
        )
        quiz_fragment = row.quiz_route.replace(f"/subjects/{row.subject_id}/", "")
        route = f"Subject: {row.learn_route}\nQuiz: {quiz_fragment}"
        ax.text(
            0.79,
            y,
            "\n".join(textwrap.fill(line, width=36) for line in route.splitlines()),
            ha="left",
            va="center",
            fontsize=_FONT_SMALL,
            color=_MUTED,
            linespacing=1.25,
        )

    ax.text(
        0.02,
        0.04,
        "Interpretation boundary: this bridge shows curriculum/export wiring for the supplement, not learner outcomes or biological validity.",
        ha="left",
        va="center",
        fontsize=_FONT_SMALL,
        color=_MUTED,
    )
    return _save_figure(
        fig,
        path,
        note="Bridge verifies supplement-to-SkillTree wiring; it is not learner-outcome evidence.",
    )


def plot_graph_bottlenecks(graph: CurriculumGraph, path: Path) -> Path:
    """Render top prerequisite bottlenecks by dependent count."""
    path = _prepare_path(path)
    levels = graph.levels()
    dependents: Counter[str] = Counter()
    prereq_counts: Counter[str] = Counter()
    for prereq_id, dependent_id in graph.prerequisite_edges():
        dependents[prereq_id] += 1
        prereq_counts[dependent_id] += 1
    rows = sorted(
        graph.skills,
        key=lambda skill: (
            -dependents[skill.skill_id],
            -prereq_counts[skill.skill_id],
            skill.skill_id,
        ),
    )[:8]
    labels = [
        f"{skill.skill_id}\n{textwrap.fill(skill.name, width=32)}" for skill in rows
    ]
    values = np.array([dependents[skill.skill_id] for skill in rows], dtype=float)
    colors = [_COLOR_FAMILIES["blue"]["base"] for _skill in rows]
    hatches = ("", "///", "\\\\\\", "...", "xx", "---", "++", "oo")

    fig, ax = plt.subplots(figsize=(12.8, 8.2), constrained_layout=True)
    y_pos = np.arange(len(rows))
    bars = ax.barh(y_pos, values, height=0.58, color=colors)
    for bar, skill in zip(bars, rows, strict=True):
        bar.set_hatch(hatches[skill.stratum.order % len(hatches)])
        bar.set_edgecolor(_COLOR_FAMILIES["blue"]["dark"])
        bar.set_linewidth(0.75)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=_FONT_SMALL)
    ax.invert_yaxis()
    ax.set_xlabel("dependent skills")
    ax.set_title("High-fan-out prerequisites are priority review targets", pad=14)
    max_value = float(values.max()) if values.size else 1.0
    metric_x = max_value * 1.04
    chip_x = max_value * 1.27
    for bar, skill in zip(bars, rows, strict=True):
        ax.text(
            metric_x,
            bar.get_y() + bar.get_height() / 2,
            f"{int(bar.get_width())} deps\n depth {levels[skill.skill_id]}",
            va="center",
            fontsize=_FONT_SMALL,
            linespacing=1.15,
        )
        ax.text(
            chip_x,
            bar.get_y() + bar.get_height() / 2,
            skill.stratum.value.replace("_", " "),
            va="center",
            fontsize=_FONT_SMALL,
            color=_INK,
            bbox={
                "boxstyle": "round,pad=0.25",
                "facecolor": _PALETTE_LIGHT[skill.stratum.order],
                "edgecolor": _PALETTE[skill.stratum.order],
                "linewidth": 0.8,
            },
        )
    if values.size:
        median_value = float(np.median(values))
        ax.axvline(
            median_value,
            color=_MUTED,
            linestyle=":",
            linewidth=1.1,
            zorder=0,
        )
        ax.text(
            median_value,
            -0.72,
            f"top-8 median {median_value:.0f}",
            ha="center",
            va="bottom",
            fontsize=_FONT_SMALL,
            color=_MUTED,
        )
    ax.set_xlim(0, max(1.0, max_value * 1.58))
    _style_axis(ax, grid_axis="x", hide=("top", "right", "left"))
    return _save_figure(
        fig,
        path,
        note="Dependent fan-out ranks maintenance risk; it does not score learner difficulty.",
    )


def plot_skill_neighborhood_paths(graph: CurriculumGraph, path: Path) -> Path:
    """Render a representative longest prerequisite path."""
    path = _prepare_path(path)
    levels = graph.levels()
    by_dependent: dict[str, list[str]] = {}
    for prereq_id, dependent_id in graph.prerequisite_edges():
        by_dependent.setdefault(dependent_id, []).append(prereq_id)
    current = max(
        graph.skills, key=lambda skill: (levels[skill.skill_id], skill.skill_id)
    )
    path_ids = [current.skill_id]
    while by_dependent.get(current.skill_id):
        next_id = max(
            by_dependent[current.skill_id],
            key=lambda skill_id: (levels[skill_id], skill_id),
        )
        path_ids.append(next_id)
        current = graph.get_skill(next_id)
    path_ids.reverse()
    skills = [graph.get_skill(skill_id) for skill_id in path_ids]

    fig, (ax, ledger_ax) = plt.subplots(
        2,
        1,
        figsize=(15.6, 7.1),
        gridspec_kw={"height_ratios": [3.0, 1.55]},
        constrained_layout=True,
    )
    x_pos = np.arange(len(skills))
    y_pos = np.array([skill.stratum.order for skill in skills])
    for stratum in ALL_STRATA:
        ax.axhspan(
            stratum.order - 0.45,
            stratum.order + 0.45,
            color=_PALETTE_LIGHT[stratum.order],
            alpha=0.18 if stratum.order % 2 == 0 else 0.09,
            zorder=0,
        )
    ax.plot(x_pos, y_pos, color="#475569", linewidth=1.8, zorder=1)
    ax.scatter(
        x_pos,
        y_pos,
        s=95,
        color=[_PALETTE[skill.stratum.order] for skill in skills],
        edgecolors="white",
        linewidths=0.8,
        zorder=2,
    )
    # The longest path can be ~76 nodes; labelling every node produces an unreadable
    # smear. Label only the endpoints and the first node of each stratum (the points a
    # reader actually navigates by), and tick the same indices, so the chain stays legible.
    label_indices = {0, len(skills) - 1}
    previous_order: int | None = None
    for idx, skill in enumerate(skills):
        if skill.stratum.order != previous_order:
            label_indices.add(idx)
            previous_order = skill.stratum.order
    checkpoint_indices = sorted(label_indices)
    transition_indices = [
        idx for idx in checkpoint_indices if idx not in {0, len(skills) - 1}
    ]
    if transition_indices:
        ax.scatter(
            [x_pos[idx] for idx in transition_indices],
            [y_pos[idx] for idx in transition_indices],
            s=175,
            facecolors="none",
            edgecolors=_INK,
            linewidths=1.0,
            zorder=3,
        )
    for ordinal, idx in enumerate(checkpoint_indices):
        if idx not in {0, len(skills) - 1}:
            continue
        skill = skills[idx]
        label = _short_label(skill.skill_id, width=18)
        role = "start" if idx == 0 else "end"
        offset = 0.42 if ordinal % 2 == 0 else -0.55
        ax.annotate(
            f"{role}: {label}",
            xy=(idx, skill.stratum.order),
            xytext=(idx, skill.stratum.order + offset),
            ha="center",
            va="bottom" if offset > 0 else "top",
            fontsize=_FONT_SMALL,
            arrowprops={
                "arrowstyle": "-",
                "color": _MUTED,
                "linewidth": 0.8,
                "shrinkA": 2,
                "shrinkB": 4,
            },
            bbox={
                "boxstyle": "round,pad=0.18",
                "facecolor": "white",
                "edgecolor": _LINE,
                "linewidth": 0.7,
                "alpha": 0.95,
            },
        )
    ax.set_yticks(range(len(ALL_STRATA)))
    ax.set_yticklabels(
        [stratum.value.replace("_", "\n") for stratum in ALL_STRATA],
        fontsize=_FONT_SMALL,
    )
    tick_indices = checkpoint_indices
    ax.set_xticks([x_pos[i] for i in tick_indices])
    ax.set_xticklabels(
        [str(levels[skills[i].skill_id]) for i in tick_indices], fontsize=_FONT_SMALL
    )
    ax.set_ylim(-0.9, len(ALL_STRATA) - 0.05)
    ax.set_xlabel("prerequisite depth along representative longest path")
    ax.set_title(
        f"Representative longest path ({len(skills)} nodes; checkpoint ledger below)",
        pad=16,
    )
    _add_badge(
        ax,
        "line labels start/end; outlined nodes mark transitions",
        xy=(0.02, 0.97),
        color=_BOUND,
    )
    ax.text(
        0.98,
        0.04,
        f"{len(skills)} nodes on this representative path; global coverage remains in the DAG.",
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=_FONT_SMALL,
        color=_MUTED,
    )
    _style_axis(ax, grid_axis="y")
    ledger_ax.axis("off")
    ledger_ax.set_xlim(0, 1)
    ledger_ax.set_ylim(0, 1)
    ledger_ax.text(
        0.0,
        0.97,
        "Checkpoint ledger",
        ha="left",
        va="top",
        fontsize=_FONT_LABEL,
        fontweight="bold",
    )
    ledger_ax.text(
        0.18,
        0.97,
        "Each cell names the readable route checkpoint; omitted nodes remain ordered in the line above.",
        ha="left",
        va="top",
        fontsize=_FONT_SMALL,
        color=_MUTED,
    )
    for ordinal, idx in enumerate(checkpoint_indices):
        skill = skills[idx]
        role = (
            "start" if idx == 0 else "end" if idx == len(skills) - 1 else "transition"
        )
        col = ordinal % 3
        row = ordinal // 3
        x = 0.02 + col * 0.325
        y = 0.74 - row * 0.27
        ledger_ax.add_patch(
            plt.Rectangle(
                (x, y - 0.17),
                0.31,
                0.22,
                facecolor=_SURFACE,
                edgecolor=_LINE,
                linewidth=0.8,
            )
        )
        ledger_ax.text(
            x + 0.012,
            y - 0.01,
            (
                f"{role} · depth {levels[skill.skill_id]}\n"
                f"{skill.skill_id} · {textwrap.shorten(skill.name, width=31, placeholder='...')}"
            ),
            ha="left",
            va="center",
            fontsize=_FONT_SMALL,
            linespacing=1.1,
        )
    return _save_figure(
        fig,
        path,
        note="Path view sacrifices global completeness so one dependency chain is inspectable.",
    )
