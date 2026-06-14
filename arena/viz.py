"""
viz.py — deterministic figure generation from metrics output.
No LLM imports. Produces PNG files in the run's figures/ directory.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
import matplotlib.ticker
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def generate_all(metrics: dict, figures_dir: Path) -> None:
    figures_dir.mkdir(parents=True, exist_ok=True)
    _arms_race(metrics, figures_dir)
    _calibration(metrics, figures_dir)
    _confusion_bar(metrics, figures_dir)
    _evasion_by_task(metrics, figures_dir)
    print(f"Figures saved to {figures_dir}/")


# ── Figure 1: Arms race ───────────────────────────────────────────────────

def _arms_race(metrics: dict, out: Path) -> None:
    per_round = metrics.get("per_round", [])
    if not per_round:
        return

    rounds  = [r["round"] for r in per_round]
    evasion = [r["evasion_rate"] for r in per_round]
    recall  = [r["defender_recall"] for r in per_round]

    RED  = "#C0392B"
    BLUE = "#2471A3"

    with plt.rc_context({
        "font.family":      "serif",
        "font.size":        12,
        "axes.spines.top":  False,
        "axes.spines.right":False,
        "axes.linewidth":   0.8,
        "xtick.direction":  "out",
        "ytick.direction":  "out",
    }):
        fig, ax = plt.subplots(figsize=(8, 4))

        ax.plot(rounds, recall, color=BLUE, linewidth=1.8,
                linestyle="-", marker="s", markersize=5,
                markerfacecolor="white", markeredgewidth=1.5,
                zorder=3)
        ax.plot(rounds, evasion, color=RED, linewidth=1.8,
                linestyle="-",  marker="o", markersize=5,
                markerfacecolor="white", markeredgewidth=1.5,
                zorder=3)

        ax.fill_between(rounds, evasion, alpha=0.08, color=RED)

        ax.set_xlabel("Round", labelpad=6)
        ax.set_ylabel("Rate", labelpad=6)

        ax.set_xlim(min(rounds) - 0.5, max(rounds) + 0.5)
        ax.set_ylim(-0.04, 1.08)
        ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
        ax.set_yticklabels(["0", ".25", ".50", ".75", "1.0"])
        ax.xaxis.set_minor_locator(matplotlib.ticker.MultipleLocator(1))
        ax.grid(axis="y", linewidth=0.5, linestyle=":", color="#AAAAAA", zorder=0)

        fig.tight_layout()
        fig.savefig(out / "arms_race.png", dpi=200, bbox_inches="tight")
        plt.close(fig)


# ── Figure 2: Reliability diagram (calibration) ──────────────────────────

def _calibration(metrics: dict, out: Path) -> None:
    bins = [b for b in metrics.get("calibration_bins", []) if b["n"] > 0]
    if not bins:
        return

    x = [b["mean_confidence"] for b in bins]
    y = [b["accuracy"] * 100 for b in bins]
    sizes = [b["n"] for b in bins]

    fig, ax = plt.subplots(figsize=(5, 5))
    ax.plot([0, 100], [0, 100], "k--", alpha=0.4, label="Perfect calibration")
    sc = ax.scatter(x, y, s=[max(30, n * 3) for n in sizes],
                    c="steelblue", zorder=3, alpha=0.8)
    ax.set_xlabel("Mean predicted confidence")
    ax.set_ylabel("Actual accuracy (%)")
    ax.set_title("Defender Reliability Diagram")
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.grid(alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(out / "calibration.png", dpi=150)
    plt.close(fig)


# ── Figure 3: Confusion matrix bar ───────────────────────────────────────

def _confusion_bar(metrics: dict, out: Path) -> None:
    cm = metrics.get("confusion", {})
    if not cm:
        return

    labels = ["TP\n(tampered→tampered)", "FN\n(tampered→clean)",
              "FP\n(clean→tampered)", "TN\n(clean→clean)"]
    values = [cm.get("tp", 0), cm.get("fn", 0), cm.get("fp", 0), cm.get("tn", 0)]
    colors = ["steelblue", "firebrick", "orange", "mediumseagreen"]

    fig, ax = plt.subplots(figsize=(6, 4))
    bars = ax.bar(labels, values, color=colors, edgecolor="white")
    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                str(val), ha="center", va="bottom", fontsize=10)
    ax.set_ylabel("Count")
    ax.set_title("Defender Confusion Matrix (all rounds)")
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(out / "confusion.png", dpi=150)
    plt.close(fig)


# ── Figure 4: Per-task evasion rate ──────────────────────────────────────

def _evasion_by_task(metrics: dict, out: Path) -> None:
    per_task = metrics.get("per_task", {})
    if not per_task:
        return

    task_ids = list(per_task.keys())
    evasion = [per_task[t]["evasion_rate"] for t in task_ids]
    real_bug_rate = [per_task[t]["real_bug_rate"] for t in task_ids]

    x = np.arange(len(task_ids))
    width = 0.35

    fig, ax = plt.subplots(figsize=(max(5, len(task_ids) * 2), 4))
    ax.bar(x - width / 2, real_bug_rate, width, label="Real bug rate", color="goldenrod")
    ax.bar(x + width / 2, evasion, width, label="Evasion rate", color="firebrick")
    ax.set_xticks(x)
    ax.set_xticklabels(task_ids, rotation=15, ha="right")
    ax.set_ylabel("Rate")
    ax.set_ylim(0, 1.1)
    ax.set_title("Per-task: Real Bug Rate vs Evasion Rate")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(out / "per_task.png", dpi=150)
    plt.close(fig)
