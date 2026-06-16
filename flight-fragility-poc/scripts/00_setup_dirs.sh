#!/usr/bin/env bash
# 00_setup_dirs.sh — Create the directory tree and validate config presence.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

echo "[setup] Creating data directories..."
mkdir -p \
  "$ROOT_DIR/data/raw/bts" \
  "$ROOT_DIR/data/raw/faa" \
  "$ROOT_DIR/data/raw/flightaware" \
  "$ROOT_DIR/data/raw/bts_hubspoke" \
  "$ROOT_DIR/data/raw/faa_hubspoke" \
  "$ROOT_DIR/data/raw/flightaware_resolution" \
  "$ROOT_DIR/data/staging" \
  "$ROOT_DIR/data/curated" \
  "$ROOT_DIR/data/curated/hubspoke_operator_fact" \
  "$ROOT_DIR/output"

echo "[setup] Validating config files..."
for cfg in config/routes.yaml config/study.yaml config/operator_classes.yaml; do
  if [[ ! -f "$ROOT_DIR/$cfg" ]]; then
    echo "[setup] ERROR: Missing required config file: $cfg" >&2
    exit 1
  fi
done

echo "[setup] Creating empty manifest files if absent..."
for manifest in \
  "$ROOT_DIR/data/raw/bts/manifest.csv" \
  "$ROOT_DIR/data/raw/faa/manifest.csv" \
  "$ROOT_DIR/data/raw/flightaware/manifest.csv" \
  "$ROOT_DIR/data/raw/bts_hubspoke/manifest.csv" \
  "$ROOT_DIR/data/raw/faa_hubspoke/manifest.csv" \
  "$ROOT_DIR/data/raw/flightaware_resolution/manifest.csv"; do
  if [[ ! -f "$manifest" ]]; then
    echo "source,filename,rows,extracted_at,checksum,params" > "$manifest"
  fi
done

echo "[setup] Directory setup complete."
