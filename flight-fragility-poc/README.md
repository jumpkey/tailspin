# Flight Fragility POC

A reproducible proof-of-concept analysis to determine whether American Airlines'
regional service in LFT and nearby spoke markets shows greater weather-related
schedule fragility than comparable peer markets.

## Business question

> Does AA regional service in LFT and nearby small-spoke markets show a larger
> increase in cancellations and severe delays under marginal or adverse weather
> than comparable peer markets (United hub spokes, Delta hub spokes)?

A more fragile regional operation would leave an observable signature:
disruption rates rising more sharply than peers as weather conditions
deteriorate. Public BTS and weather data cannot observe internal crew,
maintenance, or scheduling decisions directly, so this study tests only for
that externally observable pattern — it does not identify or test which
internal factor, if any, would be responsible.

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
| [NOAA ASOS hourly weather, via Iowa Environmental Mesonet](https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py) | Hourly airport-level METAR observations (visibility, ceiling, present weather) at every study airport | Phase 1 (required) |
| [FlightAware AeroAPI](https://www.flightaware.com/aeroapi/portal) | Historical flight-level data | Phase 2 (optional) |

The original spec called for FAA ASPM cancellation-with-weather reports as the
weather source. That system requires a restricted FAA-registered login and,
even with access, only covers cancelled flights — see [AAR.md](AAR.md) for why
it was replaced with NOAA ASOS and what changed as a result.

## Weather bucket logic

Weather conditions are classified at three levels from NOAA ASOS hourly METAR
observations at each flight's scheduled departure and arrival airport-hour,
using thresholds aligned to FAA flight-rule categories (VFR/MVFR/IFR):

| Bucket    | Rule                                                                                       |
|-----------|---------------------------------------------------------------------------------------------|
| `adverse` | Visibility < 1 SM, or ceiling < 500 ft, or TS/freezing precip/heavy snow/blizzard present    |
| `marginal`| Visibility < 3 SM, or ceiling < 1000 ft, or rain/snow/fog/mist/drizzle present (without adverse conditions) |
| `benign`  | All other conditions                                                                         |

A flight's overall `weather_bucket` is the worse of its departure-airport-hour
and arrival-airport-hour conditions. The exact threshold logic is in
`scripts/11_extract_faa_weather.py` (`classify_weather_bucket` and the
module-level threshold constants).

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
      faa/            ← NOAA ASOS raw export + manifest.csv
      flightaware/    ← FlightAware JSON payloads + manifest.csv (phase 2)
    staging/          ← normalized per-source staging CSVs
    curated/          ← integrated flight fact table

  scripts/
    00_setup_dirs.sh                  ← directory setup and config validation
    10_extract_bts.py                 ← BTS ETL
    11_extract_faa_weather.py         ← FAA ASPM ETL
    12_extract_flightaware.py         ← FlightAware ETL (optional)
    20_build_flight_fact.py           ← integration and fact table
    30_analyze_fragility.py           ← Fragility I aggregation and executive metrics
    31_analyze_fragility_machine.py   ← Fragility II controllable/cascade aggregation
    40_plot_fragility.py              ← Fragility I chart rendering
    41_plot_fragility_machine.py      ← Fragility II chart rendering
    run_pipeline.sh                   ← one-command orchestrator

  output/
    weather_fragility_chart_data.csv           ← Fragility I chart-ready aggregate metrics
    fragility_summary.json                     ← Fragility I executive annotation values
    weather_fragility_exec_chart.png            ← Fragility I deliverable PNG chart
    weather_fragility_machine_chart_data.csv    ← Fragility II chart-ready aggregate metrics
    fragility_ii_machine_summary.json           ← Fragility II executive annotation values
    fragility_ii_summary.md                     ← Fragility II written result summary
    weather_fragility_machine_exec_chart.png    ← Fragility II deliverable PNG chart
    qa_summary.csv                              ← row counts, join rates, null rates (both studies)
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
python scripts/31_analyze_fragility_machine.py --study config/study.yaml
python scripts/40_plot_fragility.py
python scripts/41_plot_fragility_machine.py
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

- NOAA-to-BTS weather-join match rate ≥ 85 % (or documented explanation if lower);
  the live run achieved 99.3% (departure) / 99.8% (arrival) — see AAR.md.
- No chart bucket with fewer than 100 flights (sparse routes are flagged in logs).
- Null rate on `weather_bucket` logged; unmatched flights fall into an `unknown`
  bucket and are excluded from weather-stratified analysis.

## Caveats and known limitations

- **BTS extraction friction**: TranStats's form-based download requires
  ASP.NET ViewState tokens. The extractor instead downloads BTS's pre-built
  monthly PREZIP archives, which need no session or form fields — see AAR.md
  Issue 1.
- **UA peer basket is thin, especially in the 2024 baseline** (426 flights),
  with the adverse-weather/baseline cell at only 32 flights. Treat UA-specific
  weather-stratified rates as directional; Delta is the better-sampled peer.
- **A single regional operator (SkyWest/OO) flies under all three carrier
  contracts** in this study (AA, UA, and DL). Operator-wide factors are
  controlled out by the peer comparison; contract-specific factors are not.
  See AAR.md "Caveats and Limitations" for the full breakdown.
- **Weather is assigned at endpoint airport-hours, not en route.** En-route
  conditions (turbulence, frontal passage in flight) are not captured; for
  short-haul spoke-to-hub flights this is treated as an acceptable
  simplification.
- **Route sparsity**: LFT–DFW alone may be too thin for a decisive signal.
  The basket approach addresses this; individual routes below `min_route_flights`
  are flagged in `output/qa_summary.csv`.
- **Peer comparability**: UA and DL peers were selected for similar stage lengths
  and spoke-to-hub geography; exact route matches may not exist.
- **FlightAware phase 2**: Historical endpoint behavior varies by recency and
  paid lookback window. Keep `use_flightaware: false` for phase-1 runs.

## Results summary

> **Status: Pipeline implemented and run against live data for 2024-01-01
> through 2025-12-31.**
>
> The full ETL, integration, analysis, and chart-rendering pipeline ran
> end-to-end against real BTS On-Time Performance and NOAA ASOS weather
> records — see [AAR.md](AAR.md) for the complete run record, including data
> volumes, join-quality checks, and the full results breakdown.
>
> Headline result — cancellation rate by weather bucket, AA regional vs. the
> average of the UA and DL peer baskets:
>
> | Weather     | AA Regional | UA Peer | DL Peer | Peer avg | AA÷Peer ratio |
> |-------------|-------------|---------|---------|----------|---------------|
> | Benign      | 2.09 %      | 1.05 %  | 1.17 %  | 1.11 %   | 1.88×         |
> | Marginal    | 6.19 %      | 3.27 %  | 2.67 %  | 2.97 %   | **2.08×**     |
> | Adverse     | 10.08 %     | 6.37 %  | 3.34 %  | 4.86 %   | **2.08×**     |
>
> The UA peer basket is the thinner of the two peer comparisons (see Caveats
> above); against Delta alone — the better-sampled peer — the ratio escalates
> with weather severity: 1.79× (benign) → 2.32× (marginal) → 3.02× (adverse).
> Full results, sample sizes, and caveats are in [AAR.md](AAR.md).

### Fragility II: controllable and cascade disruption

> **Status: Implemented as an incremental extension of the Fragility I
> pipeline and run against the same live data.**
>
> Fragility I treats all severe delay and cancellation as a single
> undifferentiated outcome. Fragility II decomposes the same flights using
> BTS's delay-cause fields to ask two more specific questions: how often is
> the *primary* disruption cause attributable to the carrier itself
> (`controllable_severe_delay_rate`), and how often is the flight delayed
> because of a *late-arriving* upstream aircraft, i.e. cascade disruption
> (`late_arriving_severe_delay_rate`)? See
> [output/fragility_ii_summary.md](output/fragility_ii_summary.md) and
> [AAR.md](AAR.md)'s Iteration 3 section for the full write-up, including
> the data-availability limitation that prevented a planned breakout by
> regional operating carrier.
>
> Controllable (Air Carrier-coded) severe-delay rate by weather bucket:
>
> | Weather  | AA Regional | Peer avg | Combined peer | AA÷Peer avg | AA÷Combined peer |
> |----------|-------------|----------|----------------|-------------|-------------------|
> | Benign   | 2.86 %      | 3.81 %   | 3.51 %         | 0.75×       | 0.81×             |
> | Marginal | 3.18 %      | 6.02 %   | 4.52 %         | 0.53×       | 0.70×             |
> | Adverse  | 4.65 %      | 6.35 %   | 4.87 %         | 0.73× (provisional) | 0.95× (provisional) |
>
> Late-arriving (cascade) severe-delay rate by weather bucket:
>
> | Weather  | AA Regional | Peer avg | Combined peer | AA÷Peer avg | AA÷Combined peer |
> |----------|-------------|----------|----------------|-------------|-------------------|
> | Benign   | 4.43 %      | 2.55 %   | 2.22 %         | 1.74×       | 2.00×             |
> | Marginal | 5.40 %      | 4.20 %   | 3.49 %         | 1.28×       | 1.55×             |
> | Adverse  | 8.11 %      | 5.48 %   | 5.31 %         | 1.48× (provisional) | 1.53× (provisional) |
>
> Benign-to-adverse escalation in the cascade rate: AA regional 1.83×,
> combined peer basket 2.39×. "Provisional" marks ratios built from a cell
> at or below the `min_sample_threshold` (30 operated flights) — currently
> only `ua_peer_basket / adverse / baseline`.
>
> This result is mixed relative to Fragility I, not confirmatory: AA's
> controllable severe-delay rate runs consistently *below* peers, while its
> cascade severe-delay rate runs consistently *above* peers but escalates
> *less* with weather severity than the peer basket does. Both findings are
> reported as observed. Full detail, sample sizes, and caveats are in
> [AAR.md](AAR.md).

See the [After Action Report](AAR.md) for decisions made, issues encountered,
and next steps.

