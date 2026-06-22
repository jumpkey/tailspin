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
