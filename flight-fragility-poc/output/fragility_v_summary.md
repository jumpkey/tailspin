# Fragility V: Network Hotspot Scorecard — Prioritization Memo

This memo summarizes which hub-spoke market-operator cells are associated with the highest composite fragility signal across AA's regional network structure. Findings reflect observed patterns in BTS on-time performance data; they do not assert operational causation. All rates are consistent with, not necessarily caused by, the factors named. See the QA notes section for data-quality caveats.

## 1. Top-ranked cells by base hotspot score

The hotspot engine scores 2,093 distinct (hub, spoke, operator_class) cells. Of these, 1,668 meet the minimum-flights threshold (100 flights) required for normalization and ranking.

Top-20 cells by base hotspot score:

| Rank | Cell | Hub | Spoke | Operator | Base Score | Robustness | Persistent |
|---|---|---|---|---|---|---|---|
| 1 | ORD-SPI SkyWest_unresolved | ORD | SPI | SkyWest_unresolved | 0.9823 | 1.00 | No |
| 2 | ORD-ORF PSA_operated | ORD | ORF | PSA_operated | 0.9797 | 1.00 | No |
| 3 | ORD-CAK PSA_operated | ORD | CAK | PSA_operated | 0.9754 | 1.00 | No |
| 4 | ORD-TYS PSA_operated | ORD | TYS | PSA_operated | 0.9746 | 1.00 | No |
| 5 | ORD-GSP PSA_operated | ORD | GSP | PSA_operated | 0.9699 | 1.00 | No |
| 6 | ORD-MGW SkyWest_unresolved | ORD | MGW | SkyWest_unresolved | 0.9689 | 1.00 | No |
| 7 | DFW-SBN PSA_operated | DFW | SBN | PSA_operated | 0.9588 | 1.00 | No |
| 8 | ORD-CID AA_mainline | ORD | CID | AA_mainline | 0.9562 | 1.00 | No |
| 9 | DFW-CID AA_mainline | DFW | CID | AA_mainline | 0.9549 | 1.00 | Yes |
| 10 | CLT-GPT Envoy_operated | CLT | GPT | Envoy_operated | 0.9517 | 1.00 | No |
| 11 | MIA-MKE AA_mainline | MIA | MKE | AA_mainline | 0.9429 | 1.00 | No |
| 12 | DFW-ICT AA_mainline | DFW | ICT | AA_mainline | 0.9425 | 1.00 | No |
| 13 | DCA-LAN PSA_operated | DCA | LAN | PSA_operated | 0.9385 | 1.00 | No |
| 14 | DFW-CRP PSA_operated | DFW | CRP | PSA_operated | 0.9377 | 1.00 | No |
| 15 | ORD-TVC SkyWest_unresolved | ORD | TVC | SkyWest_unresolved | 0.9352 | 0.75 | No |
| 16 | DFW-CVG PSA_operated | DFW | CVG | PSA_operated | 0.9300 | 0.75 | No |
| 17 | DCA-CVG PSA_operated | DCA | CVG | PSA_operated | 0.9255 | 0.50 | No |
| 18 | DFW-GNV PSA_operated | DFW | GNV | PSA_operated | 0.9238 | 0.50 | No |
| 19 | DFW-LBB AA_mainline | DFW | LBB | AA_mainline | 0.9216 | 0.50 | No |
| 20 | DFW-LIT AA_mainline | DFW | LIT | AA_mainline | 0.9191 | 0.50 | No |

## 2. Hub concentration in top-N

| Hub | Cells in top-N | Share | Total flights |
|---|---|---|---|
| DFW | 8 | 40.0% | 8,305 |
| ORD | 8 | 40.0% | 5,791 |
| DCA | 2 | 10.0% | 4,344 |
| CLT | 1 | 5.0% | 120 |
| MIA | 1 | 5.0% | 187 |

## 3. Operator concentration in top-N (resolved operators only)

| Operator class | Cells in top-N | Share | Total flights |
|---|---|---|---|
| PSA_operated | 10 | 58.8% | 7,279 |
| AA_mainline | 6 | 35.3% | 7,608 |
| Envoy_operated | 1 | 5.9% | 120 |

## 4. Dominant fragility signal

Among the top-N cells, the highest normalized component per cell is distributed as follows (a cell's dominant component is the one with the highest percentile rank in that cell):

- **unknown**: 10 cell(s)
- **economic_burden**: 3 cell(s)
- **weather_sensitivity**: 3 cell(s)
- **cascade**: 3 cell(s)
- **severe_delay**: 1 cell(s)

## 5. QA notes

- Total cells: 2,093; cells meeting min_flights=100: 1,668.
- Operator classes included in scoring: ['AA_mainline', 'Envoy_operated', 'PSA_operated', 'Republic_unresolved', 'SkyWest_unresolved'].
- Hubs in scope: ['CLT', 'DCA', 'DFW', 'JFK', 'LAX', 'MIA', 'ORD', 'PHL', 'PHX'].
- Spoke airports in scope: 249 distinct airports.
- Persistent cells (top-20 in both baseline and recent periods): 1.
- Scenario names: ['base', 'weather_emphasis', 'controllable_cascade_emphasis', 'economic_emphasis'].
- Dominant component distribution in top-20: {'unknown': 10, 'economic_burden': 3, 'weather_sensitivity': 3, 'cascade': 3, 'severe_delay': 1}.
- Operator rollup (resolved operators only, top-20): [{'operator_class': 'PSA_operated', 'hotspot_count': 10, 'total_flights_in_top_n': 7279, 'share_of_top_n': 0.5882352941176471}, {'operator_class': 'AA_mainline', 'hotspot_count': 6, 'total_flights_in_top_n': 7608, 'share_of_top_n': 0.35294117647058826}, {'operator_class': 'Envoy_operated', 'hotspot_count': 1, 'total_flights_in_top_n': 120, 'share_of_top_n': 0.058823529411764705}].
- Hub rollup (top-20): [{'hub_family': 'DFW', 'hotspot_count': 8, 'total_flights_in_top_n': 8305, 'share_of_top_n': 0.4}, {'hub_family': 'ORD', 'hotspot_count': 8, 'total_flights_in_top_n': 5791, 'share_of_top_n': 0.4}, {'hub_family': 'DCA', 'hotspot_count': 2, 'total_flights_in_top_n': 4344, 'share_of_top_n': 0.1}, {'hub_family': 'CLT', 'hotspot_count': 1, 'total_flights_in_top_n': 120, 'share_of_top_n': 0.05}, {'hub_family': 'MIA', 'hotspot_count': 1, 'total_flights_in_top_n': 187, 'share_of_top_n': 0.05}].

## 6. Caveats

- **Composite index**: The hotspot score aggregates six normalized percentile-rank components. Equal weights in the base scenario treat all components as equally important; four robustness scenarios span the space of alternative emphases.
- **Minimum-flight threshold**: Cells below the min-flights threshold are excluded from normalization and ranking; they are retained in the Parquet output for completeness.
- **Adverse-weather sample sparsity**: `norm_weather_sensitivity` is computed only from cells meeting the minimum adverse-flight threshold (`hotspot_min_adv_flights` in study.yaml). Cells below this threshold have `norm_weather_sensitivity = NaN` and are scored on the remaining five components only (weights renormalized). Without this gate, a cell with a handful of adverse flights and a perfect fragility rate on those flights would rank first — a classic small-sample upward bias.
- **Severe-delay definition inconsistency**: `severe_delay_flag` (used in `norm_severe_delay`) tests arrival delay ≥ threshold only. `controllable_severe_delay_flag` and `late_arriving_severe_delay_flag` (used in `norm_controllable` and `norm_cascade`) test departure OR arrival delay ≥ threshold. These components are not directly comparable; treat the composite score accordingly.
- **Persistence check and winner's curse**: The persistence flag marks cells that rank in the top-N in both the baseline and recent sub-periods independently. Only a small fraction of top-N cells are expected to be persistent: a top-N list of 20 drawn from 1,000+ cells will contain many cells whose rank is partly due to random variation (winner's curse). High robustness score (fraction of scenarios where the cell is top-N) is a stronger signal than base-scenario rank alone. Cells with high robustness AND persistence are the most defensible prioritization targets.
- **Persistence threshold**: Each sub-period uses `min_flights // 2` as its minimum-flight threshold (half the full-study threshold) so cells with adequate full-study coverage remain eligible after the period split.
- **SkyWest/Republic operator ambiguity**: SkyWest_unresolved and Republic_unresolved are included in hotspot scoring but excluded from the operator-concentration rollup (Module B). Their cell-level scores are valid but the operator label is ambiguous.
- **Economic burden**: Absolute-cost proxy using published DOT block-cost benchmarks, not excess vs. a peer baseline. It is not sourced from airline financials.
- **Non-AA carriers**: Other_or_non_AA rows are excluded entirely from hotspot scoring.
