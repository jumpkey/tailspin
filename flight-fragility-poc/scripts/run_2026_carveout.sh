#!/usr/bin/env bash
# run_2026_carveout.sh — Extend the curated fact layer with 2026 data
# (Jan-Apr, the BTS-published months) for the 2024-2025-vs-2026 carve-out.
#
# Runs EXTRACTION + FACT BUILD ONLY (no analysis, no plots), so the committed
# 2024-vs-2025 analysis outputs in output/ are never touched. Curated facts are
# written to dedicated *_2026 paths. Direct queries against those facts drive
# the carve-out sections of the LFT-focal report and the network report.
#
# Launch detached:
#   nohup bash scripts/run_2026_carveout.sh >/dev/null 2>&1 &
#   tail -f logs/carveout2026.latest.log

set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$ROOT_DIR"

mkdir -p logs output/2026_carveout
RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)"
LOG="logs/carveout2026_${RUN_ID}.log"
ln -sf "carveout2026_${RUN_ID}.log" logs/carveout2026.latest.log
exec > >(tee -a "$LOG") 2>&1

STUDY="config/study_2026.yaml"
FOCAL_FACT="data/curated/flight_operability_fact_2026.csv"
HUB_FACT="data/curated/hubspoke_operator_fact_2026"

ts()     { date -u +%Y-%m-%dT%H:%M:%SZ; }
banner() { echo; echo "============================================================";
           echo "  $(ts)  $*"; echo "============================================================"; }
fail()   { banner "FAILED: $*"; echo "  Full trace in: $ROOT_DIR/$LOG"; exit 1; }

# repo-root venv (one level up), per the established layout
REPO_ROOT="$(dirname "$ROOT_DIR")"
if [[ -f "$REPO_ROOT/.venv/bin/activate" ]]; then source "$REPO_ROOT/.venv/bin/activate";
elif [[ -f "$ROOT_DIR/.venv/bin/activate" ]]; then source "$ROOT_DIR/.venv/bin/activate";
else fail "no venv found"; fi

banner "2026 CARVE-OUT START — baseline=2024-25, recent=2026 (Jan-Apr)"
echo "  log:  $ROOT_DIR/$LOG   pid: $$   cores: $(nproc)"

# ---- Focal corridor (Fragility I-III inputs): 9-airport universe -----------
banner "FOCAL [10] BTS extraction (adds 2026 months to cache)"
python scripts/10_extract_bts.py --routes config/routes.yaml --study "$STUDY" \
  --out data/staging/bts_flights.csv || fail "10_extract_bts"

banner "FOCAL [11] NOAA weather extraction"
python scripts/11_extract_faa_weather.py --routes config/routes.yaml --study "$STUDY" \
  --out data/staging/airport_weather_hourly.csv || fail "11_extract_faa_weather"

banner "FOCAL [20] Build focal fact -> $FOCAL_FACT"
python scripts/20_build_flight_fact.py --routes config/routes.yaml --study "$STUDY" \
  --weather data/staging/airport_weather_hourly.csv \
  --out "$FOCAL_FACT" --qa-out output/2026_carveout/qa_summary_focal.csv || fail "20_build_flight_fact"
[[ -s "$FOCAL_FACT" ]] || fail "focal fact missing/empty"

# ---- Network (hub-spoke, 9 hubs) ------------------------------------------
banner "NET [13] BTS hub-spoke extraction (bigrun; adds 2026 months)"
python scripts/13_extract_bts_hubspoke.py --study "$STUDY" --run-mode bigrun || fail "13_extract_bts_hubspoke"

banner "NET [14] NOAA hub-spoke weather (bigrun; 2026 months) — 429/retry is expected"
python scripts/14_extract_weather_hubspoke.py --study "$STUDY" --run-mode bigrun || fail "14_extract_weather_hubspoke"

banner "NET [15] Operator-ambiguity resolution (no-op without key)"
python scripts/15_resolve_operator_ambiguity.py --study "$STUDY" || true

banner "NET [21] Build hub-spoke fact -> $HUB_FACT"
python scripts/21_build_hubspoke_fact.py --study "$STUDY" \
  --out "$HUB_FACT" --qa-out output/2026_carveout/qa_summary_hubspoke.csv || fail "21_build_hubspoke_fact"
if [[ ! -d "$HUB_FACT" ]] || ! find "$HUB_FACT" -name '*.parquet' -print -quit | grep -q .; then
  fail "hub-spoke fact has no parquet"
fi

banner "2026 CARVE-OUT COMPLETE — curated facts ready for direct querying"
echo "  focal:   $FOCAL_FACT"
echo "  network: $HUB_FACT"
echo "  QA:      output/2026_carveout/"
banner "END"
