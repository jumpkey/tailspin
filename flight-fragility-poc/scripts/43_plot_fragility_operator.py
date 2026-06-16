#!/usr/bin/env python3
"""
43_plot_fragility_operator.py — Render the Fragility IV executive chart and
written summary.

Chart design
------------
Four-panel chart (1700x950 px), x-axis = operator_class, color = hub_family
(small multiples by hub family, per the spec's "prioritize hub-family
small multiples over operator-color complexity" guidance):
  Panel A — weather_fragility_rate
  Panel B — controllable_severe_delay_rate
  Panel C — late_arriving_severe_delay_rate
  Panel D — economic_burden_proxy_usd_per_1000_flights

Each panel pools weather_bucket and period_flag (sums the underlying counts
and dollar totals, then recomputes the rate) to give one overview number per
operator_class x hub_family cell; the un-pooled, weather/period-stratified
detail remains available in fragility_iv_operator_chart_data.csv.

Inputs
------
output/fragility_iv_operator_chart_data.csv
output/fragility_iv_summary.json

Outputs
-------
output/fragility_iv_operator_exec_chart.png
output/fragility_iv_summary.md

Usage
-----
python scripts/43_plot_fragility_operator.py
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

PANELS = [
    ("weather_fragility_rate", "Weather Fragility Rate", True),
    ("controllable_severe_delay_rate", "Controllable Severe-Delay Rate", True),
    ("late_arriving_severe_delay_rate", "Late-Arriving Cascade Severe-Delay Rate", True),
    ("economic_burden_proxy_usd_per_1000_flights", "Economic Burden Proxy ($/1,000 flights)", False),
]

HUB_COLORS = {
    "focal_corridor": "#C8102E",
    "DFW": "#0B4F6C",
    "CLT": "#2E8B57",
    "ORD": "#8B5CF6",
    "PHL": "#D97706",
}
FALLBACK_COLORS = ["#999999", "#666666", "#333333"]


def load_inputs(chart_data_path: Path, summary_path: Path):
    if not chart_data_path.exists():
        raise FileNotFoundError(
            f"Chart data not found: {chart_data_path}\nRun 33_analyze_fragility_operator.py first."
        )
    df = pd.read_csv(chart_data_path)
    summary = {}
    if summary_path.exists():
        with open(summary_path) as f:
            summary = json.load(f)
    return df, summary


def pool_overview(df: pd.DataFrame) -> pd.DataFrame:
    """Pool weather_bucket and period_flag per operator_class x hub_family
    cell by summing counts/dollars, then recompute rates from the pooled
    sums (not an average of per-cell rates) to avoid Simpson's-paradox-style
    distortion."""
    group = df.groupby(["operator_class", "hub_family"]).agg(
        flights_total=("flights_total", "sum"),
        cancelled_count=("cancelled_count", "sum"),
        operated_count=("operated_count", "sum"),
        severe_delay_count=("severe_delay_count", "sum"),
        controllable_severe_delay_count=("controllable_severe_delay_count", "sum"),
        late_arriving_severe_delay_count=("late_arriving_severe_delay_count", "sum"),
        economic_burden_proxy_usd=("economic_burden_proxy_usd", "sum"),
    ).reset_index()

    group["weather_fragility_rate"] = (
        (group["cancelled_count"] + group["severe_delay_count"]) / group["flights_total"].clip(lower=1)
    )
    group["controllable_severe_delay_rate"] = (
        group["controllable_severe_delay_count"] / group["operated_count"].clip(lower=1)
    )
    group["late_arriving_severe_delay_rate"] = (
        group["late_arriving_severe_delay_count"] / group["operated_count"].clip(lower=1)
    )
    group["economic_burden_proxy_usd_per_1000_flights"] = (
        group["economic_burden_proxy_usd"] / (group["flights_total"].clip(lower=1) / 1000.0)
    )
    return group


def _panel_pivot(group: pd.DataFrame, metric: str) -> pd.DataFrame:
    pivot = group.pivot(index="operator_class", columns="hub_family", values=metric)
    return pivot


def _hub_color(hub: str, idx: int) -> str:
    if hub in HUB_COLORS:
        return HUB_COLORS[hub]
    return FALLBACK_COLORS[idx % len(FALLBACK_COLORS)]


def plot_with_plotly(group: pd.DataFrame, summary: dict, out_path: Path) -> bool:
    try:
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
    except ImportError:
        log.warning("plotly not installed — trying matplotlib fallback")
        return False

    fig = make_subplots(rows=1, cols=4, subplot_titles=[label for _, label, _ in PANELS])
    hubs = sorted(group["hub_family"].unique())

    for col_idx, (metric, _label, is_pct) in enumerate(PANELS, start=1):
        pivot = _panel_pivot(group, metric)
        operator_classes = list(pivot.index)
        for h_idx, hub in enumerate(hubs):
            if hub not in pivot.columns:
                continue
            values = pivot[hub].tolist()
            text_labels = [f"{v:.1%}" if is_pct and v == v else (f"${v:,.0f}" if v == v else "") for v in values]
            fig.add_trace(
                go.Bar(
                    name=hub,
                    x=operator_classes,
                    y=values,
                    marker_color=_hub_color(hub, h_idx),
                    text=text_labels,
                    textposition="outside",
                    legendgroup=hub,
                    showlegend=(col_idx == 1),
                ),
                row=1, col=col_idx,
            )
        if is_pct:
            fig.update_yaxes(tickformat=".0%", row=1, col=col_idx)

    annotation_text = summary.get("chart_annotation", "")
    if annotation_text and "Insufficient" not in annotation_text:
        fig.add_annotation(
            text=f"<i>{annotation_text}</i>",
            xref="paper", yref="paper", x=0.5, y=-0.18,
            showarrow=False, font=dict(size=12, color="#444444"), align="center",
        )

    fig.update_layout(
        title=dict(
            text="Fragility IV: Operator Attribution<br>"
                 "<sub>AA mainline vs. Envoy vs. PSA vs. SkyWest/Republic contracts, focal corridor + hub-spoke</sub>",
            font=dict(size=17),
        ),
        width=1700, height=950, barmode="group",
        legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5),
        plot_bgcolor="#FAFAFA", paper_bgcolor="#FFFFFF",
        font=dict(family="Arial, sans-serif", size=11),
        margin=dict(t=130, b=160, l=60, r=60),
    )
    for ann in fig.layout.annotations[:4]:
        ann.font.size = 12

    try:
        fig.write_image(str(out_path), width=1700, height=950, scale=1)
        log.info(f"Chart saved (plotly/kaleido): {out_path}")
        return True
    except Exception as exc:
        log.warning(f"Plotly/kaleido PNG export failed: {exc} — trying matplotlib fallback")
        return False


def plot_with_matplotlib(group: pd.DataFrame, summary: dict, out_path: Path) -> bool:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches
        import numpy as np
    except ImportError:
        log.error("Neither plotly/kaleido nor matplotlib is available. Cannot render chart.")
        return False

    hubs = sorted(group["hub_family"].unique())
    fig, axes = plt.subplots(1, 4, figsize=(17, 9.5))
    fig.suptitle(
        "Fragility IV: Operator Attribution\n"
        "AA mainline vs. Envoy vs. PSA vs. SkyWest/Republic contracts, focal corridor + hub-spoke",
        fontsize=13, fontweight="bold",
    )

    patches = []
    for ax_idx, (metric, label, is_pct) in enumerate(PANELS):
        pivot = _panel_pivot(group, metric)
        operator_classes = list(pivot.index)
        x = np.arange(len(operator_classes))
        width = 0.8 / max(len(hubs), 1)
        ax = axes[ax_idx]
        for h_idx, hub in enumerate(hubs):
            if hub not in pivot.columns:
                continue
            vals = pivot[hub].fillna(0).tolist()
            color = _hub_color(hub, h_idx)
            bars = ax.bar(x + h_idx * width, vals, width, color=color, label=hub)
            if ax_idx == 0:
                patches.append(mpatches.Patch(color=color, label=hub))
            for bar, val in zip(bars, vals):
                if val:
                    txt = f"{val:.1%}" if is_pct else f"${val:,.0f}"
                    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), txt,
                            ha="center", va="bottom", fontsize=7, rotation=60)
        ax.set_xticks(x + width * (len(hubs) - 1) / 2)
        ax.set_xticklabels(operator_classes, rotation=45, ha="right", fontsize=8)
        if is_pct:
            ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0))
        ax.set_title(label, fontsize=10)
        ax.grid(axis="y", linestyle="--", alpha=0.5)
        ax.set_facecolor("#FAFAFA")

    fig.legend(handles=patches, loc="lower center", ncol=min(len(hubs), 5), bbox_to_anchor=(0.5, 0.0))

    annotation_text = summary.get("chart_annotation", "")
    if annotation_text and "Insufficient" not in annotation_text:
        fig.text(0.5, 0.06, annotation_text, ha="center", fontsize=9, color="#444444", style="italic", wrap=True)

    plt.tight_layout(rect=[0, 0.12, 1, 0.92])
    plt.savefig(str(out_path), dpi=150, bbox_inches="tight")
    plt.close()
    log.info(f"Chart saved (matplotlib): {out_path}")
    return True


def write_markdown_summary(group: pd.DataFrame, df: pd.DataFrame, summary: dict, out_path: Path):
    lines = []
    lines.append("# Fragility IV: Operator Attribution — Summary")
    lines.append("")
    lines.append(
        "This summary compares observable fragility signals (weather sensitivity, "
        "controllable delay, late-arriving cascade delay, and an economic-burden proxy) "
        "across AA's operating structure — AA mainline, Envoy, PSA, and SkyWest/Republic "
        "under their resolved contracts — in the focal corridor and in the included "
        "hub-spoke network slices. It does not assert a cause for any observed difference; "
        "see `flight_fragility_iv_operator_attribution_spec.md`, \"Risks and interpretation "
        "constraints,\" which this summary should not be read without."
    )
    lines.append("")

    qa_notes = summary.get("qa_notes", [])

    lines.append("## 1. Are material operator differences observed?")
    lines.append("")
    if not group.empty:
        spread = group["weather_fragility_rate"].max() - group["weather_fragility_rate"].min()
        lines.append(
            f"Across the included operator_class x hub_family cells, the weather-fragility-rate "
            f"spread is {spread:.1%} (highest minus lowest cell, pooled across weather conditions "
            f"and study periods). {summary.get('chart_annotation', '')}"
        )
    else:
        lines.append("Insufficient data to assess.")
    lines.append("")

    lines.append("## 2. Which hubs or corridor families are most implicated?")
    lines.append("")
    if not group.empty:
        by_hub = group.groupby("hub_family")["weather_fragility_rate"].mean().sort_values(ascending=False)
        lines.append("| Hub / corridor family | Mean weather fragility rate across operator classes |")
        lines.append("|---|---|")
        for hub, rate in by_hub.items():
            lines.append(f"| {hub} | {rate:.1%} |")
    lines.append("")

    lines.append("## 3. Weather-related, controllable, or cascade-driven?")
    lines.append("")
    if not group.empty:
        comp_means = {
            "Weather (overall fragility)": group["weather_fragility_rate"].mean(),
            "Controllable severe-delay": group["controllable_severe_delay_rate"].mean(),
            "Late-arriving cascade": group["late_arriving_severe_delay_rate"].mean(),
        }
        dominant = max(comp_means, key=comp_means.get)
        lines.append(
            f"Of the three component rates averaged across included cells, **{dominant}** is "
            f"highest ({comp_means[dominant]:.1%}). This indicates where the included data "
            "concentrate, not which underlying cause produced it."
        )
    lines.append("")

    lines.append("## 4. Suggested follow-up domains")
    lines.append("")
    lines.append(
        "- Network planning and AA regional governance, if differences concentrate by hub or "
        "corridor family rather than spreading evenly.\n"
        "- Operations/IOC, if late-arriving cascade delay dominates over controllable delay.\n"
        "- Envoy/PSA/SkyWest/Republic executive leadership, framed as a performance-attribution "
        "and improvement-opportunity review, not a prosecutorial finding.\n"
        "- Finance/commercial, for the economic-burden-proxy magnitude specifically."
    )
    lines.append("")

    lines.append("## 5. QA notes")
    lines.append("")
    for note in qa_notes:
        lines.append(f"- {note}")
    lines.append("")

    lines.append("## 6. Caveats")
    lines.append("")
    lines.append(
        "- Attribution is not causation: observed differences may reflect network design, hub "
        "structure, assignment policy, schedule pressure, weather exposure, governance "
        "differences, or other latent factors this study cannot isolate.\n"
        "- Mix effects: operator classes may systematically serve different route lengths, hubs, "
        "or banks; this study minimizes apples-to-oranges comparison via corridor families and "
        "selected hub-spoke structures, but cannot eliminate it entirely.\n"
        "- SkyWest_unresolved / Republic_unresolved rows are excluded from operator-class "
        "comparisons (see QA notes above) pending targeted FlightAware validation.\n"
        "- The economic-burden proxy uses the same published-benchmark, scenario-based "
        "methodology as Fragility III (base scenario only here) — not audited financials."
    )
    lines.append("")

    out_path.write_text("\n".join(lines))
    log.info(f"Written summary: {out_path}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Render the Fragility IV executive chart and summary")
    parser.add_argument("--chart-data", default="output/fragility_iv_operator_chart_data.csv")
    parser.add_argument("--summary", default="output/fragility_iv_summary.json")
    parser.add_argument("--out", default="output/fragility_iv_operator_exec_chart.png")
    parser.add_argument("--md-out", default="output/fragility_iv_summary.md")
    args = parser.parse_args()

    script_dir = Path(__file__).parent
    root = script_dir.parent
    chart_data_path = root / args.chart_data
    summary_path = root / args.summary
    out_path = root / args.out
    md_path = root / args.md_out

    out_path.parent.mkdir(parents=True, exist_ok=True)

    df, summary = load_inputs(chart_data_path, summary_path)
    if df.empty:
        log.error("Chart data is empty — nothing to plot.")
        sys.exit(1)

    group = pool_overview(df)

    if not plot_with_plotly(group, summary, out_path):
        if not plot_with_matplotlib(group, summary, out_path):
            log.error("Chart rendering failed with both plotly and matplotlib.")
            sys.exit(1)

    write_markdown_summary(group, df, summary, md_path)


if __name__ == "__main__":
    main()
