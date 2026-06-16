# Fragility III: Economic Impact Estimation — Summary

This summary converts the excess disruption already measured by Fragility I (overall cancellation/delay) and Fragility II (controllable/cascade severe delay) into a scenario-based dollar-burden proxy, using published public cost benchmarks. It is **not** a passenger-itinerary revenue model and does not claim exact accounting loss — see `flight_fragility_iii_show_me_the_money_addon_spec.md`, "Risks and interpretation constraints," which this summary should not be read without.

## 1. Operational basis used

**Mode:** `fragility_ii_preferred` — excess controllable (carrier-attributed) + cascade (late-aircraft) delay minutes, BTS cause-minute fields.

Study window: 2024-01-01 to 2025-12-31 (both study periods combined). Excess is computed as AA regional's observed outcome minus the outcome AA would have produced at the UA/DL peer-average rate, applied to AA's own flight or operated-flight volume — i.e. excess burden relative to peer reliability, not total network cost.

| Component | Excess vs. peer-average rate (study window) |
|---|---|
| Cancellations | 270 flights |
| Controllable (carrier-attributed) delay minutes | -33,214 min |
| Cascade (late-aircraft) delay minutes | 52,106 min |
| **Net excess delay-minutes basis** | **18,891 min** |

The controllable component is negative — AA regional's carrier-attributed delay minutes run *below* what the peer-average rate would predict for AA's flight volume, consistent with Fragility II's controllable-rate finding. The cascade component is positive and larger in magnitude, so the two do not cancel out: the net excess-minutes basis is positive, driven by the cascade side. This is the same "controllable savings, cascade cost" pattern reported qualitatively in Fragility II, now expressed in minutes.

## 2. Base-case estimated excess burden

| | Airline operating-time burden | Passenger-time burden (flight-level proxy) | Combined |
|---|---|---|---|
| Base scenario (study window) | $1,903,477 | $90,975 | **$1,994,452** |

Base-case assumptions: passenger value of time $47.0/hour, airline block-time cost $100.76/minute, cancellation-equivalent burden 360 minutes per excess cancellation. See `config/economic_scenarios.yaml` and the spec's benchmark citations for sourcing.

## 3. Low / high sensitivity range

| Scenario | Airline operating-time burden | Passenger-time burden | Combined |
|---|---|---|---|
| Low | $1,511,296 | $48,838 | **$1,560,134** |
| Base | $1,903,477 | $90,975 | **$1,994,452** |
| High | $2,266,944 | $148,554 | **$2,415,498** |

The range reflects only the cost-coefficient assumptions (value of time, airline block-cost, cancellation-equivalent minutes) varying across scenarios; the underlying operational excess (cancellations, delay minutes) is held fixed across all three.

## 4. Weather-stratified view

| Weather | Net excess delay-minutes basis | Base-case combined burden |
|---|---|---|
| Benign | 35,496 min | $3,644,704 |
| Marginal | -10,152 min | $-1,011,677 |
| Adverse | -1,178 min | $-99,998 |

The pooled, study-window total above is positive, but that total is not evenly spread across weather conditions: nearly all of the net excess-minutes basis (and the dollar burden built on it) is concentrated in the *benign*-weather bucket, while the marginal- and adverse-weather buckets each run negative (AA's combined controllable+cascade minutes fall *below* the peer-average expectation once weather deteriorates). This is consistent with Fragility II's observation that AA regional's cascade severe-delay rate is already elevated in benign weather and escalates *less* with weather severity than peers' does — the economic burden this study can attach to that pattern, in other words, presents as a baseline/schedule-resilience cost rather than a weather-stress cost.

## 5. Caveats

- **Not a passenger-itinerary revenue model.** Public BTS data do not reveal who connected, who misconnected, who was reaccommodated overnight, or what fare or voucher outcomes occurred. The passenger-time burden above is a flight-level time-value proxy, not a reconstruction of actual passenger cost.
- **Flight-level burden, not passenger-count-scaled.** This run uses the spec's "Mode 1" flight-level burden framing: no passengers-per-flight multiplier is applied, because no passenger-manifest or seat-count data exists in this pipeline's public sources. The true passenger-time burden, if it could be estimated, would likely be a multiple of the passenger-time figure above (roughly the average passengers per flight) — this study does not estimate that multiplier rather than guess at one.
- **Proxy, not accounting.** These figures are scenario-based proxies built from published value-of-time and airline-delay-cost benchmarks. They are not audited revenue, voucher, hotel, or reaccommodation expense, and should not be read as exact lost revenue or cost-accounting impact.
- **Cancellation-equivalent minutes is a scenario lever, not an observed fact.** It stands in for the hidden delay and reaccommodation burden a cancellation creates, which BTS data cannot directly measure.
- All caveats from Fragility I and Fragility II (self-reported cause data, thin UA-basket samples, SkyWest cross-contract overlap, weather-bucket simplifications) propagate into this estimate, since it is built on those same underlying rates.
