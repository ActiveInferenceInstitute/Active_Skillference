"""Skill-name atlas figure and helpers."""

from __future__ import annotations

import os
import re
import textwrap
from collections import Counter
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

from .style import (
    _FONT_SMALL,
    _INK,
    _MIN_FIGURE_FONT_SIZE,
    _MUTED,
    _PALETTE,
    _SKILL_ATLAS_STOPWORDS,
    _SURFACE,
    _metric_card,
    _prepare_path,
    _save_figure,
    _style_axis,
)


def plot_skill_name_atlas(graph: CurriculumGraph, path: Path) -> Path:
    """Render a second-page atlas from every named curriculum skill."""
    path = _prepare_path(path)
    payload = _skill_name_atlas_payload(graph)
    top_terms = payload["topTerms"]
    strata_rows = payload["strata"]
    spine = _longest_path_skills(graph)

    fig = plt.figure(figsize=(13.6, 6.8), facecolor=_SURFACE)
    title_ax = fig.add_axes((0.04, 0.8, 0.92, 0.16))
    lane_ax = fig.add_axes((0.12, 0.15, 0.24, 0.58))
    term_ax = fig.add_axes((0.42, 0.15, 0.31, 0.58))
    path_ax = fig.add_axes((0.78, 0.15, 0.18, 0.58))

    title_ax.axis("off")
    title_ax.text(
        0.02,
        0.68,
        "Named Skill Atlas",
        transform=title_ax.transAxes,
        ha="left",
        va="center",
        fontsize=24,
        fontweight="bold",
    )
    title_ax.text(
        0.02,
        0.25,
        (
            f"{payload['skillCount']} unique skill names tokenized across "
            f"{payload['subjectCount']} subjects and {payload['stratumCount']} strata"
        ),
        transform=title_ax.transAxes,
        ha="left",
        va="center",
        fontsize=10,
        color=_MUTED,
    )
    _metric_card(
        title_ax,
        x=0.66,
        y=0.12,
        width=0.13,
        height=0.72,
        value=str(payload["tokenCount"]),
        label="named terms",
        color=_PALETTE[0],
    )
    _metric_card(
        title_ax,
        x=0.81,
        y=0.12,
        width=0.15,
        height=0.72,
        value=str(payload["pathLength"]),
        label="spine nodes",
        color=_PALETTE[2],
    )

    y_pos = np.arange(len(strata_rows))
    skill_counts = np.array([row["skills"] for row in strata_rows], dtype=float)
    lane_ax.barh(
        y_pos,
        skill_counts,
        color=[_PALETTE[int(index) % len(_PALETTE)] for index in y_pos],
        alpha=0.88,
    )
    lane_ax.set_yticks(y_pos)
    lane_ax.set_yticklabels(
        [
            (f"{row['label']}\n{row['skills']} skills / {row['subjects']} subjects")
            for row in strata_rows
        ],
        fontsize=_FONT_SMALL,
    )
    lane_ax.invert_yaxis()
    lane_ax.set_xlabel("named skills")
    lane_ax.set_title(
        "A  Stratum lanes\nexact skill and subject counts",
        loc="left",
        fontsize=_FONT_SMALL,
        fontweight="bold",
        pad=8,
    )
    for y, row in zip(y_pos, strata_rows, strict=True):
        lane_ax.text(
            float(row["skills"]) + max(1.0, float(skill_counts.max()) * 0.03),
            float(y),
            str(row["skills"]),
            va="center",
            fontsize=_FONT_SMALL,
            fontweight="bold",
        )
    lane_ax.set_xlim(0, float(skill_counts.max()) * 1.25)
    _style_axis(lane_ax, grid_axis="x", hide=("top", "right", "left"))

    term_ax.axis("off")
    term_ax.text(
        0.0,
        1.05,
        "B  Readable weighted terms",
        transform=term_ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=_FONT_SMALL,
        fontweight="bold",
    )
    term_ax.text(
        0.0,
        1.0,
        textwrap.fill(
            "All names feed the token ledger; visible terms show the strongest signals.",
            width=56,
        ),
        transform=term_ax.transAxes,
        ha="left",
        va="top",
        fontsize=_FONT_SMALL,
        color=_MUTED,
    )
    shown_terms = top_terms[:19]
    counts = [int(row["count"]) for row in shown_terms] or [1]
    min_count = min(counts)
    max_count = max(counts)
    stratum_by_value = {stratum.value: stratum for stratum in ALL_STRATA}
    for index, row in enumerate(shown_terms):
        count = int(row["count"])
        scale = (count - min_count) / max(1, max_count - min_count)
        fontsize = _MIN_FIGURE_FONT_SIZE + 7.0 * scale
        stratum = stratum_by_value.get(str(row["stratum"]))
        color = _PALETTE[stratum.order] if stratum is not None else _MUTED
        if index == 0:
            term_ax.text(
                0.5,
                0.81,
                str(row["term"]),
                transform=term_ax.transAxes,
                ha="center",
                va="center",
                fontsize=20,
                fontweight="bold",
                color=color,
                bbox={
                    "alpha": 0.88,
                    "boxstyle": "round,pad=0.22",
                    "edgecolor": "#e5e7eb",
                    "facecolor": "white",
                    "linewidth": 0.7,
                },
            )
            term_ax.text(
                0.5,
                0.735,
                f"{count} skill-name uses",
                transform=term_ax.transAxes,
                ha="center",
                va="top",
                fontsize=_FONT_SMALL,
                color=_MUTED,
            )
            continue
        column = (index - 1) % 3
        line = (index - 1) // 3
        x = 0.04 + column * 0.32
        y_coord = 0.64 - line * 0.072
        term_ax.text(
            x,
            y_coord,
            str(row["term"]),
            transform=term_ax.transAxes,
            ha="left",
            va="center",
            fontsize=fontsize,
            fontweight="bold" if index < 10 else "normal",
            color=color,
        )
        term_ax.text(
            x,
            y_coord - 0.03,
            str(count),
            transform=term_ax.transAxes,
            ha="left",
            va="top",
            fontsize=_FONT_SMALL,
            color=_MUTED,
        )
    term_ax.text(
        0.0,
        0.03,
        textwrap.fill(
            "Representative labels; the complete name ledger remains in the curriculum graph.",
            width=56,
        ),
        transform=term_ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=_FONT_SMALL,
        color=_MUTED,
    )

    path_ax.axis("off")
    path_ax.text(
        0.0,
        1.05,
        "C  Dependency spine",
        transform=path_ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=_FONT_SMALL,
        fontweight="bold",
    )
    path_ax.text(
        0.0,
        1.0,
        "Longest-path checkpoints.",
        transform=path_ax.transAxes,
        ha="left",
        va="top",
        fontsize=_FONT_SMALL,
        color=_MUTED,
    )
    label_indices = _spine_label_indices(spine)
    if len(label_indices) > 6:
        keep = np.linspace(0, len(label_indices) - 1, 6, dtype=int)
        label_indices = tuple(
            label_indices[index] for index in sorted(set(keep.tolist()))
        )
    labelled = [spine[index] for index in label_indices]
    y_values = np.linspace(0.74, 0.22, max(1, len(labelled)))
    x_node = 0.12
    if len(y_values) > 1:
        path_ax.plot(
            [x_node] * len(y_values),
            y_values,
            transform=path_ax.transAxes,
            color="#94a3b8",
            linewidth=1.2,
            zorder=1,
        )
    for y_val, skill in zip(y_values, labelled, strict=True):
        color = _PALETTE[skill.stratum.order]
        path_ax.scatter(
            [x_node],
            [float(y_val)],
            transform=path_ax.transAxes,
            s=92,
            color=color,
            edgecolors="white",
            linewidths=0.8,
            zorder=2,
        )
        path_ax.text(
            0.19,
            float(y_val),
            "\n".join(textwrap.wrap(skill.name, width=20)[:2]),
            transform=path_ax.transAxes,
            ha="left",
            va="center",
            fontsize=_FONT_SMALL,
            color=_INK,
        )
    path_ax.text(
        0.03,
        0.04,
        textwrap.fill(
            f"{len(labelled)} checkpoints shown; full spine has {payload['pathLength']} nodes.",
            width=34,
        ),
        transform=path_ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=_FONT_SMALL,
        color=_MUTED,
    )

    return _save_figure(
        fig,
        path,
        dpi=180,
        note=(
            f"Second-page atlas tokenizes all {payload['skillCount']} skill names; "
            "visible labels are readable representatives, not a complete printed index."
        ),
    )


def _skill_name_atlas_payload(graph: CurriculumGraph) -> dict[str, Any]:
    """Return deterministic data used by the page-two skill atlas."""
    levels = graph.levels()
    skills = sorted(
        graph.skills,
        key=lambda skill: (skill.stratum.order, levels[skill.skill_id], skill.skill_id),
    )
    token_counts: Counter[str] = Counter()
    token_strata: dict[str, Counter[str]] = {}
    for skill in skills:
        for token in _skill_name_tokens(skill.name):
            token_counts[token] += 1
            token_strata.setdefault(token, Counter())[skill.stratum.value] += 1

    strata_rows: list[dict[str, Any]] = []
    edges = graph.prerequisite_edges()
    for stratum in ALL_STRATA:
        stratum_skills = [skill for skill in skills if skill.stratum is stratum]
        stratum_skill_ids = {skill.skill_id for skill in stratum_skills}
        strata_rows.append(
            {
                "incomingEdges": sum(
                    1 for _prereq, dependent in edges if dependent in stratum_skill_ids
                ),
                "label": stratum.value.replace("_", " "),
                "representativeSkills": _sample_skill_names(
                    stratum_skills,
                    levels,
                    sample_size=3,
                ),
                "skills": len(stratum_skills),
                "subjects": sum(
                    1 for subject in graph.subjects if subject.stratum is stratum
                ),
            }
        )

    top_terms = []
    for token, count in token_counts.most_common(60):
        dominant = token_strata[token].most_common(1)[0][0]
        top_terms.append({"count": count, "stratum": dominant, "term": token})

    spine = _longest_path_skills(graph)
    return {
        "pathLength": len(spine),
        "skillCount": len(skills),
        "strata": strata_rows,
        "stratumCount": len(ALL_STRATA),
        "subjectCount": len(graph.subjects),
        "tokenCount": len(token_counts),
        "topTerms": top_terms,
    }


def _skill_name_tokens(name: str) -> tuple[str, ...]:
    tokens = []
    for token in re.findall(r"[A-Za-z][A-Za-z0-9]+", name.lower()):
        if len(token) < 3 or token in _SKILL_ATLAS_STOPWORDS:
            continue
        tokens.append(token)
    return tuple(tokens)


def _sample_skill_names(
    skills: list[Any],
    levels: Mapping[str, int],
    *,
    sample_size: int,
) -> tuple[str, ...]:
    if not skills:
        return ()
    ordered = sorted(skills, key=lambda skill: (levels[skill.skill_id], skill.skill_id))
    if len(ordered) <= sample_size:
        return tuple(skill.name for skill in ordered)
    indices = np.linspace(0, len(ordered) - 1, sample_size)
    return tuple(ordered[round(index)].name for index in indices)


def _longest_path_skills(graph: CurriculumGraph) -> list[Any]:
    levels = graph.levels()
    by_dependent: dict[str, list[str]] = {}
    for prereq_id, dependent_id in graph.prerequisite_edges():
        by_dependent.setdefault(dependent_id, []).append(prereq_id)
    current = max(
        graph.skills,
        key=lambda skill: (levels[skill.skill_id], skill.skill_id),
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
    return [graph.get_skill(skill_id) for skill_id in path_ids]


def _spine_label_indices(skills: list[Any]) -> tuple[int, ...]:
    if not skills:
        return ()
    label_indices = {0, len(skills) - 1}
    previous_order: int | None = None
    for index, skill in enumerate(skills):
        if skill.stratum.order != previous_order:
            label_indices.add(index)
            previous_order = skill.stratum.order
    return tuple(sorted(label_indices))
