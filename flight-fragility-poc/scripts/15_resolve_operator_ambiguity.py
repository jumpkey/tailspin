#!/usr/bin/env python3
"""
15_resolve_operator_ambiguity.py — Targeted FlightAware AeroAPI validation
for OO (SkyWest) / YX (Republic) flights that route-context inference
cannot resolve.

scripts/lib/operator_classify.py resolves most OO/YX rows for free: if a
flight's route already belongs to a pre-validated basket (aa_regional_basket
/ ua_peer_basket / dl_peer_basket), that basket assignment already implies
which mainline brand SkyWest or Republic operated under on that route. In
practice this resolves ~100% of Module A (focal corridor) OO rows, because
every Module A route already belongs to one of those baskets. It resolves
none of Module B (hub-spoke expansion), because hub-spoke routes are
discovered from the data and were never assigned to a basket.

This script picks up exactly the remainder: OO/YX rows still carrying the
unresolved fallback label (SkyWest_unresolved / Republic_unresolved) after
route-context inference. For each *unique* (carrier_code, flight_number,
flight_date) instance, it queries AeroAPI's historical single-flight lookup
(GET /history/flights/{ident}) and inspects the returned codeshares for an
AA/UA/DL/AS-prefixed identifier — whichever mainline brand codeshares that
specific flight on that specific day is the contract it operated under.
This is a targeted, per-flight validation query, not a bulk historical
pull, consistent with config/study.yaml's flightaware_mode:
"validation_only" and with AeroAPI's free-tier volume limits.

Guarded by (any one false/absent => no-op, writes an empty resolution file
so apply_resolution_overrides() and the rest of the pipeline never depend
on a live key being present):
  - FLIGHTAWARE_API_KEY environment variable
  - config/study.yaml: resolve_operator_ambiguity.enabled
  - at least one unresolved OO/YX row found in the curated fact table(s)

A query budget (config/study.yaml: resolve_operator_ambiguity.max_queries)
caps API calls per run; unresolved instances beyond the budget are left
unresolved (logged), not guessed.

Note on response schema: AeroAPI v4's documented response fields for
codeshares have shifted across versions (see FlightAware's AeroAPI v4
migration notes). This script checks both "codeshares_iata" and
"codeshares" defensively and treats an unparseable response as still
unresolved rather than guessing or raising — verify field names against a
live key before relying on a high resolution rate.

Outputs
-------
data/raw/flightaware_resolution/<ident>_<date>.json   Per-flight raw cache
data/staging/operator_resolution.csv                  Resolved overrides
data/raw/flightaware_resolution/manifest.csv          Audit log

Usage
-----
python scripts/15_resolve_operator_ambiguity.py --study config/study.yaml [--force]
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

sys.path.insert(0, str(Path(__file__).parent))
from lib.backend import read_table  # noqa: E402
from lib.operator_classify import classify_operator, load_operator_classes  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
log = logging.getLogger(__name__)

FA_BASE = "https://aeroapi.flightaware.com/aeroapi"

AMBIGUOUS_CODES = ("OO", "YX")
UNRESOLVED_LABELS = {"OO": "SkyWest_unresolved", "YX": "Republic_unresolved"}

# Mirrors lib/operator_classify.py's f"{code}_{contract_label}" naming, e.g.
# "OO_AA_contract", extended with Alaska_contract for SkyWest's fourth brand
# (Republic has no Alaska Airlines contract, so a YX/Alaska_contract row
# would itself be a signal something is wrong, not a valid resolution).
CODESHARE_PREFIX_TO_CONTRACT = {
    "AA": "AA_contract",
    "UA": "UA_contract",
    "DL": "DL_contract",
    "AS": "Alaska_contract",
}

KEY_COLS = ["flight_date", "carrier_code", "flight_number", "origin", "dest"]


def load_study(study_path: Path) -> dict:
    with open(study_path) as f:
        return yaml.safe_load(f)


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


def collect_unresolved(root: Path, operator_config: dict) -> pd.DataFrame:
    """Classify operator_class on every available curated fact table and
    return the rows still carrying an unresolved fallback label."""
    frames = []

    focal_path = root / "data/curated/flight_operability_fact.csv"
    if focal_path.exists():
        focal = pd.read_csv(focal_path, dtype=str)
        if "carrier_code" in focal.columns:
            focal = classify_operator(focal, operator_config, route_basket_col="market_bucket")
            frames.append(focal)

    hubspoke_path = root / "data/curated/hubspoke_operator_fact"
    if hubspoke_path.exists() and any(hubspoke_path.rglob("*.parquet")):
        hubspoke = read_table(hubspoke_path, backend="pandas")
        if "carrier_code" in hubspoke.columns:
            hubspoke = classify_operator(hubspoke, operator_config, route_basket_col=None)
            frames.append(hubspoke)

    if not frames:
        return pd.DataFrame(columns=KEY_COLS + ["operator_class"])

    combined = pd.concat(frames, ignore_index=True)
    unresolved_mask = combined["operator_class"].isin(UNRESOLVED_LABELS.values())
    unresolved = combined.loc[unresolved_mask, [c for c in KEY_COLS if c in combined.columns] + ["operator_class"]].copy()
    unresolved = unresolved.dropna(subset=["flight_date", "carrier_code", "flight_number"])
    return unresolved


def fetch_flight_history(ident: str, flight_date: str, api_key: str, session: requests.Session) -> dict:
    """GET /history/flights/{ident} scoped to one UTC day around flight_date."""
    url = f"{FA_BASE}/history/flights/{ident}"
    start_dt = datetime.strptime(flight_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    end_dt = start_dt + timedelta(days=1)
    params = {
        "start": start_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "end": end_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    headers = {"x-apikey": api_key}
    resp = session.get(url, params=params, headers=headers, timeout=30)
    if resp.status_code == 404:
        return {}
    resp.raise_for_status()
    return resp.json()


def resolve_brand_from_response(data: dict, carrier_code: str, flight_date: str) -> str | None:
    """Inspect the response's codeshares for an AA/UA/DL/AS-prefixed ident.
    Returns a resolved_operator_class label, or None if unresolvable.

    Prefix matching requires the 2-char carrier code to be immediately followed
    by a digit (IATA flight-number format), preventing "AS1234" from matching
    "ASA..." or other longer codes that happen to start with the same two letters.

    If codeshares contain more than one recognizable mainline prefix (multi-brand
    conflict), the response is treated as unresolvable and None is returned.

    Date filtering uses the first available timestamp field; if no date context
    is available the flight entry is skipped rather than risked as a wrong-day
    match.
    """
    flights = data.get("flights", []) if isinstance(data, dict) else []
    for f in flights:
        # Try several timestamp fields in priority order before giving up on date context
        sched = (f.get("scheduled_out") or f.get("scheduled_off")
                 or f.get("estimated_out") or f.get("estimated_off")
                 or f.get("actual_out") or f.get("actual_off") or "")
        if not sched or not sched.startswith(flight_date):
            # Skip flight entries where we can't confirm the date — safer than
            # risking a wrong-day codeshare match
            continue
        candidates = list(f.get("codeshares_iata") or []) + list(f.get("codeshares") or [])
        matched_contracts: set[str] = set()
        for ident in candidates:
            ident = str(ident).strip().upper()
            for prefix, contract in CODESHARE_PREFIX_TO_CONTRACT.items():
                # Require a digit immediately after the 2-char prefix to avoid
                # false matches on longer codes (e.g. "ASA..." matching "AS")
                if (ident.startswith(prefix)
                        and len(ident) > len(prefix)
                        and ident[len(prefix)].isdigit()):
                    matched_contracts.add(f"{carrier_code}_{contract}")
        if len(matched_contracts) == 1:
            return matched_contracts.pop()
        if len(matched_contracts) > 1:
            log.warning(
                f"  Multi-brand conflict for {carrier_code} on {flight_date}: "
                f"{sorted(matched_contracts)} — leaving unresolved"
            )
    return None


def main():
    parser = argparse.ArgumentParser(description="Targeted FlightAware validation for ambiguous OO/YX flights")
    parser.add_argument("--study", default="config/study.yaml")
    parser.add_argument("--raw-dir", default="data/raw/flightaware_resolution")
    parser.add_argument("--out", default="data/staging/operator_resolution.csv")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    script_dir = Path(__file__).parent
    root = script_dir.parent
    study_path = root / args.study
    raw_dir = root / args.raw_dir
    out_path = root / args.out
    manifest_path = raw_dir / "manifest.csv"

    raw_dir.mkdir(parents=True, exist_ok=True)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    study = load_study(study_path)
    resolve_cfg = study.get("resolve_operator_ambiguity", {})
    operator_config = load_operator_classes(root / study.get("operator_classes_config", "config/operator_classes.yaml"))

    resolution_cols = KEY_COLS + ["resolved_operator_class"]

    if not resolve_cfg.get("enabled", False):
        log.info("resolve_operator_ambiguity.enabled is false in study.yaml — skipping.")
        pd.DataFrame(columns=resolution_cols).to_csv(out_path, index=False)
        return

    api_key = os.environ.get("FLIGHTAWARE_API_KEY", "")
    if not api_key:
        log.info("FLIGHTAWARE_API_KEY not set — skipping targeted validation (writing empty resolution file).")
        pd.DataFrame(columns=resolution_cols).to_csv(out_path, index=False)
        return

    unresolved = collect_unresolved(root, operator_config)
    if unresolved.empty:
        log.info("No unresolved OO/YX rows found in curated fact table(s) — nothing to query.")
        pd.DataFrame(columns=resolution_cols).to_csv(out_path, index=False)
        return

    instances = (
        unresolved[KEY_COLS]
        .drop_duplicates()
        .sort_values(KEY_COLS)
        .reset_index(drop=True)
    )
    log.info(f"Unresolved rows: {len(unresolved):,}  ->  unique flight instances: {len(instances):,}")

    max_queries = resolve_cfg.get("max_queries", 200)
    if len(instances) > max_queries:
        log.warning(f"  Capping queries to max_queries={max_queries} (of {len(instances):,} unique instances)")
        instances = instances.head(max_queries)

    session = requests.Session()
    resolved_rows = []
    queried = 0

    for _, row in instances.iterrows():
        carrier_code = str(row["carrier_code"])
        flight_number = str(row["flight_number"]).split(".")[0]
        flight_date = str(row["flight_date"])[:10]
        ident = f"{carrier_code}{flight_number}"
        raw_file = raw_dir / f"{ident}_{flight_date}.json"

        if raw_file.exists() and not args.force:
            with open(raw_file) as fh:
                data = json.load(fh)
        else:
            try:
                data = fetch_flight_history(ident, flight_date, api_key, session)
                with open(raw_file, "w") as fh:
                    json.dump(data, fh)
                append_manifest(manifest_path, {
                    "source": "FlightAware_targeted_validation",
                    "filename": raw_file.name,
                    "rows": len(data.get("flights", [])) if isinstance(data, dict) else 0,
                    "extracted_at": datetime.now(timezone.utc).isoformat(),
                    "checksum": checksum(raw_file),
                    "params": f"ident={ident},date={flight_date}",
                })
                queried += 1
                time.sleep(0.5)
            except Exception as exc:
                log.warning(f"  FlightAware lookup failed for {ident} on {flight_date}: {exc}")
                continue

        resolved_class = resolve_brand_from_response(data, carrier_code, flight_date)
        if resolved_class:
            resolved_rows.append({
                "flight_date": flight_date,
                "carrier_code": carrier_code,
                "flight_number": flight_number,
                "origin": row["origin"],
                "dest": row["dest"],
                "resolved_operator_class": resolved_class,
            })

    resolution = pd.DataFrame(resolved_rows, columns=resolution_cols)
    resolution.to_csv(out_path, index=False)
    log.info(f"Operator-resolution staging written: {out_path} ({len(resolution):,} rows)")

    log.info("=== Targeted FlightAware Validation QA ===")
    log.info(f"  Unique unresolved instances: {len(instances):,}")
    log.info(f"  Queried this run:            {queried:,}")
    log.info(f"  Resolved:                    {len(resolution):,}")
    if len(instances) > 0:
        log.info(f"  Resolution rate (of queried): {len(resolution) / max(queried, 1):.1%}")
    if not resolution.empty:
        log.info(f"  Brand breakdown: {resolution['resolved_operator_class'].value_counts().to_dict()}")


if __name__ == "__main__":
    main()
