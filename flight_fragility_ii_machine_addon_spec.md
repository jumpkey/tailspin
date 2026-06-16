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

Set `primary_delay_cause` to the label with the highest minute value for flights with any delay minutes.[cite:156][cite:169]

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

fact["primary_delay_cause"] = (
    fact[cause_cols]
    .fillna(0)
    .idxmax(axis=1)
    .map(label_map)
)

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

- Count of flights with non-null BTS cause-minute data.
- Share of delayed flights receiving a non-ambiguous `primary_delay_cause`.
- Count and share of Air Carrier severe delays by basket.
- Count and share of Late-arriving severe delays by basket.
- Null rate for reused `weather_bucket` field.
- Sample sizes for each `market_bucket × weather_bucket × period_flag` bucket.[cite:156][cite:25]

If route-level counts are too sparse for stable estimates, the study should collapse some buckets or rely more heavily on basket-level aggregation.[cite:25]

## Risks and interpretation constraints

### Cause granularity limitation

Public BTS cause data do not isolate maintenance from crew, fueling, baggage, cleaning, or other airline-controlled factors inside the Air Carrier category.[cite:156][cite:167][cite:169]

### Cascade ambiguity

Late-arriving aircraft reflects propagated disruption and is analytically useful for schedule fragility, but it is not proof that maintenance was the original initiating cause.[cite:156][cite:169]

### Weather interaction

Weather can trigger or amplify later controllable or late-arriving effects, which is why reusing the weather-bucket architecture from Fragility I is important.[cite:156][cite:135][cite:79]

### Causal wording prohibition

Any written output must avoid claims such as “maintenance caused” or “crew inexperience caused” unless the data only support “consistent with,” “associated with,” or “elevated relative to peers.”[cite:156][cite:153]

## Definition of done

Fragility II is complete when the existing repository can be rerun to produce:

1. An enriched or reused fact table containing the controllable/cascade fields required for this study.
2. A chart-ready aggregated dataset for Fragility II.
3. One additional executive-ready PNG chart showing controllable and cascade fragility vs peers.
4. One short written summary of results and caveats.

All of this should occur without manual intervention beyond the same configuration and credential handling already used in the first study.[cite:25][cite:156][cite:153]
