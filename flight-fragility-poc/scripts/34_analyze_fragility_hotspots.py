#!/usr/bin/env python3
"""
34_analyze_fragility_hotspots.py — Fragility V: network hotspot engine.

Reads from the Fragility IV curated hub-spoke fact table and produces a
ranked hotspot scorecard across AA's hub-spoke network. Aggregation grain is
(hub_family, spoke_airport, operator_class) pooled across all weather
conditions and both study periods. Six normalized fragility components are
weighted under four weighting scenarios; a robustness score measures how
consistently a cell appears in the top-N across scenarios. Persistence
(Module E) flags cells that rank in the top-N in both baseline and recent
sub-periods independently.

Outputs
-------
output/fragility_v_hotspot_scorecard.parquet   — full scorecard, partitioned by hub_family
output/fragility_v_hotspot_rankings.csv        — top-N by base score (human-readable)
output/fragility_v_hub_rollup.csv              — Module C: hub concentration in top-N
output/fragility_v_operator_rollup.csv         — Module B: operator concentration in top-N
output/fragility_v_scenario_robustness.csv     — 4-scenario scores for all included cells
output/fragility_v_summary.json               — machine-readable summary with QA notes
output/fragility_v_summary.md                 — human-readable prioritization memo

Usage
-----
python scripts/34_analyze_fragility_hotspots.py --study config/study.yaml
python scripts/34_analyze_fragility_hotspots.py --run-mode local --top-n 20
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
from lib.backend import read_table, write_partitioned_parquet  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
log = logging.getLogger(__name__)

CELL_KEYS = ["hub_family", "spoke_airport", "operator_class"]
EXCLUDE_FROM_SCORING = {"Other_or_non_AA"}
COMPONENT_COLS = [
    "norm_cancel",
    "norm_severe_delay",
    "norm_controllable",
    "norm_cascade",
    "norm_weather_sensitivity",
    "norm_economic_burden",
]
WEIGHT_KEYS = ["cancel", "severe_delay", "controllable", "cascade", "weather_sensitivity", "economic_burden"]
NORM_TO_WEIGHT = dict(zip(COMPONENT_COLS, WEIGHT_KEYS))


def load_yaml(path: Path) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def load_fact(fact_dir: Path, study: dict) -> pd.DataFrame:
    backend = study.get("backend", "pandas")
    df = read_table(str(fact_dir), backend=backend)
    log.info(f"Loaded fact table: {len(df):,} rows, {len(df.columns)} columns (backend={backend})")
    return df


def derive_spoke(df: pd.DataFrame, hubs: list[str]) -> pd.DataFrame:
    hubs_set = set(hubs)
    df = df.copy()
    df["spoke_airport"] = df["dest"].where(df["origin"].isin(hubs_set), df["origin"])
    return df


def aggregate_cells(df: pd.DataFrame, econ_config: dict) -> pd.DataFrame:
    cancel_equiv_min = econ_config["cancellation_equivalent_minutes"]["base"]
    block_cost_per_min = econ_config["airline_block_cost_per_min"]["base"]

    base_agg = (
        df.groupby(CELL_KEYS, dropna=False)
        .agg(
            flights_total=("operated_flag", "size"),
            operated_count=("operated_flag", "sum"),
            cancelled_count=("cancelled_flag", "sum"),
            severe_delay_count=("severe_delay_flag", "sum"),
            controllable_severe_delay_count=("controllable_severe_delay_flag", "sum"),
            late_arriving_severe_delay_count=("late_arriving_severe_delay_flag", "sum"),
            cascade_delay_count=("cascade_delay_flag", "sum"),
            carrier_delay_min_sum=("carrier_delay_minutes", "sum"),
            late_aircraft_delay_min_sum=("late_aircraft_delay_minutes", "sum"),
        )
        .reset_index()
    )

    base_agg["cancellation_rate"] = base_agg["cancelled_count"] / base_agg["flights_total"].clip(lower=1)
    base_agg["severe_delay_rate"] = base_agg["severe_delay_count"] / base_agg["flights_total"].clip(lower=1)
    base_agg["controllable_severe_delay_rate"] = (
        base_agg["controllable_severe_delay_count"] / base_agg["operated_count"].clip(lower=1)
    )
    base_agg["late_arriving_severe_delay_rate"] = (
        base_agg["late_arriving_severe_delay_count"] / base_agg["operated_count"].clip(lower=1)
    )

    # Adverse-weather fragility: computed from adverse-wx rows only
    adverse = df[df["weather_bucket"] == "adverse"]
    if not adverse.empty:
        adv_agg = (
            adverse.groupby(CELL_KEYS, dropna=False)
            .agg(
                adv_flights=("operated_flag", "size"),
                adv_cancelled=("cancelled_flag", "sum"),
                adv_severe_delay=("severe_delay_flag", "sum"),
            )
            .reset_index()
        )
        adv_agg["adverse_weather_fragility_rate"] = (
            (adv_agg["adv_cancelled"] + adv_agg["adv_severe_delay"]) / adv_agg["adv_flights"].clip(lower=1)
        )
        base_agg = base_agg.merge(
            adv_agg[CELL_KEYS + ["adv_flights", "adverse_weather_fragility_rate"]],
            on=CELL_KEYS,
            how="left",
        )
        base_agg["adv_flights"] = base_agg["adv_flights"].fillna(0)
        base_agg["adverse_weather_fragility_rate"] = base_agg["adverse_weather_fragility_rate"].fillna(0.0)
    else:
        base_agg["adv_flights"] = 0
        base_agg["adverse_weather_fragility_rate"] = 0.0

    # Economic burden per 1k flights (absolute cost basis, not excess vs baseline)
    base_agg["economic_burden_per_1k"] = (
        (
            base_agg["cancelled_count"] * cancel_equiv_min * block_cost_per_min
            + (base_agg["carrier_delay_min_sum"] + base_agg["late_aircraft_delay_min_sum"]) * block_cost_per_min
        )
        / base_agg["flights_total"].clip(lower=1)
        * 1000
    )

    log.info(f"Aggregated to {len(base_agg):,} cells across {CELL_KEYS}")
    return base_agg


def normalize_components(agg: pd.DataFrame, min_flights: int) -> pd.DataFrame:
    """Compute percentile-rank normalization of the 6 raw metrics within
    the pool of cells meeting min_flights. Returns agg with norm_ columns
    added; cells below min_flights receive NaN norms."""
    agg = agg.copy()
    included_mask = agg["flights_total"] >= min_flights

    raw_to_norm = {
        "cancellation_rate": "norm_cancel",
        "severe_delay_rate": "norm_severe_delay",
        "controllable_severe_delay_rate": "norm_controllable",
        "late_arriving_severe_delay_rate": "norm_cascade",
        "adverse_weather_fragility_rate": "norm_weather_sensitivity",
        "economic_burden_per_1k": "norm_economic_burden",
    }

    for raw_col, norm_col in raw_to_norm.items():
        pool = agg.loc[included_mask, raw_col]
        ranks = pool.rank(pct=True, method="average")
        agg[norm_col] = np.nan
        agg.loc[included_mask, norm_col] = ranks.values

    n_included = included_mask.sum()
    n_total = len(agg)
    log.info(
        f"Normalization pool: {n_included:,} cells meet min_flights={min_flights} "
        f"(of {n_total:,} total cells)"
    )
    return agg


def compute_hotspot_score(agg: pd.DataFrame, weights: dict, scenario_name: str) -> pd.Series:
    score = pd.Series(np.nan, index=agg.index)
    has_norms = agg[COMPONENT_COLS].notna().all(axis=1)
    score[has_norms] = sum(
        weights[NORM_TO_WEIGHT[col]] * agg.loc[has_norms, col]
        for col in COMPONENT_COLS
    )
    return score


def compute_all_scenarios(agg: pd.DataFrame, scenario_weights: dict) -> pd.DataFrame:
    agg = agg.copy()
    for scenario_name, weights in scenario_weights.items():
        col = f"hotspot_score_{scenario_name}"
        agg[col] = compute_hotspot_score(agg, weights, scenario_name)
        log.info(
            f"Scenario '{scenario_name}': scored {agg[col].notna().sum():,} cells "
            f"(min={agg[col].min():.4f}, max={agg[col].max():.4f})"
        )
    return agg


def compute_robustness(agg: pd.DataFrame, scenario_names: list[str], top_n: int) -> pd.Series:
    """Fraction of scenarios where the cell ranks in the top_n."""
    included_mask = agg[COMPONENT_COLS].notna().all(axis=1)
    robustness = pd.Series(np.nan, index=agg.index)
    if included_mask.sum() == 0:
        return robustness

    in_top_count = pd.Series(0.0, index=agg.index)
    n_scenarios = len(scenario_names)
    for scenario_name in scenario_names:
        col = f"hotspot_score_{scenario_name}"
        # rank descending among included cells; dense to avoid ties shifting boundary
        ranked = agg.loc[included_mask, col].rank(ascending=False, method="min")
        in_top = (ranked <= top_n).astype(float)
        in_top_count.loc[included_mask] += in_top.values

    robustness.loc[included_mask] = in_top_count.loc[included_mask] / n_scenarios
    return robustness


def compute_dominant_component(agg: pd.DataFrame) -> pd.Series:
    """For each cell, the normalized component with the highest value."""
    label_map = {
        "norm_cancel": "cancel",
        "norm_severe_delay": "severe_delay",
        "norm_controllable": "controllable",
        "norm_cascade": "cascade",
        "norm_weather_sensitivity": "weather_sensitivity",
        "norm_economic_burden": "economic_burden",
    }
    has_norms = agg[COMPONENT_COLS].notna().all(axis=1)
    dominant = pd.Series("unknown", index=agg.index)
    if has_norms.any():
        idx_max = agg.loc[has_norms, COMPONENT_COLS].idxmax(axis=1)
        dominant.loc[has_norms] = idx_max.map(label_map)
    return dominant


def compute_period_subscores(
    df: pd.DataFrame,
    econ_config: dict,
    scenario_weights: dict,
    top_n: int,
    min_flights: int,
    period: str,
) -> set:
    """Return the set of (hub_family, spoke_airport, operator_class) tuples
    that rank in the top_n for the given period using base scenario."""
    sub = df[df["period_flag"] == period]
    if sub.empty:
        return set()

    sub_agg = aggregate_cells(sub, econ_config)
    sub_agg = normalize_components(sub_agg, min_flights // 2)
    weights = scenario_weights.get("base", list(scenario_weights.values())[0])
    sub_agg["_sub_score"] = compute_hotspot_score(sub_agg, weights, "base")

    included = sub_agg[sub_agg["_sub_score"].notna()].copy()
    if included.empty:
        return set()

    included = included.sort_values("_sub_score", ascending=False)
    top_cells = included.head(top_n)
    return set(zip(top_cells["hub_family"], top_cells["spoke_airport"], top_cells["operator_class"]))


def compute_persistence(df: pd.DataFrame, agg: pd.DataFrame, econ_config: dict,
                        scenario_weights: dict, top_n: int, min_flights: int) -> pd.Series:
    log.info("Computing persistence (Module E): baseline vs. recent period sub-scores...")
    baseline_top = compute_period_subscores(df, econ_config, scenario_weights, top_n, min_flights, "baseline")
    recent_top = compute_period_subscores(df, econ_config, scenario_weights, top_n, min_flights, "recent")
    persistent = baseline_top & recent_top
    log.info(
        f"  Baseline top-{top_n}: {len(baseline_top)} cells, "
        f"recent top-{top_n}: {len(recent_top)} cells, "
        f"persistent (both): {len(persistent)} cells"
    )

    cell_tuples = list(zip(agg["hub_family"], agg["spoke_airport"], agg["operator_class"]))
    is_persistent = pd.Series(
        [t in persistent for t in cell_tuples],
        index=agg.index,
    )
    return is_persistent


def module_b_operator_rollup(agg_top: pd.DataFrame, exclude_from_rollup: list[str]) -> pd.DataFrame:
    """Operator concentration among top-N cells (resolved operators only)."""
    resolved = agg_top[~agg_top["operator_class"].isin(exclude_from_rollup)].copy()
    if resolved.empty:
        return pd.DataFrame(columns=["operator_class", "hotspot_count", "share_of_top_n", "total_flights_in_top_n"])

    rollup = (
        resolved.groupby("operator_class")
        .agg(
            hotspot_count=("operator_class", "size"),
            total_flights_in_top_n=("flights_total", "sum"),
        )
        .reset_index()
        .sort_values("hotspot_count", ascending=False)
    )
    rollup["share_of_top_n"] = rollup["hotspot_count"] / rollup["hotspot_count"].sum()
    return rollup


def module_c_hub_rollup(agg_top: pd.DataFrame) -> pd.DataFrame:
    """Hub concentration among top-N cells."""
    rollup = (
        agg_top.groupby("hub_family")
        .agg(
            hotspot_count=("hub_family", "size"),
            total_flights_in_top_n=("flights_total", "sum"),
        )
        .reset_index()
        .sort_values("hotspot_count", ascending=False)
    )
    rollup["share_of_top_n"] = rollup["hotspot_count"] / rollup["hotspot_count"].sum()
    return rollup


def build_label(row: pd.Series) -> str:
    label = f"{row['operator_class']} @ {row['hub_family']}-{row['spoke_airport']}"
    if row.get("is_persistent", False):
        label += " (P)"
    return label


def write_markdown_summary(agg: pd.DataFrame, top: pd.DataFrame, op_rollup: pd.DataFrame,
                           hub_rollup: pd.DataFrame, summary: dict, out_path: Path):
    lines = []
    lines.append("# Fragility V: Network Hotspot Scorecard — Prioritization Memo")
    lines.append("")
    lines.append(
        "This memo summarizes which hub-spoke market-operator cells are associated with "
        "the highest composite fragility signal across AA's regional network structure. "
        "Findings reflect observed patterns in BTS on-time performance data; they do not "
        "assert operational causation. All rates are consistent with, not necessarily "
        "caused by, the factors named. See the QA notes section for data-quality caveats."
    )
    lines.append("")

    lines.append("## 1. Top-ranked cells by base hotspot score")
    lines.append("")
    lines.append(
        f"The hotspot engine scores {summary.get('total_cells', 0):,} distinct "
        f"(hub, spoke, operator_class) cells. Of these, "
        f"{summary.get('cells_meeting_min_flights', 0):,} meet the minimum-flights "
        f"threshold ({summary.get('hotspot_min_flights', 100)} flights) required for "
        "normalization and ranking."
    )
    lines.append("")
    if not top.empty:
        lines.append(f"Top-{len(top)} cells by base hotspot score:")
        lines.append("")
        lines.append("| Rank | Cell | Hub | Spoke | Operator | Base Score | Robustness | Persistent |")
        lines.append("|---|---|---|---|---|---|---|---|")
        for rank, (_, row) in enumerate(top.iterrows(), 1):
            persistent = "Yes" if row.get("is_persistent", False) else "No"
            lines.append(
                f"| {rank} | {row['hub_family']}-{row['spoke_airport']} {row['operator_class']} "
                f"| {row['hub_family']} | {row['spoke_airport']} | {row['operator_class']} "
                f"| {row.get('hotspot_score_base', float('nan')):.4f} "
                f"| {row.get('hotspot_robustness_score', float('nan')):.2f} "
                f"| {persistent} |"
            )
    lines.append("")

    lines.append("## 2. Hub concentration in top-N")
    lines.append("")
    if not hub_rollup.empty:
        lines.append("| Hub | Cells in top-N | Share | Total flights |")
        lines.append("|---|---|---|---|")
        for _, row in hub_rollup.iterrows():
            lines.append(
                f"| {row['hub_family']} | {int(row['hotspot_count'])} "
                f"| {row['share_of_top_n']:.1%} | {int(row['total_flights_in_top_n']):,} |"
            )
    lines.append("")

    lines.append("## 3. Operator concentration in top-N (resolved operators only)")
    lines.append("")
    if not op_rollup.empty:
        lines.append("| Operator class | Cells in top-N | Share | Total flights |")
        lines.append("|---|---|---|---|")
        for _, row in op_rollup.iterrows():
            lines.append(
                f"| {row['operator_class']} | {int(row['hotspot_count'])} "
                f"| {row['share_of_top_n']:.1%} | {int(row['total_flights_in_top_n']):,} |"
            )
    lines.append("")

    lines.append("## 4. Dominant fragility signal")
    lines.append("")
    if not top.empty and "dominant_component" in top.columns:
        dom_counts = top["dominant_component"].value_counts()
        lines.append(
            "Among the top-N cells, the highest normalized component per cell is distributed as follows "
            "(a cell's dominant component is the one with the highest percentile rank in that cell):"
        )
        lines.append("")
        for comp, count in dom_counts.items():
            lines.append(f"- **{comp}**: {count} cell(s)")
    lines.append("")

    lines.append("## 5. QA notes")
    lines.append("")
    for note in summary.get("qa_notes", []):
        lines.append(f"- {note}")
    lines.append("")

    lines.append("## 6. Caveats")
    lines.append("")
    lines.append(
        "- The hotspot score is a composite index based on six normalized components. "
        "Equal weights in the base scenario treat all components as equally important; "
        "alternative weighting scenarios test robustness.\n"
        "- Cells with fewer than the minimum-flights threshold are excluded from "
        "normalization and ranking but are retained in the output Parquet for completeness.\n"
        "- SkyWest_unresolved and Republic_unresolved are included in hotspot scoring but "
        "excluded from the operator-concentration rollup (Module B), where ambiguous "
        "attribution would distort the operator-level count.\n"
        "- Other_or_non_AA rows (non-AA carriers sharing BTS reporting at these airports) "
        "are excluded entirely from hotspot computation.\n"
        "- Economic burden is an absolute-cost proxy (not excess vs. a peer baseline) "
        "using published DOT block-cost benchmarks. It is not sourced from airline financials."
    )
    lines.append("")

    out_path.write_text("\n".join(lines))
    log.info(f"Written summary: {out_path}")


def main():
    parser = argparse.ArgumentParser(description="Fragility V: network hotspot engine")
    parser.add_argument("--study", default="config/study.yaml")
    parser.add_argument("--econ-config", default="config/economic_scenarios.yaml")
    parser.add_argument("--run-mode", default=None, help="Override run_mode from study.yaml")
    parser.add_argument("--top-n", type=int, default=None, help="Override hotspot_top_n from study.yaml")
    parser.add_argument("--out-dir", default="output/")
    args = parser.parse_args()

    script_dir = Path(__file__).parent
    root = script_dir.parent
    study_path = root / args.study
    econ_path = root / args.econ_config
    out_dir = root / args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    study = load_yaml(study_path)
    econ_config = load_yaml(econ_path)

    run_mode = args.run_mode or study.get("run_mode", "test")
    log.info(f"Run mode: {run_mode}")

    fv_config = study.get("fragility_v", {})
    top_n = args.top_n or fv_config.get("hotspot_top_n", 20)
    min_flights = fv_config.get("hotspot_min_flights", 100)
    scenario_weights = fv_config.get("hotspot_score_weights", {})
    exclude_from_rollup = fv_config.get("exclude_from_operator_rollup", [])

    hubs_by_mode = study.get("run_mode_hubs", {})
    hubs = hubs_by_mode.get(run_mode, hubs_by_mode.get("local", ["DFW", "CLT", "ORD", "PHL"]))
    if not hubs:
        # bigrun: use all hubs present in the data
        hubs = None

    fact_dir = root / "data/curated/hubspoke_operator_fact"
    if not fact_dir.exists() or not any(fact_dir.rglob("*.parquet")):
        log.error(f"Curated fact table not found at {fact_dir}. Run run_pipeline_iv.sh first.")
        raise SystemExit(1)

    df = load_fact(fact_dir, study)

    # Filter to run-mode hubs if specified
    if hubs:
        before = len(df)
        df = df[df["hub_family"].isin(hubs)]
        log.info(f"Filtered to hubs {hubs}: {len(df):,} rows (from {before:,})")

    # Exclude Other_or_non_AA entirely
    before = len(df)
    df = df[df["operator_class"] != "Other_or_non_AA"]
    log.info(f"Excluded Other_or_non_AA: {len(df):,} rows (removed {before - len(df):,})")

    df = derive_spoke(df, hubs if hubs else list(df["hub_family"].unique()))

    agg = aggregate_cells(df, econ_config)
    agg = normalize_components(agg, min_flights)
    agg = compute_all_scenarios(agg, scenario_weights)

    scenario_names = list(scenario_weights.keys())
    agg["hotspot_robustness_score"] = compute_robustness(agg, scenario_names, top_n)
    agg["dominant_component"] = compute_dominant_component(agg)
    agg["meets_min_flights"] = agg["flights_total"] >= min_flights

    # Module E: persistence
    agg["is_persistent"] = compute_persistence(df, agg, econ_config, scenario_weights, top_n, min_flights)

    # --- Output: full scorecard partitioned by hub_family ---
    scorecard_dir = out_dir / "fragility_v_hotspot_scorecard.parquet"
    write_partitioned_parquet(agg, scorecard_dir, ["hub_family"])
    log.info(f"Scorecard parquet written: {scorecard_dir}")

    # --- Top-N rankings by base score ---
    included = agg[agg["meets_min_flights"]].copy()
    base_score_col = "hotspot_score_base"
    if base_score_col not in included.columns:
        base_score_col = f"hotspot_score_{scenario_names[0]}"

    top = (
        included.dropna(subset=[base_score_col])
        .sort_values(base_score_col, ascending=False)
        .head(top_n)
        .reset_index(drop=True)
    )
    log.info(f"Top-{top_n} cells by {base_score_col}:")
    for i, row in top.iterrows():
        log.info(
            f"  #{i+1:2d}: {row['hub_family']}-{row['spoke_airport']} {row['operator_class']} "
            f"score={row[base_score_col]:.4f} robustness={row.get('hotspot_robustness_score', float('nan')):.2f} "
            f"persistent={row.get('is_persistent', False)}"
        )

    rankings_path = out_dir / "fragility_v_hotspot_rankings.csv"
    top.to_csv(rankings_path, index=False)
    log.info(f"Rankings CSV written: {rankings_path} ({len(top)} rows)")

    # --- Module B: operator rollup ---
    op_rollup = module_b_operator_rollup(top, exclude_from_rollup)
    op_rollup_path = out_dir / "fragility_v_operator_rollup.csv"
    op_rollup.to_csv(op_rollup_path, index=False)
    log.info(f"Operator rollup written: {op_rollup_path}")
    log.info(f"  Operator concentration in top-{top_n}: {op_rollup.to_dict('records')}")

    # --- Module C: hub rollup ---
    hub_rollup = module_c_hub_rollup(top)
    hub_rollup_path = out_dir / "fragility_v_hub_rollup.csv"
    hub_rollup.to_csv(hub_rollup_path, index=False)
    log.info(f"Hub rollup written: {hub_rollup_path}")
    log.info(f"  Hub concentration in top-{top_n}: {hub_rollup.to_dict('records')}")

    # --- Scenario robustness CSV ---
    robustness_cols = CELL_KEYS + ["flights_total", "meets_min_flights", "hotspot_robustness_score"] + [
        f"hotspot_score_{s}" for s in scenario_names
    ] + COMPONENT_COLS
    existing_cols = [c for c in robustness_cols if c in included.columns]
    robustness_path = out_dir / "fragility_v_scenario_robustness.csv"
    included[existing_cols].to_csv(robustness_path, index=False)
    log.info(f"Scenario robustness CSV written: {robustness_path} ({len(included):,} rows)")

    # --- Summary JSON ---
    top_cell = top.iloc[0].to_dict() if not top.empty else None
    n_persistent = int(top["is_persistent"].sum()) if not top.empty else 0

    dominant_in_top = top["dominant_component"].value_counts().to_dict() if not top.empty else {}

    # Annotation
    if top_cell:
        annotation = (
            f"The highest-scoring cell (base scenario) is "
            f"{top_cell['hub_family']}-{top_cell['spoke_airport']} operated by "
            f"{top_cell['operator_class']}, with a base hotspot score of "
            f"{top_cell.get('hotspot_score_base', float('nan')):.4f} across "
            f"{int(top_cell.get('flights_total', 0)):,} flights."
        )
    else:
        annotation = "Insufficient data for ranking annotation."

    qa_notes = [
        f"Total cells: {len(agg):,}; cells meeting min_flights={min_flights}: {included.shape[0]:,}.",
        f"Operator classes included in scoring: {sorted(df['operator_class'].unique())}.",
        f"Hubs in scope: {sorted(df['hub_family'].unique())}.",
        f"Spoke airports in scope: {df['spoke_airport'].nunique()} distinct airports.",
        f"Persistent cells (top-{top_n} in both baseline and recent periods): {n_persistent}.",
        f"Scenario names: {scenario_names}.",
        f"Dominant component distribution in top-{top_n}: {dominant_in_top}.",
        f"Operator rollup (resolved operators only, top-{top_n}): {op_rollup.to_dict('records')}.",
        f"Hub rollup (top-{top_n}): {hub_rollup.to_dict('records')}.",
    ]

    summary = {
        "run_mode": run_mode,
        "hubs_in_scope": sorted(df["hub_family"].unique()),
        "top_n": top_n,
        "hotspot_min_flights": min_flights,
        "total_cells": len(agg),
        "cells_meeting_min_flights": int(included.shape[0]),
        "scenario_names": scenario_names,
        "annotation": annotation,
        "top_cell": top_cell,
        "n_persistent_in_top_n": n_persistent,
        "dominant_component_distribution": dominant_in_top,
        "operator_rollup": op_rollup.to_dict("records"),
        "hub_rollup": hub_rollup.to_dict("records"),
        "qa_notes": qa_notes,
    }
    summary_json_path = out_dir / "fragility_v_summary.json"
    with open(summary_json_path, "w") as f:
        json.dump(summary, f, indent=2, default=str)
    log.info(f"Summary JSON written: {summary_json_path}")

    # --- Summary MD ---
    summary_md_path = out_dir / "fragility_v_summary.md"
    write_markdown_summary(agg, top, op_rollup, hub_rollup, summary, summary_md_path)

    log.info("=== Fragility V Hotspot Engine QA ===")
    for note in qa_notes:
        log.info(f"  - {note}")
    log.info(f"  Annotation: {annotation}")
    log.info("Fragility V analysis complete.")


if __name__ == "__main__":
    main()
