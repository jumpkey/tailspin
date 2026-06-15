#!/usr/bin/env python3
"""
20_build_flight_fact.py — Integrate BTS and FAA staging data into a single curated flight fact table.

Steps
-----
1. Load and standardize BTS and FAA staging files.
2. Assign market baskets (AA regional, UA peer, DL peer) to each flight.
3. Join FAA cancelled-flight-weather records onto BTS records by
   flight_date / carrier_code / flight_number / origin / dest /
   sched_dep within ±15 min.
4. Derive weather_bucket, severe_delay_flag, operated_flag, period_flag.
5. Write curated fact table and QA summary.

Outputs
-------
data/curated/flight_operability_fact.csv
output/qa_summary.csv

Usage
-----
python scripts/20_build_flight_fact.py \\
    --routes config/routes.yaml \\
    --study  config/study.yaml
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

# ---------------------------------------------------------------------------
# Weather-bucket derivation
# ---------------------------------------------------------------------------
# Primary approach: FAA ASPM severity levels (None, Minor, Moderate, Severe)
#   benign   — both endpoints ≤ Minor
#   marginal — one endpoint is Moderate
#   adverse  — one/both endpoints are Severe OR both are ≥ Moderate
#
# Fallback (raw text descriptors):
#   adverse  — fog, thunderstorm, very low vis/ceiling
#   marginal — rain, mist, reduced vis/ceiling
#   benign   — otherwise

ASPM_RANK = {"None": 0, "Minor": 1, "Moderate": 2, "Severe": 3}

ADVERSE_KEYWORDS = frozenset(
    ["fog", "ts", "thunderstorm", "fzra", "blizzard", "heavy snow", "+sn"]
)
MARGINAL_KEYWORDS = frozenset(
    ["ra", "rain", "mist", "br", "-ra", "sn", "snow", "drizzle", "dz"]
)


def _aspm_bucket(dep_level: str | None, arr_level: str | None) -> str:
    """Derive weather bucket from FAA ASPM severity strings."""
    d = ASPM_RANK.get(str(dep_level).strip().title(), -1)
    a = ASPM_RANK.get(str(arr_level).strip().title(), -1)
    if d == -1 and a == -1:
        return "unknown"
    d = max(d, 0)
    a = max(a, 0)
    hi = max(d, a)
    lo = min(d, a)
    if hi >= 3:  # one is Severe
        return "adverse"
    if hi == 2 and lo == 2:  # both Moderate
        return "adverse"
    if hi == 2:  # one Moderate
        return "marginal"
    return "benign"  # both ≤ Minor


def _text_bucket(dep_wx: str | None, arr_wx: str | None) -> str:
    """Derive weather bucket from raw weather-condition strings."""
    text = f"{dep_wx or ''} {arr_wx or ''}".lower()
    if any(k in text for k in ADVERSE_KEYWORDS):
        return "adverse"
    if any(k in text for k in MARGINAL_KEYWORDS):
        return "marginal"
    return "benign"


def derive_weather_bucket(row: pd.Series) -> str:
    """
    Use FAA ASPM levels when available; fall back to raw weather text.
    ASPM levels are expected in columns faa_dep_ceiling / faa_arr_ceiling
    (which may carry ASPM verbal severity if sourced from the Weather Factors
    report), otherwise use dep_local_weather / arr_local_weather text.
    """
    # Try ASPM level columns if present
    dep_lvl = row.get("faa_dep_aspm_level") or row.get("faa_dep_ceiling")
    arr_lvl = row.get("faa_arr_aspm_level") or row.get("faa_arr_ceiling")

    if pd.notna(dep_lvl) or pd.notna(arr_lvl):
        bucket = _aspm_bucket(dep_lvl, arr_lvl)
        if bucket != "unknown":
            return bucket

    # Fallback to raw text
    return _text_bucket(
        row.get("faa_dep_local_weather"),
        row.get("faa_arr_local_weather"),
    )


def load_config(routes_path: Path, study_path: Path):
    with open(routes_path) as f:
        routes = yaml.safe_load(f)
    with open(study_path) as f:
        study = yaml.safe_load(f)
    return routes, study


def build_basket_lookup(routes: dict) -> dict[tuple, str]:
    """
    Return a mapping (origin, dest, carrier_prefix) → basket_name.
    We use the hub destination to infer which basket a flight belongs to.
    """
    lookup: dict[tuple, str] = {}
    basket_carrier = {
        "aa_regional_basket": "AA",
        "ua_peer_basket": "UA",
        "dl_peer_basket": "DL",
    }
    for basket_name, carrier in basket_carrier.items():
        legs = routes.get(basket_name, [])
        for leg in legs:
            lookup[(leg["origin"], leg["dest"])] = basket_name
    return lookup


def assign_basket(row: pd.Series, basket_lookup: dict[tuple, str]) -> str:
    return basket_lookup.get((row["origin"], row["dest"]), "other")


def assign_carrier_group(basket: str) -> str:
    if basket == "aa_regional_basket":
        return "AA_regional"
    if basket == "ua_peer_basket":
        return "UA_peer"
    if basket == "dl_peer_basket":
        return "DL_peer"
    return "other"


def load_bts(path: Path) -> pd.DataFrame:
    log.info(f"Loading BTS staging: {path}")
    df = pd.read_csv(path, dtype=str)
    if "flight_date" in df.columns:
        df["flight_date"] = pd.to_datetime(df["flight_date"], errors="coerce")
    for col in ("dep_delay_min", "arr_delay_min", "distance_miles",
                "actual_elapsed_min", "scheduled_elapsed_min"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    for col in ("cancelled_flag", "diverted_flag"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
    for col in ("sched_dep_local", "sched_arr_local"):
        if col in df.columns:
            df[col] = df[col].astype(str).str.zfill(4)
    log.info(f"  BTS rows: {len(df):,}")
    return df


def load_faa(path: Path) -> pd.DataFrame:
    log.info(f"Loading FAA staging: {path}")
    if not path.exists():
        log.warning("  FAA staging file not found — proceeding without weather join.")
        return pd.DataFrame()
    df = pd.read_csv(path, dtype=str)
    if "scheduled_departure_date" in df.columns:
        df["scheduled_departure_date"] = pd.to_datetime(
            df["scheduled_departure_date"], errors="coerce"
        )
    if "scheduled_departure_time" in df.columns:
        df["scheduled_departure_time"] = df["scheduled_departure_time"].astype(str).str.zfill(4)
    log.info(f"  FAA rows: {len(df):,}")
    return df


def join_faa_weather(bts: pd.DataFrame, faa: pd.DataFrame, tolerance_min: int = 15) -> pd.DataFrame:
    """
    Left-join FAA weather records onto BTS cancelled flights.

    Join keys: flight_date, carrier_code, flight_number, origin, dest
    Time tolerance: scheduled departure within ±tolerance_min minutes.
    """
    if faa.empty:
        # Add empty FAA columns
        for col in (
            "faa_dep_wind", "faa_dep_ceiling", "faa_dep_visibility",
            "faa_dep_nearby_ts", "faa_dep_local_weather",
            "faa_arr_wind", "faa_arr_ceiling", "faa_arr_visibility",
            "faa_arr_nearby_ts", "faa_arr_local_weather",
        ):
            bts[col] = np.nan
        return bts

    # Prepare FAA side — rename to avoid collision
    faa_join = faa.rename(columns={
        "scheduled_departure_date": "faa_date",
        "carrier_code": "faa_carrier",
        "flight_number": "faa_fnum",
        "departure_airport": "faa_origin",
        "arrival_airport": "faa_dest",
        "scheduled_departure_time": "faa_sched_dep",
        "dep_wind": "faa_dep_wind",
        "dep_ceiling": "faa_dep_ceiling",
        "dep_visibility": "faa_dep_visibility",
        "dep_nearby_ts": "faa_dep_nearby_ts",
        "dep_local_weather": "faa_dep_local_weather",
        "arr_wind": "faa_arr_wind",
        "arr_ceiling": "faa_arr_ceiling",
        "arr_visibility": "faa_arr_visibility",
        "arr_nearby_ts": "faa_arr_nearby_ts",
        "arr_local_weather": "faa_arr_local_weather",
    })

    # Convert times to minutes-since-midnight for tolerance join
    def to_minutes(t: pd.Series) -> pd.Series:
        t_str = t.astype(str).str.zfill(4)
        h = pd.to_numeric(t_str.str[:2], errors="coerce")
        m = pd.to_numeric(t_str.str[2:4], errors="coerce")
        return h * 60 + m

    bts = bts.copy()
    bts["_dep_min"] = to_minutes(bts.get("sched_dep_local", pd.Series(dtype=str)))
    faa_join["_faa_dep_min"] = to_minutes(faa_join.get("faa_sched_dep", pd.Series(dtype=str)))

    # Merge on date + carrier + flight number + origin + dest
    merged = bts.merge(
        faa_join,
        left_on=["flight_date", "carrier_code", "flight_number", "origin", "dest"],
        right_on=["faa_date", "faa_carrier", "faa_fnum", "faa_origin", "faa_dest"],
        how="left",
    )

    # Apply time tolerance: drop matches that are outside the window
    dep_diff = (merged["_dep_min"] - merged["_faa_dep_min"]).abs()
    bad_time = dep_diff > tolerance_min
    faa_weather_cols = [c for c in merged.columns if c.startswith("faa_") and c not in
                        ("faa_date", "faa_carrier", "faa_fnum", "faa_origin", "faa_dest", "faa_sched_dep", "_faa_dep_min")]
    merged.loc[bad_time, faa_weather_cols] = np.nan

    # Drop helper columns
    drop_cols = [c for c in ("_dep_min", "_faa_dep_min", "faa_date", "faa_carrier",
                              "faa_fnum", "faa_origin", "faa_dest", "faa_sched_dep")
                 if c in merged.columns]
    merged = merged.drop(columns=drop_cols)

    # Deduplicate (one BTS row may match multiple FAA rows — keep first)
    key_cols = [c for c in ("flight_date", "carrier_code", "flight_number", "origin", "dest")
                if c in merged.columns]
    merged = merged.drop_duplicates(subset=key_cols, keep="first")

    join_count = merged[faa_weather_cols[0]].notna().sum() if faa_weather_cols else 0
    cancel_count = (merged.get("cancelled_flag", pd.Series(0)) == 1).sum()
    log.info(
        f"  FAA join: {join_count:,} / {cancel_count:,} cancelled flights matched "
        f"({join_count / max(cancel_count, 1):.1%} match rate)"
    )
    return merged


def derive_flags(df: pd.DataFrame, study: dict) -> pd.DataFrame:
    """Derive weather_bucket, severe_delay_flag, operated_flag, period_flag, year_month, route_key."""
    delay_thresh = study.get("delay_threshold_minutes", 60)
    baseline_end = pd.to_datetime(study["baseline_end"])

    df = df.copy()

    # weather_bucket
    df["weather_bucket"] = df.apply(derive_weather_bucket, axis=1)

    # severe_delay_flag: operated flight with arrival delay ≥ threshold
    df["severe_delay_flag"] = (
        (df.get("arr_delay_min", pd.Series(np.nan)) >= delay_thresh) &
        (df.get("cancelled_flag", pd.Series(0)) == 0)
    ).astype(int)

    # operated_flag
    df["operated_flag"] = (
        (df.get("cancelled_flag", pd.Series(0)) == 0) &
        (df.get("diverted_flag", pd.Series(0)) == 0)
    ).astype(int)

    # period_flag: baseline vs recent
    df["period_flag"] = np.where(
        df["flight_date"] <= baseline_end, "baseline", "recent"
    )

    # year_month
    df["year_month"] = df["flight_date"].dt.to_period("M").astype(str)

    # route_key
    df["route_key"] = df["origin"].str.strip() + "-" + df["dest"].str.strip()

    return df


def main():
    parser = argparse.ArgumentParser(description="Build integrated flight fact table")
    parser.add_argument("--routes", default="config/routes.yaml")
    parser.add_argument("--study", default="config/study.yaml")
    parser.add_argument("--bts", default="data/staging/bts_flights.csv")
    parser.add_argument("--faa", default="data/staging/faa_cancel_weather.csv")
    parser.add_argument("--fa", default="data/staging/flightaware_history.csv")
    parser.add_argument("--out", default="data/curated/flight_operability_fact.csv")
    parser.add_argument("--qa-out", default="output/qa_summary.csv")
    args = parser.parse_args()

    script_dir = Path(__file__).parent
    root = script_dir.parent
    routes_path = root / args.routes
    study_path = root / args.study
    bts_path = root / args.bts
    faa_path = root / args.faa
    out_path = root / args.out
    qa_path = root / args.qa_out

    out_path.parent.mkdir(parents=True, exist_ok=True)
    qa_path.parent.mkdir(parents=True, exist_ok=True)

    routes, study = load_config(routes_path, study_path)
    basket_lookup = build_basket_lookup(routes)

    bts = load_bts(bts_path)
    faa = load_faa(faa_path)

    # Filter BTS to our route universe
    known_routes = set(basket_lookup.keys())
    bts = bts[bts.apply(lambda r: (r.get("origin"), r.get("dest")) in known_routes, axis=1)].copy()
    log.info(f"BTS after route filter: {len(bts):,} rows")

    # Assign baskets
    bts["market_bucket"] = bts.apply(lambda r: assign_basket(r, basket_lookup), axis=1)
    bts["carrier_group"] = bts["market_bucket"].map(assign_carrier_group)

    # Join FAA weather
    fact = join_faa_weather(bts, faa)

    # Derive flags
    fact = derive_flags(fact, study)

    # Enforce required column order (pad any missing)
    required_cols = [
        "flight_date", "year_month", "carrier_group", "carrier_code", "operating_carrier",
        "flight_number", "origin", "dest", "route_key", "sched_dep_local", "sched_arr_local",
        "dep_delay_min", "arr_delay_min", "cancelled_flag", "diverted_flag", "distance_miles",
        "cancellation_code_bts", "faa_dep_wind", "faa_dep_ceiling", "faa_dep_visibility",
        "faa_dep_nearby_ts", "faa_dep_local_weather", "faa_arr_wind", "faa_arr_ceiling",
        "faa_arr_visibility", "faa_arr_nearby_ts", "faa_arr_local_weather", "weather_bucket",
        "market_bucket", "period_flag", "severe_delay_flag", "operated_flag",
    ]
    for col in required_cols:
        if col not in fact.columns:
            fact[col] = np.nan
    fact = fact[required_cols + [c for c in fact.columns if c not in required_cols]]

    fact.to_csv(out_path, index=False)
    log.info(f"Fact table written: {out_path}  ({len(fact):,} rows)")

    # -------------------------------------------------------------------
    # QA summary
    # -------------------------------------------------------------------
    qa_rows = []

    # Row counts by month
    if "year_month" in fact.columns and "flight_date" in fact.columns:
        month_counts = fact.groupby("year_month").size().reset_index(name="row_count")
        month_counts["check"] = "bts_rows_by_month"
        qa_rows.append(month_counts.rename(columns={"year_month": "dimension"}))

    # Row counts by route pair (FAA)
    if not faa.empty and "departure_airport" in faa.columns:
        faa_counts = (
            faa.groupby(["departure_airport", "arrival_airport"]).size()
            .reset_index(name="row_count")
        )
        faa_counts["dimension"] = faa_counts["departure_airport"] + "-" + faa_counts["arrival_airport"]
        faa_counts["check"] = "faa_rows_by_route"
        qa_rows.append(faa_counts[["dimension", "row_count", "check"]])

    # FAA join rate
    cancel_total = (fact.get("cancelled_flag", pd.Series(0)) == 1).sum()
    faa_matched = (
        fact.get("faa_dep_local_weather", pd.Series(dtype=str)).notna().sum()
        if "faa_dep_local_weather" in fact.columns else 0
    )
    qa_rows.append(pd.DataFrame([{
        "dimension": "cancelled_flights",
        "row_count": cancel_total,
        "check": "faa_join_total_cancelled",
    }, {
        "dimension": "faa_matched",
        "row_count": faa_matched,
        "check": "faa_join_matched",
    }, {
        "dimension": "faa_join_rate",
        "row_count": round(faa_matched / max(cancel_total, 1), 4),
        "check": "faa_join_rate",
    }]))

    # Null rate on weather_bucket
    wb_null = fact["weather_bucket"].isna().mean() if "weather_bucket" in fact.columns else 1.0
    qa_rows.append(pd.DataFrame([{
        "dimension": "weather_bucket",
        "row_count": round(wb_null, 4),
        "check": "null_rate",
    }]))

    # Sample size by market_bucket × weather_bucket × period_flag
    if all(c in fact.columns for c in ("market_bucket", "weather_bucket", "period_flag")):
        sample_sz = (
            fact.groupby(["market_bucket", "weather_bucket", "period_flag"])
            .size().reset_index(name="row_count")
        )
        sample_sz["dimension"] = (
            sample_sz["market_bucket"] + "/" + sample_sz["weather_bucket"] + "/" + sample_sz["period_flag"]
        )
        sample_sz["check"] = "sample_size_by_bucket"
        qa_rows.append(sample_sz[["dimension", "row_count", "check"]])

    qa_df = pd.concat(qa_rows, ignore_index=True) if qa_rows else pd.DataFrame()
    qa_df.to_csv(qa_path, index=False)
    log.info(f"QA summary written: {qa_path}")

    # Console summary
    log.info("=== Fact Table QA ===")
    log.info(f"  Total rows: {len(fact):,}")
    if "market_bucket" in fact.columns:
        log.info(f"  Market buckets: {fact['market_bucket'].value_counts().to_dict()}")
    if "weather_bucket" in fact.columns:
        log.info(f"  Weather buckets: {fact['weather_bucket'].value_counts().to_dict()}")
    log.info(f"  FAA join rate: {faa_matched}/{cancel_total} = {faa_matched/max(cancel_total,1):.1%}")


if __name__ == "__main__":
    main()
