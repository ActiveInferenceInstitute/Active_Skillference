from __future__ import annotations

import os
from collections import Counter
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import matplotlib
import numpy as np

os.environ.setdefault("MPLBACKEND", "Agg")
matplotlib.use("Agg")

import matplotlib.pyplot as plt

from .style import (
    _BOUND,
    _FONT_SMALL,
    _INK,
    _OK,
    _add_axis_subtitle,
    _add_panel_label,
    _prepare_path,
    _save_figure,
    _style_axis,
)


def _roadmap_release_class(task: Mapping[str, Any]) -> str:
    status = str(task.get("status", "unknown"))
    task_id = str(task.get("id", ""))
    if status == "blocked":
        return "external_blocker"
    if status == "todo" and task_id == "asf-release-branch-hygiene":
        return "git_authorization"
    return status


def plot_roadmap_risk(roadmap: Mapping[str, Any], path: Path) -> Path:
    """Render roadmap status and live metrics from tasks.yaml."""
    path = _prepare_path(path)
    tasks = roadmap.get("tasks", [])
    if not isinstance(tasks, list):
        tasks = []
    status_counts = Counter(
        str(task.get("status", "unknown"))
        for task in tasks
        if isinstance(task, Mapping)
    )
    project = roadmap.get("project", {})
    metrics = project.get("live_metrics", {}) if isinstance(project, Mapping) else {}
    if not isinstance(metrics, Mapping):
        metrics = {}

    active_tasks = [
        task
        for task in tasks
        if isinstance(task, Mapping) and str(task.get("status", "unknown")) != "done"
    ]
    surface_status_counts: dict[str, Counter[str]] = {}
    for task in active_tasks:
        surface = str(task.get("surface", "unspecified"))
        release_class = _roadmap_release_class(task)
        surface_status_counts.setdefault(surface, Counter())[release_class] += 1

    fig, (left, middle, right) = plt.subplots(
        1,
        3,
        figsize=(13.4, 6.4),
        gridspec_kw={"width_ratios": [0.75, 1.15, 1.35]},
        constrained_layout=True,
    )
    status_order = ["done", "in_progress", "todo", "blocked"]
    status_colors = {
        "done": "#009E73",
        "in_progress": "#56B4E9",
        "todo": "#E69F00",
        "blocked": "#D55E00",
        "external_blocker": "#D55E00",
        "git_authorization": "#E69F00",
        "unknown": "#6B7280",
    }
    status_hatches = {
        "external_blocker": "///",
        "git_authorization": "xx",
        "todo": "",
        "in_progress": "..",
        "unknown": "--",
    }
    status_values = np.array(
        [status_counts.get(status, 0) for status in status_order],
        dtype=float,
    )
    left.bar(
        status_order, status_values, color=[status_colors[s] for s in status_order]
    )
    _add_panel_label(left, "A", "Roadmap status by task count")
    left.set_ylabel("tasks")
    left.set_xticks(range(len(status_order)))
    left.set_xticklabels([status.replace("_", "\n") for status in status_order])
    left.tick_params(axis="x", labelsize=_FONT_SMALL)
    left.set_ylim(0, max(1.0, float(status_values.max()) * 1.18))
    for index, value in enumerate(status_values):
        left.text(
            index, value + 0.08, str(int(value)), ha="center", fontsize=_FONT_SMALL
        )

    surfaces = sorted(
        surface_status_counts,
        key=lambda surface: (-sum(surface_status_counts[surface].values()), surface),
    )
    y_surface = np.arange(len(surfaces))
    offsets = np.zeros(len(surfaces), dtype=float)
    for status in (
        "external_blocker",
        "git_authorization",
        "todo",
        "in_progress",
        "unknown",
    ):
        values_for_status = np.array(
            [surface_status_counts[surface].get(status, 0) for surface in surfaces],
            dtype=float,
        )
        if not np.any(values_for_status):
            continue
        middle.barh(
            y_surface,
            values_for_status,
            left=offsets,
            color=status_colors.get(status, "#6B7280"),
            edgecolor=_INK if status in status_hatches else "white",
            hatch=status_hatches.get(status, ""),
            linewidth=0.5,
            label=status.replace("_", " "),
        )
        for index, value in enumerate(values_for_status):
            if value <= 0:
                continue
            code = {
                "external_blocker": "EXT",
                "git_authorization": "GIT",
                "todo": "T",
                "in_progress": "IP",
                "unknown": "?",
            }.get(status, status[:1].upper())
            middle.text(
                offsets[index] + value / 2,
                index,
                f"{code} {int(value)}",
                ha="center",
                va="center",
                fontsize=_FONT_SMALL,
                color="white" if status != "todo" else _INK,
                fontweight="bold",
            )
        offsets += values_for_status
    middle.set_yticks(y_surface)
    middle.set_yticklabels(
        [
            f"{surface} ({sum(surface_status_counts[surface].values())})"
            for surface in surfaces
        ],
        fontsize=_FONT_SMALL,
    )
    middle.invert_yaxis()
    middle.set_xlabel("active items")
    _add_panel_label(middle, "B", "Remaining work by surface")
    _add_axis_subtitle(
        middle,
        f"{len(active_tasks)} active items; EXT=external blocker, GIT=git authorization.",
        y=-0.12,
    )
    for index, total in enumerate(offsets):
        middle.text(
            total + 0.05,
            index,
            str(int(total)),
            va="center",
            fontsize=_FONT_SMALL,
            color=_INK,
        )
    if surfaces:
        middle.set_xlim(0, max(1.0, float(offsets.max()) + 0.9))
        middle.legend(loc="lower right", fontsize=_FONT_SMALL, frameon=False)
    else:
        middle.text(
            0.5,
            0.5,
            "No open roadmap items",
            transform=middle.transAxes,
            ha="center",
            va="center",
            fontsize=10,
            color=_OK,
        )
        middle.set_xlim(0, 1)

    metric_items = [
        ("skills", metrics.get("skills", 0)),
        ("subjects", metrics.get("subjects", 0)),
        ("edges", metrics.get("prerequisite_edges", 0)),
        ("assessments", metrics.get("assessments", 0)),
        ("sources", metrics.get("cited_sources", 0)),
        ("figures", metrics.get("figures", 0)),
    ]
    labels = [label for label, _ in metric_items]
    values = np.array([int(value) for _, value in metric_items], dtype=float)
    y_pos = np.arange(len(labels))
    bars = right.barh(y_pos, values, color=_BOUND)
    right.set_yticks(y_pos)
    right.set_yticklabels(labels)
    right.invert_yaxis()
    right.set_xlabel("live value")
    _add_panel_label(right, "C", "Roadmap-bound live metrics")
    max_value = float(values.max()) if values.size else 0.0
    for bar, value in zip(bars, values, strict=True):
        right.text(
            bar.get_width() + max(1.0, max_value * 0.025),
            bar.get_y() + bar.get_height() / 2,
            str(int(value)),
            va="center",
            fontsize=_FONT_SMALL,
        )
    right.set_xlim(0, max_value * 1.25 if max_value else 1)
    for ax in (left, middle, right):
        _style_axis(ax, grid_axis="y" if ax is left else "x")
    return _save_figure(
        fig,
        path,
        note=(
            "Roadmap status, active surfaces and metrics are read from tasks.yaml "
            "and live metric checks."
        ),
    )
