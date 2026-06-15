#!/usr/bin/env python3
"""
40_plot_fragility.py — Render the executive-ready flight fragility PNG chart.

Chart design
------------
Two-panel grouped bar chart (1600×900 px):
  Left panel  — Cancellation rate by weather bucket
  Right panel — Severe delay rate among operated flights by weather bucket

Series (one bar group per weather bucket):
  AA_regional_basket  (prominent color)
  UA_peer_basket      (muted)
  DL_peer_basket      (muted)

One annotation is generated from computed summary values if the data supports it.

Inputs
------
output/weather_fragility_chart_data.csv
output/fragility_summary.json

Output
------
output/weather_fragility_exec_chart.png

Usage
-----
python scripts/40_plot_fragility.py
"""

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

# Chart colors: AA prominent, peers muted
COLORS = {
    "aa_regional_basket": "#C8102E",   # American red
    "ua_peer_basket":     "#8DB4E2",   # United muted blue
    "dl_peer_basket":     "#A8C5A0",   # Delta muted green
    "other":              "#CCCCCC",
}

DISPLAY_NAMES = {
    "aa_regional_basket": "AA Regional",
    "ua_peer_basket":     "UA Peer",
    "dl_peer_basket":     "DL Peer",
}

WEATHER_ORDER = ["benign", "marginal", "adverse"]
PERIOD_ORDER = ["baseline", "recent"]


def load_inputs(chart_data_path: Path, summary_path: Path):
    if not chart_data_path.exists():
        raise FileNotFoundError(
            f"Chart data not found: {chart_data_path}\n"
            "Run 30_analyze_fragility.py first."
        )
    df = pd.read_csv(chart_data_path, dtype=str)
    numeric_cols = [
        "flights_total", "cancelled_count", "operated_count", "severe_delay_count",
        "cancellation_rate", "severe_delay_rate", "avg_dep_delay_operated",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    summary: dict = {}
    if summary_path.exists():
        with open(summary_path) as f:
            summary = json.load(f)

    return df, summary


def _get_panel_data(df: pd.DataFrame, metric: str) -> pd.DataFrame:
    """
    Pivot data for one panel: rows = weather_bucket, cols = market_bucket.
    Uses combined baseline+recent data (sum numerators, recompute rate).
    """
    # Aggregate across periods for the overview chart
    group = df.groupby(["market_bucket", "weather_bucket"]).agg(
        flights_total=("flights_total", "sum"),
        cancelled_count=("cancelled_count", "sum"),
        operated_count=("operated_count", "sum"),
        severe_delay_count=("severe_delay_count", "sum"),
    ).reset_index()

    group["cancellation_rate"] = group["cancelled_count"] / group["flights_total"].clip(lower=1)
    group["severe_delay_rate"] = group["severe_delay_count"] / group["operated_count"].clip(lower=1)

    pivot = group.pivot(index="weather_bucket", columns="market_bucket", values=metric)
    # Reindex to consistent weather order
    pivot = pivot.reindex([w for w in WEATHER_ORDER if w in pivot.index])
    return pivot


def plot_with_plotly(df: pd.DataFrame, summary: dict, out_path: Path):
    try:
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
    except ImportError:
        log.warning("plotly not installed — trying matplotlib fallback")
        return False

    cancel_pivot = _get_panel_data(df, "cancellation_rate")
    delay_pivot = _get_panel_data(df, "severe_delay_rate")

    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=(
            "Cancellation Rate by Weather Condition",
            "Severe Delay Rate (Operated Flights) by Weather Condition",
        ),
        shared_yaxes=False,
    )

    def _add_bars(pivot: pd.DataFrame, col: int):
        weather_labels = [w.title() for w in pivot.index]
        for basket in ["aa_regional_basket", "ua_peer_basket", "dl_peer_basket"]:
            if basket not in pivot.columns:
                continue
            values = pivot[basket].fillna(0).tolist()
            text_labels = [f"{v:.1%}" if v == v else "" for v in values]
            fig.add_trace(
                go.Bar(
                    name=DISPLAY_NAMES.get(basket, basket),
                    x=weather_labels,
                    y=values,
                    marker_color=COLORS.get(basket, "#AAAAAA"),
                    text=text_labels,
                    textposition="outside",
                    legendgroup=basket,
                    showlegend=(col == 1),
                ),
                row=1, col=col,
            )

    _add_bars(cancel_pivot, 1)
    _add_bars(delay_pivot, 2)

    # Y-axis formatting as percentage
    fig.update_yaxes(tickformat=".0%", row=1, col=1, title_text="Cancellation Rate")
    fig.update_yaxes(tickformat=".0%", row=1, col=2, title_text="Severe Delay Rate (≥60 min)")

    # Annotation
    annotation_text = summary.get("chart_annotation", "")
    if annotation_text and "Insufficient" not in annotation_text:
        fig.add_annotation(
            text=f"<i>{annotation_text}</i>",
            xref="paper", yref="paper",
            x=0.5, y=-0.12,
            showarrow=False,
            font=dict(size=13, color="#444444"),
            align="center",
        )

    fig.update_layout(
        title=dict(
            text="Flight Fragility Study: AA Regional vs. Peer Carriers<br>"
                 "<sub>American Airlines regional spokes vs. UA and DL comparable markets (2024–2025)</sub>",
            font=dict(size=18),
        ),
        width=1600,
        height=900,
        barmode="group",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.08,
            xanchor="center",
            x=0.5,
        ),
        plot_bgcolor="#FAFAFA",
        paper_bgcolor="#FFFFFF",
        font=dict(family="Arial, sans-serif", size=13),
        margin=dict(t=120, b=120, l=80, r=80),
    )

    try:
        fig.write_image(str(out_path), width=1600, height=900, scale=1)
        log.info(f"Chart saved (plotly/kaleido): {out_path}")
        return True
    except Exception as exc:
        log.warning(f"Plotly/kaleido PNG export failed: {exc} — trying matplotlib fallback")
        return False


def plot_with_matplotlib(df: pd.DataFrame, summary: dict, out_path: Path):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches
        import numpy as np
    except ImportError:
        log.error("Neither plotly/kaleido nor matplotlib is available. Cannot render chart.")
        return False

    cancel_pivot = _get_panel_data(df, "cancellation_rate")
    delay_pivot = _get_panel_data(df, "severe_delay_rate")

    fig, axes = plt.subplots(1, 2, figsize=(16, 9))
    fig.suptitle(
        "Flight Fragility Study: AA Regional vs. Peer Carriers\n"
        "American Airlines regional spokes vs. UA and DL comparable markets (2024–2025)",
        fontsize=14, fontweight="bold",
    )

    baskets = ["aa_regional_basket", "ua_peer_basket", "dl_peer_basket"]
    x = np.arange(len([w for w in WEATHER_ORDER if w in cancel_pivot.index]))
    width = 0.25

    def _draw_panel(ax, pivot: pd.DataFrame, ylabel: str):
        labels = [w.title() for w in WEATHER_ORDER if w in pivot.index]
        patches = []
        for i, basket in enumerate(baskets):
            if basket not in pivot.columns:
                continue
            vals = [pivot.loc[w, basket] if w in pivot.index else 0.0
                    for w in WEATHER_ORDER if w in pivot.index]
            vals = [v if v == v else 0.0 for v in vals]
            bars = ax.bar(x + i * width, vals, width, color=COLORS.get(basket, "#AAAAAA"),
                          label=DISPLAY_NAMES.get(basket, basket))
            for bar, val in zip(bars, vals):
                if val > 0:
                    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.002,
                            f"{val:.1%}", ha="center", va="bottom", fontsize=9)
            patches.append(mpatches.Patch(color=COLORS.get(basket, "#AAAAAA"),
                                          label=DISPLAY_NAMES.get(basket, basket)))

        ax.set_xticks(x + width)
        ax.set_xticklabels(labels)
        ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0))
        ax.set_ylabel(ylabel)
        ax.grid(axis="y", linestyle="--", alpha=0.5)
        ax.set_facecolor("#FAFAFA")
        return patches

    patches = _draw_panel(axes[0], cancel_pivot, "Cancellation Rate")
    _draw_panel(axes[1], delay_pivot, "Severe Delay Rate (≥60 min)")
    axes[0].set_title("Cancellation Rate by Weather Condition")
    axes[1].set_title("Severe Delay Rate by Weather Condition")

    # Shared legend
    fig.legend(handles=patches, loc="lower center", ncol=3, bbox_to_anchor=(0.5, 0.01))

    annotation_text = summary.get("chart_annotation", "")
    if annotation_text and "Insufficient" not in annotation_text:
        fig.text(0.5, 0.04, annotation_text, ha="center", fontsize=11,
                 color="#444444", style="italic")

    plt.tight_layout(rect=[0, 0.07, 1, 0.95])
    plt.savefig(str(out_path), dpi=150, bbox_inches="tight")
    plt.close()
    log.info(f"Chart saved (matplotlib): {out_path}")
    return True


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Render executive fragility chart")
    parser.add_argument("--chart-data", default="output/weather_fragility_chart_data.csv")
    parser.add_argument("--summary", default="output/fragility_summary.json")
    parser.add_argument("--out", default="output/weather_fragility_exec_chart.png")
    args = parser.parse_args()

    script_dir = Path(__file__).parent
    root = script_dir.parent
    chart_data_path = root / args.chart_data
    summary_path = root / args.summary
    out_path = root / args.out

    out_path.parent.mkdir(parents=True, exist_ok=True)

    df, summary = load_inputs(chart_data_path, summary_path)

    if df.empty:
        log.error("Chart data is empty — nothing to plot.")
        sys.exit(1)

    # Try plotly first, fall back to matplotlib
    if not plot_with_plotly(df, summary, out_path):
        if not plot_with_matplotlib(df, summary, out_path):
            log.error("Chart rendering failed with both plotly and matplotlib.")
            sys.exit(1)


if __name__ == "__main__":
    main()
