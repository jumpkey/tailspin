#!/usr/bin/env python3
"""
11_extract_faa_weather.py — Extract hourly airport weather from NOAA ASOS via IEM.

WHY THIS REPLACES THE ORIGINAL FAA ASPM APPROACH
-------------------------------------------------
The original script targeted https://www.aspm.faa.gov/asqpwx/Index.asp (URL does
not exist) and the correct FAA ASQP portal (https://www.aspm.faa.gov/asqp/sys/)
requires a restricted FAA-registered account — not publicly accessible.

Beyond the access problem, the FAA "Cancelled Flights with Weather" report only
covers cancelled flights, making it impossible to assign a weather bucket to
operated (non-cancelled) flights. That flaw made the core analysis metric
(cancellation_rate = cancelled / all_flights_in_weather_bucket) meaningless
because the adverse/marginal buckets would contain only cancelled flights,
forcing their cancellation rate to ≈ 1.0 for every carrier.

THE NEW APPROACH
----------------
Iowa Environmental Mesonet (IEM) archives NOAA ASOS hourly METAR observations
for all U.S. airports free of charge with no authentication required.
We download visibility, cloud layers, and present-weather codes for every airport
in the study and pre-compute a weather_bucket (benign / marginal / adverse) for
each airport-hour observation. Script 20 then joins each BTS flight to the NOAA
weather at its departure airport and arrival airport using UTC-adjusted times,
giving every flight — operated or cancelled — a meaningful weather context.

Outputs
-------
data/raw/faa/noaa_asos_raw.csv            Raw NOAA ASOS download (all stations)
data/staging/airport_weather_hourly.csv   Normalized hourly weather per airport
data/raw/faa/manifest.csv                 Audit log

Usage
-----
python scripts/11_extract_faa_weather.py \\
    --routes config/routes.yaml \\
    --study  config/study.yaml \\
    --out    data/staging/airport_weather_hourly.csv [--force]
"""

import argparse
import csv
import hashlib
import io
import logging
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests
import yaml

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Airport → ICAO station mapping and timezone
# ---------------------------------------------------------------------------
AIRPORT_STATION = {
    "LFT": "KLFT",
    "BTR": "KBTR",
    "AEX": "KAEX",
    "MLU": "KMLU",
    "GPT": "KGPT",
    "SHV": "KSHV",
    "DFW": "KDFW",
    "IAH": "KIAH",
    "ATL": "KATL",
}

# All study airports except ATL are in Central Time
AIRPORT_TZ = {
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

# IEM ASOS archive API
IEM_ASOS_URL = "https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py"

# ---------------------------------------------------------------------------
# Weather bucket thresholds — mirrors spec + fallback text rules
# ---------------------------------------------------------------------------
# Adverse:  visibility < 1 SM  OR  ceiling < 500 ft
#           OR thunderstorm / freezing precip / blizzard / heavy snow
# Marginal: visibility < 3 SM  OR  ceiling < 1000 ft
#           OR rain / light snow / mist / fog / drizzle (without adverse)
# Benign:   all other conditions

ADVERSE_VIS_SM = 1.0
ADVERSE_CEIL_FT = 500.0
MARGINAL_VIS_SM = 3.0
MARGINAL_CEIL_FT = 1000.0

ADVERSE_WX_TOKENS = frozenset(["TS", "FZ", "BLSN", "+SN", "+RASN", "FC"])
MARGINAL_WX_TOKENS = frozenset(["RA", "SN", "RASN", "DZ", "FG", "MIFG", "BR", "GS", "PL"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_config(routes_path: Path, study_path: Path):
    with open(routes_path) as f:
        routes = yaml.safe_load(f)
    with open(study_path) as f:
        study = yaml.safe_load(f)
    return routes, study


def collect_airports(routes: dict) -> set:
    airports: set = set()
    for basket in routes.values():
        if isinstance(basket, list):
            for leg in basket:
                airports.add(leg["origin"])
                airports.add(leg["dest"])
    return airports


def checksum(path: Path) -> str:
    sha = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha.update(chunk)
    return sha.hexdigest()[:16]


def append_manifest(manifest_path: Path, row: dict):
    write_header = not manifest_path.exists() or manifest_path.stat().st_size == 0
    with open(manifest_path, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(row.keys()))
        if write_header:
            writer.writeheader()
        writer.writerow(row)


# ---------------------------------------------------------------------------
# NOAA IEM ASOS fetch
# ---------------------------------------------------------------------------

def fetch_noaa_asos(
    stations: list[str],
    start: str,
    end: str,
    session: requests.Session,
) -> pd.DataFrame:
    """
    Download hourly METAR observations from the IEM ASOS archive.

    Returns a raw DataFrame with columns:
        station, valid (UTC), vsby, skyc1-4, skyl1-4, wxcodes, sknt
    """
    log.info(f"  Requesting NOAA ASOS data for {len(stations)} stations "
             f"{start} → {end} ...")

    # Parse year/month/day from ISO date strings
    s_year, s_month, s_day = start.split("-")
    e_year, e_month, e_day = end.split("-")

    params = {
        "data": ["vsby", "skyc1", "skyl1", "skyc2", "skyl2",
                 "skyc3", "skyl3", "skyc4", "skyl4", "presentwx", "sknt", "gust"],
        "year1": s_year, "month1": s_month, "day1": s_day,
        "year2": e_year, "month2": e_month, "day2": e_day,
        "tz": "UTC",
        "format": "comma",
        "latlon": "no",
        "elev": "no",
        "missing": "M",
        "trace": "0.0001",
        "direct": "no",
        "report_type": "3",   # ASOS routine hourly observations
    }
    # requests handles repeated keys via list of tuples
    param_list = []
    for k, v in params.items():
        if isinstance(v, list):
            for item in v:
                param_list.append(("data", item))
        else:
            param_list.append((k, v))
    for stn in stations:
        param_list.append(("station", stn))

    resp = session.get(IEM_ASOS_URL, params=param_list, timeout=300)
    resp.raise_for_status()

    text = resp.text
    # Strip comment lines (start with #)
    data_lines = [ln for ln in text.splitlines() if not ln.startswith("#")]
    if not data_lines:
        raise ValueError("NOAA ASOS returned no data")

    df = pd.read_csv(io.StringIO("\n".join(data_lines)), dtype=str, low_memory=False)
    log.info(f"  NOAA ASOS raw rows: {len(df):,}")
    return df


# ---------------------------------------------------------------------------
# Ceiling derivation from sky-condition layers
# ---------------------------------------------------------------------------

def _derive_ceiling(row: pd.Series) -> float | None:
    """Return the lowest BKN or OVC layer height in feet, or None if none."""
    for i in range(1, 5):
        cov = str(row.get(f"skyc{i}", "M") or "M").strip().upper()
        ht_str = str(row.get(f"skyl{i}", "M") or "M").strip()
        if cov in ("BKN", "OVC", "OVX"):
            try:
                ht = float(ht_str)
                return ht
            except ValueError:
                pass
    return None


# ---------------------------------------------------------------------------
# Weather bucket classification
# ---------------------------------------------------------------------------

def classify_weather_bucket(vsby_sm: float | None, ceiling_ft: float | None, wxcodes: str) -> str:
    """
    Classify one airport-hour into benign / marginal / adverse.

    Rules mirror the spec's ASPM-level thresholds and fallback text rules,
    but expressed in METAR visibility (statute miles) and ceiling (feet AGL)
    equivalents drawn from FAA IFR/MVFR/VFR categories:

      Adverse  ≈ IFR/LIFR : vsby < 1 SM  OR ceiling < 500 ft
                             OR TS/freezing precip/heavy snow/blizzard
      Marginal ≈ MVFR     : vsby 1-3 SM  OR ceiling 500-1000 ft
                             OR rain/snow/fog/mist/drizzle
      Benign   ≈ VFR      : all other conditions
    """
    wx = str(wxcodes or "").upper()

    # --- Adverse check ---
    # Present-weather tokens that indicate severe conditions regardless of vis/ceil
    if any(tok in wx for tok in ADVERSE_WX_TOKENS):
        return "adverse"
    if vsby_sm is not None and vsby_sm < ADVERSE_VIS_SM:
        return "adverse"
    if ceiling_ft is not None and ceiling_ft < ADVERSE_CEIL_FT:
        return "adverse"

    # --- Marginal check ---
    if any(tok in wx for tok in MARGINAL_WX_TOKENS):
        return "marginal"
    if vsby_sm is not None and vsby_sm < MARGINAL_VIS_SM:
        return "marginal"
    if ceiling_ft is not None and ceiling_ft < MARGINAL_CEIL_FT:
        return "marginal"

    return "benign"


# ---------------------------------------------------------------------------
# Normalize raw NOAA → per-airport-hour staging
# ---------------------------------------------------------------------------

def normalize_noaa(df: pd.DataFrame, airport_station_inv: dict[str, str]) -> pd.DataFrame:
    """
    Normalize the raw NOAA ASOS DataFrame into one row per airport-hour.

    When there are multiple observations within an hour (SPECI + METAR),
    we take the worst conditions (min vsby, min ceiling, combined wx codes).

    Returns columns:
        airport_code, obs_utc, obs_date_utc, obs_hour_utc,
        visibility_sm, ceiling_ft, wxcodes, wind_kt, weather_bucket, tz_name
    """
    if df.empty:
        return pd.DataFrame()

    df = df.copy()

    # Map station → airport code (e.g. "LFT" → "LFT")
    df["airport_code"] = df["station"].str.upper().map(
        lambda s: airport_station_inv.get(s, airport_station_inv.get("K" + s, s))
    )

    # Parse UTC datetime
    df["obs_utc"] = pd.to_datetime(df["valid"], errors="coerce", utc=True)
    df = df.dropna(subset=["obs_utc"])
    df["obs_date_utc"] = df["obs_utc"].dt.date.astype(str)
    df["obs_hour_utc"] = df["obs_utc"].dt.hour

    # Numeric conversions
    df["visibility_sm"] = pd.to_numeric(df["vsby"].replace("M", None), errors="coerce")
    df["wind_kt"] = pd.to_numeric(df["sknt"].replace("M", None), errors="coerce")

    # Ceiling from cloud layers
    df["ceiling_ft"] = df.apply(_derive_ceiling, axis=1)

    # Present weather
    df["wxcodes"] = df["wxcodes"].replace("M", "").fillna("")

    # Derive weather bucket per observation
    df["weather_bucket_raw"] = df.apply(
        lambda r: classify_weather_bucket(r["visibility_sm"], r["ceiling_ft"], r["wxcodes"]),
        axis=1,
    )

    # Bucket severity ranking for aggregation
    bucket_rank = {"adverse": 2, "marginal": 1, "benign": 0}

    # Aggregate to one row per airport-hour (worst conditions in the hour)
    def _agg_hour(group: pd.DataFrame) -> pd.Series:
        worst_rank = group["weather_bucket_raw"].map(bucket_rank).max()
        worst_bucket = {v: k for k, v in bucket_rank.items()}[worst_rank]
        all_wx = " ".join(group["wxcodes"].dropna())
        min_vsby = group["visibility_sm"].min()
        min_ceil = group["ceiling_ft"].min()
        max_wind = group["wind_kt"].max()
        return pd.Series({
            "visibility_sm": round(min_vsby, 2) if pd.notna(min_vsby) else None,
            "ceiling_ft": round(min_ceil, 0) if pd.notna(min_ceil) else None,
            "wxcodes": all_wx.strip(),
            "wind_kt": round(max_wind, 1) if pd.notna(max_wind) else None,
            "weather_bucket": worst_bucket,
        })

    hourly = (
        df.groupby(["airport_code", "obs_date_utc", "obs_hour_utc"])
        .apply(_agg_hour)
        .reset_index()
    )

    # Add tz_name for use by the fact-builder
    hourly["tz_name"] = hourly["airport_code"].map(AIRPORT_TZ).fillna("America/Chicago")

    log.info(f"  Normalized to {len(hourly):,} airport-hour rows")
    return hourly


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Extract hourly airport weather from NOAA ASOS (IEM)"
    )
    parser.add_argument("--routes", default="config/routes.yaml")
    parser.add_argument("--study", default="config/study.yaml")
    parser.add_argument("--out", default="data/staging/airport_weather_hourly.csv")
    parser.add_argument("--raw-dir", default="data/raw/faa")
    parser.add_argument("--force", action="store_true", help="Re-download existing raw files")
    args = parser.parse_args()

    script_dir = Path(__file__).parent
    root = script_dir.parent
    routes_path = root / args.routes
    study_path = root / args.study
    out_path = root / args.out
    raw_dir = root / args.raw_dir
    manifest_path = raw_dir / "manifest.csv"
    raw_file = raw_dir / "noaa_asos_raw.csv"

    raw_dir.mkdir(parents=True, exist_ok=True)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    routes, study = load_config(routes_path, study_path)
    airports = collect_airports(routes)
    start = study["study_start"]
    end = study["study_end"]

    # Build station list for airports we have mappings for
    stations = [AIRPORT_STATION[ap] for ap in airports if ap in AIRPORT_STATION]
    # Inverse map: ICAO station → airport code (both with and without K prefix)
    airport_station_inv = {v: k for k, v in AIRPORT_STATION.items()}
    airport_station_inv.update({v[1:]: k for k, v in AIRPORT_STATION.items()})

    log.info(f"Airport universe: {sorted(airports)}")
    log.info(f"ASOS stations:    {sorted(stations)}")

    session = requests.Session()

    if raw_file.exists() and not args.force:
        log.info(f"Using cached NOAA raw file: {raw_file}")
        df_raw = pd.read_csv(raw_file, dtype=str, low_memory=False)
    else:
        df_raw = fetch_noaa_asos(stations, start, end, session)
        df_raw.to_csv(raw_file, index=False)
        append_manifest(manifest_path, {
            "source": "NOAA_ASOS_IEM",
            "filename": raw_file.name,
            "rows": len(df_raw),
            "extracted_at": datetime.now(timezone.utc).isoformat(),
            "checksum": checksum(raw_file),
            "params": f"stations={sorted(stations)},start={start},end={end}",
        })
        log.info(f"Raw NOAA file saved: {raw_file}  ({len(df_raw):,} rows)")
        time.sleep(1)

    # Normalize and write staging
    staging = normalize_noaa(df_raw, airport_station_inv)
    if staging.empty:
        log.error("No NOAA ASOS data after normalization.")
        raise SystemExit(1)

    staging.to_csv(out_path, index=False)
    log.info(f"Weather staging written: {out_path}  ({len(staging):,} rows)")

    # QA summary
    log.info("=== NOAA ASOS Weather QA ===")
    log.info(f"  Airports covered: {sorted(staging['airport_code'].unique())}")
    log.info(f"  Date range: {staging['obs_date_utc'].min()} → {staging['obs_date_utc'].max()}")
    bucket_counts = staging["weather_bucket"].value_counts()
    for bucket, n in bucket_counts.items():
        pct = n / len(staging) * 100
        log.info(f"  {bucket:10s}: {n:>7,} hours  ({pct:.1f}%)")


if __name__ == "__main__":
    main()
