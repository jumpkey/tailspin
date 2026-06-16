# Flight Fragility IV: Operator Attribution — Add-on Spec for Envoy, PSA, and Mainline Comparative Fragility

This document is a standalone add-on specification for a fourth study to be implemented alongside the existing Flight Fragility work. It assumes Fragility I, Fragility II, and Fragility III already exist in the repository, but it should be implemented in a way that can reuse those outputs without requiring manual intervention.[cite:25][cite:156][cite:70]

The purpose of Fragility IV is to answer an attribution question that is central to executive and operating-leader decision-making: **where inside the American Airlines operating structure do materially relevant fragility signals concentrate, and do Envoy, PSA, or AA mainline show meaningfully different patterns of weather sensitivity, controllable fragility, cascade fragility, and economic burden?**[cite:25][cite:156][cite:153]

This study must remain careful about causality. It should not claim to know the internal reasons for performance differences, nor should it assert that any operator or operating model is inherently defective. It should instead identify where observable operational symptoms are concentrated and frame constructive, actionable interpretations for airline leadership.[cite:156][cite:153]

## Implementation notes (resolved 2026-06-16)

The items below were open questions or gaps identified during spec review. They are resolved here so the implementation has one authoritative source of truth; the rest of this document is unchanged from the original request.

### Operator-class mapping

BTS On-Time Performance data has no `Operating_Airline` / marketing-carrier field distinct from `Reporting_Airline` — a field referenced in this repo's existing extraction code never actually populates in the downloaded data. Operator class is derived entirely from `Reporting_Airline` (`carrier_code` in this repo's fact tables), which is reliable for two of the three primary classes because Envoy Air (`MQ`) and PSA Airlines (`OH`) are wholly-owned American Airlines Group regional subsidiaries that operate exclusively under the American Eagle brand — a fact disclosed in American Airlines Group's own public corporate filings — so `carrier_code == MQ` or `OH` maps unambiguously to `Envoy_operated` / `PSA_operated` everywhere in the network, with no further disambiguation needed. `carrier_code == AA` maps unambiguously to `AA_mainline`.

Two carrier codes are genuinely ambiguous. SkyWest (`OO`) operates simultaneously as American Eagle, United Express, Delta Connection, **and** Alaska Airlines under separate capacity-purchase agreements — per SkyWest, Inc.'s FY2024 Form 10-K, this is a four-way split (~380/890/700/220 daily departures respectively), not the three-way split assumed earlier in this engagement. Republic Airways (`YX`) operates a comparable three-way split as American Eagle, United Express, and Delta Connection. BTS data alone cannot distinguish which contract a given `OO` or `YX` flight operated under; both are handled identically by the resolution pipeline below.

Resolution approach, in priority order:

1. **Route-context inference where unambiguous.** If a flight's route appears only in a pre-existing, already-validated route basket (e.g., the `aa_regional_basket` routes used in Fragility I–III), that basket assignment already implies the contract. This is a labeling convenience for already-known routes, not new information, and does not extend to markets outside a configured basket.
2. **Targeted FlightAware AeroAPI validation** (`scripts/15_resolve_operator_ambiguity.py`, new) for `OO`/`YX`-coded rows outside any pre-labeled basket. This reactivates the dormant FlightAware integration already present in this repo (`scripts/12_extract_flightaware.py`, gated by `use_flightaware` in `config/study.yaml`) in a **targeted validation** mode — querying specific ambiguous flights to resolve marketing/operating brand, not a bulk historical pull — consistent with the existing `flightaware_mode: "validation_only"` setting and with FlightAware's free-tier rate/volume limits.
3. **Unresolved fallback.** Any `OO`/`YX` row that cannot be resolved by (1) or (2) is labeled `SkyWest_unresolved` / `Republic_unresolved` rather than guessed. Unresolved rows are excluded from operator-class comparisons but retained in row counts and disclosed in the QA summary.

The carrier-code-to-class mapping is stored in `config/operator_classes.yaml`, dated and source-noted, in the shape this spec's own example anticipated.

**Equipment-type cross-check (not a primary classifier).** Regional-jet equipment (Embraer/Bombardier family) versus mainline equipment (Boeing/Airbus) is a directionally useful free cross-check — joining BTS `Tail_Number` to the FAA Releasable Aircraft Registry — but does not, by itself, resolve the SkyWest three-way contract ambiguity, since SkyWest flies similarly-sized regional jets for all three of its mainline partners. It is used only as (a) a validation check that `MQ`/`OH` rows are ~100% regional-jet equipment and `AA` rows are ~100% mainline equipment, and (b) a fleet-mix variable relevant to this spec's own "Mix effects" risk. It is not used to assign operator class.

### Hub-spoke market discovery

Rather than hand-enumerating spoke airports per hub, the hub-spoke expansion (Module B) downloads all BTS flights touching each configured hub airport and derives the spoke-market universe, operator mix, and route families directly from the data. This avoids presupposing which spokes exist or which operator serves them, consistent with this study's ab-initio framing, and is implemented as a new extraction path (`scripts/13_extract_bts_hubspoke.py`) that filters BTS PREZIP data to a configurable hub list rather than a fixed route list. It does not reuse or modify the existing 9-airport/14-route raw cache used by Fragility I–III (`data/raw/bts/`); hub-spoke data lands in a separate `data/raw/bts_hubspoke/` / `data/curated/hubspoke_operator_fact/` path so the existing studies' reproducibility carries zero risk from this work.

### Architecture and build location

This container builds and functionally validates the backend-abstracted code (pandas/duckdb/polars) and the `test` and `local` run modes, since neither requires GPU or large memory to validate correctness. The full-network, multi-year `bigrun` execution is reserved for the user's provisioned server (high-core-count, high-RAM, fast local SSD). Backend abstraction (`scripts/lib/backend.py`) is applied at the aggregation/scoring layer (script 33), where backend choice actually matters at scale; the ETL layer remains pandas-based, consistent with Fragility I–III, but writes Parquet (partitioned by `year_month`) instead of CSV for the new hub-spoke curated data.

Concrete run-mode definitions for this study:

| Mode | Hubs | Window | Notes |
|---|---|---|---|
| `test` | DFW only | 1 month | Container-safe validation slice |
| `local` | DFW, CLT, ORD, PHL | full study window (2024-01 – 2025-12) | Default for a normal workstation |
| `bigrun` | full configured network | all configured years | Reserved for the user's high-core/RAM server |

### Economic burden proxy baseline

Module A (focal corridor) reuses the existing Fragility III peer-carrier (UA/DL) baseline already built for that basket — no behavior change. Module B (hub-spoke expansion) has no pre-built UA/DL peer-route basket at each new hub, so its `economic_burden_proxy` uses baseline #3 (AA-system average across included operator classes in the same `hub_family × weather_bucket` cell) as the counterfactual. Both bases are disclosed by name wherever the metric is reported.

### Combined fragility score weights

Default weights are equal (`w1=w2=w3=w4=0.25`), configurable in `config/study.yaml`, consistent with this spec's "weights must be configurable and clearly documented" requirement. This is a default, not a claim that the four symptoms are equally material.

## Objective

Build a reproducible, operator-comparison analysis that answers: **Are AA-marketed flights operated by Envoy, PSA, or AA mainline materially different in weather fragility, controllable/cascade fragility, and implied economic burden, both in the focal corridor and in selected comparable hub-spoke portions of the network?**[cite:25][cite:156][cite:194]

This study should produce one executive-ready output graphic plus a short written result, while also generating reusable intermediate tables that support future network-wide hotspot work in Fragility V.[cite:25][cite:156]

## Target audiences and framing

### CEO and direct reports

At the CEO and ExCo level, the question is not “who is to blame,” but rather “where is the fragility concentrated, how material is it, and which parts of the organization must own improvement?”[cite:194][cite:197]

The output should therefore emphasize:

- concentration of fragility by operator,
- magnitude versus peer or system baselines,
- whether the issue appears local or systemic,
- whether the effect is operationally actionable.[cite:156][cite:194]

### Department and discipline leaders

This study should support action by:

- network planning,
- operations/IOC,
- finance/commercial,
- AA regional governance,
- Envoy and PSA executive leadership.[cite:156][cite:153]

Each of these groups should be able to see whether fragility appears associated with operator assignment, hub structure, time-of-day structure, controllable disruptions, or weather exposure.[cite:156][cite:70]

### Envoy and PSA leadership

For Envoy and PSA leadership, the study should be framed as a performance-attribution and improvement-opportunity lens, not as a prosecutorial document. The useful question is whether their operated markets show different observable fragility signatures than AA mainline and whether those signatures are localized to specific hubs, weather regimes, or schedule contexts.[cite:156][cite:153]

## Business question

Fragility IV should answer the following high-level questions:

1. Is the focal fragility pattern seen in the original corridor unique to that corridor, or does it recur in other Envoy- or PSA-operated parts of the AA network?[cite:25][cite:70]
2. Are operator-level differences visible after grouping similar hub-spoke markets together?[cite:25]
3. Is there evidence that one operator class shows more weather sensitivity, more controllable disruption, more late-arriving cascade, or more economic burden than others?[cite:156][cite:194]
4. Do any such differences appear concentrated in specific hubs, banks, or corridor families?[cite:25][cite:70]

## Scope

### Primary comparison classes

Classify AA-marketed flights into at least these buckets where data support the distinction:

- `AA_mainline`
- `Envoy_operated`
- `PSA_operated`
- optionally `Other_regional_AA_partner` if the implemented repo finds meaningful volume there.[cite:25][cite:219]

The study should use BTS operating-carrier or reporting-carrier fields to separate operator classes. BTS explicitly distinguishes reporting and marketing carrier perspectives, and on-time data include regional code-share partners.[cite:25][cite:19][cite:219]

### Geographic structure

This study should operate at two levels:

1. **Focal corridor replication** — the existing LFT/DFW and related Gulf/South corridor baskets used in Fragility I–III.[cite:25]
2. **Selected hub-spoke expansion** — a defined set of additional AA hubs and spoke families where Envoy, PSA, and AA mainline can be compared without exploding scope.[cite:25]

Recommended initial hub set:

- DFW
n- CLT
- ORD
- PHL
- optionally MIA or DCA if operator coverage is sufficient.[cite:25]

### Time window

Reuse the study windows from earlier Fragility work unless the repository has already generalized them.[cite:5][cite:25]

### Out of scope

- Direct causal claims about training, crew minima, scheduling logic, or maintenance practices.[cite:156]
- Passenger-itinerary-level revenue attribution.[cite:195][cite:196]
- Full-network hotspot discovery; that is Fragility V.[cite:25]

## Source data

### Required reused data

This study should reuse existing outputs wherever possible:

- BTS flight-level fact table from Fragility I/II.[cite:25][cite:17]
- FAA weather-bucket outputs from Fragility I.[cite:70][cite:135]
- Controllable/cascade classifications from Fragility II.[cite:156]
- Economic proxy outputs or logic from Fragility III.[cite:194][cite:197]

### Required BTS fields

At minimum, the underlying fact table must preserve:

- `Reporting_Airline` / `Marketing carrier` perspective if used in the repo,
- `Operating_Airline` or equivalent operator identifier,
- `Origin`, `Dest`, `FlightDate`,
- scheduled and actual times,
- cancellation and cause fields,
- delay-cause minute fields.[cite:25][cite:19][cite:156]

## Analytical framing

Fragility IV should compare operator classes using the same underlying fragility dimensions already established:

- **Weather fragility** from Fragility I.[cite:70][cite:135]
- **Controllable and cascade fragility** from Fragility II.[cite:156][cite:153]
- **Economic burden proxy** from Fragility III.[cite:194][cite:197]

The additive value of Fragility IV is not inventing new metrics, but assigning those metrics to operator classes in a way that leadership can use.[cite:156][cite:194]

## Core hypotheses

### Primary hypothesis

Observable fragility is not distributed uniformly across AA’s operating structure; some combination of operator class, hub, and corridor family likely carries a disproportionate share of the most relevant delay/cancellation spikes.[cite:25][cite:156]

### Secondary hypothesis

If operator-level differences exist, they may be most visible under schedule stress, such as marginal weather, peak hub banks, or short-haul spoke operations, rather than uniformly across all markets.[cite:70][cite:156]

### Explicit limitation

Even if operator-level differences are observed, the study must not assert the underlying cause. It may suggest areas that merit internal investigation, such as schedule design, crew-allocation rules, governance, or maintenance planning, but it cannot prove any of those from public data alone.[cite:156][cite:153]

## Derived operator classes

Create a standard operator mapping table, stored in config or reference data, that maps BTS carrier/operator codes into analysis classes.

Example structure:

```yaml
operator_classes:
  AA:
    class: AA_mainline
  MQ:
    class: Envoy_operated
  OH:
    class: PSA_operated
```

The final mapping must be verified against the BTS carrier/operator definitions actually present in the downloaded data.[cite:25][cite:19]

## Required metrics

For each `operator_class × hub_family × weather_bucket × period_flag`, compute at minimum:

- `flights_total`
- `cancelled_count`
- `operated_count`
- `severe_delay_count`
- `weather_fragility_rate`
- `controllable_cancel_rate`
- `controllable_severe_delay_rate`
- `late_arriving_severe_delay_rate`
- `combined_fragility_score`
- `economic_burden_proxy`[cite:70][cite:156][cite:194]

### Recommended combined fragility score

Create a transparent weighted score that combines the most decision-relevant operational symptoms. For example:

```text
combined_fragility_score =
  w1 * cancellation_rate +
  w2 * severe_delay_rate +
  w3 * controllable_severe_delay_rate +
  w4 * late_arriving_severe_delay_rate
```

Weights must be configurable and clearly documented. The study should not hide arbitrary choices.[cite:156][cite:194]

## Comparative baselines

The study should support at least three baselines:

1. **Within-AA operator comparison** — Envoy vs PSA vs AA mainline.[cite:25]
2. **Peer corridor comparison** — where the earlier studies already compare AA baskets with UA/DL peers.[cite:25]
3. **AA system baseline** — operator performance relative to AA-wide average in the included markets.[cite:25]

This allows both internal attribution and external competitive framing.[cite:194]

## Suggested analysis modules

Fragility IV is intentionally a bundle of related drill-down studies. It should therefore be implemented as one add-on with multiple analytic modules, even if only one executive graphic is required at the end.

### Module A: focal corridor operator comparison

Replicate Fragility I–III metrics within the original corridor families but slice by operator class. This preserves continuity with the original user problem.[cite:25][cite:70]

### Module B: selected hub-spoke operator comparison

For a defined list of hubs, compare operator classes across similar spoke markets, preferably short-haul and regional-style spoke corridors where comparison remains meaningful.[cite:25]

### Module C: optional time-of-day / bank sensitivity

If the existing repo already handles local times cleanly, allow an optional drill-down by bank or time-of-day to see whether operator differences cluster in specific parts of the operating day.[cite:25][cite:205]

This module is optional for phase 1 but should be architecturally feasible for later use.[cite:205]

## Chart specification

This study should produce **one executive-ready graphic** focused on operator attribution.

### Recommended chart

Use a **multi-panel grouped bar chart** or **dot-and-whisker comparison chart**.

Preferred structure:

- Panel A: weather fragility by operator class.
- Panel B: controllable severe-delay fragility by operator class.
- Panel C: late-arriving cascade fragility by operator class.
- Panel D: economic burden proxy per 1,000 flights or per study window by operator class.[cite:70][cite:156][cite:194]

The x-axis should be operator class, with color or small multiples by hub family or market family. If the chart becomes too dense, prioritize hub-family small multiples over operator-color complexity.[cite:25]

### Alternative chart

If density becomes unmanageable, use a **ranked scorecard chart** showing operator-hub combinations ranked by combined fragility score, with symbols or color denoting whether the signal is primarily weather, controllable, or cascade-driven.[cite:156][cite:194]

### Annotation

The annotation should answer the CEO-level question directly, for example:

- “Across the included AA network slices, Envoy-operated markets show the highest combined fragility score, driven primarily by controllable and cascade delays at DFW and CLT.”
- “Operator-level differences are modest systemwide, but specific hub/operator combinations account for most excess burden.”

The wording must be computed from actual results and must avoid causal overreach.[cite:156][cite:153][cite:194]

## Written result

Produce a short written result file:

- `output/fragility_iv_summary.md`

It should state:

1. Whether material operator differences are observed.
2. Which hubs or corridor families are most implicated.
3. Whether the dominant differences appear weather-related, controllable, or cascade-related.
4. Which potential action domains are suggested for internal follow-up: scheduling, governance, operator assignment, staffing, or operational resilience review.

The written result should stay constructive and outside-in.[cite:156][cite:194]

## Architecture and scalability requirements

This study must be implemented so that the coding agent can test it in a limited container, while the user can run a much larger analysis on a provisioned server.

### Run modes

Support at least:

- `test`
- `local`
- `bigrun`

Definitions:

- `test`: one or two months, one or two hubs, container-safe.
- `local`: moderate scope on a normal workstation.
- `bigrun`: selected full-network slices, multi-year if configured, intended for high-core/RAM hardware.

### Backend abstraction

Support a configurable analytics backend, with at least:

- `pandas`
- `duckdb`
- `polars`

A future GPU/distributed backend may be added later, but is not required for phase 1. The important requirement is that the code should not hardwire tiny-memory assumptions.[cite:220][cite:221]

### Storage format

Curated and staging data for this study should be written in Parquet wherever possible. DuckDB can query Parquet directly and efficiently on large datasets, which makes it suitable for single-node big-run execution on powerful hardware.[cite:220][cite:221]

### Scope controls

Every major script should accept filters such as:

- years,
- months,
- hubs,
- operator classes,
- route families,
- study modules,
- backend,
- run mode.

This allows identical logic to be validated in a tiny run and then executed at large scale on better hardware.[cite:220]

## Suggested scripts

The implementation may use separate scripts or extend a modular analysis framework, but conceptually it should add at least:

```text
scripts/
  33_analyze_fragility_operator.py
  43_plot_fragility_operator.py
```

If the repository has already evolved into a modular engine, these may become modes rather than standalone files.[cite:25]

## Output files

This study should produce at least:

- `output/fragility_iv_operator_chart_data.csv`
- `output/fragility_iv_operator_exec_chart.png`
- `output/fragility_iv_summary.md`
- optionally `output/fragility_iv_operator_scorecard.parquet` for downstream use in Fragility V.[cite:156][cite:194]

## QA requirements

Add the following QA checks:

- Verify operator-code mapping and row counts by operator class.[cite:25][cite:19]
- Verify weather-bucket reuse from Fragility I.[cite:70]
- Verify controllable/cascade field reuse from Fragility II.[cite:156]
- Confirm no operator class is being compared on trivially small sample sizes.
- Confirm any combined score weights are disclosed and loaded from config.
- Confirm big-run and test-run produce compatible schemas and metrics on overlapping slices.[cite:220]

## Risks and interpretation constraints

### Attribution is not causation

Observed operator differences may reflect network design, hub structure, assignment policy, schedule pressure, weather exposure, governance differences, or other latent factors. The study cannot isolate which of these is the root cause.[cite:156][cite:153]

### Mix effects

Operator classes may systematically serve different route lengths, hubs, or banks. The study should minimize apples-to-oranges comparisons by using corridor families and selected hub-spoke structures rather than raw systemwide averages alone.[cite:25]

### Over-density risk

A fully comprehensive operator/hub/time breakdown can become unreadable. The executive output should prioritize clarity, while detailed tables can remain as supporting artifacts.[cite:194]

## Definition of done

Fragility IV is complete when the repository can be rerun to produce a reproducible operator-attribution analysis showing whether Envoy, PSA, AA mainline, or other operator classes account for disproportionate shares of weather, controllable, cascade, or economic fragility in the included AA network slices, together with one executive-ready graphic and one short written summary.[cite:25][cite:156][cite:194]
