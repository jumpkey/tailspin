#!/usr/bin/env python3
"""
10_extract_bts.py — Extract BTS On-Time Performance data for the study period and route universe.

Outputs
-------
data/raw/bts/bts_YYYY_MM.csv   Monthly raw extracts (treated as immutable unless --force)
data/staging/bts_flights.csv   Normalized staging file with standard field names
data/raw/bts/manifest.csv      Audit log: row counts, timestamps, checksums, params

Usage
-----
python scripts/10_extract_bts.py \\
    --routes config/routes.yaml \\
    --study  config/study.yaml \\
    --out    data/staging/bts_flights.csv [--force]
"""

import argparse
import csv
import hashlib
import io
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests
import yaml
from dateutil.relativedelta import relativedelta

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# BTS TranStats field selection payload
# Ref: https://www.transtats.bts.gov/DL_SelectFields.aspx?gnoyr_VQ=FGJ&QO_fu146_anzr=b0-gvzr
# ---------------------------------------------------------------------------
BTS_BASE_URL = "https://www.transtats.bts.gov"
BTS_DL_URL = f"{BTS_BASE_URL}/DownLoad_Table.asp"

BTS_REQUIRED_FIELDS = [
    "FlightDate",
    "Reporting_Airline",
    "Operating_Airline",
    "Flight_Number_Reporting_Airline",
    "Origin",
    "Dest",
    "CRSDepTime",
    "DepTime",
    "CRSArrTime",
    "ArrTime",
    "DepDelay",
    "ArrDelay",
    "Cancelled",
    "CancellationCode",
    "Diverted",
    "Distance",
    "ActualElapsedTime",
    "CRSElapsedTime",
]

# BTS field-code mapping (numeric IDs needed by the download form)
BTS_FIELD_CODES = {
    "FlightDate": "10",
    "Reporting_Airline": "16",
    "Operating_Airline": "19",
    "Flight_Number_Reporting_Airline": "20",
    "Origin": "23",
    "Dest": "28",
    "CRSDepTime": "30",
    "DepTime": "31",
    "CRSArrTime": "40",
    "ArrTime": "41",
    "DepDelay": "32",
    "ArrDelay": "42",
    "Cancelled": "47",
    "CancellationCode": "48",
    "Diverted": "49",
    "Distance": "51",
    "ActualElapsedTime": "50",
    "CRSElapsedTime": "45",
}

# Staging column rename map: BTS name → normalized name
BTS_RENAME = {
    "FlightDate": "flight_date",
    "Reporting_Airline": "carrier_code",
    "Operating_Airline": "operating_carrier",
    "Flight_Number_Reporting_Airline": "flight_number",
    "Origin": "origin",
    "Dest": "dest",
    "CRSDepTime": "sched_dep_local",
    "DepTime": "actual_dep_local",
    "CRSArrTime": "sched_arr_local",
    "ArrTime": "actual_arr_local",
    "DepDelay": "dep_delay_min",
    "ArrDelay": "arr_delay_min",
    "Cancelled": "cancelled_flag",
    "CancellationCode": "cancellation_code_bts",
    "Diverted": "diverted_flag",
    "Distance": "distance_miles",
    "ActualElapsedTime": "actual_elapsed_min",
    "CRSElapsedTime": "scheduled_elapsed_min",
}


def load_config(routes_path: Path, study_path: Path):
    with open(routes_path) as f:
        routes = yaml.safe_load(f)
    with open(study_path) as f:
        study = yaml.safe_load(f)
    return routes, study


def collect_carriers(routes: dict) -> set:
    """Derive the set of marketing carriers implied by the basket config."""
    # AA regional basket → AA; UA peer → UA; DL peer → DL
    carriers = {"AA", "YX", "MQ", "OH", "OO", "9E", "YV", "G4"}  # AA + regionals
    carriers |= {"UA", "OO", "YX"}  # UA + regionals
    carriers |= {"DL", "9E", "OO"}  # DL + regionals
    return carriers


def collect_airports(routes: dict) -> set:
    airports: set = set()
    for basket in routes.values():
        if isinstance(basket, list):
            for leg in basket:
                airports.add(leg["origin"])
                airports.add(leg["dest"])
    return airports


def months_in_range(start: str, end: str):
    """Yield (year, month) tuples spanning start..end inclusive."""
    dt = datetime.strptime(start, "%Y-%m-%d")
    end_dt = datetime.strptime(end, "%Y-%m-%d")
    while dt <= end_dt:
        yield dt.year, dt.month
        dt += relativedelta(months=1)


def checksum(path: Path) -> str:
    sha = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha.update(chunk)
    return sha.hexdigest()[:16]


def fetch_bts_month(year: int, month: int, airports: set, session: requests.Session) -> pd.DataFrame:
    """
    Attempt a direct HTTP POST to the BTS TranStats download endpoint.
    Returns a DataFrame of raw rows filtered to the airport universe.

    BTS TranStats uses a form-based download. We POST the field selection
    with year/month parameters and parse the returned ZIP or CSV.
    """
    log.info(f"  Fetching BTS data for {year}-{month:02d} ...")

    # Build form payload matching TranStats download form structure
    field_list = ",".join(BTS_FIELD_CODES[f] for f in BTS_REQUIRED_FIELDS)
    payload = {
        "UserTableName": "On_Time_Reporting_Carrier_On_Time_Performance_1987_present",
        "DBShortName": "On_Time",
        "RawDataTable": "T_ONTIME_REPORTING",
        "sqlstr": (
            f"SELECT {','.join(BTS_REQUIRED_FIELDS)} "
            f"FROM T_ONTIME_REPORTING "
            f"WHERE YEAR={year} AND MONTH={month}"
        ),
        "varlist": field_list,
        "grouplist": "",
        "suml": "",
        "sumRegion": "",
        "filter1": "title=",
        "filter2": "title=",
        "geo": "All",
        "time": f"{year}/{month}",
        "timename": "FlightDate",
        "GEOGRAPHY": "All",
        "XYEAR": str(year),
        "FREQUENCY": str(month),
        "VarDesc": "FlightDate",
        "VarType": "Num",
        "VarDesc2": "",
        "VarType2": "",
        "Category": "On-time",
        "Submit": "Download",
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; FlightFragilityPOC/1.0; +https://github.com/jumpkey/tailspin)",
        "Referer": "https://www.transtats.bts.gov/DL_SelectFields.aspx",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    resp = session.post(BTS_DL_URL, data=payload, headers=headers, timeout=120)
    resp.raise_for_status()

    content_type = resp.headers.get("Content-Type", "")
    if "zip" in content_type or resp.content[:2] == b"PK":
        import zipfile
        zf = zipfile.ZipFile(io.BytesIO(resp.content))
        csv_name = next(n for n in zf.namelist() if n.endswith(".csv"))
        raw = pd.read_csv(zf.open(csv_name), dtype=str)
    else:
        raw = pd.read_csv(io.StringIO(resp.text), dtype=str)

    # Filter to our airport universe (origin or destination)
    if airports:
        mask = raw["Origin"].isin(airports) | raw["Dest"].isin(airports)
        raw = raw[mask].copy()

    return raw


def normalize_bts(df: pd.DataFrame) -> pd.DataFrame:
    """Rename and cast BTS columns to standard staging schema."""
    # Keep only columns we asked for
    present = [c for c in BTS_REQUIRED_FIELDS if c in df.columns]
    df = df[present].copy()
    df = df.rename(columns={k: v for k, v in BTS_RENAME.items() if k in df.columns})

    # Type coercions
    numeric_cols = [
        "dep_delay_min", "arr_delay_min", "distance_miles",
        "actual_elapsed_min", "scheduled_elapsed_min",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    for flag in ("cancelled_flag", "diverted_flag"):
        if flag in df.columns:
            df[flag] = pd.to_numeric(df[flag], errors="coerce").fillna(0).astype(int)

    if "flight_date" in df.columns:
        df["flight_date"] = pd.to_datetime(df["flight_date"], errors="coerce")

    return df


def append_manifest(manifest_path: Path, row: dict):
    write_header = not manifest_path.exists() or manifest_path.stat().st_size == 0
    with open(manifest_path, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(row.keys()))
        if write_header:
            writer.writeheader()
        writer.writerow(row)


def main():
    parser = argparse.ArgumentParser(description="Extract BTS On-Time Performance data")
    parser.add_argument("--routes", default="config/routes.yaml")
    parser.add_argument("--study", default="config/study.yaml")
    parser.add_argument("--out", default="data/staging/bts_flights.csv")
    parser.add_argument("--raw-dir", default="data/raw/bts")
    parser.add_argument("--force", action="store_true", help="Re-download existing monthly files")
    args = parser.parse_args()

    # Resolve paths relative to project root (parent of scripts/)
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
    airports = collect_airports(routes)
    log.info(f"Airport universe: {sorted(airports)}")

    start = study["study_start"]
    end = study["study_end"]

    all_frames: list[pd.DataFrame] = []
    session = requests.Session()

    for year, month in months_in_range(start, end):
        raw_file = raw_dir / f"bts_{year}_{month:02d}.csv"

        if raw_file.exists() and not args.force:
            log.info(f"  Using cached {raw_file.name}")
            df_raw = pd.read_csv(raw_file, dtype=str)
        else:
            try:
                df_raw = fetch_bts_month(year, month, airports, session)
                df_raw.to_csv(raw_file, index=False)
                log.info(f"  Saved {len(df_raw):,} rows → {raw_file.name}")
            except Exception as exc:
                log.warning(f"  BTS fetch failed for {year}-{month:02d}: {exc}")
                log.warning("  Skipping month — run with --force to retry.")
                continue

            append_manifest(manifest_path, {
                "source": "BTS",
                "filename": raw_file.name,
                "rows": len(df_raw),
                "extracted_at": datetime.now(timezone.utc).isoformat(),
                "checksum": checksum(raw_file),
                "params": f"year={year},month={month},airports={sorted(airports)}",
            })
            time.sleep(1)  # polite crawl delay

        normalized = normalize_bts(df_raw)
        all_frames.append(normalized)

    if not all_frames:
        log.error("No BTS data was extracted. Check network access and retry.")
        sys.exit(1)

    staging = pd.concat(all_frames, ignore_index=True)

    # Deduplicate
    key_cols = [c for c in ["flight_date", "carrier_code", "flight_number", "origin", "dest"]
                if c in staging.columns]
    before = len(staging)
    staging = staging.drop_duplicates(subset=key_cols)
    log.info(f"Deduplicated: {before:,} → {len(staging):,} rows")

    staging.to_csv(out_path, index=False)
    log.info(f"Staging file written: {out_path}  ({len(staging):,} rows)")

    # QA summary
    log.info("=== BTS Staging QA ===")
    if "flight_date" in staging.columns:
        log.info(f"  Date range: {staging['flight_date'].min()} .. {staging['flight_date'].max()}")
    if "carrier_code" in staging.columns:
        log.info(f"  Carriers: {sorted(staging['carrier_code'].dropna().unique())}")
    if "origin" in staging.columns:
        log.info(f"  Origins: {sorted(staging['origin'].dropna().unique())}")
    if "cancelled_flag" in staging.columns:
        cancel_rate = staging["cancelled_flag"].mean()
        log.info(f"  Overall cancellation rate: {cancel_rate:.2%}")


if __name__ == "__main__":
    main()
