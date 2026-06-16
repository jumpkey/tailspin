#!/usr/bin/env bash
# run_pipeline_iv.sh — Single-command entry point for the Fragility IV
# (operator attribution) pipeline.
#
# Kept separate from run_pipeline.sh per the project's Module A/B and
# phase-decoupling convention (see flight_fragility_iv_operator_attribution_spec.md,
# "Architecture and build location"). Module A reuses the existing
# data/curated/flight_operability_fact.csv, so run_pipeline.sh must have
# already been run at least once before this script.
#
# Usage:
#   bash scripts/run_pipeline_iv.sh [--force] [--run-mode test|local|bigrun] [--study-override <path>]
#
# Flags:
#   --force              Re-download raw data even if cached files exist
#   --run-mode            Override study.yaml's run_mode for this invocation
#   --study-override      Use an alternate study.yaml path

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$ROOT_DIR"

FORCE_FLAG=""
RUN_MODE_FLAG=""
STUDY_FILE="config/study.yaml"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --force)          FORCE_FLAG="--force" ; shift ;;
    --run-mode)        RUN_MODE_FLAG="--run-mode $2" ; shift 2 ;;
    --study-override)  STUDY_FILE="$2" ; shift 2 ;;
    *) echo "Unknown arg: $1" >&2 ; exit 1 ;;
  esac
done

echo "========================================"
echo "  Fragility IV Pipeline (Operator Attribution)"
echo "  Study config: $STUDY_FILE"
echo "  Force refresh: ${FORCE_FLAG:-no}"
echo "========================================"

if [[ ! -f "data/curated/flight_operability_fact.csv" ]]; then
  echo "[run_pipeline_iv] ERROR: data/curated/flight_operability_fact.csv not found." >&2
  echo "  Module A reuses the Fragility I-III fact table — run scripts/run_pipeline.sh first." >&2
  exit 1
fi

echo ""
echo "[00] Setting up directories..."
bash scripts/00_setup_dirs.sh

echo ""
echo "[13] Extracting BTS On-Time Performance (hub-spoke, Module B)..."
python scripts/13_extract_bts_hubspoke.py --study "$STUDY_FILE" $RUN_MODE_FLAG $FORCE_FLAG

echo ""
echo "[14] Extracting NOAA ASOS weather (hub-spoke, Module B)..."
python scripts/14_extract_weather_hubspoke.py --study "$STUDY_FILE" $RUN_MODE_FLAG $FORCE_FLAG

echo ""
echo "[15] Targeted FlightAware operator-ambiguity resolution (no-op without FLIGHTAWARE_API_KEY)..."
python scripts/15_resolve_operator_ambiguity.py --study "$STUDY_FILE" || true

echo ""
echo "[21] Building hub-spoke operator fact table (Module B)..."
python scripts/21_build_hubspoke_fact.py --study "$STUDY_FILE"

echo ""
echo "[33] Analyzing Fragility IV operator attribution (Module A + B)..."
python scripts/33_analyze_fragility_operator.py --study "$STUDY_FILE"

echo ""
echo "[43] Rendering Fragility IV executive chart and summary..."
python scripts/43_plot_fragility_operator.py

echo ""
echo "========================================"
echo "  Fragility IV pipeline complete."
echo "  Outputs:"
echo "    data/curated/hubspoke_operator_fact/"
echo "    output/qa_summary_hubspoke.csv"
echo "    output/fragility_iv_operator_chart_data.csv"
echo "    output/fragility_iv_operator_scorecard.parquet"
echo "    output/fragility_iv_summary.json"
echo "    output/fragility_iv_operator_exec_chart.png"
echo "    output/fragility_iv_summary.md"
echo "========================================"
