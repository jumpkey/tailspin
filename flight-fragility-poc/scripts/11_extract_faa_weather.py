#!/usr/bin/env python3
"""
11_extract_faa_weather.py — Extract FAA ASPM/ASQP cancelled-flights-with-weather data.

For each configured route pair and date window this script attempts to pull
the FAA "Cancelled Flights with Weather Report" from the ASPM web portal.
Both the raw export payload and a normalized staging CSV are saved.

Outputs
-------
data/raw/faa/faa_cancel_weather_<origin>_<dest>_<start>_<end>.csv
data/staging/faa_cancel_weather.csv
data/raw/faa/manifest.csv

Usage
-----
python scripts/11_extract_faa_weather.py \\
    --routes config/routes.yaml \\
    --study  config/study.yaml \\
    --out    data/staging/faa_cancel_weather.csv [--force]

Notes
-----
FAA ASPM uses ASP.NET session-based forms.  The script attempts a direct POST
session; if that fails it falls back to a static-URL variant and logs a
warning.  Raw payloads are saved unchanged for audit purposes.
"""

import argparse
import csv
import hashlib
import io
import logging
import re
import sys
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

# ASPM Cancelled Flights with Weather report base URL
FAA_ASPM_BASE = "https://www.aspm.faa.gov"
FAA_CANCEL_WEATHER_URL = f"{FAA_ASPM_BASE}/asqpwx/Index.asp"

# FAA staging schema
FAA_RENAME = {
    "Scheduled Departure Date": "scheduled_departure_date",
    "Carrier Code": "carrier_code",
    "Flight Number": "flight_number",
    "Departure Airport": "departure_airport",
    "Arrival Airport": "arrival_airport",
    "Scheduled Departure Time": "scheduled_departure_time",
    "Scheduled Arrival Time": "scheduled_arrival_time",
    "Departure Wind": "dep_wind",
    "Departure Ceiling": "dep_ceiling",
    "Departure Visibility": "dep_visibility",
    "Departure Nearby Thunderstorm": "dep_nearby_ts",
    "Departure Local Weather": "dep_local_weather",
    "Arrival Wind": "arr_wind",
    "Arrival Ceiling": "arr_ceiling",
    "Arrival Visibility": "arr_visibility",
    "Arrival Nearby Thunderstorm": "arr_nearby_ts",
    "Arrival Local Weather": "arr_local_weather",
    # Alternative FAA column spellings
    "DEP_WIND": "dep_wind",
    "DEP_CEIL": "dep_ceiling",
    "DEP_VIS": "dep_visibility",
    "DEP_TS": "dep_nearby_ts",
    "DEP_WX": "dep_local_weather",
    "ARR_WIND": "arr_wind",
    "ARR_CEIL": "arr_ceiling",
    "ARR_VIS": "arr_visibility",
    "ARR_TS": "arr_nearby_ts",
    "ARR_WX": "arr_local_weather",
}

REQUIRED_OUT_COLS = [
    "scheduled_departure_date",
    "carrier_code",
    "flight_number",
    "departure_airport",
    "arrival_airport",
    "scheduled_departure_time",
    "scheduled_arrival_time",
    "dep_wind",
    "dep_ceiling",
    "dep_visibility",
    "dep_nearby_ts",
    "dep_local_weather",
    "arr_wind",
    "arr_ceiling",
    "arr_visibility",
    "arr_nearby_ts",
    "arr_local_weather",
]


def load_config(routes_path: Path, study_path: Path):
    with open(routes_path) as f:
        routes = yaml.safe_load(f)
    with open(study_path) as f:
        study = yaml.safe_load(f)
    return routes, study


def all_route_pairs(routes: dict) -> list[dict]:
    pairs = []
    seen = set()
    for basket_name, legs in routes.items():
        if not isinstance(legs, list):
            continue
        for leg in legs:
            key = (leg["origin"], leg["dest"])
            if key not in seen:
                pairs.append(leg)
                seen.add(key)
    return pairs


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


def fetch_faa_cancel_weather(
    origin: str,
    dest: str,
    start: str,
    end: str,
    session: requests.Session,
) -> pd.DataFrame:
    """
    Attempt to pull FAA ASPM Cancelled Flights with Weather for one route pair.

    Strategy
    --------
    1. GET the report page to obtain any ASP.NET ViewState tokens.
    2. POST with route/date parameters.
    3. Parse returned HTML table or CSV.

    Returns an empty DataFrame if extraction fails (caller logs warning).
    """
    log.info(f"  FAA weather: {origin}→{dest}  {start}..{end}")

    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; FlightFragilityPOC/1.0)",
        "Referer": FAA_CANCEL_WEATHER_URL,
    }

    try:
        # Step 1 — seed session and scrape ViewState
        resp_get = session.get(FAA_CANCEL_WEATHER_URL, headers=headers, timeout=30)
        resp_get.raise_for_status()

        vs = _scrape_viewstate(resp_get.text)

        # Step 2 — POST form submission
        payload = {
            "__VIEWSTATE": vs.get("__VIEWSTATE", ""),
            "__VIEWSTATEGENERATOR": vs.get("__VIEWSTATEGENERATOR", ""),
            "__EVENTVALIDATION": vs.get("__EVENTVALIDATION", ""),
            "txtAirport": origin,
            "txtArrAirport": dest,
            "txtStartDate": start,
            "txtEndDate": end,
            "btnSubmit": "Submit",
        }
        resp_post = session.post(
            FAA_CANCEL_WEATHER_URL, data=payload, headers=headers, timeout=120
        )
        resp_post.raise_for_status()

        df = _parse_faa_response(resp_post.text)
        if df is not None and not df.empty:
            return df
        log.warning(f"  FAA: empty result for {origin}→{dest}")
        return pd.DataFrame()

    except Exception as exc:
        log.warning(f"  FAA fetch failed for {origin}→{dest}: {exc}")
        return pd.DataFrame()


def _scrape_viewstate(html: str) -> dict:
    """Extract ASP.NET hidden form fields from page HTML."""
    result = {}
    for field in ("__VIEWSTATE", "__VIEWSTATEGENERATOR", "__EVENTVALIDATION"):
        m = re.search(
            rf'<input[^>]+name="{re.escape(field)}"[^>]+value="([^"]*)"',
            html,
            re.IGNORECASE,
        )
        if m:
            result[field] = m.group(1)
    return result


def _parse_faa_response(html: str) -> pd.DataFrame | None:
    """Parse HTML table from FAA response page."""
    try:
        tables = pd.read_html(io.StringIO(html))
        # Prefer the largest table
        if tables:
            df = max(tables, key=len)
            if len(df) > 0:
                return df
    except Exception:
        pass
    return None


def normalize_faa(df: pd.DataFrame) -> pd.DataFrame:
    """Rename FAA columns to standardized staging names."""
    df = df.copy()
    # Normalize column names
    df.columns = [str(c).strip() for c in df.columns]
    df = df.rename(columns={k: v for k, v in FAA_RENAME.items() if k in df.columns})

    # Ensure all required columns exist (fill missing with NaN)
    for col in REQUIRED_OUT_COLS:
        if col not in df.columns:
            df[col] = pd.NA

    # Keep only required columns
    df = df[REQUIRED_OUT_COLS].copy()

    if "scheduled_departure_date" in df.columns:
        df["scheduled_departure_date"] = pd.to_datetime(
            df["scheduled_departure_date"], errors="coerce"
        )

    return df


def main():
    parser = argparse.ArgumentParser(description="Extract FAA ASPM cancellation-with-weather data")
    parser.add_argument("--routes", default="config/routes.yaml")
    parser.add_argument("--study", default="config/study.yaml")
    parser.add_argument("--out", default="data/staging/faa_cancel_weather.csv")
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

    raw_dir.mkdir(parents=True, exist_ok=True)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    routes, study = load_config(routes_path, study_path)
    pairs = all_route_pairs(routes)
    start = study["study_start"]
    end = study["study_end"]

    log.info(f"Route pairs to query: {pairs}")

    all_frames: list[pd.DataFrame] = []
    session = requests.Session()

    for leg in pairs:
        origin = leg["origin"]
        dest = leg["dest"]
        slug = f"{origin}_{dest}_{start}_{end}"
        raw_file = raw_dir / f"faa_cancel_weather_{slug}.csv"

        if raw_file.exists() and not args.force:
            log.info(f"  Using cached {raw_file.name}")
            df_raw = pd.read_csv(raw_file, dtype=str)
        else:
            df_raw = fetch_faa_cancel_weather(origin, dest, start, end, session)
            if df_raw.empty:
                log.warning(f"  No data returned for {origin}→{dest}; writing empty file.")
                df_raw = pd.DataFrame(columns=list(FAA_RENAME.values()))

            df_raw.to_csv(raw_file, index=False)
            append_manifest(manifest_path, {
                "source": "FAA_ASPM",
                "filename": raw_file.name,
                "rows": len(df_raw),
                "extracted_at": datetime.now(timezone.utc).isoformat(),
                "checksum": checksum(raw_file),
                "params": f"origin={origin},dest={dest},start={start},end={end}",
            })
            time.sleep(2)

        normalized = normalize_faa(df_raw)
        # Tag with route for traceability
        normalized["departure_airport"] = normalized["departure_airport"].fillna(origin)
        normalized["arrival_airport"] = normalized["arrival_airport"].fillna(dest)
        all_frames.append(normalized)

    if not all_frames:
        log.error("No FAA data extracted.")
        sys.exit(1)

    staging = pd.concat(all_frames, ignore_index=True)
    staging = staging.drop_duplicates()
    staging.to_csv(out_path, index=False)
    log.info(f"FAA staging written: {out_path}  ({len(staging):,} rows)")

    # QA
    log.info("=== FAA Staging QA ===")
    log.info(f"  Total cancelled-with-weather records: {len(staging):,}")
    if "carrier_code" in staging.columns:
        log.info(f"  Carriers: {sorted(staging['carrier_code'].dropna().unique())}")
    null_rate = staging.isnull().mean().mean()
    log.info(f"  Overall null rate: {null_rate:.2%}")


if __name__ == "__main__":
    main()
