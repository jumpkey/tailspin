#!/usr/bin/env python3
"""
14_extract_weather_hubspoke.py — Extract hourly airport weather for the
Fragility IV/V hub-spoke airport universe (Module B).

Unlike 11_extract_faa_weather.py, which uses a hand-maintained
airport->ICAO-station/timezone table for the original 9 study airports,
this script resolves both fields dynamically via the `airportsdata`
reference table (IATA -> ICAO/tz/lat/lon, no network call, no hand
enumeration) for whatever spoke airports
13_extract_bts_hubspoke.py discovered. This keeps the hub-spoke expansion
consistent with the study's ab-initio framing — it does not require
deciding in advance which spoke airports exist.

Same NOAA IEM ASOS source, weather-bucket thresholds, and airport-hour
join keys as 11_extract_faa_weather.py; kept as a separate script (not
parameterized into 11) so 11 and its 9-airport cache stay untouched for
Fragility I-III reproducibility.

The NOAA IEM ASOS request is chunked by calendar month rather than fired
once for the whole study window: a single request spanning the full
multi-year `local`/`bigrun` window against the full discovered-airport
station list would be tens of times larger than anything validated at
`test` scale (1 station-month vs. potentially 50-100+ station-months),
risking either a request timeout or the free IEM service choking on an
oversized ask. Chunking keeps each individual request close to the
already-validated size and makes a partial run resumable (cached
per-month files, same pattern as 13_extract_bts_hubspoke.py).

Outputs
-------
data/raw/faa_hubspoke/noaa_asos_raw_YYYY_MM.csv  Raw NOAA ASOS download (per month, cached)
data/staging/weather_hubspoke_hourly.csv         Normalized hourly weather per airport
data/raw/faa_hubspoke/manifest.csv               Audit log

Usage
-----
python scripts/14_extract_weather_hubspoke.py --study config/study.yaml \\
    --airports data/raw/bts_hubspoke/discovered_airports.csv [--force]
"""

import argparse
import calendar
import csv
import hashlib
import io
import logging
import time
from datetime import datetime, timezone
from pathlib import Path

import airportsdata
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

IEM_ASOS_URL = "https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py"

# Same thresholds as 11_extract_faa_weather.py — see that script's header
# comment for the rationale (ASPM-era IFR/MVFR/VFR equivalents).
ADVERSE_VIS_SM = 1.0
ADVERSE_CEIL_FT = 500.0
MARGINAL_VIS_SM = 3.0
MARGINAL_CEIL_FT = 1000.0

ADVERSE_WX_TOKENS = frozenset(["TS", "FZ", "BLSN", "+SN", "+RASN", "FC"])
MARGINAL_WX_TOKENS = frozenset(["RA", "SN", "RASN", "DZ", "FG", "MIFG", "BR", "GS", "PL"])


def load_study(study_path: Path) -> dict:
    with open(study_path) as f:
        return yaml.safe_load(f)


def resolve_window(study: dict, run_mode_override: str | None) -> tuple[str, str, str]:
    """Same run_mode scoping as 13_extract_bts_hubspoke.py's resolve_scope(),
    so the weather pull covers the same window as the BTS extract it's
    joined against rather than defaulting to the full multi-year study
    window regardless of run_mode."""
    run_mode = run_mode_override or study.get("run_mode", "test")
    window = study.get("run_mode_window", {}).get(run_mode, {})
    start = window.get("start", study.get("study_start"))
    end = window.get("end", study.get("study_end"))
    return run_mode, start, end


def months_in_range(start: str, end: str):
    dt = datetime.strptime(start, "%Y-%m-%d")
    end_dt = datetime.strptime(end, "%Y-%m-%d")
    while dt <= end_dt:
        yield dt.year, dt.month
        dt += relativedelta(months=1)


def month_chunk_bounds(year: int, month: int, overall_start: str, overall_end: str) -> tuple[str, str]:
    """Clip a calendar month to the overall window, so each NOAA request
    covers at most one month. Unlike the BTS PREZIP source (whole-month
    files only), NOAA's request takes exact start/end dates, so there's no
    reason to over-fetch beyond the configured window at the edges."""
    first = datetime(year, month, 1)
    last = datetime(year, month, calendar.monthrange(year, month)[1])
    start_dt = max(first, datetime.strptime(overall_start, "%Y-%m-%d"))
    end_dt = min(last, datetime.strptime(overall_end, "%Y-%m-%d"))
    return start_dt.strftime("%Y-%m-%d"), end_dt.strftime("%Y-%m-%d")


def load_discovered_airports(airports_path: Path) -> list[str]:
    if not airports_path.exists():
        raise FileNotFoundError(
            f"Discovered-airport list not found: {airports_path}\n"
            "Run 13_extract_bts_hubspoke.py first."
        )
    df = pd.read_csv(airports_path)
    return sorted(df["airport"].dropna().astype(str).str.upper().unique())


def resolve_airport_refs(airports: list[str]) -> tuple[dict[str, str], dict[str, str]]:
    """Resolve IATA airport codes to ICAO station codes and IANA timezone
    names via the airportsdata reference table. Airports not found in the
    table (rare for US commercial airports) are dropped with a warning
    rather than guessed.
    """
    db = airportsdata.load("IATA")
    station_map: dict[str, str] = {}
    tz_map: dict[str, str] = {}
    missing = []
    for ap in airports:
        rec = db.get(ap)
        if rec is None or not rec.get("icao") or not rec.get("tz"):
            missing.append(ap)
            continue
        station_map[ap] = rec["icao"]
        tz_map[ap] = rec["tz"]
    if missing:
        log.warning(f"  No airportsdata entry for: {missing} — excluded from weather join")
    return station_map, tz_map


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


def fetch_noaa_asos(stations: list[str], start: str, end: str, session: requests.Session) -> pd.DataFrame:
    """Download hourly METAR observations from the IEM ASOS archive."""
    log.info(f"  Requesting NOAA ASOS data for {len(stations)} stations {start} -> {end} ...")
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
        "report_type": "3",
    }
    param_list = []
    for k, v in params.items():
        if isinstance(v, list):
            for item in v:
                param_list.append(("data", item))
        else:
            param_list.append((k, v))
    for stn in stations:
        param_list.append(("station", stn))

    resp = session.get(IEM_ASOS_URL, params=param_list, timeout=600)
    resp.raise_for_status()

    text = resp.text
    data_lines = [ln for ln in text.splitlines() if not ln.startswith("#")]
    if not data_lines:
        raise ValueError("NOAA ASOS returned no data")

    df = pd.read_csv(io.StringIO("\n".join(data_lines)), dtype=str, low_memory=False)
    log.info(f"  NOAA ASOS raw rows: {len(df):,}")
    return df


def _derive_ceiling(row: pd.Series) -> float | None:
    for i in range(1, 5):
        cov = str(row.get(f"skyc{i}", "M") or "M").strip().upper()
        ht_str = str(row.get(f"skyl{i}", "M") or "M").strip()
        if cov in ("BKN", "OVC", "OVX"):
            try:
                return float(ht_str)
            except ValueError:
                pass
    return None


def classify_weather_bucket(vsby_sm: float | None, ceiling_ft: float | None, wxcodes: str) -> str:
    wx = str(wxcodes or "").upper()
    if any(tok in wx for tok in ADVERSE_WX_TOKENS):
        return "adverse"
    if vsby_sm is not None and vsby_sm < ADVERSE_VIS_SM:
        return "adverse"
    if ceiling_ft is not None and ceiling_ft < ADVERSE_CEIL_FT:
        return "adverse"
    if any(tok in wx for tok in MARGINAL_WX_TOKENS):
        return "marginal"
    if vsby_sm is not None and vsby_sm < MARGINAL_VIS_SM:
        return "marginal"
    if ceiling_ft is not None and ceiling_ft < MARGINAL_CEIL_FT:
        return "marginal"
    return "benign"


def normalize_noaa(df: pd.DataFrame, station_to_airport: dict[str, str], tz_map: dict[str, str]) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()

    df = df.copy()
    df["airport_code"] = df["station"].str.upper().map(
        lambda s: station_to_airport.get(s, station_to_airport.get("K" + s, s))
    )

    df["obs_utc"] = pd.to_datetime(df["valid"], errors="coerce", utc=True)
    df = df.dropna(subset=["obs_utc"])
    df["obs_date_utc"] = df["obs_utc"].dt.date.astype(str)
    df["obs_hour_utc"] = df["obs_utc"].dt.hour

    df["visibility_sm"] = pd.to_numeric(df["vsby"].replace("M", None), errors="coerce")
    df["wind_kt"] = pd.to_numeric(df["sknt"].replace("M", None), errors="coerce")
    df["ceiling_ft"] = df.apply(_derive_ceiling, axis=1)
    df["wxcodes"] = df["wxcodes"].replace("M", "").fillna("")

    df["weather_bucket_raw"] = df.apply(
        lambda r: classify_weather_bucket(r["visibility_sm"], r["ceiling_ft"], r["wxcodes"]),
        axis=1,
    )

    bucket_rank = {"adverse": 2, "marginal": 1, "benign": 0}

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
    hourly["tz_name"] = hourly["airport_code"].map(tz_map).fillna("America/Chicago")

    log.info(f"  Normalized to {len(hourly):,} airport-hour rows")
    return hourly


def main():
    parser = argparse.ArgumentParser(description="Extract NOAA ASOS weather for the hub-spoke airport universe")
    parser.add_argument("--study", default="config/study.yaml")
    parser.add_argument("--run-mode", default=None, help="Override study.yaml's run_mode")
    parser.add_argument("--airports", default="data/raw/bts_hubspoke/discovered_airports.csv")
    parser.add_argument("--out", default="data/staging/weather_hubspoke_hourly.csv")
    parser.add_argument("--raw-dir", default="data/raw/faa_hubspoke")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    script_dir = Path(__file__).parent
    root = script_dir.parent
    study_path = root / args.study
    airports_path = root / args.airports
    out_path = root / args.out
    raw_dir = root / args.raw_dir
    manifest_path = raw_dir / "manifest.csv"

    raw_dir.mkdir(parents=True, exist_ok=True)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    study = load_study(study_path)
    run_mode, start, end = resolve_window(study, args.run_mode)

    airports = load_discovered_airports(airports_path)
    station_map, tz_map = resolve_airport_refs(airports)
    stations = sorted(station_map.values())
    station_to_airport = {v: k for k, v in station_map.items()}
    station_to_airport.update({v[1:]: k for k, v in station_map.items()})

    log.info(f"run_mode={run_mode}  window={start}..{end}")
    log.info(f"Hub-spoke airport universe: {len(airports)} airports, {len(stations)} ASOS stations")

    session = requests.Session()
    normalized_chunks: list[pd.DataFrame] = []

    for year, month in months_in_range(start, end):
        chunk_start, chunk_end = month_chunk_bounds(year, month, start, end)
        # Cache filename is keyed by run_mode, not just year/month, for the
        # same reason as 13_extract_bts_hubspoke.py: different run_modes
        # resolve to different discovered-airport/station lists, so a
        # year_month-only key would silently reuse a cache built for the
        # wrong station set.
        raw_file = raw_dir / f"noaa_asos_raw_{run_mode}_{year}_{month:02d}.csv"

        if raw_file.exists() and not args.force:
            log.info(f"  Using cached {raw_file.name}")
            df_raw = pd.read_csv(raw_file, dtype=str, low_memory=False)
        else:
            try:
                df_raw = fetch_noaa_asos(stations, chunk_start, chunk_end, session)
                df_raw.to_csv(raw_file, index=False)
                append_manifest(manifest_path, {
                    "source": "NOAA_ASOS_IEM_hubspoke",
                    "filename": raw_file.name,
                    "rows": len(df_raw),
                    "extracted_at": datetime.now(timezone.utc).isoformat(),
                    "checksum": checksum(raw_file),
                    "params": f"stations={stations},start={chunk_start},end={chunk_end}",
                })
                log.info(f"  Raw NOAA chunk saved: {raw_file} ({len(df_raw):,} rows)")
                time.sleep(1)
            except Exception as exc:
                log.warning(f"  NOAA fetch failed for {year}-{month:02d}: {exc}")
                continue

        chunk_normalized = normalize_noaa(df_raw, station_to_airport, tz_map)
        if not chunk_normalized.empty:
            normalized_chunks.append(chunk_normalized)

    if not normalized_chunks:
        log.error("No NOAA ASOS data after normalization.")
        raise SystemExit(1)

    staging = pd.concat(normalized_chunks, ignore_index=True)
    staging.to_csv(out_path, index=False)
    log.info(f"Weather staging written: {out_path} ({len(staging):,} rows)")

    log.info("=== Hub-Spoke Weather QA ===")
    log.info(f"  Airports covered: {sorted(staging['airport_code'].unique())}")
    log.info(f"  Date range: {staging['obs_date_utc'].min()} -> {staging['obs_date_utc'].max()}")
    bucket_counts = staging["weather_bucket"].value_counts()
    for bucket, n in bucket_counts.items():
        pct = n / len(staging) * 100
        log.info(f"  {bucket:10s}: {n:>7,} hours  ({pct:.1f}%)")


if __name__ == "__main__":
    main()
