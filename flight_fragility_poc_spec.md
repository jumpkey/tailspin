# Flight Fragility POC: Re-runnable ETL, Analysis, and Chart Spec

This document specifies a repeatable proof-of-concept pipeline to test whether American Airlines regional service in LFT and nearby spoke markets shows greater weather-related schedule fragility than comparable peer markets.[cite:25][cite:70][cite:135]

The intended outcome is a repository that can be re-run to pull source data, normalize and integrate it, compute fragility metrics, and render a single executive-ready PNG chart without manual spreadsheet work.[cite:148][cite:145][cite:49]

## Objective

Build one reproducible analysis that answers: **Does AA regional service in LFT and nearby small-spoke markets show a larger increase in cancellations and severe delays under marginal or adverse weather than comparable peer markets?**[cite:70][cite:135]

The deliverable is one executive-ready chart plus supporting CSVs, produced from scripted ETL and analysis steps.[cite:25][cite:70]

## Business question

The working theory is not that pilot seniority or qualification can be observed directly in public data, but that a more fragile regional operation would leave an observable signature: disruption rates would rise more sharply than peers as weather conditions deteriorate.[cite:70][cite:79][cite:93]

This project therefore tests for an operational pattern consistent with “green crew limitations” or a thinner, more weather-sensitive regional operation, using hard flight outcome data and independent weather-linked cancellation data.[cite:70][cite:135]

## Source data

### BTS On-Time Performance

BTS TranStats is the system-of-record source for scheduled and actual departure and arrival times, cancellations, diversions, and delay fields for U.S. reporting carriers.[cite:25][cite:17]

Relevant BTS access points and documentation:

- TranStats database overview: [https://transtats.bts.gov/DatabaseInfo.asp?QO_VQ=EFD&DB_URL=](https://transtats.bts.gov/DatabaseInfo.asp?QO_VQ=EFD&DB_URL=) [cite:25]
- TranStats downloadable field-selection page: [https://www.transtats.bts.gov/DL_SelectFields.aspx?gnoyr_VQ=FGJ&QO_fu146_anzr=b0-gvzr](https://www.transtats.bts.gov/DL_SelectFields.aspx?gnoyr_VQ=FGJ&QO_fu146_anzr=b0-gvzr) [cite:148]
- BTS FAQ: [https://transtats.bts.gov/faq.asp](https://transtats.bts.gov/faq.asp) [cite:150]
- BTS workbook / field usage reference: [https://catsr.vse.gmu.edu/SYST660/BTSAirlineOnTimePerformanceData_Workbook.pdf](https://catsr.vse.gmu.edu/SYST660/BTSAirlineOnTimePerformanceData_Workbook.pdf) [cite:17]

Required BTS fields:

- `FlightDate`
- `Reporting_Airline` or `UniqueCarrier`
- `Operating_Airline` if available
- `Flight_Number_Reporting_Airline`
- `Origin`
- `Dest`
- `CRSDepTime`
- `DepTime`
- `CRSArrTime`
- `ArrTime`
- `DepDelay`
- `ArrDelay`
- `Cancelled`
- `CancellationCode`
- `Diverted`
- `Distance`
- `ActualElapsedTime`
- `CRSElapsedTime`[cite:25][cite:17]

### FAA ASPM / ASQP cancellation-with-weather data

The FAA ASPM “Cancelled Flights with Weather Report” provides individual cancelled flights and weather conditions at the scheduled departure and arrival hours, making it the key independent weather source for this POC.[cite:70]

Relevant FAA documentation:

- Cancelled Flights with Weather Report: [https://www.aspm.faa.gov/aspmhelp/index/ASQP__Cancellations__Cancelled_Flights_with_Weather_Report.html](https://www.aspm.faa.gov/aspmhelp/index/ASQP__Cancellations__Cancelled_Flights_with_Weather_Report.html) [cite:70]
- Departure Cancellations with Weather Report: [https://www.aspm.faa.gov/aspmhelp/index/ASQP__Cancellations__Departure_Cancellations_with_Weather_Report.html](https://www.aspm.faa.gov/aspmhelp/index/ASQP__Cancellations__Departure_Cancellations_with_Weather_Report.html) [cite:129]
- Arrival Cancellations with Weather Report: [https://www.aspm.faa.gov/aspmhelp/index/ASQP__Cancellations__Arrival_Cancellations_with_Weather_Report.html](https://www.aspm.faa.gov/aspmhelp/index/ASQP__Cancellations__Arrival_Cancellations_with_Weather_Report.html) [cite:133]
- ASPM Cancellations Manual: [https://www.aspm.faa.gov/aspmhelp/index/ASPM_Cancellations_Manual.html](https://www.aspm.faa.gov/aspmhelp/index/ASPM_Cancellations_Manual.html) [cite:145]
- ASPM Data Download: Cancelled Flights: [https://www.aspm.faa.gov/aspmhelp/index/ASPM_Data_Download__Cancelled_Flights.html](https://www.aspm.faa.gov/aspmhelp/index/ASPM_Data_Download__Cancelled_Flights.html) [cite:134]
- ASPM Weather Factors Manual: [https://www.aspm.faa.gov/aspmhelp/index/ASPM_Weather_Factors_Manual.html](https://www.aspm.faa.gov/aspmhelp/index/ASPM_Weather_Factors_Manual.html) [cite:135]

Required FAA fields:

- `Scheduled Departure Date`
- `Carrier Code`
- `Flight Number`
- `Departure Airport`
- `Arrival Airport`
- `Scheduled Departure Time`
- `Scheduled Arrival Time`
- Departure-hour weather fields
- Arrival-hour weather fields[cite:70]

### Optional FlightAware AeroAPI

FlightAware AeroAPI is optional and should be treated as a phase-2 validation or recency extension layer, not a hard dependency for phase 1.[cite:49][cite:46]

Relevant docs and references:

- Historical data overview: [https://go.flightaware.com/aeroapi-historical-flight-data](https://go.flightaware.com/aeroapi-historical-flight-data) [cite:43]
- Developer portal: [https://www.flightaware.com/aeroapi/portal](https://www.flightaware.com/aeroapi/portal) [cite:46]
- Historical endpoint release note: [https://blog.flightaware.com/new-flightaware-aeroapi-release-more-ways-to-access-historical-data](https://blog.flightaware.com/new-flightaware-aeroapi-release-more-ways-to-access-historical-data) [cite:49]
- Sample apps: [https://github.com/flightaware/aeroapps](https://github.com/flightaware/aeroapps) [cite:151]

Relevant historical endpoints include airport departures, airport arrivals, airport-to-destination history, and operator history.[cite:49]

## Technical goal

The repository must support a one-command rerun that performs:

1. Scripted ETL for each source.
2. Scripted normalization and integration into a single flight fact table.
3. Scripted analysis to create a chart-ready aggregate dataset.
4. Scripted Python chart generation to produce a PNG.[cite:148][cite:145][cite:49]

No manual spreadsheet editing, copy/paste, or hand-maintained intermediate tables are allowed in the production workflow.[cite:145][cite:150]

## Repository layout

```text
flight-fragility-poc/
  README.md
  requirements.txt
  .env.example

  config/
    routes.yaml
    study.yaml

  data/
    raw/
      bts/
      faa/
      flightaware/
    staging/
    curated/

  scripts/
    00_setup_dirs.sh
    10_extract_bts.py
    11_extract_faa_weather.py
    12_extract_flightaware.py
    20_build_flight_fact.py
    30_analyze_fragility.py
    40_plot_fragility.py
    run_pipeline.sh

  output/
    weather_fragility_chart_data.csv
    weather_fragility_exec_chart.png
    qa_summary.csv
```

This structure separates immutable raw extracts, normalized staging data, curated analytic outputs, and final presentation artifacts so the pipeline can be rerun and audited cleanly.[cite:145][cite:150]

## Runtime stack

Use Python for extraction, normalization, integration, analysis, and chart rendering; use bash or curl only for orchestration or where a source is easier to call that way.[cite:49][cite:151][cite:145]

Suggested Python packages:

```text
pandas
numpy
pyyaml
requests
python-dateutil
lxml
beautifulsoup4
plotly
kaleido
```

Plotly plus Kaleido is preferred for deterministic PNG output, though a matplotlib fallback is acceptable if PNG rendering proves more stable in the target environment.[cite:49]

## Configuration

### `config/routes.yaml`

This file defines the primary route and basket definitions so the analysis can be rerun without code edits.[cite:25]

```yaml
primary_route:
  - origin: LFT
    dest: DFW

aa_regional_basket:
  - { origin: LFT, dest: DFW }
  - { origin: BTR, dest: DFW }
  - { origin: AEX, dest: DFW }
  - { origin: MLU, dest: DFW }
  - { origin: GPT, dest: DFW }
  - { origin: SHV, dest: DFW }

ua_peer_basket:
  - { origin: LFT, dest: IAH }
  - { origin: BTR, dest: IAH }
  - { origin: GPT, dest: IAH }
  - { origin: SHV, dest: IAH }

dl_peer_basket:
  - { origin: LFT, dest: ATL }
  - { origin: BTR, dest: ATL }
  - { origin: GPT, dest: ATL }
  - { origin: SHV, dest: ATL }
```

Final route membership should still be validated against observed BTS service in the study window rather than assumed statically.[cite:25]

### `config/study.yaml`

This file defines the study dates, thresholds, and optional use of FlightAware.[cite:5][cite:49]

```yaml
study_start: "2024-01-01"
study_end:   "2025-12-31"

baseline_start: "2024-01-01"
baseline_end:   "2024-12-31"
recent_start:   "2025-01-01"
recent_end:     "2025-12-31"

delay_threshold_minutes: 60
min_route_flights: 100

weather_bucket_logic:
  benign:
    aspm_levels_allowed: ["None", "Minor"]
  marginal:
    aspm_levels_allowed: ["Moderate"]
  adverse:
    aspm_levels_allowed: ["Severe"]

use_flightaware: false
flightaware_mode: "validation_only"
```

## ETL specification

### Script: `scripts/00_setup_dirs.sh`

Purpose:

- Create directory structure if missing.
- Validate presence of config files.
- Optionally create empty manifest files.[cite:145]

Example:

```bash
#!/usr/bin/env bash
set -euo pipefail
mkdir -p data/raw/bts data/raw/faa data/raw/flightaware data/staging data/curated output
```

### Script: `scripts/10_extract_bts.py`

Purpose:

- Pull BTS On-Time Performance source data for the study period and route universe.
- Save monthly raw extracts under `data/raw/bts/`.
- Save a normalized staging file under `data/staging/`.[cite:25][cite:148]

Inputs:

- `config/routes.yaml`
- `config/study.yaml`

Outputs:

- `data/raw/bts/bts_YYYY_MM.csv`
- `data/staging/bts_flights.csv`
- `data/raw/bts/manifest.csv`

Required behavior:

- Support idempotent reruns.
- Skip existing monthly raw files unless `--force` is passed.
- Record row count, extraction timestamp, source parameters, and file checksum in the manifest.[cite:150]

Extraction approach:

- Use the TranStats download page as the source entry point.[cite:148]
- Implement a first-pass scripted HTTP flow if the request pattern can be stabilized.
- If direct HTTP extraction is not robust, implement an automated browser-export fallback invoked by the Python script so the process still remains rerunnable.[cite:148][cite:150]

CLI example:

```bash
python scripts/10_extract_bts.py \
  --routes config/routes.yaml \
  --study config/study.yaml \
  --out data/staging/bts_flights.csv
```

Required staging fields:

- `flight_date`
- `carrier_code`
- `operating_carrier`
- `flight_number`
- `origin`
- `dest`
- `sched_dep_local`
- `actual_dep_local`
- `sched_arr_local`
- `actual_arr_local`
- `dep_delay_min`
- `arr_delay_min`
- `cancelled_flag`
- `cancellation_code_bts`
- `diverted_flag`
- `distance_miles`
- `actual_elapsed_min`
- `scheduled_elapsed_min`[cite:25][cite:17]

### Script: `scripts/11_extract_faa_weather.py`

Purpose:

- Pull FAA ASPM/ASQP cancellation-with-weather data for the selected route pairs and date range.
- Save raw report exports and a normalized staging file.[cite:70][cite:145]

Inputs:

- `config/routes.yaml`
- `config/study.yaml`

Outputs:

- `data/raw/faa/faa_cancel_weather_<origin>_<dest>_<start>_<end>.xlsx|html|csv`
- `data/staging/faa_cancel_weather.csv`
- `data/raw/faa/manifest.csv`

Required behavior:

- Loop over configured route pairs and date windows.
- Save raw report payloads unchanged.
- Parse and normalize weather-related fields immediately after extraction.[cite:70]

Extraction approach:

- Attempt a session-aware `requests` or `curl` flow first.
- If the report requires form-postback or browser session behavior, encapsulate that fallback inside the script rather than relying on manual export.[cite:145][cite:70]

CLI example:

```bash
python scripts/11_extract_faa_weather.py \
  --routes config/routes.yaml \
  --study config/study.yaml \
  --out data/staging/faa_cancel_weather.csv
```

Required staging fields:

- `scheduled_departure_date`
- `carrier_code`
- `flight_number`
- `departure_airport`
- `arrival_airport`
- `scheduled_departure_time`
- `scheduled_arrival_time`
- `dep_wind`
- `dep_ceiling`
- `dep_visibility`
- `dep_nearby_ts`
- `dep_local_weather`
- `arr_wind`
- `arr_ceiling`
- `arr_visibility`
- `arr_nearby_ts`
- `arr_local_weather`[cite:70]

### Script: `scripts/12_extract_flightaware.py` (optional)

Purpose:

- Provide a recency extension or ATC-grounded validation layer for phase 2.[cite:49][cite:46]

Inputs:

- `FLIGHTAWARE_API_KEY`
- `config/routes.yaml`
- `config/study.yaml`

Outputs:

- `data/raw/flightaware/*.json`
- `data/staging/flightaware_history.csv`
- `data/raw/flightaware/manifest.csv`

Relevant endpoints:

- `GET /history/airports/{id}/flights/departures`
- `GET /history/airports/{id}/flights/arrivals`
- `GET /history/airports/{id}/to/{dest}`
- `GET /history/operator/{id}`[cite:49]

Header-based auth example:

```bash
curl -s \
  -H "x-apikey: $FLIGHTAWARE_API_KEY" \
  "https://aeroapi.flightaware.com/aeroapi/history/airports/LFT/to/DFW?date=2025-06-01"
```

Engineering note:

- Historical airport endpoint behavior may vary by recency or lookback window, so this script should remain optional and guarded by config.[cite:149][cite:49]

## Integration and fact-building

### Script: `scripts/20_build_flight_fact.py`

Purpose:

- Integrate BTS and FAA staging data, and optionally FlightAware, into a single curated flight fact table.[cite:25][cite:70][cite:49]

Inputs:

- `data/staging/bts_flights.csv`
- `data/staging/faa_cancel_weather.csv`
- optional `data/staging/flightaware_history.csv`
- `config/routes.yaml`
- `config/study.yaml`

Outputs:

- `data/curated/flight_operability_fact.csv`
- `output/qa_summary.csv`

Core logic:

1. Standardize date/time formats and carrier/flight identifiers.
2. Assign configured market baskets.
3. Join FAA cancellation-weather records onto BTS by:
   - flight date,
   - carrier code,
   - flight number,
   - origin,
   - destination,
   - scheduled departure time within a tolerance window, such as ±15 minutes.[cite:70][cite:17]
4. Derive key analytic flags.
5. Emit QA summaries and join-match diagnostics.[cite:70][cite:25]

Required curated columns:

- `flight_date`
- `year_month`
- `carrier_group`
- `carrier_code`
- `operating_carrier`
- `flight_number`
- `origin`
- `dest`
- `route_key`
- `sched_dep_local`
- `sched_arr_local`
- `dep_delay_min`
- `arr_delay_min`
- `cancelled_flag`
- `diverted_flag`
- `distance_miles`
- `cancellation_code_bts`
- `faa_dep_wind`
- `faa_dep_ceiling`
- `faa_dep_visibility`
- `faa_dep_nearby_ts`
- `faa_dep_local_weather`
- `faa_arr_wind`
- `faa_arr_ceiling`
- `faa_arr_visibility`
- `faa_arr_nearby_ts`
- `faa_arr_local_weather`
- `weather_bucket`
- `market_bucket`
- `period_flag`
- `severe_delay_flag`
- `operated_flag`[cite:25][cite:70]

### Weather-bucket derivation

Preferred approach:

- Use FAA ASPM severity levels such as None, Minor, Moderate, and Severe where available, since the ASPM Weather Factors module explicitly categorizes airport-hour weather impact using that scale.[cite:135]

Bucket rules:

- `benign`: both endpoints are `None` or `Minor`
- `marginal`: one endpoint is `Moderate`
- `adverse`: one or both endpoints are `Severe`, or both are at least `Moderate`[cite:135]

Fallback approach if only raw weather descriptors are available:

- `adverse` if fog, thunderstorms, very low visibility, or very low ceiling appears at either end.
- `marginal` if rain, mist, reduced visibility, or reduced ceiling appears without the stronger adverse conditions.
- `benign` otherwise.[cite:70][cite:129]

The exact thresholds and parsing logic must be documented in code comments and surfaced in the README.[cite:70][cite:135]

## Analysis specification

### Script: `scripts/30_analyze_fragility.py`

Purpose:

- Reduce the curated flight fact table to a chart-ready aggregate dataset and executive summary metrics.[cite:25][cite:70]

Input:

- `data/curated/flight_operability_fact.csv`

Outputs:

- `output/weather_fragility_chart_data.csv`
- `output/fragility_summary.json`

Aggregation grain:

- `market_bucket × weather_bucket × period_flag`

Required metrics:

- `flights_total`
- `cancelled_count`
- `operated_count`
- `severe_delay_count`
- `cancellation_rate`
- `severe_delay_rate`
- `avg_dep_delay_operated`
- optional peer-weighted benchmark metrics[cite:25]

Reference logic:

```python
agg = (
    fact.groupby(["market_bucket", "weather_bucket", "period_flag"])
        .agg(
            flights_total=("route_key", "size"),
            cancelled_count=("cancelled_flag", "sum"),
            operated_count=("operated_flag", "sum"),
            severe_delay_count=("severe_delay_flag", "sum"),
            avg_dep_delay_operated=("dep_delay_min", "mean"),
        )
        .reset_index()
)

agg["cancellation_rate"] = agg["cancelled_count"] / agg["flights_total"]
agg["severe_delay_rate"] = agg["severe_delay_count"] / agg["operated_count"]
```

The script should also compute executive annotation values such as AA regional cancellation-rate ratio versus peers under marginal weather.[cite:70][cite:135]

## Chart specification

### Script: `scripts/40_plot_fragility.py`

Purpose:

- Render a single executive-ready PNG chart from the aggregated chart dataset.[cite:25][cite:70]

Inputs:

- `output/weather_fragility_chart_data.csv`
- `output/fragility_summary.json`

Output:

- `output/weather_fragility_exec_chart.png`

Chart design:

- Two-panel grouped bar chart.
- Left panel: cancellation rate by weather bucket.
- Right panel: severe delay rate among operated flights by weather bucket.
- Series:
  - `AA_regional_basket`
  - `UA_peer_basket`
  - `DL_peer_basket`[cite:25][cite:70]

Rendering rules:

- Use a visually prominent color for AA regional and muted comparison colors for peers.
- Add direct labels or a clean legend.
- Add one annotation generated from computed results, such as “AA regional cancellation rate in marginal weather is 2.1x peers,” if supported by the data.[cite:70][cite:135]
- Fix output dimensions, for example 1600×900, for reproducibility.[cite:49]

## Orchestration

### Script: `scripts/run_pipeline.sh`

This script is the single-command entry point for reruns.[cite:145][cite:49]

```bash
#!/usr/bin/env bash
set -euo pipefail

bash scripts/00_setup_dirs.sh
python scripts/10_extract_bts.py --routes config/routes.yaml --study config/study.yaml
python scripts/11_extract_faa_weather.py --routes config/routes.yaml --study config/study.yaml

# Optional phase 2 validation layer
python scripts/12_extract_flightaware.py --routes config/routes.yaml --study config/study.yaml || true

python scripts/20_build_flight_fact.py --routes config/routes.yaml --study config/study.yaml
python scripts/30_analyze_fragility.py --study config/study.yaml
python scripts/40_plot_fragility.py
```

Suggested flags across scripts:

- `--force` to refresh raw downloads.
- `--skip-existing` to preserve current raw extracts.
- `--skip-flightaware` to disable the optional layer.
- `--study-override <path>` for alternate windows.[cite:145][cite:49]

## QA and reproducibility requirements

Each ETL script must write a manifest containing source parameters, extraction timestamp, row counts, and output filenames so reruns can be audited.[cite:145][cite:150]

Raw files must be treated as immutable unless a `--force` refresh is explicitly requested.[cite:150]

All downstream steps must be deterministic given the staged inputs and config files.[cite:145]

Minimum QA checks:

- BTS extract row counts by month.
- FAA extract row counts by route pair.
- Join-match rate between BTS cancelled flights and FAA cancellation-weather records.
- Null rate on `weather_bucket`.
- Final sample size by market basket, weather bucket, and period.[cite:70][cite:25]

Recommended acceptance thresholds:

- FAA-to-BTS cancelled-flight join rate of at least 85 percent, or documented explanation if lower.[cite:70]
- No chart bucket with trivially small counts; if counts are too sparse, merge `marginal` and `adverse` or expand the route basket.[cite:25]

## Risks and mitigations

### BTS extraction friction

TranStats exposes downloadable data through web flows rather than a simple modern REST API, so robust scripted extraction may require some request-pattern discovery or browser automation fallback.[cite:148][cite:150]

Mitigation:

- Build the extractor to support both direct HTTP and automated browser-export modes behind one script interface.[cite:148][cite:150]

### FAA report automation friction

FAA ASPM report export mechanics may require session handling or form-postback logic.[cite:145][cite:70]

Mitigation:

- Keep the FAA extraction inside one script with a stable staging output schema, regardless of underlying retrieval method.[cite:145]

### Route sparsity

LFT–DFW alone may be too thin for a decisive signal.[cite:25]

Mitigation:

- Retain LFT–DFW as the narrative anchor but expand to nearby spoke baskets for statistical stability.[cite:25]

### Peer comparability

Exact peer route matches may not exist.[cite:25][cite:17]

Mitigation:

- Use comparable short-haul spoke-to-hub baskets and keep stage lengths similar.[cite:17][cite:25]

### FlightAware cost or window limits

FlightAware historical endpoints are useful, but should remain optional because endpoint behavior, lookback mechanics, and paid usage may complicate the initial build.[cite:49][cite:149][cite:46]

Mitigation:

- Keep FlightAware out of the critical path for phase 1.[cite:49]

## Deliverables

The coding agent should produce the following outputs:

1. `data/curated/flight_operability_fact.csv` — integrated flight-level fact table.[cite:25][cite:70]
2. `output/weather_fragility_chart_data.csv` — chart-ready aggregated metrics.[cite:25]
3. `output/weather_fragility_exec_chart.png` — single executive PNG chart.[cite:25][cite:70]
4. `output/qa_summary.csv` — row counts, join rates, null rates, and validation checks.[cite:70][cite:25]
5. `README.md` — run instructions, environment variables, source notes, caveats, and reproducibility guidance.[cite:145][cite:49][cite:150]

## Definition of done

This proof of concept is complete when a new repository can run a single orchestrating script and produce raw ETL artifacts, a curated flight fact table, a chart-ready aggregate CSV, a QA summary, and one executive-ready PNG with no manual intervention beyond supplying credentials or config values.[cite:145][cite:148][cite:49]
