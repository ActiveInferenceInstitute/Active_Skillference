"""Scholarship figure: source health."""

from __future__ import annotations

import os
import textwrap
from collections import Counter
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import matplotlib

os.environ.setdefault("MPLBACKEND", "Agg")
matplotlib.use("Agg")

import matplotlib.pyplot as plt

from .registry_helpers import (
    _int_from_mapping,
)
from .style import (
    _ALERT,
    _COLOR_FAMILIES,
    _FONT_SMALL,
    _INK,
    _LINE,
    _MUTED,
    _OK,
    _PANEL,
    _SURFACE,
    _WARN,
    _add_axis_subtitle,
    _add_badge,
    _prepare_path,
    _save_figure,
)


def plot_scholarship_source_health(audit: Mapping[str, Any], path: Path) -> Path:
    """Render source-health status by issue state and online/offline mode."""
    path = _prepare_path(path)
    summary = audit.get("summary", {})
    if not isinstance(summary, Mapping):
        summary = {}
    checked_online = bool(audit.get("checkedOnline", False))
    issues = audit.get("issues", ())
    if not isinstance(issues, (list, tuple)):
        issues = ()
    source_count = _int_from_mapping(summary, "sources")
    issue_count = _int_from_mapping(summary, "issueCount")
    online_count = _int_from_mapping(summary, "onlineCheckedSources")
    online_results = audit.get("onlineResults", {})
    if not isinstance(online_results, Mapping):
        online_results = {}
    status_counts: Counter[str] = Counter()
    for raw_status in online_results.values():
        status = str(raw_status)
        if status.startswith("ok:"):
            bucket = "reachable"
        elif "http_error:403" in status:
            bucket = "bot-blocked"
        elif status.startswith(("timeout:", "url_error:", "tls_error:")):
            bucket = "unreachable"
        else:
            bucket = "review"
        status_counts[bucket] += 1
    reachable_count = status_counts["reachable"]
    bot_blocked_count = status_counts["bot-blocked"]
    unreachable_count = status_counts["unreachable"]
    review_count = status_counts["review"]
    online_issue_count = bot_blocked_count + unreachable_count + review_count
    metadata_issue_count = max(issue_count - online_issue_count, 0)

    fig, ax = plt.subplots(figsize=(9.4, 5.8), constrained_layout=True)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.set_title(
        "Source-health audit separates metadata, reachability, and release mode"
    )
    _add_axis_subtitle(
        ax,
        "Offline artifacts verify source metadata; strict online runs add DOI/URL reachability and record bot-blocked endpoints.",
        y=0.94,
    )
    _add_badge(
        ax,
        "source integrity, not source truth",
        xy=(0.02, 0.84),
        color=_OK if metadata_issue_count == 0 else _ALERT,
    )
    cards = [
        (
            str(source_count),
            "matrixed sources",
            _COLOR_FAMILIES["blue"]["base"],
            "source rows checked locally",
        ),
        (
            str(metadata_issue_count),
            "metadata issues",
            _OK if metadata_issue_count == 0 else _ALERT,
            "BibTeX, locator, lane, and role checks",
        ),
        (
            f"{reachable_count}/{online_count}" if checked_online else "not run",
            "reachable online",
            _OK if checked_online and online_issue_count == 0 else _WARN,
            "strict mode checks DOI and URL endpoints",
        ),
        (
            str(online_issue_count) if checked_online else "offline",
            "network issues",
            _WARN if checked_online and online_issue_count else _OK,
            "bot blocks stay separate from metadata",
        ),
    ]
    for index, (value, label, color, detail) in enumerate(cards):
        x = 0.035 + index * 0.235
        ax.add_patch(
            plt.Rectangle(
                (x, 0.51),
                0.215,
                0.27,
                transform=ax.transAxes,
                facecolor=_PANEL,
                edgecolor=color,
                linewidth=1.25,
            )
        )
        ax.text(
            x + 0.018,
            0.705,
            value,
            transform=ax.transAxes,
            ha="left",
            va="center",
            fontsize=15,
            fontweight="bold",
            color=_INK,
        )
        ax.text(
            x + 0.018,
            0.625,
            label,
            transform=ax.transAxes,
            ha="left",
            va="center",
            fontsize=_FONT_SMALL,
            color=_INK,
        )
        ax.text(
            x + 0.018,
            0.575,
            textwrap.fill(detail, width=24),
            transform=ax.transAxes,
            ha="left",
            va="top",
            fontsize=_FONT_SMALL,
            color=_MUTED,
        )
    issue_rows = (
        ["no local source-health issues detected"]
        if not issues
        else [str(issue) for issue in issues[:5]]
    )
    table_rows = [
        (
            "Metadata contract",
            "PASS" if metadata_issue_count == 0 else "REVIEW",
            "no local metadata issues detected"
            if metadata_issue_count == 0
            else issue_rows[0],
        ),
        (
            "Network mode",
            "ONLINE" if checked_online else "OFFLINE",
            f"{online_count} DOI/URL endpoints checked"
            if checked_online
            else "run strict online validation for reachability evidence",
        ),
        (
            "Reachability detail",
            "RECORDED" if checked_online else "NOT RUN",
            (
                f"{reachable_count} reachable; {bot_blocked_count} bot-blocked; "
                f"{unreachable_count + review_count} need review"
            )
            if checked_online
            else "offline generation does not certify public URL availability",
        ),
        (
            "Release boundary",
            "STRICT" if checked_online else "LOCAL",
            "online failures are explicit release evidence, not hidden pass counts"
            if checked_online
            else "local artifacts remain reproducible without network access",
        ),
    ]
    for index, (check, status, detail) in enumerate(table_rows):
        y = 0.37 - index * 0.092
        ax.add_patch(
            plt.Rectangle(
                (0.04, y - 0.034),
                0.92,
                0.074,
                transform=ax.transAxes,
                facecolor=_SURFACE if index % 2 == 0 else _PANEL,
                edgecolor=_LINE,
                linewidth=0.7,
            )
        )
        if status in {"PASS", "ONLINE"}:
            color = _OK
        elif status in {"REVIEW"}:
            color = _ALERT
        else:
            color = _WARN
        ax.text(
            0.065, y, check, transform=ax.transAxes, va="center", fontsize=_FONT_SMALL
        )
        ax.text(
            0.36,
            y,
            status,
            transform=ax.transAxes,
            va="center",
            fontsize=_FONT_SMALL,
            fontweight="bold",
            color=color,
        )
        ax.text(
            0.53,
            y,
            detail,
            transform=ax.transAxes,
            va="center",
            fontsize=_FONT_SMALL,
            color=_MUTED,
        )
    return _save_figure(
        fig,
        path,
        note="Online checked sources are reported separately from offline source-matrix health.",
    )
