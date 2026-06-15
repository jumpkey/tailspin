# Flight Fragility POC

A reproducible proof-of-concept analysis to determine whether American Airlines'
regional service in LFT and nearby spoke markets shows greater weather-related
schedule fragility than comparable peer markets.

## Business question

> Does AA regional service in LFT and nearby small-spoke markets show a larger
> increase in cancellations and severe delays under marginal or adverse weather
> than comparable peer markets (United hub spokes, Delta hub spokes)?

The working theory is that a more fragile regional operation leaves an
observable signature: disruption rates rise more sharply than peers as weather
conditions deteriorate — consistent with "green crew limitations" or a
thinner, more weather-sensitive regional operation.

## Study period

| Window       | Dates                    |
|--------------|--------------------------|
| Baseline     | 2024-01-01 – 2024-12-31  |
| Recent       | 2025-01-01 – 2025-12-31  |
| Combined     | 2024-01-01 – 2025-12-31  |

## Route baskets

| Basket              | Routes                                                               |
|---------------------|----------------------------------------------------------------------|
| AA regional basket  | LFT–DFW, BTR–DFW, AEX–DFW, MLU–DFW, GPT–DFW, SHV–DFW              |
| UA peer basket      | LFT–IAH, BTR–IAH, GPT–IAH, SHV–IAH                                 |
| DL peer basket      | LFT–ATL, BTR–ATL, GPT–ATL, SHV–ATL                                 |

Route membership should be validated against observed BTS service; routes with
fewer than 100 observed flights are excluded from chart buckets.

## Data sources

| Source | Description | Phase |
|--------|-------------|-------|
| [BTS TranStats On-Time Performance](https://www.transtats.bts.gov/DL_SelectFields.aspx?gnoyr_VQ=FGJ) | Scheduled / actual times, cancellations, delays | Phase 1 (required) |
| [FAA ASPM Cancelled Flights with Weather](https://www.aspm.faa.gov/aspmhelp/index/ASQP__Cancellations__Cancelled_Flights_with_Weather_Report.html) | Cancelled flights with departure/arrival-hour weather fields | Phase 1 (required) |
| [FlightAware AeroAPI](https://www.flightaware.com/aeroapi/portal) | Historical flight-level data | Phase 2 (optional) |

## Weather bucket logic

Weather conditions are classified at three levels using FAA ASPM severity
where available, with a text-descriptor fallback:

| Bucket    | ASPM primary rule                         | Fallback text rule                            |
|-----------|-------------------------------------------|-----------------------------------------------|
| `benign`  | Both endpoints ≤ Minor                    | No adverse or marginal keywords               |
| `marginal`| One endpoint is Moderate                  | Rain, mist, reduced vis/ceiling               |
| `adverse` | One/both Severe; or both ≥ Moderate       | Fog, thunderstorm, very low vis/ceiling       |

The exact threshold logic is in `scripts/20_build_flight_fact.py`
(`derive_weather_bucket` function and module-level constants).

## Repository layout

```
flight-fragility-poc/
  README.md           ← this file
  requirements.txt
  .env.example

  config/
    routes.yaml       ← route basket definitions
    study.yaml        ← study dates, thresholds, feature flags

  data/
    raw/
      bts/            ← monthly BTS raw CSVs + manifest.csv
      faa/            ← FAA ASPM raw exports + manifest.csv
      flightaware/    ← FlightAware JSON payloads + manifest.csv (phase 2)
    staging/          ← normalized per-source staging CSVs
    curated/          ← integrated flight fact table

  scripts/
    00_setup_dirs.sh           ← directory setup and config validation
    10_extract_bts.py          ← BTS ETL
    11_extract_faa_weather.py  ← FAA ASPM ETL
    12_extract_flightaware.py  ← FlightAware ETL (optional)
    20_build_flight_fact.py    ← integration and fact table
    30_analyze_fragility.py    ← aggregation and executive metrics
    40_plot_fragility.py       ← chart rendering
    run_pipeline.sh            ← one-command orchestrator

  output/
    weather_fragility_chart_data.csv   ← chart-ready aggregate metrics
    fragility_summary.json             ← executive annotation values
    qa_summary.csv                     ← row counts, join rates, null rates
    weather_fragility_exec_chart.png   ← deliverable PNG chart
```

## Setup

```bash
# 1. Clone or enter the project directory
cd flight-fragility-poc

# 2. Create a Python virtual environment (Python 3.11+)
python -m venv .venv
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy and configure environment
cp .env.example .env
# Edit .env if you plan to use FlightAware (phase 2 only)
```

## Running the pipeline

```bash
# Full pipeline (single command)
bash scripts/run_pipeline.sh

# With options
bash scripts/run_pipeline.sh --force               # re-download raw data
bash scripts/run_pipeline.sh --skip-flightaware    # skip FA extraction
bash scripts/run_pipeline.sh --study-override config/study_2024_only.yaml

# Run individual steps
python scripts/10_extract_bts.py --routes config/routes.yaml --study config/study.yaml
python scripts/11_extract_faa_weather.py --routes config/routes.yaml --study config/study.yaml
python scripts/20_build_flight_fact.py --routes config/routes.yaml --study config/study.yaml
python scripts/30_analyze_fragility.py --study config/study.yaml
python scripts/40_plot_fragility.py
```

## Environment variables

| Variable              | Required | Description                                       |
|-----------------------|----------|---------------------------------------------------|
| `FLIGHTAWARE_API_KEY` | No       | FlightAware AeroAPI key (phase 2 only; set `use_flightaware: true` in study.yaml) |

## Idempotency and reproducibility

- Raw files are treated as **immutable** once downloaded. Pass `--force` to refresh.
- Each ETL script writes a `manifest.csv` recording row counts, extraction
  timestamps, source parameters, and SHA-256 checksums.
- All downstream steps are deterministic given the staged inputs and config files.
- No manual spreadsheet editing or copy/paste is required at any step.

## QA acceptance thresholds

- FAA-to-BTS cancelled-flight join rate ≥ 85 % (or documented explanation if lower).
- No chart bucket with fewer than 100 flights (sparse routes are flagged in logs).
- Null rate on `weather_bucket` logged; unknown values indicate unmatched FAA records.

## Caveats and known limitations

- **BTS extraction friction**: TranStats uses form-based downloads without a
  stable REST API. The extractor uses HTTP POST; if the form structure changes,
  re-examine field codes in `scripts/10_extract_bts.py`.
- **FAA ASPM session handling**: ASPM uses ASP.NET ViewState sessions.
  If extraction fails, check the form-field names in `scripts/11_extract_faa_weather.py`.
- **Route sparsity**: LFT–DFW alone may be too thin for a decisive signal.
  The basket approach addresses this; individual routes below `min_route_flights`
  are flagged in `output/qa_summary.csv`.
- **Peer comparability**: UA and DL peers were selected for similar stage lengths
  and spoke-to-hub geography; exact route matches may not exist.
- **FlightAware phase 2**: Historical endpoint behavior varies by recency and
  paid lookback window. Keep `use_flightaware: false` for phase-1 runs.

## Results summary

> **Status: Pipeline implemented and smoke-tested with synthetic data.**
>
> The full ETL, integration, analysis, and chart rendering pipeline is
> implemented and verified runnable.  Committed outputs (`output/`) were
> generated from **synthetic data only** to validate the pipeline end-to-end;
> they are not based on live BTS or FAA records.
>
> **Re-run the pipeline** in a network-enabled environment to replace these
> placeholder outputs with actual results:
> ```bash
> bash scripts/run_pipeline.sh --force
> ```
>
> Synthetic smoke-test ratios (illustrative only):
>
> | Weather     | AA Regional | UA Peer | DL Peer | AA÷Peer ratio |
> |-------------|-------------|---------|---------|---------------|
> | Benign      | 1.4 %       | 1.2 %   | 1.0 %   | 1.25×         |
> | Marginal    | 12.8 %      | 5.1 %   | 5.3 %   | **2.46×**     |
> | Adverse     | 30.0 %      | 10.5 %  | 10.0 %  | **2.92×**     |
>
> *(These numbers are random-seed artifacts, not real flight data.)*

See the [After Action Report](AAR.md) for decisions made, issues encountered,
and next steps.

