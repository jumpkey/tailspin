---
title: "Flight Schedule Fragility in the American Airlines Network"
subtitle: "A Reproducible, Public-Data Analysis — Technical Report"
author: "Larry Baker"
date: "June 2026"
---


## Executive Summary

This study asks a narrow, verifiable question: using only public records, can an outside observer locate where American Airlines' branded schedule is most likely to fail a passenger — by hub, spoke, operator, weather, and year? The answer is yes, and the result is specific enough to name routes.

**Data.** Two public sources only: U.S. DOT BTS On-Time Performance and NOAA ASOS hourly weather. The main study covers Jan 2024–Dec 2025 (24 months) across American's 9 hubs and 264 airports total (9 hubs plus 255 discovered spokes) — 6,152,599 flights, joined to weather at a 100.0% match rate (0.0% null). No proprietary, leaked, or insider data was used. A 2026 carve-out (Jan–Apr, the only BTS-published 2026 months) is always compared season-matched to the same months of 2024–25 to remove winter bias.

**Headline findings.**

| Finding | Evidence |
|---|---|
| Fragility is concentrated, not anecdotal | 2,093 (hub, spoke, operator) cells scored; 1,668 met the 100-flight ranking threshold. Top-20 hotspots cluster at DFW (40%) and ORD (40%), with DCA, CLT, MIA making up the rest. |
| One operator is sharply over-represented — and the test is fair | PSA-operated cells are 51.8% of the worst 5% of cells but only 12.2% of ranked flights: a **4.25x** over-representation. Envoy, also a wholly-owned American regional, is *under*-represented (0.16x). AA mainline sits near parity (0.63x). |
| Volume is not fragility | The largest new hubs by traffic — LAX, PHX, JFK — contribute **zero** top-20 hotspots. The signal lives in thin, short-haul regional spokes, dominated by cascade (late-aircraft) delay, not in big gateways or weather alone. |
| The personal anchor corridor confirms the pattern | PSA-operated DFW–LFT ranks **#63 of 1,668** (worst ~3.8%), cascade-driven. The same-corridor Envoy (#1,060) and SkyWest (#809) cells are markedly milder — so this is an operator-and-structure pattern, not "Lafayette is hard." |
| The pattern persists into 2026 | Season-matched, PSA stayed worst and worsened (cancel 4.2%→6.3%, severe 9.5%→11.2%); Envoy stayed cleanest and stable. ORD and DCA severe-delay rose (9.3%→11.6%, 9.1%→10.5%); LAX/PHX stayed cleanest. DFW–LFT is now ~90% PSA (up from ~42% in 2024) and did not improve. |

The Envoy counter-example is the methodological keystone: PSA and Envoy are both wholly-owned American regionals flying American Eagle under American's schedule and brand, yet they land at opposite ends of the fragility distribution. A finding that merely blamed "regional carriers" would implicate both; this one does not, and AA mainline appears throughout the worst cells, so the mainline is not shielded either.

**What we claim, and do not.** The study reports associations in public data, not causation: it has no internal operational data, leans on carriers' self-reported BTS delay-cause codes for cascade/controllable attribution, and conservatively *excludes* 904,924 flights (14.7%) whose operator could not be resolved from route context — including the rank-1 hotspot (ORD–SPI). These limitations are disclosed in full and, where they bite, run *against* the headline rather than toward it.

**The central governance question.** This entire analysis was reproduced from free public records in roughly one hour on commodity-relevant compute (~63 minutes wall-clock). The strongest, fair takeaway is therefore not "one route is bad" — it is this: if an outside observer can see exactly where this branded schedule concentrates its fragility, from public data alone, in an afternoon, the question worth answering is whether the same is being seen and acted on inside the airline — and if not, why not.


```{=openxml}
<w:p><w:r><w:br w:type="page"/></w:r></w:p>
```


## 1. Introduction & Motivation

This study began with a single, ordinary complaint: one frequent flyer's
recurring experience that flights between Dallas/Fort Worth (DFW) and Lafayette,
Louisiana (LFT) were chronically unreliable, and a working hypothesis that bad
weather was the proximate cause. That anecdote is not evidence. The purpose of
the work that follows is to test whether a lived impression survives contact with
the public record — and, having generalized the question, to map where schedule
fragility actually concentrates across an entire hub network.

The investigation deliberately uses only public data: the U.S. DOT Bureau of
Transportation Statistics (BTS) On-Time Performance database and NOAA ASOS hourly
surface-weather observations. No proprietary, leaked, or insider operational data
is used. The main study covers January 2024 through December 2025 (24 months); a
later carve-out extends through the BTS-published 2026 months (January–April),
always compared season-matched to the same months of 2024–25 to remove winter
bias. At national scale the analysis spans American Airlines' nine hubs (DFW,
CLT, ORD, PHL, MIA, PHX, DCA, LAX, JFK), 264 airports, and 6,152,599 flights,
with a 100.0% weather-match rate.

### What this report is

This is an observational study of public outcome data. Its unit of analysis is
the (hub, spoke, operator) cell, further stratified by weather bucket and period,
and scored on a transparent, equally-weighted six-component composite. It
generalizes the originating DFW–LFT question into a network-wide search for
repeatable cancellation and cascade-delay pressure points, and it places the
focal corridor honestly within that larger ranking rather than treating it as
special. The DFW–LFT PSA-operated cell ranks #63 of the 1,668 ranked cells (top
3.8%) — confirming the lived impression without inflating it.

### What this report is not

It is not a causal analysis. We observe associations in outcome records; we do
not have, and do not claim, access to the operational facts — crew routing,
maintenance status, dispatch decisions, ATC interactions — that would be needed
to assign cause. Notably, the original weather hypothesis is not the answer the
data returns: the dominant components in the highest-scoring cells are cascade
(late-arriving-aircraft) delay and economic burden, not weather sensitivity.
Weather sensitivity and absolute disruption level are distinct facts and are kept
separate throughout. This report does not evaluate any carrier's crews,
maintenance, or station performance, and it does not isolate a single driver of
disruption.

### How to read it

State the stance up front: **association, not causation.** Every finding here is
a statement about what public records show, framed conservatively. Where operator
attribution cannot be resolved from route context (14.7% of flights, including
the rank-1 cell), those flights are excluded from operator comparisons rather
than guessed. Where samples are thin (cells below 30 flights), results are flagged
indicative-only. The composite weighting is a disclosed, subjective choice, tested
against three alternate weightings and a robustness score.

Sections 3–8 document the data, design, and methodology in the detail a skeptical
reader needs to attack them; Sections 9–11 report network-wide, corridor, and
2026 findings; Sections 12–15 are candid about weaknesses and fully reproducible.
The intended contribution is not a list of bad routes but a fair, hard-to-dismiss
question: if an outside observer can locate the worst 4% of a national network in
about an hour from free data, is the same being seen and acted on inside?

## 2. Data & Provenance

This study uses **only public data**. There are two required sources — U.S. DOT
Bureau of Transportation Statistics (BTS) On-Time Performance and NOAA ASOS
hourly weather — and one optional, dormant source (FlightAware AeroAPI) used
solely for targeted operator-ambiguity resolution and not exercised in the
results reported here (no API key was set). No internal airline operational,
crew, maintenance, or passenger-manifest data is used or available.

### 2.1 What each source provides

| Source | Provides | Grain | Role |
|---|---|---|---|
| BTS TranStats On-Time Performance | Scheduled and actual departure/arrival times, cancellation flags, delay minutes, and BTS delay-cause codes (carrier, late-aircraft, weather, NAS, security) | One row per scheduled flight | Primary outcome data: cancellations, severe delays, controllable/cascade decomposition |
| NOAA ASOS hourly METAR (via Iowa Environmental Mesonet) | Hourly airport-level observations — visibility, ceiling, present-weather codes | One row per station per hour | Weather stratification at each flight's departure and arrival airport-hour |

BTS supplies every outcome the fragility framework measures. Because BTS
On-Time Performance carries no marketing-carrier field distinct from the
reporting/operating carrier code, operator attribution is derived from
`carrier_code` plus route-context inference (Section 5); the two genuinely
ambiguous codes (`OO` SkyWest, `YX` Republic) account for the 904,924 flights
(14.7%) conservatively excluded from operator comparisons. NOAA ASOS supplies
the weather classification. Weather is assigned at the **endpoint
airport-hours** (departure and arrival), not en route — a documented
simplification (Section 12) that is reasonable for short-haul spoke-to-hub legs
but does not capture in-flight frontal passage or turbulence.

### 2.2 Vintages and study windows

The main study covers **January 2024 through December 2025 (24 months)**. The
2026 carve-out covers **January–April 2026** — the only BTS-published months as
of June 2026 — and is always compared **season-matched** to the same Jan–Apr
months of 2024–25, mitigating (though not eliminating) the winter-heavy bias of
a four-month partial year. BTS monthly archives can be **revised upstream**;
the manifests (Section 2.4) fix the extraction vintage for reproducibility.

### 2.3 Acquisition method and public/licensing status

Both required sources are public and free to redistribute; neither requires
credentialed access.

- **BTS** is downloaded as BTS's pre-built **monthly PREZIP archives** rather
  than through the TranStats form, which would require ASP.NET ViewState/session
  tokens. The PREZIP path needs no session or form fields. At bigrun scale this
  is 24 national monthly files (~27 MB each, ~650 MB).
- **NOAA ASOS** is fetched **per station-month** from the Iowa Environmental
  Mesonet endpoint, with **retry-with-backoff** (30/60/120/240/480 s) to absorb
  429/503 rate-limit responses. The fetch is throttle-bound, not
  transfer-bound: the bigrun spanned 264 airports (9 hubs + 255 discovered
  spokes) across 24 months.

An earlier design called for FAA ASPM weather reports; that source was rejected
because it requires a restricted FAA-registered login and covers only cancelled
flights. NOAA ASOS replaced it and provides weather for all flights, cancelled
or not.

### 2.4 Manifests as audit log

Every ETL script writes a `manifest.csv` recording row counts, extraction
timestamps, source parameters, and **SHA-256 checksums** for each downloaded
file. Raw files are treated as immutable once downloaded (refreshed only with
`--force`), and all downstream steps are deterministic given the staged inputs
and config. No manual spreadsheet editing or copy/paste occurs at any step.
The manifests (`data/raw/bts_hubspoke/manifest.csv`,
`data/raw/faa_hubspoke/manifest.csv`) are committed even though the bulk raw
CSVs are gitignored, so the provenance trail survives without shipping
multi-gigabyte data in the repository.

### 2.5 Weather match and dataset footprint

The bigrun achieved a **100.0% weather match** — every one of the **6,152,599**
flights joined to a NOAA observation, with **0.0% null** on `weather_bucket`.
(For context, the smaller focal-corridor Module A run reported 99.3% departure /
99.8% arrival match, and the container local-mode run 96.6%; the national bigrun
attained complete coverage.) Unmatched flights, where they occur, fall into an
`unknown` bucket and are excluded from weather-stratified analysis rather than
imputed.

The full national bigrun ran in **~63 minutes** of wall-clock time on a
72-core / 503 GB host using the duckdb backend. The underlying raw + curated
dataset (~**4.9 GB**) was **archived** rather than committed; the repository
ships the committed result files in `output/` plus the manifests. Because the
sources are public and the manifests pin vintage and checksums, **the entire
study is reproducible from public sources** by re-running the documented
pipeline (`run_pipeline.sh` → `run_pipeline_iv.sh` → `run_pipeline_v.sh`).

## 3. Study Design

### 3.1 Unit of analysis

The study's atomic observation is a scheduled flight, but every comparative claim is built on a single aggregation grain:

> **hub × spoke × operator_class × weather_bucket × period**

Each dimension is defined operationally and resolved entirely from public data:

| Dimension | Definition | Levels |
|---|---|---|
| `hub` | The American Airlines hub airport, assigned origin-priority (see §5) | DFW, CLT, ORD, PHL, MIA, PHX, DCA, LAX, JFK |
| `spoke` | The non-hub endpoint of a hub-touching flight | 255 discovered spokes (264 airports total incl. hubs) |
| `operator_class` | The carrier/regional operator inferred from BTS reporting + route context | AA_mainline, Envoy_operated, PSA_operated, SkyWest_unresolved, Republic_unresolved, Other_or_non_AA |
| `weather_bucket` | Endpoint ASOS-derived condition severity (§6) | benign (None/Minor), marginal (Moderate), adverse (Severe) |
| `period` | A binary split at `baseline_end`, set by `period_flag` in the fact builders | baseline vs. recent |

Holding four dimensions fixed and varying the fifth is what isolates an operator's behavior from confounds such as a hub's structural weather exposure or a corridor's traffic mix. The grain is also what makes the operator-attribution discipline enforceable: the 904,924 ambiguity-flagged flights (14.7% of 6,152,599) are excluded at this grain rather than guessed, and small cells (<30 flights, `min_sample_threshold`) are flagged indicative rather than dropped silently.

### 3.2 Hub and spoke universe

Hubs are not discovered — they are the fixed scope of the study (American's nine mainline operational hubs and gateways) and are listed explicitly in `run_mode_hubs`. **Spokes, by contrast, are discovered from the data.** Any airport that appears as the non-hub endpoint of a flight touching one of the nine hubs in the study window enters the spoke universe. No external route list is imposed; the network is reconstructed from the BTS On-Time records themselves. The big-run scope resolved to **264 airports (9 hubs + 255 spokes)** across **6,152,599 flights**, with a **100.0% weather match (0.0% null)** after the ASOS join.

A consequence worth flagging: because hub attribution uses origin-priority, hub-level totals are **not directly comparable across run modes** (a flight can only be charged to one hub). This is acceptable within a single run but means the 4-hub `local` baseline and the 9-hub `bigrun` cannot be differenced naively.

### 3.3 Main study and the 2026 carve-out

Two configs drive two temporally distinct runs over the same code path:

| | Main study (`study.yaml`) | 2026 carve-out (`study_2026.yaml`) |
|---|---|---|
| Study window | 2024-01-01 → 2025-12-31 (24 mo.) | 2024-01-01 → 2026-04-30 |
| `baseline` period | 2024 (Jan–Dec) | 2024–2025 |
| `recent` period | 2025 (Jan–Dec) | 2026 (Jan–Apr) |

The `period` split is implemented identically in both: `period_flag` is set at `baseline_end`, cleanly partitioning each fact row into baseline vs. recent. The carve-out reuses every threshold, weather rule, weight vector, and operator-class definition from the main study — **only the temporal split differs** — so any change between the two outputs is attributable to time, not method. The carve-out writes to separate `*_2026` curated paths (`run_2026_carveout.sh`) so the committed 2024-vs-2025 analysis is never overwritten.

The 2026 recent period is deliberately bounded at **Jan–Apr 2026**: these are the only BTS-published months as of June 2026. This is a four-month, winter-heavy partial year and is the single largest external-validity caveat in the carve-out.

### 3.4 Season-matching the partial year

Comparing a Jan–Apr 2026 partial year against a full 2024–25 baseline would conflate seasonality (winter operations are structurally worse) with genuine year-over-year change. To remove this, **every 2026 comparison is season-matched**: 2026 Jan–Apr is compared only against the **same Jan–Apr months of 2024–25**, never against the full baseline year. This does not eliminate the small-sample limitation, but it removes the dominant confound. All 2026 figures reported downstream (e.g., network-wide cancellation and severe-delay shifts, the DFW–LFT corridor) are season-matched on this basis.

### 3.5 Run modes

A single `run_mode` switch (`test` | `local` | `bigrun`) selects both the hub set and the time window, so the pipeline scales from a smoke test to the full network without code changes:

| Mode | Hubs | Window | Purpose |
|---|---|---|---|
| `test` | DFW | Jan 2024 (1 mo.) | Fast smoke test / CI |
| `local` | DFW, CLT, ORD, PHL | full window | Developer iteration on a laptop-sized slice |
| `bigrun` | all 9 hubs | full window | Canonical result (264 airports, 6.15M flights) |

`bigrun` must be set explicitly — an empty hub list raises `ValueError` in `resolve_scope()`, a guard against a silently empty canonical run. All headline figures in this report come from `bigrun` on the `duckdb` backend, completing in roughly **63 minutes of wall-clock on a 72-core / 503 GB host**.

## 4. Methodology: Operator Attribution

Every claim about a *specific* operator in this study depends on first answering a
deceptively hard question: who actually flew the flight? The U.S. DOT BTS On-Time
Performance feed records a single `Reporting_Airline` (carrier) code per flight and
has no separate marketing-carrier field. For a major like American that subcontracts
much of its regional flying to multiple operators — some wholly owned, some
independent — that one code is sometimes sufficient and sometimes fundamentally
ambiguous. Our attribution method is built to be exact where the code permits and
to *withhold judgment* where it does not, rather than guess.

### Operator classes and the wholly-owned-subsidiary framing

We classify all 6,152,599 in-scope flights into six operator classes. Three of these
resolve directly and unambiguously from the BTS carrier code (per
`config/operator_classes.yaml`, `as_of` 2026-06-16):

| Carrier code | Operator class | Resolution | Flights |
|---|---|---|---|
| `AA` | `AA_mainline` | Direct (high confidence) | 1,943,962 |
| `MQ` | `Envoy_operated` | Direct (high confidence) | 568,329 |
| `OH` | `PSA_operated` | Direct (high confidence) | 476,691 |

Envoy Air (`MQ`) and PSA Airlines (`OH`) are **wholly-owned regional subsidiaries of
American Airlines Group**, disclosed in American's public corporate filings as
operating *exclusively* as American Eagle under American's schedule and brand. This
matters for interpretation: when this report compares PSA against AA mainline against
Envoy, it is comparing *operating structures within the same parent company flying the
same brand*, not American against an outside competitor. Because each of these carriers
flies under one and only one mainline contract, its code maps to exactly one operator
class everywhere in the network, and no further inference is required.

### Genuinely ambiguous codes: route-context inference for OO and YX

Two regional codes cannot be resolved by code alone, because the operator flies for
more than one mainline brand simultaneously under separate capacity-purchase
agreements:

- **`OO` — SkyWest.** Per SkyWest's FY2024 Form 10-K, SkyWest operates concurrently
  as United Express (~890 daily departures), Delta Connection (~700), American Eagle
  (~380), and Alaska Airlines (~220). A bare `OO` row could be any of the four.
- **`YX` — Republic.** Republic operates as American Eagle, United Express, and Delta
  Connection.

For these, attribution proceeds in priority order. **Route-context inference**
(`scripts/lib/operator_classify.py`) is applied first: if a flight's route already
belongs to a pre-validated basket in `config/routes.yaml`, that basket assignment
implies the mainline contract and resolves the row deterministically. This works well
for Module A (the focal corridor, which has hand-validated baskets) but, by
construction, cannot resolve flights in the Module B hub-spoke expansion, where the
spoke universe is discovered from the data and no pre-built basket exists. Rows that
route-context inference cannot resolve retain the explicit holding labels
`SkyWest_unresolved` (606,125 flights) and `Republic_unresolved` (298,799 flights).

### The unresolved-ambiguity classes are excluded, not guessed

This is the most important defensive choice in the attribution layer. The two
unresolved labels together account for **904,924 flights — 14.7% of the 6,152,599-flight
universe** — and they are **conservatively excluded from every operator-class
comparison**, never imputed to a most-likely brand. We would rather report a
narrower-but-defensible operator comparison than inflate any single operator's count
with flights we cannot prove it flew.

| Operator class | Flights | Share | Status in operator comparisons |
|---|---|---|---|
| `Other_or_non_AA` | 2,258,693 | 36.7% | Excluded (peer/other carriers) |
| `AA_mainline` | 1,943,962 | 31.6% | Included |
| `SkyWest_unresolved` | 606,125 | 9.9% | **Excluded (ambiguous)** |
| `Envoy_operated` | 568,329 | 9.2% | Included |
| `PSA_operated` | 476,691 | 7.7% | Included |
| `Republic_unresolved` | 298,799 | 4.9% | **Excluded (ambiguous)** |

The exclusion is not cost-free, and we flag it candidly. The single highest-scoring
Fragility IV cell is `PSA_operated / ORD / adverse / 2025` (combined fragility score
0.187, 186 flights) — but the top *unresolved* cell would, if resolved, potentially
enter the same neighborhood. More directly, the Fragility V rank-1 network hotspot,
ORD–SPI, carries the `SkyWest_unresolved` label (base score 0.982, robustness 1.00):
it ranks first precisely because its disruption signature is severe, yet we cannot
attribute it to a specific mainline contract under the keyless configuration. Readers
should treat all SkyWest- and Republic-specific silence in the operator findings as a
deliberate abstention, not evidence of clean performance.

### The optional FlightAware AeroAPI validation path (kept off here)

The pipeline includes a second, targeted resolution method that was **deliberately
left disabled for this run**. `scripts/15_resolve_operator_ambiguity.py` can issue a
single-flight historical lookup (`GET /history/flights/{ident}`) against the FlightAware
AeroAPI for each otherwise-unresolved row, inspecting that flight's codeshares for an
`AA`/`UA`/`DL`/`AS`-prefixed identifier to recover the operating contract. It is a
narrow per-flight query — never a bulk pull — gated independently by
`resolve_operator_ambiguity.enabled` and a `max_queries` budget, and it no-ops safely
(writing an empty resolution file) when `FLIGHTAWARE_API_KEY` is unset, so no other
stage ever depends on a live key. Because the bigrun was executed **keyless**, this
path produced no resolutions, which is the direct and expected cause of the 14.7%
exclusion above. Enabling a key in future work would reassign most of those 904,924
flights to `American_Eagle`, `United_Express`, `Delta_Connection`, or `Alaska` contracts,
and would in particular let the ORD–SPI rank-1 hotspot and similar `OO`/`YX` cells be
attributed to a named operator — the single largest available improvement to attribution
coverage.

## 5. Methodology: Weather & Metric Definitions

This section specifies how observed weather is reduced to three ordinal buckets, how that weather is joined to individual flights, and how the four outcome metrics are defined. The aim is to make every figure in the Findings sections reconstructible from public inputs and explicit rules. Where a choice is a judgment call rather than a standard, it is flagged as such.

### 5.1 Weather source and bucketing

Weather is sourced from NOAA ASOS hourly METAR observations, retrieved through the Iowa Environmental Mesonet (IEM) ASOS archive — a free, public, no-login endpoint. Each raw observation is normalized to one row per airport-hour (UTC), carrying visibility (statute miles), derived ceiling (feet AGL), and present-weather codes.

Each airport-hour is classified into one of three buckets. The thresholds map deliberately onto the FAA's published VFR / MVFR / IFR flight-rule categories, so the cut points are interpretable and externally anchored rather than tuned to this dataset:

| Bucket | Rule (any condition triggers the worse bucket) |
|---|---|
| **benign** | visibility ≥ 3 SM **and** ceiling ≥ 1000 ft **and** no precipitation codes |
| **marginal** | visibility 1–3 SM **or** ceiling 500–1000 ft **or** RA/SN/FG/BR/DZ present |
| **adverse** | visibility < 1 SM **or** ceiling < 500 ft **or** TS/FZ/BLSN/+SN present |

The buckets are strictly ordered: `adverse > marginal > benign`.

### 5.2 Joining weather to flights

Weather is assigned per flight at **endpoint airport-hours**, not en route. The procedure (implemented in the fact builders):

1. Convert each flight's scheduled departure from local airport time to UTC using DST-aware, per-airport timezones (`zoneinfo`; ICAO/timezone lookups via `airportsdata` for discovered spokes).
2. Derive scheduled arrival UTC by adding BTS `scheduled_elapsed_min` to departure UTC, handling overnight rollovers.
3. Join the airport-hour weather table twice — once on `(origin, dep_utc_date, dep_utc_hour)`, once on `(dest, arr_utc_date, arr_utc_hour)`.
4. Set the flight's `weather_bucket` to the **worse** of departure and arrival conditions.

Critically, this join applies to **every scheduled flight — operated and cancelled alike** — because the weather context comes from the airport-hour, not from any flight-level outcome record. This is the fix that made cross-carrier weather comparison valid: an earlier design joined weather only via a cancelled-flights-only source, which forced the cancellation-rate denominator to equal its numerator in non-benign buckets (rate ≈ 1.0 by construction). At national bigrun scale the endpoint-hour join achieves **100.0% weather match (0.0% null)** across 6,152,599 flights.

**Limitation.** Endpoint weather captures conditions at the two airports at the two relevant hours; it does not capture en-route turbulence or fronts crossed in flight. For short-haul spoke-to-hub flights endpoint weather is generally the dominant cancellation driver, so this is an accepted simplification rather than a measurement of total weather exposure.

### 5.3 Outcome metric definitions

All four composite components are computed over a single, common denominator: **all scheduled flights** in the cell (`flights_total`). Let a "cell" be a (hub, spoke, operator_class, period, weather_bucket) group.

- **Cancellation rate** = `cancelled_count / flights_total`.
- **Severe delay** = arrival delay ≥ 60 minutes (the DOT/BTS standard; `delay_threshold_minutes: 60`). Severe-delay rate = `severe_delay_count / flights_total`. By definition only operated flights can be severely delayed.
- **Controllable severe delay** ⊆ severe delay: a severely delayed flight whose BTS-reported primary delay cause is air-carrier (controllable). Rate = `controllable_severe_delay_count / flights_total`.
- **Late-arriving / cascade severe delay** ⊆ severe delay: a severely delayed flight attributed to a late-arriving aircraft (knock-on / cascade). Rate = `late_arriving_severe_delay_count / flights_total`.

The two cause-decomposed metrics are **strict subsets** of severe delay:

```
controllable_severe_delay_count  ≤  severe_delay_count
late_arriving_severe_delay_count ≤  severe_delay_count
```

This relationship now holds unconditionally at every cell. It did not always: cause-coded flags were once defined on `(departure OR arrival) ≥ threshold` while the parent `severe_delay_flag` used arrival-only, so a flight with an 80-minute departure delay but a 30-minute arrival could be counted as a controllable severe delay without being a severe delay at all — allowing the subset to exceed its parent. All three flags were standardized to arrival-only (`arr_delay_min ≥ 60`), restoring the containment.

### 5.4 Denominator standardization (AAR Iteration 9)

A more consequential correction concerns the denominator itself. Earlier code mixed denominators across the composite's components:

| Component | Denominator (before) | Denominator (after) |
|---|---|---|
| cancellation rate | `flights_total` | `flights_total` |
| severe delay rate | `operated_count` | `flights_total` |
| controllable severe delay rate | `operated_count` | `flights_total` |
| cascade severe delay rate | `operated_count` | `flights_total` |

Because `operated_count` excludes cancellations (`operated_count ≤ flights_total`), the weighted composite was summing rates measured over different sample spaces. Worse, it created a **cancellation-strategy artifact**: a carrier that cancels aggressively removes its worst-performing flights from the delay denominator, lowering its apparent delay rates — so the composite quietly *rewarded* aggressive cancellation in the delay components while penalizing it only in the cancellation component. Standardizing all four components to `flights_total` removes that bias. Each component now answers one unconditional question: *what fraction of all scheduled departures in this cell resulted in this outcome?* This is the standardization underlying the operator and hotspot rankings reported in Sections 9–11.

These metric definitions feed directly into the six-component composite hotspot score described in Section 7; the two remaining components (weather sensitivity and economic burden) are defined there.

## 6. Methodology: Fragility Framework & Scoring

The fragility analysis was built incrementally as five numbered stages (Fragility I–V). Each stage answers a more general question than the last, and each reuses the metric definitions fixed in Section 6 (Weather & Metric Definitions). The progression is deliberate: it starts from a single, fully-auditable corridor and only widens scope once the narrower computation has been validated. Reviewers should treat the stages as nested, not independent — the network engine (V) is the corridor scorer (I–IV) applied across thousands of cells with the addition of cross-cell normalization.

### 6.1 The Fragility I–V progression

| Stage | Unit of analysis | Question answered |
|---|---|---|
| I | DFW–LFT focal corridor | Is the focal corridor measurably fragile, and by which raw rates? |
| II | Corridor × weather bucket | Does fragility concentrate in adverse weather? |
| III | Corridor × operator, with UA/DL peer baseline | Which operator carries the fragility, net of a peer-carrier benchmark? |
| IV | (operator × hub × weather × period) cells | A single `combined_fragility_score` per cell, comparable across the network |
| V | (hub, spoke, operator_class) cells, network-wide | A normalized composite hotspot score ranking all cells |

Fragility III introduced the peer-carrier economic baseline (UA/DL route basket) that Module A (focal corridor) retains unchanged. Fragility IV generalized scoring to all hubs but lacked a pre-built peer basket at each new hub, which motivated the pooled `aa_system_average` baseline used in Module B (Section 6.5). Fragility V added cross-cell normalization, the six-component composite, weighting-scenario robustness, and the persistence check.

### 6.2 The combined_fragility_score (Fragility IV)

Fragility IV produces one score per (operator_class, hub_family, weather_bucket, period_flag) cell. It is a fixed equal-weighted sum of four rates:

| Component | Weight |
|---|---|
| `cancellation_rate` | 0.25 |
| `severe_delay_rate` | 0.25 |
| `controllable_severe_delay_rate` | 0.25 |
| `late_arriving_severe_delay_rate` | 0.25 |

Critically, all four components share a single denominator — `flights_total`, the full scheduled sample for the cell — so each is an unconditional probability over the same sample space (AAR Iteration 9 standardization). This is what allows the four to be summed without a denominator-mismatch artifact. The top Fragility IV cell is **PSA_operated / ORD / adverse / 2025 (recent)** with `combined_fragility_score` = **0.1868** over 186 flights, driven by a 22.6% cancellation rate, a 30.7% severe-delay rate, and a 16.7% late-arriving (cascade) severe-delay rate. Note the score is an absolute level (sum of raw rates), not normalized against other cells — that step is Fragility V's contribution.

### 6.3 The composite hotspot score (Fragility V): six components, equal weights

Fragility V scores 2,093 (hub, spoke, operator_class) cells; **1,668** clear the `hotspot_min_flights = 100` threshold required for ranking. The composite is a weighted sum of six components. In the base scenario each carries weight 0.1667 (1/6):

| Component | Captures |
|---|---|
| `norm_cancellation` | cancellation rate |
| `norm_severe_delay` | arrival delay ≥ 60 min rate |
| `norm_controllable` | carrier-controllable severe-delay rate |
| `norm_cascade` | late-arriving (knock-on) severe-delay rate |
| `norm_weather_sensitivity` | degradation of the fragility rate from good to adverse weather |
| `norm_economic_burden` | economic-burden proxy (Section 6.5) |

**Normalization.** Each component is converted to a **percentile rank across all ranking-eligible cells**, then averaged with its weights. Percentile-rank normalization (rather than min–max or z-score) is robust to the heavy right tails and outliers that raw delay rates exhibit, and it makes the six dimensionally-different components directly comparable on a common [0,1] scale. The penalty is that the composite measures *relative* standing within this specific cell population, not an absolute fragility magnitude. The Rank-1 cell is **ORD–SPI (SkyWest_unresolved)**, base score **0.982**, robustness 1.00.

**Weather-sensitivity gating.** `norm_weather_sensitivity` is computed only for cells with at least `hotspot_min_adv_flights = 30` adverse-weather flights. Cells below that gate are set to NaN and scored on the remaining five components with weights renormalized. Without this gate, a cell with a handful of adverse flights and a perfect fragility rate would rank first — a small-sample upward bias.

### 6.4 Alternate weighting scenarios and the robustness score

Equal weighting is a subjective choice; to test sensitivity to it, three additional scenarios shift mass toward one emphasis:

| Scenario | cancel | severe_delay | controllable | cascade | weather_sens. | economic |
|---|---|---|---|---|---|---|
| `base` | 0.167 | 0.167 | 0.167 | 0.167 | 0.167 | 0.167 |
| `weather_emphasis` | 0.10 | 0.10 | 0.10 | 0.10 | **0.50** | 0.10 |
| `controllable_cascade_emphasis` | 0.10 | 0.10 | **0.30** | **0.30** | 0.10 | 0.10 |
| `economic_emphasis` | 0.10 | 0.10 | 0.10 | 0.10 | 0.10 | **0.50** |

The **robustness score** is the fraction of the four scenarios in which a cell appears in the top-N. A cell scoring 1.00 (e.g., ORD–SPI) is top-ranked regardless of which emphasis a stakeholder prefers, and is therefore a more defensible prioritization target than a cell that is top-ranked only in the base scenario. A separate **persistence flag** marks cells that are independently top-N in *both* the 2024 baseline and 2025 recent sub-periods (each using `min_flights // 2` as its threshold); only **1** of the top-20 cells (DFW–CID, AA_mainline) is persistent, consistent with the winner's-curse expectation that single-period top-N membership is partly noise. High robustness combined with persistence is the strongest signal.

### 6.5 The economic-burden proxy (aa_system_average, pooled)

Module B (the network expansion) has no pre-built peer-carrier route basket at each new hub, so its economic-burden component benchmarks each cell against an `aa_system_average` baseline that **pools all resolved operator classes within the same hub × weather × period cell**. Excess cancellations and excess controllable/cascade delay minutes versus that pooled mean are converted to dollars using published DOT block-cost benchmarks (an absolute-cost proxy, not airline financials). For the top Fragility IV cell this yields an economic-burden proxy of **$580,079** (~$3.12M per 1,000 flights).

This baseline is deliberately **conservative**: because it is pooled rather than leave-one-out, a high-volume operator with above-average fragility is itself part of its own baseline and therefore partially *suppresses* its own measured excess. The reported economic excess for the worst, highest-volume operators is thus a lower bound, not an inflation. Reviewers should read the economic component as conservative by construction.

### 6.6 Known limitations of the framework

The composite weights are a subjective choice (mitigated, not eliminated, by the scenario/robustness apparatus). The `norm_severe_delay` component tests arrival delay only, whereas `norm_controllable` and `norm_cascade` test departure-or-arrival delay; the components are not strictly nested and the composite mixes slightly different event definitions. Percentile-rank normalization measures relative standing within this cell population only. And the entire framework is associational: the scores rank where fragility is observed, not why it occurs.

## 7. Controls & Defensibility

This section enumerates the design choices that exist specifically to keep the
analysis fair and difficult to dismiss. Each is a deliberate decision, made
before the headline result was known, that trades convenience or completeness
for defensibility. None of them is a post-hoc rationalization of the finding;
several actively work *against* it.

### 7.1 Public data and full reproducibility

The study uses only two public sources: U.S. DOT BTS On-Time Performance and
NOAA ASOS hourly weather. There is no proprietary, leaked, or insider data, and
no privileged access to American Airlines' operational systems. Anyone can
obtain the same inputs and re-derive every number. The entire 6,152,599-flight,
264-airport pipeline runs from one command (`bash scripts/run_bigrun.sh`) in
roughly 63 minutes of wall-clock on commodity high-memory hardware. The
reproducibility burden is therefore low enough that a skeptic can verify rather
than argue. This is the foundational control: a result an outsider can
regenerate cannot be waved away as a black box.

### 7.2 Conservative exclusion of ambiguous flights

SkyWest and Republic fly for multiple mainline brands, so route context alone
cannot attribute their flights to a specific contract. Rather than guess, the
analysis **excludes** all 904,924 such flights — 14.7% of the dataset — from
every operator comparison. This is costly: it removes the rank-1 hotspot
(ORD–SPI, currently labeled `SkyWest_unresolved`) and 12 of the worst-83 cells
from attributed conclusions. We accept that cost. The headline (PSA
over-representation; widespread structural fragility) rests on resolved data
only. Refusing to impute operator identity is a defensibility asset: there is no
attribution we cannot defend, because we made none we were unsure of.

### 7.3 Disclosed weights, thresholds, and alternate scenarios

The composite hotspot score is six equal-weighted normalized components
(cancellation, severe delay, controllable, cascade, weather sensitivity,
economic burden). Equal weighting is a subjective choice and is disclosed as
such. To test whether the ranking depends on that choice, three alternate
weighting scenarios plus a robustness score are reported. The rank-1 hotspot
(ORD–SPI) carries a robustness of 1.00, and the top cell did not move when the
study scaled from 4 hubs to 9. Thresholds are stated explicitly: 60-minute
arrival for "severe delay" (the DOT standard, not a custom cutoff) and a
100-flight minimum for ranking eligibility (1,668 of 2,093 scored cells qualify).
A reviewer can re-weight or re-threshold and check stability themselves.

### 7.4 Coherent metrics: subsets and a shared denominator

The four composite components that derive from delay (controllable,
late-arriving/cascade) are strict subsets of the severe-delay parent, and all
components share a single denominator — all scheduled flights (AAR Iteration 9
standardization). This removes a cancellation-strategy artifact in which a
carrier that cancels aggressively would appear to have *fewer* delays simply
because cancelled flights left the delay denominator. Metric coherence closes a
common and legitimate line of attack on operational comparisons.

### 7.5 The PSA-vs-Envoy divergence as a built-in anti-bias check

The strongest internal control is structural. Envoy and PSA are **both**
wholly-owned American regional subsidiaries flying as American Eagle under
American's schedule and brand. If the method were biased against regional
carriers, both would surface in the worst cells. They do not:

| Operator class | Share of worst 5% cells | Share of ranked flights | Over-representation | Mean base score |
|---|---|---|---|---|
| PSA_operated | 51.8% | 12.2% | 4.25× | 0.683 |
| AA_mainline | 31.3% | 50.0% | 0.63× | 0.575 |
| Envoy_operated | 2.4% | 14.6% | 0.16× (under) | 0.346 |

PSA is over-represented 4.25×; Envoy is *under*-represented at 0.16×, the
lowest mean base score of any operator class. A finding that singled out
"regionals" would implicate both subsidiaries; this one separates them. The
result is operator- and cell-specific, which is exactly what makes it credible.

### 7.6 Mainline is included, not shielded

American mainline is not exempted from scoring. It accounts for 50.0% of ranked
flights and appears throughout the worst cells (31.3% of the worst 5%, 0.63×
over-representation), and in the 2026 carve-out its season-matched cancellation
rate more than doubled (1.5% → 3.4%). The economic-burden baseline
(`aa_system_average`) is pooled rather than leave-one-out, which slightly
*suppresses* a high-volume operator's own excess — a conservative choice that
works against, not toward, the headline. The method cannot be characterized as
protecting the parent carrier.

### 7.7 Season-matching the 2026 carve-out

The 2026 data covers only Jan–Apr (the BTS-published months as of June 2026), a
winter-heavy partial year. Comparing it directly to a full prior year would
import a seasonal bias. Instead, 2026 is always compared **season-matched** to
the same Jan–Apr months of 2024–25. This neutralizes the winter skew and lets
the persistence finding (PSA worst and worsening: cancel 4.2% → 6.3%, severe
9.5% → 11.2%; Envoy stable: cancel 2.4% → 2.7%) stand on a like-for-like basis.

### 7.8 Small-sample flagging

Reliability floors are enforced and disclosed. Cells below 100 flights are
excluded from ranking; the 30 cells below a 30-flight floor are flagged
"indicative only." Where a high-ranked cell has fewer than 30 adverse-weather
flights, its weather-sensitivity component is not scored (reported as dominant
component "unknown") rather than computed on noise. Thin cells are labeled, not
laundered into the headline.

Taken together, these controls mean the study's central claim survives because
it does not overreach: it reports associations in public data, names what it
will not claim, and embeds checks — most notably the PSA/Envoy divergence — that
a hostile reviewer would otherwise have to construct themselves.

## 8. Findings: Network-wide

This section reports the network-level results of the Fragility V hotspot engine over the full Jan 2024–Dec 2025 study window across American's nine-hub branded network. All figures are associations observed in public BTS on-time data, not causal claims; see §12 for the limitations that bound each statement.

### 8.1 The signal is distributed, concentrated, and stable

The hotspot engine scored **2,093** distinct (hub, spoke, operator-class) cells. Of these, **1,668** met the 100-flight minimum required for normalization and ranking; the remainder are retained but excluded from ranking. This matters for interpretation: fragility is not a single bad route or an anecdote. It is a *distributed* pattern measured across more than sixteen hundred markets, within which a measurable minority of cells carry disproportionate disruption.

Two stability checks support the ranking. First, scaling from the four-hub local baseline to the nine-hub national run (1.71× the flights, +2.6M records) did not move the core finding: the rank-1 hotspot remained **ORD–SPI** and the most fragile operator/weather cell remained PSA-at-ORD-adverse. Adding five hubs confirmed rather than diluted the signal. Second, each top cell carries a **robustness score** — the fraction of four alternate weighting scenarios under which the cell remains top-N — which is a stronger signal than base-scenario rank alone. The top six cells all hold robustness 1.00. Persistence (top-20 in both an early and late sub-period independently) is rarer and expected to be: only **1** of the top-20 cells (DFW–CID, AA_mainline) is flagged persistent, consistent with winner's-curse expectations for a 20-of-1,668 draw. We therefore lean on robustness, not single-period rank, when prioritizing.

### 8.2 One operator class is over-represented in the worst cells

![One operator flies 1 in 8 flights but half the worst trouble spots](output/exec/B1_one_operator_half_the_trouble.png)

The central network finding is an over-representation of **PSA_operated** cells among the worst-scoring cells, measured as the share of worst cells divided by the operator's share of all ranked flights (a lift of 1.0× means proportional; above 1.0× means over-represented).

| Operator class | Worst 5% (83 cells) | Worst 10% | Worst 25% | Share of ranked flights | Lift (worst 5%) |
|---|---|---|---|---|---|
| **PSA_operated** | **51.8%** | 43.7% | 33.3% | 12.2% | **4.25×** |
| AA_mainline | 31.3% | — | — | 50.0% | 0.63× |
| Envoy_operated | 2.4% | — | — | 14.6% | **0.16×** |

PSA flies roughly **1 in 8** ranked flights yet accounts for **more than half** of the worst 5% of cells — a 4.25× over-representation that persists, attenuating gradually, deeper into the distribution (3.58× at worst 10%, 2.73× at worst 25%). The pattern is corroborated by mean base score across the *entire* ranked universe, not just the tails:

| Operator class | Mean base hotspot score |
|---|---|
| PSA_operated | 0.683 |
| AA_mainline | 0.575 |
| SkyWest_unresolved | 0.487 |
| Republic_unresolved | 0.360 |
| Envoy_operated | 0.346 |

Two design features make this finding hard to dismiss as anti-regional bias. **Envoy and PSA are both wholly-owned American regional subsidiaries** flying as American Eagle under American's own schedule and brand — yet they land at opposite ends: PSA is over-represented (4.25×) while Envoy is the *most under-represented* class in the network (0.16×, and lowest mean score at 0.346). A finding that merely indicted "regional carriers" would implicate both; this one separates them. And AA_mainline is present throughout the worst cells (31.3% of the worst 5%) at roughly proportional-to-below levels (0.63×), so the mainline is neither shielded nor scapegoated. The signal is operator- and cell-specific. A further conservative bias works *against* the headline: the economic-burden component uses a pooled `aa_system_average` baseline rather than leave-one-out, which slightly suppresses a high-volume operator's own excess (§7), so PSA's true over-representation is, if anything, understated.

### 8.3 Volume does not predict fragility

![Size does not predict trouble](output/exec/B2_size_doesnt_predict_trouble.png)

Hub traffic and hub fragility are decoupled. The largest *new* hubs by volume — **LAX, PHX, and JFK** — contributed **zero** top-20 hotspots. Fragility instead concentrates in thin, short-haul regional spokes. Top-20 hub concentration:

| Hub | Cells in top-20 | Share | Flights in those cells |
|---|---|---|---|
| DFW | 8 | 40% | 8,305 |
| ORD | 8 | 40% | 5,791 |
| DCA | 2 | 10% | 4,344 |
| CLT | 1 | 5% | 120 |
| MIA | 1 | 5% | 187 |

DFW and ORD together hold 80% of the top-20. The CLT and MIA entries are small cells (120 and 187 flights) and should be read as indicative. A caveat applies to comparing hub *totals* across run modes: the origin-priority hub-attribution rule means nine-hub hub totals are not directly comparable to the four-hub run; cell-level rankings are unaffected (§5, §12).

### 8.4 DCA emerged; PHL exited

Two structural shifts appear at national scale relative to the four-hub baseline (where the top-20 split DFW 50 / ORD 45 / PHL 5). **DCA (Reagan National) newly emerged**, surfacing two top-20 cells (DCA–LAN and DCA–CVG, both PSA_operated), having been absent at four hubs. Conversely, **PHL dropped out** of the top-20 entirely. The change is partly attribution mechanics (more hubs absorb origin-priority assignment) and partly a genuine surfacing of DCA's thin-spoke exposure, but it is a clear caution against treating any single hub's prominence as fixed.

### 8.5 What drives the worst cells: cascade and economic burden, not weather

Examining the dominant (highest-percentile) component within each top-20 cell, the leading signatures are **economic_burden (3 cells)**, **cascade / late-arriving aircraft (3 cells)**, and **weather_sensitivity (3 cells)**, with one cell led by severe_delay; the remaining 10 are labelled "unknown" because they fall below the adverse-flight threshold needed to score weather sensitivity and are scored on the other five components. The substantive point is that **weather does not dominate the worst cells** — cascade and economic burden do — which is consistent with schedule and equipment-routing structure as much as with execution or weather exposure.

The **rank-1 cell is ORD–SPI** (Chicago–Springfield, IL), operator-class **SkyWest_unresolved**, with a base score of **0.982** and robustness **1.00** — identical to the four-hub baseline's rank-1. It illustrates two things at once: the signal's stability, and the cost of the operator-ambiguity exclusion. ORD–SPI carries the highest fragility score in the network, yet because SkyWest flies for multiple mainline brands, its operator label cannot be resolved from route context alone and it sits in the 14.7% conservatively excluded from operator comparisons (§5, §12). Twelve of the worst-83 cells share this limitation. We name the cell but, deliberately, not its contracting structure — a FlightAware AeroAPI key would resolve it, but the conservative exclusion is preserved here as a defensibility asset rather than guessed past.

## 9. Findings: DFW-LFT Corridor

The Dallas/Fort Worth–Lafayette (DFW–LFT) corridor is the study's focal single-route case. It is a thin regional spoke flown by three of American's regional carriers under the American Eagle brand, and it serves two purposes here: first, it demonstrates the fragility framework at the level a single traveler experiences; second, it shows that the network-wide structure documented in Section 8 reproduces on an individual corridor rather than being an artifact of aggregation. The findings below draw on the corridor focal report and the canonical figures; small weather-stratified cells in the 2026 window are flagged as directional throughout.

### 9.1 Weather sensitivity: two facts that are not in conflict

The lead corridor finding concerns weather, and it requires care because two true statements about it look superficially contradictory. Measuring the share of flights cancelled or delayed at least one hour across the 2024–2025 main study window, stratified into good- and bad-weather buckets, produces the following per-operator picture:

| Operator (American Eagle) | Good weather | Bad weather | Weather multiplier |
|---|---|---|---|
| Envoy | 7% | 30% | 4.3× (most sensitive) |
| SkyWest | 8% | 28% | 3.3× |
| PSA | 16% | 40% | 2.5× |

The two facts are these:

- **Envoy is the most weather-*sensitive* operator** on the corridor. Its disruption rate climbs most steeply from good to bad conditions — a 4.3× jump — meaning its schedule degrades the sharpest when weather turns. This is the weather-stress signature that motivated the original question about the route.
- **PSA is the worst in *absolute* terms in every weather bucket.** PSA's good-weather rate (16%) already exceeds Envoy's and SkyWest's bad-weather rates, and under adverse conditions roughly 4 in 10 PSA flights are cancelled or badly delayed (40%).

These are not in tension because the multiplier and the level measure different things. The multiplier is a *ratio* describing how much an operator's performance changes between conditions; the absolute rate is the *level* a passenger actually faces. An operator can have a modest multiplier and still be the worst in every bucket if its baseline is high — which is exactly PSA's case — while another operator can post the steepest multiplier yet remain the lowest-rate operator overall, which is Envoy's case. Conflating the two ("Envoy is worst in weather because it has the highest multiplier") would invert the passenger-facing conclusion. The honest reading is that **no operator on the corridor holds up well as weather deteriorates, the most weather-sensitive operator is Envoy, and the operator a traveler is most likely to be disrupted by in any given condition is PSA.**

A useful fairness check is built in: the three operators diverge sharply from one another on the *same physical route*. That rules out "Lafayette is simply a hard airport" and "all regional flying is bad" as sufficient explanations — the variation is operator-specific and condition-specific.

![On DFW-Lafayette PSA is least reliable in any weather](output/exec/A1_weather_breaks_schedule.png)

![Weather hits every operator hard](output/exec/A1b_weather_sensitivity.png)

### 9.2 Corridor fragility rank by operator

Placing each operator's DFW–LFT cell against the full network of 1,668 ranked (hub, spoke, operator) cells shows that fragility on the corridor is also operator-dependent:

| Operator on DFW–LFT | Network rank (of 1,668) | Percentile |
|---|---|---|
| PSA | #63 | top 3.8% |
| SkyWest | #809 | ~top 48% |
| Envoy | #1,060 | ~top 64% |

The PSA-operated cell sits in the worst ~4% of the entire 9-hub network, and the focal report characterizes its score as cascade-driven — that is, dominated by knock-on (late-inbound-aircraft) delays rather than by weather alone. The SkyWest and Envoy cells on the identical route fall near or below the middle of the distribution. This is the single corridor confirming the network result: PSA-operated routes are over-represented among the worst trouble spots (Section 8 reports a 4.25× over-representation in the worst 5% of cells), and Envoy is not.

### 9.3 Operator rotation: the corridor is now ~90% PSA

DFW–LFT has no single steady operator; assignment rotates among PSA, Envoy, and SkyWest month to month. That rotation has, however, resolved decisively toward PSA. Envoy — historically a major operator on this route — has nearly exited since late 2025, and through the most recent data (2026) the corridor is overwhelmingly PSA, up from roughly 42% PSA in 2024 to about 89–90%.

![The operator on your route keeps changing](output/exec/A2_operator_keeps_changing.png)

The consequence is specific and quantitative. Season-matched (Jan–Apr 2026 vs. the same months of 2024–2025), **corridor-level disruption rose from 15.1% to 16.8%**, but **PSA measured on its own was essentially flat (17.1% → 17.7%)**. The corridor worsened chiefly because its operator mix shifted toward PSA — its least-reliable operator — not because any single operator's own performance collapsed. This distinction matters for attribution: a corridor-level trend line can move purely on mix, and reading it as a performance change for a fixed operator would be a mistake. In parallel, corridor knock-on (cascade) delays rose +39% season-matched, consistent with the cascade-driven character of the PSA cell.

A caveat applies to the finer 2026 weather cuts: the adverse-weather PSA sample in the four-month 2026 window is on the order of tens of flights, so weather-stratified 2026 figures for this corridor are directional, not precise. The 2026 window is also winter-heavy; season-matching mitigates but does not eliminate that bias.

### 9.4 What the corridor shows

The lived passenger experience on DFW–LFT — "it used to be tolerable, now it isn't" — decomposes into two measurable components: the schedule is acutely weather-sensitive across all operators, and *who flies it has changed underneath the traveler*, settling on PSA, the operator with the highest absolute disruption rate in every weather bucket and a top-4% network fragility cell. None of this is an allegation about any carrier; it is an association visible entirely from public records, and the structural questions it raises — equipment routing, turn buffers, and PSA-vs-Envoy assignment on matched routes — belong to American as the brand and schedule owner. The corridor is valuable precisely because it is *not* unusual: it is one instance of the nationwide pattern detailed in Section 9 (network-wide findings) and Section 11 (the 2026 carve-out).

## 10. Findings: 2026 Carve-out

The 2026 carve-out tests whether the network-wide and corridor-level patterns documented in Sections 9 and 10 (above) persist into the most recent data. As of the June 2026 compile date, BTS had published On-Time Performance for January through April 2026 only. To avoid contaminating the committed main-study artifacts, this carve-out was run as a separate split (`baseline = 2024–25`, `recent = 2026`) writing to distinct `*_2026` curated paths. Because a four-month window is winter-heavy and not comparable to a full calendar year, **every 2026 figure here is season-matched**: 2026 (Jan–Apr) is compared only against the same January–April months of 2024 and 2025. This removes the seasonal-weather bias that would otherwise inflate 2026 against an all-year baseline. The caveat in Section 12 still applies: four months is a partial sample, and cell-level weather-stratified counts fall to tens of flights and are treated as directional rather than precise.

![Is 2026 any better? No](output/exec/A3_is_2026_better.png)

### Network-wide operator trends (season-matched)

The operator ordering established over 2024–25 held, and on several measures deteriorated. PSA remained the worst-performing operator class and worsened on both headline metrics; Envoy remained the cleanest and was essentially flat.

| Operator (season-matched Jan–Apr) | Cancellation 2024–25 → 2026 | Severe-delay 2024–25 → 2026 |
|---|---|---|
| **PSA_operated** | 4.2% → **6.3%** | 9.5% → **11.2%** |
| **Envoy_operated** | 2.4% → 2.7% | 6.3% → 6.6% |
| **AA_mainline** | 1.5% → **3.4%** | (delay rate held) |

Two points deserve emphasis. First, the divergence between the two wholly-owned regional subsidiaries — PSA worsening, Envoy stable and benign — is the same fairness-preserving split seen in the main study, now reproduced in an independent time window. Second, AA mainline cancellations **more than doubled** (1.5% → 3.4%) while its severe-delay rate held roughly constant. A doubling of the cancellation rate with a flat delay rate is consistent with a shift in disruption-handling posture (cancelling earlier rather than running deeply late) rather than a broad operational collapse; the available public data cannot distinguish the mechanism, so this is reported as an observation, not an explanation.

### Hub trends (season-matched)

The hub ranking was equally persistent. The two worst severe-delay hubs in the main study not only stayed worst but climbed, while the cleanest high-volume hubs stayed clean.

| Hub | Severe-delay 2024–25 → 2026 |
|---|---|
| **ORD** (Chicago O'Hare) | 9.3% → **11.6%** |
| **DCA** (Washington National) | 9.1% → **10.5%** |
| LAX / PHX | ~5.5–5.9% (cleanest, stable) |

ORD and DCA — the same two hubs that anchor the top-20 hotspot concentration (Section 9) — are the top two on this metric and both rising. LAX and PHX, the largest new hubs by traffic, remained the cleanest, reaffirming that volume is not fragility into 2026.

### The DFW–LFT corridor: a mix-shift, not a single-operator decline

The focal corridor requires careful reading, because the corridor-level number and the operator-level number tell different stories, and conflating them would misstate the finding.

| DFW–LFT (season-matched Jan–Apr) | Disruption rate 2024–25 → 2026 |
|---|---|
| **Corridor (all operators)** | 15.1% → **16.8%** |
| **PSA only** | 17.1% → **17.7%** |

PSA's own performance on the corridor was nearly flat (17.1% → 17.7%). The corridor-wide deterioration to 16.8% is driven **chiefly by a change in who flies the route**, not by any single operator degrading. The corridor shifted from roughly 42% PSA operation toward approximately 89% PSA — Envoy, historically a major operator here, all but exited by late 2025 (the 2026 monthly counts in the focal report show Envoy at 10, 32, 14, then 0 flights Jan–Apr). Because more of the corridor's flights now sit with its least-reliable operator, the blended corridor rate rises even though that operator barely moved. This is a compositional effect, and we label it as such. Separately, corridor-wide knock-on (late-arriving-aircraft) cascade delay rose approximately **39%** season-matched, and PSA's bad-weather cancellations roughly doubled (≈11% → ≈24%) — but the latter rests on only ~51 adverse-weather PSA flights in the 2026 window and is explicitly directional.

### Reading the carve-out

Season-matched, 2026 shows **no improvement**. The network-level signal — PSA worst and worsening, Envoy stable, ORD and DCA climbing, the clean hubs staying clean — is well-sampled and reproduces the main study in fresh data. The corridor-level signal is real but compositional: DFW–LFT got worse for the traveler primarily because the route consolidated onto its weakest operator. The four-month, winter-weighted nature of the window means the network aggregates carry far more weight than any weather-stratified cell figure, and none of the carve-out's small-sample numbers are presented as precise.

## 11. Structural & Strategic Weaknesses

This is the section a skeptical reader should read first. Every finding in this report carries a known weakness; the credibility of the work rests on naming each one before anyone else does, stating its likely direction of bias, and showing what bounds or mitigates it. We distinguish *structural* weaknesses (inherent to public-data observation) from *strategic* ones (consequences of design choices we made). None of them, individually or together, overturns the headline associations — but several constrain how far those associations can be pushed, and we say so explicitly.

### 11.1 Association, not causation

The single most important limitation. The study observes outcomes (cancellations, severe delays, cascade delays) in public records; it has no access to crew rosters, maintenance basing, fleet assignment, schedule-buffer design, or station staffing. We can show that PSA-operated cells are over-represented in the worst tail (51.8% of the worst-5% cells against 12.2% of ranked flights, a 4.25× lift) and that the DFW–LFT PSA cell sits in the worst ~4% (rank #63 of 1,668). We cannot show *why*. The signal is at least as consistent with schedule and network structure — turn times, bank architecture, equipment routing, thin-spoke exposure, all of which American designs for its Eagle subsidiaries — as with execution by any operator's crews. **Mitigation:** the report's claims are scoped to associations throughout, and the dominant components in the highest-scoring cells are cascade and economic burden, not weather sensitivity, which is itself informative about mechanism without asserting cause. No causal language should survive into any external communication.

### 11.2 Reliance on self-reported BTS cause codes

The controllable (carrier-attributed) and cascade (late-arriving-aircraft) components depend entirely on carriers' own BTS delay-cause coding. Carriers have discretion and an incentive structure in how minutes are allocated across the five cause buckets. An earlier focal-corridor finding (AAR Iteration 2) is directly relevant: AA regional attributed 81.8% of its cancellations to weather versus 55.8% for peers — a gap that could reflect either genuine weather exposure or a reporting tendency. **Direction:** unknown and possibly self-serving; a carrier that under-codes "carrier" minutes would look artificially clean on the controllable component. **Mitigation:** cascade attribution (late-arriving aircraft) is harder to game than carrier-versus-weather splits, and the highest-scoring cells are cascade-driven; we report cause-derived components alongside cause-agnostic ones (cancellation rate, raw severe-delay rate) so a reader can weight the self-reported components down without losing the finding.

### 11.3 The 14.7% operator-ambiguity exclusion

SkyWest and Republic fly for multiple mainline brands, so 904,924 flights (14.7% of 6,152,599) cannot be attributed to an operator class from route context alone and are **excluded** from operator comparisons rather than guessed. This is conservative but consequential: the excluded set contains 12 of the worst-83 cells, including the network's rank-1 hotspot, ORD–SPI (SkyWest_unresolved, base score 0.982). The operator over-representation table is therefore computed on resolved data only. **Direction:** the exclusion removes cells from *both* numerator and denominator of every operator's share, so its net effect on the PSA lift is indeterminate but bounded by the 14.7% mass. **Mitigation:** the refusal to guess is itself a defensibility asset; a FlightAware AeroAPI key (~$100/month minimum spend) would resolve the ambiguity and name ORD–SPI, but the established direction of the finding does not depend on it.

### 11.4 Hub-attribution origin-priority (totals not cross-comparable)

When both endpoints of a flight are hubs, the flight is assigned to its origin hub. A consequence: DFW and ORD totals in the 9-hub run are slightly *lower* than in the 4-hub run despite more total flights. **Impact:** hub-level *totals* are not comparable across run modes; **cell-level rankings are unaffected**, because a (hub, spoke, operator) cell is defined identically regardless of run mode. Any statement comparing absolute hub volumes between the 4-hub and 9-hub runs is invalid; statements about cell rankings and within-run hub concentration are not.

### 11.5 Economic-burden baseline pooling

The economic-burden component uses an `aa_system_average` baseline that pools all resolved operators within a (hub, weather, period) cell, rather than leave-one-out. A high-volume operator with above-average fragility partially contributes to its own baseline, which **suppresses** its measured excess. **Direction:** conservative *against* the headline — it understates, not overstates, a dominant operator's burden signal. A leave-one-out baseline would widen the PSA gap, not close it. We accept the conservative version deliberately.

### 11.6 Endpoint versus en-route weather

Weather is assigned at the departure airport at departure hour and the arrival airport at arrival hour (worst of the two), with 100.0% match in the bigrun. En-route conditions — turbulence, fronts crossed in flight — are not captured. **Mitigation:** the network is short-haul spoke-to-hub (typically 1–2.5 hours), where endpoint conditions dominate the cancellation and dispatch decision; the simplification is most defensible exactly where the fragility concentrates. **Residual risk:** longer segments among the 264 airports are less well served by this assumption, and the weather-sensitivity component should be read as endpoint-weather sensitivity, not total-weather sensitivity.

### 11.7 Composite-weight subjectivity and the absolute-versus-multiplier trap

The composite hotspot score is six equal-weighted, percentile-normalized components. Equal weighting is a defensible default but a subjective one. **Mitigation:** three alternate weighting scenarios plus a robustness score test stability; the rank-1 cell holds robustness 1.00, and no top-20 cell is the artifact of a single weighting. Separately, this study has one hard-won interpretive lesson — the **A1 trap**. On DFW–LFT, Envoy is the *most weather-sensitive* operator by multiplier (7%→30%, ×4.3) yet PSA is *worst in absolute terms in every weather bucket* (16%→40%, ×2.5). A multiplier and an absolute level are different facts; conflating them previously produced a misleading exec chart that was corrected. We state both wherever weather sensitivity appears and never substitute one for the other.

### 11.8 Ranking noise, multiple comparisons, and small cells

Scoring 2,093 cells and reporting the extreme tail invites winner's-curse and multiple-comparison concerns: some cells rank high by chance. **Mitigations:** a 100-flight minimum for ranking (1,668 cells qualify); a separate 30-adverse-flight floor below which the weather-sensitivity component is dropped and the score renormalized on the remaining five (correcting a prior small-sample upward bias); a 30-flight reliability floor flagging 30 cells as "indicative only"; and persistence and robustness reported as signals distinct from rank. The low expected persistence rate for a top-20 list drawn from 1,000+ cells is disclosed rather than spun as instability.

### 11.9 2026 partiality and winter seasonality

The 2026 carve-out is four months (Jan–Apr), the only BTS-published months as of June 2026, and is winter-heavy. A naive 2026-versus-full-year comparison would be biased by season. **Mitigation:** every 2026 figure is **season-matched** to the same Jan–Apr months of 2024–25 (e.g., ORD severe 9.3%→11.6%, PSA cancel 4.2%→6.3%). Cell-level weather-stratified 2026 samples remain small and are treated as directional; network operator/hub aggregates are well-sampled.

### 11.10 Corridor mix-shift confound

Corridor-level changes can reflect *who flies the route* rather than how any operator performs. DFW–LFT rose 15.1%→16.8% (season-matched) at the corridor level, but PSA-only was roughly flat (17.1%→17.7%); the corridor move is **mainly the mix shift** toward PSA (≈42%→≈90% as Envoy exited), not a single operator deteriorating. **Mitigation:** we report operator-held-constant figures beside corridor aggregates and never attribute a corridor-level change to performance without the operator-level check.

### 11.11 AA-centric hub selection and generalizability

The scope is American's 9 hubs and their discovered spokes. There is no non-AA mainline control group at the new hubs (Module B uses the pooled AA-system baseline precisely because none exists). The findings are therefore *internal* to American's branded network: they identify where fragility concentrates within it, not whether American as a whole is worse than United or Delta. The earlier focal-corridor peer comparison (AA vs. DL/UA) is the only cross-carrier benchmark, and it is thin on the UA side. Generalization beyond American's network is not supported by this design.

## 12. Reproducibility

The study is built entirely on public data (U.S. DOT BTS On-Time Performance and NOAA ASOS hourly weather) and committed code, so a third party can reproduce every reported figure end to end. This section gives the concrete steps. All paths are relative to the `flight-fragility-poc/` working directory unless noted; the Python virtual environment lives one level up at the `tailspin/` repo root, matching the established layout.

### Environment

Python 3.11 or later is required. The bigrun used a DuckDB backend (`backend: duckdb` in `config/study.yaml`) on a 72-core / 503 GB host, completing the full keyless I-V bigrun in approximately 63 minutes of wall clock. The pipeline does not require that hardware; DuckDB scales down, but expect proportionally longer extraction and join times on a smaller machine.

```bash
git clone https://github.com/jumpkey/tailspin.git
cd tailspin/flight-fragility-poc
python3 -m venv ../.venv && source ../.venv/bin/activate
pip install -r requirements.txt
python -c "import pandas, pyarrow, requests, airportsdata, duckdb; print('OK', duckdb.__version__)"
```

Required packages include `pandas`, `numpy`, `pyarrow`, `requests`, `airportsdata`, `duckdb`, and the chart stack (`matplotlib`, `plotly`, `kaleido`). If `kaleido` fails to install on Linux, `matplotlib` is the automatic fallback for PNG rendering; all chart outputs are still produced.

### Configuration files

| File | Purpose |
|---|---|
| `config/study.yaml` | Main-study config: `run_mode`, `backend`, and the `bigrun:` hub list (the 9 AA hubs). |
| `config/study_2026.yaml` | 2026 carve-out config: Jan-Apr 2026 months, season-matched comparison windows. |
| `config/routes.yaml` | Focal-corridor route/airport universe for Fragility I-III. |
| `.env` (from `.env.example`) | Optional `FLIGHTAWARE_API_KEY`. Unset is the published baseline. |

The committed results were produced **without** a FlightAware key, which is why the 904,924 operator-ambiguity flights (14.7%) remain unresolved and conservatively excluded from operator comparisons. Supplying `FLIGHTAWARE_API_KEY` activates `scripts/15_resolve_operator_ambiguity.py`, which would reduce that residual and shift operator-class counts; without it the script no-ops safely.

### Run scripts

The four phase scripts can be run individually, or chained by the two batch drivers:

| Script | Produces |
|---|---|
| `scripts/run_pipeline.sh` | Fragility I-III; required once to emit `data/curated/flight_operability_fact.csv`. |
| `scripts/run_pipeline_iv.sh` | Fragility IV; cell-level fragility scores and the curated `hubspoke_operator_fact/` Parquet layer. |
| `scripts/run_pipeline_v.sh` | Fragility V; hotspot rankings (reads IV's Parquet; under 5 minutes). |
| `scripts/run_bigrun.sh` | One-shot driver chaining I-III -> IV (bigrun) -> V, gated on each phase's output. |
| `scripts/run_2026_carveout.sh` | Extraction + fact build only for Jan-Apr 2026, writing dedicated `*_2026` facts so committed 2024-25 outputs are untouched. |

`run_bigrun.sh` is designed to be launched detached and tailed:

```bash
nohup bash scripts/run_bigrun.sh >/dev/null 2>&1 &
tail -f logs/bigrun.latest.log
```

It hard-stops with a timestamped `FAILED` banner if any phase errors or a required artifact is missing, so it never runs a later phase on bad input.

### Idempotent caching and data restoration

Caching is at the **raw-file level**. Each extraction script skips the download if the monthly BTS PREZIP or NOAA ASOS file already exists, and re-downloads only what is missing; `--force` re-fetches everything. The raw monthly CSVs (~1-2 GB) and the curated Parquet layer are gitignored and absent on a fresh clone, but the committed `data/raw/*/manifest.csv` files record exactly which files the published run used.

Two restore paths:

1. **Re-download (default):** run the pipeline on a fresh clone; extraction scripts pull the BTS and NOAA files automatically. NOAA is rate-limited, so expect 429/503 responses handled by retry-with-backoff; on a cold cache budget extra wall-clock for those delays.
2. **Restore the archive:** if the raw datasets were archived, unzip them back into `data/raw/` (and `data/curated/` if the Parquet layer was archived) before running. With a warm cache the extraction steps skip straight to the joins and the run is far faster.

The published bigrun achieved 100.0% weather match (0.0% null) across 6,152,599 flights; a reproduction reporting a materially lower match rate indicates incomplete NOAA fetches (check for near-empty ASOS CSVs and re-run with `--force`).

### Verification and charts

After a run, verify against the committed result files in `output/` (Fragility IV `top_cell`, the Fragility V hotspot rankings, and the hub/operator rollups). Executive figures are regenerated by the exec-chart module, which renders the storyline charts (A1-A3, B1-B2) directly from the curated facts via the same `kaleido`/`matplotlib` path. Numbers that diverge from the canonical figures usually trace to upstream BTS revisions, a set `FLIGHTAWARE_API_KEY`, or a changed `run_mode`/hub list in `config/study.yaml`.

## 13. Future Work

The findings in this report rest on resolved public data with several
deliberately conservative exclusions. The following extensions would tighten the
analysis, broaden its reach, or — in one case — convert association into
something closer to causal inference. They are ordered roughly by cost-to-value.

**1. Resolve the 14.7% operator-ambiguity via FlightAware AeroAPI.** The largest
single methodological gap is the 904,924 flights (14.7% of 6,152,599) flown by
SkyWest and Republic for multiple mainline brands, which route context alone
cannot attribute and which are currently excluded — including 12 of the worst-83
cells and, notably, **the rank-1 network hotspot ORD–SPI** (currently labeled
`SkyWest_unresolved`, base score 0.982, robustness 1.00). AeroAPI's Standard
tier (a $100/month minimum-spend floor, with the actual run consuming ~200
capped queries / ~$4 of usage) would let the pipeline resolve these to specific
mainline contracts. This would not overturn the headline — PSA over-representation
is already established on resolved data — but it would *complete* it by naming the
operator on otherwise-unresolved top cells. The trade-off is candid: it exchanges
some of the "we refused to guess" defensibility for completeness, so it is
recommended only when a specific external communication needs to name the
operator on a top cell.

**2. Produce a network-wide economic-burden total.** The economic-burden
component is currently a per-cell proxy against a pooled `aa_system_average`
baseline. Aggregating it into a defensible dollar figure across all 1,668 ranked
cells — with passenger-volume weighting and disclosed assumptions — would give
the burden component a standalone interpretation rather than only a normalized
score contribution. The pooled (not leave-one-out) baseline should be revisited
here, since it conservatively suppresses a high-volume operator's own excess.

**3. Widen coverage.** The study is scoped to American's 9 hubs and 264 airports.
Extending the same engine to additional corridors below the 100-flight ranking
threshold, to other mainline carriers (United, Delta) and their regional
subsidiaries would test whether the PSA-style concentration is American-specific
or a general property of wholly-owned-regional schedule architecture.

**4. Causal inference, conditional on internal data.** The central limitation is
association, not causation: with only public BTS cause-codes and endpoint weather,
we cannot separate schedule/network structure from execution. If operational data
became available (actual turn times, crew/equipment routing, maintenance events),
methods such as matched comparisons across operators flying the same
hub-spoke-equipment under the same weather, or difference-in-differences around
schedule changes, could begin to attribute fragility to specific levers.

**5. Ongoing monitoring as 2026+ months publish.** The 2026 carve-out is a
four-month, winter-heavy partial sample (mitigated by season-matching). As BTS
publishes May 2026 onward, the season-matched series should be extended to confirm
whether the observed trends persist — e.g., PSA worsening (cancel 4.2%→6.3%,
severe 9.5%→11.2%) and ORD/DCA climbing (severe 9.3%→11.6% and 9.1%→10.5%).

**6. Composite-weight sensitivity analysis.** The composite uses 6
equal-weighted components, a subjective choice already stress-tested with 3
alternate weighting scenarios and a robustness score. A fuller sweep — randomized
weight perturbation, per-component leave-one-out, and rank-stability bands — would
quantify exactly how much each finding depends on the weighting choice rather than
the underlying signal.

## 14. Appendices

### Appendix A — Data Dictionary (curated fact-table columns)

The Fragility V cell-level table is the analytic core. Each row is one `(hub_family, spoke_airport, operator_class)` cell aggregated over the main study window (Jan 2024–Dec 2025). Key columns:

| Column | Meaning |
|---|---|
| `hub_family` | One of the 9 AA hubs (origin-priority attribution; see §5). |
| `spoke_airport` | The non-hub endpoint of the market. |
| `operator_class` | Attributed operator: `AA_mainline`, `Envoy_operated`, `PSA_operated`, `SkyWest_unresolved`, `Republic_unresolved`, or `Other_or_non_AA`. |
| `flights_total` | All scheduled flights in the cell — the single shared denominator for every composite component (AAR Iteration 9 standardization). |
| `operated_count` / `cancelled_count` | Flights operated vs. cancelled. |
| `severe_delay_count` | Arrivals 60+ min late (DOT standard). |
| `controllable_severe_delay_count` | Subset of severe delays attributed to carrier-controllable BTS cause codes. |
| `late_arriving_severe_delay_count` / `cascade_delay_count` | Severe delays propagated from a late inbound aircraft (cascade). |
| `carrier_delay_min_sum`, `late_aircraft_delay_min_sum` | Summed BTS delay minutes feeding the economic-burden proxy. |
| `cancellation_rate`, `severe_delay_rate`, `controllable_severe_delay_rate`, `late_arriving_severe_delay_rate` | Counts ÷ `flights_total`. |
| `adv_flights`, `adverse_weather_fragility_rate` | Flights in adverse weather hours and their cancelled-or-delayed share (weather assigned at endpoint airport-hours, not en route). |
| `economic_burden_per_1k` | Absolute-cost proxy per 1,000 flights, pooled `aa_system_average` baseline (conservative; not leave-one-out). |
| `norm_*` (6 columns) | Percentile-rank normalizations of the six components; `norm_weather_sensitivity` is `NaN` when below the adverse-flight gate. |
| `hotspot_score_base` + 3 scenario scores | Equal-weighted composite and 3 alternate weightings. |
| `hotspot_robustness_score` | Fraction of scenarios in which the cell remains top-N. |
| `meets_min_flights`, `meets_min_adv_flights`, `is_persistent` | Eligibility and stability flags. |

### Appendix B — Fragility V Top-20 Hotspot Cells

Reproduced from `output/fragility_v_hotspot_rankings.csv` (1,668 of 2,093 cells meet the 100-flight ranking threshold). Robustness = share of weighting scenarios in which the cell is top-N; Persistent = top-N in both baseline and recent sub-periods.

| Rank | Hub | Spoke | Operator | Base Score | Robustness | Persistent |
|---|---|---|---|---|---|---|
| 1 | ORD | SPI | SkyWest_unresolved | 0.9823 | 1.00 | No |
| 2 | ORD | ORF | PSA_operated | 0.9797 | 1.00 | No |
| 3 | ORD | CAK | PSA_operated | 0.9754 | 1.00 | No |
| 4 | ORD | TYS | PSA_operated | 0.9746 | 1.00 | No |
| 5 | ORD | GSP | PSA_operated | 0.9699 | 1.00 | No |
| 6 | ORD | MGW | SkyWest_unresolved | 0.9689 | 1.00 | No |
| 7 | DFW | SBN | PSA_operated | 0.9588 | 1.00 | No |
| 8 | ORD | CID | AA_mainline | 0.9562 | 1.00 | No |
| 9 | DFW | CID | AA_mainline | 0.9549 | 1.00 | Yes |
| 10 | CLT | GPT | Envoy_operated | 0.9517 | 1.00 | No |
| 11 | MIA | MKE | AA_mainline | 0.9429 | 1.00 | No |
| 12 | DFW | ICT | AA_mainline | 0.9425 | 1.00 | No |
| 13 | DCA | LAN | PSA_operated | 0.9385 | 1.00 | No |
| 14 | DFW | CRP | PSA_operated | 0.9377 | 1.00 | No |
| 15 | ORD | TVC | SkyWest_unresolved | 0.9352 | 0.75 | No |
| 16 | DFW | CVG | PSA_operated | 0.9300 | 0.75 | No |
| 17 | DCA | CVG | PSA_operated | 0.9255 | 0.50 | No |
| 18 | DFW | GNV | PSA_operated | 0.9238 | 0.50 | No |
| 19 | DFW | LBB | AA_mainline | 0.9216 | 0.50 | No |
| 20 | DFW | LIT | AA_mainline | 0.9191 | 0.50 | No |

Only ORD-CID (rank 9, AA_mainline) is flagged persistent; ranks 1–14 carry full robustness (1.00), ranks 15–20 degrade. Per the §7 caveat, robustness and persistence are stronger prioritization signals than base rank alone (winner's-curse risk in a 20-from-1,668 list).

### Appendix C — QA Summary

From `output/qa_summary_hubspoke.csv`. Total flights: **6,152,599**. Weather-match null rate: **0.0%** (100.0% match).

**Operator-class counts**

| Operator class | Flights | Share |
|---|---|---|
| Other_or_non_AA | 2,258,693 | 36.7% |
| AA_mainline | 1,943,962 | 31.6% |
| SkyWest_unresolved | 606,125 | 9.9% |
| Envoy_operated | 568,329 | 9.2% |
| PSA_operated | 476,691 | 7.7% |
| Republic_unresolved | 298,799 | 4.9% |

Unresolved ambiguity (SkyWest + Republic) totals **904,924 flights (14.7%)**, excluded from operator comparisons rather than guessed (§5).

**Hub-family flight counts** (origin-priority; not cross-run-mode comparable)

| Hub | Flights |
|---|---|
| DFW | 1,186,156 |
| ORD | 1,131,482 |
| CLT | 770,451 |
| PHX | 722,022 |
| LAX | 686,522 |
| DCA | 518,567 |
| JFK | 400,577 |
| MIA | 382,727 |
| PHL | 354,095 |

### Appendix D — Glossary

- **Fragility** — Susceptibility of a market-operator cell to cancellation/severe-delay disruption, expressed as a composite of six normalized components. Association, not causation.
- **Severe delay** — Arrival 60+ minutes late (DOT standard). The shared composite denominator is all scheduled flights.
- **Controllable delay** — Severe delay attributed to carrier-controllable BTS cause codes (self-reported).
- **Cascade (late-arriving) delay** — Severe delay propagated from a late inbound aircraft; a strict subset of severe delay.
- **Weather sensitivity** — Ratio of fragility in adverse vs. good weather hours (a multiplier), distinct from the absolute adverse-weather rate.
- **Economic burden** — Absolute-cost proxy from pooled DOT block-cost benchmarks; conservative (not peer-relative).
- **Hotspot cell** — A `(hub, spoke, operator_class)` unit scored by the composite index.
- **Composite hotspot score** — Six equal-weighted percentile-rank components; tested against 3 alternate weightings.
- **Robustness score** — Fraction of weighting scenarios in which a cell stays top-N (1.00 = stable across all).
- **Persistence** — Cell ranks top-N independently in both the baseline and recent sub-periods.
- **Season-matched** — Comparing 2026 Jan–Apr only against the same Jan–Apr months of 2024–25, controlling for winter-heavy seasonality in the partial-year sample.
- **Over-representation multiplier** — An operator's share of worst cells ÷ its share of flights (1.0 = neutral).
- **Unresolved operator** — SkyWest/Republic codeshare rows whose operating carrier could not be disambiguated from public data; scored at cell level but excluded from operator rollups.

