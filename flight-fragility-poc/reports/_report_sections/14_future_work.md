## 13. Future Work

The findings in this report rest on resolved public data with several
deliberately conservative exclusions. The following extensions would tighten the
analysis, broaden its reach, or — in one case — convert association into
something closer to causal inference. They are ordered roughly by cost-to-value.

**1. Resolve the 14.7% operator-ambiguity via FlightAware AeroAPI.** The largest
single methodological gap is the 904,924 flights (14.7% of 6,152,599) flown by
SkyWest and Republic for multiple mainline brands, which route context alone
cannot attribute and which are currently excluded — including 12 of the worst-83
cells and, notably, **the rank-1 network hotspot ORD–SPI** (currently labeled
`SkyWest_unresolved`, base score 0.982, robustness 1.00). AeroAPI's Standard
tier (a $100/month minimum-spend floor, with the actual run consuming ~200
capped queries / ~$4 of usage) would let the pipeline resolve these to specific
mainline contracts. This would not overturn the headline — PSA over-representation
is already established on resolved data — but it would *complete* it by naming the
operator on otherwise-unresolved top cells. The trade-off is candid: it exchanges
some of the "we refused to guess" defensibility for completeness, so it is
recommended only when a specific external communication needs to name the
operator on a top cell.

**2. Produce a network-wide economic-burden total.** The economic-burden
component is currently a per-cell proxy against a pooled `aa_system_average`
baseline. Aggregating it into a defensible dollar figure across all 1,668 ranked
cells — with passenger-volume weighting and disclosed assumptions — would give
the burden component a standalone interpretation rather than only a normalized
score contribution. The pooled (not leave-one-out) baseline should be revisited
here, since it conservatively suppresses a high-volume operator's own excess.

**3. Widen coverage.** The study is scoped to American's 9 hubs and 264 airports.
Extending the same engine to additional corridors below the 100-flight ranking
threshold, to other mainline carriers (United, Delta) and their regional
subsidiaries would test whether the PSA-style concentration is American-specific
or a general property of wholly-owned-regional schedule architecture.

**4. Causal inference, conditional on internal data.** The central limitation is
association, not causation: with only public BTS cause-codes and endpoint weather,
we cannot separate schedule/network structure from execution. If operational data
became available (actual turn times, crew/equipment routing, maintenance events),
methods such as matched comparisons across operators flying the same
hub-spoke-equipment under the same weather, or difference-in-differences around
schedule changes, could begin to attribute fragility to specific levers.

**5. Ongoing monitoring as 2026+ months publish.** The 2026 carve-out is a
four-month, winter-heavy partial sample (mitigated by season-matching). As BTS
publishes May 2026 onward, the season-matched series should be extended to confirm
whether the observed trends persist — e.g., PSA worsening (cancel 4.2%→6.3%,
severe 9.5%→11.2%) and ORD/DCA climbing (severe 9.3%→11.6% and 9.1%→10.5%).

**6. Composite-weight sensitivity analysis.** The composite uses 6
equal-weighted components, a subjective choice already stress-tested with 3
alternate weighting scenarios and a robustness score. A fuller sweep — randomized
weight perturbation, per-component leave-one-out, and rank-stability bands — would
quantify exactly how much each finding depends on the weighting choice rather than
the underlying signal.
