## 6. Methodology: Fragility Framework & Scoring

The fragility analysis was built incrementally as five numbered stages (Fragility I–V). Each stage answers a more general question than the last, and each reuses the metric definitions fixed in Section 6 (Weather & Metric Definitions). The progression is deliberate: it starts from a single, fully-auditable corridor and only widens scope once the narrower computation has been validated. Reviewers should treat the stages as nested, not independent — the network engine (V) is the corridor scorer (I–IV) applied across thousands of cells with the addition of cross-cell normalization.

### 6.1 The Fragility I–V progression

| Stage | Unit of analysis | Question answered |
|---|---|---|
| I | DFW–LFT focal corridor | Is the focal corridor measurably fragile, and by which raw rates? |
| II | Corridor × weather bucket | Does fragility concentrate in adverse weather? |
| III | Corridor × operator, with UA/DL peer baseline | Which operator carries the fragility, net of a peer-carrier benchmark? |
| IV | (operator × hub × weather × period) cells | A single `combined_fragility_score` per cell, comparable across the network |
| V | (hub, spoke, operator_class) cells, network-wide | A normalized composite hotspot score ranking all cells |

Fragility III introduced the peer-carrier economic baseline (UA/DL route basket) that Module A (focal corridor) retains unchanged. Fragility IV generalized scoring to all hubs but lacked a pre-built peer basket at each new hub, which motivated the pooled `aa_system_average` baseline used in Module B (Section 6.5). Fragility V added cross-cell normalization, the six-component composite, weighting-scenario robustness, and the persistence check.

### 6.2 The combined_fragility_score (Fragility IV)

Fragility IV produces one score per (operator_class, hub_family, weather_bucket, period_flag) cell. It is a fixed equal-weighted sum of four rates:

| Component | Weight |
|---|---|
| `cancellation_rate` | 0.25 |
| `severe_delay_rate` | 0.25 |
| `controllable_severe_delay_rate` | 0.25 |
| `late_arriving_severe_delay_rate` | 0.25 |

Critically, all four components share a single denominator — `flights_total`, the full scheduled sample for the cell — so each is an unconditional probability over the same sample space (AAR Iteration 9 standardization). This is what allows the four to be summed without a denominator-mismatch artifact. The top Fragility IV cell is **PSA_operated / ORD / adverse / 2025 (recent)** with `combined_fragility_score` = **0.1868** over 186 flights, driven by a 22.6% cancellation rate, a 30.7% severe-delay rate, and a 16.7% late-arriving (cascade) severe-delay rate. Note the score is an absolute level (sum of raw rates), not normalized against other cells — that step is Fragility V's contribution.

### 6.3 The composite hotspot score (Fragility V): six components, equal weights

Fragility V scores 2,093 (hub, spoke, operator_class) cells; **1,668** clear the `hotspot_min_flights = 100` threshold required for ranking. The composite is a weighted sum of six components. In the base scenario each carries weight 0.1667 (1/6):

| Component | Captures |
|---|---|
| `norm_cancellation` | cancellation rate |
| `norm_severe_delay` | arrival delay ≥ 60 min rate |
| `norm_controllable` | carrier-controllable severe-delay rate |
| `norm_cascade` | late-arriving (knock-on) severe-delay rate |
| `norm_weather_sensitivity` | degradation of the fragility rate from good to adverse weather |
| `norm_economic_burden` | economic-burden proxy (Section 6.5) |

**Normalization.** Each component is converted to a **percentile rank across all ranking-eligible cells**, then averaged with its weights. Percentile-rank normalization (rather than min–max or z-score) is robust to the heavy right tails and outliers that raw delay rates exhibit, and it makes the six dimensionally-different components directly comparable on a common [0,1] scale. The penalty is that the composite measures *relative* standing within this specific cell population, not an absolute fragility magnitude. The Rank-1 cell is **ORD–SPI (SkyWest_unresolved)**, base score **0.982**, robustness 1.00.

**Weather-sensitivity gating.** `norm_weather_sensitivity` is computed only for cells with at least `hotspot_min_adv_flights = 30` adverse-weather flights. Cells below that gate are set to NaN and scored on the remaining five components with weights renormalized. Without this gate, a cell with a handful of adverse flights and a perfect fragility rate would rank first — a small-sample upward bias.

### 6.4 Alternate weighting scenarios and the robustness score

Equal weighting is a subjective choice; to test sensitivity to it, three additional scenarios shift mass toward one emphasis:

| Scenario | cancel | severe_delay | controllable | cascade | weather_sens. | economic |
|---|---|---|---|---|---|---|
| `base` | 0.167 | 0.167 | 0.167 | 0.167 | 0.167 | 0.167 |
| `weather_emphasis` | 0.10 | 0.10 | 0.10 | 0.10 | **0.50** | 0.10 |
| `controllable_cascade_emphasis` | 0.10 | 0.10 | **0.30** | **0.30** | 0.10 | 0.10 |
| `economic_emphasis` | 0.10 | 0.10 | 0.10 | 0.10 | 0.10 | **0.50** |

The **robustness score** is the fraction of the four scenarios in which a cell appears in the top-N. A cell scoring 1.00 (e.g., ORD–SPI) is top-ranked regardless of which emphasis a stakeholder prefers, and is therefore a more defensible prioritization target than a cell that is top-ranked only in the base scenario. A separate **persistence flag** marks cells that are independently top-N in *both* the 2024 baseline and 2025 recent sub-periods (each using `min_flights // 2` as its threshold); only **1** of the top-20 cells (DFW–CID, AA_mainline) is persistent, consistent with the winner's-curse expectation that single-period top-N membership is partly noise. High robustness combined with persistence is the strongest signal.

### 6.5 The economic-burden proxy (aa_system_average, pooled)

Module B (the network expansion) has no pre-built peer-carrier route basket at each new hub, so its economic-burden component benchmarks each cell against an `aa_system_average` baseline that **pools all resolved operator classes within the same hub × weather × period cell**. Excess cancellations and excess controllable/cascade delay minutes versus that pooled mean are converted to dollars using published DOT block-cost benchmarks (an absolute-cost proxy, not airline financials). For the top Fragility IV cell this yields an economic-burden proxy of **$580,079** (~$3.12M per 1,000 flights).

This baseline is deliberately **conservative**: because it is pooled rather than leave-one-out, a high-volume operator with above-average fragility is itself part of its own baseline and therefore partially *suppresses* its own measured excess. The reported economic excess for the worst, highest-volume operators is thus a lower bound, not an inflation. Reviewers should read the economic component as conservative by construction.

### 6.6 Known limitations of the framework

The composite weights are a subjective choice (mitigated, not eliminated, by the scenario/robustness apparatus). The `norm_severe_delay` component tests arrival delay only, whereas `norm_controllable` and `norm_cascade` test departure-or-arrival delay; the components are not strictly nested and the composite mixes slightly different event definitions. Percentile-rank normalization measures relative standing within this cell population only. And the entire framework is associational: the scores rank where fragility is observed, not why it occurs.
