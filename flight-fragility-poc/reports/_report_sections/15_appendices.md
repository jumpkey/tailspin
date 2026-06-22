## 14. Appendices

### Appendix A — Data Dictionary (curated fact-table columns)

The Fragility V cell-level table is the analytic core. Each row is one `(hub_family, spoke_airport, operator_class)` cell aggregated over the main study window (Jan 2024–Dec 2025). Key columns:

| Column | Meaning |
|---|---|
| `hub_family` | One of the 9 AA hubs (origin-priority attribution; see §5). |
| `spoke_airport` | The non-hub endpoint of the market. |
| `operator_class` | Attributed operator: `AA_mainline`, `Envoy_operated`, `PSA_operated`, `SkyWest_unresolved`, `Republic_unresolved`, or `Other_or_non_AA`. |
| `flights_total` | All scheduled flights in the cell — the single shared denominator for every composite component (AAR Iteration 9 standardization). |
| `operated_count` / `cancelled_count` | Flights operated vs. cancelled. |
| `severe_delay_count` | Arrivals 60+ min late (DOT standard). |
| `controllable_severe_delay_count` | Subset of severe delays attributed to carrier-controllable BTS cause codes. |
| `late_arriving_severe_delay_count` / `cascade_delay_count` | Severe delays propagated from a late inbound aircraft (cascade). |
| `carrier_delay_min_sum`, `late_aircraft_delay_min_sum` | Summed BTS delay minutes feeding the economic-burden proxy. |
| `cancellation_rate`, `severe_delay_rate`, `controllable_severe_delay_rate`, `late_arriving_severe_delay_rate` | Counts ÷ `flights_total`. |
| `adv_flights`, `adverse_weather_fragility_rate` | Flights in adverse weather hours and their cancelled-or-delayed share (weather assigned at endpoint airport-hours, not en route). |
| `economic_burden_per_1k` | Absolute-cost proxy per 1,000 flights, pooled `aa_system_average` baseline (conservative; not leave-one-out). |
| `norm_*` (6 columns) | Percentile-rank normalizations of the six components; `norm_weather_sensitivity` is `NaN` when below the adverse-flight gate. |
| `hotspot_score_base` + 3 scenario scores | Equal-weighted composite and 3 alternate weightings. |
| `hotspot_robustness_score` | Fraction of scenarios in which the cell remains top-N. |
| `meets_min_flights`, `meets_min_adv_flights`, `is_persistent` | Eligibility and stability flags. |

### Appendix B — Fragility V Top-20 Hotspot Cells

Reproduced from `output/fragility_v_hotspot_rankings.csv` (1,668 of 2,093 cells meet the 100-flight ranking threshold). Robustness = share of weighting scenarios in which the cell is top-N; Persistent = top-N in both baseline and recent sub-periods.

| Rank | Hub | Spoke | Operator | Base Score | Robustness | Persistent |
|---|---|---|---|---|---|---|
| 1 | ORD | SPI | SkyWest_unresolved | 0.9823 | 1.00 | No |
| 2 | ORD | ORF | PSA_operated | 0.9797 | 1.00 | No |
| 3 | ORD | CAK | PSA_operated | 0.9754 | 1.00 | No |
| 4 | ORD | TYS | PSA_operated | 0.9746 | 1.00 | No |
| 5 | ORD | GSP | PSA_operated | 0.9699 | 1.00 | No |
| 6 | ORD | MGW | SkyWest_unresolved | 0.9689 | 1.00 | No |
| 7 | DFW | SBN | PSA_operated | 0.9588 | 1.00 | No |
| 8 | ORD | CID | AA_mainline | 0.9562 | 1.00 | No |
| 9 | DFW | CID | AA_mainline | 0.9549 | 1.00 | Yes |
| 10 | CLT | GPT | Envoy_operated | 0.9517 | 1.00 | No |
| 11 | MIA | MKE | AA_mainline | 0.9429 | 1.00 | No |
| 12 | DFW | ICT | AA_mainline | 0.9425 | 1.00 | No |
| 13 | DCA | LAN | PSA_operated | 0.9385 | 1.00 | No |
| 14 | DFW | CRP | PSA_operated | 0.9377 | 1.00 | No |
| 15 | ORD | TVC | SkyWest_unresolved | 0.9352 | 0.75 | No |
| 16 | DFW | CVG | PSA_operated | 0.9300 | 0.75 | No |
| 17 | DCA | CVG | PSA_operated | 0.9255 | 0.50 | No |
| 18 | DFW | GNV | PSA_operated | 0.9238 | 0.50 | No |
| 19 | DFW | LBB | AA_mainline | 0.9216 | 0.50 | No |
| 20 | DFW | LIT | AA_mainline | 0.9191 | 0.50 | No |

Only ORD-CID (rank 9, AA_mainline) is flagged persistent; ranks 1–14 carry full robustness (1.00), ranks 15–20 degrade. Per the §7 caveat, robustness and persistence are stronger prioritization signals than base rank alone (winner's-curse risk in a 20-from-1,668 list).

### Appendix C — QA Summary

From `output/qa_summary_hubspoke.csv`. Total flights: **6,152,599**. Weather-match null rate: **0.0%** (100.0% match).

**Operator-class counts**

| Operator class | Flights | Share |
|---|---|---|
| Other_or_non_AA | 2,258,693 | 36.7% |
| AA_mainline | 1,943,962 | 31.6% |
| SkyWest_unresolved | 606,125 | 9.9% |
| Envoy_operated | 568,329 | 9.2% |
| PSA_operated | 476,691 | 7.7% |
| Republic_unresolved | 298,799 | 4.9% |

Unresolved ambiguity (SkyWest + Republic) totals **904,924 flights (14.7%)**, excluded from operator comparisons rather than guessed (§5).

**Hub-family flight counts** (origin-priority; not cross-run-mode comparable)

| Hub | Flights |
|---|---|
| DFW | 1,186,156 |
| ORD | 1,131,482 |
| CLT | 770,451 |
| PHX | 722,022 |
| LAX | 686,522 |
| DCA | 518,567 |
| JFK | 400,577 |
| MIA | 382,727 |
| PHL | 354,095 |

### Appendix D — Glossary

- **Fragility** — Susceptibility of a market-operator cell to cancellation/severe-delay disruption, expressed as a composite of six normalized components. Association, not causation.
- **Severe delay** — Arrival 60+ minutes late (DOT standard). The shared composite denominator is all scheduled flights.
- **Controllable delay** — Severe delay attributed to carrier-controllable BTS cause codes (self-reported).
- **Cascade (late-arriving) delay** — Severe delay propagated from a late inbound aircraft; a strict subset of severe delay.
- **Weather sensitivity** — Ratio of fragility in adverse vs. good weather hours (a multiplier), distinct from the absolute adverse-weather rate.
- **Economic burden** — Absolute-cost proxy from pooled DOT block-cost benchmarks; conservative (not peer-relative).
- **Hotspot cell** — A `(hub, spoke, operator_class)` unit scored by the composite index.
- **Composite hotspot score** — Six equal-weighted percentile-rank components; tested against 3 alternate weightings.
- **Robustness score** — Fraction of weighting scenarios in which a cell stays top-N (1.00 = stable across all).
- **Persistence** — Cell ranks top-N independently in both the baseline and recent sub-periods.
- **Season-matched** — Comparing 2026 Jan–Apr only against the same Jan–Apr months of 2024–25, controlling for winter-heavy seasonality in the partial-year sample.
- **Over-representation multiplier** — An operator's share of worst cells ÷ its share of flights (1.0 = neutral).
- **Unresolved operator** — SkyWest/Republic codeshare rows whose operating carrier could not be disambiguated from public data; scored at cell level but excluded from operator rollups.
