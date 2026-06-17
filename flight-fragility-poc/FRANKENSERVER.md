# Frankenserver Run Instructions

This document covers the complete workflow for resuming this study on a local
high-memory server using a local Claude Code session: from git checkout through
pipeline execution to committing and pushing results back. It is written for
a session that starts with no container state — no cached data, no virtual
environment, no Python packages.

---

## 1. Git checkout

```bash
# Clone the repo (if not already present)
git clone https://github.com/jumpkey/tailspin.git
cd tailspin

# Or, if already cloned, fetch and fast-forward to current main
git fetch origin
git checkout main
git pull origin main

# Confirm you are on main and up to date
git log --oneline -5
```

The working directory for all subsequent steps is `tailspin/flight-fragility-poc/`.

```bash
cd flight-fragility-poc
```

---

## 2. Python environment setup

Python 3.11 or later is required.

```bash
# Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

Key packages that must install cleanly: `pandas`, `numpy`, `requests`,
`airportsdata`, `pyarrow`, `matplotlib`, `kaleido`, `plotly`. If `kaleido`
fails (it sometimes does on Linux), `matplotlib` is the automatic fallback
for chart rendering; the pipeline will still produce all PNG outputs.

Verify the install:
```bash
python -c "import pandas, pyarrow, requests, airportsdata, matplotlib; print('OK')"
```

---

## 3. Environment variables (optional but recommended)

```bash
cp .env.example .env
```

Edit `.env`:

```
# Set if you want FlightAware operator-ambiguity resolution for OO/YX rows.
# If unset, scripts/15_resolve_operator_ambiguity.py no-ops safely.
FLIGHTAWARE_API_KEY=your_key_here
```

If `FLIGHTAWARE_API_KEY` is provided, the pipeline will attempt targeted
single-flight lookups for SkyWest_unresolved / Republic_unresolved rows.
This reduces the ~485K unresolved-ambiguity flights to a smaller residual.
The pipeline runs correctly without it; operator-ambiguity rows are retained
in hub-level rollups and excluded from operator-class comparisons.

---

## 4. Data situation: what is cached vs. what needs to run

### What is already committed to the repository

- `data/raw/bts_hubspoke/manifest.csv` and `data/raw/faa_hubspoke/manifest.csv`
  record which raw files were downloaded in the container's local-mode run.
- `output/` contains all current Fragility I–V result files, already committed.
- **The raw monthly CSVs themselves are gitignored** (BTS PREZIP and NOAA ASOS
  files, ~1–2 GB total). They will not be present on a fresh clone.
- **The curated Parquet layer is gitignored** (`data/curated/hubspoke_operator_fact/`).
  It will not be present on a fresh clone.

### What will re-run vs. skip

The pipeline has **idempotent caching at the raw-file level**. If the raw files
exist, each extraction script skips the download and uses the cached file. If
they do not exist (fresh clone), the scripts re-download them.

For a fresh Frankenserver run:
- **Fragility I–III** (`run_pipeline.sh`): re-downloads ~9 monthly BTS ZIPs and
  ~9 months of NOAA ASOS data (focal corridor, 9 airports). Fast, small data.
  Must run at least once to produce `data/curated/flight_operability_fact.csv`
  for Fragility IV Module A.
- **Fragility IV** (`run_pipeline_iv.sh`, local mode): re-downloads 24 monthly
  BTS PREZIP files (national, ~27 MB each = ~650 MB) and 24 months × ~175–240
  ASOS stations of NOAA data. NOAA downloads are rate-limited; the pipeline
  handles this automatically with retry-with-backoff, but expect ~30–60 minutes
  of elapsed time for the NOAA fetches on a fresh run (the actual data transfer
  is fast; the retry delays are the bottleneck only if the service throttles).
- **Fragility V** (`run_pipeline_v.sh`): no new data downloads — it reads the
  Fragility IV curated Parquet layer and runs in under 5 minutes.

---

## 5. Running the pipelines

### Step 1: Fragility I–III (required once, then skip)

```bash
bash scripts/run_pipeline.sh
```

Expected output: `output/weather_fragility_exec_chart.png`,
`output/fragility_ii_*`, `output/fragility_iii_*`. If you are resuming with
`data/curated/flight_operability_fact.csv` already present, you can skip this
step and go directly to Fragility IV.

### Step 2: Fragility IV — local mode (default)

The current `config/study.yaml` `run_mode: local` covers DFW/CLT/ORD/PHL,
Jan 2024–Dec 2025. This is the configuration used for the committed results.

```bash
bash scripts/run_pipeline_iv.sh
```

Override options:
```bash
bash scripts/run_pipeline_iv.sh --run-mode local    # explicit local mode
bash scripts/run_pipeline_iv.sh --force             # re-download all raw files
bash scripts/run_pipeline_iv.sh --run-mode bigrun   # if you want a wider hub set
```

For `bigrun`, first edit `config/study.yaml` to set `run_mode_hubs` to the
full hub list you want (e.g., add MIA, LAX, PHX). The bigrun logic is already
wired; it will use whatever hubs are listed under `bigrun:` in the config.

**Expected runtime (local mode, fresh download):** 45–90 minutes on a
multi-core server (dominated by NOAA retry wait times on a cold start; on a
warm cache with all raw files present, the pipeline finishes in ~15–20 minutes).

**Watch for:**
- NOAA 429/503 responses in the log — the retry-with-backoff logic handles these
  automatically (30/60/120/240/480 s delays). If you see `NOAA returned 429;
  retrying in 30s (attempt 1/5)`, that is expected and correct.
- Weather match rate in the QA output — should be ≥ 90% (the container run
  achieved 96.6%). If it is below 85%, check the NOAA fetch logs for persistent
  failures after all retries.

### Step 3: Fragility V

```bash
bash scripts/run_pipeline_v.sh
```

No arguments needed. Reads from `data/curated/hubspoke_operator_fact/` which
Fragility IV just produced. Completes in under 5 minutes.

Override:
```bash
bash scripts/run_pipeline_v.sh --run-mode local
```

---

## 6. Verifying results

```bash
# Check the top-20 hotspot rankings
head -5 output/fragility_v_hotspot_rankings.csv

# Check hub and operator concentration
cat output/fragility_v_hub_rollup.csv
cat output/fragility_v_operator_rollup.csv

# Check Fragility IV top cell
python -c "import json; d = json.load(open('output/fragility_iv_summary.json')); print(d['top_cell']['operator_class'], d['top_cell']['hub_family'], d['top_cell']['combined_fragility_score'])"

# View QA summary
cat output/qa_summary_hubspoke.csv
```

Baseline numbers to verify against (from the container run):
- `qa_summary_hubspoke.csv`: total_flights = 3,587,814; DFW = 1,230,629; ORD = 1,183,012
- `fragility_iv_summary.json`: top cell PSA_operated / ORD, score 0.225
- `fragility_v_summary.md`: rank-1 cell ORD-SPI SkyWest_unresolved, base score 0.978
- `fragility_v_hub_rollup.csv`: DFW 50%, ORD 45%, PHL 5%, CLT 0%

If numbers differ from baseline, the most likely causes are:
1. BTS source data has been updated upstream (monthly archives can be revised)
2. `FLIGHTAWARE_API_KEY` is set this time, reducing unresolved-ambiguity counts
3. `config/study.yaml` `run_mode` or `run_mode_hubs` was changed

---

## 7. Running with Claude Code locally

Start a local Claude Code session from inside the `tailspin/` directory:

```bash
cd tailspin
claude
```

Or, from anywhere:
```bash
claude --project /path/to/tailspin
```

Useful things to ask Claude Code in a local session:
- "Run the Fragility IV pipeline in bigrun mode and summarize what changed vs. the local-mode results."
- "Add MIA and LAX to the bigrun hub list and re-run Fragility IV and V."
- "Explain the top-20 Fragility V hotspots and which ones warrant follow-up."
- "Extend Fragility V's economic burden computation to produce a network-wide total."
- "Add the operator-level Fragility III cost breakdown (Entry 2 open item in LEADERSHIP_READOUT_NOTES.md)."

Claude Code will have access to all the files and can run the pipelines directly.
It can also read `AAR.md`, `LEADERSHIP_READOUT_NOTES.md`, and the spec files to
understand the study's design history before making changes.

---

## 8. Committing and pushing results back

After a successful run, commit the new output files and any config changes:

```bash
# Stage output files (CSVs, JSONs, PNGs, MDs)
git add output/
git add data/raw/bts_hubspoke/manifest.csv
git add data/raw/faa_hubspoke/manifest.csv

# Stage any config changes if you modified study.yaml
git add config/study.yaml

# Commit
git commit -m "$(cat <<'EOF'
Fragility IV + V bigrun results: <hub list>, <month range>

Add updated output files from bigrun-mode execution on Frankenserver.

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"

# Push to main (or a feature branch if preferred)
git push origin main
```

**Do not commit:**
- `data/raw/bts_hubspoke/*.csv` — gitignored, large (~650 MB for local mode)
- `data/raw/faa_hubspoke/*.csv` — gitignored, large
- `data/curated/hubspoke_operator_fact/` — gitignored, large
- `data/staging/` — gitignored
- `.venv/` — gitignored

If push fails due to a network error, retry up to 4 times with exponential backoff
(2s, 4s, 8s, 16s):
```bash
git push origin main || sleep 2 && git push origin main || sleep 4 && git push origin main
```

---

## 9. What to hand back to Claude Code

After pushing, re-open a Claude Code session (local or remote) and say:

> "The bigrun results are pushed to main. Review the new output files vs. the
> local-mode baselines in AAR.md and update AAR.md, README.md, and
> LEADERSHIP_READOUT_NOTES.md to reflect the new findings."

Claude Code will read the committed output files, compare against the local-mode
baselines documented in AAR.md, and update the documents accordingly.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| NOAA returns 429 immediately on month 2 | Rate limiting; expected | Wait 15 min, then `--force` re-run; retry-with-backoff should handle it automatically |
| Weather match rate < 85% | NOAA fetch failed silently | Check `data/raw/faa_hubspoke/` for near-empty CSVs; re-run with `--force` |
| `parquet` import error | `pyarrow` not installed | `pip install pyarrow` |
| Chart renders blank | `kaleido` issue | Matplotlib fallback is automatic; check `output/fragility_*_exec_chart.png` |
| Row counts differ from baseline | BTS source updated or config changed | Expected if running bigrun; document in AAR.md |
| `airportsdata` not found | Missing from requirements | `pip install airportsdata` |
