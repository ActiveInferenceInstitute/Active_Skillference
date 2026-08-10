"""Cover figure for Active Skillference."""

from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import matplotlib
import numpy as np

os.environ.setdefault("MPLBACKEND", "Agg")
matplotlib.use("Agg")

import matplotlib.pyplot as plt

from src.curriculum.graph import CurriculumGraph
from src.curriculum.model import ALL_STRATA
from src.provenance.claims import ClaimRegistry

from .registry_helpers import _coerce_int, _resolve_cover_figure_count
from .style import (
    _FONT_SMALL,
    _INK,
    _LINE,
    _MUTED,
    _OK,
    _PALETTE,
    _PALETTE_LIGHT,
    _PANEL,
    _SURFACE,
    _add_axis_subtitle,
    _add_badge,
    _add_panel_label,
    _metric_card,
    _prepare_path,
    _save_figure,
    _style_axis,
)


def plot_active_skillference_cover(
    graph: CurriculumGraph,
    registry: ClaimRegistry,
    roadmap: Mapping[str, Any] | None,
    path: Path,
    *,
    figure_count: int | None = None,
    figure_registry_path: Path | None = None,
) -> Path:
    """Render the deterministic first-page cover image from live project data."""
    path = _prepare_path(path)
    stats = graph.stats()
    levels = graph.levels()
    strata = list(ALL_STRATA)
    skill_counts = np.array(
        [
            sum(1 for skill in graph.skills if skill.stratum is stratum)
            for stratum in strata
        ],
        dtype=float,
    )
    subject_counts = np.array(
        [
            sum(1 for subject in graph.subjects if subject.stratum is stratum)
            for stratum in strata
        ],
        dtype=float,
    )
    edge_counts = np.zeros(len(strata), dtype=float)
    for _prereq_id, dependent_id in graph.prerequisite_edges():
        edge_counts[graph.get_skill(dependent_id).stratum.order] += 1

    roadmap_metrics: Mapping[str, Any] = {}
    project = roadmap.get("project") if isinstance(roadmap, Mapping) else None
    if isinstance(project, Mapping):
        metrics = project.get("live_metrics")
        if isinstance(metrics, Mapping):
            roadmap_metrics = {str(key): value for key, value in metrics.items()}

    quiz_count = sum(1 for skill in graph.skills if skill.assessments)
    figure_count = _resolve_cover_figure_count(
        roadmap_metrics,
        figure_count=figure_count,
        figure_registry_path=figure_registry_path,
    )
    source_count = _coerce_int(roadmap_metrics.get("cited_sources"))

    fig = plt.figure(figsize=(12.0, 12.0), facecolor=_SURFACE, constrained_layout=True)
    grid = fig.add_gridspec(
        5,
        2,
        height_ratios=[1.12, 0.82, 1.9, 1.32, 0.78],
        width_ratios=[1.18, 0.82],
    )
    title_ax = fig.add_subplot(grid[0, :])
    badge_ax = fig.add_subplot(grid[1, :])
    graph_ax = fig.add_subplot(grid[2, :])
    bars_ax = fig.add_subplot(grid[3, 0])
    audit_ax = fig.add_subplot(grid[3, 1])
    footer_ax = fig.add_subplot(grid[4, :])

    title_ax.axis("off")
    title_ax.add_patch(
        plt.Rectangle(
            (0.0, 0.03),
            1.0,
            0.9,
            transform=title_ax.transAxes,
            facecolor="#f8fafc",
            edgecolor="#d8dee9",
            linewidth=1.2,
            zorder=0,
        )
    )
    title_ax.text(
        0.035,
        0.62,
        "Active Skillference",
        transform=title_ax.transAxes,
        ha="left",
        va="center",
        fontsize=40,
        fontweight="bold",
        color="#111827",
    )
    title_ax.text(
        0.038,
        0.26,
        "A provenance-bound SkillTree curriculum from kernel claims to quiz-gated delivery",
        transform=title_ax.transAxes,
        ha="left",
        va="center",
        fontsize=16,
        color="#374151",
    )
    title_ax.text(
        0.962,
        0.56,
        "Evidence-led cover\nnot learner-outcome evidence\nstatic public-review asset",
        transform=title_ax.transAxes,
        ha="right",
        va="center",
        fontsize=10,
        linespacing=1.35,
        color=_MUTED,
    )

    badge_ax.axis("off")
    badges = (
        ("skills", stats["skills"], _PALETTE[0]),
        ("subjects", stats["subjects"], _PALETTE[1]),
        ("dependencies", stats["prerequisite_edges"], _PALETTE[2]),
        ("quizzes", quiz_count, _PALETTE[3]),
        ("claims", len(registry), _PALETTE[4]),
    )
    for index, (label, value, color) in enumerate(badges):
        _metric_card(
            badge_ax,
            x=0.02 + index * 0.194,
            y=0.14,
            width=0.17,
            height=0.72,
            value=str(value),
            label=label,
            color=color,
        )

    pos: dict[str, tuple[float, float]] = {}
    per_stratum_counts: dict[int, int] = {}
    max_depth = max(levels.values()) if levels else 1
    for skill in sorted(
        graph.skills,
        key=lambda item: (item.stratum.order, levels[item.skill_id], item.skill_id),
    ):
        x = skill.stratum.order
        seen = per_stratum_counts.get(x, 0)
        per_stratum_counts[x] = seen + 1
        normalized_depth = levels[skill.skill_id] / max(1, max_depth)
        pos[skill.skill_id] = (x, normalized_depth + 0.012 * (seen % 9))

    for stratum in strata:
        graph_ax.axvspan(
            stratum.order - 0.42,
            stratum.order + 0.42,
            color=_PALETTE_LIGHT[stratum.order],
            alpha=0.18,
            zorder=0,
        )
    for index, (prereq, dependent) in enumerate(graph.prerequisite_edges()):
        if index % 4 != 0:
            continue
        x0, y0 = pos[prereq]
        x1, y1 = pos[dependent]
        graph_ax.plot(
            [x0, x1],
            [y0, y1],
            color="#7C8797",
            alpha=0.16,
            linewidth=0.45,
            zorder=1,
        )
    graph_ax.scatter(
        [point[0] for point in pos.values()],
        [point[1] for point in pos.values()],
        c=[_PALETTE[graph.get_skill(skill_id).stratum.order] for skill_id in pos],
        s=16,
        edgecolors="white",
        linewidths=0.25,
        alpha=0.86,
        zorder=2,
    )
    graph_ax.set_ylim(-0.06, 1.2)
    _add_panel_label(graph_ax, "A", "Validated prerequisite graph", y=0.985)
    _add_axis_subtitle(
        graph_ax,
        "Sampled edge layer preserves direction while count badges carry exact totals.",
        y=0.925,
    )
    graph_ax.set_xticks(range(len(strata)))
    graph_ax.set_xticklabels(
        [stratum.value.replace("_", "\n") for stratum in strata],
        fontsize=_FONT_SMALL,
    )
    graph_ax.set_yticks([0, 0.5, 1.0])
    graph_ax.set_yticklabels(["root", "middle", "canopy"], fontsize=_FONT_SMALL)
    graph_ax.set_ylabel("normalized depth")
    _add_badge(graph_ax, "acyclic, connected export", xy=(0.72, 0.95), color=_OK)
    _style_axis(graph_ax, grid_axis="y")

    y = np.arange(len(strata))
    bars_ax.barh(
        y - 0.18,
        skill_counts,
        height=0.34,
        color=[_PALETTE[stratum.order] for stratum in strata],
        label="skills",
    )
    bars_ax.barh(
        y + 0.18,
        subject_counts,
        height=0.34,
        color="#6b7280",
        label="subjects",
    )
    bars_ax.set_yticks(y)
    bars_ax.set_yticklabels(
        [stratum.value.replace("_", " ") for stratum in strata], fontsize=_FONT_SMALL
    )
    bars_ax.invert_yaxis()
    bars_ax.set_ylim(len(strata) - 0.5, -1.25)
    _add_panel_label(bars_ax, "B", "Stratum load evidence", y=1.08)
    _add_axis_subtitle(
        bars_ax,
        "Bars show raw volume; dashboard and tables retain exact records.",
        y=0.985,
    )
    bars_ax.legend(frameon=False, fontsize=_FONT_SMALL)
    _style_axis(bars_ax, grid_axis="x", hide=("top", "right", "left"))

    audit_ax.axis("off")
    _add_panel_label(audit_ax, "C", "Audit chain")
    audit_ax.text(
        0.06,
        0.71,
        "kernels -> claims -> DAG\nSkillTree -> dashboard",
        transform=audit_ax.transAxes,
        ha="left",
        va="center",
        fontsize=10,
        linespacing=1.35,
        fontweight="bold",
        color=_INK,
        bbox={
            "boxstyle": "round,pad=0.42",
            "facecolor": _PANEL,
            "edgecolor": _LINE,
            "linewidth": 1.1,
        },
    )
    rows = [
        ("max depth", str(stats["max_depth"])),
        ("incoming edges", str(int(edge_counts.sum()))),
        ("registered figures", str(figure_count)),
        ("cited sources", str(source_count or "tracked")),
    ]
    for row, (label, value) in enumerate(rows):
        y0 = 0.38 - row * 0.09
        audit_ax.text(
            0.06,
            y0,
            label,
            transform=audit_ax.transAxes,
            ha="left",
            va="center",
            fontsize=_FONT_SMALL,
            color=_MUTED,
        )
        audit_ax.text(
            0.94,
            y0,
            value,
            transform=audit_ax.transAxes,
            ha="right",
            va="center",
            fontsize=_FONT_SMALL,
            fontweight="bold",
            color=_INK,
        )

    footer_ax.axis("off")
    footer_ax.add_patch(
        plt.Rectangle(
            (0.0, 0.08),
            1.0,
            0.82,
            transform=footer_ax.transAxes,
            facecolor="#f8fafc",
            edgecolor="#d8dee9",
            linewidth=1.0,
            zorder=0,
        )
    )
    formulas = [
        r"$F=\mathrm{KL}(q\|p)-\mathbb{E}_q[\ln p(o\mid s)]$",
        r"$G(\pi)=\mathrm{risk}+\mathrm{ambiguity}-\mathrm{epistemic\ value}$",
    ]
    for index, formula in enumerate(formulas):
        footer_ax.text(
            0.035,
            0.7 - index * 0.32,
            formula,
            transform=footer_ax.transAxes,
            ha="left",
            va="center",
            fontsize=13,
            color="#111827",
        )
    footer_ax.text(
        0.965,
        0.22,
        "Provenance footer: computed quantities travel through rendered claims before publication or dashboard handoff.",
        transform=footer_ax.transAxes,
        ha="right",
        va="center",
        fontsize=_FONT_SMALL,
        color="#4b5563",
    )

    return _save_figure(
        fig,
        path,
        dpi=240,
        note=(
            "Cover is generated from graph counts, claim registry, roadmap metrics "
            "and artifact-chain state: kernels -> claims -> DAG -> SkillTree -> dashboard."
        ),
    )
