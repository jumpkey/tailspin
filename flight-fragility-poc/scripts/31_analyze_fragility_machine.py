#!/usr/bin/env python3
"""
31_analyze_fragility_machine.py — Fragility II: controllable/cascade aggregates.

Reduces the curated flight fact table to chart-ready controllable-disruption
and cascade-disruption aggregates, parallel to 30_analyze_fragility.py but
focused on the BTS delay-cause fields added for this add-on study. See
flight_fragility_ii_machine_addon_spec.md for the full methodology and the
"Risks, threats to validity, and alternative explanations" section this
script's output is meant to support.

Aggregation grain: market_bucket × weather_bucket × period_flag, plus a
pooled `combined_peer_basket` (UA + DL summed) sensitivity series.

A second, coarser aggregation (market_bucket × carrier_code × weather_bucket,
periods combined to preserve sample size) breaks out the controllable/cascade
metrics by regional operator within each basket. BTS's `Reporting_Airline`
field (`carrier_code` in the fact table) is the carrier that files the
on-time-performance report, which for these routes is the regional partner
itself (e.g. MQ/Envoy, OH/PSA, OO/SkyWest) rather than "AA" — so it already
provides operator-level granularity without needing a separate
operating-carrier field.

Outputs
-------
output/weather_fragility_machine_chart_data.csv
output/fragility_ii_machine_summary.json
output/fragility_ii_summary.md
output/fragility_ii_operator_breakdown.csv

Usage
-----
python scripts/31_analyze_fragility_machine.py --study config/study.yaml
"""

import argparse
import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
log = logging.getLogger(__name__)

GROUP_KEYS = ["market_bucket", "weather_bucket", "period_flag"]
WEATHER_BUCKETS = ["benign", "marginal", "adverse"]
PEER_BASKETS = ["ua_peer_basket", "dl_peer_basket"]

COUNT_COLS = [
    "flights_total", "cancelled_count", "operated_count",
    "controllable_cancel_count", "controllable_delay_count",
    "late_arriving_delay_count", "controllable_severe_delay_count",
    "late_arriving_severe_delay_count",
]


def load_study(path: Path) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def load_fact(path: Path) -> pd.DataFrame:
    log.info(f"Loading fact table: {path}")
    df = pd.read_csv(path, dtype=str)
    flag_cols = [
        "cancelled_flag", "diverted_flag", "severe_delay_flag", "operated_flag",
        "controllable_delay_flag", "controllable_cancel_flag", "late_arriving_flag",
        "cascade_delay_flag", "controllable_severe_delay_flag", "late_arriving_severe_delay_flag",
    ]
    for col in flag_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
    log.info(f"  Rows: {len(df):,}")
    return df


def aggregate(fact: pd.DataFrame, min_sample_threshold: int) -> pd.DataFrame:
    """Aggregate to market_bucket × weather_bucket × period_flag grain."""
    for k in GROUP_KEYS:
        if k not in fact.columns:
            log.warning(f"  Column '{k}' missing — using 'unknown' placeholder")
            fact[k] = "unknown"

    agg = (
        fact.groupby(GROUP_KEYS)
        .agg(
            flights_total=("route_key", "size"),
            cancelled_count=("cancelled_flag", "sum"),
            operated_count=("operated_flag", "sum"),
            controllable_cancel_count=("controllable_cancel_flag", "sum"),
            controllable_delay_count=("controllable_delay_flag", "sum"),
            late_arriving_delay_count=("late_arriving_flag", "sum"),
            controllable_severe_delay_count=("controllable_severe_delay_flag", "sum"),
            late_arriving_severe_delay_count=("late_arriving_severe_delay_flag", "sum"),
        )
        .reset_index()
    )

    combined_rows = []
    for weather in agg["weather_bucket"].unique():
        for period in agg["period_flag"].unique():
            subset = agg[
                (agg["weather_bucket"] == weather) & (agg["period_flag"] == period) &
                (agg["market_bucket"].isin(PEER_BASKETS))
            ]
            if subset.empty:
                continue
            row = {"market_bucket": "combined_peer_basket", "weather_bucket": weather, "period_flag": period}
            for c in COUNT_COLS:
                row[c] = subset[c].sum()
            combined_rows.append(row)

    if combined_rows:
        agg = pd.concat([agg, pd.DataFrame(combined_rows)], ignore_index=True)

    agg = _add_rates(agg)
    # The denominator-based threshold check uses operated_count, the smaller
    # of the two denominators in play, as the conservative single gate for
    # all four rate columns (see spec "Statistical robustness" section).
    # Uses <= rather than < so a cell sitting exactly at the threshold (e.g.
    # the UA peer basket's adverse/baseline cell, 30 operated flights) is
    # still flagged rather than treated as comfortably sampled.
    agg["low_confidence_flag"] = (agg["operated_count"] <= min_sample_threshold).astype(int)
    return agg


def aggregate_by_operator(fact: pd.DataFrame, min_sample_threshold: int) -> pd.DataFrame:
    """
    Aggregate to market_bucket x carrier_code x weather_bucket grain (periods
    combined) so the controllable/cascade signature can be inspected per
    regional operator within each basket, e.g. to see whether the AA basket's
    cascade-delay signature is concentrated in one regional partner or spread
    across all of them.
    """
    if "carrier_code" not in fact.columns:
        log.warning("  Column 'carrier_code' missing — skipping operator breakdown")
        return pd.DataFrame()

    df = fact[fact["weather_bucket"].isin(WEATHER_BUCKETS)]
    agg = (
        df.groupby(["market_bucket", "carrier_code", "weather_bucket"])
        .agg(
            flights_total=("route_key", "size"),
            operated_count=("operated_flag", "sum"),
            controllable_cancel_count=("controllable_cancel_flag", "sum"),
            controllable_severe_delay_count=("controllable_severe_delay_flag", "sum"),
            late_arriving_severe_delay_count=("late_arriving_severe_delay_flag", "sum"),
        )
        .reset_index()
    )
    agg["controllable_cancel_rate"] = (agg["controllable_cancel_count"] / agg["flights_total"]).round(4)
    agg["controllable_severe_delay_rate"] = np.where(
        agg["operated_count"] > 0,
        (agg["controllable_severe_delay_count"] / agg["operated_count"]).round(4), np.nan,
    )
    agg["late_arriving_severe_delay_rate"] = np.where(
        agg["operated_count"] > 0,
        (agg["late_arriving_severe_delay_count"] / agg["operated_count"]).round(4), np.nan,
    )
    agg["low_confidence_flag"] = (agg["operated_count"] <= min_sample_threshold).astype(int)
    agg["weather_bucket"] = pd.Categorical(agg["weather_bucket"], categories=WEATHER_BUCKETS, ordered=True)
    agg = agg.sort_values(["market_bucket", "carrier_code", "weather_bucket"]).reset_index(drop=True)
    return agg


def _add_rates(agg: pd.DataFrame) -> pd.DataFrame:
    agg["controllable_cancel_rate"] = agg["controllable_cancel_count"] / agg["flights_total"]
    agg["controllable_delay_rate"] = np.where(
        agg["operated_count"] > 0, agg["controllable_delay_count"] / agg["operated_count"], np.nan
    )
    agg["controllable_severe_delay_rate"] = np.where(
        agg["operated_count"] > 0, agg["controllable_severe_delay_count"] / agg["operated_count"], np.nan
    )
    agg["late_arriving_severe_delay_rate"] = np.where(
        agg["operated_count"] > 0, agg["late_arriving_severe_delay_count"] / agg["operated_count"], np.nan
    )
    for c in ("controllable_cancel_rate", "controllable_delay_rate",
              "controllable_severe_delay_rate", "late_arriving_severe_delay_rate"):
        agg[c] = agg[c].round(4)
    return agg


def _rate_from_cells(cells: pd.DataFrame, numerator_col: str, denom_col: str) -> tuple:
    """Sum numerator/denominator across cells and return (rate, denom_total, low_conf)."""
    if cells.empty:
        return np.nan, 0, True
    denom = cells[denom_col].sum()
    numer = cells[numerator_col].sum()
    rate = round(numer / denom, 4) if denom > 0 else np.nan
    low_conf = bool(cells["low_confidence_flag"].any())
    return rate, int(denom), low_conf


def compute_executive_summary(agg: pd.DataFrame, min_sample_threshold: int) -> dict:
    """Compute headline controllable/cascade metrics, mirroring 30_analyze_fragility.py."""
    summary: dict = {"min_sample_threshold": min_sample_threshold}

    metrics = [
        ("controllable_cancel_rate", "controllable_cancel_count", "flights_total"),
        ("controllable_severe_delay_rate", "controllable_severe_delay_count", "operated_count"),
        ("late_arriving_severe_delay_rate", "late_arriving_severe_delay_count", "operated_count"),
    ]

    for metric_name, num_col, denom_col in metrics:
        for weather in WEATHER_BUCKETS:
            subset = agg[agg["weather_bucket"] == weather]
            aa = subset[subset["market_bucket"] == "aa_regional_basket"]
            ua = subset[subset["market_bucket"] == "ua_peer_basket"]
            dl = subset[subset["market_bucket"] == "dl_peer_basket"]
            combined = subset[subset["market_bucket"] == "combined_peer_basket"]

            aa_rate, aa_n, aa_low = _rate_from_cells(aa, num_col, denom_col)
            ua_rate, ua_n, ua_low = _rate_from_cells(ua, num_col, denom_col)
            dl_rate, dl_n, dl_low = _rate_from_cells(dl, num_col, denom_col)
            combined_rate, combined_n, combined_low = _rate_from_cells(combined, num_col, denom_col)

            peer_avg = (
                np.nanmean([ua_rate, dl_rate]) if not (np.isnan(ua_rate) and np.isnan(dl_rate)) else np.nan
            )

            prefix = f"{metric_name}_{weather}"
            summary[f"aa_{prefix}"] = aa_rate
            summary[f"aa_{prefix}_n"] = aa_n
            summary[f"ua_{prefix}"] = ua_rate
            summary[f"ua_{prefix}_n"] = ua_n
            summary[f"dl_{prefix}"] = dl_rate
            summary[f"dl_{prefix}_n"] = dl_n
            summary[f"peer_avg_{prefix}"] = round(peer_avg, 4) if not np.isnan(peer_avg) else None
            summary[f"combined_peer_{prefix}"] = combined_rate
            summary[f"combined_peer_{prefix}_n"] = combined_n

            ratio_provisional = bool(aa_low or ua_low or dl_low)
            if not np.isnan(aa_rate) and not np.isnan(peer_avg) and peer_avg > 0:
                summary[f"aa_vs_peer_avg_ratio_{prefix}"] = round(aa_rate / peer_avg, 2)
            else:
                summary[f"aa_vs_peer_avg_ratio_{prefix}"] = None
            if not np.isnan(aa_rate) and not np.isnan(combined_rate) and combined_rate > 0:
                summary[f"aa_vs_combined_peer_ratio_{prefix}"] = round(aa_rate / combined_rate, 2)
            else:
                summary[f"aa_vs_combined_peer_ratio_{prefix}"] = None
            summary[f"{prefix}_ratio_provisional"] = ratio_provisional

    # Escalation: benign -> adverse, AA vs combined peer (late-arriving / cascade panel)
    cascade_metric = "late_arriving_severe_delay_rate"
    aa_benign = summary.get(f"aa_{cascade_metric}_benign")
    aa_adverse = summary.get(f"aa_{cascade_metric}_adverse")
    peer_benign = summary.get(f"combined_peer_{cascade_metric}_benign")
    peer_adverse = summary.get(f"combined_peer_{cascade_metric}_adverse")

    if aa_benign and aa_adverse and aa_benign > 0:
        summary["aa_cascade_escalation_benign_to_adverse"] = round(aa_adverse / aa_benign, 2)
    else:
        summary["aa_cascade_escalation_benign_to_adverse"] = None
    if peer_benign and peer_adverse and peer_benign > 0:
        summary["combined_peer_cascade_escalation_benign_to_adverse"] = round(peer_adverse / peer_benign, 2)
    else:
        summary["combined_peer_cascade_escalation_benign_to_adverse"] = None

    # Chart annotations
    marginal_ratio = summary.get("aa_vs_peer_avg_ratio_controllable_severe_delay_rate_marginal")
    marginal_provisional = summary.get("controllable_severe_delay_rate_marginal_ratio_provisional")
    if marginal_ratio is not None:
        marker = " (provisional — built on a low-sample cell)" if marginal_provisional else ""
        summary["chart_annotation_panel_a"] = (
            f"AA regional controllable severe-delay rate in marginal weather is "
            f"{marginal_ratio}x the peer average{marker}"
        )
    else:
        summary["chart_annotation_panel_a"] = "Insufficient data for ratio annotation"

    aa_esc = summary.get("aa_cascade_escalation_benign_to_adverse")
    peer_esc = summary.get("combined_peer_cascade_escalation_benign_to_adverse")
    if aa_esc is not None and peer_esc is not None:
        summary["chart_annotation_panel_b"] = (
            f"AA regional late-arriving severe-delay rate rises {aa_esc}x from benign to "
            f"adverse conditions, versus {peer_esc}x for the combined peer basket"
        )
    else:
        summary["chart_annotation_panel_b"] = "Insufficient data for escalation annotation"

    return summary


def low_confidence_cells(agg: pd.DataFrame) -> pd.DataFrame:
    cells = agg[(agg["low_confidence_flag"] == 1) & (agg["weather_bucket"] != "unknown")]
    return cells[GROUP_KEYS + ["flights_total", "operated_count"]]


OPERATOR_LABELS = {
    "MQ": "Envoy Air (MQ)",
    "OH": "PSA Airlines (OH)",
    "OO": "SkyWest (OO)",
    "DL": "Delta mainline (DL)",
    "9E": "Endeavor Air (9E)",
    "UA": "United mainline (UA)",
}


def write_operator_markdown(op_agg: pd.DataFrame) -> list:
    """Render the operator-breakdown section as a list of markdown lines."""
    def fmt_pct(x):
        return f"{x:.2%}" if x is not None and not (isinstance(x, float) and np.isnan(x)) else "n/a"

    lines = []
    lines.append("## 6. Operator-level breakdown within baskets")
    lines.append("")
    lines.append(
        "BTS's `Reporting_Airline` field (`carrier_code` in the fact table) is the carrier "
        "that files the on-time-performance report for each flight. For these routes that is "
        "the regional partner itself, not \"AA\"/\"UA\"/\"DL\" — so it already provides "
        "operator-level granularity inside each route-defined basket, without a separate "
        "operating-carrier field. Periods (2024/2025) are combined here to keep cells "
        "above the minimum-sample threshold; this view cannot also be split by period."
    )
    lines.append("")

    if op_agg.empty:
        lines.append("Operator breakdown unavailable for this run (missing `carrier_code`).")
        lines.append("")
        return lines

    for basket in ["aa_regional_basket", "dl_peer_basket", "ua_peer_basket"]:
        sub = op_agg[op_agg["market_bucket"] == basket]
        if sub.empty:
            continue
        carriers = [c for c in sub["carrier_code"].unique()]
        lines.append(f"**{basket}**")
        lines.append("")
        lines.append(
            "| Operator | Weather | Operated (n) | Controllable severe-delay rate | "
            "Late-arriving (cascade) severe-delay rate | Controllable cancel rate |"
        )
        lines.append("|---|---|---|---|---|---|")
        for carrier in carriers:
            crows = sub[sub["carrier_code"] == carrier].sort_values("weather_bucket")
            label = OPERATOR_LABELS.get(carrier, carrier)
            for _, r in crows.iterrows():
                flag = " *" if r["low_confidence_flag"] else ""
                lines.append(
                    f"| {label} | {str(r['weather_bucket']).title()} | {int(r['operated_count'])}{flag} | "
                    f"{fmt_pct(r['controllable_severe_delay_rate'])} | "
                    f"{fmt_pct(r['late_arriving_severe_delay_rate'])} | "
                    f"{fmt_pct(r['controllable_cancel_rate'])} |"
                )
        lines.append("")

    lines.append(
        "\\* low-confidence row (operated flights at or below the minimum-sample threshold)."
    )
    lines.append("")
    lines.append(
        "SkyWest (OO) appears in all three baskets under a different mainline contract in "
        "each. Comparing its row across the AA, DL, and UA tables above is the closest this "
        "study can get to separating an operator-wide SkyWest effect from an AA-contract-"
        "specific effect, per the spec's \"Regional-operator overlap across baskets\" risk. "
        "Envoy (MQ) and PSA (OH) fly only under the AA contract in this study's baskets, so "
        "there is no cross-contract comparison available for them here; any signature specific "
        "to either carrier cannot be distinguished from an AA-contract-specific effect using "
        "this data alone."
    )
    lines.append("")
    lines.append(
        "This breakdown is still subject to every caveat in section 4 and 7 below: cause "
        "codes are self-reported per flight by whichever carrier reports it, "
        "`controllable_*` does not isolate maintenance from crew or other factors, and "
        "`late_arriving_severe_delay_rate` reflects propagated disruption, not its original cause."
    )
    lines.append("")
    return lines


def write_markdown_summary(summary: dict, low_conf: pd.DataFrame, op_agg: pd.DataFrame, out_path: Path):
    def fmt_pct(x):
        return f"{x:.2%}" if x is not None and not (isinstance(x, float) and np.isnan(x)) else "n/a"

    def fmt_ratio(x, provisional):
        if x is None:
            return "n/a"
        return f"{x}x{' (provisional)' if provisional else ''}"

    lines = []
    lines.append("# Fragility II: Controllable and Cascade Disruption — Summary")
    lines.append("")
    lines.append(
        "This summary reports whether the public-data signature of controllable "
        "(Air Carrier-coded) disruption and late-arriving-aircraft cascade disruption "
        "is higher, lower, or similar for the AA regional basket relative to the UA and "
        "DL peer baskets, and whether that signature strengthens under marginal or "
        "adverse weather. It does not identify which internal function (maintenance, "
        "crew, or another controllable factor) is responsible — see the spec's "
        '"Risks, threats to validity, and alternative explanations" section, item 7 below.'
    )
    lines.append("")

    lines.append("## 1–3. Controllable and cascade disruption by weather condition")
    lines.append("")
    lines.append(
        "| Weather | AA controllable severe-delay rate (n) | Peer-avg (n) | Combined-peer (n) | AA÷peer-avg | AA÷combined-peer |"
    )
    lines.append("|---|---|---|---|---|---|")
    for weather in WEATHER_BUCKETS:
        prefix = f"controllable_severe_delay_rate_{weather}"
        aa = summary.get(f"aa_{prefix}")
        aa_n = summary.get(f"aa_{prefix}_n")
        peer_avg = summary.get(f"peer_avg_{prefix}")
        combined = summary.get(f"combined_peer_{prefix}")
        combined_n = summary.get(f"combined_peer_{prefix}_n")
        ratio_avg = summary.get(f"aa_vs_peer_avg_ratio_{prefix}")
        ratio_combined = summary.get(f"aa_vs_combined_peer_ratio_{prefix}")
        provisional = summary.get(f"{prefix}_ratio_provisional")
        lines.append(
            f"| {weather.title()} | {fmt_pct(aa)} ({aa_n}) | {fmt_pct(peer_avg)} | "
            f"{fmt_pct(combined)} ({combined_n}) | {fmt_ratio(ratio_avg, provisional)} | "
            f"{fmt_ratio(ratio_combined, provisional)} |"
        )
    lines.append("")
    lines.append(
        "| Weather | AA late-arriving severe-delay rate (n) | Peer-avg (n) | Combined-peer (n) | AA÷peer-avg | AA÷combined-peer |"
    )
    lines.append("|---|---|---|---|---|---|")
    for weather in WEATHER_BUCKETS:
        prefix = f"late_arriving_severe_delay_rate_{weather}"
        aa = summary.get(f"aa_{prefix}")
        aa_n = summary.get(f"aa_{prefix}_n")
        peer_avg = summary.get(f"peer_avg_{prefix}")
        combined = summary.get(f"combined_peer_{prefix}")
        combined_n = summary.get(f"combined_peer_{prefix}_n")
        ratio_avg = summary.get(f"aa_vs_peer_avg_ratio_{prefix}")
        ratio_combined = summary.get(f"aa_vs_combined_peer_ratio_{prefix}")
        provisional = summary.get(f"{prefix}_ratio_provisional")
        lines.append(
            f"| {weather.title()} | {fmt_pct(aa)} ({aa_n}) | {fmt_pct(peer_avg)} | "
            f"{fmt_pct(combined)} ({combined_n}) | {fmt_ratio(ratio_avg, provisional)} | "
            f"{fmt_ratio(ratio_combined, provisional)} |"
        )
    lines.append("")
    aa_esc = summary.get("aa_cascade_escalation_benign_to_adverse")
    peer_esc = summary.get("combined_peer_cascade_escalation_benign_to_adverse")
    lines.append(
        f"Benign-to-adverse escalation in the late-arriving (cascade) severe-delay rate: "
        f"AA regional {aa_esc}x, combined peer basket {peer_esc}x."
    )
    lines.append("")

    lines.append("## 4. Cause-data caveat")
    lines.append("")
    lines.append(
        "BTS cause-code reporting does not distinguish maintenance from crew, fueling, "
        "ground handling, or other airline-controlled factors within the Air Carrier "
        "category, and carriers self-report the cause code for each delayed or cancelled "
        "flight. An elevated `controllable_*` rate is evidence of elevated airline-"
        "attributed disruption in the public data, not evidence about which specific "
        "internal function is responsible."
    )
    lines.append("")

    lines.append("## 5. Sample sizes and low-confidence cells")
    lines.append("")
    lines.append(
        f"The minimum-sample threshold used for this run is {summary.get('min_sample_threshold')} "
        "operated flights per `market_bucket × weather_bucket × period_flag` cell. "
        "Flight-count denominators for each headline rate are shown in the tables above "
        "(in parentheses)."
    )
    lines.append("")
    if low_conf.empty:
        lines.append(
            "No `market_bucket × weather_bucket × period_flag` cell among the benign, "
            "marginal, or adverse weather buckets fell below this threshold in the current run."
        )
    else:
        lines.append("Cells below the minimum-sample threshold:")
        lines.append("")
        lines.append("| Market bucket | Weather | Period | Flights total | Operated |")
        lines.append("|---|---|---|---|---|")
        for _, r in low_conf.iterrows():
            lines.append(
                f"| {r['market_bucket']} | {r['weather_bucket']} | {r['period_flag']} | "
                f"{r['flights_total']} | {r['operated_count']} |"
            )
    lines.append("")
    lines.append(
        "**Data availability note**: BTS On-Time Performance extracts do not include a "
        "field literally named \"operating carrier\" distinct from the reporting carrier. "
        "For the routes in this study, however, the reporting carrier (`carrier_code`, BTS's "
        "`Reporting_Airline`) already identifies the regional partner operating the flight "
        "(MQ/Envoy, OH/PSA, OO/SkyWest), because regional carriers file their own on-time-"
        "performance reports under their own code even when the flight is sold and gated as "
        "American Eagle. Section 7 below uses that field to break out the controllable/cascade "
        "metrics by operator within each basket, addressing the spec's request to test whether "
        "an AA-basket effect concentrates in one regional partner or is spread across all of them."
    )
    lines.append("")

    lines.extend(write_operator_markdown(op_agg))

    lines.append("## 7. Threats to validity")
    lines.append("")
    lines.append(
        "See `flight_fragility_ii_machine_addon_spec.md`, section \"Risks, threats to "
        "validity, and alternative explanations,\" for the full disclosure of this study's "
        "known limitations, including self-reported cause data, the SkyWest cross-contract "
        "overlap, the pre-registered route baskets, the definitional difference between "
        "this study's severe-delay measure and Fragility I's, and a list of non-causal "
        "explanations consistent with any observed gap. This summary should not be read "
        "without that section."
    )
    lines.append("")

    out_path.write_text("\n".join(lines))
    log.info(f"Written summary: {out_path}")


def main():
    parser = argparse.ArgumentParser(description="Analyze Fragility II controllable/cascade aggregates")
    parser.add_argument("--study", default="config/study.yaml")
    parser.add_argument("--fact", default="data/curated/flight_operability_fact.csv")
    parser.add_argument("--out", default="output/weather_fragility_machine_chart_data.csv")
    parser.add_argument("--summary-out", default="output/fragility_ii_machine_summary.json")
    parser.add_argument("--md-out", default="output/fragility_ii_summary.md")
    parser.add_argument("--operator-out", default="output/fragility_ii_operator_breakdown.csv")
    args = parser.parse_args()

    script_dir = Path(__file__).parent
    root = script_dir.parent
    study_path = root / args.study
    fact_path = root / args.fact
    out_path = root / args.out
    summary_path = root / args.summary_out
    md_path = root / args.md_out
    operator_path = root / args.operator_out

    out_path.parent.mkdir(parents=True, exist_ok=True)

    study = load_study(study_path)
    min_sample_threshold = study.get("min_sample_threshold", 30)

    if not fact_path.exists():
        raise FileNotFoundError(f"Fact table not found: {fact_path}\nRun 20_build_flight_fact.py first.")

    fact = load_fact(fact_path)
    agg = aggregate(fact, min_sample_threshold)
    log.info(f"Aggregation complete: {len(agg)} rows at market×weather×period grain (incl. combined_peer_basket)")

    agg.to_csv(out_path, index=False)
    log.info(f"Chart data written: {out_path}")

    summary = compute_executive_summary(agg, min_sample_threshold)
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2, default=str)
    log.info(f"Machine summary written: {summary_path}")

    low_conf = low_confidence_cells(agg)
    if not low_conf.empty:
        log.warning(f"Low-confidence cells (operated_count < {min_sample_threshold}):\n{low_conf.to_string(index=False)}")

    op_agg = aggregate_by_operator(fact, min_sample_threshold)
    if not op_agg.empty:
        op_agg.to_csv(operator_path, index=False)
        log.info(f"Operator breakdown written: {operator_path}")

    write_markdown_summary(summary, low_conf, op_agg, md_path)

    log.info("=== Fragility II Summary ===")
    for wx in WEATHER_BUCKETS:
        aa = summary.get(f"aa_controllable_severe_delay_rate_{wx}")
        peer = summary.get(f"peer_avg_controllable_severe_delay_rate_{wx}")
        ratio = summary.get(f"aa_vs_peer_avg_ratio_controllable_severe_delay_rate_{wx}")
        log.info(f"  {wx:8s}: AA controllable severe-delay={aa}  peer_avg={peer}  ratio={ratio}")
    log.info(f"  Panel A annotation: {summary.get('chart_annotation_panel_a')}")
    log.info(f"  Panel B annotation: {summary.get('chart_annotation_panel_b')}")


if __name__ == "__main__":
    main()
