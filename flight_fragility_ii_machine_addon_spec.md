# Flight Fragility II: The Machine — Add-on Spec for Controllable-Factor Schedule Fragility

This document is a standalone add-on specification for a second study to be implemented alongside the existing Flight Fragility study. It assumes the first study already exists in the repository and should be treated as the base pipeline and project structure.[cite:25][cite:70][cite:135]

The purpose of this add-on is to determine whether **controllable** operational factors — especially blended crew or mechanical issues as represented in public cause data — appear to exacerbate schedule collapse more on American’s regional-style spoke network than on comparable peer markets.[cite:153][cite:156][cite:169]

This study does **not** attempt to prove causality. It does not try to separate maintenance from crew with certainty, nor does it attempt to model internal airline decision-making. It studies only the observable effects of blended controllable issues using public flight-performance and delay-cause data.[cite:156][cite:153]

An ATC-focused fragility study is explicitly out of scope for this phase because systemwide ATC and NAS disruptions are less actionable from the perspective of airline operational design, and because the present question is whether airline-controlled fragility is worse on American than peers.[cite:169][cite:156]

## Objective

Build a second reproducible analysis that answers: **Does AA regional service in LFT and nearby small-spoke markets show a larger increase in controllable delays, controllable cancellations, and delay cascades than comparable peer markets, especially when the schedule is stressed?**[cite:153][cite:156][cite:169]

This add-on should produce one additional output graphic and any supporting written result needed by the existing project workflow.[cite:156][cite:153]

## Study framing

The first fragility study tested whether weather sensitivity appeared abnormal in American’s regional-like spoke markets relative to peers.[cite:70][cite:135]

This second study extends that architecture to test whether **controllable schedule fragility** appears abnormal — specifically, whether airline-controlled disruptions and their cascades seem to amplify schedule collapse more in the AA regional basket than in peer spoke baskets.[cite:153][cite:156][cite:169]

The key analytic distinction is:

- **Causality is not observable.** Public data cannot prove whether a disruption came from maintenance, crew quality, crew availability, aircraft routing fragility, or another internal controllable issue.[cite:156]
- **Effects are observable.** BTS and related DOT/FAA materials do let the study observe airline-controlled cause categories and downstream cascade behavior such as late-arriving aircraft delays.[cite:156][cite:169]

Accordingly, the outcome should be framed as a study of **controllable operational fragility**, not a proof of “mechanical-only” or “crew-only” causation.[cite:156][cite:153]

## Source data

### BTS / DOT on-time performance and cause data

BTS remains the primary system-of-record source for flight outcomes and cause categories. Airlines report delay and cancellation causes to BTS in broad categories including Air Carrier, Extreme Weather, National Aviation System, Security, and Late-arriving Aircraft.[cite:156][cite:167][cite:27]

Relevant references:

- BTS database overview: [https://transtats.bts.gov/DatabaseInfo.asp?QO_VQ=EFD&DB_URL=](https://transtats.bts.gov/DatabaseInfo.asp?QO_VQ=EFD&DB_URL=) [cite:25]
- BTS delay-cause explainer: [https://www.bts.gov/topics/airlines-and-airports/understanding-reporting-causes-flight-delays-and-cancellations](https://www.bts.gov/topics/airlines-and-airports/understanding-reporting-causes-flight-delays-and-cancellations) [cite:156]
- BTS topic page on on-time performance and causes: [https://www.bts.gov/explore-topics-and-geography/topics/airline-time-performance-and-causes-flight-delays](https://www.bts.gov/explore-topics-and-geography/topics/airline-time-performance-and-causes-flight-delays) [cite:167]
- BTS workbook / field reference: [https://catsr.vse.gmu.edu/SYST660/BTSAirlineOnTimePerformanceData_Workbook.pdf](https://catsr.vse.gmu.edu/SYST660/BTSAirlineOnTimePerformanceData_Workbook.pdf) [cite:17]

The most important BTS fact for this study is that **Air Carrier** includes circumstances within the airline’s control such as maintenance or crew problems, while **Late-arriving aircraft** reflects propagated downstream delay from earlier operational disruption.[cite:156][cite:167]

### DOT controllable-delay framing

DOT’s Airline Cancellation and Delay Dashboard defines a controllable flight cancellation or delay as one essentially caused by the airline, with examples including maintenance or crew problems.[cite:153]

This is important because it justifies the use of Air Carrier as the public proxy for blended internal operational issues even though the data do not isolate maintenance from crew.[cite:153][cite:156]

Relevant reference:

- DOT controllable dashboard: [https://www.transportation.gov/airconsumer/airline-cancellation-delay-dashboard](https://www.transportation.gov/airconsumer/airline-cancellation-delay-dashboard) [cite:153]

### FAA / ASPM delay-cause framing

FAA ASPM definitions can help interpret delay categories. ASPM identifies carrier delay as within airline control and explicitly lists maintenance, crew legality, late crew, engineering inspection, fueling, aircraft damage, and similar items as examples. ASPM also defines NAS delay and late-arrival delay distinctly, which is useful for the cascade interpretation in this study.[cite:169]

Relevant reference:

- FAA ASPM delay types: [https://aspm.faa.gov/aspmhelp/index/Types_of_Delay.html](https://aspm.faa.gov/aspmhelp/index/Types_of_Delay.html) [cite:169]

### Reuse of the weather-study data

This study should reuse the flight-level fact table, route baskets, study windows, and weather-bucket framework from the first fragility study wherever possible.[cite:70][cite:135][cite:25]

That reuse is desirable because the machine/controllable study should be able to answer both:

1. Whether controllable fragility is elevated in general.
2. Whether controllable fragility becomes even more pronounced under marginal or adverse weather stress.[cite:156][cite:135]

## Conceptual model

This study treats schedule collapse as a combination of:

- **Primary controllable disruptions** — delays or cancellations directly coded as Air Carrier.[cite:156][cite:153]
- **Downstream cascades** — late-arriving aircraft delays that represent knock-on effects from earlier disruptions and fragile rotations.[cite:156][cite:169]
- **Stress interaction** — the possibility that weather or moderate system stress reveals a more fragile internal operating structure, causing controllable and late-arriving impacts to rise more sharply than in peer systems.[cite:156][cite:135][cite:79]

The study should therefore focus not on a pure “mechanical count,” which public data do not expose, but on whether **controllable plus cascade effects** appear disproportionately large in American’s regional basket relative to peer baskets.[cite:156][cite:153]

## Main hypotheses

### Primary hypothesis

AA regional spoke markets show a higher incidence of **controllable schedule fragility** than peer spoke markets, as measured by Air Carrier cancellations, Air Carrier severe delays, and Late-arriving severe delays.[cite:156][cite:153][cite:169]

### Secondary hypothesis

AA regional spoke markets show a larger increase in controllable and cascade disruption under marginal or adverse weather than peer spoke markets, suggesting that internal fragility is more exposed when the schedule is stressed.[cite:156][cite:135][cite:79]

### Non-hypothesis / explicit limitation

This study does **not** test whether maintenance alone, or crew alone, is the true cause of the disruptions. It only tests whether the observable public categories associated with airline-controlled fragility are elevated relative to peers.[cite:156][cite:153]

## Scope

### Primary route anchor

- LFT–DFW remains the narrative anchor market.[cite:25]

### AA regional basket

This add-on should reuse the basket design from the first study unless the implemented repo has already adjusted it. Candidate basket members may include:

- LFT–DFW
- BTR–DFW
- AEX–DFW
- MLU–DFW
- GPT–DFW
- SHV–DFW[cite:25]

### Peer baskets

Reuse the same peer corridor shape from the first study unless the implemented repo has an improved peer definition:

- UA small-spoke routes into IAH
- DL small-spoke routes into ATL[cite:25]

### Time window

Reuse the first study’s baseline/recent windows and route-inclusion criteria so findings are directly comparable across Fragility I and Fragility II.[cite:25][cite:5]

## Data reuse and extension strategy

This study should be implemented as an extension of the existing project, not as a new standalone pipeline.[cite:25][cite:70]

Preferred approach:

- Reuse the existing BTS ETL and curated fact table from Fragility I if those outputs already contain the necessary fields.[cite:25][cite:17]
- Extend the fact-building step only as needed to add the delay-cause and controllable/cascade fields defined below.[cite:156][cite:169]
- Reuse the weather-bucket assignment from Fragility I so this study can compare benign, marginal, and adverse weather regimes without rebuilding that logic independently.[cite:135][cite:70]

## Additional required fields

If not already present in the curated fact table, add the following fields.

### BTS cause fields

- `carrier_delay_minutes`
- `weather_delay_minutes`
- `nas_delay_minutes`
- `security_delay_minutes`
- `late_aircraft_delay_minutes`
- `cancellation_code_bts`[cite:156][cite:17]

### Derived classification fields

- `primary_delay_cause`
- `controllable_delay_flag`
- `controllable_cancel_flag`
- `late_arriving_flag`
- `cascade_delay_flag`
- `fragility_ii_market_bucket`
- `weather_bucket` (reused from Fragility I)
- `period_flag` (reused from Fragility I)[cite:156][cite:135]

### Definitions

- `primary_delay_cause`: the cause with the largest reported delay-minute contribution among carrier, weather, NAS, security, and late-arriving categories for a delayed operated flight.[cite:156][cite:169]
- `controllable_delay_flag`: 1 if `primary_delay_cause == Air Carrier`, else 0.[cite:153][cite:156]
- `controllable_cancel_flag`: 1 if `Cancelled == 1` and `cancellation_code_bts` indicates Air Carrier, else 0.[cite:156]
- `late_arriving_flag`: 1 if `primary_delay_cause == Late-arriving aircraft`, else 0.[cite:156][cite:169]
- `cascade_delay_flag`: same as `late_arriving_flag` for phase 1 of this add-on, unless the repo later implements a more advanced cascade allocation model.[cite:156]

### Field population and null-handling rules

BTS only populates the five cause-minute fields for flights that both operated and arrived 15 or more minutes late; on-time, early, and cancelled flights report all five fields as null, not zero.[cite:156][cite:17] Implementations must not default missing cause-minute fields to zero before selecting the largest value, because doing so manufactures a spurious "Air Carrier" attribution (the first column in most natural orderings) for every on-time and cancelled flight, which would silently overstate `controllable_delay_count` across the entire study.

The required rule is: `primary_delay_cause` is computed only for rows where at least one of the five cause-minute fields is non-null and their sum is greater than zero. All other rows — on-time/early operated flights below the 15-minute reporting threshold, and all cancelled flights — must receive `primary_delay_cause = null` and `controllable_delay_flag = 0` / `late_arriving_flag = 0` by definition, not by an arithmetic coincidence of filling with zero. `controllable_cancel_flag` is derived independently from `cancellation_code_bts` and is unaffected by this rule, since BTS never reports cause-minute breakdowns for cancellations.

## Fragility II metrics

This study should compute a new set of aggregated metrics, parallel to the first study but focused on controllable and cascade effects.[cite:156][cite:25]

For each `market_bucket × weather_bucket × period_flag`, compute:

- `flights_total`
- `cancelled_count`
- `operated_count`
- `controllable_cancel_count`
- `controllable_delay_count`
- `late_arriving_delay_count`
- `controllable_severe_delay_count`
- `late_arriving_severe_delay_count`
- `controllable_cancel_rate = controllable_cancel_count / flights_total`
- `controllable_delay_rate = controllable_delay_count / operated_count`
- `controllable_severe_delay_rate = controllable_severe_delay_count / operated_count`
- `late_arriving_severe_delay_rate = late_arriving_severe_delay_count / operated_count`[cite:156][cite:153]

Recommended severe-delay definition:

- `ArrDelay >= 60` or `DepDelay >= 60`, consistent with the first study’s severe-delay threshold unless the implemented repo already standardized differently.[cite:25]

### Optional advanced metrics

If the existing implementation already has a strong fact table and enough observations, optionally compute:

- `air_carrier_delay_minutes_share`
- `late_arriving_delay_minutes_share`
- `controllable_fragility_index = AA_regional controllable severe-delay rate / peer weighted controllable severe-delay rate`
- `cascade_fragility_index = AA_regional late-arriving severe-delay rate / peer weighted late-arriving severe-delay rate`[cite:156][cite:169]

## Statistical robustness and sample-size handling

Fragility II subsets the flight population twice relative to Fragility I: first to operated flights, then to the smaller subset with a reported cause-minute breakdown (delayed >= 15 minutes). The first study's own results already show some `market_bucket × weather_bucket × period_flag` cells with very small populations — for example, the UA peer basket's adverse-weather/baseline cell contains 32 total flights. Cause-attributed subsets of cells this size will be smaller still, and any rate computed from a low count is unstable and can produce a misleadingly large or small ratio purely from sampling noise.

This study must therefore:

- Report the raw flight count (`flights_total` or `operated_count`, as appropriate to the denominator) alongside every rate in both the chart-ready CSV and the written summary, so a reader can judge precision without recomputing it.
- Define a minimum-sample threshold (suggested: 30 operated flights, or the prior study's `min_route_flights` configuration value if the implementer prefers a single shared constant) below which a cell's rate is flagged as low-confidence in the output data and is either suppressed from the chart or rendered with a visibly distinct treatment (e.g., hatched bar, footnote marker) rather than presented at face value next to well-sampled cells.
- Compute a combined-peer-basket sensitivity series (UA and DL pooled, weighted by flight count) alongside the separate UA and DL series, since pooling is the most direct mitigation for the UA basket's known thinness and lets the chart show a stable comparison even where the individual peer baskets cannot support one.
- Treat any single-cell ratio (such as an executive annotation's "Nx peers" figure) as provisional if either the AA cell or the peer cell it is built from falls below the minimum-sample threshold, and say so explicitly in the annotation or its accompanying footnote rather than presenting a precise-looking multiplier built on a handful of flights.

## Chart specification

This study should produce **one additional output graphic** that complements the first study rather than replacing it.[cite:156]

### Graphic objective

The chart should show whether American’s regional basket experiences more **controllable disruption** and more **cascade disruption** than peer baskets, especially under schedule stress.[cite:153][cite:156]

### Recommended chart

Use a **two-panel grouped bar chart**.

#### Panel A

- Y-axis: `controllable_cancel_rate` or `controllable_severe_delay_rate`
- X-axis: `weather_bucket` (`benign`, `marginal`, `adverse`)
- Series:
  - `AA_regional_basket`
  - `UA_peer_basket`
  - `DL_peer_basket`[cite:156][cite:135]

#### Panel B

- Y-axis: `late_arriving_severe_delay_rate`
- X-axis: same `weather_bucket`
- Series: same basket definitions[cite:156][cite:169]

This pairing is recommended because it distinguishes:

- **primary controllable fragility** in Panel A, and
- **schedule-collapse cascade fragility** in Panel B.[cite:156][cite:169]

### Executive annotation

The chart should include one computed annotation using actual values from the run, such as:

- “AA regional controllable severe-delay rate in marginal weather is 1.9x peers.”
- “AA regional late-arriving severe-delay rate rises 2.4x from benign to adverse conditions, versus 1.3x for peers.”

The wording must be generated from computed values and should avoid causal claims the data cannot support.[cite:156][cite:153]

## Written result

This add-on should also produce a short machine-readable or markdown summary result that fits the existing repo’s reporting style.[cite:156]

Minimum output:

- `output/fragility_ii_summary.md`

The summary should state:

1. Whether controllable disruption appears higher, lower, or similar for AA regional vs peers.
2. Whether cascade disruption appears higher, lower, or similar for AA regional vs peers.
3. Whether the signal strengthens in marginal/adverse weather.
4. A brief caveat that public data do not distinguish maintenance from crew within Air Carrier causes.[cite:156][cite:153]
5. The flight-count denominator behind each headline rate, and an explicit note on which `market_bucket × weather_bucket × period_flag` cells fell below the minimum-sample threshold.
6. A reference to the "Risks, threats to validity, and alternative explanations" section so a reader is pointed to the full disclosure rather than only the headline finding.

## Implementation architecture

This add-on should be implemented using the same repo architecture as the first study and should add scripts rather than redesign the project.[cite:25][cite:70]

### Suggested additional scripts

```text
scripts/
  31_analyze_fragility_machine.py
  41_plot_fragility_machine.py
```

If the first study’s analysis script is already modular, these can be implemented as extensions or modes instead of separate files. The important requirement is that Fragility II be rerunnable without disturbing Fragility I outputs.[cite:25]

## ETL and fact-table changes

### BTS extractor

No new external source is required if the existing BTS extraction already pulls the delay-cause fields. If it does not, the existing BTS ETL should be extended to include the cause-minute fields needed for Fragility II.[cite:17][cite:156]

Required BTS delay-cause fields if not already present:

- `CarrierDelay`
- `WeatherDelay`
- `NASDelay`
- `SecurityDelay`
- `LateAircraftDelay`
- `CancellationCode`[cite:156][cite:17]

### FAA weather data

No new FAA source is required for this add-on if the first study already assigns weather buckets at the flight level or route-period level. Fragility II should reuse that output directly.[cite:70][cite:135]

### Flight fact table

The curated flight fact table should be extended rather than duplicated. If the first study already produces `flight_operability_fact.csv`, this add-on should add columns or produce a compatible enriched successor table rather than a parallel incompatible file.[cite:25][cite:70]

## Analysis logic

### Step 1: classify cause

For each operated delayed flight, determine the dominant delay cause by selecting the largest of the BTS cause-minute fields.[cite:156]

Illustrative logic:

```python
cause_cols = {
    "Air Carrier": "carrier_delay_minutes",
    "Weather": "weather_delay_minutes",
    "NAS": "nas_delay_minutes",
    "Security": "security_delay_minutes",
    "Late-arriving": "late_aircraft_delay_minutes",
}
```

Set `primary_delay_cause` to the label with the highest minute value, but only for flights where the raw cause-minute fields are not all null (see "Field population and null-handling rules" above). Flights with no reported cause-minute breakdown — on-time/early operated flights and all cancellations — must keep `primary_delay_cause` unset rather than defaulting to a column via a zero-filled tie-break.[cite:156][cite:169]

### Step 2: classify controllable and cascade flags

- `controllable_delay_flag = 1` if `primary_delay_cause == "Air Carrier"`
- `late_arriving_flag = 1` if `primary_delay_cause == "Late-arriving"`
- `cascade_delay_flag = late_arriving_flag`
- `controllable_cancel_flag = 1` if canceled and `cancellation_code_bts` maps to Air Carrier[cite:156][cite:153]

### Step 3: aggregate by basket, weather bucket, and period

Aggregate the metrics defined above using the same `market_bucket`, `weather_bucket`, and `period_flag` definitions as the first study.[cite:25][cite:135]

### Step 4: compute peer comparisons

Compute weighted or simple peer benchmarks so that the additional graphic can compare AA regional directly with UA/DL peers and optionally with a combined peer baseline.[cite:25]

## Example pseudocode

```python
fact = pd.read_csv("data/curated/flight_operability_fact.csv")

cause_cols = [
    "carrier_delay_minutes",
    "weather_delay_minutes",
    "nas_delay_minutes",
    "security_delay_minutes",
    "late_aircraft_delay_minutes",
]

label_map = {
    "carrier_delay_minutes": "Air Carrier",
    "weather_delay_minutes": "Weather",
    "nas_delay_minutes": "NAS",
    "security_delay_minutes": "Security",
    "late_aircraft_delay_minutes": "Late-arriving",
}

has_cause_data = fact[cause_cols].notna().any(axis=1) & (fact[cause_cols].fillna(0).sum(axis=1) > 0)

fact["primary_delay_cause"] = None
fact.loc[has_cause_data, "primary_delay_cause"] = (
    fact.loc[has_cause_data, cause_cols]
    .idxmax(axis=1)
    .map(label_map)
)
# has_cause_data is false for on-time/early operated flights (BTS reports cause
# minutes only when ArrDelay >= 15) and for all cancellations. Those rows keep
# primary_delay_cause = None rather than defaulting to the first cause column.

fact["controllable_delay_flag"] = (fact["primary_delay_cause"] == "Air Carrier").astype(int)
fact["late_arriving_flag"] = (fact["primary_delay_cause"] == "Late-arriving").astype(int)
fact["cascade_delay_flag"] = fact["late_arriving_flag"]
fact["controllable_cancel_flag"] = (
    (fact["cancelled_flag"] == 1) &
    (fact["cancellation_code_bts"] == "A")
).astype(int)

fact["controllable_severe_delay_flag"] = (
    (fact["controllable_delay_flag"] == 1) &
    ((fact["dep_delay_min"] >= 60) | (fact["arr_delay_min"] >= 60))
).astype(int)

fact["late_arriving_severe_delay_flag"] = (
    (fact["late_arriving_flag"] == 1) &
    ((fact["dep_delay_min"] >= 60) | (fact["arr_delay_min"] >= 60))
).astype(int)

agg = (
    fact.groupby(["market_bucket", "weather_bucket", "period_flag"])
        .agg(
            flights_total=("route_key", "size"),
            operated_count=("operated_flag", "sum"),
            controllable_cancel_count=("controllable_cancel_flag", "sum"),
            controllable_delay_count=("controllable_delay_flag", "sum"),
            controllable_severe_delay_count=("controllable_severe_delay_flag", "sum"),
            late_arriving_severe_delay_count=("late_arriving_severe_delay_flag", "sum"),
        )
        .reset_index()
)

agg["controllable_cancel_rate"] = agg["controllable_cancel_count"] / agg["flights_total"]
agg["controllable_delay_rate"] = agg["controllable_delay_count"] / agg["operated_count"]
agg["controllable_severe_delay_rate"] = agg["controllable_severe_delay_count"] / agg["operated_count"]
agg["late_arriving_severe_delay_rate"] = agg["late_arriving_severe_delay_count"] / agg["operated_count"]
```

The coding agent should adjust the exact field names to match the existing Fragility I implementation in the repository.[cite:17][cite:156]

## Output files

This add-on should produce at least the following new outputs:

- `output/weather_fragility_machine_chart_data.csv`
- `output/weather_fragility_machine_exec_chart.png`
- `output/fragility_ii_summary.md`[cite:156]

If the existing repo already has naming conventions for alternate studies, those can be adapted as long as the outputs are clearly distinct from Fragility I.[cite:25]

## QA requirements

Add the following QA checks for Fragility II:

- Count of flights with non-null BTS cause-minute data, and confirmation that this count is restricted to flights with ArrDelay >= 15 (i.e., that on-time and cancelled flights were not zero-filled into a spurious cause).
- Share of delayed flights receiving a non-ambiguous `primary_delay_cause`.
- Count and share of Air Carrier severe delays by basket.
- Count and share of Late-arriving severe delays by basket.
- Null rate for reused `weather_bucket` field.
- Sample sizes for each `market_bucket × weather_bucket × period_flag` bucket, with cells below the minimum-sample threshold explicitly listed.[cite:156][cite:25]

If route-level counts are too sparse for stable estimates, the study should collapse some buckets, rely more heavily on basket-level aggregation, or fall back to the combined-peer-basket series described above rather than discard the comparison entirely.[cite:25]

## Risks, threats to validity, and alternative explanations

This section exists so that a skeptical outside reviewer — including analysts inside the carrier being studied — can see the study's own account of where it could be wrong, rather than relying on a third party to find these issues later.

### Cause granularity limitation

Public BTS cause data do not isolate maintenance from crew, fueling, baggage, cleaning, or other airline-controlled factors inside the Air Carrier category.[cite:156][cite:167][cite:169] An elevated `controllable_*` rate in this study is evidence of elevated *airline-attributed* disruption, not evidence about which specific internal function (maintenance, crew scheduling, ground handling, etc.) is responsible.

### Self-reported cause data

Carriers, not an independent third party, select the cause code for each delayed or cancelled flight in BTS reporting. Coding conventions or thresholds for attributing a delay to "Air Carrier" versus another category could in principle differ across carriers in ways this study cannot detect or adjust for. This is a property of the public data source itself, not of this study's methodology, and should be disclosed alongside any controllable-fragility finding.

### Cascade ambiguity

Late-arriving aircraft reflects propagated disruption and is analytically useful for schedule fragility, but it is not proof that maintenance was the original initiating cause.[cite:156][cite:169]

### Weather interaction

Weather can trigger or amplify later controllable or late-arriving effects, which is why reusing the weather-bucket architecture from Fragility I is important.[cite:156][cite:135][cite:79]

### Regional-operator overlap across baskets

Fragility I documented that a single regional operator (SkyWest, reporting as OO) flies under all three carrier contracts in this study's route baskets — AA, UA, and DL. Any operator-level factor that is consistent across contracts (e.g., a SkyWest-wide crew-scheduling practice) would tend to appear in all three baskets and be controlled out by the AA-vs-peer comparison; any factor specific to the AA contract terms or AA-assigned aircraft would not be controlled out. Fragility II should report controllable and cascade metrics broken out by reporting/operating carrier within each basket wherever sample size allows, so a reviewer can see whether an AA-basket effect is concentrated in a specific regional partner or spread across all of them.

### Route-basket selection was fixed before this study was designed

The AA regional, UA peer, and DL peer route baskets were defined in the first fragility study, before the controllable/cascade question in this add-on was formulated. Fragility II reuses those baskets unchanged rather than redefining or tuning them to fit a controllable-disruption narrative. This sequencing is recorded here so a reviewer can verify that the route selection was not adjusted after the fact to produce a particular result.

### Definitional consistency with Fragility I

Fragility II's recommended severe-delay definition (`ArrDelay >= 60` or `DepDelay >= 60`) is an OR of both delay measures, while Fragility I's `severe_delay_flag` uses arrival delay only. Both use the same 60-minute threshold, but the boolean logic differs. The implementation must document which definition backs each published metric, and should not present `severe_delay_rate` (Fragility I) and `controllable_severe_delay_rate` / `late_arriving_severe_delay_rate` (Fragility II) as directly comparable without that disclosure.

### Alternative, non-causal explanations for an observed gap

If AA regional shows an elevated controllable or cascade rate relative to peers, at least the following non-mutually-exclusive explanations are consistent with that observation and cannot be ruled out by this study's data alone:

- Differences in aircraft age, type, or maintenance-base proximity across the regional fleets operating each basket.
- Differences in schedule buffer (the slack built into turn times and block times) independent of crew or maintenance quality.
- Differences in route/airport infrastructure (gate availability, ramp congestion, de-icing capacity) that are airport- or network-specific rather than carrier-specific.
- Random period-to-period variation; this is partially addressed by comparing both the baseline and recent periods rather than a single pooled window, but a two-period, two-year study cannot fully rule out an unusual year.
- Reporting-convention differences between carriers in how cause codes are assigned (see "Self-reported cause data" above).

This study does not attempt to adjudicate among these explanations. It reports whether the public-data signature is elevated, and by how much, with the sample sizes and definitions needed for a reader to evaluate the result independently.

### Causal wording prohibition

Any written output must avoid claims such as “maintenance caused” or “crew inexperience caused” unless the data only support “consistent with,” “associated with,” or “elevated relative to peers.”[cite:156][cite:153]

## Definition of done

Fragility II is complete when the existing repository can be rerun to produce:

1. An enriched or reused fact table containing the controllable/cascade fields required for this study.
2. A chart-ready aggregated dataset for Fragility II.
3. One additional executive-ready PNG chart showing controllable and cascade fragility vs peers.
4. One short written summary of results and caveats.

All of this should occur without manual intervention beyond the same configuration and credential handling already used in the first study.[cite:25][cite:156][cite:153]
