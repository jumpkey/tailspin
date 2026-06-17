# Fragility V: Network Hotspot Scorecard — Prioritization Memo

This memo summarizes which hub-spoke market-operator cells are associated with the highest composite fragility signal across AA's regional network structure. Findings reflect observed patterns in BTS on-time performance data; they do not assert operational causation. All rates are consistent with, not necessarily caused by, the factors named. See the QA notes section for data-quality caveats.

## 1. Top-ranked cells by base hotspot score

The hotspot engine scores 1,304 distinct (hub, spoke, operator_class) cells. Of these, 1,070 meet the minimum-flights threshold (100 flights) required for normalization and ranking.

Top-20 cells by base hotspot score:

| Rank | Cell | Hub | Spoke | Operator | Base Score | Robustness | Persistent |
|---|---|---|---|---|---|---|---|
| 1 | ORD-SPI SkyWest_unresolved | ORD | SPI | SkyWest_unresolved | 0.9778 | 1.00 | No |
| 2 | ORD-ORF PSA_operated | ORD | ORF | PSA_operated | 0.9705 | 1.00 | No |
| 3 | ORD-CAK PSA_operated | ORD | CAK | PSA_operated | 0.9689 | 1.00 | No |
| 4 | ORD-TYS PSA_operated | ORD | TYS | PSA_operated | 0.9636 | 1.00 | No |
| 5 | ORD-MGW SkyWest_unresolved | ORD | MGW | SkyWest_unresolved | 0.9600 | 1.00 | No |
| 6 | DFW-CID AA_mainline | DFW | CID | AA_mainline | 0.9482 | 1.00 | Yes |
| 7 | DFW-SBN PSA_operated | DFW | SBN | PSA_operated | 0.9422 | 1.00 | No |
| 8 | DFW-ICT AA_mainline | DFW | ICT | AA_mainline | 0.9326 | 1.00 | Yes |
| 9 | ORD-TVC SkyWest_unresolved | ORD | TVC | SkyWest_unresolved | 0.9234 | 1.00 | No |
| 10 | DFW-CRP PSA_operated | DFW | CRP | PSA_operated | 0.9172 | 0.75 | No |
| 11 | ORD-FWA PSA_operated | ORD | FWA | PSA_operated | 0.9159 | 0.75 | No |
| 12 | DFW-GNV PSA_operated | DFW | GNV | PSA_operated | 0.9159 | 0.75 | Yes |
| 13 | DFW-MLI PSA_operated | DFW | MLI | PSA_operated | 0.9079 | 0.50 | No |
| 14 | ORD-DAY PSA_operated | ORD | DAY | PSA_operated | 0.9023 | 0.75 | No |
| 15 | DFW-LBB AA_mainline | DFW | LBB | AA_mainline | 0.9018 | 0.75 | No |
| 16 | DFW-STL SkyWest_unresolved | DFW | STL | SkyWest_unresolved | 0.9000 | 1.00 | No |
| 17 | DFW-LIT AA_mainline | DFW | LIT | AA_mainline | 0.8996 | 0.50 | No |
| 18 | ORD-COU SkyWest_unresolved | ORD | COU | SkyWest_unresolved | 0.8920 | 0.25 | No |
| 19 | DFW-ECP AA_mainline | DFW | ECP | AA_mainline | 0.8901 | 0.75 | No |
| 20 | PHL-XNA PSA_operated | PHL | XNA | PSA_operated | 0.8901 | 0.50 | No |

## 2. Hub concentration in top-N

| Hub | Cells in top-N | Share | Total flights |
|---|---|---|---|
| DFW | 10 | 50.0% | 10,119 |
| ORD | 9 | 45.0% | 7,051 |
| PHL | 1 | 5.0% | 706 |

## 3. Operator concentration in top-N (resolved operators only)

| Operator class | Cells in top-N | Share | Total flights |
|---|---|---|---|
| PSA_operated | 10 | 66.7% | 4,683 |
| AA_mainline | 5 | 33.3% | 8,765 |

## 4. Dominant fragility signal

Among the top-N cells, the highest normalized component per cell is distributed as follows (a cell's dominant component is the one with the highest percentile rank in that cell):

- **economic_burden**: 7 cell(s)
- **cascade**: 5 cell(s)
- **severe_delay**: 4 cell(s)
- **cancel**: 2 cell(s)
- **controllable**: 1 cell(s)
- **weather_sensitivity**: 1 cell(s)

## 5. QA notes

- Total cells: 1,304; cells meeting min_flights=100: 1,070.
- Operator classes included in scoring: ['AA_mainline', 'Envoy_operated', 'PSA_operated', 'Republic_unresolved', 'SkyWest_unresolved'].
- Hubs in scope: ['CLT', 'DFW', 'ORD', 'PHL'].
- Spoke airports in scope: 239 distinct airports.
- Persistent cells (top-20 in both baseline and recent periods): 3.
- Scenario names: ['base', 'weather_emphasis', 'controllable_cascade_emphasis', 'economic_emphasis'].
- Dominant component distribution in top-20: {'economic_burden': 7, 'cascade': 5, 'severe_delay': 4, 'cancel': 2, 'controllable': 1, 'weather_sensitivity': 1}.
- Operator rollup (resolved operators only, top-20): [{'operator_class': 'PSA_operated', 'hotspot_count': 10, 'total_flights_in_top_n': 4683, 'share_of_top_n': 0.6666666666666666}, {'operator_class': 'AA_mainline', 'hotspot_count': 5, 'total_flights_in_top_n': 8765, 'share_of_top_n': 0.3333333333333333}].
- Hub rollup (top-20): [{'hub_family': 'DFW', 'hotspot_count': 10, 'total_flights_in_top_n': 10119, 'share_of_top_n': 0.5}, {'hub_family': 'ORD', 'hotspot_count': 9, 'total_flights_in_top_n': 7051, 'share_of_top_n': 0.45}, {'hub_family': 'PHL', 'hotspot_count': 1, 'total_flights_in_top_n': 706, 'share_of_top_n': 0.05}].

## 6. Caveats

- The hotspot score is a composite index based on six normalized components. Equal weights in the base scenario treat all components as equally important; alternative weighting scenarios test robustness.
- Cells with fewer than the minimum-flights threshold are excluded from normalization and ranking but are retained in the output Parquet for completeness.
- SkyWest_unresolved and Republic_unresolved are included in hotspot scoring but excluded from the operator-concentration rollup (Module B), where ambiguous attribution would distort the operator-level count.
- Other_or_non_AA rows (non-AA carriers sharing BTS reporting at these airports) are excluded entirely from hotspot computation.
- Economic burden is an absolute-cost proxy (not excess vs. a peer baseline) using published DOT block-cost benchmarks. It is not sourced from airline financials.
