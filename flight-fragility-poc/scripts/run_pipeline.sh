#!/usr/bin/env bash
# run_pipeline.sh — Single-command entry point for the flight fragility pipeline.
#
# Usage:
#   bash scripts/run_pipeline.sh [--force] [--skip-flightaware] [--study-override <path>]
#
# Flags:
#   --force              Re-download raw data even if cached files exist
#   --skip-flightaware   Skip the optional FlightAware extraction step
#   --study-override     Use an alternate study.yaml path

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$ROOT_DIR"

FORCE_FLAG=""
SKIP_FA=false
STUDY_FILE="config/study.yaml"

# Parse args
while [[ $# -gt 0 ]]; do
  case "$1" in
    --force)           FORCE_FLAG="--force" ; shift ;;
    --skip-flightaware) SKIP_FA=true ; shift ;;
    --study-override)  STUDY_FILE="$2" ; shift 2 ;;
    *) echo "Unknown arg: $1" >&2 ; exit 1 ;;
  esac
done

echo "========================================"
echo "  Flight Fragility Pipeline"
echo "  Study config: $STUDY_FILE"
echo "  Force refresh: ${FORCE_FLAG:-no}"
echo "========================================"

# Step 0 — Create directories and validate config
echo ""
echo "[00] Setting up directories..."
bash scripts/00_setup_dirs.sh

# Step 1 — Extract BTS On-Time Performance data
echo ""
echo "[10] Extracting BTS On-Time Performance..."
python scripts/10_extract_bts.py \
  --routes config/routes.yaml \
  --study  "$STUDY_FILE" \
  --out    data/staging/bts_flights.csv \
  $FORCE_FLAG

# Step 2 — Extract NOAA ASOS hourly airport weather (replaces FAA ASPM)
echo ""
echo "[11] Extracting NOAA ASOS hourly weather data..."
python scripts/11_extract_faa_weather.py \
  --routes config/routes.yaml \
  --study  "$STUDY_FILE" \
  --out    data/staging/airport_weather_hourly.csv \
  $FORCE_FLAG

# Step 3 — Optional: FlightAware AeroAPI extraction
if [[ "$SKIP_FA" == "false" ]]; then
  echo ""
  echo "[12] Running FlightAware extraction (optional — errors will not abort pipeline)..."
  python scripts/12_extract_flightaware.py \
    --routes config/routes.yaml \
    --study  "$STUDY_FILE" \
    $FORCE_FLAG || true
else
  echo ""
  echo "[12] Skipping FlightAware extraction (--skip-flightaware)"
fi

# Step 4 — Build integrated flight fact table
echo ""
echo "[20] Building flight fact table..."
python scripts/20_build_flight_fact.py \
  --routes config/routes.yaml \
  --study  "$STUDY_FILE" \
  --weather data/staging/airport_weather_hourly.csv

# Step 5 — Analyze fragility
echo ""
echo "[30] Analyzing fragility..."
python scripts/30_analyze_fragility.py \
  --study "$STUDY_FILE"

# Step 6 — Analyze Fragility II controllable/cascade aggregates
echo ""
echo "[31] Analyzing Fragility II controllable/cascade disruption..."
python scripts/31_analyze_fragility_machine.py \
  --study "$STUDY_FILE"

# Step 7 — Render Fragility I chart
echo ""
echo "[40] Rendering Fragility I executive chart..."
python scripts/40_plot_fragility.py

# Step 8 — Render Fragility II chart
echo ""
echo "[41] Rendering Fragility II executive chart..."
python scripts/41_plot_fragility_machine.py

echo ""
echo "========================================"
echo "  Pipeline complete."
echo "  Outputs:"
echo "    data/curated/flight_operability_fact.csv"
echo "    output/weather_fragility_chart_data.csv"
echo "    output/fragility_summary.json"
echo "    output/qa_summary.csv"
echo "    output/weather_fragility_exec_chart.png"
echo "    output/weather_fragility_machine_chart_data.csv"
echo "    output/fragility_ii_machine_summary.json"
echo "    output/fragility_ii_summary.md"
echo "    output/weather_fragility_machine_exec_chart.png"
echo "========================================"
