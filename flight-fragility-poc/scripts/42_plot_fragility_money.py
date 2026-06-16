#!/usr/bin/env python3
"""
42_plot_fragility_money.py — Render the Fragility III executive PNG chart.

Chart design
------------
Single grouped bar chart (1600x900 px), the spec's "preferred version":
  X-axis: cost scenario (low, base, high)
  Y-axis: estimated excess economic burden (USD)
  Bars grouped by component: airline operating-time burden, passenger-time
  burden, with the combined total marked as a text annotation per bar group.

Uses the pooled "all weather" row from the chart data (the headline,
study-window figure), not the weather-stratified breakdown — the weather
breakdown is in output/fragility_iii_summary.md section 4 instead.

Inputs
------
output/fragility_iii_chart_data.csv
output/fragility_iii_summary.json

Output
------
output/fragility_iii_exec_chart.png

Usage
-----
python scripts/42_plot_fragility_money.py
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

SCENARIO_ORDER = ["low", "base", "high"]
COMPONENT_COLORS = {
    "Airline operating-time burden": "#C8102E",
    "Passenger-time burden": "#8DB4E2",
}


def load_inputs(chart_data_path: Path, summary_path: Path):
    if not chart_data_path.exists():
        raise FileNotFoundError(
            f"Chart data not found: {chart_data_path}\nRun 32_analyze_fragility_money.py first."
        )
    df = pd.read_csv(chart_data_path)
    df = df[df["weather_bucket"] == "all"].copy()
    df["scenario"] = pd.Categorical(df["scenario"], categories=SCENARIO_ORDER, ordered=True)
    df = df.sort_values("scenario")

    summary: dict = {}
    if summary_path.exists():
        with open(summary_path) as f:
            summary = json.load(f)
    return df, summary


def plot_with_plotly(df: pd.DataFrame, summary: dict, out_path: Path):
    try:
        import plotly.graph_objects as go
    except ImportError:
        log.warning("plotly not installed — trying matplotlib fallback")
        return False

    scenarios = [s.title() for s in df["scenario"]]
    airline_vals = df["excess_airline_cost_proxy"].tolist()
    passenger_vals = df["excess_passenger_cost_proxy"].tolist()
    combined_vals = df["excess_combined_cost_proxy"].tolist()

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Airline operating-time burden",
        x=scenarios, y=airline_vals,
        marker=dict(color=COMPONENT_COLORS["Airline operating-time burden"]),
        text=[f"${v:,.0f}" for v in airline_vals],
        textposition="outside",
    ))
    fig.add_trace(go.Bar(
        name="Passenger-time burden (flight-level proxy)",
        x=scenarios, y=passenger_vals,
        marker=dict(color=COMPONENT_COLORS["Passenger-time burden"]),
        text=[f"${v:,.0f}" for v in passenger_vals],
        textposition="outside",
    ))

    for i, (scen, total) in enumerate(zip(scenarios, combined_vals)):
        fig.add_annotation(
            x=scen, y=max(airline_vals[i], passenger_vals[i]) * 1.15 if max(airline_vals[i], passenger_vals[i]) else 1,
            text=f"Combined: ${total:,.0f}",
            showarrow=False,
            font=dict(size=12, color="#222222"),
            yshift=20,
        )

    fig.update_yaxes(title_text="Estimated Excess Economic Burden (USD)", tickformat=",.0f")
    fig.update_xaxes(title_text="Cost Scenario")

    mode_label = summary.get("basis_description", "")
    annotation_text = summary.get("chart_annotation", "")
    footer = f"{annotation_text}<br><i>Basis: {mode_label}. Proxy estimate from public cost benchmarks, not audited financials.</i>"

    fig.add_annotation(
        text=footer,
        xref="paper", yref="paper",
        x=0.5, y=-0.22,
        showarrow=False,
        font=dict(size=11, color="#444444"),
        align="center",
    )

    fig.update_layout(
        title=dict(
            text="Flight Fragility III: Estimated Excess Economic Burden<br>"
                 "<sub>AA regional spokes vs. peer-reliability benchmark — controllable + cascade basis (2024-2025)</sub>",
            font=dict(size=18),
        ),
        width=1600,
        height=900,
        barmode="group",
        legend=dict(orientation="h", yanchor="bottom", y=-0.12, xanchor="center", x=0.5),
        plot_bgcolor="#FAFAFA",
        paper_bgcolor="#FFFFFF",
        font=dict(family="Arial, sans-serif", size=13),
        margin=dict(t=120, b=180, l=80, r=80),
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
        import numpy as np
    except ImportError:
        log.error("Neither plotly/kaleido nor matplotlib is available. Cannot render chart.")
        return False

    scenarios = [s.title() for s in df["scenario"]]
    airline_vals = df["excess_airline_cost_proxy"].to_numpy()
    passenger_vals = df["excess_passenger_cost_proxy"].to_numpy()
    combined_vals = df["excess_combined_cost_proxy"].to_numpy()

    fig, ax = plt.subplots(figsize=(16, 9))
    fig.suptitle(
        "Flight Fragility III: Estimated Excess Economic Burden\n"
        "AA regional spokes vs. peer-reliability benchmark — controllable + cascade basis (2024-2025)",
        fontsize=14, fontweight="bold",
    )

    x = np.arange(len(scenarios))
    width = 0.35
    bars1 = ax.bar(x - width / 2, airline_vals, width, color=COMPONENT_COLORS["Airline operating-time burden"],
                   label="Airline operating-time burden")
    bars2 = ax.bar(x + width / 2, passenger_vals, width, color=COMPONENT_COLORS["Passenger-time burden"],
                   label="Passenger-time burden (flight-level proxy)")

    for bars, vals in ((bars1, airline_vals), (bars2, passenger_vals)):
        for bar, val in zip(bars, vals):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), f"${val:,.0f}",
                    ha="center", va="bottom", fontsize=9)

    for xi, total in zip(x, combined_vals):
        ymax = max(airline_vals[xi], passenger_vals[xi])
        ax.text(xi, ymax * 1.12 if ymax else 1, f"Combined: ${total:,.0f}",
                ha="center", va="bottom", fontsize=11, fontweight="bold")

    ax.set_xticks(x)
    ax.set_xticklabels(scenarios)
    ax.set_xlabel("Cost Scenario")
    ax.set_ylabel("Estimated Excess Economic Burden (USD)")
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"${v:,.0f}"))
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    ax.set_facecolor("#FAFAFA")
    ax.legend(loc="upper left")

    mode_label = summary.get("basis_description", "")
    annotation_text = summary.get("chart_annotation", "")
    footer = f"{annotation_text}\nBasis: {mode_label}. Proxy estimate from public cost benchmarks, not audited financials."
    fig.text(0.5, 0.01, footer, ha="center", fontsize=9, color="#444444", style="italic", wrap=True)

    plt.tight_layout(rect=[0, 0.08, 1, 0.93])
    plt.savefig(str(out_path), dpi=150, bbox_inches="tight")
    plt.close()
    log.info(f"Chart saved (matplotlib): {out_path}")
    return True


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Render Fragility III executive chart")
    parser.add_argument("--chart-data", default="output/fragility_iii_chart_data.csv")
    parser.add_argument("--summary", default="output/fragility_iii_summary.json")
    parser.add_argument("--out", default="output/fragility_iii_exec_chart.png")
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
