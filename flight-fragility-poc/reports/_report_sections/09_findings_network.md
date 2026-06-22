## 8. Findings: Network-wide

This section reports the network-level results of the Fragility V hotspot engine over the full Jan 2024–Dec 2025 study window across American's nine-hub branded network. All figures are associations observed in public BTS on-time data, not causal claims; see §12 for the limitations that bound each statement.

### 8.1 The signal is distributed, concentrated, and stable

The hotspot engine scored **2,093** distinct (hub, spoke, operator-class) cells. Of these, **1,668** met the 100-flight minimum required for normalization and ranking; the remainder are retained but excluded from ranking. This matters for interpretation: fragility is not a single bad route or an anecdote. It is a *distributed* pattern measured across more than sixteen hundred markets, within which a measurable minority of cells carry disproportionate disruption.

Two stability checks support the ranking. First, scaling from the four-hub local baseline to the nine-hub national run (1.71× the flights, +2.6M records) did not move the core finding: the rank-1 hotspot remained **ORD–SPI** and the most fragile operator/weather cell remained PSA-at-ORD-adverse. Adding five hubs confirmed rather than diluted the signal. Second, each top cell carries a **robustness score** — the fraction of four alternate weighting scenarios under which the cell remains top-N — which is a stronger signal than base-scenario rank alone. The top six cells all hold robustness 1.00. Persistence (top-20 in both an early and late sub-period independently) is rarer and expected to be: only **1** of the top-20 cells (DFW–CID, AA_mainline) is flagged persistent, consistent with winner's-curse expectations for a 20-of-1,668 draw. We therefore lean on robustness, not single-period rank, when prioritizing.

### 8.2 One operator class is over-represented in the worst cells

![One operator flies 1 in 8 flights but half the worst trouble spots](output/exec/B1_one_operator_half_the_trouble.png)

The central network finding is an over-representation of **PSA_operated** cells among the worst-scoring cells, measured as the share of worst cells divided by the operator's share of all ranked flights (a lift of 1.0× means proportional; above 1.0× means over-represented).

| Operator class | Worst 5% (83 cells) | Worst 10% | Worst 25% | Share of ranked flights | Lift (worst 5%) |
|---|---|---|---|---|---|
| **PSA_operated** | **51.8%** | 43.7% | 33.3% | 12.2% | **4.25×** |
| AA_mainline | 31.3% | — | — | 50.0% | 0.63× |
| Envoy_operated | 2.4% | — | — | 14.6% | **0.16×** |

PSA flies roughly **1 in 8** ranked flights yet accounts for **more than half** of the worst 5% of cells — a 4.25× over-representation that persists, attenuating gradually, deeper into the distribution (3.58× at worst 10%, 2.73× at worst 25%). The pattern is corroborated by mean base score across the *entire* ranked universe, not just the tails:

| Operator class | Mean base hotspot score |
|---|---|
| PSA_operated | 0.683 |
| AA_mainline | 0.575 |
| SkyWest_unresolved | 0.487 |
| Republic_unresolved | 0.360 |
| Envoy_operated | 0.346 |

Two design features make this finding hard to dismiss as anti-regional bias. **Envoy and PSA are both wholly-owned American regional subsidiaries** flying as American Eagle under American's own schedule and brand — yet they land at opposite ends: PSA is over-represented (4.25×) while Envoy is the *most under-represented* class in the network (0.16×, and lowest mean score at 0.346). A finding that merely indicted "regional carriers" would implicate both; this one separates them. And AA_mainline is present throughout the worst cells (31.3% of the worst 5%) at roughly proportional-to-below levels (0.63×), so the mainline is neither shielded nor scapegoated. The signal is operator- and cell-specific. A further conservative bias works *against* the headline: the economic-burden component uses a pooled `aa_system_average` baseline rather than leave-one-out, which slightly suppresses a high-volume operator's own excess (§7), so PSA's true over-representation is, if anything, understated.

### 8.3 Volume does not predict fragility

![Size does not predict trouble](output/exec/B2_size_doesnt_predict_trouble.png)

Hub traffic and hub fragility are decoupled. The largest *new* hubs by volume — **LAX, PHX, and JFK** — contributed **zero** top-20 hotspots. Fragility instead concentrates in thin, short-haul regional spokes. Top-20 hub concentration:

| Hub | Cells in top-20 | Share | Flights in those cells |
|---|---|---|---|
| DFW | 8 | 40% | 8,305 |
| ORD | 8 | 40% | 5,791 |
| DCA | 2 | 10% | 4,344 |
| CLT | 1 | 5% | 120 |
| MIA | 1 | 5% | 187 |

DFW and ORD together hold 80% of the top-20. The CLT and MIA entries are small cells (120 and 187 flights) and should be read as indicative. A caveat applies to comparing hub *totals* across run modes: the origin-priority hub-attribution rule means nine-hub hub totals are not directly comparable to the four-hub run; cell-level rankings are unaffected (§5, §12).

### 8.4 DCA emerged; PHL exited

Two structural shifts appear at national scale relative to the four-hub baseline (where the top-20 split DFW 50 / ORD 45 / PHL 5). **DCA (Reagan National) newly emerged**, surfacing two top-20 cells (DCA–LAN and DCA–CVG, both PSA_operated), having been absent at four hubs. Conversely, **PHL dropped out** of the top-20 entirely. The change is partly attribution mechanics (more hubs absorb origin-priority assignment) and partly a genuine surfacing of DCA's thin-spoke exposure, but it is a clear caution against treating any single hub's prominence as fixed.

### 8.5 What drives the worst cells: cascade and economic burden, not weather

Examining the dominant (highest-percentile) component within each top-20 cell, the leading signatures are **economic_burden (3 cells)**, **cascade / late-arriving aircraft (3 cells)**, and **weather_sensitivity (3 cells)**, with one cell led by severe_delay; the remaining 10 are labelled "unknown" because they fall below the adverse-flight threshold needed to score weather sensitivity and are scored on the other five components. The substantive point is that **weather does not dominate the worst cells** — cascade and economic burden do — which is consistent with schedule and equipment-routing structure as much as with execution or weather exposure.

The **rank-1 cell is ORD–SPI** (Chicago–Springfield, IL), operator-class **SkyWest_unresolved**, with a base score of **0.982** and robustness **1.00** — identical to the four-hub baseline's rank-1. It illustrates two things at once: the signal's stability, and the cost of the operator-ambiguity exclusion. ORD–SPI carries the highest fragility score in the network, yet because SkyWest flies for multiple mainline brands, its operator label cannot be resolved from route context alone and it sits in the 14.7% conservatively excluded from operator comparisons (§5, §12). Twelve of the worst-83 cells share this limitation. We name the cell but, deliberately, not its contracting structure — a FlightAware AeroAPI key would resolve it, but the conservative exclusion is preserved here as a defensibility asset rather than guessed past.
