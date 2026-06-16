#!/usr/bin/env python3
"""
20_build_flight_fact.py — Integrate BTS and NOAA weather into a flight fact table.

Steps
-----
1. Load and standardize BTS and NOAA hourly weather staging files.
2. Assign market baskets (AA regional, UA peer, DL peer) to each flight.
3. Convert each BTS flight's scheduled departure and arrival local times to UTC.
4. Join NOAA hourly weather onto BTS by (airport, UTC date, UTC hour):
   - Departure weather  : origin airport + departure UTC hour
   - Arrival weather    : dest airport   + arrival UTC hour
5. Derive weather_bucket = worst of departure + arrival conditions.
6. Derive severe_delay_flag, operated_flag, period_flag.
7. Write curated fact table and QA summary.

WHY THIS REPLACES THE ORIGINAL JOIN LOGIC
------------------------------------------
The original join matched FAA ASPM (cancelled-flights-only) records to BTS by
flight number. Because FAA data only covers cancellations, all operated
(non-cancelled) flights received null weather columns and fell through to the
text-keyword fallback, which returned "benign" for null inputs. This forced
every operated flight into the benign bucket, making adverse/marginal buckets
contain only cancelled flights — a cancellation_rate of ≈ 1.0 by construction
and useless for cross-carrier comparison.

The NOAA ASOS approach assigns weather to every flight at its actual departure
and arrival airport-hours, giving the analysis meaningful denominators (all
scheduled flights during adverse/marginal conditions, not just the cancelled ones).

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
from datetime import datetime, date, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

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
# Airport timezone mapping (same as 11_extract_faa_weather.py)
# ---------------------------------------------------------------------------
AIRPORT_TZ_NAMES = {
    "LFT": "America/Chicago",
    "BTR": "America/Chicago",
    "AEX": "America/Chicago",
    "MLU": "America/Chicago",
    "GPT": "America/Chicago",
    "SHV": "America/Chicago",
    "DFW": "America/Chicago",
    "IAH": "America/Chicago",
    "ATL": "America/New_York",
}

# Pre-load ZoneInfo objects (one per unique timezone)
_TZ_CACHE: dict[str, ZoneInfo] = {}

def _get_tz(tz_name: str) -> ZoneInfo:
    if tz_name not in _TZ_CACHE:
        try:
            _TZ_CACHE[tz_name] = ZoneInfo(tz_name)
        except ZoneInfoNotFoundError:
            _TZ_CACHE[tz_name] = ZoneInfo("America/Chicago")
    return _TZ_CACHE[tz_name]

UTC = ZoneInfo("UTC")

# ---------------------------------------------------------------------------
# Weather bucket severity ordering
# ---------------------------------------------------------------------------
BUCKET_RANK = {"adverse": 2, "marginal": 1, "benign": 0, "unknown": -1}
RANK_BUCKET = {v: k for k, v in BUCKET_RANK.items()}


def _worst_bucket(b1: str, b2: str) -> str:
    r1 = BUCKET_RANK.get(b1, -1)
    r2 = BUCKET_RANK.get(b2, -1)
    worst_rank = max(r1, r2)
    return RANK_BUCKET.get(worst_rank, "benign")


# ---------------------------------------------------------------------------
# Local HHMM → UTC conversion
# ---------------------------------------------------------------------------

def _hhmm_to_utc(flight_date: date, hhmm_str: str, airport: str) -> tuple[date, int]:
    """
    Convert a BTS HHMM local time + flight_date to a (UTC date, UTC hour) pair.

    BTS reports scheduled times in local airport time without a DST flag.
    We use Python's zoneinfo module which handles DST transitions correctly.
    Returns (utc_date, utc_hour).
    """
    try:
        hhmm = str(hhmm_str).strip().zfill(4)
        h = int(hhmm[:2])
        m = int(hhmm[2:4])
        # Handle BTS "2400" (midnight of next day)
        if h == 24:
            h = 0
            flight_date = flight_date + timedelta(days=1)
        h = min(h, 23)  # clamp any other out-of-range values
        tz_name = AIRPORT_TZ_NAMES.get(airport, "America/Chicago")
        tz = _get_tz(tz_name)
        local_dt = datetime(flight_date.year, flight_date.month, flight_date.day, h, m, tzinfo=tz)
        utc_dt = local_dt.astimezone(UTC)
        return utc_dt.date(), utc_dt.hour
    except Exception:
        return flight_date, int(str(hhmm_str).strip().zfill(4)[:2]) if hhmm_str else 0


# ---------------------------------------------------------------------------
# Config and data loaders
# ---------------------------------------------------------------------------

def load_config(routes_path: Path, study_path: Path):
    with open(routes_path) as f:
        routes = yaml.safe_load(f)
    with open(study_path) as f:
        study = yaml.safe_load(f)
    return routes, study


def build_basket_lookup(routes: dict) -> dict[tuple, str]:
    lookup: dict[tuple, str] = {}
    for basket_name in ("aa_regional_basket", "ua_peer_basket", "dl_peer_basket"):
        for leg in routes.get(basket_name, []):
            lookup[(leg["origin"], leg["dest"])] = basket_name
    return lookup


def assign_basket(row: pd.Series, basket_lookup: dict[tuple, str]) -> str:
    return basket_lookup.get((row["origin"], row["dest"]), "other")


def assign_carrier_group(basket: str) -> str:
    return {"aa_regional_basket": "AA_regional",
            "ua_peer_basket": "UA_peer",
            "dl_peer_basket": "DL_peer"}.get(basket, "other")


def load_bts(path: Path) -> pd.DataFrame:
    log.info(f"Loading BTS staging: {path}")
    df = pd.read_csv(path, dtype=str)
    if "flight_date" in df.columns:
        df["flight_date"] = pd.to_datetime(df["flight_date"], errors="coerce")
    for col in ("dep_delay_min", "arr_delay_min", "distance_miles",
                "actual_elapsed_min", "scheduled_elapsed_min",
                "carrier_delay_minutes", "weather_delay_minutes", "nas_delay_minutes",
                "security_delay_minutes", "late_aircraft_delay_minutes"):
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


def load_weather(path: Path) -> pd.DataFrame:
    """Load the NOAA ASOS hourly staging produced by 11_extract_faa_weather.py."""
    log.info(f"Loading NOAA weather staging: {path}")
    if not path.exists():
        log.warning("  Weather staging file not found — all flights will get 'benign' bucket.")
        return pd.DataFrame()
    df = pd.read_csv(path, dtype=str)
    df["obs_hour_utc"] = pd.to_numeric(df["obs_hour_utc"], errors="coerce").astype("Int64")
    for col in ("visibility_sm", "ceiling_ft", "wind_kt"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    log.info(f"  Weather rows: {len(df):,}")
    return df


# ---------------------------------------------------------------------------
# Weather join: BTS flight → NOAA airport-hour
# ---------------------------------------------------------------------------

def _add_utc_keys(bts: pd.DataFrame) -> pd.DataFrame:
    """
    Vectorized conversion of BTS local scheduled times to (UTC date, UTC hour).
    Adds columns:
        dep_utc_date, dep_utc_hour, arr_utc_date, arr_utc_hour
    """
    log.info("  Converting BTS local times to UTC ...")
    dep_dates, dep_hours = [], []
    arr_dates, arr_hours = [], []

    for _, row in bts.iterrows():
        fd = row["flight_date"].date() if pd.notna(row["flight_date"]) else date.today()
        origin = str(row.get("origin", "")).strip().upper()
        dest = str(row.get("dest", "")).strip().upper()

        d_date, d_hour = _hhmm_to_utc(fd, row.get("sched_dep_local", "0000"), origin)
        dep_dates.append(str(d_date))
        dep_hours.append(d_hour)

        # For arrival, add scheduled elapsed minutes to departure UTC datetime
        elapsed = row.get("scheduled_elapsed_min")
        try:
            elapsed = float(elapsed)
        except (TypeError, ValueError):
            elapsed = None

        if elapsed is not None and elapsed > 0:
            dep_tz = _get_tz(AIRPORT_TZ_NAMES.get(origin, "America/Chicago"))
            hhmm = str(row.get("sched_dep_local", "0000")).strip().zfill(4)
            h = min(int(hhmm[:2]), 23)
            m = int(hhmm[2:4]) if hhmm[2:4].isdigit() else 0
            try:
                local_dep = datetime(fd.year, fd.month, fd.day, h, m, tzinfo=dep_tz)
                from datetime import timedelta as _td
                utc_arr = local_dep.astimezone(UTC) + _td(minutes=elapsed)
                arr_dates.append(str(utc_arr.date()))
                arr_hours.append(utc_arr.hour)
            except Exception:
                arr_dates.append(str(d_date))
                arr_hours.append((d_hour + 2) % 24)
        else:
            # Fall back: use arrival local time
            a_date, a_hour = _hhmm_to_utc(fd, row.get("sched_arr_local", "0000"), dest)
            # If arrival appears before departure, assume next-day arrival
            if (a_date, a_hour) < (d_date, d_hour):
                from datetime import timedelta as _td
                a_date = (datetime.combine(a_date, datetime.min.time()) + _td(days=1)).date()
            arr_dates.append(str(a_date))
            arr_hours.append(a_hour)

    bts = bts.copy()
    bts["dep_utc_date"] = dep_dates
    bts["dep_utc_hour"] = dep_hours
    bts["arr_utc_date"] = arr_dates
    bts["arr_utc_hour"] = arr_hours
    return bts


def join_weather(bts: pd.DataFrame, wx: pd.DataFrame) -> pd.DataFrame:
    """
    Left-join NOAA hourly weather onto BTS flights.

    For each flight we look up:
      1. Departure weather: origin airport, dep_utc_date, dep_utc_hour
      2. Arrival weather:   dest airport, arr_utc_date, arr_utc_hour
    Then combine to a single flight weather_bucket (worst of two).
    """
    if wx.empty:
        log.warning("  No weather data — all flights assigned 'benign' bucket.")
        for col in ("wx_dep_visibility", "wx_dep_ceiling", "wx_dep_wxcodes",
                    "wx_dep_wind_kt", "wx_dep_bucket",
                    "wx_arr_visibility", "wx_arr_ceiling", "wx_arr_wxcodes",
                    "wx_arr_wind_kt", "wx_arr_bucket"):
            bts[col] = np.nan
        bts["weather_bucket"] = "benign"
        return bts

    # Build lookup dict: (airport, date_str, hour_int) → row
    wx_dep = wx[["airport_code", "obs_date_utc", "obs_hour_utc",
                 "visibility_sm", "ceiling_ft", "wxcodes", "wind_kt", "weather_bucket"]].copy()
    wx_dep.columns = ["airport_code", "obs_date_utc", "obs_hour_utc",
                      "wx_dep_visibility", "wx_dep_ceiling", "wx_dep_wxcodes",
                      "wx_dep_wind_kt", "wx_dep_bucket"]

    wx_arr = wx[["airport_code", "obs_date_utc", "obs_hour_utc",
                 "visibility_sm", "ceiling_ft", "wxcodes", "wind_kt", "weather_bucket"]].copy()
    wx_arr.columns = ["airport_code", "obs_date_utc", "obs_hour_utc",
                      "wx_arr_visibility", "wx_arr_ceiling", "wx_arr_wxcodes",
                      "wx_arr_wind_kt", "wx_arr_bucket"]

    bts = bts.copy()
    bts["dep_utc_hour"] = bts["dep_utc_hour"].astype("Int64")
    bts["arr_utc_hour"] = bts["arr_utc_hour"].astype("Int64")

    # Merge departure weather
    merged = bts.merge(
        wx_dep,
        left_on=["origin", "dep_utc_date", "dep_utc_hour"],
        right_on=["airport_code", "obs_date_utc", "obs_hour_utc"],
        how="left",
    ).drop(columns=["airport_code", "obs_date_utc", "obs_hour_utc"], errors="ignore")

    # Merge arrival weather
    merged = merged.merge(
        wx_arr,
        left_on=["dest", "arr_utc_date", "arr_utc_hour"],
        right_on=["airport_code", "obs_date_utc", "obs_hour_utc"],
        how="left",
    ).drop(columns=["airport_code", "obs_date_utc", "obs_hour_utc"], errors="ignore")

    # Combine departure + arrival into flight-level weather bucket
    merged["weather_bucket"] = merged.apply(
        lambda r: _worst_bucket(
            r.get("wx_dep_bucket") or "benign",
            r.get("wx_arr_bucket") or "benign",
        ),
        axis=1,
    )

    dep_matched = merged["wx_dep_bucket"].notna().sum()
    arr_matched = merged["wx_arr_bucket"].notna().sum()
    total = len(merged)
    log.info(f"  Departure weather matched: {dep_matched:,}/{total:,} ({dep_matched/total:.1%})")
    log.info(f"  Arrival weather matched:   {arr_matched:,}/{total:,} ({arr_matched/total:.1%})")

    return merged


# ---------------------------------------------------------------------------
# Analytic flag derivation
# ---------------------------------------------------------------------------

def derive_flags(df: pd.DataFrame, study: dict) -> pd.DataFrame:
    """Derive severe_delay_flag, operated_flag, period_flag, year_month, route_key."""
    delay_thresh = study.get("delay_threshold_minutes", 60)
    baseline_end = pd.to_datetime(study["baseline_end"])

    df = df.copy()

    # severe_delay_flag: operated and arrived ≥ threshold late
    df["severe_delay_flag"] = (
        (df.get("arr_delay_min", pd.Series(np.nan)) >= delay_thresh) &
        (df.get("cancelled_flag", pd.Series(0)) == 0)
    ).astype(int)

    # operated_flag: not cancelled and not diverted
    df["operated_flag"] = (
        (df.get("cancelled_flag", pd.Series(0)) == 0) &
        (df.get("diverted_flag", pd.Series(0)) == 0)
    ).astype(int)

    # period_flag
    df["period_flag"] = np.where(
        df["flight_date"] <= baseline_end, "baseline", "recent"
    )

    # year_month
    df["year_month"] = df["flight_date"].dt.to_period("M").astype(str)

    # route_key
    df["route_key"] = df["origin"].str.strip() + "-" + df["dest"].str.strip()

    return df


# ---------------------------------------------------------------------------
# Fragility II: controllable / cascade classification
#
# BTS only populates the five cause-minute fields for flights that operated
# and arrived >= 15 minutes late; on-time, early, and cancelled flights report
# all five as null. Defaulting nulls to zero before taking the largest value
# would manufacture a spurious "Air Carrier" attribution for every one of
# those rows (idxmax on an all-zero row returns the first column), so
# has_cause_data must gate the assignment rather than rely on a zero fill.
# See flight_fragility_ii_machine_addon_spec.md, "Field population and
# null-handling rules."
# ---------------------------------------------------------------------------

CAUSE_COLS = [
    "carrier_delay_minutes",
    "weather_delay_minutes",
    "nas_delay_minutes",
    "security_delay_minutes",
    "late_aircraft_delay_minutes",
]

CAUSE_LABEL_MAP = {
    "carrier_delay_minutes": "Air Carrier",
    "weather_delay_minutes": "Weather",
    "nas_delay_minutes": "NAS",
    "security_delay_minutes": "Security",
    "late_aircraft_delay_minutes": "Late-arriving",
}


def derive_fragility_ii_flags(df: pd.DataFrame, study: dict) -> pd.DataFrame:
    """Derive primary_delay_cause and the controllable/cascade flags."""
    delay_thresh = study.get("delay_threshold_minutes", 60)

    df = df.copy()
    for col in CAUSE_COLS:
        if col not in df.columns:
            df[col] = np.nan

    has_cause_data = (
        df[CAUSE_COLS].notna().any(axis=1) & (df[CAUSE_COLS].fillna(0).sum(axis=1) > 0)
    )

    df["primary_delay_cause"] = None
    df.loc[has_cause_data, "primary_delay_cause"] = (
        df.loc[has_cause_data, CAUSE_COLS].idxmax(axis=1).map(CAUSE_LABEL_MAP)
    )

    df["controllable_delay_flag"] = (df["primary_delay_cause"] == "Air Carrier").astype(int)
    df["late_arriving_flag"] = (df["primary_delay_cause"] == "Late-arriving").astype(int)
    df["cascade_delay_flag"] = df["late_arriving_flag"]

    df["controllable_cancel_flag"] = (
        (df.get("cancelled_flag", pd.Series(0)) == 1) &
        (df.get("cancellation_code_bts", pd.Series("")) == "A")
    ).astype(int)

    # Severe-delay definition for Fragility II is an OR of dep/arr delay,
    # which differs from Fragility I's arrival-only severe_delay_flag — see
    # spec section "Definitional consistency with Fragility I."
    severe_either = (
        (df.get("dep_delay_min", pd.Series(np.nan)) >= delay_thresh) |
        (df.get("arr_delay_min", pd.Series(np.nan)) >= delay_thresh)
    )
    df["controllable_severe_delay_flag"] = (
        (df["controllable_delay_flag"] == 1) & severe_either
    ).astype(int)
    df["late_arriving_severe_delay_flag"] = (
        (df["late_arriving_flag"] == 1) & severe_either
    ).astype(int)

    return df


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Build integrated flight fact table")
    parser.add_argument("--routes", default="config/routes.yaml")
    parser.add_argument("--study", default="config/study.yaml")
    parser.add_argument("--bts", default="data/staging/bts_flights.csv")
    parser.add_argument("--weather", default="data/staging/airport_weather_hourly.csv")
    parser.add_argument("--out", default="data/curated/flight_operability_fact.csv")
    parser.add_argument("--qa-out", default="output/qa_summary.csv")
    args = parser.parse_args()

    script_dir = Path(__file__).parent
    root = script_dir.parent
    routes_path = root / args.routes
    study_path = root / args.study
    bts_path = root / args.bts
    weather_path = root / args.weather
    out_path = root / args.out
    qa_path = root / args.qa_out

    out_path.parent.mkdir(parents=True, exist_ok=True)
    qa_path.parent.mkdir(parents=True, exist_ok=True)

    routes, study = load_config(routes_path, study_path)
    basket_lookup = build_basket_lookup(routes)

    bts = load_bts(bts_path)
    wx = load_weather(weather_path)

    # Filter BTS to our route universe
    known_routes = set(basket_lookup.keys())
    bts = bts[bts.apply(lambda r: (r.get("origin"), r.get("dest")) in known_routes, axis=1)].copy()
    log.info(f"BTS after route filter: {len(bts):,} rows")

    if bts.empty:
        log.error("No BTS flights in the configured route universe. Check routes.yaml.")
        raise SystemExit(1)

    # Assign baskets
    bts["market_bucket"] = bts.apply(lambda r: assign_basket(r, basket_lookup), axis=1)
    bts["carrier_group"] = bts["market_bucket"].map(assign_carrier_group)

    # Convert BTS local times to UTC keys for weather join
    bts = _add_utc_keys(bts)

    # Join NOAA weather
    fact = join_weather(bts, wx)

    # Derive flags
    fact = derive_flags(fact, study)
    fact = derive_fragility_ii_flags(fact, study)

    # Enforce required column order
    required_cols = [
        "flight_date", "year_month", "carrier_group", "carrier_code", "operating_carrier",
        "flight_number", "origin", "dest", "route_key", "sched_dep_local", "sched_arr_local",
        "dep_delay_min", "arr_delay_min", "cancelled_flag", "diverted_flag", "distance_miles",
        "cancellation_code_bts",
        "wx_dep_visibility", "wx_dep_ceiling", "wx_dep_wxcodes", "wx_dep_wind_kt", "wx_dep_bucket",
        "wx_arr_visibility", "wx_arr_ceiling", "wx_arr_wxcodes", "wx_arr_wind_kt", "wx_arr_bucket",
        "weather_bucket", "market_bucket", "period_flag", "severe_delay_flag", "operated_flag",
        "carrier_delay_minutes", "weather_delay_minutes", "nas_delay_minutes",
        "security_delay_minutes", "late_aircraft_delay_minutes", "primary_delay_cause",
        "controllable_delay_flag", "controllable_cancel_flag", "late_arriving_flag",
        "cascade_delay_flag", "controllable_severe_delay_flag", "late_arriving_severe_delay_flag",
    ]
    for col in required_cols:
        if col not in fact.columns:
            fact[col] = np.nan
    extra_cols = [c for c in fact.columns if c not in required_cols]
    fact = fact[required_cols + extra_cols]

    fact.to_csv(out_path, index=False)
    log.info(f"Fact table written: {out_path}  ({len(fact):,} rows)")

    # -------------------------------------------------------------------
    # QA summary
    # -------------------------------------------------------------------
    qa_rows = []

    # Row counts by month
    if "year_month" in fact.columns:
        month_counts = fact.groupby("year_month").size().reset_index(name="row_count")
        month_counts["check"] = "bts_rows_by_month"
        qa_rows.append(month_counts.rename(columns={"year_month": "dimension"}))

    # Weather join match rates
    dep_matched = fact["wx_dep_bucket"].notna().sum()
    arr_matched = fact["wx_arr_bucket"].notna().sum()
    total = len(fact)
    qa_rows.append(pd.DataFrame([
        {"dimension": "total_flights", "row_count": total, "check": "weather_join"},
        {"dimension": "dep_wx_matched", "row_count": dep_matched, "check": "weather_join"},
        {"dimension": "arr_wx_matched", "row_count": arr_matched, "check": "weather_join"},
        {"dimension": "dep_match_rate", "row_count": round(dep_matched / max(total, 1), 4), "check": "weather_join"},
        {"dimension": "arr_match_rate", "row_count": round(arr_matched / max(total, 1), 4), "check": "weather_join"},
    ]))

    # Cancellation stats
    cancel_total = (fact.get("cancelled_flag", pd.Series(0)) == 1).sum()
    weather_cancel = fact[
        (fact.get("cancelled_flag", pd.Series(0)) == 1) &
        (fact.get("cancellation_code_bts", pd.Series("")) == "B")
    ].shape[0]
    qa_rows.append(pd.DataFrame([
        {"dimension": "total_cancellations", "row_count": cancel_total, "check": "cancellation_qa"},
        {"dimension": "weather_cancellations_bts_code_B", "row_count": weather_cancel, "check": "cancellation_qa"},
    ]))

    # Weather bucket null rate
    wb_null = fact["weather_bucket"].isna().mean() if "weather_bucket" in fact.columns else 1.0
    qa_rows.append(pd.DataFrame([{
        "dimension": "weather_bucket",
        "row_count": round(wb_null, 4),
        "check": "null_rate",
    }]))

    # Sample size by market × weather × period
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

    # Fragility II: cause-data restriction check.
    # has_cause_data should equal the set of operated flights with ArrDelay >= 15;
    # any mismatch means the null-guard isn't behaving as documented in the spec.
    delay_thresh = study.get("delay_threshold_minutes", 60)
    cause_data_count = int((fact["primary_delay_cause"].notna()).sum())
    arrdelay15_operated = int(
        ((fact.get("arr_delay_min", pd.Series(np.nan)) >= 15) &
         (fact.get("operated_flag", pd.Series(0)) == 1)).sum()
    )
    cancelled_with_cause = int(
        ((fact.get("cancelled_flag", pd.Series(0)) == 1) &
         (fact["primary_delay_cause"].notna())).sum()
    )
    qa_rows.append(pd.DataFrame([
        {"dimension": "cause_data_count", "row_count": cause_data_count, "check": "fragility_ii_cause_data"},
        {"dimension": "arrdelay15_operated_count", "row_count": arrdelay15_operated, "check": "fragility_ii_cause_data"},
        {"dimension": "cause_data_matches_arrdelay15", "row_count": int(cause_data_count == arrdelay15_operated), "check": "fragility_ii_cause_data"},
        {"dimension": "cancelled_flights_with_spurious_cause", "row_count": cancelled_with_cause, "check": "fragility_ii_cause_data"},
    ]))

    # Fragility II: controllable / cascade counts by basket
    if "market_bucket" in fact.columns:
        cause_by_basket = (
            fact.groupby("market_bucket")
            .agg(
                controllable_delay_count=("controllable_delay_flag", "sum"),
                controllable_severe_delay_count=("controllable_severe_delay_flag", "sum"),
                late_arriving_severe_delay_count=("late_arriving_severe_delay_flag", "sum"),
                controllable_cancel_count=("controllable_cancel_flag", "sum"),
                operated_count=("operated_flag", "sum"),
            )
            .reset_index()
        )
        for _, r in cause_by_basket.iterrows():
            basket = r["market_bucket"]
            qa_rows.append(pd.DataFrame([
                {"dimension": f"{basket}/controllable_severe_delay_count", "row_count": int(r["controllable_severe_delay_count"]), "check": "fragility_ii_basket_counts"},
                {"dimension": f"{basket}/late_arriving_severe_delay_count", "row_count": int(r["late_arriving_severe_delay_count"]), "check": "fragility_ii_basket_counts"},
                {"dimension": f"{basket}/controllable_cancel_count", "row_count": int(r["controllable_cancel_count"]), "check": "fragility_ii_basket_counts"},
                {"dimension": f"{basket}/operated_count", "row_count": int(r["operated_count"]), "check": "fragility_ii_basket_counts"},
            ]))

    qa_df = pd.concat(qa_rows, ignore_index=True) if qa_rows else pd.DataFrame()
    qa_df.to_csv(qa_path, index=False)
    log.info(f"QA summary written: {qa_path}")

    # Console summary
    log.info("=== Fact Table Summary ===")
    log.info(f"  Total flights:      {len(fact):,}")
    log.info(f"  Total cancellations:{cancel_total:,} ({cancel_total/max(len(fact),1):.2%})")
    if "market_bucket" in fact.columns:
        log.info(f"  Market buckets: {fact['market_bucket'].value_counts().to_dict()}")
    if "weather_bucket" in fact.columns:
        log.info(f"  Weather buckets: {fact['weather_bucket'].value_counts().to_dict()}")
    log.info(f"  Fragility II cause data: {cause_data_count:,} flights "
             f"(ArrDelay>=15 operated: {arrdelay15_operated:,}, "
             f"cancelled w/ spurious cause: {cancelled_with_cause:,})")


if __name__ == "__main__":
    main()
