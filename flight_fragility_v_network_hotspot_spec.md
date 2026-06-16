# Flight Fragility V: Network Hotspot Engine — Spec for Systemwide Fragility Discovery and Prioritization

This document is a standalone specification for a fifth study intended to evolve the Flight Fragility work from corridor-focused analysis into a scalable, systemwide fragility-discovery and prioritization engine. It assumes that Fragility I through IV either exist or are conceptually available, but it must be designed so the user can run small validation slices in a constrained environment and large exploratory runs on a powerful single-node server.[cite:25][cite:70][cite:156][cite:220]

The purpose of Fragility V is to answer a network-wide management question: **where across the AA network are the most materially relevant fragility hotspots, which operator/hub/market combinations drive them, and which findings are robust enough to support actionable leadership focus?**[cite:25][cite:156][cite:194]

This study should be framed as an outside-in, decision-support engine rather than a narrow complaint analysis. It is intended to produce one executive-ready graphic, but also to generate a reusable scoring dataset and ranking framework that can support broader management and operational interpretation.[cite:194][cite:197]

## Objective

Build a scalable, rerunnable network-wide analysis that identifies and ranks **fragility hotspots** across the AA network using weather, controllable, cascade, and economic-burden dimensions, with sufficient structure to support executive, operator-level, and discipline-specific follow-up.[cite:70][cite:156][cite:194]

## Strategic framing

Fragility I established whether the focal corridor appeared unusually weather-sensitive.[cite:70][cite:135]

Fragility II established whether controllable and cascade symptoms were elevated.[cite:156][cite:153]

Fragility III translated those symptoms into an economic-burden proxy.[cite:194][cite:197]

Fragility IV attributes the symptoms across operator classes such as Envoy, PSA, and AA mainline.[cite:25][cite:156]

Fragility V extends all of the above into a **systemwide hotspot-seeking analysis** so leadership can determine:

- whether the original corridor is an isolated case or part of a broader pattern,
- which hubs/operators/markets account for most meaningful excess fragility,
- and which hotspots are robust across definitions and assumptions.[cite:25][cite:194]

## Target audiences

### CEO and executive committee

The CEO-level readout should answer:

- Where is the biggest excess fragility?
- Is it isolated or systemic?
- Who needs to own investigation or remediation?
- What are the largest potential customer and economic stakes?[cite:194][cite:197]

### Operating and network leaders

Ops, network planning, regional governance, and operator leadership should be able to use the outputs to identify:

- which hubs or spoke families are most unstable,
- which operator-hub combinations matter most,
- whether the dominant signature is weather, controllable, cascade, or mixed,
- which candidate levers warrant internal study.[cite:156][cite:153]

### Finance and commercial leadership

Finance and commercial readers should be able to see where excess fragility plausibly translates into the greatest economic or customer-value burden, even if exact passenger itineraries are not observed.[cite:194][cite:197][cite:195]

## Core business questions

Fragility V should answer at least these questions:

1. Which AA markets or market families have the worst fragility scores on a normalized basis?[cite:25]
2. Which hubs and operators are associated with the highest concentration of those hotspots?[cite:25][cite:156]
3. Are the most material hotspots weather-led, controllable-led, cascade-led, or economically led?[cite:70][cite:156][cite:194]
4. Which findings remain hotspots across multiple scenario definitions and sensitivity cases?[cite:194][cite:197]
5. Does the original corridor resemble a broader systemic class of hotspot or remain an edge case?[cite:25]

## Scope

### Default network unit

The default unit of analysis should be **hub-spoke market families** rather than all possible O&D pairs, at least in phase 1. This reduces noise and helps keep comparisons more operationally meaningful.[cite:25]

Recommended level for phase 1:

- AA-marketed domestic hub-spoke markets,
- grouped by hub, operator class, and spoke airport,
- with optional aggregation to spoke-region or distance-band family.[cite:25]

### Optional expansions

The engine should be architected so it can later expand to:

- all AA-marketed domestic O&D markets,
- rolling windows,
- time-of-day bank analysis,
- trend detection,
- clustering or graph-style exploration.

These are not required for the first executable version but should not be blocked by the data model.[cite:220][cite:221]

## Required source data

Fragility V should reuse and extend the curated outputs of earlier studies wherever possible.

### Reused inputs

- BTS flight-level operational data.[cite:25]
- FAA weather-bucket assignments from Fragility I.[cite:70][cite:135]
- Controllable/cascade fields from Fragility II.[cite:156]
- Economic-burden logic or outputs from Fragility III.[cite:194][cite:197]
- Operator-class mapping from Fragility IV.[cite:25]

### Core fields needed

At minimum, the engine requires:

- `flight_date`
- `origin`
- `dest`
- `hub_family`
- `operator_class`
- `weather_bucket`
- `dep_delay_min`
- `arr_delay_min`
- `cancelled_flag`
- `operated_flag`
- `controllable_delay_flag`
- `controllable_cancel_flag`
- `late_arriving_flag`
- `period_flag`
- any burden-proxy fields used in Fragility III.[cite:25][cite:70][cite:156][cite:194]

## Analytical philosophy

Fragility V is not just another chart. It is a **scoring engine** that produces one executive chart as a distillation layer on top of a broader ranking dataset.[cite:194]

The internal engine should compute a standardized fragility scorecard for every analyzed market family and then expose:

- top hotspots,
- hub/operator concentrations,
- scenario robustness,
- and economic materiality.[cite:156][cite:194]

## Hotspot definition

A hotspot should not be defined by a single raw metric alone. The study should support a composite definition using at least these dimensions:

- cancellation intensity,
- severe-delay intensity,
- controllable fragility,
- late-arriving cascade fragility,
- weather sensitivity,
- economic burden proxy.[cite:70][cite:156][cite:194]

### Recommended hotspot score

For each market family, define a configurable composite score such as:

```text
hotspot_score =
  a1 * normalized_cancellation_rate +
  a2 * normalized_severe_delay_rate +
  a3 * normalized_controllable_fragility +
  a4 * normalized_cascade_fragility +
  a5 * normalized_weather_fragility +
  a6 * normalized_economic_burden
```

Each component should be normalized in a documented way, such as z-score within the included network or percentile rank, and all weights must be configurable.[cite:194][cite:156]

## Robustness layer

This study should explicitly support the idea that a good hotspot is one that remains a hotspot under more than one reasonable definition.[cite:194][cite:197]

### Required robustness concepts

At minimum, allow the engine to rerun hotspot ranking under changes to:

- component weights,
- cancellation-equivalent burden assumptions,
- severity thresholds,
- weather-bucket handling,
- market-family aggregation granularity.[cite:194][cite:197][cite:207]

### Recommended robustness metric

Create a field such as:

- `hotspot_robustness_score`

Possible definition:

- share of tested scenarios in which a market appears in the top decile or top N hotspots.

This helps distinguish true management-relevant hotspots from artifacts of one narrow scoring choice.[cite:194][cite:197]

## Analysis modules

Fragility V should be structured as a bundle of analytic modules under one scoring framework.

### Module A: network-wide hotspot ranking

Rank all included market families by composite hotspot score.[cite:25][cite:194]

### Module B: operator concentration analysis

Summarize what share of top hotspots are operated by Envoy, PSA, AA mainline, or other operator classes.[cite:25][cite:156]

### Module C: hub concentration analysis

Summarize what share of top hotspots are associated with each major AA hub.[cite:25]

### Module D: signature decomposition

For each hotspot, identify whether the score is primarily driven by weather, controllable, cascade, or economic components.[cite:70][cite:156][cite:194]

### Module E: trend / persistence analysis

If sufficient data volume exists, measure whether hotspots are persistent across rolling windows or are episodic.[cite:5][cite:25]

This module is desirable but can be optional in phase 1 if scope pressure is high.[cite:25]

## Chart specification

This study should produce **one executive-ready graphic** and may optionally produce supporting tables or second-level charts for internal analysis.

### Recommended executive chart

Use a **ranked hotspot chart** or **network hotspot scorecard heat map**.

Preferred version:

- Y-axis: top N hotspot market families or operator-hub-market combinations.
- X-axis: component scores or a small set of component columns.
- Visual encoding: heat map or stacked marker structure showing the relative contribution of:
  - weather,
  - controllable,
  - cascade,
  - economic burden.[cite:70][cite:156][cite:194]

This produces a management-consulting style “where to look first” output rather than another one-dimensional bar chart.[cite:194]

### Alternative executive chart

If readability is better, use a **bubble scatter** where:

- X-axis = economic burden proxy,
- Y-axis = composite hotspot score,
- point size = flight volume,
- point color = operator class or dominant fragility signature.

This can be very effective for showing which hotspots are both operationally bad and commercially material.[cite:194][cite:197]

### Annotation

The annotation should answer the top-level management question directly, for example:

- “The original corridor resembles a broader class of DFW/CLT regional spoke hotspots, with a majority of the most material hotspots concentrated in a small number of operator-hub combinations.”
- “The largest hotspots are not systemwide weather artifacts; they are concentrated in a limited set of high-burden markets with mixed controllable and cascade signatures.”

The language must remain careful about causality and focus on concentration, pattern, and actionability.[cite:156][cite:194]

## Written result

Produce:

- `output/fragility_v_summary.md`

It should summarize:

1. The top hotspots.
2. Which hubs/operators dominate the list.
3. Whether the original corridor is isolated or representative.
4. Which signatures dominate: weather, controllable, cascade, or economic burden.
5. Which areas appear most worthy of internal management review.

The summary should read like an outside-in prioritization memo, not an advocacy brief.[cite:194][cite:197]

## Architecture and execution model

Fragility V must be designed explicitly for two realities:

1. The coding agent will validate and test only a small slice in a constrained container.
2. The user may execute a much larger “big run” on a high-core, high-memory server with fast local storage.[cite:220][cite:221]

### Required run modes

Support at least:

- `test`
- `local`
- `bigrun`

Definitions:

- `test`: one or two months, one hub family or a tiny route subset, enough to validate logic and artifact creation.
- `local`: multi-hub but still bounded.
- `bigrun`: full configured network scope, all selected years, all scenarios, intended for provisioned hardware.

### Required backend abstraction

Support a configurable backend layer with at least:

- `pandas`
- `duckdb`
- `polars`

This is required so the same logical analysis can run on tiny subsets in a sandbox and large datasets on a powerful server. DuckDB is especially attractive because it can query Parquet directly and efficiently at large scale on a single node.[cite:220][cite:221]

GPU support is optional and may be added later, but the design should not require GPU to function at large scale.[cite:220][cite:221]

### Required storage design

- Use Parquet for staging and curated layers wherever possible.
- Partition curated datasets by at least year/month and optionally by operator or hub family.
- Avoid using CSV as the main internal analytical store except for small final outputs.[cite:220][cite:221]

### Required scope controls

Major scripts must support filters for:

- years and months,
- hubs,
- operator classes,
- route families,
- weather-mode use,
- scenario sets,
- top-N hotspot count,
- backend,
- run mode.

### Recommended orchestration approach

The repository should allow the same command pattern to run either tiny or big analyses via config overrides, rather than maintaining separate code paths.[cite:220]

## Suggested scripts

The implementation may use separate scripts or modes, but conceptually it should add at least:

```text
scripts/
  34_analyze_fragility_hotspots.py
  44_plot_fragility_hotspots.py
```

If the repo has evolved into a more modular engine, these may be implemented as subcommands or modes instead.[cite:25]

## Output files

This study should produce at least:

- `output/fragility_v_hotspot_scorecard.parquet`
- `output/fragility_v_hotspot_rankings.csv`
- `output/fragility_v_exec_chart.png`
- `output/fragility_v_summary.md`

Optional but useful:

- `output/fragility_v_hub_rollup.csv`
- `output/fragility_v_operator_rollup.csv`
- `output/fragility_v_scenario_robustness.csv`

## QA requirements

Add the following QA checks:

- Confirm all included markets have sufficient sample size.
- Confirm normalization and weighting steps are logged and reproducible.
- Confirm hotspot rankings are stable on overlapping slices between `test` and `local` modes where data overlap.
- Confirm scenario results are stored with scenario identifiers.
- Confirm all Parquet partitions are readable and schema-consistent across runs.[cite:220][cite:221]

## Risks and interpretation constraints

### Composite-score arbitrariness

Any composite hotspot score introduces design choices. Those choices must be visible, configurable, and tested via robustness scenarios.[cite:194][cite:197]

### Apples-to-oranges risk

Markets differ by stage length, weather, hub structure, and operator role. Use market-family and hub-spoke structures to limit misleading comparisons.[cite:25]

### Signal vs noise risk

Some hotspots may reflect temporary events rather than persistent operational patterns. A persistence or rolling-window check is recommended wherever feasible.[cite:5][cite:25]

### Causal discipline

The study must not claim to know the underlying causes of hotspots beyond the public categories it observes. It should suggest areas for internal management review, not diagnose internal mechanisms with certainty.[cite:156][cite:153]

## Definition of done

Fragility V is complete when the repository can be rerun in both small validation mode and large systemwide mode to produce a reproducible hotspot ranking engine, one executive-ready network hotspot graphic, and a written prioritization summary that identifies the most material fragility hotspots across the included AA network and frames them in a constructive, action-oriented way for airline leadership.[cite:25][cite:156][cite:194][cite:220]
