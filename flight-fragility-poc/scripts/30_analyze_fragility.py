#!/usr/bin/env python3
"""
30_analyze_fragility.py — Reduce the curated flight fact table to chart-ready aggregates.

Aggregation grain: market_bucket × weather_bucket × period_flag

Outputs
-------
output/weather_fragility_chart_data.csv   Chart-ready aggregate metrics
output/fragility_summary.json             Executive annotation values

Usage
-----
python scripts/30_analyze_fragility.py --study config/study.yaml
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


def load_study(path: Path) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def load_fact(path: Path) -> pd.DataFrame:
    log.info(f"Loading fact table: {path}")
    df = pd.read_csv(path, dtype=str)
    for col in ("dep_delay_min", "arr_delay_min"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    for col in ("cancelled_flag", "diverted_flag", "severe_delay_flag", "operated_flag"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
    log.info(f"  Rows: {len(df):,}")
    return df


def aggregate(fact: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate to market_bucket × weather_bucket × period_flag grain.

    Reference logic (from spec):
        agg = fact.groupby([...]).agg(
            flights_total, cancelled_count, operated_count,
            severe_delay_count, avg_dep_delay_operated
        )
        agg["cancellation_rate"] = cancelled_count / flights_total
        agg["severe_delay_rate"] = severe_delay_count / operated_count
    """
    group_keys = ["market_bucket", "weather_bucket", "period_flag"]
    # Ensure all group keys present
    for k in group_keys:
        if k not in fact.columns:
            log.warning(f"  Column '{k}' missing — using 'unknown' placeholder")
            fact[k] = "unknown"

    # Compute avg departure delay on operated flights only (cancelled flights
    # have NaN dep_delay_min, but we filter explicitly for correctness)
    operated = fact[fact["operated_flag"] == 1].copy() if "operated_flag" in fact.columns else fact.copy()

    delay_by_group = (
        operated.groupby(group_keys)["dep_delay_min"]
        .mean()
        .reset_index()
        .rename(columns={"dep_delay_min": "avg_dep_delay_operated"})
    )

    agg = (
        fact.groupby(group_keys)
        .agg(
            flights_total=("route_key", "size"),
            cancelled_count=("cancelled_flag", "sum"),
            operated_count=("operated_flag", "sum"),
            severe_delay_count=("severe_delay_flag", "sum"),
        )
        .reset_index()
        .merge(delay_by_group, on=group_keys, how="left")
    )

    agg["cancellation_rate"] = agg["cancelled_count"] / agg["flights_total"]
    agg["severe_delay_rate"] = np.where(
        agg["operated_count"] > 0,
        agg["severe_delay_count"] / agg["operated_count"],
        np.nan,
    )

    # Round for readability
    agg["cancellation_rate"] = agg["cancellation_rate"].round(4)
    agg["severe_delay_rate"] = agg["severe_delay_rate"].round(4)
    agg["avg_dep_delay_operated"] = agg["avg_dep_delay_operated"].round(2)

    return agg


def compute_executive_summary(agg: pd.DataFrame) -> dict:
    """
    Compute top-level executive annotation values.

    Key metric: AA regional cancellation-rate ratio vs peers under marginal weather.
    """
    summary: dict = {}

    for weather in ("marginal", "adverse", "benign"):
        subset = agg[agg["weather_bucket"] == weather]
        aa = subset[subset["market_bucket"] == "aa_regional_basket"]
        ua = subset[subset["market_bucket"] == "ua_peer_basket"]
        dl = subset[subset["market_bucket"] == "dl_peer_basket"]

        def _rate(df: pd.DataFrame) -> float:
            if df.empty:
                return np.nan
            total = df["flights_total"].sum()
            cancelled = df["cancelled_count"].sum()
            return round(cancelled / total, 4) if total > 0 else np.nan

        aa_rate = _rate(aa)
        ua_rate = _rate(ua)
        dl_rate = _rate(dl)
        peer_avg = np.nanmean([ua_rate, dl_rate]) if not np.isnan([ua_rate, dl_rate]).all() else np.nan

        summary[f"aa_cancel_rate_{weather}"] = aa_rate
        summary[f"ua_cancel_rate_{weather}"] = ua_rate
        summary[f"dl_cancel_rate_{weather}"] = dl_rate
        summary[f"peer_avg_cancel_rate_{weather}"] = round(peer_avg, 4) if not np.isnan(peer_avg) else None

        if not np.isnan(aa_rate) and not np.isnan(peer_avg) and peer_avg > 0:
            ratio = round(aa_rate / peer_avg, 2)
            summary[f"aa_vs_peer_cancel_ratio_{weather}"] = ratio
        else:
            summary[f"aa_vs_peer_cancel_ratio_{weather}"] = None

    # Build annotation string for chart
    marginal_ratio = summary.get("aa_vs_peer_cancel_ratio_marginal")
    if marginal_ratio is not None:
        summary["chart_annotation"] = (
            f"AA regional cancellation rate in marginal weather is {marginal_ratio}x peers"
        )
    else:
        summary["chart_annotation"] = "Insufficient data for ratio annotation"

    # Period comparison (recent vs baseline for AA adverse)
    aa_rows = agg[agg["market_bucket"] == "aa_regional_basket"]
    for wx in ("adverse", "marginal"):
        baseline = aa_rows[(aa_rows["weather_bucket"] == wx) & (aa_rows["period_flag"] == "baseline")]
        recent = aa_rows[(aa_rows["weather_bucket"] == wx) & (aa_rows["period_flag"] == "recent")]
        b_rate = baseline["cancellation_rate"].mean() if not baseline.empty else None
        r_rate = recent["cancellation_rate"].mean() if not recent.empty else None
        summary[f"aa_cancel_baseline_{wx}"] = round(b_rate, 4) if b_rate is not None else None
        summary[f"aa_cancel_recent_{wx}"] = round(r_rate, 4) if r_rate is not None else None

    return summary


def main():
    parser = argparse.ArgumentParser(description="Analyze flight fragility and produce chart-ready data")
    parser.add_argument("--study", default="config/study.yaml")
    parser.add_argument("--fact", default="data/curated/flight_operability_fact.csv")
    parser.add_argument("--out", default="output/weather_fragility_chart_data.csv")
    parser.add_argument("--summary-out", default="output/fragility_summary.json")
    args = parser.parse_args()

    script_dir = Path(__file__).parent
    root = script_dir.parent
    study_path = root / args.study
    fact_path = root / args.fact
    out_path = root / args.out
    summary_path = root / args.summary_out

    out_path.parent.mkdir(parents=True, exist_ok=True)

    study = load_study(study_path)
    min_route_flights = study.get("min_route_flights", 100)

    if not fact_path.exists():
        raise FileNotFoundError(
            f"Fact table not found: {fact_path}\n"
            "Run 20_build_flight_fact.py first."
        )

    fact = load_fact(fact_path)

    # Check minimum route flight counts
    if "route_key" in fact.columns:
        route_counts = fact.groupby("route_key").size()
        sparse = route_counts[route_counts < min_route_flights]
        if not sparse.empty:
            log.warning(
                f"Routes with fewer than {min_route_flights} flights "
                f"(consider merging marginal/adverse buckets or expanding basket): "
                f"{sparse.to_dict()}"
            )

    agg = aggregate(fact)
    log.info(f"Aggregation complete: {len(agg)} rows at market×weather×period grain")

    agg.to_csv(out_path, index=False)
    log.info(f"Chart data written: {out_path}")

    summary = compute_executive_summary(agg)
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2, default=str)
    log.info(f"Executive summary written: {summary_path}")

    # Console highlights
    log.info("=== Fragility Summary ===")
    for wx in ("benign", "marginal", "adverse"):
        aa = summary.get(f"aa_cancel_rate_{wx}")
        peer = summary.get(f"peer_avg_cancel_rate_{wx}")
        ratio = summary.get(f"aa_vs_peer_cancel_ratio_{wx}")
        log.info(
            f"  {wx:8s}: AA={aa}  peer_avg={peer}  ratio={ratio}"
        )
    log.info(f"  Chart annotation: {summary.get('chart_annotation')}")


if __name__ == "__main__":
    main()
