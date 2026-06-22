# Flight Fragility POC

A reproducible proof-of-concept analysis to determine whether American Airlines'
regional service in LFT and nearby spoke markets shows greater weather-related
schedule fragility than comparable peer markets.

> 📌 **National-scale results are in — start with
> [BIGRUN-FINDINGS-GUIDE.md](BIGRUN-FINDINGS-GUIDE.md).** The full pipeline has
> been run across American's complete 9-hub network (6.15M flights, 24 months)
> on a high-memory server. That guide is the top-level read-out; this README
> remains the engineering/method reference.

## Specifications

Design specs for each analytical pass live in [`spec/`](spec/):

- [Fragility I — focal corridor](spec/flight_fragility_poc_spec.md)
- [Fragility II — controllable / cascade disruption](spec/flight_fragility_ii_machine_addon_spec.md)
- [Fragility III — economic burden](spec/flight_fragility_iii_show_me_the_money_addon_spec.md)
- [Fragility IV — operator attribution + hub-spoke expansion](spec/flight_fragility_iv_operator_attribution_spec.md)
- [Fragility V — network hotspot engine](spec/flight_fragility_v_network_hotspot_spec.md)

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

## Fragility IV: operator attribution and hub-spoke expansion

Fragility I-III ask whether AA's focal-corridor regional service, taken as a
whole, shows a weather-fragility signature relative to UA/DL peers.
Fragility IV (`flight_fragility_iv_operator_attribution_spec.md`) asks a
narrower question: does that signature differ by *which* operating structure
flew the flight — AA mainline, Envoy Air, PSA Airlines, or SkyWest/Republic
under their resolved mainline contracts — and does it generalize beyond the
focal corridor to a hub-spoke expansion at additional AA hubs? It is built as
two modules sharing one operator-attribution methodology:

- **Module A (focal corridor)** reuses the existing
  `data/curated/flight_operability_fact.csv` unchanged, adding an
  `operator_class` column.
- **Module B (hub-spoke expansion)** is net-new extraction at a configurable
  set of hubs (`config/study.yaml` `run_mode_hubs`), with the spoke-market
  universe discovered from the data rather than hand-enumerated.

A `run_mode` setting (`test` / `local` / `bigrun`, `config/study.yaml`) scopes
Module B's hub list and date window: `test` (DFW only, January 2024) is sized
for this sandboxed container; `local` (DFW/CLT/ORD/PHL, full 2024-2025) and
`bigrun` (full configured network, hubs set explicitly) are intended for
provisioned infrastructure with more runtime and storage. See
[AAR.md](AAR.md), "Fragility IV: Operator Attribution," for the implementation
record, a bug found and fixed during validation, and the current validation
status — a `test`-mode structural smoke test has been run successfully, but no
`local`- or `bigrun`-scale result exists yet, so no Fragility IV finding is
reported.

## Data sources

| Source | Description | Phase |
|--------|-------------|-------|
| [BTS TranStats On-Time Performance](https://www.transtats.bts.gov/DL_SelectFields.aspx?gnoyr_VQ=FGJ) | Scheduled / actual times, cancellations, delays | Phase 1 (required); also used for Fragility IV Module B at a configurable hub list |
| [NOAA ASOS hourly weather, via Iowa Environmental Mesonet](https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py) | Hourly airport-level METAR observations (visibility, ceiling, present weather) at every study airport | Phase 1 (required); also used for Fragility IV Module B at the discovered hub-spoke airport universe |
| [FlightAware AeroAPI](https://www.flightaware.com/aeroapi/portal) | Historical flight-level data | Phase 2 bulk extraction (optional, `use_flightaware`, dormant); separately, targeted single-flight operator-ambiguity validation for Fragility IV (optional, `resolve_operator_ambiguity`, see below) |

The original spec called for FAA ASPM cancellation-with-weather reports as the
weather source. That system requires a restricted FAA-registered login and,
even with access, only covers cancelled flights — see [AAR.md](AAR.md) for why
it was replaced with NOAA ASOS and what changed as a result.

### Operator-class resolution and targeted FlightAware validation

BTS On-Time Performance has no marketing-carrier field distinct from the
reporting/operating carrier code, so most operator classes (`AA_mainline`,
`Envoy_operated`, `PSA_operated`) resolve directly from `carrier_code`. Two
codes are genuinely ambiguous because each flies under more than one
mainline brand: `OO` (SkyWest: American Eagle/United Express/Delta
Connection/Alaska Airlines) and `YX` (Republic: American Eagle/United
Express/Delta Connection). These are resolved in priority order:

1. **Route-context inference** (`scripts/lib/operator_classify.py`) — if the
   route already belongs to a pre-validated basket
   (`config/routes.yaml`), that basket assignment implies the mainline
   contract. This resolves the large majority of Module A's ambiguous rows
   for free.
2. **Targeted FlightAware AeroAPI validation** (`scripts/15_resolve_operator_ambiguity.py`)
   — for rows route-context inference can't resolve (chiefly Module B, which
   has no pre-built basket), a single-flight historical lookup
   (`GET /history/flights/{ident}`) inspects that flight's codeshares for an
   AA/UA/DL/AS-prefixed identifier. This is a narrow, per-flight query, never
   a bulk historical pull — gated independently of `use_flightaware` by
   `config/study.yaml`'s `resolve_operator_ambiguity.enabled` and a
   `max_queries` budget, and a no-op (writes an empty resolution file) if
   `FLIGHTAWARE_API_KEY` is unset, so the rest of the pipeline never depends
   on a live key.
3. Anything still unresolved keeps a `SkyWest_unresolved` / `Republic_unresolved`
   label and is excluded from operator-class comparisons (disclosed in QA
   notes and chart-summary caveats).

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
  AAR.md               ← after-action report: decisions, issues found and fixed, run results
  LEADERSHIP_READOUT_NOTES.md  ← append-only, phase-by-phase leadership-facing synthesis
  requirements.txt
  .env.example

  config/
    routes.yaml                ← route basket definitions (Module A)
    study.yaml                  ← study dates, thresholds, feature flags, run_mode/backend controls
    economic_scenarios.yaml     ← Fragility III/IV cost-proxy scenario inputs
    operator_classes.yaml       ← carrier_code -> operator_class mapping (Fragility IV/V)

  data/
    raw/
      bts/                      ← monthly BTS raw CSVs + manifest.csv (Module A)
      faa/                      ← NOAA ASOS raw export + manifest.csv (Module A)
      flightaware/              ← FlightAware JSON payloads + manifest.csv (phase 2 bulk, optional)
      bts_hubspoke/              ← monthly BTS raw CSVs + discovered_airports.csv + manifest.csv (Module B)
      faa_hubspoke/               ← NOAA ASOS raw export + manifest.csv (Module B)
      flightaware_resolution/    ← targeted single-flight lookups + manifest.csv (Fragility IV operator resolution)
    staging/                    ← normalized per-source staging CSVs/Parquet
    curated/
      flight_operability_fact.csv     ← Module A integrated flight fact table
      hubspoke_operator_fact/         ← Module B integrated flight fact table (Hive-partitioned Parquet, by year_month)

  scripts/
    lib/
      backend.py                 ← pandas/duckdb/polars aggregation backend abstraction
      operator_classify.py       ← operator_class derivation + FlightAware-resolution overrides
    00_setup_dirs.sh                  ← directory setup and config validation
    10_extract_bts.py                 ← BTS ETL (Module A)
    11_extract_faa_weather.py         ← NOAA ASOS ETL (Module A)
    12_extract_flightaware.py         ← FlightAware bulk ETL (phase 2, optional, dormant)
    13_extract_bts_hubspoke.py        ← BTS ETL (Module B, hub-spoke expansion)
    14_extract_weather_hubspoke.py    ← NOAA ASOS ETL (Module B)
    15_resolve_operator_ambiguity.py  ← targeted FlightAware operator-ambiguity validation (Fragility IV)
    20_build_flight_fact.py           ← integration and fact table (Module A)
    21_build_hubspoke_fact.py         ← integration and fact table (Module B)
    30_analyze_fragility.py           ← Fragility I aggregation and executive metrics
    31_analyze_fragility_machine.py   ← Fragility II controllable/cascade aggregation
    32_analyze_fragility_money.py     ← Fragility III economic-burden cost proxy
    33_analyze_fragility_operator.py  ← Fragility IV operator-attribution scorecard (Module A + B)
    40_plot_fragility.py              ← Fragility I chart rendering
    41_plot_fragility_machine.py      ← Fragility II chart rendering
    42_plot_fragility_money.py        ← Fragility III chart rendering
    43_plot_fragility_operator.py     ← Fragility IV chart rendering
    run_pipeline.sh                   ← one-command orchestrator, Fragility I-III
    run_pipeline_iv.sh                ← one-command orchestrator, Fragility IV (requires run_pipeline.sh has run at least once)
    run_pipeline_v.sh                 ← one-command orchestrator, Fragility V (requires run_pipeline_iv.sh has run at least once)
    34_analyze_fragility_hotspots.py  ← Fragility V network hotspot scoring engine (Modules A–E)
    44_plot_fragility_hotspots.py     ← Fragility V executive chart rendering

  output/
    weather_fragility_chart_data.csv           ← Fragility I chart-ready aggregate metrics
    fragility_summary.json                     ← Fragility I executive annotation values
    weather_fragility_exec_chart.png            ← Fragility I deliverable PNG chart
    weather_fragility_machine_chart_data.csv    ← Fragility II chart-ready aggregate metrics
    fragility_ii_machine_summary.json           ← Fragility II executive annotation values
    fragility_ii_summary.md                     ← Fragility II written result summary
    fragility_ii_operator_breakdown.csv         ← Fragility II controllable/cascade by regional operator
    weather_fragility_machine_exec_chart.png    ← Fragility II deliverable PNG chart
    fragility_iii_chart_data.csv                ← Fragility III chart-ready cost-proxy data
    fragility_iii_summary.json                  ← Fragility III executive annotation values
    fragility_iii_summary.md                    ← Fragility III written result summary
    fragility_iii_exec_chart.png                ← Fragility III deliverable PNG chart
    fragility_iv_operator_chart_data.csv        ← Fragility IV chart-ready operator-attribution scorecard
    fragility_iv_operator_scorecard.parquet     ← same scorecard, Parquet (best-effort; CSV is authoritative)
    fragility_iv_summary.json                   ← Fragility IV executive annotation values
    fragility_iv_summary.md                     ← Fragility IV written result summary
    fragility_iv_operator_exec_chart.png        ← Fragility IV deliverable PNG chart
    fragility_v_hotspot_scorecard.parquet/      ← Fragility V hotspot scores, all cells (Hive-partitioned by hub_family)
    fragility_v_hotspot_rankings.csv            ← Fragility V top-N ranked cells with all component scores
    fragility_v_exec_chart.png                  ← Fragility V executive chart (stacked hotspot scorecard)
    fragility_v_hub_rollup.csv                  ← Fragility V hub concentration in top-N
    fragility_v_operator_rollup.csv             ← Fragility V operator concentration in top-N (resolved operators only)
    fragility_v_scenario_robustness.csv         ← Fragility V robustness scores across all scenarios
    fragility_v_summary.json                    ← Fragility V executive annotation values
    fragility_v_summary.md                      ← Fragility V written prioritization memo
    qa_summary.csv                              ← row counts, join rates, null rates (Module A)
    qa_summary_hubspoke.csv                     ← row counts, operator/hub-family counts, null rates (Module B)
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
# Full Fragility I-III pipeline (single command)
bash scripts/run_pipeline.sh

# With options
bash scripts/run_pipeline.sh --force               # re-download raw data
bash scripts/run_pipeline.sh --skip-flightaware    # skip FA extraction
bash scripts/run_pipeline.sh --study-override config/study_2024_only.yaml

# Fragility IV pipeline (requires run_pipeline.sh has produced
# data/curated/flight_operability_fact.csv at least once)
bash scripts/run_pipeline_iv.sh
bash scripts/run_pipeline_iv.sh --run-mode local   # override study.yaml's run_mode
bash scripts/run_pipeline_iv.sh --force

# Run individual steps
python scripts/10_extract_bts.py --routes config/routes.yaml --study config/study.yaml
python scripts/11_extract_faa_weather.py --routes config/routes.yaml --study config/study.yaml
python scripts/20_build_flight_fact.py --routes config/routes.yaml --study config/study.yaml
python scripts/30_analyze_fragility.py --study config/study.yaml
python scripts/31_analyze_fragility_machine.py --study config/study.yaml
python scripts/40_plot_fragility.py
python scripts/41_plot_fragility_machine.py
python scripts/32_analyze_fragility_money.py --study config/study.yaml --econ-config config/economic_scenarios.yaml
python scripts/42_plot_fragility_money.py

# Fragility IV individual steps
python scripts/13_extract_bts_hubspoke.py --study config/study.yaml
python scripts/14_extract_weather_hubspoke.py --study config/study.yaml
python scripts/15_resolve_operator_ambiguity.py --study config/study.yaml
python scripts/21_build_hubspoke_fact.py --study config/study.yaml
python scripts/33_analyze_fragility_operator.py --study config/study.yaml
python scripts/43_plot_fragility_operator.py

# Fragility V pipeline (requires run_pipeline_iv.sh has run and produced
# data/curated/hubspoke_operator_fact/)
bash scripts/run_pipeline_v.sh
bash scripts/run_pipeline_v.sh --run-mode local   # override study.yaml's run_mode

# Fragility V individual steps
python scripts/34_analyze_fragility_hotspots.py --study config/study.yaml
python scripts/44_plot_fragility_hotspots.py
```

## Environment variables

| Variable              | Required | Description                                       |
|-----------------------|----------|---------------------------------------------------|
| `FLIGHTAWARE_API_KEY` | No       | FlightAware AeroAPI key. Used by two independently-gated paths: phase 2 bulk extraction (`use_flightaware: true`, dormant) and Fragility IV's targeted single-flight operator-ambiguity validation (`resolve_operator_ambiguity.enabled: true`, `scripts/15_resolve_operator_ambiguity.py`). Both no-op safely if unset. |

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

### Fragility IV/V — national bigrun (2026-06-21)

> **Status: Full pipeline executed across American's complete 9-hub network**
> (DFW, CLT, ORD, PHL, MIA, PHX, DCA, LAX, JFK), keyless, on a high-memory
> server. **6,152,599 flights**, 264 airports, 24 months, duckdb backend,
> 100.0% weather match, ~63 min wall-clock. See
> [BIGRUN-FINDINGS-GUIDE.md](BIGRUN-FINDINGS-GUIDE.md) and
> [AAR.md](AAR.md) Iteration 10.
>
> - **Core finding robust to scale:** Fragility IV top cell (PSA at ORD, adverse)
>   and Fragility V rank-1 hotspot (ORD–SPI) unchanged from the 4-hub baseline.
> - **PSA over-represented 4.25×** in the worst-5% of 1,668 ranked cells (51.8%
>   of worst cells, 12.2% of flights); **Envoy under-represented (0.16×)** — a
>   second wholly-owned regional at the opposite end, establishing the result is
>   operating-structure-specific, not anti-regional.
> - **DFW–LFT** (PSA-operated) ranks #63 of 1,668 (top 3.8%, cascade-driven).
> - **904,924 flights (14.7%)** remain operator-ambiguous and are conservatively
>   excluded from operator comparisons.

### Fragility I — weather-stratified cancellation (focal corridor)

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
> reported as observed.
>
> A further breakdown by regional operator within the AA basket (BTS's
> reporting-carrier field is already operator-level for these routes — see
> [output/fragility_ii_summary.md](output/fragility_ii_summary.md) section 6
> and [AAR.md](AAR.md)) finds the basket-level pattern is not uniform across
> Envoy Air (MQ), PSA Airlines (OH), and SkyWest (OO): Envoy and PSA show the
> low-controllable / high-and-escalating-cascade profile, while SkyWest
> within the AA basket shows the opposite — a high and weather-escalating
> controllable rate with a low, flat cascade rate — a profile that also
> appears for SkyWest under its DL contract, suggesting an operator-level
> rather than AA-contract-specific signature for SkyWest specifically. Full
> detail, sample sizes, and caveats are in [AAR.md](AAR.md).

### Fragility III: economic impact estimation

> **Status: Implemented as a third add-on per
> `flight_fragility_iii_show_me_the_money_addon_spec.md`, run against the
> same live data.**
>
> Fragility III converts the excess disruption Fragility I and II already
> measured into a scenario-based dollar-burden proxy, using published public
> cost benchmarks (A4A's 2024 airline block-time cost, DOT/FAA passenger
> value-of-time guidance) rather than internal accounting data. It runs in
> the spec's "Fragility II-preferred" mode: the cost basis is excess
> controllable (carrier-attributed) delay minutes plus excess cascade
> (late-aircraft) delay minutes, using BTS's own reported cause-minute
> fields, with a separate scenario-based cancellation-equivalent-minutes
> lever for excess cancellations. See
> [output/fragility_iii_summary.md](output/fragility_iii_summary.md) for
> the full write-up and caveats.
>
> | Component | Excess vs. peer-average rate (study window) |
> |---|---|
> | Cancellations | 270 flights |
> | Controllable (carrier-attributed) delay minutes | -33,214 min |
> | Cascade (late-aircraft) delay minutes | 52,106 min |
> | **Net excess delay-minutes basis** | **18,891 min** |
>
> | Scenario | Airline operating-time burden | Passenger-time burden (flight-level proxy) | Combined |
> |---|---|---|---|
> | Low  | $1,511,296 | $48,838  | $1,560,134 |
> | Base | $1,903,477 | $90,975  | **$1,994,452** |
> | High | $2,266,944 | $148,554 | $2,415,498 |
>
> The controllable component is negative — AA regional's carrier-attributed
> delay minutes run below the peer-average expectation, consistent with
> Fragility II's controllable-rate finding — while the larger, positive
> cascade component drives the net total. That net total is also not spread
> evenly across weather: nearly all of it is concentrated in the
> *benign*-weather bucket, while marginal and adverse weather each run
> negative on this basis. The economic burden this study can attach to AA's
> elevated cascade exposure therefore presents as a baseline/schedule-
> resilience cost rather than a weather-stress cost — see
> [output/fragility_iii_summary.md](output/fragility_iii_summary.md) section 4.
>
> These are scenario-based proxies built from published benchmarks, not
> audited revenue, voucher, or reaccommodation expense, and they are not
> scaled by an actual passenger count (no passenger-manifest data exists in
> this pipeline's public sources) — see the full caveats in
> [output/fragility_iii_summary.md](output/fragility_iii_summary.md) and
> [AAR.md](AAR.md).

### Fragility IV: operator attribution

> **Status: Implemented (Module A + Module B, `scripts/13`–`15`, `21`, `33`,
> `43`) and run end-to-end at local-mode scale (DFW/CLT/ORD/PHL, Jan 2024–Dec 2025,
> 3.59M flights).** See [AAR.md](AAR.md) "Fragility IV" for the implementation
> record, three data-pipeline bugs found and fixed during local-mode execution
> (NOAA rate-limiting, cache-key collision, normalize_noaa() performance), and
> the full QA and results detail.
>
> Headline result: PSA_operated at ORD shows the highest combined fragility score
> (0.225) among cells meeting the minimum sample threshold — 186 flights in
> adverse weather during the 2025 recent period, with a 22.6% cancellation rate,
> 39.6% severe delay rate, and a cascade (late-arriving) severe delay rate of
> 21.5% vs. a controllable rate of 6.3%. The cascade-dominant, controllable-low
> signature observed in the original focal corridor appears here at a different
> hub and operator, extending the observation beyond the original corridor.
>
> 485,006 flights remain in unresolved operator-ambiguity labels
> (SkyWest_unresolved / Republic_unresolved) and are excluded from operator-class
> comparisons — expected, since `FLIGHTAWARE_API_KEY` is unset and the
> targeted-validation step correctly no-ops. See
> [output/fragility_iv_summary.md](output/fragility_iv_summary.md) and
> [output/fragility_iv_operator_exec_chart.png](output/fragility_iv_operator_exec_chart.png).

### Fragility V: network hotspot engine

> **Status: Implemented (`scripts/34`, `44`, `run_pipeline_v.sh`) and run at
> local-mode scale, consuming the Fragility IV curated layer directly.**
>
> Fragility V scores all 1,304 (hub_family × spoke_airport × operator_class)
> cells from the Fragility IV curated data using a six-component composite
> hotspot score (cancellation rate, severe-delay rate, controllable severe-delay
> rate, cascade severe-delay rate, adverse-weather fragility rate, economic
> burden per 1,000 flights), with 4 robustness scenarios and a persistence
> check. 1,070 of 1,304 cells meet the min-flights threshold (100) and are
> ranked.
>
> Headline results: DFW and ORD together account for 95% of the top-20 hotspot
> cells; CLT accounts for 0%. Among resolved operators, PSA_operated holds 67%
> of the top-20 slots. The dominant fragility signature across the top-20 is
> economic burden (7 cells) and cascade (5 cells), not weather sensitivity
> (1 cell). 3 of the top-20 cells are persistent (top-20 in both the 2024
> baseline and 2025 recent periods). See
> [output/fragility_v_summary.md](output/fragility_v_summary.md) and
> [output/fragility_v_exec_chart.png](output/fragility_v_exec_chart.png).

See the [After Action Report](AAR.md) for decisions made, issues encountered,
and next steps.

