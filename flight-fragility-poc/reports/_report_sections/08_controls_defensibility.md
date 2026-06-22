## 7. Controls & Defensibility

This section enumerates the design choices that exist specifically to keep the
analysis fair and difficult to dismiss. Each is a deliberate decision, made
before the headline result was known, that trades convenience or completeness
for defensibility. None of them is a post-hoc rationalization of the finding;
several actively work *against* it.

### 7.1 Public data and full reproducibility

The study uses only two public sources: U.S. DOT BTS On-Time Performance and
NOAA ASOS hourly weather. There is no proprietary, leaked, or insider data, and
no privileged access to American Airlines' operational systems. Anyone can
obtain the same inputs and re-derive every number. The entire 6,152,599-flight,
264-airport pipeline runs from one command (`bash scripts/run_bigrun.sh`) in
roughly 63 minutes of wall-clock on commodity high-memory hardware. The
reproducibility burden is therefore low enough that a skeptic can verify rather
than argue. This is the foundational control: a result an outsider can
regenerate cannot be waved away as a black box.

### 7.2 Conservative exclusion of ambiguous flights

SkyWest and Republic fly for multiple mainline brands, so route context alone
cannot attribute their flights to a specific contract. Rather than guess, the
analysis **excludes** all 904,924 such flights — 14.7% of the dataset — from
every operator comparison. This is costly: it removes the rank-1 hotspot
(ORD–SPI, currently labeled `SkyWest_unresolved`) and 12 of the worst-83 cells
from attributed conclusions. We accept that cost. The headline (PSA
over-representation; widespread structural fragility) rests on resolved data
only. Refusing to impute operator identity is a defensibility asset: there is no
attribution we cannot defend, because we made none we were unsure of.

### 7.3 Disclosed weights, thresholds, and alternate scenarios

The composite hotspot score is six equal-weighted normalized components
(cancellation, severe delay, controllable, cascade, weather sensitivity,
economic burden). Equal weighting is a subjective choice and is disclosed as
such. To test whether the ranking depends on that choice, three alternate
weighting scenarios plus a robustness score are reported. The rank-1 hotspot
(ORD–SPI) carries a robustness of 1.00, and the top cell did not move when the
study scaled from 4 hubs to 9. Thresholds are stated explicitly: 60-minute
arrival for "severe delay" (the DOT standard, not a custom cutoff) and a
100-flight minimum for ranking eligibility (1,668 of 2,093 scored cells qualify).
A reviewer can re-weight or re-threshold and check stability themselves.

### 7.4 Coherent metrics: subsets and a shared denominator

The four composite components that derive from delay (controllable,
late-arriving/cascade) are strict subsets of the severe-delay parent, and all
components share a single denominator — all scheduled flights (AAR Iteration 9
standardization). This removes a cancellation-strategy artifact in which a
carrier that cancels aggressively would appear to have *fewer* delays simply
because cancelled flights left the delay denominator. Metric coherence closes a
common and legitimate line of attack on operational comparisons.

### 7.5 The PSA-vs-Envoy divergence as a built-in anti-bias check

The strongest internal control is structural. Envoy and PSA are **both**
wholly-owned American regional subsidiaries flying as American Eagle under
American's schedule and brand. If the method were biased against regional
carriers, both would surface in the worst cells. They do not:

| Operator class | Share of worst 5% cells | Share of ranked flights | Over-representation | Mean base score |
|---|---|---|---|---|
| PSA_operated | 51.8% | 12.2% | 4.25× | 0.683 |
| AA_mainline | 31.3% | 50.0% | 0.63× | 0.575 |
| Envoy_operated | 2.4% | 14.6% | 0.16× (under) | 0.346 |

PSA is over-represented 4.25×; Envoy is *under*-represented at 0.16×, the
lowest mean base score of any operator class. A finding that singled out
"regionals" would implicate both subsidiaries; this one separates them. The
result is operator- and cell-specific, which is exactly what makes it credible.

### 7.6 Mainline is included, not shielded

American mainline is not exempted from scoring. It accounts for 50.0% of ranked
flights and appears throughout the worst cells (31.3% of the worst 5%, 0.63×
over-representation), and in the 2026 carve-out its season-matched cancellation
rate more than doubled (1.5% → 3.4%). The economic-burden baseline
(`aa_system_average`) is pooled rather than leave-one-out, which slightly
*suppresses* a high-volume operator's own excess — a conservative choice that
works against, not toward, the headline. The method cannot be characterized as
protecting the parent carrier.

### 7.7 Season-matching the 2026 carve-out

The 2026 data covers only Jan–Apr (the BTS-published months as of June 2026), a
winter-heavy partial year. Comparing it directly to a full prior year would
import a seasonal bias. Instead, 2026 is always compared **season-matched** to
the same Jan–Apr months of 2024–25. This neutralizes the winter skew and lets
the persistence finding (PSA worst and worsening: cancel 4.2% → 6.3%, severe
9.5% → 11.2%; Envoy stable: cancel 2.4% → 2.7%) stand on a like-for-like basis.

### 7.8 Small-sample flagging

Reliability floors are enforced and disclosed. Cells below 100 flights are
excluded from ranking; the 30 cells below a 30-flight floor are flagged
"indicative only." Where a high-ranked cell has fewer than 30 adverse-weather
flights, its weather-sensitivity component is not scored (reported as dominant
component "unknown") rather than computed on noise. Thin cells are labeled, not
laundered into the headline.

Taken together, these controls mean the study's central claim survives because
it does not overreach: it reports associations in public data, names what it
will not claim, and embeds checks — most notably the PSA/Envoy divergence — that
a hostile reviewer would otherwise have to construct themselves.
