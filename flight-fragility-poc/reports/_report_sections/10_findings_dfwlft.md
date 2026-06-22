## 9. Findings: DFW-LFT Corridor

The Dallas/Fort Worth–Lafayette (DFW–LFT) corridor is the study's focal single-route case. It is a thin regional spoke flown by three of American's regional carriers under the American Eagle brand, and it serves two purposes here: first, it demonstrates the fragility framework at the level a single traveler experiences; second, it shows that the network-wide structure documented in Section 8 reproduces on an individual corridor rather than being an artifact of aggregation. The findings below draw on the corridor focal report and the canonical figures; small weather-stratified cells in the 2026 window are flagged as directional throughout.

### 9.1 Weather sensitivity: two facts that are not in conflict

The lead corridor finding concerns weather, and it requires care because two true statements about it look superficially contradictory. Measuring the share of flights cancelled or delayed at least one hour across the 2024–2025 main study window, stratified into good- and bad-weather buckets, produces the following per-operator picture:

| Operator (American Eagle) | Good weather | Bad weather | Weather multiplier |
|---|---|---|---|
| Envoy | 7% | 30% | 4.3× (most sensitive) |
| SkyWest | 8% | 28% | 3.3× |
| PSA | 16% | 40% | 2.5× |

The two facts are these:

- **Envoy is the most weather-*sensitive* operator** on the corridor. Its disruption rate climbs most steeply from good to bad conditions — a 4.3× jump — meaning its schedule degrades the sharpest when weather turns. This is the weather-stress signature that motivated the original question about the route.
- **PSA is the worst in *absolute* terms in every weather bucket.** PSA's good-weather rate (16%) already exceeds Envoy's and SkyWest's bad-weather rates, and under adverse conditions roughly 4 in 10 PSA flights are cancelled or badly delayed (40%).

These are not in tension because the multiplier and the level measure different things. The multiplier is a *ratio* describing how much an operator's performance changes between conditions; the absolute rate is the *level* a passenger actually faces. An operator can have a modest multiplier and still be the worst in every bucket if its baseline is high — which is exactly PSA's case — while another operator can post the steepest multiplier yet remain the lowest-rate operator overall, which is Envoy's case. Conflating the two ("Envoy is worst in weather because it has the highest multiplier") would invert the passenger-facing conclusion. The honest reading is that **no operator on the corridor holds up well as weather deteriorates, the most weather-sensitive operator is Envoy, and the operator a traveler is most likely to be disrupted by in any given condition is PSA.**

A useful fairness check is built in: the three operators diverge sharply from one another on the *same physical route*. That rules out "Lafayette is simply a hard airport" and "all regional flying is bad" as sufficient explanations — the variation is operator-specific and condition-specific.

![On DFW-Lafayette PSA is least reliable in any weather](output/exec/A1_weather_breaks_schedule.png)

![Weather hits every operator hard](output/exec/A1b_weather_sensitivity.png)

### 9.2 Corridor fragility rank by operator

Placing each operator's DFW–LFT cell against the full network of 1,668 ranked (hub, spoke, operator) cells shows that fragility on the corridor is also operator-dependent:

| Operator on DFW–LFT | Network rank (of 1,668) | Percentile |
|---|---|---|
| PSA | #63 | top 3.8% |
| SkyWest | #809 | ~top 48% |
| Envoy | #1,060 | ~top 64% |

The PSA-operated cell sits in the worst ~4% of the entire 9-hub network, and the focal report characterizes its score as cascade-driven — that is, dominated by knock-on (late-inbound-aircraft) delays rather than by weather alone. The SkyWest and Envoy cells on the identical route fall near or below the middle of the distribution. This is the single corridor confirming the network result: PSA-operated routes are over-represented among the worst trouble spots (Section 8 reports a 4.25× over-representation in the worst 5% of cells), and Envoy is not.

### 9.3 Operator rotation: the corridor is now ~90% PSA

DFW–LFT has no single steady operator; assignment rotates among PSA, Envoy, and SkyWest month to month. That rotation has, however, resolved decisively toward PSA. Envoy — historically a major operator on this route — has nearly exited since late 2025, and through the most recent data (2026) the corridor is overwhelmingly PSA, up from roughly 42% PSA in 2024 to about 89–90%.

![The operator on your route keeps changing](output/exec/A2_operator_keeps_changing.png)

The consequence is specific and quantitative. Season-matched (Jan–Apr 2026 vs. the same months of 2024–2025), **corridor-level disruption rose from 15.1% to 16.8%**, but **PSA measured on its own was essentially flat (17.1% → 17.7%)**. The corridor worsened chiefly because its operator mix shifted toward PSA — its least-reliable operator — not because any single operator's own performance collapsed. This distinction matters for attribution: a corridor-level trend line can move purely on mix, and reading it as a performance change for a fixed operator would be a mistake. In parallel, corridor knock-on (cascade) delays rose +39% season-matched, consistent with the cascade-driven character of the PSA cell.

A caveat applies to the finer 2026 weather cuts: the adverse-weather PSA sample in the four-month 2026 window is on the order of tens of flights, so weather-stratified 2026 figures for this corridor are directional, not precise. The 2026 window is also winter-heavy; season-matching mitigates but does not eliminate that bias.

### 9.4 What the corridor shows

The lived passenger experience on DFW–LFT — "it used to be tolerable, now it isn't" — decomposes into two measurable components: the schedule is acutely weather-sensitive across all operators, and *who flies it has changed underneath the traveler*, settling on PSA, the operator with the highest absolute disruption rate in every weather bucket and a top-4% network fragility cell. None of this is an allegation about any carrier; it is an association visible entirely from public records, and the structural questions it raises — equipment routing, turn buffers, and PSA-vs-Envoy assignment on matched routes — belong to American as the brand and schedule owner. The corridor is valuable precisely because it is *not* unusual: it is one instance of the nationwide pattern detailed in Section 9 (network-wide findings) and Section 11 (the 2026 carve-out).
