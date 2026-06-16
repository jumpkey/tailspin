# Fragility II: Controllable and Cascade Disruption — Summary

This summary reports whether the public-data signature of controllable (Air Carrier-coded) disruption and late-arriving-aircraft cascade disruption is higher, lower, or similar for the AA regional basket relative to the UA and DL peer baskets, and whether that signature strengthens under marginal or adverse weather. It does not identify which internal function (maintenance, crew, or another controllable factor) is responsible — see the spec's "Risks, threats to validity, and alternative explanations" section, item 6 below.

## 1–3. Controllable and cascade disruption by weather condition

| Weather | AA controllable severe-delay rate (n) | Peer-avg (n) | Combined-peer (n) | AA÷peer-avg | AA÷combined-peer |
|---|---|---|---|---|---|
| Benign | 2.86% (14266) | 3.81% | 3.51% (8697) | 0.75x | 0.81x |
| Marginal | 3.18% (1980) | 6.02% | 4.52% (1461) | 0.53x | 0.7x |
| Adverse | 4.65% (1183) | 6.35% | 4.87% (904) | 0.73x (provisional) | 0.95x (provisional) |

| Weather | AA late-arriving severe-delay rate (n) | Peer-avg (n) | Combined-peer (n) | AA÷peer-avg | AA÷combined-peer |
|---|---|---|---|---|---|
| Benign | 4.43% (14266) | 2.55% | 2.22% (8697) | 1.74x | 2.0x |
| Marginal | 5.40% (1980) | 4.20% | 3.49% (1461) | 1.28x | 1.55x |
| Adverse | 8.11% (1183) | 5.48% | 5.31% (904) | 1.48x (provisional) | 1.53x (provisional) |

Benign-to-adverse escalation in the late-arriving (cascade) severe-delay rate: AA regional 1.83x, combined peer basket 2.39x.

## 4. Cause-data caveat

BTS cause-code reporting does not distinguish maintenance from crew, fueling, ground handling, or other airline-controlled factors within the Air Carrier category, and carriers self-report the cause code for each delayed or cancelled flight. An elevated `controllable_*` rate is evidence of elevated airline-attributed disruption in the public data, not evidence about which specific internal function is responsible.

## 5. Sample sizes and low-confidence cells

The minimum-sample threshold used for this run is 30 operated flights per `market_bucket × weather_bucket × period_flag` cell. Flight-count denominators for each headline rate are shown in the tables above (in parentheses).

Cells below the minimum-sample threshold:

| Market bucket | Weather | Period | Flights total | Operated |
|---|---|---|---|---|
| ua_peer_basket | adverse | baseline | 32 | 30 |

**Data availability note**: the spec for this add-on anticipated breaking out controllable and cascade metrics by operating/regional carrier within each basket (to test whether an AA-basket effect is concentrated in one regional partner or spread across all of them). The BTS On-Time Performance extract used in this study reports only the marketing/reporting carrier (already the basket-defining field — AA, UA, or DL) and does not include a separate operating-carrier identity field, so that breakout could not be implemented from this data source. The SkyWest cross-contract overlap documented in Fragility I therefore remains a qualitative, not a quantitative, finding in this study.

## 6. Threats to validity

See `flight_fragility_ii_machine_addon_spec.md`, section "Risks, threats to validity, and alternative explanations," for the full disclosure of this study's known limitations, including self-reported cause data, the SkyWest cross-contract overlap, the pre-registered route baskets, the definitional difference between this study's severe-delay measure and Fragility I's, and a list of non-causal explanations consistent with any observed gap. This summary should not be read without that section.
