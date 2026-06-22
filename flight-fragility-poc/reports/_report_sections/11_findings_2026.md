## 10. Findings: 2026 Carve-out

The 2026 carve-out tests whether the network-wide and corridor-level patterns documented in Sections 9 and 10 (above) persist into the most recent data. As of the June 2026 compile date, BTS had published On-Time Performance for January through April 2026 only. To avoid contaminating the committed main-study artifacts, this carve-out was run as a separate split (`baseline = 2024–25`, `recent = 2026`) writing to distinct `*_2026` curated paths. Because a four-month window is winter-heavy and not comparable to a full calendar year, **every 2026 figure here is season-matched**: 2026 (Jan–Apr) is compared only against the same January–April months of 2024 and 2025. This removes the seasonal-weather bias that would otherwise inflate 2026 against an all-year baseline. The caveat in Section 12 still applies: four months is a partial sample, and cell-level weather-stratified counts fall to tens of flights and are treated as directional rather than precise.

![Is 2026 any better? No](output/exec/A3_is_2026_better.png)

### Network-wide operator trends (season-matched)

The operator ordering established over 2024–25 held, and on several measures deteriorated. PSA remained the worst-performing operator class and worsened on both headline metrics; Envoy remained the cleanest and was essentially flat.

| Operator (season-matched Jan–Apr) | Cancellation 2024–25 → 2026 | Severe-delay 2024–25 → 2026 |
|---|---|---|
| **PSA_operated** | 4.2% → **6.3%** | 9.5% → **11.2%** |
| **Envoy_operated** | 2.4% → 2.7% | 6.3% → 6.6% |
| **AA_mainline** | 1.5% → **3.4%** | (delay rate held) |

Two points deserve emphasis. First, the divergence between the two wholly-owned regional subsidiaries — PSA worsening, Envoy stable and benign — is the same fairness-preserving split seen in the main study, now reproduced in an independent time window. Second, AA mainline cancellations **more than doubled** (1.5% → 3.4%) while its severe-delay rate held roughly constant. A doubling of the cancellation rate with a flat delay rate is consistent with a shift in disruption-handling posture (cancelling earlier rather than running deeply late) rather than a broad operational collapse; the available public data cannot distinguish the mechanism, so this is reported as an observation, not an explanation.

### Hub trends (season-matched)

The hub ranking was equally persistent. The two worst severe-delay hubs in the main study not only stayed worst but climbed, while the cleanest high-volume hubs stayed clean.

| Hub | Severe-delay 2024–25 → 2026 |
|---|---|
| **ORD** (Chicago O'Hare) | 9.3% → **11.6%** |
| **DCA** (Washington National) | 9.1% → **10.5%** |
| LAX / PHX | ~5.5–5.9% (cleanest, stable) |

ORD and DCA — the same two hubs that anchor the top-20 hotspot concentration (Section 9) — are the top two on this metric and both rising. LAX and PHX, the largest new hubs by traffic, remained the cleanest, reaffirming that volume is not fragility into 2026.

### The DFW–LFT corridor: a mix-shift, not a single-operator decline

The focal corridor requires careful reading, because the corridor-level number and the operator-level number tell different stories, and conflating them would misstate the finding.

| DFW–LFT (season-matched Jan–Apr) | Disruption rate 2024–25 → 2026 |
|---|---|
| **Corridor (all operators)** | 15.1% → **16.8%** |
| **PSA only** | 17.1% → **17.7%** |

PSA's own performance on the corridor was nearly flat (17.1% → 17.7%). The corridor-wide deterioration to 16.8% is driven **chiefly by a change in who flies the route**, not by any single operator degrading. The corridor shifted from roughly 42% PSA operation toward approximately 89% PSA — Envoy, historically a major operator here, all but exited by late 2025 (the 2026 monthly counts in the focal report show Envoy at 10, 32, 14, then 0 flights Jan–Apr). Because more of the corridor's flights now sit with its least-reliable operator, the blended corridor rate rises even though that operator barely moved. This is a compositional effect, and we label it as such. Separately, corridor-wide knock-on (late-arriving-aircraft) cascade delay rose approximately **39%** season-matched, and PSA's bad-weather cancellations roughly doubled (≈11% → ≈24%) — but the latter rests on only ~51 adverse-weather PSA flights in the 2026 window and is explicitly directional.

### Reading the carve-out

Season-matched, 2026 shows **no improvement**. The network-level signal — PSA worst and worsening, Envoy stable, ORD and DCA climbing, the clean hubs staying clean — is well-sampled and reproduces the main study in fresh data. The corridor-level signal is real but compositional: DFW–LFT got worse for the traveler primarily because the route consolidated onto its weakest operator. The four-month, winter-weighted nature of the window means the network aggregates carry far more weight than any weather-stratified cell figure, and none of the carve-out's small-sample numbers are presented as precise.
