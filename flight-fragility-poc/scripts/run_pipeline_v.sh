#!/usr/bin/env bash
# run_pipeline_v.sh — Fragility V: network hotspot engine pipeline.
# Prereq: run_pipeline_iv.sh must have run first (reads IV curated layer).
# Usage: bash scripts/run_pipeline_v.sh [--run-mode test|local|bigrun] [--study-override <path>]

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$ROOT_DIR"

STUDY_FILE="config/study.yaml"
RUN_MODE_FLAG=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --run-mode)       RUN_MODE_FLAG="--run-mode $2"; shift 2 ;;
    --study-override) STUDY_FILE="$2"; shift 2 ;;
    *) echo "Unknown arg: $1" >&2; exit 1 ;;
  esac
done

# Check IV curated layer exists
if [[ ! -d "data/curated/hubspoke_operator_fact" ]]; then
  echo "[run_pipeline_v] ERROR: data/curated/hubspoke_operator_fact not found." >&2
  echo "  Run scripts/run_pipeline_iv.sh first." >&2
  exit 1
fi

echo "[34] Analyzing Fragility V network hotspots..."
python scripts/34_analyze_fragility_hotspots.py --study "$STUDY_FILE" $RUN_MODE_FLAG

echo "[44] Rendering Fragility V executive chart..."
python scripts/44_plot_fragility_hotspots.py

echo "Fragility V pipeline complete."
