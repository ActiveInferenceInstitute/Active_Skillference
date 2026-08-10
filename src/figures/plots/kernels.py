from __future__ import annotations

import os
from pathlib import Path
from typing import cast

import matplotlib
import numpy as np

os.environ.setdefault("MPLBACKEND", "Agg")
matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.patches import Patch

from src.kernels.examples import (
    efe_precision_sweep,
    planning_lookahead_data,
    predictive_coding_data,
    vfe_belief_sweep,
)
from src.kernels.inference import bayes_posterior
from src.provenance.claims import ClaimRegistry

from .style import (
    _ALERT,
    _FONT_SMALL,
    _INK,
    _LINE,
    _MUTED,
    _OK,
    _PALETTE,
    _WARN,
    _add_axis_subtitle,
    _add_badge,
    _add_panel_label,
    _line_end_label,
    _prepare_path,
    _save_figure,
    _style_axis,
)


def plot_free_energy_descent(registry: ClaimRegistry, path: Path) -> Path:
    """Line plot: VFE over beliefs, tight at posterior and above surprise elsewhere."""
    path = _prepare_path(path)
    sweep = vfe_belief_sweep()
    beliefs = np.asarray(sweep["belief_present"], dtype=np.float64)
    free_energy = np.asarray(sweep["free_energy"], dtype=np.float64)
    posterior_present = float(sweep["posterior_present"])
    neg_log_evidence = float(sweep["neg_log_evidence"])
    uniform_free_energy = float(registry.value("vfe_descent_start"))

    fig, ax = plt.subplots(figsize=(8, 5), constrained_layout=True)
    ax.plot(
        beliefs,
        free_energy,
        color=_PALETTE[0],
        linewidth=2.0,
        label="variational free energy $F(q)$",
    )
    ax.axhline(
        neg_log_evidence,
        color=_PALETTE[2],
        linestyle="--",
        linewidth=1.5,
        label=r"$-\ln p(o)$",
    )
    ax.axvline(
        posterior_present,
        color=_PALETTE[1],
        linestyle=":",
        linewidth=1.8,
        label="exact posterior",
    )
    ax.scatter(
        [0.5, posterior_present],
        [uniform_free_energy, neg_log_evidence],
        color=[_PALETTE[4], _PALETTE[1]],
        edgecolors="white",
        linewidths=0.8,
        zorder=3,
    )
    ax.annotate(
        f"uniform belief\nF={uniform_free_energy:.3f}",
        xy=(0.5, uniform_free_energy),
        xytext=(0.57, uniform_free_energy + 0.25),
        arrowprops={"arrowstyle": "->", "color": "#4b5563", "lw": 0.8},
        fontsize=_FONT_SMALL,
    )
    ax.annotate(
        f"posterior={posterior_present:.3f}\nF={neg_log_evidence:.3f}",
        xy=(posterior_present, neg_log_evidence),
        xytext=(posterior_present + 0.08, neg_log_evidence + 0.34),
        arrowprops={"arrowstyle": "->", "color": "#4b5563", "lw": 0.8},
        fontsize=_FONT_SMALL,
    )
    _line_end_label(
        ax,
        x=float(beliefs[-1]),
        y=float(free_energy[-1]),
        label=r"$F(q)$",
        color=_PALETTE[0],
        x_offset=0.015,
    )
    ax.text(
        0.015,
        neg_log_evidence + 0.03,
        r"$-\ln p(o)$ floor",
        ha="left",
        va="bottom",
        fontsize=_FONT_SMALL,
        color=_PALETTE[2],
        fontweight="bold",
    )
    ax.set_xlim(0.0, 1.08)
    ax.set_xlabel(r"belief $q(\mathrm{present})$")
    ax.set_ylabel("variational free energy (nats)")
    ax.set_title("Free-energy bound is tight at the posterior")
    _add_axis_subtitle(
        ax,
        "Source: deterministic noisy-sensor kernel; units are nats.",
    )
    ax.legend(loc="upper right", frameon=False)
    _add_badge(ax, "single discrete noisy-sensor model", xy=(0.02, 0.87), color=_WARN)
    _style_axis(ax, grid_axis="y")
    return _save_figure(
        fig,
        path,
        note="Claim-backed VFE sweep; this is a pedagogical kernel example.",
    )


def plot_efe_decomposition(registry: ClaimRegistry, path: Path) -> Path:
    """Expected-free-energy comparison plus sensor-precision regime sweep."""
    path = _prepare_path(path)
    sample_g = float(registry.value("agent_g_sample"))
    commit_g = float(registry.value("agent_g_commit"))
    sample_epi = float(registry.value("agent_epistemic_sample"))
    commit_epi = float(registry.value("agent_epistemic_commit"))
    switch_precision = float(registry.value("agent_regime_switch_precision"))
    sweep = efe_precision_sweep()

    fig, (left, right) = plt.subplots(1, 2, figsize=(11, 4.8), constrained_layout=True)

    x = np.arange(2)
    width = 0.34
    g_bars = left.bar(
        x - width / 2,
        [sample_g, commit_g],
        width,
        color=_PALETTE[0],
        label="total EFE $G$",
    )
    epi_bars = left.bar(
        x + width / 2,
        [sample_epi, commit_epi],
        width,
        color=_PALETTE[4],
        label="epistemic value",
    )
    for bars in (g_bars, epi_bars):
        for bar in bars:
            value = bar.get_height()
            left.text(
                bar.get_x() + bar.get_width() / 2,
                value,
                f"{value:.3f}",
                ha="center",
                va="bottom",
                fontsize=_FONT_SMALL,
            )
    left.set_xticks(x)
    left.set_xticklabels(["sample", "commit"])
    left.set_ylabel("nats")
    _add_panel_label(left, "A", "Policy terms at the reference sensor precision")
    left.text(
        0.04,
        0.94,
        "lower G is preferred",
        transform=left.transAxes,
        fontsize=_FONT_SMALL,
        ha="left",
        va="top",
    )

    sensor_values = np.asarray(sweep["sensor_precision"], dtype=np.float64)
    g_sample_sweep = np.asarray(sweep["g_sample"], dtype=np.float64)
    g_commit_sweep = np.asarray(sweep["g_commit"], dtype=np.float64)
    right.plot(
        sensor_values,
        g_sample_sweep,
        color=_PALETTE[0],
        linewidth=2,
        label="sample",
    )
    right.plot(
        sensor_values,
        g_commit_sweep,
        color=_PALETTE[2],
        linewidth=2,
        label="commit",
    )
    right.axvline(
        switch_precision,
        color="#111827",
        linestyle="--",
        linewidth=1.1,
        label=f"switch {switch_precision:.2f}",
    )
    right.scatter([0.9], [sample_g], color=_PALETTE[0], edgecolors="white", zorder=3)
    right.scatter([0.9], [commit_g], color=_PALETTE[2], edgecolors="white", zorder=3)
    sensor_end = float(sensor_values[-1])
    _line_end_label(
        right,
        x=sensor_end,
        y=float(g_sample_sweep[-1]),
        label="sample",
        color=_PALETTE[0],
        x_offset=0.012,
    )
    _line_end_label(
        right,
        x=sensor_end,
        y=float(g_commit_sweep[-1]),
        label="commit",
        color=_PALETTE[2],
        x_offset=0.012,
    )
    right.set_xlim(float(sensor_values[0]), sensor_end + 0.12)
    right.set_xlabel("sensor precision")
    right.set_ylabel("expected free energy (nats)")
    _add_panel_label(right, "B", "Information seeking is regime-dependent")
    _add_axis_subtitle(
        right,
        "Switch line is local to this toy policy set and preference specification.",
        y=0.90,
    )
    right.legend(frameon=False, fontsize=_FONT_SMALL)
    for ax in (left, right):
        _style_axis(ax, grid_axis="y")
    fig.legend(
        handles=[g_bars, epi_bars],
        labels=["total EFE $G$", "epistemic value"],
        loc="lower center",
        bbox_to_anchor=(0.28, 0.035),
        ncol=2,
        frameon=False,
        fontsize=_FONT_SMALL,
    )
    return _save_figure(
        fig,
        path,
        note=(
            "EFE comparison is bounded to the stated policy set, preferences and "
            "sensor-precision sweep."
        ),
    )


def plot_planning_lookahead(registry: ClaimRegistry, path: Path) -> Path:
    """Multi-step planning: measured look-ahead gain and per-policy expected free energy."""
    path = _prepare_path(path)
    gain_coupled = float(registry.value("plan_lookahead_gain_coupled"))
    gain_decoupled = float(registry.value("plan_lookahead_gain_decoupled"))
    data = planning_lookahead_data()
    labels = cast(list[str], data["policy_labels"])
    policy_g = np.asarray(data["policy_g"], dtype=np.float64)
    greedy_index = cast(int, data["greedy_index"])
    optimal_index = cast(int, data["optimal_index"])

    fig, (left, right) = plt.subplots(
        1, 2, figsize=(11.5, 4.8), constrained_layout=False
    )
    fig.subplots_adjust(top=0.84, bottom=0.24, left=0.07, right=0.98, wspace=0.26)

    # Left: the honest contrast — look-ahead gain in each regime.
    gains = [gain_decoupled, gain_coupled]
    gain_bars = left.bar(
        np.arange(2),
        gains,
        width=0.5,
        color=[_MUTED, _OK],
    )
    for bar, value in zip(gain_bars, gains):
        left.text(
            bar.get_x() + bar.get_width() / 2,
            value,
            f"{value:.3f}",
            ha="center",
            va="bottom",
            fontsize=_FONT_SMALL,
        )
    left.set_xticks(np.arange(2))
    left.set_xticklabels(["decoupled\n(sample/commit)", "coupled\n(investment)"])
    left.set_ylabel("look-ahead gain (nats)")
    left.set_ylim(0, max(gains) * 1.25 + 0.05)
    _add_panel_label(left, "A", "Look-ahead gain vs the strongest greedy policy")
    left.text(
        0.04,
        0.94,
        "gain = greedy G − optimal G; zero is an honest null",
        transform=left.transAxes,
        fontsize=_FONT_SMALL,
        ha="left",
        va="top",
    )

    # Right: cumulative G of every enumerated policy in the coupled model.
    colors = [_LINE] * len(policy_g)
    colors[greedy_index] = _WARN
    colors[optimal_index] = _OK
    bars = right.bar(np.arange(len(policy_g)), policy_g, width=0.6, color=colors)
    for bar, value in zip(bars, policy_g):
        right.text(
            bar.get_x() + bar.get_width() / 2,
            value,
            f"{value:.2f}",
            ha="center",
            va="bottom",
            fontsize=_FONT_SMALL,
        )
    right.set_xticks(np.arange(len(policy_g)))
    right.set_xticklabels(labels, rotation=20, ha="right", fontsize=_FONT_SMALL)
    right.set_ylabel("cumulative EFE $G_\\pi$ (nats)")
    right.set_ylim(0, float(policy_g.max()) * 1.2)
    _add_panel_label(right, "B", "Every policy in the coupled model (lower is better)")
    legend_handles = [
        Patch(facecolor=_WARN, label="greedy myopic policy"),
        Patch(facecolor=_OK, label="optimal multi-step plan"),
        Patch(facecolor=_LINE, label="other policies"),
    ]
    fig.legend(
        handles=legend_handles,
        frameon=False,
        fontsize=_FONT_SMALL,
        loc="lower center",
        bbox_to_anchor=(0.60, 0.035),
        ncol=3,
    )

    return _save_figure(
        fig,
        path,
        note=(
            "Look-ahead value is a measured, model-dependent quantity from the planning "
            "kernel; it is not a universal property of planning."
        ),
    )


def plot_predictive_coding(registry: ClaimRegistry, path: Path) -> Path:
    """Continuous predictive coding: estimate settling to the analytic posterior + F descent."""
    path = _prepare_path(path)
    estimate_claim = float(registry.value("pc_posterior_estimate"))
    data = predictive_coding_data()
    steps = np.asarray(data["steps"], dtype=np.float64)
    trajectory = np.asarray(data["trajectory"], dtype=np.float64)
    free_energy = np.asarray(data["free_energy"], dtype=np.float64)
    analytic = float(cast(float, data["analytic_posterior_mean"]))
    observation = float(cast(float, data["observation"]))
    prior_mean = float(cast(float, data["prior_mean"]))
    converge_step = int(cast(int, data["steps_to_converge"]))

    fig, (left, right) = plt.subplots(
        1, 2, figsize=(11.5, 4.6), constrained_layout=True
    )

    left.plot(steps, trajectory, color=_PALETTE[0], linewidth=2, label="estimate")
    left.axhline(
        analytic,
        color=_OK,
        linestyle="--",
        linewidth=1.4,
        label=f"analytic posterior {analytic:.3f}",
    )
    left.axhline(
        observation, color=_MUTED, linestyle=":", linewidth=1.1, label="observation"
    )
    left.axhline(
        prior_mean, color=_LINE, linestyle=":", linewidth=1.1, label="prior mean"
    )
    left.axvline(converge_step, color=_INK, linestyle="-", linewidth=0.8, alpha=0.5)
    left.text(
        converge_step,
        analytic,
        f" converged @ step {converge_step}",
        fontsize=_FONT_SMALL,
        va="bottom",
        ha="left",
    )
    left.set_xlabel("descent step")
    left.set_ylabel("latent estimate")
    _add_panel_label(left, "A", "Estimate settles to the precision-weighted posterior")
    left.legend(frameon=False, fontsize=_FONT_SMALL, loc="center right")

    right.plot(steps, free_energy, color=_ALERT, linewidth=2)
    right.set_xlabel("descent step")
    right.set_ylabel("free energy $F$ (nats)")
    right.set_ylim(0, float(free_energy.max()) * 1.1 + 1e-6)
    _add_panel_label(right, "B", "Free energy descends monotonically to its minimum")
    right.text(
        0.96,
        0.94,
        f"estimate = {estimate_claim:.3f}",
        transform=right.transAxes,
        fontsize=_FONT_SMALL,
        ha="right",
        va="top",
    )

    return _save_figure(
        fig,
        path,
        note=(
            "Deterministic linear-Gaussian predictive-coding descent; the fixed point "
            "is the exact analytic posterior mean for this one model."
        ),
    )


def plot_kernel_sensitivity_profiles(registry: ClaimRegistry, path: Path) -> Path:
    """Render noisy-sensor posterior and EFE precision sensitivity diagnostics."""
    path = _prepare_path(path)
    base_rates = np.linspace(0.001, 0.25, 160, dtype=np.float64)
    likelihood = np.array(
        [
            [0.99, 0.05],
            [0.01, 0.95],
        ],
        dtype=np.float64,
    )
    posteriors = np.array(
        [
            bayes_posterior(np.array([rate, 1.0 - rate]), likelihood, 0)[0]
            for rate in base_rates
        ],
        dtype=np.float64,
    )
    vfe_sweep = vfe_belief_sweep()
    efe_sweep = efe_precision_sweep()
    efe_sensor_precision = np.asarray(efe_sweep["sensor_precision"], dtype=np.float64)
    efe_g_sample = np.asarray(efe_sweep["g_sample"], dtype=np.float64)
    efe_g_commit = np.asarray(efe_sweep["g_commit"], dtype=np.float64)
    switch_precision = float(registry.value("agent_regime_switch_precision"))

    fig, axes = plt.subplots(1, 3, figsize=(14, 4.8), constrained_layout=True)
    axes[0].plot(base_rates, posteriors, color=_PALETTE[0], linewidth=2.0)
    axes[0].scatter(
        [0.01],
        [float(registry.value("bayes_posterior_present_given_positive"))],
        color=_PALETTE[2],
        zorder=3,
    )
    axes[0].set_xlabel("base rate $p(s=present)$")
    axes[0].set_ylabel("posterior after positive observation")
    _add_panel_label(axes[0], "A", "Posterior sensitivity to base rate")
    axes[0].annotate(
        "reference base rate",
        xy=(0.01, float(registry.value("bayes_posterior_present_given_positive"))),
        xytext=(0.055, 0.78),
        arrowprops={"arrowstyle": "->", "color": _MUTED, "lw": 0.8},
        fontsize=_FONT_SMALL,
        color=_INK,
    )

    axes[1].plot(
        vfe_sweep["belief_present"],
        vfe_sweep["free_energy"],
        color=_PALETTE[1],
        linewidth=2.0,
    )
    axes[1].axhline(
        float(vfe_sweep["neg_log_evidence"]),
        color=_PALETTE[2],
        linestyle="--",
        linewidth=1.2,
    )
    axes[1].axvline(
        float(vfe_sweep["posterior_present"]),
        color="#111827",
        linestyle=":",
        linewidth=1.4,
    )
    axes[1].set_xlabel(r"belief $q(\mathrm{present})$")
    axes[1].set_ylabel("VFE (nats)")
    _add_panel_label(axes[1], "B", "VFE bound tightness profile")
    axes[1].text(
        0.03,
        float(vfe_sweep["neg_log_evidence"]) + 0.04,
        "evidence floor",
        ha="left",
        va="bottom",
        fontsize=_FONT_SMALL,
        color=_PALETTE[2],
        fontweight="bold",
    )

    axes[2].plot(
        efe_sensor_precision,
        efe_g_sample,
        color=_PALETTE[0],
        linewidth=2.0,
        label="sample",
    )
    axes[2].plot(
        efe_sensor_precision,
        efe_g_commit,
        color=_PALETTE[2],
        linewidth=2.0,
        label="commit",
    )
    axes[2].axvline(
        switch_precision,
        color="#111827",
        linestyle="--",
        linewidth=1.2,
        label="tie",
    )
    axes[2].set_xlabel("sensor precision")
    axes[2].set_ylabel("expected free energy (nats)")
    _add_panel_label(axes[2], "C", "Policy-regime boundary")
    _line_end_label(
        axes[2],
        x=float(efe_sensor_precision[-1]),
        y=float(efe_g_sample[-1]),
        label="sample",
        color=_PALETTE[0],
        x_offset=0.01,
    )
    _line_end_label(
        axes[2],
        x=float(efe_sensor_precision[-1]),
        y=float(efe_g_commit[-1]),
        label="commit",
        color=_PALETTE[2],
        x_offset=0.01,
    )
    axes[2].set_xlim(
        float(efe_sensor_precision[0]),
        float(efe_sensor_precision[-1]) + 0.1,
    )
    axes[2].legend(frameon=False, fontsize=_FONT_SMALL)

    for ax in axes:
        _style_axis(ax, grid_axis="y")
    return _save_figure(
        fig,
        path,
        note="Sensitivity panels expose deterministic kernel boundaries, not empirical effects.",
    )
