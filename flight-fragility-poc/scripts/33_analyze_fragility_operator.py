#!/usr/bin/env python3
"""
33_analyze_fragility_operator.py — Fragility IV: operator-attribution
scorecard, combining Module A (focal corridor) and Module B (hub-spoke
expansion).

Aggregation grain: module x operator_class x hub_family x weather_bucket x
period_flag. Module A has no hub spread, so its rows carry the constant
hub_family label "focal_corridor" to keep one uniform output schema across
both modules.

Metric definitions
-------------------
- cancellation_rate, severe_delay_rate, controllable_cancel_rate,
  controllable_severe_delay_rate, late_arriving_severe_delay_rate: standard
  rate-over-denominator metrics already established by Fragility I/II.
- weather_fragility_rate: (cancelled_count + severe_delay_count) /
  flights_total within a cell — the spec lists this metric by name without
  a formula; this is the chosen, disclosed definition (a single combined
  "something went wrong" rate, consistent with Fragility I's two pillars).
- combined_fragility_score: w1*cancellation_rate + w2*severe_delay_rate +
  w3*controllable_severe_delay_rate + w4*late_arriving_severe_delay_rate,
  weights from config/study.yaml combined_fragility_score_weights.
- economic_burden_proxy: same excess-vs-baseline-rate x published-cost-
  benchmark methodology as 32_analyze_fragility_money.py (base scenario
  only, since this is a per-cell scorecard, not a scenario sensitivity
  table), but the baseline differs by module:
    Module A -> UA/DL peer-average rate (Fragility III baseline, unchanged)
    Module B -> AA-system average across included operator classes
                (AA_mainline/Envoy_operated/PSA_operated/resolved SkyWest or
                Republic contracts) within the same
                hub_family x weather_bucket x period_flag cell, pooling all
                included rows in that cell (not leave-one-out) per
                config/study.yaml hubspoke_economic_burden_baseline.

See flight_fragility_iv_operator_attribution_spec.md, "Implementation
notes," for why these two baselines differ and why no peer-carrier basket
exists yet at the new hubs.

Outputs
-------
output/fragility_iv_operator_chart_data.csv
output/fragility_iv_operator_scorecard.parquet
output/fragility_iv_summary.json

Usage
-----
python scripts/33_analyze_fragility_operator.py --study config/study.yaml
"""

import argparse
import json
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

sys.path.insert(0, str(Path(__file__).parent))
from lib.backend import read_table  # noqa: E402
from lib.operator_classify import apply_resolution_overrides, classify_operator, load_operator_classes  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
log = logging.getLogger(__name__)

GROUP_KEYS = ["module", "operator_class", "hub_family", "weather_bucket", "period_flag"]
PEER_BASKETS = ["ua_peer_basket", "dl_peer_basket"]
UNRESOLVED_OR_OTHER = {"SkyWest_unresolved", "Republic_unresolved", "Other_or_non_AA"}


def load_yaml(path: Path) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def load_module_a(root: Path, operator_config: dict) -> pd.DataFrame:
    path = root / "data/curated/flight_operability_fact.csv"
    if not path.exists():
        log.warning(f"  Module A fact table not found: {path} — skipping Module A.")
        return pd.DataFrame()

    fact = pd.read_csv(path, dtype=str)
    numeric_cols = ["dep_delay_min", "arr_delay_min", "carrier_delay_minutes", "late_aircraft_delay_minutes"]
    for col in numeric_cols:
        if col in fact.columns:
            fact[col] = pd.to_numeric(fact[col], errors="coerce")
    flag_cols = [
        "cancelled_flag", "diverted_flag", "severe_delay_flag", "operated_flag",
        "controllable_delay_flag", "controllable_cancel_flag", "late_arriving_flag",
        "controllable_severe_delay_flag", "late_arriving_severe_delay_flag",
    ]
    for col in flag_cols:
        if col in fact.columns:
            fact[col] = pd.to_numeric(fact[col], errors="coerce").fillna(0).astype(int)

    fact = classify_operator(fact, operator_config, route_basket_col="market_bucket")
    fact = apply_resolution_overrides(fact, root / "data/staging/operator_resolution.csv")
    fact["module"] = "focal_corridor"
    fact["hub_family"] = "focal_corridor"
    log.info(f"Module A (focal corridor) rows: {len(fact):,}")
    return fact


def load_module_b(root: Path, study: dict, operator_config: dict) -> pd.DataFrame:
    path = root / "data/curated/hubspoke_operator_fact"
    if not path.exists() or not any(path.rglob("*.parquet")):
        log.warning(f"  Module B fact table not found: {path} — skipping Module B.")
        return pd.DataFrame()

    backend = study.get("backend", "pandas")
    fact = read_table(path, backend=backend)
    fact["module"] = "hub_spoke"
    log.info(f"Module B (hub-spoke) rows: {len(fact):,} (backend={backend})")
    return fact


def aggregate_grain(fact: pd.DataFrame) -> pd.DataFrame:
    for k in GROUP_KEYS:
        if k not in fact.columns:
            fact[k] = "unknown"

    agg = (
        fact.groupby(GROUP_KEYS, dropna=False)
        .agg(
            flights_total=("operator_class", "size"),
            cancelled_count=("cancelled_flag", "sum"),
            operated_count=("operated_flag", "sum"),
            severe_delay_count=("severe_delay_flag", "sum"),
            controllable_cancel_count=("controllable_cancel_flag", "sum"),
            controllable_severe_delay_count=("controllable_severe_delay_flag", "sum"),
            late_arriving_severe_delay_count=("late_arriving_severe_delay_flag", "sum"),
            carrier_delay_minutes_sum=("carrier_delay_minutes", "sum"),
            late_aircraft_delay_minutes_sum=("late_aircraft_delay_minutes", "sum"),
        )
        .reset_index()
    )

    # All four rates use flights_total (unconditional denominator) so the weighted
    # combined_fragility_score compares outcomes over the same sample space and
    # does not reward aggressive cancellation with artificially lower delay rates.
    agg["cancellation_rate"] = agg["cancelled_count"] / agg["flights_total"].clip(lower=1)
    agg["severe_delay_rate"] = agg["severe_delay_count"] / agg["flights_total"].clip(lower=1)
    agg["controllable_cancel_rate"] = agg["controllable_cancel_count"] / agg["flights_total"].clip(lower=1)
    agg["controllable_severe_delay_rate"] = agg["controllable_severe_delay_count"] / agg["flights_total"].clip(lower=1)
    agg["late_arriving_severe_delay_rate"] = agg["late_arriving_severe_delay_count"] / agg["flights_total"].clip(lower=1)
    agg["weather_fragility_rate"] = (
        (agg["cancelled_count"] + agg["severe_delay_count"]) / agg["flights_total"].clip(lower=1)
    )
    return agg


def add_combined_score(agg: pd.DataFrame, weights: dict) -> pd.DataFrame:
    agg = agg.copy()
    agg["combined_fragility_score"] = (
        weights.get("w1_cancellation_rate", 0.25) * agg["cancellation_rate"]
        + weights.get("w2_severe_delay_rate", 0.25) * agg["severe_delay_rate"]
        + weights.get("w3_controllable_severe_delay_rate", 0.25) * agg["controllable_severe_delay_rate"]
        + weights.get("w4_late_arriving_severe_delay_rate", 0.25) * agg["late_arriving_severe_delay_rate"]
    )
    return agg


def _excess_cost_proxy(row: pd.Series, baseline_cancel_rate: float, baseline_controllable_rate: float,
                        baseline_cascade_rate: float, econ_config: dict) -> dict:
    flights_total = row["flights_total"]
    operated_count = row["operated_count"]

    expected_cancelled = flights_total * baseline_cancel_rate if not np.isnan(baseline_cancel_rate) else np.nan
    excess_cancelled = row["cancelled_count"] - expected_cancelled if not np.isnan(expected_cancelled) else np.nan

    expected_controllable = operated_count * baseline_controllable_rate if not np.isnan(baseline_controllable_rate) else np.nan
    excess_controllable = row["carrier_delay_minutes_sum"] - expected_controllable if not np.isnan(expected_controllable) else np.nan

    expected_cascade = operated_count * baseline_cascade_rate if not np.isnan(baseline_cascade_rate) else np.nan
    excess_cascade = row["late_aircraft_delay_minutes_sum"] - expected_cascade if not np.isnan(expected_cascade) else np.nan

    excess_minutes_basis = (
        (excess_controllable if not np.isnan(excess_controllable) else 0.0)
        + (excess_cascade if not np.isnan(excess_cascade) else 0.0)
    )
    excess_cancelled_clean = excess_cancelled if not np.isnan(excess_cancelled) else 0.0

    cancel_equiv_minutes = excess_cancelled_clean * econ_config["cancellation_equivalent_minutes"]["base"]
    airline_cost = excess_minutes_basis * econ_config["airline_block_cost_per_min"]["base"]
    passenger_cost = ((excess_minutes_basis + cancel_equiv_minutes) / 60.0) * econ_config["value_of_time_per_hour"]["base"]
    combined_cost = airline_cost + passenger_cost

    per_1000 = combined_cost / (flights_total / 1000.0) if flights_total > 0 else np.nan

    return {
        "excess_cancelled_vs_baseline": round(excess_cancelled_clean, 2),
        "excess_controllable_delay_minutes": round(excess_controllable, 1) if not np.isnan(excess_controllable) else None,
        "excess_cascade_delay_minutes": round(excess_cascade, 1) if not np.isnan(excess_cascade) else None,
        "economic_burden_proxy_usd": round(combined_cost, 2),
        "economic_burden_proxy_usd_per_1000_flights": round(per_1000, 2) if not np.isnan(per_1000) else None,
    }


def apply_module_a_baseline(agg: pd.DataFrame, fact: pd.DataFrame, econ_config: dict) -> pd.DataFrame:
    """Baseline #2: UA/DL peer-average rate, computed per weather_bucket x
    period_flag cell (peer baskets have no operator_class or hub_family
    split — the same peer rate applies to every operator_class row in that
    weather/period cell)."""
    peer = fact[fact["market_bucket"].isin(PEER_BASKETS)] if "market_bucket" in fact.columns else pd.DataFrame()
    peer_rates: dict[tuple, dict] = {}
    if not peer.empty:
        peer_operated = peer[peer["operated_flag"] == 1]
        for (wx, period), grp in peer.groupby(["weather_bucket", "period_flag"]):
            op_grp = peer_operated[(peer_operated["weather_bucket"] == wx) & (peer_operated["period_flag"] == period)]
            cancel_rate = grp["cancelled_flag"].sum() / max(len(grp), 1)
            controllable_rate = op_grp["carrier_delay_minutes"].sum() / max(len(op_grp), 1) if not op_grp.empty else np.nan
            cascade_rate = op_grp["late_aircraft_delay_minutes"].sum() / max(len(op_grp), 1) if not op_grp.empty else np.nan
            peer_rates[(wx, period)] = {
                "cancel": cancel_rate, "controllable": controllable_rate, "cascade": cascade_rate,
            }

    rows = []
    for _, row in agg.iterrows():
        rates = peer_rates.get((row["weather_bucket"], row["period_flag"]), {})
        proxy = _excess_cost_proxy(
            row,
            rates.get("cancel", np.nan), rates.get("controllable", np.nan), rates.get("cascade", np.nan),
            econ_config,
        )
        rows.append({**row.to_dict(), "baseline_label": "ua_dl_peer_average", **proxy})
    return pd.DataFrame(rows)


def apply_module_b_baseline(agg: pd.DataFrame, fact: pd.DataFrame, econ_config: dict) -> pd.DataFrame:
    """Baseline #3: AA-system average across included operator classes,
    pooled per hub_family x weather_bucket x period_flag cell (all included
    rows in that cell, not leave-one-out)."""
    included = fact[~fact["operator_class"].isin(UNRESOLVED_OR_OTHER)] if "operator_class" in fact.columns else pd.DataFrame()
    system_rates: dict[tuple, dict] = {}
    if not included.empty:
        included_operated = included[included["operated_flag"] == 1]
        for (hub, wx, period), grp in included.groupby(["hub_family", "weather_bucket", "period_flag"]):
            op_grp = included_operated[
                (included_operated["hub_family"] == hub) &
                (included_operated["weather_bucket"] == wx) &
                (included_operated["period_flag"] == period)
            ]
            cancel_rate = grp["cancelled_flag"].sum() / max(len(grp), 1)
            controllable_rate = op_grp["carrier_delay_minutes"].sum() / max(len(op_grp), 1) if not op_grp.empty else np.nan
            cascade_rate = op_grp["late_aircraft_delay_minutes"].sum() / max(len(op_grp), 1) if not op_grp.empty else np.nan
            system_rates[(hub, wx, period)] = {
                "cancel": cancel_rate, "controllable": controllable_rate, "cascade": cascade_rate,
            }

    rows = []
    for _, row in agg.iterrows():
        rates = system_rates.get((row["hub_family"], row["weather_bucket"], row["period_flag"]), {})
        proxy = _excess_cost_proxy(
            row,
            rates.get("cancel", np.nan), rates.get("controllable", np.nan), rates.get("cascade", np.nan),
            econ_config,
        )
        rows.append({**row.to_dict(), "baseline_label": "aa_system_average", **proxy})
    return pd.DataFrame(rows)


def run_qa(scorecard: pd.DataFrame, study: dict) -> list[str]:
    notes = []
    min_sample = study.get("min_sample_threshold", 30)
    sparse = scorecard[scorecard["flights_total"] < min_sample]
    if not sparse.empty:
        notes.append(
            f"{len(sparse)} operator/hub/weather/period cells have fewer than "
            f"{min_sample} flights (min_sample_threshold) — treat their rates as indicative only."
        )

    unresolved = scorecard[scorecard["operator_class"].isin(["SkyWest_unresolved", "Republic_unresolved"])]
    if not unresolved.empty:
        unresolved_flights = int(unresolved["flights_total"].sum())
        notes.append(
            f"{unresolved_flights:,} flights remain in an unresolved operator-ambiguity label "
            "(SkyWest_unresolved / Republic_unresolved) and are excluded from operator-class "
            "comparisons; see scripts/15_resolve_operator_ambiguity.py."
        )

    weights = study.get("combined_fragility_score_weights", {})
    notes.append(f"combined_fragility_score weights used: {weights}")

    modules = sorted(scorecard["module"].unique())
    notes.append(f"Modules present: {modules}")

    notes.append(
        "All four combined_fragility_score components use flights_total as their denominator "
        "(unconditional probability over the full scheduled sample). This ensures the weighted "
        "sum compares outcomes over the same sample space for every component."
    )

    notes.append(
        "Module B economic baseline (aa_system_average) pools all resolved operator classes "
        "within the same hub×weather×period cell — it is NOT leave-one-out. High-volume "
        "operators with above-average fragility partially suppress their own excess signal "
        "against this baseline."
    )

    return notes


def main():
    parser = argparse.ArgumentParser(description="Analyze Fragility IV operator attribution")
    parser.add_argument("--study", default="config/study.yaml")
    parser.add_argument("--econ-config", default="config/economic_scenarios.yaml")
    parser.add_argument("--out", default="output/fragility_iv_operator_chart_data.csv")
    parser.add_argument("--scorecard-out", default="output/fragility_iv_operator_scorecard.parquet")
    parser.add_argument("--summary-out", default="output/fragility_iv_summary.json")
    args = parser.parse_args()

    script_dir = Path(__file__).parent
    root = script_dir.parent
    study_path = root / args.study
    econ_path = root / args.econ_config
    out_path = root / args.out
    scorecard_path = root / args.scorecard_out
    summary_path = root / args.summary_out

    out_path.parent.mkdir(parents=True, exist_ok=True)

    study = load_yaml(study_path)
    econ_config = load_yaml(econ_path)
    operator_config = load_operator_classes(root / study.get("operator_classes_config", "config/operator_classes.yaml"))
    weights = study.get("combined_fragility_score_weights", {})

    fact_a = load_module_a(root, operator_config)
    fact_b = load_module_b(root, study, operator_config)

    if fact_a.empty and fact_b.empty:
        log.error("Neither Module A nor Module B fact tables are available. "
                   "Run 20_build_flight_fact.py and/or 21_build_hubspoke_fact.py first.")
        raise SystemExit(1)

    scorecard_parts = []

    if not fact_a.empty:
        agg_a = aggregate_grain(fact_a)
        agg_a = apply_module_a_baseline(agg_a, fact_a, econ_config)
        scorecard_parts.append(agg_a)

    if not fact_b.empty:
        agg_b = aggregate_grain(fact_b)
        agg_b = apply_module_b_baseline(agg_b, fact_b, econ_config)
        scorecard_parts.append(agg_b)

    scorecard = pd.concat(scorecard_parts, ignore_index=True)
    scorecard = add_combined_score(scorecard, weights)

    for col in ("cancellation_rate", "severe_delay_rate", "controllable_cancel_rate",
                "controllable_severe_delay_rate", "late_arriving_severe_delay_rate",
                "weather_fragility_rate", "combined_fragility_score"):
        scorecard[col] = scorecard[col].round(4)

    scorecard.to_csv(out_path, index=False)
    log.info(f"Chart data written: {out_path} ({len(scorecard):,} rows)")

    try:
        scorecard.to_parquet(scorecard_path, index=False)
        log.info(f"Scorecard parquet written: {scorecard_path}")
    except Exception as exc:
        log.warning(f"  Could not write scorecard parquet ({exc}) — CSV output above is still authoritative.")

    qa_notes = run_qa(scorecard, study)

    min_sample = study.get("min_sample_threshold", 30)
    ranked = (
        scorecard[scorecard["flights_total"] >= min_sample]
        .sort_values("combined_fragility_score", ascending=False)
    )
    top = ranked.iloc[0] if not ranked.empty else None
    annotation = None
    if top is not None:
        annotation = (
            f"Across the included AA network slices, {top['operator_class']} at "
            f"{top['hub_family']} shows the highest combined fragility score "
            f"({top['combined_fragility_score']:.3f}) among cells with at least "
            f"{min_sample} flights ({top['flights_total']:,} flights in this cell)."
        )

    summary = {
        "qa_notes": qa_notes,
        "combined_fragility_score_weights": weights,
        "modules_present": sorted(scorecard["module"].unique()),
        "operator_classes_present": sorted(scorecard["operator_class"].unique()),
        "hub_families_present": sorted(scorecard["hub_family"].unique()),
        "chart_annotation": annotation or "Insufficient data for ranking annotation",
        "top_cell": top.to_dict() if top is not None else None,
    }
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2, default=str)
    log.info(f"Executive summary written: {summary_path}")

    log.info("=== Fragility IV Operator Attribution QA ===")
    for note in qa_notes:
        log.info(f"  - {note}")
    log.info(f"  Chart annotation: {summary['chart_annotation']}")


if __name__ == "__main__":
    main()
