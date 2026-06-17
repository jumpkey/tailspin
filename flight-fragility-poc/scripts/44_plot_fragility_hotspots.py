#!/usr/bin/env python3
"""
44_plot_fragility_hotspots.py — Render the Fragility V executive chart.

Chart design
------------
Horizontal stacked bar chart where each bar represents one of the top-20
hotspot cells. Each bar is decomposed into 6 colored segments corresponding
to the 6 normalized components; bar width = total base hotspot score. A
robustness indicator (dot) appears to the right of each bar. Cells flagged
as persistent (top-20 in both study periods) are marked with "(P)" in the
label.

Inputs
------
output/fragility_v_hotspot_rankings.csv
output/fragility_v_summary.json

Outputs
-------
output/fragility_v_exec_chart.png
output/fragility_v_summary.md  (already written by 34_analyze_fragility_hotspots.py;
                                this script does not overwrite it)

Usage
-----
python scripts/44_plot_fragility_hotspots.py
python scripts/44_plot_fragility_hotspots.py --scorecard output/fragility_v_hotspot_rankings.csv
"""

import argparse
import json
import logging
import sys
from pathlib import Path

import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
log = logging.getLogger(__name__)

COMPONENT_COLS = [
    "norm_cancel",
    "norm_severe_delay",
    "norm_controllable",
    "norm_cascade",
    "norm_weather_sensitivity",
    "norm_economic_burden",
]
COMPONENT_LABELS = [
    "Cancellation",
    "Severe Delay",
    "Controllable",
    "Cascade",
    "Weather Sensitivity",
    "Economic Burden",
]
COMPONENT_COLORS = [
    "#C8102E",
    "#FF6B35",
    "#F4C842",
    "#4CAF50",
    "#2196F3",
    "#9C27B0",
]

HUB_MARKER_COLORS = {
    "DFW": "#0B4F6C",
    "CLT": "#2E8B57",
    "ORD": "#8B5CF6",
    "PHL": "#D97706",
}
FALLBACK_MARKER = "#999999"


def load_inputs(scorecard_path: Path, summary_path: Path):
    if not scorecard_path.exists():
        raise FileNotFoundError(
            f"Rankings CSV not found: {scorecard_path}\nRun 34_analyze_fragility_hotspots.py first."
        )
    df = pd.read_csv(scorecard_path)
    summary = {}
    if summary_path.exists():
        with open(summary_path) as f:
            summary = json.load(f)
    return df, summary


def build_label(row: pd.Series) -> str:
    label = f"{row['operator_class']} @ {row['hub_family']}-{row['spoke_airport']}"
    if row.get("is_persistent", False):
        label += " (P)"
    return label


def plot_exec_chart(df: pd.DataFrame, summary: dict, out_path: Path) -> bool:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches
        import numpy as np
    except ImportError:
        log.error("matplotlib is not available — cannot render chart.")
        return False

    df = df.copy()

    # Fill missing component cols with 0 to still plot partial data
    for col in COMPONENT_COLS:
        if col not in df.columns:
            df[col] = 0.0
        else:
            df[col] = df[col].fillna(0.0)

    if "hotspot_score_base" not in df.columns:
        score_cols = [c for c in df.columns if c.startswith("hotspot_score_")]
        base_col = score_cols[0] if score_cols else None
    else:
        base_col = "hotspot_score_base"

    # Sort ascending so highest-score cell appears at top
    df = df.sort_values(base_col or "hotspot_score_base", ascending=True).reset_index(drop=True)

    labels = [build_label(row) for _, row in df.iterrows()]
    n_cells = len(df)
    y_pos = np.arange(n_cells)

    fig, (ax_bars, ax_rob) = plt.subplots(
        1, 2,
        figsize=(14, max(10, n_cells * 0.4 + 2)),
        gridspec_kw={"width_ratios": [5, 1]},
    )
    fig.patch.set_facecolor("#FFFFFF")

    title = "Fragility V: Network Hotspot Scorecard — Top 20 AA Hub-Spoke Market-Operator Cells"
    annotation = summary.get("annotation", "")

    fig.suptitle(title, fontsize=13, fontweight="bold", y=0.98)
    if annotation:
        fig.text(0.5, 0.955, annotation, ha="center", va="top", fontsize=8.5,
                 color="#444444", style="italic", wrap=True)

    # Stacked horizontal bars
    left = np.zeros(n_cells)
    patches = []
    for col, label, color in zip(COMPONENT_COLS, COMPONENT_LABELS, COMPONENT_COLORS):
        vals = df[col].values
        ax_bars.barh(y_pos, vals, left=left, height=0.7, color=color, label=label)
        patches.append(mpatches.Patch(color=color, label=label))
        left += vals

    # Y-axis: cell labels, colored by hub
    ax_bars.set_yticks(y_pos)
    ax_bars.set_yticklabels(labels, fontsize=8)
    for tick_label, (_, row) in zip(ax_bars.get_yticklabels(), df.iterrows()):
        hub = row.get("hub_family", "")
        tick_label.set_color(HUB_MARKER_COLORS.get(hub, "#222222"))

    ax_bars.set_xlabel("Composite Hotspot Score (sum of weighted normalized components)", fontsize=9)
    ax_bars.set_title("Hotspot Score Decomposition", fontsize=10)
    ax_bars.grid(axis="x", linestyle="--", alpha=0.4)
    ax_bars.set_facecolor("#FAFAFA")
    ax_bars.set_xlim(0, max(left.max() * 1.05, 0.01))

    # Legend for components
    ax_bars.legend(
        handles=patches,
        loc="lower right",
        fontsize=7.5,
        framealpha=0.85,
        ncol=2,
    )

    # Robustness panel: dot plot
    if "hotspot_robustness_score" in df.columns:
        rob_vals = df["hotspot_robustness_score"].fillna(0.0).values
    else:
        rob_vals = np.zeros(n_cells)

    hub_colors = [HUB_MARKER_COLORS.get(str(h), FALLBACK_MARKER) for h in df["hub_family"]]
    ax_rob.scatter(rob_vals, y_pos, c=hub_colors, s=60, zorder=3)

    ax_rob.set_xlim(-0.05, 1.1)
    ax_rob.set_xticks([0, 0.25, 0.5, 0.75, 1.0])
    ax_rob.set_xticklabels(["0", ".25", ".5", ".75", "1"], fontsize=7)
    ax_rob.set_yticks(y_pos)
    ax_rob.set_yticklabels([])
    ax_rob.set_xlabel("Robustness\n(fraction of scenarios)", fontsize=8)
    ax_rob.set_title("Robustness", fontsize=10)
    ax_rob.grid(axis="x", linestyle="--", alpha=0.4)
    ax_rob.set_facecolor("#FAFAFA")
    ax_rob.axvline(x=1.0, color="#333333", linestyle=":", linewidth=0.8, alpha=0.6)

    # Hub color legend (right panel bottom)
    hub_patches = [
        mpatches.Patch(color=color, label=hub)
        for hub, color in HUB_MARKER_COLORS.items()
        if hub in df["hub_family"].values
    ]
    if hub_patches:
        ax_rob.legend(
            handles=hub_patches,
            loc="lower right",
            fontsize=7,
            title="Hub",
            title_fontsize=7.5,
            framealpha=0.85,
        )

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.savefig(str(out_path), dpi=200, bbox_inches="tight")
    plt.close()
    log.info(f"Executive chart saved: {out_path}")
    return True


def main():
    parser = argparse.ArgumentParser(description="Render the Fragility V executive chart")
    parser.add_argument("--scorecard", default="output/fragility_v_hotspot_rankings.csv")
    parser.add_argument("--summary", default="output/fragility_v_summary.json")
    parser.add_argument("--out", default="output/fragility_v_exec_chart.png")
    args = parser.parse_args()

    script_dir = Path(__file__).parent
    root = script_dir.parent
    scorecard_path = root / args.scorecard
    summary_path = root / args.summary
    out_path = root / args.out

    out_path.parent.mkdir(parents=True, exist_ok=True)

    df, summary = load_inputs(scorecard_path, summary_path)
    if df.empty:
        log.error("Rankings CSV is empty — nothing to plot.")
        sys.exit(1)

    if not plot_exec_chart(df, summary, out_path):
        log.error("Chart rendering failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
