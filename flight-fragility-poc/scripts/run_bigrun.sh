#!/usr/bin/env bash
# run_bigrun.sh — One-shot batch driver for the full keyless Fragility I–V
# bigrun on the Frankenserver (9-hub AA network, duckdb backend, no
# FlightAware key).
#
# Designed to be launched detached and watched later:
#
#   cd ~/projects/tailspin/flight-fragility-poc
#   nohup bash scripts/run_bigrun.sh >/dev/null 2>&1 &
#   tail -f logs/bigrun.latest.log
#
# Runs, in strict order (each phase gated on the previous one's output):
#   STEP 0  Python environment        (create/activate .venv, verify deps)
#   STEP 1  Fragility I–III           run_pipeline.sh   -> flight_operability_fact.csv
#   STEP 2  Fragility IV  (bigrun)     run_pipeline_iv.sh-> hubspoke_operator_fact/
#   STEP 3  Fragility V                run_pipeline_v.sh -> hotspot rankings
#
# It HARD-STOPS with a loud, timestamped FAILED banner if any phase errors or
# a required artifact is missing — so it never silently runs a later phase on
# bad input. The Fragility IV banner prints ">>> REACHED STEP IV <<<" so you
# can confirm at a glance (while tailing, or tomorrow) that I–III succeeded
# and IV started.

# NOT `set -e`: we catch each phase failure explicitly with `|| fail`, so the
# log always ends with a clear PASS/FAIL summary instead of a bare non-zero exit.
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$ROOT_DIR"

# ---- logging -------------------------------------------------------------
mkdir -p logs
RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)"
LOG="logs/bigrun_${RUN_ID}.log"
ln -sf "bigrun_${RUN_ID}.log" logs/bigrun.latest.log
# Mirror all stdout+stderr to the timestamped log AND to the original stdout
# (whatever nohup points at), so `tail -f logs/bigrun.latest.log` always works.
exec > >(tee -a "$LOG") 2>&1

FACT_CSV="data/curated/flight_operability_fact.csv"
HUBSPOKE_PARQUET="data/curated/hubspoke_operator_fact"

ts()     { date -u +%Y-%m-%dT%H:%M:%SZ; }
banner() { echo; echo "============================================================";
           echo "  $(ts)  $*";
           echo "============================================================"; }
fail()   { banner "FAILED: $*"; echo "  Full trace in: $ROOT_DIR/$LOG"; exit 1; }
phase_time() { local m=$((SECONDS/60)) s=$((SECONDS%60)); echo "  phase elapsed: ${m}m${s}s"; }

banner "BIGRUN START — 9-hub AA network · duckdb · no FlightAware key"
echo "  log:   $ROOT_DIR/$LOG"
echo "  host:  $(hostname)   cores: $(nproc)   pid: $$"
echo "  effective config (config/study.yaml):"
grep -E '^(run_mode|backend):' config/study.yaml | sed 's/^/    /'
grep -E '^\s*bigrun:' config/study.yaml | sed 's/^/    /'

# ---- STEP 0: environment -------------------------------------------------
# The venv lives at the tailspin repo root (one level up), not inside this
# subdirectory. Detect that first, then a local .venv, then create one at the
# repo root to match the established layout.
banner "STEP 0  Python environment"
REPO_ROOT="$(dirname "$ROOT_DIR")"
if [[ -f "$REPO_ROOT/.venv/bin/activate" ]]; then
  echo "  using repo-root venv: $REPO_ROOT/.venv"
  # shellcheck disable=SC1091
  source "$REPO_ROOT/.venv/bin/activate" || fail "source $REPO_ROOT/.venv/bin/activate"
elif [[ -f "$ROOT_DIR/.venv/bin/activate" ]]; then
  echo "  using local venv: $ROOT_DIR/.venv"
  # shellcheck disable=SC1091
  source "$ROOT_DIR/.venv/bin/activate" || fail "source $ROOT_DIR/.venv/bin/activate"
else
  echo "  no venv found — creating $REPO_ROOT/.venv and installing requirements (one-time)..."
  python3 -m venv "$REPO_ROOT/.venv" || fail "python3 -m venv $REPO_ROOT/.venv"
  # shellcheck disable=SC1091
  source "$REPO_ROOT/.venv/bin/activate"
  pip install --upgrade pip >/dev/null 2>&1
  pip install -r requirements.txt || fail "pip install -r requirements.txt"
fi
python -c "import pandas, pyarrow, requests, airportsdata, duckdb; \
print('  deps OK — duckdb', duckdb.__version__)" \
  || fail "dependency import check (duckdb missing? rerun: pip install -r requirements.txt)"

# ---- STEP 1: Fragility I–III --------------------------------------------
banner "STEP 1  Fragility I–III  (produces the IV prerequisite fact table)"
SECONDS=0
bash scripts/run_pipeline.sh || fail "Fragility I–III (run_pipeline.sh)"
phase_time
[[ -s "$FACT_CSV" ]] || fail "I–III finished but $FACT_CSV is missing/empty — refusing to start IV"
echo "  prerequisite OK: $FACT_CSV ($(wc -l < "$FACT_CSV") lines)"

# ---- STEP 2: Fragility IV (bigrun) --------------------------------------
banner "STEP 2  Fragility IV  (bigrun: 9 AA hubs · duckdb)   >>> REACHED STEP IV <<<"
echo "  NOTE: NOAA weather fetches are rate-limited; '429; retrying' lines are EXPECTED."
echo "        This is the long pole — budget a few hours on a cold cache."
SECONDS=0
bash scripts/run_pipeline_iv.sh || fail "Fragility IV (run_pipeline_iv.sh)"
phase_time
if [[ ! -d "$HUBSPOKE_PARQUET" ]] || ! find "$HUBSPOKE_PARQUET" -name '*.parquet' -print -quit | grep -q .; then
  fail "IV finished but no parquet under $HUBSPOKE_PARQUET — refusing to start V"
fi
echo "  curated parquet OK: $HUBSPOKE_PARQUET"
if [[ -f output/qa_summary_hubspoke.csv ]]; then
  echo "  --- QA summary (output/qa_summary_hubspoke.csv) ---"
  sed 's/^/    /' output/qa_summary_hubspoke.csv
fi

# ---- STEP 3: Fragility V -------------------------------------------------
banner "STEP 3  Fragility V  (hotspot rankings)"
SECONDS=0
bash scripts/run_pipeline_v.sh || fail "Fragility V (run_pipeline_v.sh)"
phase_time

# ---- done ----------------------------------------------------------------
banner "BIGRUN COMPLETE — all three phases finished"
echo "  Key outputs:"
for f in output/qa_summary_hubspoke.csv \
         output/fragility_iv_summary.json \
         output/fragility_v_hotspot_rankings.csv \
         output/fragility_v_hub_rollup.csv \
         output/fragility_v_operator_rollup.csv; do
  if [[ -f "$f" ]]; then echo "    [ok]   $f"; else echo "    [MISS] $f"; fi
done
echo
echo "  Next: compare against the local-mode baselines (FRANKENSERVER.md §6, AAR.md),"
echo "  then commit output/ + the raw manifests if the numbers check out."
banner "END"
