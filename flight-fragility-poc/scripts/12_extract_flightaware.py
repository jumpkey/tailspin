#!/usr/bin/env python3
"""
12_extract_flightaware.py — Optional FlightAware AeroAPI extraction (phase-2 validation layer).

This script is guarded by ``use_flightaware: false`` in study.yaml and is
NOT part of the phase-1 critical path.  It provides recency extension and
ATC-grounded validation for historical flight data.

Outputs
-------
data/raw/flightaware/<origin>_<dest>_<date>.json
data/staging/flightaware_history.csv
data/raw/flightaware/manifest.csv

Usage
-----
python scripts/12_extract_flightaware.py \\
    --routes config/routes.yaml \\
    --study  config/study.yaml [--force]

Requires
--------
FLIGHTAWARE_API_KEY environment variable (or .env file)
"""

import argparse
import csv
import hashlib
import json
import logging
import os
import sys
import time
from datetime import datetime, timedelta, timezone
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

FA_BASE = "https://aeroapi.flightaware.com/aeroapi"

FA_STAGING_COLS = [
    "flight_date",
    "carrier_code",
    "flight_number",
    "origin",
    "dest",
    "sched_dep_utc",
    "actual_dep_utc",
    "sched_arr_utc",
    "actual_arr_utc",
    "dep_delay_min",
    "arr_delay_min",
    "cancelled_flag",
    "diverted_flag",
    "distance_miles",
    "source",
]


def load_config(routes_path: Path, study_path: Path):
    with open(routes_path) as f:
        routes = yaml.safe_load(f)
    with open(study_path) as f:
        study = yaml.safe_load(f)
    return routes, study


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


def date_range(start: str, end: str):
    dt = datetime.strptime(start, "%Y-%m-%d")
    end_dt = datetime.strptime(end, "%Y-%m-%d")
    while dt <= end_dt:
        yield dt.strftime("%Y-%m-%d")
        dt += timedelta(days=1)


def fetch_route_history(
    origin: str,
    dest: str,
    date: str,
    api_key: str,
    session: requests.Session,
) -> list[dict]:
    """
    Fetch historical flights for a route on a given date using
    GET /history/airports/{id}/to/{dest}
    """
    url = f"{FA_BASE}/history/airports/{origin}/to/{dest}"
    params = {"date": date, "max_pages": 2}
    headers = {"x-apikey": api_key}
    resp = session.get(url, params=params, headers=headers, timeout=30)
    if resp.status_code == 404:
        return []
    resp.raise_for_status()
    data = resp.json()
    return data.get("flights", [])


def normalize_fa_flights(flights: list[dict], origin: str, dest: str) -> pd.DataFrame:
    rows = []
    for f in flights:
        ident = f.get("ident", "")
        carrier = ident[:2] if len(ident) >= 2 else ""
        fnum = ident[2:] if len(ident) > 2 else ""
        dep = f.get("actual_off") or f.get("actual_out") or ""
        sched_dep = f.get("scheduled_off") or f.get("scheduled_out") or ""
        arr = f.get("actual_on") or f.get("actual_in") or ""
        sched_arr = f.get("scheduled_on") or f.get("scheduled_in") or ""

        dep_delay = None
        if dep and sched_dep:
            try:
                dep_delay = (
                    datetime.fromisoformat(dep.rstrip("Z")) -
                    datetime.fromisoformat(sched_dep.rstrip("Z"))
                ).total_seconds() / 60
            except Exception:
                pass

        rows.append({
            "flight_date": sched_dep[:10] if sched_dep else None,
            "carrier_code": carrier,
            "flight_number": fnum,
            "origin": f.get("origin", {}).get("code", origin) if isinstance(f.get("origin"), dict) else origin,
            "dest": f.get("destination", {}).get("code", dest) if isinstance(f.get("destination"), dict) else dest,
            "sched_dep_utc": sched_dep,
            "actual_dep_utc": dep,
            "sched_arr_utc": sched_arr,
            "actual_arr_utc": arr,
            "dep_delay_min": dep_delay,
            "arr_delay_min": None,
            "cancelled_flag": int(f.get("cancelled", False)),
            "diverted_flag": int(f.get("diverted", False)),
            "distance_miles": None,
            "source": "flightaware",
        })
    return pd.DataFrame(rows, columns=FA_STAGING_COLS)


def main():
    parser = argparse.ArgumentParser(description="Extract FlightAware AeroAPI data (optional phase-2)")
    parser.add_argument("--routes", default="config/routes.yaml")
    parser.add_argument("--study", default="config/study.yaml")
    parser.add_argument("--out", default="data/staging/flightaware_history.csv")
    parser.add_argument("--raw-dir", default="data/raw/flightaware")
    parser.add_argument("--force", action="store_true")
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

    if not study.get("use_flightaware", False):
        log.info("use_flightaware is false in study.yaml — skipping FlightAware extraction.")
        # Write empty staging file so downstream scripts don't fail
        pd.DataFrame(columns=FA_STAGING_COLS).to_csv(out_path, index=False)
        sys.exit(0)

    api_key = os.environ.get("FLIGHTAWARE_API_KEY", "")
    if not api_key:
        log.error("FLIGHTAWARE_API_KEY not set. Export it or add to .env before running.")
        sys.exit(1)

    # Collect all route pairs
    pairs = []
    seen: set = set()
    for basket_legs in routes.values():
        if isinstance(basket_legs, list):
            for leg in basket_legs:
                k = (leg["origin"], leg["dest"])
                if k not in seen:
                    pairs.append(leg)
                    seen.add(k)

    start = study["study_start"]
    end = study["study_end"]

    all_frames: list[pd.DataFrame] = []
    session = requests.Session()

    for leg in pairs:
        origin, dest = leg["origin"], leg["dest"]
        for date in date_range(start, end):
            raw_file = raw_dir / f"{origin}_{dest}_{date}.json"
            if raw_file.exists() and not args.force:
                with open(raw_file) as fh:
                    flights = json.load(fh)
            else:
                try:
                    flights = fetch_route_history(origin, dest, date, api_key, session)
                    with open(raw_file, "w") as fh:
                        json.dump(flights, fh)
                    append_manifest(manifest_path, {
                        "source": "FlightAware",
                        "filename": raw_file.name,
                        "rows": len(flights),
                        "extracted_at": datetime.now(timezone.utc).isoformat(),
                        "checksum": checksum(raw_file),
                        "params": f"origin={origin},dest={dest},date={date}",
                    })
                    time.sleep(0.5)
                except Exception as exc:
                    log.warning(f"  FA fetch failed {origin}→{dest} {date}: {exc}")
                    flights = []

            if flights:
                df = normalize_fa_flights(flights, origin, dest)
                all_frames.append(df)

    if all_frames:
        staging = pd.concat(all_frames, ignore_index=True)
    else:
        staging = pd.DataFrame(columns=FA_STAGING_COLS)

    staging.to_csv(out_path, index=False)
    log.info(f"FlightAware staging written: {out_path}  ({len(staging):,} rows)")


if __name__ == "__main__":
    main()
