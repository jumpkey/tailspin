#!/usr/bin/env python3
"""
21_build_hubspoke_fact.py — Build the Module B (hub-spoke expansion)
curated fact table for Fragility IV/V.

Mirrors 20_build_flight_fact.py's weather-join and flag-derivation logic
(UTC-keyed airport-hour weather join, severe_delay_flag/operated_flag/
period_flag, and the Fragility II null-guarded controllable/cascade
classification) against the hub-spoke BTS extract instead of the fixed
9-airport/14-route extract. Kept as its own script rather than extending
20 — same non-coupling rationale as 13_extract_bts_hubspoke.py vs.
10_extract_bts.py: the hub-spoke airport universe is discovered, not fixed,
so airport timezone is resolved dynamically via `airportsdata` instead of
20's hand-maintained AIRPORT_TZ_NAMES table.

Adds operator_class (scripts/lib/operator_classify.py) and applies any
targeted FlightAware resolutions from 15_resolve_operator_ambiguity.py,
since Fragility IV's metrics are aggregated by operator_class, not just
market_bucket.

Outputs
-------
data/curated/hubspoke_operator_fact/   Hive-partitioned Parquet, by year_month
output/qa_summary_hubspoke.csv

Usage
-----
python scripts/21_build_hubspoke_fact.py --study config/study.yaml
"""

import argparse
import logging
import sys
from datetime import datetime, date, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import airportsdata
import numpy as np
import pandas as pd
import yaml

sys.path.insert(0, str(Path(__file__).parent))
from lib.backend import read_table, write_partitioned_parquet  # noqa: E402
from lib.operator_classify import apply_resolution_overrides, classify_operator, load_operator_classes  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
log = logging.getLogger(__name__)

_AIRPORTS_DB = airportsdata.load("IATA")
_TZ_CACHE: dict[str, ZoneInfo] = {}
UTC = ZoneInfo("UTC")


def _airport_tz_name(airport: str) -> str:
    rec = _AIRPORTS_DB.get(airport)
    return rec["tz"] if rec and rec.get("tz") else "America/Chicago"


def _get_tz(tz_name: str) -> ZoneInfo:
    if tz_name not in _TZ_CACHE:
        try:
            _TZ_CACHE[tz_name] = ZoneInfo(tz_name)
        except ZoneInfoNotFoundError:
            _TZ_CACHE[tz_name] = ZoneInfo("America/Chicago")
    return _TZ_CACHE[tz_name]


BUCKET_RANK = {"adverse": 2, "marginal": 1, "benign": 0, "unknown": -1}
RANK_BUCKET = {v: k for k, v in BUCKET_RANK.items()}


def _worst_bucket(b1: str, b2: str) -> str:
    r1 = BUCKET_RANK.get(b1, -1)
    r2 = BUCKET_RANK.get(b2, -1)
    return RANK_BUCKET.get(max(r1, r2), "benign")


def _hhmm_to_utc(flight_date: date, hhmm_str: str, airport: str) -> tuple[date, int]:
    try:
        hhmm = str(hhmm_str).strip().zfill(4)
        h = int(hhmm[:2])
        m = int(hhmm[2:4])
        if h == 24:
            h = 0
            flight_date = flight_date + timedelta(days=1)
        h = min(h, 23)
        tz = _get_tz(_airport_tz_name(airport))
        local_dt = datetime(flight_date.year, flight_date.month, flight_date.day, h, m, tzinfo=tz)
        utc_dt = local_dt.astimezone(UTC)
        return utc_dt.date(), utc_dt.hour
    except Exception:
        return flight_date, int(str(hhmm_str).strip().zfill(4)[:2]) if hhmm_str else 0


def load_study(path: Path) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def load_weather(path: Path) -> pd.DataFrame:
    if not path.exists():
        log.warning("  Hub-spoke weather staging not found — all flights will get 'benign' bucket.")
        return pd.DataFrame()
    df = pd.read_csv(path, dtype=str)
    df["obs_hour_utc"] = pd.to_numeric(df["obs_hour_utc"], errors="coerce").astype("Int64")
    for col in ("visibility_sm", "ceiling_ft", "wind_kt"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def _add_utc_keys(bts: pd.DataFrame) -> pd.DataFrame:
    log.info("  Converting BTS local times to UTC ...")
    dep_dates, dep_hours, arr_dates, arr_hours = [], [], [], []

    for _, row in bts.iterrows():
        fd = row["flight_date"].date() if pd.notna(row["flight_date"]) else date.today()
        origin = str(row.get("origin", "")).strip().upper()
        dest = str(row.get("dest", "")).strip().upper()

        d_date, d_hour = _hhmm_to_utc(fd, row.get("sched_dep_local", "0000"), origin)
        dep_dates.append(str(d_date))
        dep_hours.append(d_hour)

        elapsed = row.get("scheduled_elapsed_min")
        try:
            elapsed = float(elapsed)
        except (TypeError, ValueError):
            elapsed = None

        if elapsed is not None and elapsed > 0:
            dep_tz = _get_tz(_airport_tz_name(origin))
            hhmm = str(row.get("sched_dep_local", "0000")).strip().zfill(4)
            h = min(int(hhmm[:2]), 23)
            m = int(hhmm[2:4]) if hhmm[2:4].isdigit() else 0
            try:
                local_dep = datetime(fd.year, fd.month, fd.day, h, m, tzinfo=dep_tz)
                utc_arr = local_dep.astimezone(UTC) + timedelta(minutes=elapsed)
                arr_dates.append(str(utc_arr.date()))
                arr_hours.append(utc_arr.hour)
            except Exception:
                arr_dates.append(str(d_date))
                arr_hours.append((d_hour + 2) % 24)
        else:
            a_date, a_hour = _hhmm_to_utc(fd, row.get("sched_arr_local", "0000"), dest)
            if (a_date, a_hour) < (d_date, d_hour):
                a_date = (datetime.combine(a_date, datetime.min.time()) + timedelta(days=1)).date()
            arr_dates.append(str(a_date))
            arr_hours.append(a_hour)

    bts = bts.copy()
    bts["dep_utc_date"] = dep_dates
    bts["dep_utc_hour"] = dep_hours
    bts["arr_utc_date"] = arr_dates
    bts["arr_utc_hour"] = arr_hours
    return bts


def join_weather(bts: pd.DataFrame, wx: pd.DataFrame) -> pd.DataFrame:
    if wx.empty:
        bts = bts.copy()
        for col in ("wx_dep_bucket", "wx_arr_bucket"):
            bts[col] = np.nan
        bts["weather_bucket"] = "benign"
        return bts

    wx_dep = wx[["airport_code", "obs_date_utc", "obs_hour_utc", "weather_bucket"]].copy()
    wx_dep.columns = ["airport_code", "obs_date_utc", "obs_hour_utc", "wx_dep_bucket"]
    wx_arr = wx[["airport_code", "obs_date_utc", "obs_hour_utc", "weather_bucket"]].copy()
    wx_arr.columns = ["airport_code", "obs_date_utc", "obs_hour_utc", "wx_arr_bucket"]

    bts = bts.copy()
    bts["dep_utc_hour"] = bts["dep_utc_hour"].astype("Int64")
    bts["arr_utc_hour"] = bts["arr_utc_hour"].astype("Int64")

    merged = bts.merge(
        wx_dep, left_on=["origin", "dep_utc_date", "dep_utc_hour"],
        right_on=["airport_code", "obs_date_utc", "obs_hour_utc"], how="left",
    ).drop(columns=["airport_code", "obs_date_utc", "obs_hour_utc"], errors="ignore")

    merged = merged.merge(
        wx_arr, left_on=["dest", "arr_utc_date", "arr_utc_hour"],
        right_on=["airport_code", "obs_date_utc", "obs_hour_utc"], how="left",
    ).drop(columns=["airport_code", "obs_date_utc", "obs_hour_utc"], errors="ignore")

    merged["weather_bucket"] = merged.apply(
        lambda r: _worst_bucket(r.get("wx_dep_bucket") or "benign", r.get("wx_arr_bucket") or "benign"),
        axis=1,
    )

    total = len(merged)
    dep_matched = merged["wx_dep_bucket"].notna().sum()
    arr_matched = merged["wx_arr_bucket"].notna().sum()
    log.info(f"  Departure weather matched: {dep_matched:,}/{total:,} ({dep_matched/max(total,1):.1%})")
    log.info(f"  Arrival weather matched:   {arr_matched:,}/{total:,} ({arr_matched/max(total,1):.1%})")
    return merged


def derive_flags(df: pd.DataFrame, study: dict) -> pd.DataFrame:
    delay_thresh = study.get("delay_threshold_minutes", 60)
    baseline_end = pd.to_datetime(study["baseline_end"])

    df = df.copy()
    df["severe_delay_flag"] = (
        (df.get("arr_delay_min", pd.Series(np.nan)) >= delay_thresh) &
        (df.get("cancelled_flag", pd.Series(0)) == 0)
    ).astype(int)
    df["operated_flag"] = (
        (df.get("cancelled_flag", pd.Series(0)) == 0) &
        (df.get("diverted_flag", pd.Series(0)) == 0)
    ).astype(int)
    df["period_flag"] = np.where(df["flight_date"] <= baseline_end, "baseline", "recent")
    df["route_key"] = df["origin"].str.strip() + "-" + df["dest"].str.strip()
    return df


# Same null-guard rationale as 20_build_flight_fact.py: BTS only populates
# the five cause-minute fields for operated flights that arrived >= 15 min
# late, so has_cause_data must gate idxmax rather than rely on a zero fill.
CAUSE_COLS = [
    "carrier_delay_minutes", "weather_delay_minutes", "nas_delay_minutes",
    "security_delay_minutes", "late_aircraft_delay_minutes",
]
CAUSE_LABEL_MAP = {
    "carrier_delay_minutes": "Air Carrier",
    "weather_delay_minutes": "Weather",
    "nas_delay_minutes": "NAS",
    "security_delay_minutes": "Security",
    "late_aircraft_delay_minutes": "Late-arriving",
}


def derive_fragility_ii_flags(df: pd.DataFrame, study: dict) -> pd.DataFrame:
    delay_thresh = study.get("delay_threshold_minutes", 60)
    df = df.copy()
    for col in CAUSE_COLS:
        if col not in df.columns:
            df[col] = np.nan

    has_cause_data = df[CAUSE_COLS].notna().any(axis=1) & (df[CAUSE_COLS].fillna(0).sum(axis=1) > 0)
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

    severe_either = (
        (df.get("dep_delay_min", pd.Series(np.nan)) >= delay_thresh) |
        (df.get("arr_delay_min", pd.Series(np.nan)) >= delay_thresh)
    )
    df["controllable_severe_delay_flag"] = ((df["controllable_delay_flag"] == 1) & severe_either).astype(int)
    df["late_arriving_severe_delay_flag"] = ((df["late_arriving_flag"] == 1) & severe_either).astype(int)
    return df


def main():
    parser = argparse.ArgumentParser(description="Build the hub-spoke (Module B) curated fact table")
    parser.add_argument("--study", default="config/study.yaml")
    parser.add_argument("--bts", default="data/staging/bts_hubspoke")
    parser.add_argument("--weather", default="data/staging/weather_hubspoke_hourly.csv")
    parser.add_argument("--resolution", default="data/staging/operator_resolution.csv")
    parser.add_argument("--out", default="data/curated/hubspoke_operator_fact")
    parser.add_argument("--qa-out", default="output/qa_summary_hubspoke.csv")
    args = parser.parse_args()

    script_dir = Path(__file__).parent
    root = script_dir.parent
    study_path = root / args.study
    bts_path = root / args.bts
    weather_path = root / args.weather
    resolution_path = root / args.resolution
    out_path = root / args.out
    qa_path = root / args.qa_out

    qa_path.parent.mkdir(parents=True, exist_ok=True)

    study = load_study(study_path)
    operator_config = load_operator_classes(root / study.get("operator_classes_config", "config/operator_classes.yaml"))

    if not bts_path.exists():
        raise FileNotFoundError(f"Hub-spoke BTS staging not found: {bts_path}\nRun 13_extract_bts_hubspoke.py first.")

    backend = study.get("backend", "pandas")
    bts = read_table(bts_path, backend=backend)
    log.info(f"Loaded hub-spoke BTS staging: {len(bts):,} rows (backend={backend})")

    if "flight_date" in bts.columns:
        bts["flight_date"] = pd.to_datetime(bts["flight_date"], errors="coerce")
    for col in ("dep_delay_min", "arr_delay_min", "distance_miles", "actual_elapsed_min",
                "scheduled_elapsed_min", "carrier_delay_minutes", "weather_delay_minutes",
                "nas_delay_minutes", "security_delay_minutes", "late_aircraft_delay_minutes"):
        if col in bts.columns:
            bts[col] = pd.to_numeric(bts[col], errors="coerce")
    for col in ("cancelled_flag", "diverted_flag"):
        if col in bts.columns:
            bts[col] = pd.to_numeric(bts[col], errors="coerce").fillna(0).astype(int)
    for col in ("sched_dep_local", "sched_arr_local"):
        if col in bts.columns:
            bts[col] = bts[col].astype(str).str.zfill(4)

    wx = load_weather(weather_path)
    bts = _add_utc_keys(bts)
    fact = join_weather(bts, wx)
    fact = derive_flags(fact, study)
    fact = derive_fragility_ii_flags(fact, study)

    fact = classify_operator(fact, operator_config, route_basket_col=None)
    fact = apply_resolution_overrides(fact, resolution_path)

    if "year_month" not in fact.columns:
        fact["year_month"] = fact["flight_date"].dt.to_period("M").astype(str)

    write_partitioned_parquet(fact, out_path, partition_cols=["year_month"])

    # -------------------------------------------------------------------
    # QA summary
    # -------------------------------------------------------------------
    qa_rows = []
    qa_rows.append(pd.DataFrame([{"dimension": "total_flights", "row_count": len(fact), "check": "row_count"}]))

    if "operator_class" in fact.columns:
        op_counts = fact["operator_class"].value_counts().reset_index()
        op_counts.columns = ["dimension", "row_count"]
        op_counts["check"] = "operator_class_counts"
        qa_rows.append(op_counts)

    if "hub_family" in fact.columns:
        hub_counts = fact["hub_family"].value_counts().reset_index()
        hub_counts.columns = ["dimension", "row_count"]
        hub_counts["check"] = "hub_family_counts"
        qa_rows.append(hub_counts)

    wb_null = fact["weather_bucket"].isna().mean() if "weather_bucket" in fact.columns else 1.0
    qa_rows.append(pd.DataFrame([{"dimension": "weather_bucket", "row_count": round(wb_null, 4), "check": "null_rate"}]))

    qa_df = pd.concat(qa_rows, ignore_index=True)
    qa_df.to_csv(qa_path, index=False)
    log.info(f"QA summary written: {qa_path}")

    log.info("=== Hub-Spoke Fact Table Summary ===")
    log.info(f"  Total flights: {len(fact):,}")
    if "operator_class" in fact.columns:
        log.info(f"  Operator classes: {fact['operator_class'].value_counts().to_dict()}")
    if "hub_family" in fact.columns:
        log.info(f"  Hub families: {fact['hub_family'].value_counts().to_dict()}")
    if "weather_bucket" in fact.columns:
        log.info(f"  Weather buckets: {fact['weather_bucket'].value_counts().to_dict()}")


if __name__ == "__main__":
    main()
