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
from src.curriculum.model import ALL_STRATA
from src.curriculum.quality import (
    MIN_ASSESSMENTS_PER_SKILL,
)

from .style import (
    _ALERT,
    _FLOW_CMAP,
    _FONT_SMALL,
    _INK,
    _LINE,
    _MUTED,
    _OK,
    _PALETTE,
    _PALETTE_LIGHT,
    _WARN,
    _add_axis_subtitle,
    _add_badge,
    _add_panel_label,
    _label_horizontal_bars,
    _prepare_path,
    _save_figure,
    _style_axis,
)


def plot_curriculum_dag(graph: CurriculumGraph, path: Path) -> Path:
    """Lay skills out at x = stratum order, y = depth; draw prerequisite edges."""
    path = _prepare_path(path)
    levels = graph.levels()
    pos: dict[str, tuple[float, float]] = {}
    per_stratum_counts: dict[int, int] = {}
    for skill in sorted(
        graph.skills, key=lambda s: (s.stratum.order, levels[s.skill_id])
    ):
        x = skill.stratum.order
        seen = per_stratum_counts.get(x, 0)
        per_stratum_counts[x] = seen + 1
        # jitter within a stratum column by insertion order to avoid overlap
        pos[skill.skill_id] = (x, levels[skill.skill_id] + 0.12 * (seen % 5))

    fig, ax = plt.subplots(figsize=(15.2, 9.4), constrained_layout=True)
    max_depth = max(levels.values()) if levels else 0
    for stratum in ALL_STRATA:
        ax.axvspan(
            stratum.order - 0.44,
            stratum.order + 0.44,
            color=_PALETTE_LIGHT[stratum.order],
            alpha=0.18,
            zorder=0,
        )
    for prereq, dependent in graph.prerequisite_edges():
        x0, y0 = pos[prereq]
        x1, y1 = pos[dependent]
        ax.plot(
            [x0, x1],
            [y0, y1],
            color="#7C8797",
            linewidth=0.28,
            alpha=0.24,
            zorder=1,
        )
    xs = [p[0] for p in pos.values()]
    ys = [p[1] for p in pos.values()]
    colours = [graph.get_skill(sid).stratum.order for sid in pos]
    colour_values = [_PALETTE[index] for index in colours]
    ax.scatter(
        xs,
        ys,
        c=colour_values,
        s=34,
        zorder=2,
        edgecolors="white",
        linewidths=0.4,
    )
    for root_id, label, offset in (
        ("m_sets", "root: sets", (0.08, 0.45)),
        ("p_axioms", "root: probability axioms", (0.08, 0.45)),
    ):
        if root_id in pos:
            root_x, root_y = pos[root_id]
            ax.annotate(
                label,
                xy=(root_x, root_y),
                xytext=(root_x + offset[0], root_y + offset[1]),
                fontsize=_FONT_SMALL,
                arrowprops={"arrowstyle": "->", "color": _MUTED, "lw": 0.7},
                color=_INK,
            )
    ax.text(
        0.99,
        0.04,
        f"{len(graph.skills)} skills | {len(graph.subjects)} subjects | "
        f"{len(graph.prerequisite_edges())} edges | max depth {max_depth}",
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=_FONT_SMALL,
        bbox={
            "boxstyle": "round,pad=0.25",
            "facecolor": "white",
            "edgecolor": _LINE,
        },
    )
    _add_badge(
        ax,
        "roots limited to foundational strata; edges respect topological order",
        xy=(0.02, 0.89),
        color=_OK,
    )
    ax.set_xticks(range(len(ALL_STRATA)))
    ax.set_xticklabels(
        [s.value.replace("_", "\n") for s in ALL_STRATA], fontsize=_FONT_SMALL
    )
    ax.set_ylabel("prerequisite depth (longest chain)")
    ax.set_xlabel("pedagogical stratum")
    ax.set_title("Prerequisite DAG by stratum and depth (validator-checked)", pad=18)
    _add_axis_subtitle(
        ax,
        "Background lanes and direct labels encode strata; gray links encode prerequisite edges.",
        y=0.845,
    )
    for stratum in ALL_STRATA:
        count = per_stratum_counts.get(stratum.order, 0)
        ax.text(
            stratum.order,
            max_depth + 1.15,
            "\n".join(textwrap.wrap(stratum.value.replace("_", " "), width=13))
            + f"\n{count} skills",
            ha="center",
            va="bottom",
            fontsize=_FONT_SMALL,
            fontweight="bold",
            linespacing=1.18,
            color=_PALETTE[stratum.order],
            bbox={
                "boxstyle": "round,pad=0.25",
                "facecolor": "white",
                "edgecolor": _PALETTE_LIGHT[stratum.order],
                "linewidth": 0.8,
            },
        )
    ax.set_xlim(-0.6, len(ALL_STRATA) - 0.4)
    ax.set_ylim(-0.35, max_depth + 5.2)
    _style_axis(ax, grid_axis="y")
    return _save_figure(
        fig,
        path,
        note=(
            "Overview graph; inspect bottleneck and path figures for local "
            "dependency review."
        ),
    )


def plot_dependency_strata_flow(graph: CurriculumGraph, path: Path) -> Path:
    """Show prerequisite-edge density from source stratum to dependent stratum."""
    path = _prepare_path(path)
    strata = list(ALL_STRATA)
    n_strata = len(strata)
    matrix = np.zeros((n_strata, n_strata), dtype=int)
    skill_counts = np.zeros(n_strata, dtype=int)

    for skill in graph.skills:
        skill_counts[skill.stratum.order] += 1
    for prereq_id, dependent_id in graph.prerequisite_edges():
        prereq = graph.get_skill(prereq_id)
        dependent = graph.get_skill(dependent_id)
        matrix[prereq.stratum.order, dependent.stratum.order] += 1
    row_totals = matrix.sum(axis=1)
    col_totals = matrix.sum(axis=0)

    labels = [stratum.value.replace("_", "\n") for stratum in strata]
    fig = plt.figure(figsize=(12, 7.5))
    grid = fig.add_gridspec(
        1,
        3,
        width_ratios=[5.4, 0.28, 1.55],
        left=0.12,
        right=0.96,
        bottom=0.18,
        top=0.84,
        wspace=0.10,
    )
    heat = fig.add_subplot(grid[0, 0])
    colorbar_axis = fig.add_subplot(grid[0, 1])
    bars = fig.add_subplot(grid[0, 2])
    image = heat.imshow(matrix, cmap=_FLOW_CMAP, aspect="equal", vmin=0)
    heat.set_xticks(np.arange(n_strata))
    heat.set_yticks(np.arange(n_strata))
    heat.set_xticklabels(labels, rotation=45, ha="right", fontsize=_FONT_SMALL)
    heat.set_yticklabels(labels, fontsize=_FONT_SMALL)
    heat.set_xlabel("dependent skill stratum")
    heat.set_ylabel("prerequisite skill stratum")

    # The strictly-lower triangle (prerequisite stratum below the dependent
    # stratum) encodes backward dependencies, which the quality gate rejects
    # before export. Shade and hatch it as an explicit "must be empty" zone so
    # the DAG-safety invariant is self-proving: empty cells read as the gray
    # safe zone, and any populated cell stands out against it.
    backward_violation = bool(np.tril(matrix, k=-1).any())
    for row in range(n_strata):
        for col in range(row):
            heat.add_patch(
                plt.Rectangle(
                    (col - 0.5, row - 0.5),
                    1.0,
                    1.0,
                    facecolor="#ECEFF3",
                    edgecolor="#C8CED8",
                    hatch="////",
                    zorder=2.0,
                )
            )
    title = "Prerequisite flow: totals expose load; no backward edges"
    if backward_violation:
        title = "Prerequisite flow: BACKWARD EDGE detected"
    fig.suptitle(
        title,
        x=0.15,
        y=0.965,
        ha="left",
        fontsize=13,
        fontweight="bold",
        color=_INK,
    )
    _add_panel_label(heat, "A", "Edge counts by source and target stratum", y=1.10)
    _add_axis_subtitle(
        heat,
        "Rows are prerequisite strata; columns are dependent strata; lower triangle is forbidden.",
        y=1.04,
    )
    heat.set_xticks(np.arange(-0.5, n_strata, 1), minor=True)
    heat.set_yticks(np.arange(-0.5, n_strata, 1), minor=True)
    heat.grid(which="minor", color="white", linestyle="-", linewidth=1.1)
    heat.tick_params(which="minor", bottom=False, left=False)
    heat.set_xlim(-0.5, n_strata + 1.0)
    heat.set_ylim(n_strata - 0.5, -1.18)

    max_edge = int(matrix.max()) if matrix.size else 0
    for row in range(n_strata):
        for col in range(n_strata):
            count = int(matrix[row, col])
            if count == 0:
                continue
            backward = row > col
            colour = (
                "white"
                if (not backward and max_edge and count > max_edge * 0.55)
                else "#111827"
            )
            # A populated backward cell is an invariant violation: ring it in the
            # palette's vermillion so it cannot be mistaken for the empty safe zone.
            if backward:
                heat.add_patch(
                    plt.Rectangle(
                        (col - 0.5, row - 0.5),
                        1.0,
                        1.0,
                        facecolor=_ALERT,
                        edgecolor=_INK,
                        linewidth=1.6,
                        zorder=3.0,
                    )
                )
                colour = "white"
            heat.text(
                col,
                row,
                str(count),
                ha="center",
                va="center",
                color=colour,
                fontsize=_FONT_SMALL,
                fontweight="bold",
                zorder=4.0,
            )
    heat.text(
        n_strata + 0.15,
        -0.72,
        "row\ntotal",
        ha="center",
        va="center",
        fontsize=_FONT_SMALL,
        fontweight="bold",
        color=_MUTED,
    )
    for row, total in enumerate(row_totals):
        heat.text(
            n_strata + 0.15,
            row,
            str(int(total)),
            ha="center",
            va="center",
            fontsize=_FONT_SMALL,
            fontweight="bold",
            color=_INK,
        )
    for col, total in enumerate(col_totals):
        heat.text(
            col,
            -0.72,
            str(int(total)),
            ha="center",
            va="center",
            fontsize=_FONT_SMALL,
            fontweight="bold",
            color=_INK,
        )
    heat.text(
        0.69,
        0.1,
        "diagonal = same-stratum support",
        transform=heat.transAxes,
        ha="left",
        va="center",
        fontsize=_FONT_SMALL,
        color=_INK,
        bbox={
            "boxstyle": "round,pad=0.25",
            "facecolor": "white",
            "edgecolor": _LINE,
        },
    )
    heat.text(
        0.69,
        0.04,
        "upper triangle = forward learning flow",
        transform=heat.transAxes,
        ha="left",
        va="center",
        fontsize=_FONT_SMALL,
        color=_INK,
        bbox={
            "boxstyle": "round,pad=0.25",
            "facecolor": "white",
            "edgecolor": _LINE,
        },
    )
    cbar = fig.colorbar(image, cax=colorbar_axis)
    cbar.set_label("prerequisite edges")
    heat.legend(
        handles=[
            plt.Rectangle(
                (0, 0),
                1,
                1,
                facecolor="#ECEFF3",
                hatch="////",
                edgecolor="#6b7280",
                label="backward zone: must stay empty",
            )
        ],
        loc="upper left",
        bbox_to_anchor=(0.0, -0.18),
        frameon=False,
        fontsize=_FONT_SMALL,
    )

    y_pos = np.arange(n_strata)
    bars.barh(y_pos, skill_counts, color=[_PALETTE[s.order] for s in strata])
    bars.set_yticks(y_pos)
    bars.set_yticklabels([])
    bars.set_xlabel("skills")
    _add_panel_label(bars, "B", "Skill counts")
    bars.set_ylim(heat.get_ylim())
    for y, count in zip(y_pos, skill_counts, strict=True):
        bars.text(
            float(count) + max(1.0, float(skill_counts.max()) * 0.02),
            float(y),
            str(int(count)),
            va="center",
            fontsize=_FONT_SMALL,
            color=_INK,
        )
    _style_axis(bars, grid_axis="x", hide=("top", "right", "left"))

    return _save_figure(
        fig,
        path,
        note=(
            "Lower triangle encodes backward dependencies and must remain empty "
            "after validation."
        ),
    )


def plot_assessment_depth_matrix(graph: CurriculumGraph, path: Path) -> Path:
    """Show assessment depth and multiple-choice coverage by stratum."""
    path = _prepare_path(path)
    strata = list(ALL_STRATA)
    skill_counts = np.zeros(len(strata), dtype=int)
    min_questions = np.zeros(len(strata), dtype=int)
    below_floor = np.zeros(len(strata), dtype=int)
    total_questions = np.zeros(len(strata), dtype=int)
    # Single source of truth: the enforced per-skill assessment floor (quality.py),
    # not a hand-typed literal that can silently diverge from the gate.
    quality_floor = MIN_ASSESSMENTS_PER_SKILL
    for stratum in strata:
        skills = [skill for skill in graph.skills if skill.stratum is stratum]
        question_counts = [len(skill.assessments) for skill in skills]
        skill_counts[stratum.order] = len(skills)
        min_questions[stratum.order] = min(question_counts) if question_counts else 0
        below_floor[stratum.order] = sum(
            1 for question_count in question_counts if question_count < quality_floor
        )
        total_questions[stratum.order] = sum(question_counts)

    labels = [stratum.value.replace("_", " ") for stratum in strata]
    fig, (bars, audit) = plt.subplots(
        1,
        2,
        figsize=(11.2, 6.9),
        gridspec_kw={"width_ratios": [1.0, 1.45]},
        constrained_layout=False,
    )
    fig.subplots_adjust(top=0.83, bottom=0.12, left=0.16, right=0.99, wspace=0.16)
    fig.suptitle(
        "Assessment-depth floor audit by stratum",
        x=0.16,
        y=0.975,
        ha="left",
        fontsize=13,
        fontweight="bold",
        color=_INK,
    )
    y_pos = np.arange(len(strata))
    colors = [_PALETTE[stratum.order] for stratum in strata]
    bar_artists = bars.barh(y_pos, skill_counts, color=colors)
    bars.set_yticks(y_pos)
    bars.set_yticklabels(labels, fontsize=_FONT_SMALL)
    bars.invert_yaxis()
    bars.set_xlabel("skills with exported quizzes")
    bars.set_ylim(len(strata) - 0.5, -1.35)
    _add_panel_label(bars, "A", "Quiz-bearing skills", y=0.99)
    _add_axis_subtitle(
        bars,
        "Bars are counts; the table verifies the shared floor.",
        y=0.91,
    )
    _label_horizontal_bars(bars, bar_artists, skill_counts.astype(float), suffix="")
    bars.set_xlim(0, max(1, int(skill_counts.max())) * 1.28)
    _style_axis(bars, grid_axis="x", hide=("top", "right", "left"))

    audit.axis("off")
    _add_panel_label(audit, "B", "Floor and assessment-load contract")
    audit.text(
        0.02,
        0.94,
        f"Every exported skill must carry a quiz with at least "
        f"{MIN_ASSESSMENTS_PER_SKILL} questions.",
        transform=audit.transAxes,
        ha="left",
        va="center",
        fontsize=_FONT_SMALL,
        color=_MUTED,
    )
    headers = ("stratum", "min q", "below floor", "q / skill", "status")
    x_positions = (0.02, 0.39, 0.55, 0.74, 0.91)
    for x, header in zip(x_positions, headers, strict=True):
        audit.text(
            x,
            0.84,
            header,
            transform=audit.transAxes,
            ha="left" if header == "stratum" else "center",
            va="center",
            fontsize=_FONT_SMALL,
            fontweight="bold",
            color=_MUTED,
        )
    for row, stratum in enumerate(strata):
        y = 0.76 - row * 0.083
        fill = _PALETTE_LIGHT[stratum.order] if row % 2 == 0 else "#FFFFFF"
        audit.add_patch(
            plt.Rectangle(
                (0.01, y - 0.035),
                0.98,
                0.063,
                transform=audit.transAxes,
                facecolor=fill,
                edgecolor=_LINE,
                linewidth=0.5,
            )
        )
        q_per_skill = (
            total_questions[stratum.order] / skill_counts[stratum.order]
            if skill_counts[stratum.order]
            else 0
        )
        status = "PASS" if below_floor[stratum.order] == 0 else "REVIEW"
        status_color = _OK if status == "PASS" else _ALERT
        values = (
            stratum.value.replace("_", " "),
            str(int(min_questions[stratum.order])),
            str(int(below_floor[stratum.order])),
            f"{q_per_skill:.1f}",
            status,
        )
        for x, value, header in zip(x_positions, values, headers, strict=True):
            audit.text(
                x,
                y,
                value,
                transform=audit.transAxes,
                ha="left" if header == "stratum" else "center",
                va="center",
                fontsize=_FONT_SMALL,
                fontweight="bold" if header == "status" else "normal",
                color=status_color if header == "status" else _INK,
            )
    _add_badge(
        audit,
        f"floor satisfied: min {int(min_questions.min())} questions",
        xy=(0.02, 0.08),
        color=_OK if not below_floor.any() else _ALERT,
    )
    return _save_figure(
        fig,
        path,
        note=(
            "Assessment-floor audit is derived from exported quiz tuples after "
            "curriculum-quality validation."
        ),
    )


def plot_curriculum_stratum_balance(graph: CurriculumGraph, path: Path) -> Path:
    """Show whether curriculum expansion is balanced across strata."""
    path = _prepare_path(path)
    strata = list(ALL_STRATA)
    labels = [stratum.value.replace("_", "\n") for stratum in strata]
    skills_by_stratum = np.array(
        [sum(skill.stratum is stratum for skill in graph.skills) for stratum in strata],
        dtype=float,
    )
    subjects_by_stratum = np.array(
        [
            sum(subject.stratum is stratum for subject in graph.subjects)
            for stratum in strata
        ],
        dtype=float,
    )
    assessments_by_stratum = np.array(
        [
            sum(
                len(skill.assessments)
                for skill in graph.skills
                if skill.stratum is stratum
            )
            for stratum in strata
        ],
        dtype=float,
    )
    edges_by_target = np.zeros(len(strata), dtype=float)
    for _source, target in graph.prerequisite_edges():
        edges_by_target[graph.get_skill(target).stratum.order] += 1
    skills_per_subject = np.divide(
        skills_by_stratum,
        subjects_by_stratum,
        out=np.zeros_like(skills_by_stratum),
        where=subjects_by_stratum != 0,
    )
    questions_per_skill = np.divide(
        assessments_by_stratum,
        skills_by_stratum,
        out=np.zeros_like(assessments_by_stratum),
        where=skills_by_stratum != 0,
    )
    incoming_edges_per_skill = np.divide(
        edges_by_target,
        skills_by_stratum,
        out=np.zeros_like(edges_by_target),
        where=skills_by_stratum != 0,
    )

    fig, (left, load, ratio) = plt.subplots(
        1,
        3,
        figsize=(13.2, 6.6),
        gridspec_kw={"width_ratios": [1.0, 1.04, 1.15]},
        constrained_layout=False,
    )
    fig.subplots_adjust(top=0.84, bottom=0.24, left=0.10, right=0.99, wspace=0.24)
    y_pos = np.arange(len(strata))
    colors = [_PALETTE[stratum.order] for stratum in strata]
    left.barh(y_pos, skills_by_stratum, color=colors)
    left.set_yticks(y_pos)
    left.set_yticklabels(labels, fontsize=_FONT_SMALL)
    left.invert_yaxis()
    left.set_xlabel("skills")
    _add_panel_label(left, "A", "Skill and subject coverage by stratum")
    max_skills = float(skills_by_stratum.max()) if skills_by_stratum.size else 1.0
    for y, skills, subjects in zip(
        y_pos, skills_by_stratum, subjects_by_stratum, strict=True
    ):
        left.text(
            skills + max(1.0, max_skills * 0.025),
            y,
            f"{int(skills)} skills / {int(subjects)} subjects",
            va="center",
            fontsize=_FONT_SMALL,
            color="#111827",
        )
    left.set_xlim(0, max_skills * 1.38)

    height = 0.34
    load.barh(
        y_pos - height / 2,
        assessments_by_stratum,
        height=height,
        color=_OK,
        label="assessment questions",
    )
    load.barh(
        y_pos + height / 2,
        edges_by_target,
        height=height,
        color=_WARN,
        label="incoming prerequisite edges",
    )
    load.set_yticks(y_pos)
    load.set_yticklabels([])
    load.invert_yaxis()
    load.set_xlabel("count")
    _add_panel_label(load, "B", "Assessment and dependency load")
    max_right = float(max(assessments_by_stratum.max(), edges_by_target.max(), 1.0))
    for y, assessments, edges in zip(
        y_pos, assessments_by_stratum, edges_by_target, strict=True
    ):
        load.text(
            assessments + max(1.0, max_right * 0.02),
            y - height / 2,
            str(int(assessments)),
            va="center",
            fontsize=_FONT_SMALL,
        )
        load.text(
            edges + max(1.0, max_right * 0.02),
            y + height / 2,
            str(int(edges)),
            va="center",
            fontsize=_FONT_SMALL,
        )
    load.set_xlim(0, max_right * 1.22)

    marker_series = [
        ("skills / subject", skills_per_subject, _PALETTE[0], "o"),
        ("questions / skill", questions_per_skill, _PALETTE[3], "s"),
        ("incoming edges / skill", incoming_edges_per_skill, _PALETTE[4], "^"),
    ]
    for label, values, color, marker in marker_series:
        ratio.plot(
            values,
            y_pos,
            marker=marker,
            linestyle="None",
            markersize=5.5,
            color=color,
            label=label,
            zorder=3,
        )
        for y, value in zip(y_pos, values, strict=True):
            ratio.text(
                value + 0.12,
                y,
                f"{value:.1f}",
                va="center",
                fontsize=_FONT_SMALL,
                color=color,
            )
    ratio.set_yticks(y_pos)
    ratio.set_yticklabels([])
    ratio.invert_yaxis()
    ratio.set_xlabel("normalized measure")
    _add_panel_label(ratio, "C", "Companion per-unit measures")
    _add_axis_subtitle(
        ratio,
        "Normalized dots bound raw-count interpretation.",
    )
    max_ratio = float(
        max(
            skills_per_subject.max(),
            questions_per_skill.max(),
            incoming_edges_per_skill.max(),
            1.0,
        )
    )
    ratio.set_xlim(0, max_ratio * 1.24)

    for axis in (left, load, ratio):
        axis.set_ylim(len(strata) - 0.5, -1.05)

    load_handles, load_labels = load.get_legend_handles_labels()
    ratio_handles, ratio_labels = ratio.get_legend_handles_labels()
    fig.legend(
        load_handles + ratio_handles,
        load_labels + ratio_labels,
        loc="lower center",
        bbox_to_anchor=(0.60, 0.065),
        ncol=3,
        frameon=False,
        fontsize=_FONT_SMALL,
    )

    for ax in (left, load, ratio):
        _style_axis(ax, grid_axis="x")
    return _save_figure(
        fig,
        path,
        note=(
            "Raw stratum volume is paired with per-skill and per-subject normalized "
            "measures to bound imbalance interpretation."
        ),
    )
