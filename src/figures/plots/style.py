from __future__ import annotations

import os
from collections.abc import Iterable
from pathlib import Path
from typing import Any, Literal

import matplotlib
import numpy as np

os.environ.setdefault("MPLBACKEND", "Agg")
matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

_COLOR_FAMILIES = {
    "blue": {"light": "#D7E2F7", "base": "#5477C4", "dark": "#244A93"},
    "gold": {"light": "#F4E7A4", "base": "#D7B633", "dark": "#9A7B16"},
    "orange": {"light": "#F5C5AD", "base": "#CC6F47", "dark": "#8D3F22"},
    "olive": {"light": "#CFE5A8", "base": "#71B436", "dark": "#3E7A1E"},
    "pink": {"light": "#E7BCD7", "base": "#BD569B", "dark": "#823467"},
    "sky": {"light": "#D6EDF8", "base": "#5B9BD5", "dark": "#2F6FAE"},
}
_PALETTE = (
    _COLOR_FAMILIES["blue"]["base"],
    _COLOR_FAMILIES["olive"]["base"],
    _COLOR_FAMILIES["orange"]["base"],
    _COLOR_FAMILIES["pink"]["base"],
    _COLOR_FAMILIES["gold"]["base"],
    _COLOR_FAMILIES["sky"]["base"],
    "#8C6D1F",
    "#4B5563",
)
_PALETTE_LIGHT = (
    _COLOR_FAMILIES["blue"]["light"],
    _COLOR_FAMILIES["olive"]["light"],
    _COLOR_FAMILIES["orange"]["light"],
    _COLOR_FAMILIES["pink"]["light"],
    _COLOR_FAMILIES["gold"]["light"],
    _COLOR_FAMILIES["sky"]["light"],
    "#E8DAA2",
    "#E5E7EB",
)
_FLOW_CMAP = LinearSegmentedColormap.from_list(
    "active_skillference_flow",
    ["#F7FAFF", _COLOR_FAMILIES["blue"]["light"], _COLOR_FAMILIES["blue"]["dark"]],
)
_INK = "#111827"
_MUTED = "#4b5563"
_GRID = "#e5e7eb"
_LINE = "#d1d5db"
_SURFACE = "#f8fafc"
_PANEL = "#ffffff"
_BOUND = _PALETTE[0]
_OK = _PALETTE[1]
_WARN = _PALETTE[4]
_ALERT = _PALETTE[2]
_NOTE = (
    "Generated from validated project artifacts; visual summaries are not learner-outcome "
    "or biological-validity evidence."
)
_FONT_TITLE = 16.0
_FONT_SUBTITLE = 12.0
_FONT_LABEL = 11.0
_FONT_SMALL = 9.5
_FONT_NOTE = 8.5
_MIN_FIGURE_FONT_SIZE = 9.5


class FigureRegistryError(ValueError):
    """Raised when figure registry counts or files drift from rendered outputs."""


_SKILL_ATLAS_STOPWORDS = frozenset(
    {
        "active",
        "and",
        "capstone",
        "checks",
        "for",
        "from",
        "handoff",
        "inference",
        "into",
        "review",
        "skill",
        "skills",
        "skilltree",
        "the",
        "using",
        "with",
    }
)

plt.rcParams.update(
    {
        "axes.edgecolor": "#9ca3af",
        "axes.labelcolor": _MUTED,
        "axes.titlecolor": _INK,
        "font.family": "DejaVu Sans",
        "font.size": 11,
        "figure.facecolor": "white",
        "savefig.facecolor": "white",
        "text.color": _INK,
        "xtick.color": _MUTED,
        "ytick.color": _MUTED,
    }
)


def _prepare_path(path: Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _style_axis(
    ax: plt.Axes,
    *,
    grid_axis: Literal["both", "x", "y"] | None = None,
    hide: tuple[str, ...] = ("top", "right"),
) -> None:
    """Apply the shared manuscript/dashboard figure grammar to one axis."""
    for spine in hide:
        ax.spines[spine].set_visible(False)
    if grid_axis:
        ax.grid(axis=grid_axis, color=_GRID, linewidth=0.8, zorder=0)
        ax.set_axisbelow(True)


def _add_panel_label(
    ax: plt.Axes, label: str, title: str | None = None, *, y: float = 0.992
) -> None:
    text = label if title is None else f"{label}  {title}"
    ax.text(
        0.0,
        y,
        text,
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=_FONT_LABEL,
        fontweight="bold",
        color=_INK,
        bbox={
            "facecolor": "white",
            "edgecolor": "none",
            "alpha": 0.9,
            "pad": 1.5,
        },
    )


def _add_badge(
    ax: plt.Axes,
    text: str,
    *,
    xy: tuple[float, float] = (0.02, 0.96),
    color: str = _OK,
) -> None:
    ax.text(
        xy[0],
        xy[1],
        text,
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=_FONT_SMALL,
        fontweight="bold",
        color=_INK,
        bbox={
            "boxstyle": "round,pad=0.35",
            "facecolor": "white",
            "edgecolor": color,
            "linewidth": 1.1,
        },
    )


def _label_horizontal_bars(
    ax: plt.Axes,
    bars: Iterable[Any],
    values: np.ndarray,
    *,
    suffix: str = "",
    fontsize: float = _FONT_SMALL,
) -> None:
    max_value = float(values.max()) if values.size else 1.0
    for bar, value in zip(bars, values, strict=True):
        ax.text(
            bar.get_width() + max(0.2, max_value * 0.025),
            bar.get_y() + bar.get_height() / 2,
            f"{int(value)}{suffix}",
            va="center",
            fontsize=fontsize,
            color=_INK,
        )


def _add_source_note(fig: plt.Figure, note: str = _NOTE) -> None:
    fig.text(
        0.01,
        0.006,
        note,
        ha="left",
        va="bottom",
        fontsize=_FONT_NOTE,
        color=_MUTED,
    )


def _add_axis_subtitle(ax: plt.Axes, text: str, *, y: float = 0.955) -> None:
    ax.text(
        0.0,
        y,
        text,
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=_FONT_SMALL,
        color=_MUTED,
    )


def _metric_card(
    ax: plt.Axes,
    *,
    x: float,
    y: float,
    width: float,
    height: float,
    value: str,
    label: str,
    color: str,
) -> None:
    ax.add_patch(
        plt.Rectangle(
            (x, y),
            width,
            height,
            transform=ax.transAxes,
            facecolor=_PANEL,
            edgecolor=color,
            linewidth=1.4,
            zorder=1,
        )
    )
    ax.text(
        x + 0.04 * width,
        y + 0.62 * height,
        value,
        transform=ax.transAxes,
        ha="left",
        va="center",
        fontsize=15,
        fontweight="bold",
        color=_INK,
        zorder=2,
    )
    ax.text(
        x + 0.04 * width,
        y + 0.26 * height,
        label,
        transform=ax.transAxes,
        ha="left",
        va="center",
        fontsize=_FONT_SMALL,
        color=_MUTED,
        zorder=2,
    )


def _line_end_label(
    ax: plt.Axes,
    *,
    x: float,
    y: float,
    label: str,
    color: str,
    x_offset: float = 0.02,
) -> None:
    ax.text(
        x + x_offset,
        y,
        label,
        ha="left",
        va="center",
        fontsize=_FONT_SMALL,
        color=color,
        fontweight="bold",
    )


def _save_figure(
    fig: plt.Figure, path: Path, *, dpi: int = 150, note: str = _NOTE
) -> Path:
    engine: Any = fig.get_layout_engine()
    if engine is not None:
        try:
            engine.set(rect=(0.0, 0.06, 1.0, 0.94))
        except AttributeError:
            pass
    _add_source_note(fig, note)
    fig.savefig(path, dpi=dpi)
    plt.close(fig)
    return path


def _short_label(value: str, *, width: int = 28) -> str:
    return value if len(value) <= width else value[: max(0, width - 3)] + "..."
