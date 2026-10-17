"""Presentation only: plot the already-audited, frozen summary table."""
from __future__ import annotations
import argparse
import csv
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    directory = Path(args.input)
    if not (directory / "VERIFICATION.json").exists():
        raise ValueError("Run the independent audit before plotting")
    with (directory / "summary.csv").open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    methods = ("raw95", "calibrated_raw95", "budget_zero95", "budget_prediction95")
    labels = ("Ordinary raw95", "Calibrated raw95", "Matched zero", "Prediction")
    colors = ("#64748b", "#0f766e", "#94a3b8", "#2563eb")
    pairs = ("en-de", "he-en", "zh-en")
    scenarios = ("aligned", "permuted_history", "reversed_history")
    titles = ("Aligned history", "Permuted history", "Reversed history")
    fig, axes = plt.subplots(3, 3, figsize=(10.4, 8.7), sharey="col")
    for i, scenario in enumerate(scenarios):
        for j, pair in enumerate(pairs):
            ax = axes[i, j]
            values = [float(next(r["mean_queries"] for r in rows
                                if r["scenario"] == scenario and
                                r["language_pair"] == pair and r["method"] == method))
                      for method in methods]
            bars = ax.bar(np.arange(4), values, color=colors, width=.72)
            ax.set_ylim(0, max(values) * 1.19)
            ax.bar_label(bars, labels=[f"{v:.1f}" for v in values], fontsize=8, padding=3)
            ax.set_xticks([])
            ax.spines[["top", "right", "bottom"]].set_visible(False)
            ax.set_axisbelow(True)
            ax.yaxis.grid(True, alpha=.17)
            if i == 0:
                ax.set_title(pair, fontsize=12, fontweight="bold", pad=12)
            if j == 0:
                ax.set_ylabel(titles[i] + "\nMean target labels", fontsize=10)
    handles = [plt.Rectangle((0, 0), 1, 1, color=c) for c in colors]
    fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(.5, .94),
               ncol=4, frameon=False, fontsize=10)
    fig.suptitle("Stage 9: label cost on three fixed WMT23 development pools",
                 x=.5, y=.98, fontsize=14, fontweight="bold")
    fig.text(.5, .02, "100 paired query paths per target; equal system weights within each language.\n"
             "All conditions retained. These are development results, not new human annotation.",
             ha="center", fontsize=9, color="#475569")
    fig.tight_layout(rect=(0, .065, 1, .90), h_pad=2)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=180, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    main()
