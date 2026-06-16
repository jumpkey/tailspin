# Flight Fragility III: Show Me the Money — Add-on Spec for Economic Impact Estimation

This document is a standalone add-on specification for a third study to be implemented alongside the existing Flight Fragility work. It assumes Fragility I and Fragility II already exist in the repository, but this study should be able to run in parallel if the required base flight-level data and route baskets are available.[cite:25][cite:156][cite:70]

The purpose of this add-on is to translate observed schedule fragility into an **economic-impact proxy** using public operational data and published benchmark cost inputs. It does **not** attempt to reconstruct passenger-level opportunity cost from actual itineraries, because public BTS and FAA operational data do not contain itinerary, fare, or rebooking detail at the passenger level.[cite:25][cite:19][cite:195]

The study therefore estimates the **economic drag associated with excess disruption** using flight-level and passenger-time cost benchmarks rather than exact realized lost revenue from individual misconnects and rebookings.[cite:194][cite:197][cite:207]

## Objective

Build a third reproducible analysis that answers: **Given the excess disruption observed in AA regional-style spoke markets relative to peers, what is the approximate economic burden implied by that excess fragility using defensible public cost benchmarks?**[cite:194][cite:197][cite:207]

This add-on should produce one additional executive-ready graphic and a short written result, and it must be rerunnable under the same repo conventions as the earlier Fragility studies.[cite:194][cite:197]

## Study framing

Fragility I measures weather sensitivity. Fragility II measures controllable and cascade sensitivity. Fragility III converts one or both of those operational findings into a **money frame** that is understandable to executive audiences.[cite:70][cite:135][cite:156]

This study is intentionally conservative in framing:

- It does **not** claim exact lost revenue from specific displaced passengers.[cite:195][cite:196]
- It does **not** claim exact voucher, hotel, or reaccommodation expense without internal accounting data.[cite:202]
- It **does** estimate the order-of-magnitude economic burden associated with excess delay and cancellation outcomes using published cost references and value-of-time guidance.[cite:194][cite:197][cite:207]

## What this study is and is not

### In scope

- Estimating excess cost associated with excess disruption in AA regional spoke markets relative to peers.[cite:194][cite:197]
- Using public benchmarks for passenger value of time, airline block-time cost, and total delay burden.[cite:194][cite:207][cite:217]
- Producing a comparative, scenario-style economic estimate based on observed flight-level differences.[cite:197][cite:208]

### Out of scope

- Reconstructing individual passenger itineraries or actual misconnect paths.[cite:195][cite:196]
- Estimating exact spoilage, sell-up, refund, voucher, or displaced demand from internal commercial inventory systems.[cite:196][cite:202]
- Claiming causal economic loss directly attributable to maintenance, crew, weather, or routing decisions beyond what public data can support.[cite:156][cite:153]

## Feasibility conclusion

This study is feasible because public data can quantify the **difference in operational outcomes** between AA regional markets and peers, and published guidance can assign standardized economic values to delay time and aircraft operating time.[cite:25][cite:194][cite:207]

This study is **not** feasible as a passenger-itinerary revenue model because public flight datasets do not include itinerary, booking, or revenue allocation information. Commercial and proprietary products such as OAG and other passenger-data tools exist precisely because those inferences cannot be made reliably from BTS schedule and on-time data alone.[cite:196][cite:201][cite:195]

## Source data

### Reused operational data

This study should reuse the curated or staged outputs from Fragility I and/or Fragility II whenever possible.[cite:25][cite:70][cite:156]

Minimum reused operational inputs:

- Flight-level BTS on-time and cancellation data.[cite:25]
- Market-basket definitions from the prior studies.[cite:25]
- Weather buckets from Fragility I if using weather-stratified costing.[cite:70][cite:135]
- Controllable and cascade flags from Fragility II if using controllable-cost attribution.[cite:156]

### Economic benchmark sources

Use published, citable benchmark sources rather than invented assumptions.

#### Airlines for America / FAA / NEXTOR summary

Airlines for America’s delay-cost dataset states that in 2024 the average cost of aircraft block time for U.S. passenger airlines was **$100.76 per minute**, and that using **$47 per hour** as the average value of a passenger’s time yields passenger delay costs in the billions. The same summary cites FAA/NEXTOR estimates of **$33 billion** in annual delay costs in 2019.[cite:194]

Reference:

- A4A U.S. Passenger Carrier Delay Costs: [https://www.airlines.org/dataset/u-s-passenger-carrier-delay-costs/](https://www.airlines.org/dataset/u-s-passenger-carrier-delay-costs/) [cite:194]

#### DOT value-of-time guidance

DOT’s revised departmental guidance on the valuation of travel time provides the policy basis for assigning monetary value to time in transportation economic analysis.[cite:207]

Reference:

- DOT travel-time valuation guidance: [https://www.transportation.gov/office-policy/transportation-policy/revised-departmental-guidance-valuation-travel-time-economic](https://www.transportation.gov/office-policy/transportation-policy/revised-departmental-guidance-valuation-travel-time-economic) [cite:207]

#### FAA treatment of time

FAA benefit-cost materials provide aviation-specific treatment of time and related economic-analysis conventions, which can be used to justify sensitivity cases or value-of-time assumptions.[cite:217][cite:212]

References:

- FAA treatment of time: [https://www.faa.gov/sites/faa.gov/files/regulations_policies/policy_guidance/benefit_cost/econ-value-section-1-tx-time.pdf](https://www.faa.gov/sites/faa.gov/files/regulations_policies/policy_guidance/benefit_cost/econ-value-section-1-tx-time.pdf) [cite:217]
- FAA airport benefit-cost guidance: [https://www.faa.gov/regulations_policies/policy_guidance/benefit_cost/FAA-Airport-Benefit-Cost-Guidance.pdf](https://www.faa.gov/regulations_policies/policy_guidance/benefit_cost/FAA-Airport-Benefit-Cost-Guidance.pdf) [cite:212]

#### NEXTOR / Total Delay Impact study

The FAA-sponsored NEXTOR / Brattle Total Delay Impact study is useful because it explicitly notes that cancellations and missed connections can create passenger delay burdens not visible in ordinary flight-delay statistics.[cite:197]

Reference:

- Total Delay Impact study: [http://rosap.ntl.bts.gov/view/dot/6234](http://rosap.ntl.bts.gov/view/dot/6234) [cite:197]

#### Supplemental academic cost references

Academic work estimating U.S. domestic passenger delay costs can be used for calibration and sanity checks, but should not replace the primary benchmark sources above.[cite:208][cite:213]

References:

- Estimation of flight delay costs for U.S. domestic air passengers: [https://scholarsmine.mst.edu/cgi/viewcontent.cgi?article=4151&context=civarc_enveng_facwork](https://scholarsmine.mst.edu/cgi/viewcontent.cgi?article=4151&context=civarc_enveng_facwork) [cite:208]
- Analysis of airline and passenger delay costs using FAA data: [https://search.proquest.com/openview/b23519010c927475ee4827467d8e78db/1?pq-origsite=gscholar&cbl=51908](https://search.proquest.com/openview/b23519010c927475ee4827467d8e78db/1?pq-origsite=gscholar&cbl=51908) [cite:213]

## Dependence on Fragility I and II

Fragility III can run in either of two modes.

### Mode A: Parallel to Fragility II

If only Fragility I or base BTS flight data exist, Fragility III can estimate economic burden from **overall excess cancellations and delays** in AA regional spoke markets versus peers.[cite:25][cite:194]

### Mode B: Extension of Fragility II

If Fragility II outputs exist, Fragility III should preferentially estimate economic burden from **controllable** and **cascade** excess fragility, which is a stronger and more actionable business framing.[cite:156][cite:194]

The implementation should therefore support both modes through configuration, with Fragility II-enhanced mode preferred when its outputs are available.[cite:156]

## Conceptual model

Fragility III estimates **excess economic burden** as the difference between observed AA regional disruption and a counterfactual benchmark built from peer performance.[cite:194][cite:197]

The counterfactual is:

- “What would AA regional spoke markets have cost if they had experienced peer-level disruption rates under the same broad market-basket structure?”[cite:194]

The estimate should be framed as **excess burden relative to peer reliability**, not as total network cost.[cite:194][cite:197]

## Costing approaches

This study should support a tiered costing framework.

### Tier 1: Passenger-time burden proxy

This is the simplest and most defensible public-data cost model.[cite:194][cite:207][cite:217]

Formula concept:

- Excess disrupted passenger-hours × value of passenger time = excess passenger burden.

Where:

- Excess disrupted passenger-hours are estimated from excess delay minutes and cancellation-equivalent delay assumptions.[cite:197]
- Passenger value of time is drawn from FAA/DOT-guided benchmarks, with the A4A summary citing **$47/hour** as an average value of passenger time.[cite:194][cite:217]

### Tier 2: Airline operating-time burden proxy

This estimates direct airline operating burden from excess delay time.[cite:194]

Formula concept:

- Excess block-delay minutes × airline block-time cost per minute = excess airline operating burden.

The A4A source provides **$100.76 per minute** as the 2024 average cost of aircraft block time for U.S. passenger airlines.[cite:194]

### Tier 3: Combined burden proxy

Combine Tier 1 and Tier 2 into a blended “executive burden” estimate, while making clear that this is still a proxy and does not equal accounting P&L impact.[cite:194][cite:197]

Formula concept:

- Combined proxy burden = passenger-time burden + airline operating-time burden.

### Tier 4: Cancellation-equivalent burden scenario

Because cancellations create hidden delays and reaccommodation burdens not visible in simple delay minutes, the study should support a scenario assumption that each cancellation carries a fixed passenger-hour burden and optional airline burden multiple.[cite:197]

This is not a factual observed value; it is a configurable scenario lever with transparent sensitivity testing.[cite:197][cite:207]

## Recommended scenario assumptions

The implementation should support a configuration file with one base case and optional sensitivity cases.[cite:194][cite:207]

### Base case assumptions

- Passenger value of time: `$47/hour`.[cite:194]
- Airline block-time cost: `$100.76/minute`.[cite:194]
- Severe delay threshold: reuse prior studies, e.g. `60 minutes`.[cite:25]
- Cancellation-equivalent passenger burden: configurable, e.g. `240`, `360`, or `480` minutes per canceled passenger as scenario cases, not as asserted facts.[cite:197]
- Load-factor or passenger-count proxy: configurable if using seats or estimated passengers per flight; otherwise keep the core analysis at the flight-count level to avoid overreach.[cite:196][cite:197]

### Sensitivity cases

Support at least three scenarios:

- `low`
- `base`
- `high`

These scenarios should vary at least:

- passenger time value,
- cancellation-equivalent delay burden,
- and optionally estimated passengers affected per disrupted flight.[cite:207][cite:217][cite:197]

## Passenger-count problem and feasible solutions

Public BTS operational data do not include flight-level passenger manifests or itinerary details, so passenger-level cost estimation must handle passenger volume transparently.[cite:25][cite:195]

This study should support two modes.

### Mode 1: Flight-level burden only

Estimate excess cost at the flight level without multiplying by passengers. This is the most conservative approach and relies only on excess flight delays and cancellations.[cite:194]

### Mode 2: Passenger-exposure proxy

Allow an optional estimated passengers-per-flight input, ideally by aircraft-type or route-average seat count if available in the repo or from a separate, documented source. This remains a proxy and must be labeled clearly.[cite:196][cite:208]

If no robust passenger proxy exists, the default implementation should favor the flight-level burden framing to avoid false precision.[cite:195][cite:196]

## Inputs

### Required operational inputs

At minimum, this add-on requires:

- `flight_date`
- `market_bucket`
- `period_flag`
- `weather_bucket` if weather-stratified costing is used
- `dep_delay_min`
- `arr_delay_min`
- `cancelled_flag`
- `operated_flag`
- peer/AA basket identification[cite:25][cite:70]

### Optional Fragility II inputs

If available, also use:

- `controllable_delay_flag`
- `controllable_cancel_flag`
- `late_arriving_flag`
- `controllable_severe_delay_flag`
- `late_arriving_severe_delay_flag`[cite:156]

### Required configuration inputs

Create a new file such as `config/economic_scenarios.yaml`.

Example:

```yaml
mode: "fragility_ii_preferred"

value_of_time_per_hour:
  low: 35.0
  base: 47.0
  high: 60.0

airline_block_cost_per_min:
  low: 80.0
  base: 100.76
  high: 120.0

cancellation_equivalent_minutes:
  low: 240
  base: 360
  high: 480

estimated_passengers_per_flight:
  low: null
  base: null
  high: null

cost_mode: "combined"
stratify_by_weather: true
```

The defaults should favor transparent and conservative public benchmarks.[cite:194][cite:207]

## Derived fields

Create or derive the following fields as needed:

- `excess_delay_minutes_vs_peer`
- `excess_cancellations_vs_peer`
- `cancellation_equivalent_minutes`
- `excess_airline_cost_proxy`
- `excess_passenger_cost_proxy`
- `excess_combined_cost_proxy`
- `cost_scenario`
- `cost_basis`[cite:194][cite:197]

If Fragility II mode is enabled, also derive:

- `excess_controllable_delay_minutes_vs_peer`
- `excess_controllable_cancellations_vs_peer`
- `excess_cascade_delay_minutes_vs_peer`[cite:156]

## Core analytic logic

### Step 1: define peer benchmark

For each market basket and optional weather bucket, calculate peer baseline disruption rates.[cite:25][cite:70]

### Step 2: calculate excess disruption for AA regional

For each AA regional bucket, calculate the difference between AA observed rates and peer benchmark rates.[cite:25][cite:194]

Illustrative examples:

- `excess_cancel_rate = aa_cancel_rate - peer_cancel_rate`
- `excess_severe_delay_rate = aa_severe_delay_rate - peer_severe_delay_rate`

### Step 3: convert excess disruption into excess minutes

Convert excess disruption into excess burden minutes.

Examples:

- Excess delay minutes can be taken from actual excess delay totals versus peer-normalized expectations.[cite:194]
- Excess cancellations can be converted into scenario-based cancellation-equivalent minutes.[cite:197]

### Step 4: apply economic assumptions

Apply the selected cost scenario:

- Passenger burden = excess passenger-equivalent hours × value of time.[cite:194][cite:207]
- Airline burden = excess block-delay minutes × airline block-cost per minute.[cite:194]
- Combined burden = passenger burden + airline burden.[cite:194][cite:197]

### Step 5: summarize by period and optionally by weather bucket

Aggregate to the executive message level, such as annualized excess burden or study-window excess burden.[cite:194]

## Suggested formulas

Illustrative formulas for base implementation:

```python
excess_delay_minutes = observed_delay_minutes_aa - expected_delay_minutes_at_peer_rate
excess_cancellations = observed_cancellations_aa - expected_cancellations_at_peer_rate

cancellation_equiv_minutes = excess_cancellations * scenario_cancel_minutes

excess_airline_cost_proxy = excess_delay_minutes * airline_cost_per_min
excess_passenger_cost_proxy = ((excess_delay_minutes + cancellation_equiv_minutes) / 60.0) * value_of_time_per_hour
excess_combined_cost_proxy = excess_airline_cost_proxy + excess_passenger_cost_proxy
```

If passenger counts are introduced later, the passenger-cost formula can be extended, but the phase-1 implementation should stay conservative unless the repo already has a defensible passenger-exposure input.[cite:195][cite:196]

## Chart specification

This study should produce **one additional executive-ready graphic** focused on money, not rates.[cite:194]

### Recommended chart

Use a **single grouped bar chart** or **waterfall-style bar chart** showing the estimated excess economic burden for AA regional versus the peer benchmark under low, base, and high scenarios.[cite:194][cite:197]

#### Preferred version

- X-axis: cost scenarios (`low`, `base`, `high`)
- Y-axis: estimated excess economic burden (USD)
- Bars segmented or paired by component:
  - passenger-time burden
  - airline operating burden
  - optional combined total marker[cite:194][cite:207]

#### Optional alternate version

- X-axis: `benign`, `marginal`, `adverse` weather buckets
- Y-axis: excess combined burden
- Series: `low`, `base`, `high`

The preferred version is stronger for executive consumption because it directly frames the range of plausible economic burden rather than leading with weather methodology.[cite:194][cite:197]

### Annotation

Add one annotation generated from computed values, such as:

- “Under the base scenario, AA regional spoke fragility implies an estimated $X million excess burden versus peer reliability.”

If Fragility II mode is used, the annotation may state:

- “Under the base scenario, excess controllable and cascade fragility implies an estimated $X million burden versus peer reliability.”

The annotation must be explicit that these are **proxy estimates based on public benchmarks**, not exact accounting losses.[cite:194][cite:197][cite:207]

## Written result

Produce a short written result file:

- `output/fragility_iii_summary.md`

The summary should state:

1. Which operational basis was used: overall fragility, weather fragility, or Fragility II controllable/cascade fragility.[cite:70][cite:156]
2. The base-case estimated excess burden.
3. The low/high sensitivity range.
4. A caveat that passenger itineraries, vouchers, and internal reaccommodation economics are not observed in the public data.[cite:195][cite:196][cite:202]

## Implementation architecture

This add-on should fit the same rerunnable repo structure and can be implemented with new scripts such as:

```text
scripts/
  32_analyze_fragility_money.py
  42_plot_fragility_money.py
```

If the existing repo uses a modular analysis design, a mode-based extension is acceptable instead of new files. The important requirement is that Fragility III can be rerun without breaking Fragility I or II outputs.[cite:25][cite:156]

## Output files

This add-on should produce at least:

- `output/fragility_iii_chart_data.csv`
- `output/fragility_iii_exec_chart.png`
- `output/fragility_iii_summary.md`[cite:194][cite:197]

## QA requirements

Add the following QA checks:

- Confirm peer benchmark rates used in the economic model.[cite:25]
- Confirm excess disruption values are non-negative where plotted, or explicitly show negative values if AA outperforms peers.[cite:194]
- Confirm the cost-scenario parameters used in the run match the config file.[cite:207]
- Confirm whether Fragility II mode or base operational mode was used.[cite:156]
- Confirm any passenger proxy input is clearly documented and not silently assumed.[cite:195][cite:196]

## Risks and interpretation constraints

### Passenger-itinerary limitation

Public flight data do not reveal who connected, who misconnected, who was reaccommodated overnight, or what fare or voucher outcomes occurred. The analysis must never imply otherwise.[cite:195][cite:196][cite:202]

### Proxy-not-accounting limitation

The economic outputs are scenario-based proxies using public value-of-time and airline-delay-cost benchmarks. They are not audited revenue, cost-accounting, or P&L measures.[cite:194][cite:197][cite:207]

### Sensitivity dependence

The output dollar values will be sensitive to assumptions about cancellation-equivalent burden and passenger exposure. This is a reason to show a scenario range rather than a single asserted number.[cite:197][cite:207]

### Interpretation discipline

The right executive message is “this level of excess fragility plausibly carries an economic burden in this range,” not “the airline definitely lost exactly this amount.”[cite:194][cite:197]

## Definition of done

Fragility III is complete when the existing repository can be rerun to produce:

1. A chart-ready dataset converting excess fragility into cost-proxy terms.
2. One executive-ready PNG graphic showing the estimated range of excess economic burden.
3. One short written summary explaining basis, scenario range, and caveats.

The implementation must work under the same repeatable, scripted standards as the earlier studies and must clearly disclose that the outputs are benchmark-based economic proxies derived from public operational data.[cite:194][cite:197][cite:207]
EOF && ls -l output/flight_fragility_iii_show_me_the_money_addon_spec.md
