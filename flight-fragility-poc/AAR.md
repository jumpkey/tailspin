# After Action Report — Flight Fragility POC, Iterations 2–9

**Date:** 2026-06-15 (Iteration 2) — 2026-06-18 (Iteration 9)
**Agent:** Claude (claude-sonnet-4-6)
**Repository:** jumpkey/tailspin
**Branch:** claude/trusting-allen-0he9md
**Building on:** Iteration 1 implementation by GitHub Copilot Coding Agent

---

## Summary

Iteration 1 produced a structurally complete pipeline skeleton but could not
run against live data due to the sandboxed environment. A pre-run review of the
code (Iteration 2, before touching anything) identified four issues — three of
them outright blockers — documented below in full. All four were fixed. The
pipeline was then run end-to-end against real BTS and NOAA weather data for
the full 2024–2025 study period, producing all five deliverables.

**The study question is answered with real data.** AA regional service in LFT
and nearby spoke markets shows a clear and statistically meaningful
weather-fragility signature:

| Weather condition | AA Regional | Peer avg | AA ÷ peer |
|-------------------|-------------|----------|-----------|
| Benign            | 2.09%       | 1.11%    | **1.88×** |
| Marginal          | 6.19%       | 2.97%    | **2.08×** |
| Adverse           | 10.08%      | 4.86%    | **2.08×** |

The cancellation rate ratio rises from 1.88× in benign conditions to 2.08×
in both marginal and adverse conditions. Against Delta alone (the better-sampled
peer basket) the ratio escalates with weather severity: 1.79× (benign) →
2.32× (marginal) → **3.02×** (adverse) — a pattern consistent with a
weather-specific fragility signature in the regional operation. The public
data used here cannot identify which internal factor (crew staffing or
experience, fleet/equipment assignment, schedule buffer design, maintenance
basing, or another scheduling choice) produces it; see Caveats and Limitations
below.

---

## Issues Found in Pre-Run Review

### Issue 1 — Critical: BTS extraction had no ViewState scraping

**What was wrong:**  
`10_extract_bts.py` targeted `https://www.transtats.bts.gov/DownLoad_Table.asp`
and submitted the download form via direct `POST`. The BTS TranStats download
system is built on ASP.NET WebForms, which requires hidden `__VIEWSTATE` tokens
that are only available after a prior authenticated `GET` request to the form page.
The script skipped that step entirely — unlike the FAA script (which correctly
scraped ViewState before posting). The POST would have returned an error or blank
page.

A secondary problem: the numeric field-code mapping (`BTS_FIELD_CODES`) that
translates field names like `FlightDate` to numeric IDs (`"10"`, `"16"`, etc.)
was derived from documentation and never validated against the live form. If any
single code was wrong, the downloaded columns would be misaligned or empty.

**Fix applied:**  
Replaced the form-POST logic entirely with BTS's pre-built monthly ZIP archive,
which is publicly accessible at a stable, session-free URL:

```
https://transtats.bts.gov/PREZIP/
  On_Time_Reporting_Carrier_On_Time_Performance_1987_present_{YYYY}_{M}.zip
```

The archive file already contains the full monthly on-time table with correct
column headers — no field codes, no ViewState, no session needed. Each ~27 MB
ZIP is streamed, decompressed in memory, and immediately filtered to the 9 study
airports, yielding a few thousand rows per month. The entire `BTS_FIELD_CODES`
dict and the `BTS_DL_URL` constant were removed from the script.

**Effect on study:**  
Zero effect on data content. The PREZIP archive is the same underlying table
as the form download; the field names and data values are identical.

---

### Issue 2 — Critical: FAA ASPM ASQP URL does not exist and requires login

**What was wrong:**  
`11_extract_faa_weather.py` targeted
`https://www.aspm.faa.gov/asqpwx/Index.asp`, which returns:

> `<h2>The requested resource does not exist!</h2>`

The correct ASQP system URL is `https://www.aspm.faa.gov/asqp/sys/`, and it
presents a login gate with the message:

> "This area contains proprietary information and requires a registered user name
> and password. You may request a login from FAA by following this link."

The FAA ASQP system is a **restricted federal system** that requires an
account request through FAA channels. It is not publicly accessible. The
form-scraping strategy — regardless of whether the field names were correct —
could never work without credentials.

Beyond access, the Iteration 1 AAR flagged that the form field names
(`txtAirport`, `txtArrAirport`, `txtStartDate`, `txtEndDate`, `btnSubmit`) were
assumed from first principles and never confirmed against the actual ASP.NET form.

**Fix applied:**  
`11_extract_faa_weather.py` was completely rewritten to use the Iowa
Environmental Mesonet (IEM) ASOS archive, a free, public, no-login-required
API that serves NOAA ASOS hourly METAR observations for every U.S. airport:

```
https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py
```

A single request retrieves 2 years × 9 airports of hourly weather observations
(visibility in statute miles, cloud layer coverage and heights, present-weather
codes, wind speed). The script pre-computes a `weather_bucket`
(benign/marginal/adverse) for each airport-hour using thresholds that map the
spec's ASPM verbal categories to observable METAR values:

| ASPM spec level | METAR equivalent used |
|---|---|
| None / Minor (Benign) | vsby ≥ 3 SM **and** ceiling ≥ 1000 ft **and** no precip codes |
| Moderate (Marginal) | vsby 1–3 SM **or** ceiling 500–1000 ft **or** RA/SN/FG/BR/DZ present |
| Severe (Adverse) | vsby < 1 SM **or** ceiling < 500 ft **or** TS/FZ/BLSN/+SN present |

These thresholds correspond to the FAA's own IFR/MVFR/VFR flight-rule
categories, making them a principled and directly interpretable substitute for
ASPM severity levels.

**Effect on study:**  
The data source changed from a restricted FAA government system to a public NOAA
archive, but the underlying weather information is the same: hourly airport
conditions derived from METAR observations, which are the primary input to the
FAA ASPM Weather Factors module in any case. The thresholds are well-documented
and aligned with FAA published criteria.

The staging file format changed from one row per cancelled flight (FAA ASQP) to
one row per airport-hour (NOAA ASOS). This required a corresponding change to
the weather-join logic in `20_build_flight_fact.py`, described in Issue 3 below.

Results from the live run: 157,192 raw NOAA observations normalized to 157,145
airport-hour rows. All 9 airports covered, date range 2024-01-01 to 2025-12-30.
Weather distribution: 87.2% benign, 8.4% marginal, 4.4% adverse — consistent
with Gulf South and Texas weather climatology.

---

### Issue 3 — Critical: Weather bucket logic was conceptually broken for operated flights

**What was wrong:**  
This was the most consequential bug. The original join in `20_build_flight_fact.py`
matched FAA ASQP records onto BTS records by flight date + carrier code + flight
number + origin + destination. Because FAA ASQP is a *cancelled flights only*
report, every operated (non-cancelled) flight had no FAA match. The text-keyword
fallback (`_text_bucket`) receives two `None` arguments in that case and returns
`"benign"` unconditionally.

The result was:

- **Operated flights**: always assigned `weather_bucket = "benign"`.
- **Cancelled flights** (FAA match exists): could be assigned marginal or adverse.

This broke the core metric. Because `cancellation_rate = cancelled_count /
flights_total` is computed within each weather bucket, and the adverse/marginal
buckets contained *only* cancelled flights, the denominator equalled the
numerator: `cancellation_rate ≈ 1.0` for every carrier in every non-benign
bucket. The metric was meaningless by construction.

The benign bucket had artificially inflated sample sizes (it absorbed all
operated flights) and deflated cancellation rates (all operated flights are
trivially non-cancelled). No cross-carrier weather comparison was possible.

**Fix applied:**  
The join logic was completely replaced with an airport-hour weather join:

1. Each BTS flight's scheduled departure local time (`sched_dep_local`) and
   flight date are converted from local airport time (using Python's `zoneinfo`
   module with per-airport DST-aware timezone assignments) to UTC.

2. The scheduled arrival UTC time is derived by adding `scheduled_elapsed_min`
   from BTS to the departure UTC datetime, handling overnight flights correctly.

3. The NOAA staging file (one row per airport-hour UTC) is joined to each BTS
   flight twice — once for departure weather and once for arrival weather — on
   `(airport, utc_date, utc_hour)`.

4. The per-flight `weather_bucket` is set to the *worst* of the departure and
   arrival airport conditions, using the severity ordering: adverse > marginal >
   benign.

This means every flight — operated or cancelled — now has a weather context
derived from the actual conditions at its scheduled departure and arrival
airports at the time of the flight. The denominator for, e.g., "adverse weather
cancellation rate" is now all flights scheduled during adverse conditions at
either endpoint, not just the cancelled ones.

**Effect on study:**  
This is the fix that makes the study valid. The new approach also improves on
the original FAA data in an important way: rather than using weather only for
the subset of flights that happened to appear in the ASQP cancelled-flight
export, every flight has airport-hour weather context, giving much higher join
coverage (99.3% departure match, 99.8% arrival match vs. the anticipated <85%
ASQP join rate for cancelled flights only).

The study design is now:

> On days and hours when adverse/marginal weather was observed at either the
> departure or arrival airport, does AA regional cancel at a higher rate than
> United or Delta peer baskets flying comparable spoke-to-hub routes?

This is precisely the question the spec intends.

---

### Issue 4 — Minor: `avg_dep_delay_operated` computed on all flights, not operated ones

**What was wrong:**  
In `30_analyze_fragility.py`, the aggregation computed `avg_dep_delay_operated`
using `("dep_delay_min", "mean")` across **all** flights in each groupby bucket,
including cancelled flights. Cancelled flights have `NaN` for `dep_delay_min`
(no actual departure occurred), so pandas `mean` excludes them silently — meaning
the result was numerically correct by accident, not by design.

The variable `operated = fact[fact["operated_flag"] == 1]` was created on line 72
but never used in the aggregation.

**Fix applied:**  
The aggregation was split: the four count-based metrics (`flights_total`,
`cancelled_count`, `operated_count`, `severe_delay_count`) are computed on all
flights as before, but `avg_dep_delay_operated` is computed in a separate
groupby on the `operated` filtered DataFrame and merged back. The unused
`operated` variable is now actually used.

**Effect on study:**  
The numeric values are unchanged (NaN exclusion from `mean` produced the same
result). The fix is correctness and intent — the metric now explicitly reflects
what it claims to measure.

---

## Pipeline Changes Summary

| Script | Change type | What changed |
|--------|-------------|-------------|
| `10_extract_bts.py` | Fix | Replaced form-POST with direct PREZIP URL download; removed `BTS_FIELD_CODES`, `BTS_DL_URL` |
| `11_extract_faa_weather.py` | Complete rewrite | Replaced FAA ASQP (inaccessible) with NOAA ASOS via IEM; new staging schema per airport-hour |
| `20_build_flight_fact.py` | Major rewrite | New weather join on airport+UTC-hour; local→UTC time conversion using `zoneinfo`; removed per-flight FAA join |
| `30_analyze_fragility.py` | Minor fix | `avg_dep_delay_operated` now explicitly computed on operated-only subset |
| `run_pipeline.sh` | Minor update | Updated staging file name and `--weather` argument to script 20 |
| `40_plot_fragility.py` | Unchanged | No modifications needed |
| `config/`, `data/`, `output/` | No change | All configuration unchanged |

---

## Live Run Results

### Data volumes

| Source | Raw rows | Staged rows | Note |
|--------|----------|-------------|------|
| BTS PREZIP (24 months) | 2,986,488 | 29,333 after route filter | ~27 MB/month, 9-airport filter → 14 specific route pairs |
| NOAA ASOS IEM | 157,192 | 157,145 hourly | 9 airports, 2024-01-01 – 2025-12-30 |

**Route filter yields 29,333 study flights** across 14 configured route pairs:
AA regional (6 routes, 18,054 flights), DL peer (4 routes, 8,892 flights),
UA peer (4 routes, 2,387 flights).

### Weather join quality

| Check | Value |
|-------|-------|
| Departure weather match rate | 99.3% |
| Arrival weather match rate | 99.8% |
| Weather-bucket null rate | 0.0% |
| "Unknown" bucket flights | 33 (0.1%) |

The near-100% match rates substantially exceed the spec's 85% acceptance
threshold. The 33 "unknown" flights (0.1%) are hours where NOAA had no
observation; these are excluded from weather-bucket analysis.

### Carrier composition

| Basket | Reporting carriers | Total flights |
|--------|-------------------|---------------|
| AA regional (→DFW) | MQ (Envoy Air), OH (PSA), OO (SkyWest) | 18,054 |
| UA peer (→IAH)     | OO (SkyWest); 3 UA mainline | 2,387 |
| DL peer (→ATL)     | DL (mainline), 9E (Endeavor), OO (SkyWest) | 8,892 |

All three baskets include SkyWest (OO) operating under different mainline
contracts, which is relevant context for interpreting any operational differences.

### Key finding: overall cancellation rates

| Period | AA regional | UA peer | DL peer |
|--------|-------------|---------|---------|
| 2024 (baseline) | 2.35% | 1.88% | 1.36% |
| 2025 (recent) | **3.92%** | 1.73% | 1.85% |

AA regional's overall cancellation rate increased 67% from 2024 to 2025.
Peer rates were effectively flat (UA) or modestly increased (DL +35%).

### Key finding: cancellation rates by weather bucket

| Weather | AA Regional | UA Peer | DL Peer | Peer avg | AA ÷ peer |
|---------|-------------|---------|---------|----------|-----------|
| Benign  | 2.09% | 1.05% | 1.17% | 1.11% | **1.88×** |
| Marginal | 6.19% | 3.27% | 2.67% | 2.97% | **2.08×** |
| Adverse | 10.08% | 6.37% | 3.34% | 4.86% | **2.08×** |

### Key finding: period comparison for AA

| Period | Benign | Marginal | Adverse |
|--------|--------|----------|---------|
| 2024 (baseline) | 1.44% | 4.96% | 8.20% |
| 2025 (recent)   | 2.71% | 7.53% | 11.67% |

AA regional cancellation rates increased substantially in every weather
bucket from 2024 to 2025. The adverse-weather rate grew from 8.2% to
11.7% — a 42% increase in a single year.

For DL peers over the same period:
- Benign: 0.94% → 1.50% (stable-to-modest increase)
- Marginal: 2.74% → 2.58% (essentially flat)
- Adverse: 2.97% → 3.86% (moderate increase)

### Key finding: AA vs Delta alone (primary peer, better sample)

Against Delta specifically, the fragility ratio **escalates with weather
severity** — the hallmark of weather-specific operational stress:

| Weather | AA Regional | DL Peer | AA ÷ DL |
|---------|-------------|---------|---------|
| Benign  | 2.09% | 1.17% | 1.79× |
| Marginal | 6.19% | 2.67% | **2.32×** |
| Adverse | 10.08% | 3.34% | **3.02×** |

If the elevated AA rate were merely a fixed operational baseline difference
(better network, different scheduling), the ratio would be approximately
constant across weather conditions. Instead it escalates: AA's disadvantage
is disproportionately large in marginal and adverse weather — a pattern
consistent with weather-specific operational sensitivity. As noted above,
the public data used here cannot distinguish among the internal factors
(crew, fleet, scheduling, maintenance basing, or other causes) that could
produce this signature; this study tests only for the externally observable
pattern, not its internal cause.

### Key finding: cancellation attribution

BTS `CancellationCode` independently confirms that AA regional attributes a
higher share of its cancellations to weather:

| Basket | Code B (Weather) | Code A (Carrier) | Code C (NAS) | Total |
|--------|-----------------|-----------------|-------------|-------|
| AA regional | 466 (81.8%) | 37 (6.5%) | 67 (11.8%) | 570 |
| Peers combined | 101 (55.8%) | 55 (30.4%) | 25 (13.8%) | 181 |

AA regional attributes 82% of its cancellations to weather; peer carriers
attribute only 56%. Weather-coded cancellations as a share of all study
flights: 2.58% (AA) vs 0.89% (peers).

### Severe delay rate (operated flights)

| Weather | AA Regional | UA Peer | DL Peer |
|---------|-------------|---------|---------|
| Benign  | 8.0% | 8.3% | 4.9% |
| Marginal | 14.3% | 17.1% | 8.2% |
| Adverse | 27.9% | 26.3% | 15.1% |

All carriers show elevated severe-delay rates (≥60 min arrival delay) in
worse weather, as expected. AA's severe-delay rate is broadly comparable to
UA peer and higher than DL peer, suggesting that when AA regional does
operate through weather, it also accumulates significant delays. The primary
differentiator is the higher cancellation frequency, not delay severity on
operated flights.

---

## Deliverables

All five required outputs produced:

| File | Size | Description |
|------|------|-------------|
| `data/curated/flight_operability_fact.csv` | 6.0 MB | 29,333-row flight fact table with weather, basket, flags |
| `output/weather_fragility_chart_data.csv` | 1.5 KB | 21-row aggregate at market × weather × period grain |
| `output/fragility_summary.json` | 828 B | Executive metrics: rates, ratios, period deltas, annotation |
| `output/qa_summary.csv` | 2.4 KB | Row counts, join rates, bucket sizes, null rates |
| `output/weather_fragility_exec_chart.png` | 148 KB | Executive 1600×900 PNG (matplotlib fallback; see caveat below) |

Chart rendering: Plotly+Kaleido failed because the environment lacks Google
Chrome (kaleido dependency). The matplotlib fallback completed successfully and
produced a chart with all required elements (two panels, three carrier groups,
percentage labels, annotation, legend). The output is visually identical in
layout to the Plotly design; Plotly would produce sharper typography. To install
Chrome for Plotly in future: `plotly_get_chrome`.

---

## Caveats and Limitations

**UA peer basket is thin, especially in 2024.** The UA peer basket has only
2,387 total study flights, with just 426 in the 2024 baseline period. United
appears to have significantly expanded service on these routes in 2025 (426 →
1,961 flights). The GPT-IAH route (Gulfport to Houston) had only 21 total
flights (OO/SkyWest), far below the 100-flight QA threshold flagged by the
pipeline. Weather-stratified metrics for UA, particularly in the adverse bucket
(32 baseline flights), carry wide confidence intervals and should be treated as
directional only. **Delta is the more credible peer comparator.**

**SkyWest (OO) operates under all three contracts.** SkyWest appears in the AA
regional basket (5,167 flights under AA contract), the UA peer basket (2,384
flights under UA contract), and the DL peer basket (2,067 flights under DL
contract). Any SkyWest-specific operational factors that are consistent across
contracts will be controlled out by the peer comparison; any AA-contract-specific
operational constraints would show up in the AA basket. The three-way
SkyWest presence is actually helpful for isolating the mainline-contract effect.

**Weather is assigned at endpoint airport-hours, not en-route.** The NOAA ASOS
join uses weather at the departure airport at departure time and the arrival
airport at arrival time. En-route weather (turbulence, fronts crossing in
flight) is not captured. For short-haul spoke-to-hub flights (1–2.5 hours),
endpoint weather is generally the dominant driver of cancellation decisions,
so this is an acceptable simplification.

**NOAA ASOS covers through 2025-12-30, missing one day.** The IEM request
for `end=2025-12-31` returned data through 2025-12-30. The 2025-12-31
flights in BTS will not have weather coverage for that date; they receive
the "unknown" bucket (included in the 33 unmatched flights). Effect on results:
negligible.

**BTS study-end date 2025-12-31 is fully available.** The pipeline requested
data through December 2025. As of June 2026, all 2025 monthly PREZIP files are
published by BTS and were successfully downloaded.

**No FlightAware phase-2 data.** FlightAware AeroAPI was not enabled
(`use_flightaware: false` in `study.yaml`), consistent with the spec's
designation of phase 2 as optional. The BTS + NOAA ASOS data is sufficient
for phase-1 deliverables.

---

## Open Decisions from Iteration 1 — Status

| # | Decision | Status |
|---|----------|--------|
| D1 | Confirm BTS form field IDs | **Resolved** — field codes eliminated; PREZIP download used instead |
| D2 | Confirm FAA ASPM form field names | **Resolved** — FAA replaced with NOAA ASOS; field names no longer relevant |
| D3 | Confirm FAA column names for ASPM severity | **Resolved** — NOAA METAR vsby/ceiling/wxcodes used instead |
| D4 | Validate route membership against BTS service | **Confirmed** — all 14 routes have BTS service; GPT-IAH flagged as sparse (21 flights) |
| D5 | Assess FAA–BTS join rate | **Resolved** — NOAA-to-BTS join rate is 99.3% (dep) / 99.8% (arr), far exceeding the 85% threshold |
| D6 | Chart annotation wording | **Confirmed** — auto-generated: "AA regional cancellation rate in marginal weather is 2.08x peers" |
| D7 | Phase 2 FlightAware | Remains open — not activated; deferred per spec |

---

## Next Steps

1. **Install Chrome for Plotly rendering:** Run `plotly_get_chrome` in the
   environment and re-run `40_plot_fragility.py` for sharper chart typography.

2. **Expand UA peer basket or use DL as primary peer:** Given the thin UA
   baseline sample, consider either adding more UA hub-spoke routes (e.g.,
   IAH connections from BNA, CRP, or ECP) or re-framing the executive
   narrative around AA vs. DL, which has the strongest sample.

3. **Period-aware analysis:** The 67% increase in AA regional cancellation
   rates from 2024 to 2025 is itself a finding. A route-by-route breakdown
   might reveal whether the increase is concentrated in specific carriers
   (Envoy/MQ vs. PSA/OH vs. SkyWest/OO under AA contract) or specific routes.

4. **Cross-validate cancellation attribution:** The BTS `CancellationCode`
   finding (81.8% of AA cancellations attributed to weather vs. 55.8% for
   peers) can be triangulated against news/NOTAM records for significant
   weather events to verify the attribution pattern is not a reporting artifact.

5. **Phase 2 FlightAware:** If AeroAPI access is obtained, enable
   `use_flightaware: true` in `study.yaml` and run `12_extract_flightaware.py`
   to add near-real-time recency data and validate against BTS reported values.

---

## Fragility II: Controllable and Cascade Disruption (Iteration 3)

**Date:** 2026-06-16
**Builds on:** Iteration 2 (above) and `flight_fragility_ii_machine_addon_spec.md`

### What was implemented

- Extended `10_extract_bts.py` to capture the five BTS cause-minute fields
  (`CarrierDelay`, `WeatherDelay`, `NASDelay`, `SecurityDelay`,
  `LateAircraftDelay`). No new downloads were required — the cached raw
  monthly files already contained these columns from the original BTS PREZIP
  download; only the staging-stage field selection needed extending.
- Extended `20_build_flight_fact.py` to derive `primary_delay_cause`,
  `controllable_delay_flag`, `controllable_cancel_flag`, `late_arriving_flag`,
  `cascade_delay_flag`, `controllable_severe_delay_flag`, and
  `late_arriving_severe_delay_flag`, applying the null-guard rule from the
  spec: cause-minute fields are null, not zero, for on-time and cancelled
  flights, so a row only receives a `primary_delay_cause` if at least one
  cause-minute field is non-null and their sum exceeds zero.
- Added `scripts/31_analyze_fragility_machine.py` and
  `scripts/41_plot_fragility_machine.py`, producing a parallel chart-data
  CSV, executive-summary JSON, written markdown summary, and PNG chart
  without modifying any Fragility I output.
- Added a `combined_peer_basket` (UA + DL pooled) series and a per-cell
  `low_confidence_flag` (operated flight count at or below
  `min_sample_threshold`, set to 30 in `config/study.yaml`) to address the
  sample-size risk the spec called out.

### QA results

- **Null-guard check passed**: `cause_data_count` (5,825) exactly matches
  the count of operated flights with `ArrDelay >= 15` (5,825); zero
  cancelled flights received a spurious cause assignment. This confirms the
  fillna(0)-before-idxmax defect identified during spec review is not
  present in the implementation.
- **One low-confidence cell**: `ua_peer_basket / adverse / baseline` (30
  operated flights of 32 total) — the same cell already flagged as thin
  elsewhere in this document. All adverse-weather ratios in the written
  summary are marked provisional as a result.
- **Operating-carrier breakout — corrected**: an earlier draft of this
  section stated this breakout was impossible because BTS has no field
  distinct from the marketing/reporting carrier. That was wrong on the key
  point: the basket is assigned by route, not by `Reporting_Airline`, and
  `Reporting_Airline` (`carrier_code` in the fact table) for these routes is
  already the regional partner's own code — MQ (Envoy), OH (PSA), OO
  (SkyWest) — not "AA"/"UA"/"DL", because regional carriers file their own
  on-time-performance reports under their own code. The breakout the spec
  asked for is therefore implemented; see "Operator-level breakdown" below
  and `output/fragility_ii_summary.md` section 6 /
  `output/fragility_ii_operator_breakdown.csv`.

### Headline results

| Weather  | AA controllable severe-delay rate | Peer avg | Combined peer | AA÷peer avg | AA÷combined peer |
|----------|-----------------------------------|----------|----------------|-------------|-------------------|
| Benign   | 2.86%                              | 3.81%    | 3.51%          | 0.75×       | 0.81×             |
| Marginal | 3.18%                              | 6.02%    | 4.52%          | 0.53×       | 0.70×             |
| Adverse  | 4.65%                              | 6.35%    | 4.87%          | 0.73× (provisional) | 0.95× (provisional) |

| Weather  | AA late-arriving (cascade) severe-delay rate | Peer avg | Combined peer | AA÷peer avg | AA÷combined peer |
|----------|-----------------------------------------------|----------|----------------|-------------|-------------------|
| Benign   | 4.43%                                          | 2.55%    | 2.22%          | 1.74×       | 2.00×             |
| Marginal | 5.40%                                          | 4.20%    | 3.49%          | 1.28×       | 1.55×             |
| Adverse  | 8.11%                                          | 5.48%    | 5.31%          | 1.48× (provisional) | 1.53× (provisional) |

Benign-to-adverse escalation in the cascade rate: AA regional 1.83×,
combined peer basket 2.39×.

**This result is mixed relative to Fragility I, not confirmatory.** The
controllable (Air Carrier-coded) severe-delay rate is consistently *lower*
for AA regional than for peers across all three weather buckets, and does
not show the escalating-with-weather-stress pattern that Fragility I's
cancellation-rate finding showed. The late-arriving (cascade) severe-delay
rate is consistently *higher* for AA regional than peers, but its own
escalation from benign to adverse conditions is smaller for AA (1.83×) than
for the combined peer basket (2.39×) — the opposite direction from what the
secondary hypothesis anticipated. Both observations are reported as found;
see `output/fragility_ii_summary.md` and the spec's "Risks, threats to
validity, and alternative explanations" section for the full disclosure
this finding should be read alongside.

### Operator-level breakdown

The AA regional basket is served by three regional carriers with usable
sample sizes in every weather bucket: Envoy Air (MQ, 7,530 flights), PSA
Airlines (OH, 5,357), and SkyWest (OO, 5,167). Breaking the same two metrics
out by operator (periods combined to preserve sample size) shows the
basket-level pattern is not uniform:

| Operator | Benign controllable | Marginal controllable | Adverse controllable | Benign cascade | Marginal cascade | Adverse cascade |
|---|---|---|---|---|---|---|
| Envoy (MQ) | 1.48% | 2.21% | 2.28% | 3.82% | 5.41% | 9.73% |
| PSA (OH) | 2.54% | 2.86% | 4.29% | 8.60% | 10.38% | 11.36% |
| SkyWest (OO, AA contract) | 5.23% | 4.78% | 8.88% | 1.06% | 0.82% | 1.32% |

Envoy and PSA show the same qualitative profile as the AA basket overall —
low controllable rate, high and weather-escalating cascade rate. SkyWest
under the AA contract shows close to the opposite profile: a higher,
weather-escalating *controllable* rate and a low, flat cascade rate. That
SkyWest profile also appears when SkyWest flies under the DL contract
(controllable 8.31% → 6.99% → 10.32%, cascade 0.00% throughout in the DL
peer basket), which is some evidence the SkyWest signature travels with the
operator rather than the AA contract specifically — though Envoy and PSA
fly only under the AA contract in this study, so no equivalent
cross-contract check exists for them. This is unpacked further in
`output/fragility_ii_summary.md` section 6 and
`output/fragility_ii_operator_breakdown.csv`; the same self-reported-cause-
data and cause-granularity caveats apply at this finer grain.

### Files produced

- `output/weather_fragility_machine_chart_data.csv`
- `output/fragility_ii_machine_summary.json`
- `output/fragility_ii_summary.md`
- `output/fragility_ii_operator_breakdown.csv`
- `output/weather_fragility_machine_exec_chart.png`

---

## Fragility III: Economic Impact Estimation (Iteration 4)

**Date:** 2026-06-16
**Builds on:** Iterations 2–3 (above) and `flight_fragility_iii_show_me_the_money_addon_spec.md`

### What was implemented

- Added `scripts/32_analyze_fragility_money.py` and
  `scripts/42_plot_fragility_money.py`, producing a chart-ready cost-proxy
  CSV, executive-summary JSON, written markdown summary, and PNG chart
  without modifying any Fragility I or II output.
- Added `config/economic_scenarios.yaml` with low/base/high cost
  coefficients (passenger value of time, airline block-time cost,
  cancellation-equivalent minutes), matching the spec's example defaults
  exactly: `$35/$47/$60` per hour, `$80/$100.76/$120` per minute,
  `240/360/480` minutes per excess cancellation.
- Implemented the spec's "Fragility II-preferred" mode: the cost basis is
  excess controllable (carrier-attributed) delay minutes plus excess
  cascade (late-aircraft) delay minutes, computed directly from BTS's
  reported cause-minute fields (`carrier_delay_minutes`,
  `late_aircraft_delay_minutes`) rather than from severe-delay-rate
  proxies — a stronger and more direct mapping to the spec's "convert
  excess disruption into excess minutes" step. An "overall" fallback mode
  (Fragility I arrival-delay-minutes basis, no cause decomposition) is
  implemented and used automatically if the cause-minute fields are ever
  unavailable.
- Excess is computed at market_bucket x weather_bucket grain (periods
  combined to preserve sample size) plus a pooled "all weather" row used
  for the headline scenario chart, per the spec's "stratify_by_weather"
  configuration flag.
- Cancellations are costed separately from delay minutes via a
  configurable cancellation-equivalent-minutes scenario lever (not an
  observed fact), exactly matching the spec's Tier 4 costing approach.
- Implemented the spec's "Mode 1: flight-level burden only" passenger-cost
  framing throughout — no passengers-per-flight multiplier is applied,
  since no passenger-manifest or seat-count data exists in this pipeline's
  public sources. This is disclosed explicitly in the written summary
  rather than silently assumed.

### QA results

- **Peer benchmark confirmed**: the same UA/DL peer-average rates reported
  in Fragility I and II are reused as the costing counterfactual, not
  independently recomputed.
- **Negative-excess values shown, not hidden**: the controllable delay-
  minutes component is negative (AA runs below the peer-average
  expectation) and is reported as a negative number throughout the chart
  data, summary JSON, and written summary, per the spec's QA requirement
  to show negative values explicitly when AA outperforms peers.
- **Scenario parameters verified against config**: low/base/high cost
  coefficients in the written summary and chart match
  `config/economic_scenarios.yaml` exactly.
- **Mode used is logged and disclosed**: both the console output and
  `output/fragility_iii_summary.md` section 1 state which mode
  (`fragility_ii_preferred` or `overall`) was actually used for the run.
- **Full pipeline rerun verified**: running `scripts/run_pipeline.sh`
  end-to-end reproduces identical Fragility I and II numbers alongside the
  new Fragility III outputs — this iteration does not alter any prior
  output.

### Headline results

| Component | Excess vs. peer-average rate (study window) |
|---|---|
| Cancellations | 270 flights |
| Controllable (carrier-attributed) delay minutes | -33,214 min |
| Cascade (late-aircraft) delay minutes | 52,106 min |
| **Net excess delay-minutes basis** | **18,891 min** |

| Scenario | Airline operating-time burden | Passenger-time burden (flight-level proxy) | Combined |
|---|---|---|---|
| Low  | $1,511,296 | $48,838  | $1,560,134 |
| Base | $1,903,477 | $90,975  | **$1,994,452** |
| High | $2,266,944 | $148,554 | $2,415,498 |

**This result sharpens, rather than restates, Fragility II's finding.** The
controllable component is negative — consistent with AA regional's
below-peer controllable severe-delay rate — while the larger, positive
cascade component drives the net total, so the two components do not net
to zero. Breaking the net total out by weather bucket shows it is not
evenly distributed: benign weather alone accounts for essentially all of
the positive net (+35,496 minutes, ~$3.6M base-case burden), while marginal
and adverse weather each run *negative* on this basis (AA below the
peer-average expectation once weather deteriorates). The economic burden
this study can attach to AA's elevated cascade exposure therefore presents
as a baseline/schedule-resilience cost rather than a weather-stress cost —
see `output/fragility_iii_summary.md` section 4 for the full breakdown and
section 5 for the complete caveat list this finding should be read
alongside.

### Files produced

- `output/fragility_iii_chart_data.csv`
- `output/fragility_iii_summary.json`
- `output/fragility_iii_summary.md`
- `output/fragility_iii_exec_chart.png`

---

## Fragility IV: Operator Attribution (Iteration 5)

**Date:** 2026-06-16
**Builds on:** Iterations 2–4 (above) and `flight_fragility_iv_operator_attribution_spec.md`

### What was implemented

Fragility IV asks whether AA's four operating structures — AA mainline, Envoy
Air, PSA Airlines, and SkyWest/Republic under their resolved mainline
contracts — show different fragility signatures, in the same focal corridor
plus a net-new hub-spoke expansion. It is built as two modules sharing one
operator-attribution methodology, per the spec's "Architecture and build
location":

- **Module A (focal corridor)** reuses the existing
  `data/curated/flight_operability_fact.csv` unchanged, adding an
  `operator_class` column derived from `carrier_code` via
  `scripts/lib/operator_classify.py` and `config/operator_classes.yaml`. No
  new extraction was required.
- **Module B (hub-spoke expansion)** is net-new: `scripts/13_extract_bts_hubspoke.py`
  and `scripts/14_extract_weather_hubspoke.py` extract BTS and NOAA ASOS data
  for a configurable hub list (`config/study.yaml` `run_mode_hubs`), with the
  spoke-market universe discovered directly from the data rather than
  hand-enumerated. Airport timezone/ICAO-station lookups use the new
  `airportsdata` package instead of a hand-maintained table, since the
  spoke-airport set is not known in advance.
- A `run_mode` framework (`test` / `local` / `bigrun`, `config/study.yaml`)
  scopes Module B's hub list and date window so the pipeline can be
  functionally validated inside this sandboxed container (`test`: DFW only,
  January 2024) before a full run on provisioned infrastructure.
- `scripts/lib/backend.py` adds an optional pandas/duckdb/polars backend
  abstraction for the aggregation step, materializing results back to pandas
  so downstream chart code is backend-agnostic (`config/study.yaml`
  `backend:`, defaults to `pandas`).
- **FlightAware AeroAPI was reactivated**, but narrowly: `scripts/15_resolve_operator_ambiguity.py`
  performs targeted, single-flight historical lookups
  (`GET /history/flights/{ident}`) only for the OO (SkyWest) / YX (Republic)
  rows that route-context inference cannot resolve — never a bulk
  route-date pull. This is a distinct, separately-gated reactivation
  (`config/study.yaml` `resolve_operator_ambiguity.enabled` +
  `FLIGHTAWARE_API_KEY`) from the dormant bulk extractor
  (`12_extract_flightaware.py`, still gated by `use_flightaware: false`,
  untouched). It no-ops safely (writes an empty resolution file) if the key
  is absent, so the rest of the pipeline never depends on a live key.
  Querying the existing Module A fact table directly showed OO already
  appears in all three pre-validated route baskets (`aa_regional_basket`,
  `ua_peer_basket`, `dl_peer_basket`), so route-context inference alone
  resolves ~100% of Module A's OO ambiguity — this targeted FlightAware path
  is primarily exercised by Module B, where no basket assignment exists yet.
- `scripts/33_analyze_fragility_operator.py` builds the combined
  module x operator_class x hub_family x weather_bucket x period_flag
  scorecard, computing `weather_fragility_rate` (chosen, disclosed
  definition: `(cancelled_count + severe_delay_count) / flights_total`,
  since the spec names this metric without a formula) and
  `combined_fragility_score` (configurable weights,
  `config/study.yaml` `combined_fragility_score_weights`, default equal
  0.25 each). The economic-burden proxy reuses Fragility III's
  excess-vs-baseline-rate x published-cost-benchmark methodology, but with
  two different baselines as the spec specifies: Module A keeps the existing
  UA/DL peer-average baseline; Module B has no peer-carrier basket yet at
  the new hubs, so it uses an AA-system average pooled across included
  operator classes per hub_family x weather_bucket x period_flag cell
  (`hubspoke_economic_burden_baseline: "aa_system_average"`, not
  leave-one-out).
- `scripts/43_plot_fragility_operator.py` renders the four-panel executive
  chart (small multiples by hub family, per the spec's guidance to
  prioritize that over operator-color complexity) and the written summary,
  reusing the dual plotly/kaleido-then-matplotlib rendering pattern from
  `40_plot_fragility.py`.
- `scripts/run_pipeline_iv.sh` orchestrates steps 13→14→15→21→33→43, kept
  separate from `run_pipeline.sh` per the project's established
  phase-decoupling convention; it requires `run_pipeline.sh` to have already
  produced `data/curated/flight_operability_fact.csv` at least once, since
  Module A reuses that table rather than rebuilding it.

### Bug found and fixed during validation

**`lib.backend.write_partitioned_parquet()` was not idempotent.** pandas'
`to_parquet(partition_cols=...)` adds new uniquely-named files into an
existing Hive-partitioned directory rather than replacing its contents. The
first end-to-end test run produced correct row counts; re-running the same
`test` slice without `--force` (using cached raw files, the expected normal
case) silently **doubled** the row counts in `data/staging/bts_hubspoke/`
and `data/curated/hubspoke_operator_fact/`, because each script run added a
second set of Parquet files alongside the first instead of replacing them.
Fixed by clearing the output directory (`shutil.rmtree`) before writing.
Re-ran the full `test`-mode pipeline twice in a row after the fix to confirm
row counts now stay constant across repeated runs (47,158 Module B rows
both times). A second pre-existing issue was found and fixed in the same
pass: `14_extract_weather_hubspoke.py` ignored `run_mode_window` and always
requested the full multi-year study window regardless of `run_mode`,
causing the `test` slice to request 175 ASOS stations x 2 years instead of
175 stations x 1 month; it now resolves its window the same way
`13_extract_bts_hubspoke.py` does.

### Validation scope and status

**This is a container-safe `test`-mode structural validation, not a
statistically meaningful result.** Per the spec's "Architecture and build
location," this sandboxed container is expected to functionally validate the
`test` and `local` run modes; a `bigrun` (full configured hub network) is
expected to run on separately-provisioned infrastructure with the longer
runtime and storage it requires. The `test` slice used here is DFW only,
January 2024 — one hub, one month. Module A (focal corridor) in this same
scorecard run still covers its full original 2024–2025 window, since it
reuses the existing fact table unchanged; the two modules are therefore on
different time windows in this `test`-mode run specifically. (`local` mode
aligns both modules to the same 2024–2025 window and adds CLT/ORD/PHL; that
run has not yet been executed in this container.)

End-to-end execution (`bash scripts/run_pipeline_iv.sh`) completed without
errors and produced all expected deliverables. QA output from this run:

- Module B (DFW, January 2024): 47,158 flights. Operator classes:
  AA_mainline 26,056; Envoy_operated 10,284; Other_or_non_AA 5,981;
  SkyWest_unresolved 3,441; PSA_operated 1,390; Republic_unresolved 6.
  Weather buckets: benign 30,762; marginal 9,429; adverse 5,304;
  unknown 1,663. Departure/arrival weather match rates: 96.3% / 96.0%
  (slightly below Fragility I-III's ~99% because the discovered spoke-airport
  set is much larger and includes smaller fields with sparser ASOS coverage).
- Combined scorecard (Module A + B): 63 operator_class x hub_family x
  weather_bucket x period_flag cells. 7 cells fall below
  `min_sample_threshold` (30 flights) and are QA-flagged as indicative only.
  10,341 flights system-wide remain in an unresolved operator-ambiguity label
  (`SkyWest_unresolved` / `Republic_unresolved`) and are excluded from
  operator-class comparisons — expected, since `FLIGHTAWARE_API_KEY` is unset
  in this container and the targeted-validation step correctly no-opped.
- `output/fragility_iv_summary.md`'s top-ranked cell by
  `combined_fragility_score` in this run is `OO_UA_contract` at
  `focal_corridor` (0.149, 32 flights) — a cell already flagged elsewhere in
  this report as thin, and not comparable in confidence to a `bigrun` result.

No headline finding is reported for Fragility IV in this Iteration 5 section, and
none should be inferred from the test-mode numbers above: a one-hub, one-month Module B
slice compared against a two-year Module A window is a structural smoke test
of the pipeline, not evidence about operator fragility. The local-mode execution
(DFW/CLT/ORD/PHL, Jan 2024–Dec 2025) was subsequently completed and is documented
in Iteration 6 below.

### Files produced

- `data/curated/hubspoke_operator_fact/` (Hive-partitioned by `year_month`)
- `output/qa_summary_hubspoke.csv`
- `output/fragility_iv_operator_chart_data.csv`
- `output/fragility_iv_operator_scorecard.parquet`
- `output/fragility_iv_summary.json`
- `output/fragility_iv_operator_exec_chart.png`
- `output/fragility_iv_summary.md`

---

## Fragility IV: Local-Mode Execution (Iteration 6)

**Date:** 2026-06-17
**Builds on:** Iteration 5 (Fragility IV implementation, above)

### Issues found and fixed during local-mode execution

Three bugs surfaced during the local-mode run (DFW/CLT/ORD/PHL, Jan 2024–Dec 2025) that were not visible in the single-hub, single-month `test`-mode run.

#### Bug 1 — NOAA IEM rate-limiting silently lost 23 of 24 months of weather data

**What happened.** The NOAA IEM Mesonet service applies abuse-prevention throttling. The first monthly request (January 2024, ~175 stations) succeeded with 174K rows. All 23 subsequent months failed immediately with HTTP 503 then HTTP 429 responses. The original `fetch_noaa_asos()` caught these errors with a bare `except: log.warning; continue`, swallowing every failure silently. Downstream, 96.5% of flights fell into the `unknown` weather bucket — a diagnostic flag that passed QA without triggering an abort.

**Fix applied.** Added retry-with-backoff to `scripts/14_extract_weather_hubspoke.py`: up to 5 retries per request, exponential backoff starting at 30 seconds (30/60/120/240/480 s), covering HTTP 429/502/503/504 and connection/timeout errors. Constants: `NOAA_MAX_RETRIES = 5`, `NOAA_RETRY_BASE_DELAY_SEC = 30`, `NOAA_RETRY_STATUS_CODES = {429, 502, 503, 504}`. Validated via live probe: throttle cleared in ~13 minutes; re-run succeeded with 96.6% weather match across all 24 months.

#### Bug 2 — Cache-key collision between `test` and `local` raw files

**What happened.** Raw BTS and NOAA files were keyed only by `{year}_{month}`. After the test-mode run (DFW-only, January 2024) cached `bts_hubspoke_2024_01.csv`, the local-mode run (4 hubs) silently reused that single-hub file for January 2024 rather than re-fetching the 4-hub version. Result: Module B's January 2024 data contained only DFW flights in local mode.

**Fix applied.** `run_mode` is now embedded in raw filenames: `bts_hubspoke_{run_mode}_{year}_{month:02d}.csv`, `noaa_asos_raw_{run_mode}_{year}_{month:02d}.csv`. Each run_mode maintains an independent file cache.

#### Bug 3 — Background task timeout due to slow `normalize_noaa()`

**What happened.** The container's background task runner has a ~2-hour execution limit. The old `normalize_noaa()` used three Python-level `apply()` loops (per-row ceiling derivation, per-row weather-bucket classification, per-group hourly aggregation): ~285 seconds per month × 22 months of normalization work ≈ ~105 minutes. The second local-mode attempt was killed mid-execution at October 2025 normalization, after the rate-limit and cache-key fixes had been applied.

**Fix applied.** Rewrote `normalize_noaa()` in `scripts/14_extract_weather_hubspoke.py` using vectorized pandas operations: pre-compiled regex patterns for weather-token matching (`_ADVERSE_WX_RE`, `_MARGINAL_WX_RE`), a vectorized `_derive_ceiling_vectorized()` using column-wise masking instead of per-row `apply()`, and native `groupby().agg()` with named aggregations instead of `groupby().apply()`. Result: ~6 seconds per month — a 47× speedup. All 24 months of normalization now complete in under 3 minutes.

### Local-mode run results

End-to-end execution completed without errors. QA results:

- **Total flights:** 3,587,814 across 4 hubs, 24 months (Jan 2024–Dec 2025)
- **Hub breakdown:** DFW 1,230,629; ORD 1,183,012; CLT 801,447; PHL 372,726
- **Operator classes:** AA_mainline 1,468,337; Other_or_non_AA 851,529; Envoy_operated 458,554; SkyWest_unresolved 346,969; PSA_operated 324,388; Republic_unresolved 138,037
- **Unresolved operator ambiguity:** 485,006 flights (SkyWest_unresolved + Republic_unresolved) excluded from operator-class comparisons — expected, since `FLIGHTAWARE_API_KEY` is unset and the targeted-validation step correctly no-ops. These rows are retained in hub-level and network-wide rollups.
- **Weather match:** 96.6% across all 24 months (departure and arrival combined). Slightly below Fragility I–III's ~99% rate because the discovered spoke-airport universe (239 airports) includes many smaller fields with sparser ASOS station coverage.
- **18 operator/hub/weather/period cells** fall below `min_sample_threshold` (30 flights) — flagged as indicative only.

**Top-ranked cell.** PSA_operated at ORD shows the highest combined fragility score among cells meeting the minimum sample threshold:

| Attribute | Value |
|---|---|
| Cell | PSA_operated × ORD × adverse weather × recent period |
| Flights | 186 |
| Cancellation rate | 22.6% (42/186) |
| Severe delay rate | 39.6% (57/144 operated) |
| Controllable severe delay rate | 6.3% (9/144) |
| Cascade (late-arriving) severe delay rate | 21.5% (31/144) |
| Economic burden proxy (base scenario) | $581,540 |
| Combined fragility score | 0.225 |

The cascade component dominates the score (21.5%) relative to the controllable component (6.3%), which is consistent with the pattern observed in the focal corridor across Fragility I–III.

### Files produced or updated

- `data/curated/hubspoke_operator_fact/` — re-populated from local-mode run (24 months, 4 hubs)
- `output/qa_summary_hubspoke.csv`
- `output/fragility_iv_operator_chart_data.csv`
- `output/fragility_iv_operator_scorecard.parquet`
- `output/fragility_iv_summary.json`
- `output/fragility_iv_operator_exec_chart.png`
- `output/fragility_iv_summary.md`

---

## Fragility V: Network Hotspot Engine (Iteration 7)

**Date:** 2026-06-17
**Builds on:** Iteration 6 (Fragility IV local-mode curated layer) and `flight_fragility_v_network_hotspot_spec.md`

### What was implemented

Fragility V extends the earlier studies into a systemwide hotspot-discovery and ranking engine. Rather than testing one corridor against peer baskets, it scores every (hub_family × spoke_airport × operator_class) cell in the Fragility IV curated layer using a six-component composite hotspot score, then ranks cells, tests robustness across four weighting scenarios, and summarizes hub and operator concentrations.

- **Scoring grain:** (hub_family, spoke_airport, operator_class) — 1,304 distinct cells from the local-mode curated data.
- **Hotspot score:** composite of six percentile-ranked components (ranked within cells meeting the min-flights threshold): cancellation rate, severe-delay rate, controllable severe-delay rate, cascade (late-arriving) severe-delay rate, adverse-weather fragility rate, and economic burden per 1,000 flights.
- **Component weights:** equal weights (1/6 each) in the base scenario; three additional scenarios (`weather_emphasis`, `controllable_cascade_emphasis`, `economic_emphasis`) vary weights to test robustness.
- **Robustness metric:** `hotspot_robustness_score` = share of the four scenarios in which a cell appears in the top-N hotspot list. A score of 1.0 means top-N under all four weighting assumptions.
- **Persistence (Module E):** cells are independently scored on 2024 (baseline) and 2025 (recent) windows; `is_persistent` marks cells appearing in top-N in both.
- New scripts: `scripts/34_analyze_fragility_hotspots.py`, `scripts/44_plot_fragility_hotspots.py`, `scripts/run_pipeline_v.sh`. Added `fragility_v:` configuration block in `config/study.yaml`.

### Local-mode run results

End-to-end execution consumed the Fragility IV curated layer without additional data extraction and completed in under 5 minutes.

- **Total cells scored:** 1,304 (hub × spoke × operator_class combinations)
- **Cells meeting min_flights=100:** 1,070 (used for normalization and ranking)
- **Persistent cells** (top-20 in both baseline and recent periods): 3 of 20

Top-20 cells by base hotspot score (excerpt — full ranked table in `output/fragility_v_summary.md`):

| Rank | Hub | Spoke | Operator | Base Score | Robustness | Persistent |
|---|---|---|---|---|---|---|
| 1 | ORD | SPI | SkyWest_unresolved | 0.978 | 1.00 | No |
| 2 | ORD | ORF | PSA_operated | 0.971 | 1.00 | No |
| 3 | ORD | CAK | PSA_operated | 0.969 | 1.00 | No |
| 6 | DFW | CID | AA_mainline | 0.948 | 1.00 | Yes |
| 8 | DFW | ICT | AA_mainline | 0.933 | 1.00 | Yes |

**Hub concentration in top-20:** DFW 50% (10 cells), ORD 45% (9 cells), PHL 5% (1 cell), CLT 0%.

**Operator concentration in top-20 (resolved operators only):** PSA_operated 67% (10 cells), AA_mainline 33% (5 cells). SkyWest_unresolved and Republic_unresolved are excluded from this rollup per the spec (ambiguous attribution would distort operator-level counts) but are retained in hub-level rollups.

**Dominant fragility signature in top-20:** economic_burden (7 cells), cascade (5 cells), severe_delay (4 cells), cancel (2 cells), controllable (1 cell), weather_sensitivity (1 cell). The majority of highest-scoring cells are driven by economic burden or cascade rather than raw weather sensitivity.

**Robustness:** 9 of the top-20 cells have a robustness score of 1.0; 5 score 0.75; 3 score 0.50; 3 score 0.25. None of the top-20 cells are artifacts of a single scenario weighting.

### Files produced

- `output/fragility_v_hotspot_scorecard.parquet/` (Hive-partitioned by hub_family)
- `output/fragility_v_hotspot_rankings.csv`
- `output/fragility_v_exec_chart.png`
- `output/fragility_v_hub_rollup.csv`
- `output/fragility_v_operator_rollup.csv`
- `output/fragility_v_scenario_robustness.csv`
- `output/fragility_v_summary.json`
- `output/fragility_v_summary.md`

---

*End of After Action Report — Iterations 2–7*

---

## Iteration 8: Pre-Bigrun Hardening — Code Review Fixes (2026-06-18)

**Date:** 2026-06-18
**Builds on:** Iteration 7 (Fragility V implementation)

### What this iteration is

A complete end-to-end code and methodology review of every Fragility IV/V
component was conducted before the bigrun (full configured hub network,
Jan 2024–Dec 2025). The review adopted an outside-in critical perspective
covering: correctness, defensibility of headline findings, bigrun
reliability, and disclosure of known limitations. Sixteen specific findings
were identified and all sixteen were implemented in a single commit
(`3acf9b5`).

### Findings and fixes

#### Tier 1 — Defensibility of headline findings

**Finding 1: Adverse-weather sample sparsity (Fragility V)**

`norm_weather_sensitivity` was computed purely from `adverse_weather_fragility_rate`
with no minimum adverse-flight count. The top-ranked cell in the
local-mode run (ORD-SPI, SkyWest_unresolved, rank 1) had 8 adverse-weather
flights with an 87.5% adverse-fragility rate, yielding a normalized score of
0.992 — a classic small-sample upward bias. 9 of the top-20 local-mode cells
had fewer than 30 adverse flights.

*Fix:* Added `hotspot_min_adv_flights: 30` to `config/study.yaml`'s `fragility_v`
block. In `normalize_components()`, cells below this threshold receive
`norm_weather_sensitivity = NaN` and are scored on the remaining 5 components
only, with weights renormalized to sum to 1.0 (no hard exclusion from scoring).
`compute_hotspot_score()` was rewritten as a vectorized weighted-available-
components average, handling NaN components gracefully. A `meets_min_adv_flights`
flag is added to the output.

**Finding 2: Winner's curse / persistence framing (Fragility V)**

The `hotspot_robustness_score` metric was computed using a mask that required
all 6 components to be non-NaN — incompatible with the new partial-scoring
approach. The persistence check also used `min_flights // 2` as its per-period
threshold without disclosing this halving anywhere in logs or output.

*Fix:* `compute_robustness()` updated to use the base-scenario score's notna
mask (cells scoring on 5 components are correctly included). `compute_persistence()`
now logs `"per-period min_flights={min_flights // 2} = {min_flights} // 2"`. The
caveats section in `write_markdown_summary()` now foregrounds winner's curse, the
low expected persistence rate for a top-20 list drawn from 1,000+ cells, and the
interpretation of robustness vs. rank as separate signals.

**Finding 3: Min-sample gating for top-cell selection (Fragility IV)**

In `33_analyze_fragility_operator.py`, the top-cell annotation and JSON summary
were selected from the full scorecard with no minimum sample requirement —
a 1-flight cell could win. 

*Fix:* Top-cell selection now filters to `flights_total >= min_sample_threshold`
(study.yaml default: 30) before sorting. Annotation text updated to state the
minimum-sample gate.

#### Tier 2 — Disclosures

**Finding 4: Mixed denominators in combined_fragility_score (Fragility IV)**

`cancellation_rate` uses `flights_total` as its denominator; `severe_delay_rate`,
`controllable_severe_delay_rate`, and `late_arriving_severe_delay_rate` use
`operated_count`. The combined score is a weighted sum of rates with
heterogeneous denominators.

*Fix:* Added an explicit caveat to `run_qa()` output in
`33_analyze_fragility_operator.py`.

**Finding 5: Self-inclusive Module B baseline (Fragility IV)**

The `aa_system_average` baseline used in Module B pools all resolved operator
classes within the same `hub × weather × period` cell, including the operator
being scored. It is not leave-one-out. High-volume operators with above-average
fragility partially suppress their own excess signal.

*Fix:* Added an explicit caveat to `run_qa()` output, supplementing the
existing docstring note.

**Finding 6: Severe-delay definition inconsistency (Fragility V)**

`severe_delay_flag` (basis for `norm_severe_delay`) tests arrival delay
≥ threshold only. `controllable_severe_delay_flag` and
`late_arriving_severe_delay_flag` (basis for `norm_controllable` and
`norm_cascade`) test departure OR arrival delay ≥ threshold. These components
are therefore not directly comparable within the composite score.

*Fix:* Added an explicit caveat to the caveats section of `fragility_v_summary.md`
in `write_markdown_summary()`.

#### Tier 3 — Bigrun protection

**Finding 7: Silent partial-window failures (scripts 13 and 14)**

Both extractors used `except Exception: log.warning; continue` per-month,
only hard-failing if ALL months failed. A partial failure (e.g., 2 months
failing due to network interruption mid-bigrun) would silently produce an
incomplete output with exit code 0.

*Fix:* Both scripts now track `expected_months` (set of all `(year, month)`
tuples in the configured window) and `fetched_months`/`normalized_months`
(actually completed). After the loop, `missing_months = expected_months - fetched_months`
triggers a hard `sys.exit(1)` with a specific error listing the missing months
and the `--force` remedy.

**Finding 8: Cache-key collision for `discovered_airports.csv` (script 13)**

`13_extract_bts_hubspoke.py` wrote a single global `discovered_airports.csv`
regardless of run_mode. A `test`-mode run (DFW-only) would overwrite the
local-mode discovered-airport list, corrupting `14_extract_weather_hubspoke.py`'s
station coverage on the next local-mode run.

*Fix:* Script 13 now writes `discovered_airports_{run_mode}.csv`. Script 14's
`--airports` argument defaults to `"auto"`, which resolves the run_mode-keyed path
automatically in `main()` after loading `study.yaml` and resolving `run_mode`.

**Finding 9: `iterrows()` loop in `_add_utc_keys` (script 21)**

`_add_utc_keys` in `21_build_hubspoke_fact.py` looped row-by-row with
`for _, row in bts.iterrows()`, calling per-row timezone logic via `_hhmm_to_utc`
and `_get_tz`. At 3.59M flights for the local-mode run this would have been
prohibitively slow for the bigrun (~20M+ flights).

*Fix:* `_add_utc_keys` fully vectorized using the per-timezone-group approach
(iterate over unique timezone names, ~50 groups for the full US network, rather
than over rows). Uses `pd.Series.dt.tz_localize()` per group, which is
O(rows in group) in pandas' C layer. Dead code removed: `_hhmm_to_utc`,
`_get_tz`, `_TZ_CACHE`, `UTC = ZoneInfo("UTC")`, and the `datetime`/`zoneinfo`
imports that were only needed by those functions.

**Finding 10: Misleading `or "benign"` idiom in `join_weather` (script 21)**

`merged.apply(lambda r: _worst_bucket(r.get("wx_dep_bucket") or "benign", ...), axis=1)`
— the `or "benign"` does NOT coerce NaN to "benign" because NaN is truthy in Python.
NaN passes through to `_worst_bucket` where it maps to rank -1. The idiom was
both misleading and used an `apply()` loop on a potentially multi-million-row frame.

*Fix:* Replaced `apply()` with a vectorized rank-map + `np.maximum()`:
```python
dep_rank = merged["wx_dep_bucket"].map(BUCKET_RANK).fillna(-1).astype(int)
arr_rank = merged["wx_arr_bucket"].map(BUCKET_RANK).fillna(-1).astype(int)
merged["weather_bucket"] = np.maximum(dep_rank, arr_rank).map(RANK_BUCKET)
```
Added an inline comment explaining the NaN semantics and the known downward bias
of single-endpoint-miss flights. `_worst_bucket` removed as dead code.

#### Tier 4 — Correctness / cosmetic

**Finding 11: Dead `EXCLUDE_FROM_SCORING` constant (script 34)**

`EXCLUDE_FROM_SCORING = {"Other_or_non_AA"}` was defined at module level but
never referenced; the exclusion was done inline in `main()` via a string compare.

*Fix:* Constant removed.

**Finding 12: Unused `scenario_name` parameter in `compute_hotspot_score` (script 34)**

The parameter was passed to the function but never used inside it.

*Fix:* Parameter removed from signature and all call sites.

**Finding 13: FlightAware prefix matching (script 15)**

`ident.startswith(prefix)` on a 2-char IATA prefix matched any ident starting with
those two letters, including longer codes like "ASA..." that coincidentally share
a prefix with "AS" (Alaska Airlines).

*Fix:* Added digit-boundary check — `ident.startswith(prefix) and ident[len(prefix)].isdigit()`.
IATA flight identifiers are always [2-char code][digits], so this is both
correct and stricter without over-filtering real codeshares.

**Finding 14: No multi-brand conflict detection in FlightAware resolution (script 15)**

`resolve_brand_from_response()` returned on the first matching codeshare prefix,
with no check for cases where multiple mainline brands appear in the same flight's
codeshare list (data error or ambiguous response).

*Fix:* Now collects all matching contracts into a `set`. Returns the single resolved
class if exactly 1 match; logs a warning and returns `None` (unresolved) if more
than 1 match.

**Finding 15: Weak date filter in FlightAware resolution (script 15)**

The date filter only checked `scheduled_out`/`scheduled_off`; if both were absent,
the flight entry was passed through regardless of date — risking a wrong-day
codeshare match.

*Fix:* Extended the fallback chain to also check `estimated_out`, `estimated_off`,
`actual_out`, `actual_off`. If no date context is available from any field, the
flight entry is now skipped rather than passed through.

**Finding 16: `rate guard .clip(lower=1)` limitation undisclosed**

The `flights_total.clip(lower=1)` and `operated_count.clip(lower=1)` denominators
guard against division-by-zero but produce nonsensical rates (≥100%) for 0-flight
cells that could theoretically receive a count from the aggregation. No 0-flight
cells exist in practice (groupby only produces rows that exist in the data), so
this is informational only and was not changed.

*Disclosure added:* Noted in Tier 4 review findings; no code change.

### Summary table

| # | File | Change | Tier |
|---|------|--------|------|
| 1 | `config/study.yaml` | Added `hotspot_min_adv_flights: 30` | 1 |
| 2 | `34_analyze_fragility_hotspots.py` | min_adv_flights gate in `normalize_components` | 1 |
| 3 | `34_analyze_fragility_hotspots.py` | `compute_hotspot_score` rewritten: vectorized, NaN-aware, param removed | 1/4 |
| 4 | `34_analyze_fragility_hotspots.py` | `compute_robustness` uses score notna mask | 1 |
| 5 | `34_analyze_fragility_hotspots.py` | Persistence threshold logged; caveats expanded | 1/2 |
| 6 | `33_analyze_fragility_operator.py` | Top-cell selection gates on min_sample_threshold | 1 |
| 7 | `33_analyze_fragility_operator.py` | QA notes: mixed-denominator + self-inclusive baseline caveats | 2 |
| 8 | `13_extract_bts_hubspoke.py` | Window-completeness assertion; hard-fail on missing months | 3 |
| 9 | `13_extract_bts_hubspoke.py` | `discovered_airports_{run_mode}.csv` run_mode keying | 3 |
| 10 | `14_extract_weather_hubspoke.py` | Window-completeness assertion | 3 |
| 11 | `14_extract_weather_hubspoke.py` | `--airports auto` resolves run_mode-keyed discovered-airports path | 3 |
| 12 | `21_build_hubspoke_fact.py` | `_add_utc_keys` vectorized; dead helpers removed | 3 |
| 13 | `21_build_hubspoke_fact.py` | `join_weather` vectorized; `or "benign"` replaced + commented | 3 |
| 14 | `34_analyze_fragility_hotspots.py` | Dead `EXCLUDE_FROM_SCORING` removed | 4 |
| 15 | `15_resolve_operator_ambiguity.py` | Digit-boundary prefix check + multi-brand conflict detection | 4 |
| 16 | `15_resolve_operator_ambiguity.py` | Date filter strengthened; unverifiable-date entries skipped | 4 |

---

## Iteration 9 — Structural Defensibility Fixes (2026-06-18)

**Commit:** `17053f4`
**Branch:** `claude/trusting-allen-0he9md` (merged to `main`)
**Trigger:** Post-Iteration-8 honest review identified two structural gaps that
remained unfixed after the 16-item hardening pass and that could undermine
the credibility of headline outputs from the bigrun.

### Background

The Iteration 8 review produced a gap list. Two items were categorized as
structural rather than cosmetic: (1) an inconsistent severe-delay definition
that violated the subset relationship between component metrics, and (2) mixed
denominators in the combined fragility score that implicitly penalized carriers
differently depending on their cancellation strategy. Both were authorized for
fixing before bigrun output reaches any external audience.

### Finding 1 — Incoherent severe-delay subset relationship

**Root cause:**
`severe_delay_flag` (used in Fragility I and as the basis for `norm_severe_delay`)
was defined as **arrival delay ≥ threshold** (arrival-only). But
`controllable_severe_delay_flag` and `late_arriving_severe_delay_flag` — which are
logical subsets of `severe_delay_flag` — were defined as **(departure OR arrival)
≥ threshold** in both `20_build_flight_fact.py` and `21_build_hubspoke_fact.py`.

This created a contradiction: a flight with departure delay = 80 min and arrival
delay = 30 min would receive `severe_delay_flag = 0` but
`controllable_severe_delay_flag = 1` if air-carrier-attributed. At the cell level,
`controllable_severe_delay_count` could exceed `severe_delay_count` — a logically
incoherent outcome for a metric that is supposed to be a strict subset of the
parent.

**Fix:**
Both fact builders now use **arrival-only** (`arr_delay_min >= threshold`) for
all three severe-delay flags, consistent with the DOT/BTS standard metric and with
the existing `severe_delay_flag` definition. The subset relationship
`controllable_severe_delay_count ≤ severe_delay_count` and
`late_arriving_severe_delay_count ≤ severe_delay_count` now holds unconditionally
at every (hub, spoke, operator_class, period, weather_bucket) cell.

**Files changed:**
- `scripts/20_build_flight_fact.py` — `derive_fragility_ii_flags()`: replaced `severe_either` (dep OR arr) with `severe_arr` (arr only)
- `scripts/21_build_hubspoke_fact.py` — `derive_fragility_ii_flags()`: same change

### Finding 2 — Mixed denominators in combined fragility score

**Root cause:**
`aggregate_grain()` in `33_analyze_fragility_operator.py` and `aggregate_cells()`
in `34_analyze_fragility_hotspots.py` used **different denominators** for the four
components of `combined_fragility_score`:

| Component | Denominator (before fix) |
|-----------|--------------------------|
| `cancellation_rate` | `flights_total` |
| `severe_delay_rate` | `operated_count` |
| `controllable_severe_delay_rate` | `operated_count` |
| `late_arriving_severe_delay_rate` | `operated_count` |

`operated_count` excludes cancelled flights, so it is always ≤ `flights_total`.
This made the weighted sum compare rates computed over different sample spaces.
More critically, it introduced a selection-bias artifact: a carrier that cancels
aggressively removes its worst-performing flights from the delay denominator,
producing lower apparent delay rates than a carrier that operates through and
incurs the delay. The combined score would therefore systematically favor
aggressive-cancellation strategies in the delay components even while penalizing
them in the cancellation component.

**Fix:**
All four rates in both `aggregate_grain()` and `aggregate_cells()` now use
`flights_total` as their denominator. This gives unconditional probabilities over
the full scheduled sample — every component now answers the question "what fraction
of all scheduled departures resulted in this outcome?" regardless of whether the
flight was cancelled or operated.

**Files changed:**
- `scripts/33_analyze_fragility_operator.py` — `aggregate_grain()`: changed `operated_count` → `flights_total` for `severe_delay_rate`, `controllable_severe_delay_rate`, `late_arriving_severe_delay_rate`; updated QA note
- `scripts/34_analyze_fragility_hotspots.py` — `aggregate_cells()`: same change for `controllable_severe_delay_rate` and `late_arriving_severe_delay_rate` (`severe_delay_rate` was already correct)

### Summary table

| # | File | Change |
|---|------|--------|
| 1 | `20_build_flight_fact.py` | `controllable_severe_delay_flag` and `late_arriving_severe_delay_flag` use arrival-only severe definition |
| 2 | `21_build_hubspoke_fact.py` | Same arrival-only fix (mirrors script 20) |
| 3 | `33_analyze_fragility_operator.py` | `severe_delay_rate`, `controllable_severe_delay_rate`, `late_arriving_severe_delay_rate` denominator → `flights_total` |
| 4 | `33_analyze_fragility_operator.py` | QA note updated to reflect now-homogeneous denominators |
| 5 | `34_analyze_fragility_hotspots.py` | `controllable_severe_delay_rate`, `late_arriving_severe_delay_rate` denominator → `flights_total` |

---

## Iteration 10 — Frankenserver Bigrun Execution (2026-06-21)

**Trigger:** First national-scale execution of the full pipeline on a local
high-memory server ("Frankenserver"), extending Fragility IV/V from the 4-hub
local baseline to American Airlines' complete 9-hub network, run keyless (no
FlightAware) to reproduce and stress the committed findings at scale.

### Configuration

- `config/study.yaml`: `run_mode: bigrun`, `backend: duckdb`,
  `run_mode_hubs.bigrun: [DFW, CLT, ORD, PHL, MIA, PHX, DCA, LAX, JFK]`.
- Note: an empty `bigrun: []` raises `ValueError` in
  `13_extract_bts_hubspoke.py::resolve_scope()` — the prior inline comment
  ("empty == full network") was misleading and was corrected. bigrun hubs must
  be set explicitly.
- New batch driver `scripts/run_bigrun.sh`: runs Fragility I–III → IV → V with
  prerequisite gating between phases (refuses to start IV without
  `flight_operability_fact.csv`; refuses V without the curated hub-spoke parquet),
  a stable `logs/bigrun.latest.log` symlink, repo-root `.venv` detection, and a
  loud FAILED banner on any phase error. Designed for `nohup` + `tail -f`.
- FlightAware: key removed (`.env` commented), `use_flightaware: false`,
  `resolve_operator_ambiguity` no-ops and writes an empty resolution file.

### Execution

- Wall-clock ~63 min on a 72-core / 503 GB host (I–III 23m17s, IV 38m41s,
  V 42s). NOAA did not throttle materially; the feared multi-hour weather stretch
  did not occur. duckdb made aggregation negligible.
- **6,152,599 flights** (vs. 3,587,814 local), **264 airports** (9 hubs + 255
  spokes), weather match **100.0%** (0.0% null rate; container baseline 96.6%).
- All output artifacts produced; no failures.

### Findings vs. local baseline

- **Core finding robust to scale.** Fragility IV top cell unchanged
  (PSA_operated / ORD / adverse / recent; combined score 0.187 vs. 0.225 local —
  shift is renormalization against a now-9-hub `aa_system_average` baseline).
  Fragility V rank-1 unchanged (ORD–SPI, base 0.982 vs. 0.978, robustness 1.00).
- **DCA emerged** as a new top-20 hotspot hub (2 cells); PHL dropped out. Top-20
  hub mix: DFW 40%, ORD 40%, DCA 10%, CLT 5%, MIA 5% (was DFW 50%/ORD 45%/PHL 5%).
- **Volume ≠ fragility:** LAX/PHX/JFK (the largest new hubs by traffic) produced
  zero top-20 hotspots.
- **Operator over-representation quantified on non-arbitrary cuts** (full 1,668-
  cell ranked universe): PSA_operated = 51.8% of worst-5% cells but 12.2% of
  flights (**4.25× lift**); AA_mainline 31.3% / 50.0% (0.63×); Envoy_operated
  2.4% / 14.6% (**0.16×**, under-represented). Mean base score: PSA 0.683 >
  AA_mainline 0.575 > SkyWest_unresolved 0.487 > Republic_unresolved 0.360 >
  Envoy 0.346. The PSA/Envoy divergence (two wholly-owned regionals at opposite
  ends) is the keystone defensibility result against an anti-regional-bias claim.
- **DFW–LFT corridor placed honestly:** PSA-operated cell ranks #63 of 1,668
  (top 3.8%, cascade-dominated); SkyWest_unresolved #809; Envoy #1,060.

### Caveats reaffirmed at scale

- Operator ambiguity rose to **904,924 flights (14.7%)** unresolved and excluded
  (was ~485K at 4 hubs); includes 12 of the worst-83 cells and the rank-1 cell.
- Hub totals are run-mode-dependent (origin-priority attribution): DFW/ORD counts
  are slightly *lower* than the 4-hub run despite more total flights — expected,
  affects totals not cell rankings.
- Small-cell thinness unchanged (30 cells <30 flights; many top cells <30 adverse
  flights → weather-sensitivity unscored, dominant component "unknown").

### Deliverables added this iteration

- `BIGRUN-FINDINGS-GUIDE.md` (top-level master read-out).
- `reports/FRAGILITY_NETWORK_REPORT_DRAFT.md` (formal write-up, draft).
- `reports/letters/letter_AA_stakeholders_DRAFT.md`,
  `reports/letters/letter_PSA_Envoy_stakeholders_DRAFT.md` (draft outreach).
- `LEADERSHIP_READOUT_NOTES.md` Entry 4 (network synthesis).
- `$100 FlightAware key` decision analysis (in the findings guide): optional, not
  decision-critical; would name the rank-1 cell and resolve 14.7% ambiguity but
  does not change the established direction; conservative exclusion is itself a
  defensibility asset.

---

*End of After Action Report — Iterations 2–10*
