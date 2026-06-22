## 11. Structural & Strategic Weaknesses

This is the section a skeptical reader should read first. Every finding in this report carries a known weakness; the credibility of the work rests on naming each one before anyone else does, stating its likely direction of bias, and showing what bounds or mitigates it. We distinguish *structural* weaknesses (inherent to public-data observation) from *strategic* ones (consequences of design choices we made). None of them, individually or together, overturns the headline associations — but several constrain how far those associations can be pushed, and we say so explicitly.

### 11.1 Association, not causation

The single most important limitation. The study observes outcomes (cancellations, severe delays, cascade delays) in public records; it has no access to crew rosters, maintenance basing, fleet assignment, schedule-buffer design, or station staffing. We can show that PSA-operated cells are over-represented in the worst tail (51.8% of the worst-5% cells against 12.2% of ranked flights, a 4.25× lift) and that the DFW–LFT PSA cell sits in the worst ~4% (rank #63 of 1,668). We cannot show *why*. The signal is at least as consistent with schedule and network structure — turn times, bank architecture, equipment routing, thin-spoke exposure, all of which American designs for its Eagle subsidiaries — as with execution by any operator's crews. **Mitigation:** the report's claims are scoped to associations throughout, and the dominant components in the highest-scoring cells are cascade and economic burden, not weather sensitivity, which is itself informative about mechanism without asserting cause. No causal language should survive into any external communication.

### 11.2 Reliance on self-reported BTS cause codes

The controllable (carrier-attributed) and cascade (late-arriving-aircraft) components depend entirely on carriers' own BTS delay-cause coding. Carriers have discretion and an incentive structure in how minutes are allocated across the five cause buckets. An earlier focal-corridor finding (AAR Iteration 2) is directly relevant: AA regional attributed 81.8% of its cancellations to weather versus 55.8% for peers — a gap that could reflect either genuine weather exposure or a reporting tendency. **Direction:** unknown and possibly self-serving; a carrier that under-codes "carrier" minutes would look artificially clean on the controllable component. **Mitigation:** cascade attribution (late-arriving aircraft) is harder to game than carrier-versus-weather splits, and the highest-scoring cells are cascade-driven; we report cause-derived components alongside cause-agnostic ones (cancellation rate, raw severe-delay rate) so a reader can weight the self-reported components down without losing the finding.

### 11.3 The 14.7% operator-ambiguity exclusion

SkyWest and Republic fly for multiple mainline brands, so 904,924 flights (14.7% of 6,152,599) cannot be attributed to an operator class from route context alone and are **excluded** from operator comparisons rather than guessed. This is conservative but consequential: the excluded set contains 12 of the worst-83 cells, including the network's rank-1 hotspot, ORD–SPI (SkyWest_unresolved, base score 0.982). The operator over-representation table is therefore computed on resolved data only. **Direction:** the exclusion removes cells from *both* numerator and denominator of every operator's share, so its net effect on the PSA lift is indeterminate but bounded by the 14.7% mass. **Mitigation:** the refusal to guess is itself a defensibility asset; a FlightAware AeroAPI key (~$100/month minimum spend) would resolve the ambiguity and name ORD–SPI, but the established direction of the finding does not depend on it.

### 11.4 Hub-attribution origin-priority (totals not cross-comparable)

When both endpoints of a flight are hubs, the flight is assigned to its origin hub. A consequence: DFW and ORD totals in the 9-hub run are slightly *lower* than in the 4-hub run despite more total flights. **Impact:** hub-level *totals* are not comparable across run modes; **cell-level rankings are unaffected**, because a (hub, spoke, operator) cell is defined identically regardless of run mode. Any statement comparing absolute hub volumes between the 4-hub and 9-hub runs is invalid; statements about cell rankings and within-run hub concentration are not.

### 11.5 Economic-burden baseline pooling

The economic-burden component uses an `aa_system_average` baseline that pools all resolved operators within a (hub, weather, period) cell, rather than leave-one-out. A high-volume operator with above-average fragility partially contributes to its own baseline, which **suppresses** its measured excess. **Direction:** conservative *against* the headline — it understates, not overstates, a dominant operator's burden signal. A leave-one-out baseline would widen the PSA gap, not close it. We accept the conservative version deliberately.

### 11.6 Endpoint versus en-route weather

Weather is assigned at the departure airport at departure hour and the arrival airport at arrival hour (worst of the two), with 100.0% match in the bigrun. En-route conditions — turbulence, fronts crossed in flight — are not captured. **Mitigation:** the network is short-haul spoke-to-hub (typically 1–2.5 hours), where endpoint conditions dominate the cancellation and dispatch decision; the simplification is most defensible exactly where the fragility concentrates. **Residual risk:** longer segments among the 264 airports are less well served by this assumption, and the weather-sensitivity component should be read as endpoint-weather sensitivity, not total-weather sensitivity.

### 11.7 Composite-weight subjectivity and the absolute-versus-multiplier trap

The composite hotspot score is six equal-weighted, percentile-normalized components. Equal weighting is a defensible default but a subjective one. **Mitigation:** three alternate weighting scenarios plus a robustness score test stability; the rank-1 cell holds robustness 1.00, and no top-20 cell is the artifact of a single weighting. Separately, this study has one hard-won interpretive lesson — the **A1 trap**. On DFW–LFT, Envoy is the *most weather-sensitive* operator by multiplier (7%→30%, ×4.3) yet PSA is *worst in absolute terms in every weather bucket* (16%→40%, ×2.5). A multiplier and an absolute level are different facts; conflating them previously produced a misleading exec chart that was corrected. We state both wherever weather sensitivity appears and never substitute one for the other.

### 11.8 Ranking noise, multiple comparisons, and small cells

Scoring 2,093 cells and reporting the extreme tail invites winner's-curse and multiple-comparison concerns: some cells rank high by chance. **Mitigations:** a 100-flight minimum for ranking (1,668 cells qualify); a separate 30-adverse-flight floor below which the weather-sensitivity component is dropped and the score renormalized on the remaining five (correcting a prior small-sample upward bias); a 30-flight reliability floor flagging 30 cells as "indicative only"; and persistence and robustness reported as signals distinct from rank. The low expected persistence rate for a top-20 list drawn from 1,000+ cells is disclosed rather than spun as instability.

### 11.9 2026 partiality and winter seasonality

The 2026 carve-out is four months (Jan–Apr), the only BTS-published months as of June 2026, and is winter-heavy. A naive 2026-versus-full-year comparison would be biased by season. **Mitigation:** every 2026 figure is **season-matched** to the same Jan–Apr months of 2024–25 (e.g., ORD severe 9.3%→11.6%, PSA cancel 4.2%→6.3%). Cell-level weather-stratified 2026 samples remain small and are treated as directional; network operator/hub aggregates are well-sampled.

### 11.10 Corridor mix-shift confound

Corridor-level changes can reflect *who flies the route* rather than how any operator performs. DFW–LFT rose 15.1%→16.8% (season-matched) at the corridor level, but PSA-only was roughly flat (17.1%→17.7%); the corridor move is **mainly the mix shift** toward PSA (≈42%→≈90% as Envoy exited), not a single operator deteriorating. **Mitigation:** we report operator-held-constant figures beside corridor aggregates and never attribute a corridor-level change to performance without the operator-level check.

### 11.11 AA-centric hub selection and generalizability

The scope is American's 9 hubs and their discovered spokes. There is no non-AA mainline control group at the new hubs (Module B uses the pooled AA-system baseline precisely because none exists). The findings are therefore *internal* to American's branded network: they identify where fragility concentrates within it, not whether American as a whole is worse than United or Delta. The earlier focal-corridor peer comparison (AA vs. DL/UA) is the only cross-carrier benchmark, and it is thin on the UA side. Generalization beyond American's network is not supported by this design.
