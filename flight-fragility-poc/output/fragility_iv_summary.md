# Fragility IV: Operator Attribution — Summary

This summary compares observable fragility signals (weather sensitivity, controllable delay, late-arriving cascade delay, and an economic-burden proxy) across AA's operating structure — AA mainline, Envoy, PSA, and SkyWest/Republic under their resolved contracts — in the focal corridor and in the included hub-spoke network slices. It does not assert a cause for any observed difference; see `flight_fragility_iv_operator_attribution_spec.md`, "Risks and interpretation constraints," which this summary should not be read without.

## 1. Are material operator differences observed?

Across the included operator_class x hub_family cells, the weather-fragility-rate spread is 22.7% (highest minus lowest cell, pooled across weather conditions and study periods). Across the included AA network slices, PSA_operated at ORD shows the highest combined fragility score (0.187) among cells with at least 30 flights (186 flights in this cell).

## 2. Which hubs or corridor families are most implicated?

| Hub / corridor family | Mean weather fragility rate across operator classes |
|---|---|
| ORD | 13.3% |
| DFW | 13.0% |
| focal_corridor | 11.9% |
| PHL | 11.2% |
| DCA | 11.1% |
| JFK | 10.7% |
| MIA | 10.2% |
| CLT | 9.9% |
| PHX | 6.2% |
| LAX | 6.1% |

## 3. Weather-related, controllable, or cascade-driven?

Of the three component rates averaged across included cells, **Weather (overall fragility)** is highest (10.7%). This indicates where the included data concentrate, not which underlying cause produced it.

## 4. Suggested follow-up domains

- Network planning and AA regional governance, if differences concentrate by hub or corridor family rather than spreading evenly.
- Operations/IOC, if late-arriving cascade delay dominates over controllable delay.
- Envoy/PSA/SkyWest/Republic executive leadership, framed as a performance-attribution and improvement-opportunity review, not a prosecutorial finding.
- Finance/commercial, for the economic-burden-proxy magnitude specifically.

## 5. QA notes

- 30 operator/hub/weather/period cells have fewer than 30 flights (min_sample_threshold) — treat their rates as indicative only.
- 904,924 flights remain in an unresolved operator-ambiguity label (SkyWest_unresolved / Republic_unresolved) and are excluded from operator-class comparisons; see scripts/15_resolve_operator_ambiguity.py.
- combined_fragility_score weights used: {'w1_cancellation_rate': 0.25, 'w2_severe_delay_rate': 0.25, 'w3_controllable_severe_delay_rate': 0.25, 'w4_late_arriving_severe_delay_rate': 0.25}
- Modules present: ['focal_corridor', 'hub_spoke']
- All four combined_fragility_score components use flights_total as their denominator (unconditional probability over the full scheduled sample). This ensures the weighted sum compares outcomes over the same sample space for every component.
- Module B economic baseline (aa_system_average) pools all resolved operator classes within the same hub×weather×period cell — it is NOT leave-one-out. High-volume operators with above-average fragility partially suppress their own excess signal against this baseline.

## 6. Caveats

- Attribution is not causation: observed differences may reflect network design, hub structure, assignment policy, schedule pressure, weather exposure, governance differences, or other latent factors this study cannot isolate.
- Mix effects: operator classes may systematically serve different route lengths, hubs, or banks; this study minimizes apples-to-oranges comparison via corridor families and selected hub-spoke structures, but cannot eliminate it entirely.
- SkyWest_unresolved / Republic_unresolved rows are excluded from operator-class comparisons (see QA notes above) pending targeted FlightAware validation.
- The economic-burden proxy uses the same published-benchmark, scenario-based methodology as Fragility III (base scenario only here) — not audited financials.
