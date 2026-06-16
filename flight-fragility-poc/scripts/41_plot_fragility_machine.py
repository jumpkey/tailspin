#!/usr/bin/env python3
"""
41_plot_fragility_machine.py — Render the Fragility II executive PNG chart.

Chart design
------------
Two-panel grouped bar chart (1600x900 px):
  Panel A — Controllable (Air Carrier-coded) severe-delay rate by weather bucket
  Panel B — Late-arriving (cascade) severe-delay rate by weather bucket

Series (one bar group per weather bucket):
  AA_regional_basket  (prominent color)
  UA_peer_basket      (muted)
  DL_peer_basket      (muted)

Bars built from a cell flagged low_confidence_flag=1 in the chart data are
rendered at reduced opacity with a footnote, per the spec's sample-size
handling requirement, rather than presented at face value next to
well-sampled bars.

Inputs
------
output/weather_fragility_machine_chart_data.csv
output/fragility_ii_machine_summary.json

Output
------
output/weather_fragility_machine_exec_chart.png

Usage
-----
python scripts/41_plot_fragility_machine.py
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

COLORS = {
    "aa_regional_basket": "#C8102E",
    "ua_peer_basket":     "#8DB4E2",
    "dl_peer_basket":     "#A8C5A0",
}

DISPLAY_NAMES = {
    "aa_regional_basket": "AA Regional",
    "ua_peer_basket":     "UA Peer",
    "dl_peer_basket":     "DL Peer",
}

WEATHER_ORDER = ["benign", "marginal", "adverse"]
BASKETS = ["aa_regional_basket", "ua_peer_basket", "dl_peer_basket"]
LOW_CONFIDENCE_ALPHA = 0.45


def load_inputs(chart_data_path: Path, summary_path: Path):
    if not chart_data_path.exists():
        raise FileNotFoundError(
            f"Chart data not found: {chart_data_path}\nRun 31_analyze_fragility_machine.py first."
        )
    df = pd.read_csv(chart_data_path, dtype=str)
    numeric_cols = [
        "flights_total", "operated_count", "controllable_severe_delay_count",
        "late_arriving_severe_delay_count", "controllable_severe_delay_rate",
        "late_arriving_severe_delay_rate", "low_confidence_flag",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    summary: dict = {}
    if summary_path.exists():
        with open(summary_path) as f:
            summary = json.load(f)
    return df, summary


def _get_panel_data(df: pd.DataFrame, metric: str, count_col: str):
    """
    Pivot data for one panel: rows = weather_bucket, cols = market_bucket.
    Combines baseline+recent periods (sum numerators/denominators, recompute rate).
    Returns (rate_pivot, low_confidence_pivot) where low_confidence_pivot is True
    if any underlying period-cell for that (basket, weather) pair was low-confidence.
    """
    denom_col = "operated_count"
    group = df.groupby(["market_bucket", "weather_bucket"]).agg(
        **{count_col: (count_col, "sum")},
        operated_count=(denom_col, "sum"),
        low_confidence_flag=("low_confidence_flag", "max"),
    ).reset_index()

    group[metric] = group[count_col] / group["operated_count"].clip(lower=1)

    rate_pivot = group.pivot(index="weather_bucket", columns="market_bucket", values=metric)
    low_conf_pivot = group.pivot(index="weather_bucket", columns="market_bucket", values="low_confidence_flag")

    rate_pivot = rate_pivot.reindex([w for w in WEATHER_ORDER if w in rate_pivot.index])
    low_conf_pivot = low_conf_pivot.reindex(rate_pivot.index)
    return rate_pivot, low_conf_pivot


def plot_with_plotly(df: pd.DataFrame, summary: dict, out_path: Path):
    try:
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
    except ImportError:
        log.warning("plotly not installed — trying matplotlib fallback")
        return False

    controllable_pivot, controllable_lc = _get_panel_data(
        df, "controllable_severe_delay_rate", "controllable_severe_delay_count"
    )
    cascade_pivot, cascade_lc = _get_panel_data(
        df, "late_arriving_severe_delay_rate", "late_arriving_severe_delay_count"
    )

    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=(
            "Controllable (Air Carrier) Severe-Delay Rate by Weather Condition",
            "Late-Arriving (Cascade) Severe-Delay Rate by Weather Condition",
        ),
        shared_yaxes=False,
    )

    def _add_bars(pivot: pd.DataFrame, low_conf: pd.DataFrame, col: int):
        weather_labels = [w.title() for w in pivot.index]
        for basket in BASKETS:
            if basket not in pivot.columns:
                continue
            values = pivot[basket].fillna(0).tolist()
            lc_flags = low_conf[basket].fillna(0).tolist() if basket in low_conf.columns else [0] * len(values)
            text_labels = [
                (f"{v:.1%}*" if lc else f"{v:.1%}") if v == v else "" for v, lc in zip(values, lc_flags)
            ]
            opacities = [LOW_CONFIDENCE_ALPHA if lc else 1.0 for lc in lc_flags]
            fig.add_trace(
                go.Bar(
                    name=DISPLAY_NAMES.get(basket, basket),
                    x=weather_labels,
                    y=values,
                    marker=dict(color=COLORS.get(basket, "#AAAAAA"), opacity=opacities),
                    text=text_labels,
                    textposition="outside",
                    legendgroup=basket,
                    showlegend=(col == 1),
                ),
                row=1, col=col,
            )

    _add_bars(controllable_pivot, controllable_lc, 1)
    _add_bars(cascade_pivot, cascade_lc, 2)

    fig.update_yaxes(tickformat=".0%", row=1, col=1, title_text="Controllable Severe-Delay Rate")
    fig.update_yaxes(tickformat=".0%", row=1, col=2, title_text="Late-Arriving Severe-Delay Rate")

    annotation_lines = []
    for key in ("chart_annotation_panel_a", "chart_annotation_panel_b"):
        text = summary.get(key, "")
        if text and "Insufficient" not in text:
            annotation_lines.append(text)
    annotation_lines.append("* low-confidence cell (operated flights at or below the minimum-sample threshold)")
    annotation_text = "<br>".join(annotation_lines)

    fig.add_annotation(
        text=f"<i>{annotation_text}</i>",
        xref="paper", yref="paper",
        x=0.5, y=-0.18,
        showarrow=False,
        font=dict(size=12, color="#444444"),
        align="center",
    )

    fig.update_layout(
        title=dict(
            text="Flight Fragility II: Controllable and Cascade Disruption<br>"
                 "<sub>American Airlines regional spokes vs. UA and DL comparable markets (2024-2025)</sub>",
            font=dict(size=18),
        ),
        width=1600,
        height=900,
        barmode="group",
        legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5),
        plot_bgcolor="#FAFAFA",
        paper_bgcolor="#FFFFFF",
        font=dict(family="Arial, sans-serif", size=13),
        margin=dict(t=120, b=160, l=80, r=80),
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

    controllable_pivot, controllable_lc = _get_panel_data(
        df, "controllable_severe_delay_rate", "controllable_severe_delay_count"
    )
    cascade_pivot, cascade_lc = _get_panel_data(
        df, "late_arriving_severe_delay_rate", "late_arriving_severe_delay_count"
    )

    fig, axes = plt.subplots(1, 2, figsize=(16, 9))
    fig.suptitle(
        "Flight Fragility II: Controllable and Cascade Disruption\n"
        "American Airlines regional spokes vs. UA and DL comparable markets (2024-2025)",
        fontsize=14, fontweight="bold",
    )

    x = np.arange(len([w for w in WEATHER_ORDER if w in controllable_pivot.index]))
    width = 0.25

    def _draw_panel(ax, pivot: pd.DataFrame, low_conf: pd.DataFrame, ylabel: str):
        labels = [w.title() for w in WEATHER_ORDER if w in pivot.index]
        patches = []
        for i, basket in enumerate(BASKETS):
            if basket not in pivot.columns:
                continue
            vals = [pivot.loc[w, basket] if w in pivot.index else 0.0
                    for w in WEATHER_ORDER if w in pivot.index]
            vals = [v if v == v else 0.0 for v in vals]
            lc_flags = [low_conf.loc[w, basket] if (basket in low_conf.columns and w in low_conf.index) else 0
                        for w in WEATHER_ORDER if w in pivot.index]
            bars = ax.bar(x + i * width, vals, width, color=COLORS.get(basket, "#AAAAAA"),
                          label=DISPLAY_NAMES.get(basket, basket))
            for bar, val, lc in zip(bars, vals, lc_flags):
                if lc:
                    bar.set_alpha(LOW_CONFIDENCE_ALPHA)
                    bar.set_hatch("///")
                if val > 0:
                    label = f"{val:.1%}{'*' if lc else ''}"
                    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.002,
                            label, ha="center", va="bottom", fontsize=9)
            patches.append(mpatches.Patch(color=COLORS.get(basket, "#AAAAAA"),
                                          label=DISPLAY_NAMES.get(basket, basket)))

        ax.set_xticks(x + width)
        ax.set_xticklabels(labels)
        ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0))
        ax.set_ylabel(ylabel)
        ax.grid(axis="y", linestyle="--", alpha=0.5)
        ax.set_facecolor("#FAFAFA")
        return patches

    patches = _draw_panel(axes[0], controllable_pivot, controllable_lc, "Controllable Severe-Delay Rate")
    _draw_panel(axes[1], cascade_pivot, cascade_lc, "Late-Arriving Severe-Delay Rate")
    axes[0].set_title("Controllable (Air Carrier) Severe-Delay Rate")
    axes[1].set_title("Late-Arriving (Cascade) Severe-Delay Rate")

    fig.legend(handles=patches, loc="lower center", ncol=3, bbox_to_anchor=(0.5, 0.07))

    annotation_lines = []
    for key in ("chart_annotation_panel_a", "chart_annotation_panel_b"):
        text = summary.get(key, "")
        if text and "Insufficient" not in text:
            annotation_lines.append(text)
    annotation_lines.append("* low-confidence cell (operated flights at or below the minimum-sample threshold)")
    fig.text(0.5, 0.005, "\n".join(annotation_lines), ha="center", fontsize=10,
             color="#444444", style="italic")

    plt.tight_layout(rect=[0, 0.11, 1, 0.95])
    plt.savefig(str(out_path), dpi=150, bbox_inches="tight")
    plt.close()
    log.info(f"Chart saved (matplotlib): {out_path}")
    return True


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Render Fragility II executive chart")
    parser.add_argument("--chart-data", default="output/weather_fragility_machine_chart_data.csv")
    parser.add_argument("--summary", default="output/fragility_ii_machine_summary.json")
    parser.add_argument("--out", default="output/weather_fragility_machine_exec_chart.png")
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

    if not plot_with_plotly(df, summary, out_path):
        if not plot_with_matplotlib(df, summary, out_path):
            log.error("Chart rendering failed with both plotly and matplotlib.")
            sys.exit(1)


if __name__ == "__main__":
    main()
