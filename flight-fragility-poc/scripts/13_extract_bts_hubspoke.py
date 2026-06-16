#!/usr/bin/env python3
"""
13_extract_bts_hubspoke.py — Extract BTS On-Time Performance data for the
Fragility IV/V hub-spoke expansion (Module B).

Unlike 10_extract_bts.py, which is driven by a fixed route list
(config/routes.yaml baskets) and is left untouched to preserve Fragility
I-III reproducibility, this script is driven by a configurable hub list and
discovers the spoke-market universe directly from the data: every flight
touching a configured hub airport is retained, whatever the other endpoint
turns out to be. This avoids hand-enumerating spoke airports per hub.

Run mode controls scope (config/study.yaml: run_mode, run_mode_hubs,
run_mode_window) — see flight_fragility_iv_operator_attribution_spec.md,
"Architecture and build location."

Outputs
-------
data/raw/bts_hubspoke/bts_hubspoke_YYYY_MM.csv   Monthly raw extracts (cached)
data/staging/bts_hubspoke/                       Hive-partitioned Parquet, partitioned by year_month
data/raw/bts_hubspoke/manifest.csv               Audit log
data/raw/bts_hubspoke/discovered_airports.csv    Spoke-airport universe discovered this run

Usage
-----
python scripts/13_extract_bts_hubspoke.py --study config/study.yaml [--run-mode test|local|bigrun] [--force]
"""

import argparse
import csv
import hashlib
import io
import logging
import sys
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests
import yaml
from dateutil.relativedelta import relativedelta

sys.path.insert(0, str(Path(__file__).parent))
from lib.backend import write_partitioned_parquet  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
log = logging.getLogger(__name__)

BTS_PREZIP_URL = (
    "https://transtats.bts.gov/PREZIP/"
    "On_Time_Reporting_Carrier_On_Time_Performance_1987_present_{year}_{month}.zip"
)

# Same field selection as 10_extract_bts.py; kept separate rather than
# imported to avoid coupling the two extraction paths to a shared schema
# that one might evolve out from under the other.
BTS_REQUIRED_FIELDS = [
    "FlightDate", "Reporting_Airline", "Flight_Number_Reporting_Airline",
    "Origin", "Dest", "CRSDepTime", "DepTime", "CRSArrTime", "ArrTime",
    "DepDelay", "ArrDelay", "Cancelled", "CancellationCode", "Diverted",
    "Distance", "ActualElapsedTime", "CRSElapsedTime",
    "CarrierDelay", "WeatherDelay", "NASDelay", "SecurityDelay", "LateAircraftDelay",
]

BTS_RENAME = {
    "FlightDate": "flight_date",
    "Reporting_Airline": "carrier_code",
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
    "CarrierDelay": "carrier_delay_minutes",
    "WeatherDelay": "weather_delay_minutes",
    "NASDelay": "nas_delay_minutes",
    "SecurityDelay": "security_delay_minutes",
    "LateAircraftDelay": "late_aircraft_delay_minutes",
}


def load_study(study_path: Path) -> dict:
    with open(study_path) as f:
        return yaml.safe_load(f)


def resolve_scope(study: dict, run_mode_override: str | None) -> tuple[str, list[str], str, str]:
    run_mode = run_mode_override or study.get("run_mode", "test")
    hubs = study.get("run_mode_hubs", {}).get(run_mode, [])
    window = study.get("run_mode_window", {}).get(run_mode, {})
    start = window.get("start", study.get("study_start"))
    end = window.get("end", study.get("study_end"))
    if not hubs:
        raise ValueError(
            f"run_mode '{run_mode}' has no hubs configured in study.yaml "
            "run_mode_hubs (bigrun must set this explicitly before running)."
        )
    return run_mode, hubs, start, end


def months_in_range(start: str, end: str):
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


def append_manifest(manifest_path: Path, row: dict):
    write_header = not manifest_path.exists() or manifest_path.stat().st_size == 0
    with open(manifest_path, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(row.keys()))
        if write_header:
            writer.writeheader()
        writer.writerow(row)


def fetch_bts_month(year: int, month: int, hubs: list[str], session: requests.Session) -> pd.DataFrame:
    """Download a BTS PREZIP month and filter to flights touching any configured hub."""
    url = BTS_PREZIP_URL.format(year=year, month=month)
    log.info(f"  Downloading BTS PREZIP for {year}-{month:02d} ...")
    headers = {"User-Agent": "Mozilla/5.0 (compatible; FlightFragilityPOC/1.0)"}
    resp = session.get(url, headers=headers, timeout=300, stream=True)
    resp.raise_for_status()

    buf = io.BytesIO()
    for chunk in resp.iter_content(chunk_size=131072):
        buf.write(chunk)
    buf.seek(0)

    with zipfile.ZipFile(buf) as zf:
        csv_names = [n for n in zf.namelist() if n.endswith(".csv")]
        if not csv_names:
            raise ValueError(f"No CSV found in PREZIP for {year}-{month:02d}")
        raw = pd.read_csv(zf.open(csv_names[0]), dtype=str, low_memory=False)

    mask = raw["Origin"].isin(hubs) | raw["Dest"].isin(hubs)
    raw = raw[mask].copy()
    log.info(f"  {len(raw):,} rows touching hubs {hubs}")
    return raw


def normalize_bts(df: pd.DataFrame) -> pd.DataFrame:
    present = [c for c in BTS_REQUIRED_FIELDS if c in df.columns]
    df = df[present].copy()
    df = df.rename(columns={k: v for k, v in BTS_RENAME.items() if k in df.columns})

    numeric_cols = [
        "dep_delay_min", "arr_delay_min", "distance_miles",
        "actual_elapsed_min", "scheduled_elapsed_min",
        "carrier_delay_minutes", "weather_delay_minutes", "nas_delay_minutes",
        "security_delay_minutes", "late_aircraft_delay_minutes",
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


def main():
    parser = argparse.ArgumentParser(description="Extract BTS hub-spoke data for Fragility IV/V")
    parser.add_argument("--study", default="config/study.yaml")
    parser.add_argument("--run-mode", default=None, help="Override study.yaml's run_mode")
    parser.add_argument("--raw-dir", default="data/raw/bts_hubspoke")
    parser.add_argument("--out", default="data/staging/bts_hubspoke")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    script_dir = Path(__file__).parent
    root = script_dir.parent
    study_path = root / args.study
    raw_dir = root / args.raw_dir
    out_dir = root / args.out
    manifest_path = raw_dir / "manifest.csv"

    raw_dir.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)

    study = load_study(study_path)
    run_mode, hubs, start, end = resolve_scope(study, args.run_mode)
    log.info(f"run_mode={run_mode}  hubs={hubs}  window={start}..{end}")

    all_frames: list[pd.DataFrame] = []
    session = requests.Session()

    for year, month in months_in_range(start, end):
        # Cache filename is keyed by run_mode, not just year/month: different
        # run_modes filter the same calendar month to different hub sets
        # (e.g. test=DFW-only vs local=DFW+CLT+ORD+PHL), so a year_month-only
        # key would silently reuse a cache built for the wrong hub list.
        raw_file = raw_dir / f"bts_hubspoke_{run_mode}_{year}_{month:02d}.csv"

        if raw_file.exists() and not args.force:
            log.info(f"  Using cached {raw_file.name}")
            df_raw = pd.read_csv(raw_file, dtype=str)
        else:
            try:
                df_raw = fetch_bts_month(year, month, hubs, session)
                df_raw.to_csv(raw_file, index=False)
            except Exception as exc:
                log.warning(f"  BTS fetch failed for {year}-{month:02d}: {exc}")
                continue

            append_manifest(manifest_path, {
                "source": "BTS_hubspoke",
                "filename": raw_file.name,
                "rows": len(df_raw),
                "extracted_at": datetime.now(timezone.utc).isoformat(),
                "checksum": checksum(raw_file),
                "params": f"year={year},month={month},hubs={sorted(hubs)},run_mode={run_mode}",
            })
            time.sleep(1)

        normalized = normalize_bts(df_raw)
        normalized["year_month"] = normalized["flight_date"].dt.to_period("M").astype(str)
        normalized["hub_family"] = normalized.apply(
            lambda r: r["origin"] if r["origin"] in hubs else r["dest"], axis=1
        )
        all_frames.append(normalized)

    if not all_frames:
        log.error("No BTS hub-spoke data extracted. Check network access and retry.")
        sys.exit(1)

    staging = pd.concat(all_frames, ignore_index=True)
    key_cols = [c for c in ["flight_date", "carrier_code", "flight_number", "origin", "dest"]
                if c in staging.columns]
    before = len(staging)
    staging = staging.drop_duplicates(subset=key_cols)
    log.info(f"Deduplicated: {before:,} -> {len(staging):,} rows")

    write_partitioned_parquet(staging, out_dir, partition_cols=["year_month"])

    discovered_airports = sorted(set(staging["origin"]) | set(staging["dest"]))
    discovered_path = raw_dir / "discovered_airports.csv"
    pd.DataFrame({"airport": discovered_airports}).to_csv(discovered_path, index=False)
    log.info(f"Discovered {len(discovered_airports)} airports (hubs + spokes) "
             f"-> {discovered_path}")

    log.info("=== BTS Hub-Spoke Staging QA ===")
    log.info(f"  Run mode: {run_mode}  Hubs: {hubs}")
    log.info(f"  Total rows: {len(staging):,}")
    log.info(f"  Distinct airports touched: {len(discovered_airports)}")
    log.info(f"  Carriers present: {sorted(staging['carrier_code'].dropna().unique())}")


if __name__ == "__main__":
    main()
