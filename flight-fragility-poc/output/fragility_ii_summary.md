# Fragility II: Controllable and Cascade Disruption — Summary

This summary reports whether the public-data signature of controllable (Air Carrier-coded) disruption and late-arriving-aircraft cascade disruption is higher, lower, or similar for the AA regional basket relative to the UA and DL peer baskets, and whether that signature strengthens under marginal or adverse weather. It does not identify which internal function (maintenance, crew, or another controllable factor) is responsible — see the spec's "Risks, threats to validity, and alternative explanations" section, item 7 below.

## 1–3. Controllable and cascade disruption by weather condition

| Weather | AA controllable severe-delay rate (n) | Peer-avg (n) | Combined-peer (n) | AA÷peer-avg | AA÷combined-peer |
|---|---|---|---|---|---|
| Benign | 2.60% (14266) | 3.46% | 3.20% (8697) | 0.75x | 0.81x |
| Marginal | 3.08% (1980) | 5.98% | 4.45% (1461) | 0.52x | 0.69x |
| Adverse | 4.48% (1183) | 6.08% | 4.76% (904) | 0.74x (provisional) | 0.94x (provisional) |

| Weather | AA late-arriving severe-delay rate (n) | Peer-avg (n) | Combined-peer (n) | AA÷peer-avg | AA÷combined-peer |
|---|---|---|---|---|---|
| Benign | 3.99% (14266) | 2.10% | 1.79% (8697) | 1.9x | 2.23x |
| Marginal | 4.80% (1980) | 3.80% | 3.08% (1461) | 1.26x | 1.56x |
| Adverse | 7.78% (1183) | 5.08% | 4.98% (904) | 1.53x (provisional) | 1.56x (provisional) |

Benign-to-adverse escalation in the late-arriving (cascade) severe-delay rate: AA regional 1.95x, combined peer basket 2.78x.

## 4. Cause-data caveat

BTS cause-code reporting does not distinguish maintenance from crew, fueling, ground handling, or other airline-controlled factors within the Air Carrier category, and carriers self-report the cause code for each delayed or cancelled flight. An elevated `controllable_*` rate is evidence of elevated airline-attributed disruption in the public data, not evidence about which specific internal function is responsible.

## 5. Sample sizes and low-confidence cells

The minimum-sample threshold used for this run is 30 operated flights per `market_bucket × weather_bucket × period_flag` cell. Flight-count denominators for each headline rate are shown in the tables above (in parentheses).

Cells below the minimum-sample threshold:

| Market bucket | Weather | Period | Flights total | Operated |
|---|---|---|---|---|
| ua_peer_basket | adverse | baseline | 32 | 30 |

**Data availability note**: BTS On-Time Performance extracts do not include a field literally named "operating carrier" distinct from the reporting carrier. For the routes in this study, however, the reporting carrier (`carrier_code`, BTS's `Reporting_Airline`) already identifies the regional partner operating the flight (MQ/Envoy, OH/PSA, OO/SkyWest), because regional carriers file their own on-time-performance reports under their own code even when the flight is sold and gated as American Eagle. Section 7 below uses that field to break out the controllable/cascade metrics by operator within each basket, addressing the spec's request to test whether an AA-basket effect concentrates in one regional partner or is spread across all of them.

## 6. Operator-level breakdown within baskets

BTS's `Reporting_Airline` field (`carrier_code` in the fact table) is the carrier that files the on-time-performance report for each flight. For these routes that is the regional partner itself, not "AA"/"UA"/"DL" — so it already provides operator-level granularity inside each route-defined basket, without a separate operating-carrier field. Periods (2024/2025) are combined here to keep cells above the minimum-sample threshold; this view cannot also be split by period.

**aa_regional_basket**

| Operator | Weather | Operated (n) | Controllable severe-delay rate | Late-arriving (cascade) severe-delay rate | Controllable cancel rate |
|---|---|---|---|---|---|
| Envoy Air (MQ) | Benign | 6021 | 1.33% | 3.39% | 0.10% |
| Envoy Air (MQ) | Marginal | 814 | 2.21% | 4.91% | 0.00% |
| Envoy Air (MQ) | Adverse | 483 | 1.86% | 8.90% | 0.19% |
| PSA Airlines (OH) | Benign | 4172 | 2.35% | 7.81% | 0.54% |
| PSA Airlines (OH) | Marginal | 559 | 2.68% | 8.94% | 0.99% |
| PSA Airlines (OH) | Adverse | 396 | 4.29% | 11.36% | 0.00% |
| SkyWest (OO) | Benign | 4073 | 4.74% | 0.96% | 0.00% |
| SkyWest (OO) | Marginal | 607 | 4.61% | 0.82% | 0.00% |
| SkyWest (OO) | Adverse | 304 | 8.88% | 1.32% | 0.29% |

**dl_peer_basket**

| Operator | Weather | Operated (n) | Controllable severe-delay rate | Late-arriving (cascade) severe-delay rate | Controllable cancel rate |
|---|---|---|---|---|---|
| Endeavor Air (9E) | Benign | 1953 | 1.43% | 2.15% | 0.56% |
| Endeavor Air (9E) | Marginal | 337 | 1.48% | 2.97% | 0.85% |
| Endeavor Air (9E) | Adverse | 193 | 2.59% | 7.77% | 0.99% |
| Delta mainline (DL) | Benign | 3282 | 1.68% | 1.95% | 0.72% |
| Delta mainline (DL) | Marginal | 575 | 3.13% | 3.83% | 1.02% |
| Delta mainline (DL) | Adverse | 365 | 1.64% | 5.48% | 1.84% |
| SkyWest (OO) | Benign | 1577 | 7.67% | 0.00% | 0.06% |
| SkyWest (OO) | Marginal | 286 | 6.99% | 0.00% | 0.00% |
| SkyWest (OO) | Adverse | 155 | 10.32% | 0.00% | 0.60% |

**ua_peer_basket**

| Operator | Weather | Operated (n) | Controllable severe-delay rate | Late-arriving (cascade) severe-delay rate | Controllable cancel rate |
|---|---|---|---|---|---|
| SkyWest (OO) | Benign | 1883 | 3.93% | 2.66% | 0.00% |
| SkyWest (OO) | Marginal | 263 | 8.37% | 4.94% | 0.00% |
| SkyWest (OO) | Adverse | 190 | 8.42% | 5.26% | 0.00% |
| United mainline (UA) | Benign | 2 * | 0.00% | 0.00% | 0.00% |
| United mainline (UA) | Adverse | 1 * | 0.00% | 0.00% | 0.00% |

\* low-confidence row (operated flights at or below the minimum-sample threshold).

SkyWest (OO) appears in all three baskets under a different mainline contract in each. Comparing its row across the AA, DL, and UA tables above is the closest this study can get to separating an operator-wide SkyWest effect from an AA-contract-specific effect, per the spec's "Regional-operator overlap across baskets" risk. Envoy (MQ) and PSA (OH) fly only under the AA contract in this study's baskets, so there is no cross-contract comparison available for them here; any signature specific to either carrier cannot be distinguished from an AA-contract-specific effect using this data alone.

This breakdown is still subject to every caveat in section 4 and 7 below: cause codes are self-reported per flight by whichever carrier reports it, `controllable_*` does not isolate maintenance from crew or other factors, and `late_arriving_severe_delay_rate` reflects propagated disruption, not its original cause.

## 7. Threats to validity

See `flight_fragility_ii_machine_addon_spec.md`, section "Risks, threats to validity, and alternative explanations," for the full disclosure of this study's known limitations, including self-reported cause data, the SkyWest cross-contract overlap, the pre-registered route baskets, the definitional difference between this study's severe-delay measure and Fragility I's, and a list of non-causal explanations consistent with any observed gap. This summary should not be read without that section.
