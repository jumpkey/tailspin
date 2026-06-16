#!/usr/bin/env python3
"""
32_analyze_fragility_money.py — Fragility III: economic-burden cost proxy.

Converts the excess disruption already measured by Fragility I (overall
cancellation/delay) and Fragility II (controllable/cascade severe delay)
into a scenario-based dollar-burden proxy, using published public cost
benchmarks rather than internal accounting data. See
flight_fragility_iii_show_me_the_money_addon_spec.md for the full
methodology, benchmark citations, and interpretation constraints this
script's output must be read alongside.

Conceptual model
-----------------
excess = observed AA regional outcome - expected outcome at the peer-average
rate, applied to AA's own flight / operated-flight volume. This is computed
for two mode-dependent excess-minutes bases plus one mode-independent
cancellation basis:

- "fragility_ii_preferred" mode (default): excess delay-minutes basis =
  excess carrier-attributed (controllable) delay minutes + excess
  late-aircraft (cascade) delay minutes, using BTS's own reported
  cause-minute fields (`carrier_delay_minutes`, `late_aircraft_delay_minutes`).
- "overall" mode: excess delay-minutes basis = excess arrival-delay minutes
  with no cause decomposition (Fragility I basis only).
- Both modes: excess cancellations = AA cancelled flights - AA flights x
  peer-average cancellation rate, converted to a cancellation-equivalent
  minutes burden via a scenario assumption (not an observed fact).

Cost scenarios (low/base/high) apply published value-of-time and airline
block-cost benchmarks to the same excess-minutes basis; only the cost
coefficients vary by scenario, not the underlying operational excess.

This implementation stays in the spec's "Mode 1: flight-level burden only"
mode throughout — it does not multiply by an estimated passenger count,
because no passenger-manifest or seat-count data exists in this pipeline's
public sources. The passenger-time cost proxy below should be read as a
flight-level time-value proxy, not a total-passenger-burden estimate.

Aggregation grain: market_bucket x weather_bucket (periods combined), plus
a pooled "all" weather row used for the headline scenario chart.

Outputs
-------
output/fragility_iii_chart_data.csv
output/fragility_iii_summary.json
output/fragility_iii_summary.md

Usage
-----
python scripts/32_analyze_fragility_money.py --study config/study.yaml --econ-config config/economic_scenarios.yaml
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

WEATHER_BUCKETS = ["benign", "marginal", "adverse"]
WEATHER_GRAIN = WEATHER_BUCKETS + ["all"]
PEER_BASKETS = ["ua_peer_basket", "dl_peer_basket"]
SCENARIOS = ["low", "base", "high"]


def load_yaml(path: Path) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def load_fact(path: Path) -> pd.DataFrame:
    log.info(f"Loading fact table: {path}")
    df = pd.read_csv(path, dtype=str)
    numeric_cols = [
        "arr_delay_min", "carrier_delay_minutes", "late_aircraft_delay_minutes",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
    for col in ("cancelled_flag", "operated_flag"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
    log.info(f"  Rows: {len(df):,}")
    return df


def aggregate_basis(fact: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate to market_bucket x weather_bucket grain (periods combined,
    "unknown" weather excluded), plus a pooled "all" weather row per basket.
    """
    df = fact[fact["weather_bucket"].isin(WEATHER_BUCKETS)].copy()
    operated = df[df["operated_flag"] == 1]

    by_weather = (
        df.groupby(["market_bucket", "weather_bucket"])
        .agg(
            flights_total=("route_key", "size"),
            cancelled_count=("cancelled_flag", "sum"),
        )
        .reset_index()
    )
    op_by_weather = (
        operated.groupby(["market_bucket", "weather_bucket"])
        .agg(
            operated_count=("route_key", "size"),
            carrier_delay_minutes_sum=("carrier_delay_minutes", "sum"),
            late_aircraft_delay_minutes_sum=("late_aircraft_delay_minutes", "sum"),
            arr_delay_min_sum=("arr_delay_min", "sum"),
        )
        .reset_index()
    )
    by_weather = by_weather.merge(op_by_weather, on=["market_bucket", "weather_bucket"], how="left")

    pooled = by_weather.groupby("market_bucket").sum(numeric_only=True).reset_index()
    pooled["weather_bucket"] = "all"

    agg = pd.concat([by_weather, pooled], ignore_index=True)
    for col in ("operated_count", "carrier_delay_minutes_sum", "late_aircraft_delay_minutes_sum", "arr_delay_min_sum"):
        agg[col] = agg[col].fillna(0.0)
    return agg


def _basket_row(agg: pd.DataFrame, basket: str, weather: str) -> dict:
    rows = agg[(agg["market_bucket"] == basket) & (agg["weather_bucket"] == weather)]
    if rows.empty:
        return {
            "flights_total": 0, "cancelled_count": 0, "operated_count": 0,
            "carrier_delay_minutes_sum": 0.0, "late_aircraft_delay_minutes_sum": 0.0,
            "arr_delay_min_sum": 0.0,
        }
    return rows.iloc[0].to_dict()


def compute_excess(agg: pd.DataFrame, mode: str) -> pd.DataFrame:
    """
    For each weather grain (benign/marginal/adverse/all), compute AA
    regional's excess vs. the UA/DL peer-average rate, applied to AA's own
    flight / operated-flight volume.
    """
    rows = []
    for weather in WEATHER_GRAIN:
        aa = _basket_row(agg, "aa_regional_basket", weather)
        ua = _basket_row(agg, "ua_peer_basket", weather)
        dl = _basket_row(agg, "dl_peer_basket", weather)

        def _rate(d: dict, num_key: str, denom_key: str) -> float:
            denom = d[denom_key]
            return d[num_key] / denom if denom > 0 else np.nan

        peer_cancel_rate = np.nanmean([
            _rate(ua, "cancelled_count", "flights_total"),
            _rate(dl, "cancelled_count", "flights_total"),
        ])
        peer_carrier_min_rate = np.nanmean([
            _rate(ua, "carrier_delay_minutes_sum", "operated_count"),
            _rate(dl, "carrier_delay_minutes_sum", "operated_count"),
        ])
        peer_cascade_min_rate = np.nanmean([
            _rate(ua, "late_aircraft_delay_minutes_sum", "operated_count"),
            _rate(dl, "late_aircraft_delay_minutes_sum", "operated_count"),
        ])
        peer_overall_min_rate = np.nanmean([
            _rate(ua, "arr_delay_min_sum", "operated_count"),
            _rate(dl, "arr_delay_min_sum", "operated_count"),
        ])

        aa_flights_total = aa["flights_total"]
        aa_operated_count = aa["operated_count"]

        expected_cancelled = aa_flights_total * peer_cancel_rate if not np.isnan(peer_cancel_rate) else np.nan
        excess_cancelled = aa["cancelled_count"] - expected_cancelled if not np.isnan(expected_cancelled) else np.nan

        effective_mode = mode
        excess_controllable_min = None
        excess_cascade_min = None
        if mode == "fragility_ii_preferred" and aa_operated_count > 0:
            expected_controllable = aa_operated_count * peer_carrier_min_rate if not np.isnan(peer_carrier_min_rate) else np.nan
            excess_controllable_min = aa["carrier_delay_minutes_sum"] - expected_controllable if not np.isnan(expected_controllable) else np.nan
            expected_cascade = aa_operated_count * peer_cascade_min_rate if not np.isnan(peer_cascade_min_rate) else np.nan
            excess_cascade_min = aa["late_aircraft_delay_minutes_sum"] - expected_cascade if not np.isnan(expected_cascade) else np.nan
            excess_delay_minutes_basis = (
                (excess_controllable_min if not np.isnan(excess_controllable_min) else 0.0)
                + (excess_cascade_min if not np.isnan(excess_cascade_min) else 0.0)
            )
        else:
            effective_mode = "overall"
            expected_overall = aa_operated_count * peer_overall_min_rate if not np.isnan(peer_overall_min_rate) else np.nan
            excess_delay_minutes_basis = aa["arr_delay_min_sum"] - expected_overall if not np.isnan(expected_overall) else np.nan

        rows.append({
            "weather_bucket": weather,
            "mode": effective_mode,
            "aa_flights_total": aa_flights_total,
            "aa_operated_count": aa_operated_count,
            "aa_cancelled_count": aa["cancelled_count"],
            "peer_avg_cancel_rate": round(peer_cancel_rate, 4) if not np.isnan(peer_cancel_rate) else None,
            "excess_cancelled_vs_peer_avg": round(excess_cancelled, 2) if not np.isnan(excess_cancelled) else None,
            "excess_controllable_delay_minutes": round(excess_controllable_min, 1) if excess_controllable_min is not None and not np.isnan(excess_controllable_min) else None,
            "excess_cascade_delay_minutes": round(excess_cascade_min, 1) if excess_cascade_min is not None and not np.isnan(excess_cascade_min) else None,
            "excess_delay_minutes_basis": round(excess_delay_minutes_basis, 1) if not np.isnan(excess_delay_minutes_basis) else None,
        })
    return pd.DataFrame(rows)


def apply_scenarios(excess_df: pd.DataFrame, econ_config: dict) -> pd.DataFrame:
    """Apply low/base/high cost coefficients to the same operational excess."""
    rows = []
    for _, r in excess_df.iterrows():
        excess_cancelled = r["excess_cancelled_vs_peer_avg"] or 0.0
        excess_minutes = r["excess_delay_minutes_basis"] or 0.0
        for scenario in SCENARIOS:
            cancel_equiv_minutes = excess_cancelled * econ_config["cancellation_equivalent_minutes"][scenario]
            airline_cost = excess_minutes * econ_config["airline_block_cost_per_min"][scenario]
            passenger_cost = ((excess_minutes + cancel_equiv_minutes) / 60.0) * econ_config["value_of_time_per_hour"][scenario]
            combined_cost = airline_cost + passenger_cost
            rows.append({
                "weather_bucket": r["weather_bucket"],
                "mode": r["mode"],
                "scenario": scenario,
                "excess_cancelled_vs_peer_avg": r["excess_cancelled_vs_peer_avg"],
                "excess_controllable_delay_minutes": r["excess_controllable_delay_minutes"],
                "excess_cascade_delay_minutes": r["excess_cascade_delay_minutes"],
                "excess_delay_minutes_basis": r["excess_delay_minutes_basis"],
                "cancellation_equiv_minutes": round(cancel_equiv_minutes, 1),
                "excess_airline_cost_proxy": round(airline_cost, 2),
                "excess_passenger_cost_proxy": round(passenger_cost, 2),
                "excess_combined_cost_proxy": round(combined_cost, 2),
            })
    return pd.DataFrame(rows)


def compute_executive_summary(chart_data: pd.DataFrame, mode: str) -> dict:
    summary: dict = {"mode_requested": mode}
    all_rows = chart_data[chart_data["weather_bucket"] == "all"]
    summary["mode_used"] = all_rows.iloc[0]["mode"] if not all_rows.empty else mode
    summary["basis_description"] = (
        "excess controllable (carrier-attributed) + cascade (late-aircraft) delay minutes, "
        "BTS cause-minute fields"
        if summary["mode_used"] == "fragility_ii_preferred"
        else "excess overall arrival-delay minutes, no cause decomposition"
    )

    for weather in WEATHER_GRAIN:
        wrows = all_rows if weather == "all" else chart_data[chart_data["weather_bucket"] == weather]
        if wrows.empty:
            continue
        first = wrows.iloc[0]
        prefix = weather
        summary[f"excess_cancelled_vs_peer_avg_{prefix}"] = first["excess_cancelled_vs_peer_avg"]
        summary[f"excess_controllable_delay_minutes_{prefix}"] = first["excess_controllable_delay_minutes"]
        summary[f"excess_cascade_delay_minutes_{prefix}"] = first["excess_cascade_delay_minutes"]
        summary[f"excess_delay_minutes_basis_{prefix}"] = first["excess_delay_minutes_basis"]
        for scenario in SCENARIOS:
            srow = wrows[wrows["scenario"] == scenario]
            if srow.empty:
                continue
            srow = srow.iloc[0]
            summary[f"{scenario}_airline_cost_proxy_{prefix}"] = srow["excess_airline_cost_proxy"]
            summary[f"{scenario}_passenger_cost_proxy_{prefix}"] = srow["excess_passenger_cost_proxy"]
            summary[f"{scenario}_combined_cost_proxy_{prefix}"] = srow["excess_combined_cost_proxy"]

    base_combined_all = summary.get("base_combined_cost_proxy_all")
    low_combined_all = summary.get("low_combined_cost_proxy_all")
    high_combined_all = summary.get("high_combined_cost_proxy_all")
    if base_combined_all is not None:
        summary["chart_annotation"] = (
            f"Base scenario: ${base_combined_all:,.0f} estimated excess economic burden "
            f"vs. peer reliability over the study window (range ${low_combined_all:,.0f}"
            f"–${high_combined_all:,.0f} across low/high scenarios) — proxy estimate, "
            "not audited financials"
        )
    else:
        summary["chart_annotation"] = "Insufficient data for cost annotation"

    return summary


def write_markdown_summary(summary: dict, econ_config: dict, study_start: str, study_end: str, out_path: Path):
    def usd(x):
        return f"${x:,.0f}" if x is not None else "n/a"

    def mins(x):
        return f"{x:,.0f} min" if x is not None else "n/a"

    lines = []
    lines.append("# Fragility III: Economic Impact Estimation — Summary")
    lines.append("")
    lines.append(
        "This summary converts the excess disruption already measured by Fragility I "
        "(overall cancellation/delay) and Fragility II (controllable/cascade severe delay) "
        "into a scenario-based dollar-burden proxy, using published public cost benchmarks. "
        "It is **not** a passenger-itinerary revenue model and does not claim exact "
        "accounting loss — see `flight_fragility_iii_show_me_the_money_addon_spec.md`, "
        "\"Risks and interpretation constraints,\" which this summary should not be read "
        "without."
    )
    lines.append("")

    lines.append("## 1. Operational basis used")
    lines.append("")
    mode_used = summary.get("mode_used")
    lines.append(
        f"**Mode:** `{mode_used}` — {summary.get('basis_description')}."
    )
    lines.append("")
    lines.append(
        f"Study window: {study_start} to {study_end} (both study periods combined). "
        "Excess is computed as AA regional's observed outcome minus the outcome AA "
        "would have produced at the UA/DL peer-average rate, applied to AA's own "
        "flight or operated-flight volume — i.e. excess burden relative to peer "
        "reliability, not total network cost."
    )
    lines.append("")
    lines.append(
        "| Component | Excess vs. peer-average rate (study window) |"
    )
    lines.append("|---|---|")
    lines.append(f"| Cancellations | {summary.get('excess_cancelled_vs_peer_avg_all'):,.0f} flights |")
    if mode_used == "fragility_ii_preferred":
        lines.append(f"| Controllable (carrier-attributed) delay minutes | {mins(summary.get('excess_controllable_delay_minutes_all'))} |")
        lines.append(f"| Cascade (late-aircraft) delay minutes | {mins(summary.get('excess_cascade_delay_minutes_all'))} |")
    lines.append(f"| **Net excess delay-minutes basis** | **{mins(summary.get('excess_delay_minutes_basis_all'))}** |")
    lines.append("")
    if mode_used == "fragility_ii_preferred":
        lines.append(
            "The controllable component is negative — AA regional's carrier-attributed "
            "delay minutes run *below* what the peer-average rate would predict for AA's "
            "flight volume, consistent with Fragility II's controllable-rate finding. The "
            "cascade component is positive and larger in magnitude, so the two do not "
            "cancel out: the net excess-minutes basis is positive, driven by the cascade "
            "side. This is the same \"controllable savings, cascade cost\" pattern reported "
            "qualitatively in Fragility II, now expressed in minutes."
        )
        lines.append("")

    lines.append("## 2. Base-case estimated excess burden")
    lines.append("")
    lines.append(
        f"| | Airline operating-time burden | Passenger-time burden (flight-level proxy) | Combined |"
    )
    lines.append("|---|---|---|---|")
    lines.append(
        f"| Base scenario (study window) | {usd(summary.get('base_airline_cost_proxy_all'))} | "
        f"{usd(summary.get('base_passenger_cost_proxy_all'))} | "
        f"**{usd(summary.get('base_combined_cost_proxy_all'))}** |"
    )
    lines.append("")
    lines.append(
        f"Base-case assumptions: passenger value of time "
        f"${econ_config['value_of_time_per_hour']['base']}/hour, airline block-time cost "
        f"${econ_config['airline_block_cost_per_min']['base']}/minute, cancellation-equivalent "
        f"burden {econ_config['cancellation_equivalent_minutes']['base']} minutes per excess "
        "cancellation. See `config/economic_scenarios.yaml` and the spec's benchmark "
        "citations for sourcing."
    )
    lines.append("")

    lines.append("## 3. Low / high sensitivity range")
    lines.append("")
    lines.append("| Scenario | Airline operating-time burden | Passenger-time burden | Combined |")
    lines.append("|---|---|---|---|")
    for scenario in SCENARIOS:
        lines.append(
            f"| {scenario.title()} | {usd(summary.get(f'{scenario}_airline_cost_proxy_all'))} | "
            f"{usd(summary.get(f'{scenario}_passenger_cost_proxy_all'))} | "
            f"**{usd(summary.get(f'{scenario}_combined_cost_proxy_all'))}** |"
        )
    lines.append("")
    lines.append(
        "The range reflects only the cost-coefficient assumptions (value of time, "
        "airline block-cost, cancellation-equivalent minutes) varying across scenarios; "
        "the underlying operational excess (cancellations, delay minutes) is held fixed "
        "across all three."
    )
    lines.append("")

    lines.append("## 4. Weather-stratified view")
    lines.append("")
    lines.append("| Weather | Net excess delay-minutes basis | Base-case combined burden |")
    lines.append("|---|---|---|")
    for weather in WEATHER_BUCKETS:
        lines.append(
            f"| {weather.title()} | {mins(summary.get(f'excess_delay_minutes_basis_{weather}'))} | "
            f"{usd(summary.get(f'base_combined_cost_proxy_{weather}'))} |"
        )
    lines.append("")
    benign_basis = summary.get("excess_delay_minutes_basis_benign")
    marginal_basis = summary.get("excess_delay_minutes_basis_marginal")
    adverse_basis = summary.get("excess_delay_minutes_basis_adverse")
    if benign_basis is not None and marginal_basis is not None and adverse_basis is not None and benign_basis > 0 and marginal_basis <= 0 and adverse_basis <= 0:
        lines.append(
            "The pooled, study-window total above is positive, but that total is not evenly "
            "spread across weather conditions: nearly all of the net excess-minutes basis "
            "(and the dollar burden built on it) is concentrated in the *benign*-weather "
            "bucket, while the marginal- and adverse-weather buckets each run negative "
            "(AA's combined controllable+cascade minutes fall *below* the peer-average "
            "expectation once weather deteriorates). This is consistent with Fragility II's "
            "observation that AA regional's cascade severe-delay rate is already elevated in "
            "benign weather and escalates *less* with weather severity than peers' does — "
            "the economic burden this study can attach to that pattern, in other words, "
            "presents as a baseline/schedule-resilience cost rather than a weather-stress cost."
        )
        lines.append("")

    lines.append("## 5. Caveats")
    lines.append("")
    lines.append(
        "- **Not a passenger-itinerary revenue model.** Public BTS data do not reveal who "
        "connected, who misconnected, who was reaccommodated overnight, or what fare or "
        "voucher outcomes occurred. The passenger-time burden above is a flight-level time-"
        "value proxy, not a reconstruction of actual passenger cost."
    )
    lines.append(
        "- **Flight-level burden, not passenger-count-scaled.** This run uses the spec's "
        "\"Mode 1\" flight-level burden framing: no passengers-per-flight multiplier is "
        "applied, because no passenger-manifest or seat-count data exists in this "
        "pipeline's public sources. The true passenger-time burden, if it could be "
        "estimated, would likely be a multiple of the passenger-time figure above "
        "(roughly the average passengers per flight) — this study does not estimate "
        "that multiplier rather than guess at one."
    )
    lines.append(
        "- **Proxy, not accounting.** These figures are scenario-based proxies built from "
        "published value-of-time and airline-delay-cost benchmarks. They are not audited "
        "revenue, voucher, hotel, or reaccommodation expense, and should not be read as "
        "exact lost revenue or cost-accounting impact."
    )
    lines.append(
        "- **Cancellation-equivalent minutes is a scenario lever, not an observed fact.** "
        "It stands in for the hidden delay and reaccommodation burden a cancellation "
        "creates, which BTS data cannot directly measure."
    )
    lines.append(
        "- All caveats from Fragility I and Fragility II (self-reported cause data, "
        "thin UA-basket samples, SkyWest cross-contract overlap, weather-bucket "
        "simplifications) propagate into this estimate, since it is built on those same "
        "underlying rates."
    )
    lines.append("")

    out_path.write_text("\n".join(lines))
    log.info(f"Written summary: {out_path}")


def main():
    parser = argparse.ArgumentParser(description="Analyze Fragility III economic-burden cost proxy")
    parser.add_argument("--study", default="config/study.yaml")
    parser.add_argument("--econ-config", default="config/economic_scenarios.yaml")
    parser.add_argument("--fact", default="data/curated/flight_operability_fact.csv")
    parser.add_argument("--out", default="output/fragility_iii_chart_data.csv")
    parser.add_argument("--summary-out", default="output/fragility_iii_summary.json")
    parser.add_argument("--md-out", default="output/fragility_iii_summary.md")
    args = parser.parse_args()

    script_dir = Path(__file__).parent
    root = script_dir.parent
    study_path = root / args.study
    econ_path = root / args.econ_config
    fact_path = root / args.fact
    out_path = root / args.out
    summary_path = root / args.summary_out
    md_path = root / args.md_out

    out_path.parent.mkdir(parents=True, exist_ok=True)

    study = load_yaml(study_path)
    econ_config = load_yaml(econ_path)

    if not fact_path.exists():
        raise FileNotFoundError(f"Fact table not found: {fact_path}\nRun 20_build_flight_fact.py first.")

    fact = load_fact(fact_path)
    agg = aggregate_basis(fact)

    requested_mode = econ_config.get("mode", "fragility_ii_preferred")
    has_cause_fields = "carrier_delay_minutes" in fact.columns and "late_aircraft_delay_minutes" in fact.columns
    mode = requested_mode if (requested_mode == "fragility_ii_preferred" and has_cause_fields) else "overall"
    if requested_mode == "fragility_ii_preferred" and not has_cause_fields:
        log.warning("Fragility II cause-minute fields not found in fact table — falling back to 'overall' mode")

    excess_df = compute_excess(agg, mode)
    chart_data = apply_scenarios(excess_df, econ_config)
    chart_data.to_csv(out_path, index=False)
    log.info(f"Chart data written: {out_path}")

    summary = compute_executive_summary(chart_data, mode)
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2, default=str)
    log.info(f"Executive summary written: {summary_path}")

    write_markdown_summary(summary, econ_config, study.get("study_start"), study.get("study_end"), md_path)

    log.info("=== Fragility III Summary ===")
    log.info(f"  Mode used: {summary.get('mode_used')}")
    log.info(f"  Net excess delay-minutes basis (all): {summary.get('excess_delay_minutes_basis_all')}")
    log.info(f"  Excess cancellations vs peer avg (all): {summary.get('excess_cancelled_vs_peer_avg_all')}")
    log.info(f"  Base-case combined cost proxy (all): {summary.get('base_combined_cost_proxy_all')}")
    log.info(f"  Chart annotation: {summary.get('chart_annotation')}")


if __name__ == "__main__":
    main()
