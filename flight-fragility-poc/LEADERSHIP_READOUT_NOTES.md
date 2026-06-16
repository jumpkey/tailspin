# Leadership Read-Out Notes — Working Document

**Status: draft, accumulating across study phases. Not a final deliverable.**

This file is a working scratchpad, separate from the neutral, ab-initio
study artifacts (`flight_fragility_*_spec.md`, `AAR.md`, `README.md`,
`output/*_summary.md`). Its purpose is to accumulate synthesis notes —
phase by phase, as Fragility I, II, III, and any later pass complete — that
will be drawn on at the end of the study to prepare a small set of
audience-specific read-outs:

1. A top-level (CEO-level) read-out for American Airlines.
2. Read-outs for the AA executive discipline heads whose functions this
   pattern touches.
3. A read-out for Envoy Air's CEO and discipline heads, as the regional
   carrier most directly positioned to act on whatever this network's
   pattern turns out to mean.

Every note below is written the same way the formal study artifacts are:
as an observation tied to a specific computed result, with the same
"consistent with / associated with" discipline and the same disclosure of
what the data cannot tell us. Nothing here should be read as a finished
conclusion — it is raw material for whoever drafts the final read-outs to
select from, sharpen, or discard.

---

## Entry 1 — Fragility I + II synthesis (2026-06-16)

### Source data

- Fragility I: `AAR.md` "Key finding: cancellation rates by weather bucket,"
  "Key finding: AA vs Delta alone," "Key finding: cancellation attribution."
- Fragility II: `output/fragility_ii_summary.md` (sections 1–3, 6),
  `output/fragility_ii_machine_summary.json` (includes the
  `controllable_cancel_rate_*` series, computed but not yet promoted into
  the written summary), `output/fragility_ii_operator_breakdown.csv`.

### A. Top-level (CEO-level) read-out notes

**The core fact pattern.** AA regional service in this basket of small
Louisiana/Mississippi/Texas spokes into DFW cancels and incurs severe delay
at a higher rate than comparable United and Delta regional spokes, and the
gap widens as weather deteriorates (cancellation ratio vs. peer average:
1.88× benign → 2.08× marginal → 2.08× adverse; vs. Delta alone, the
better-sampled peer, it escalates more cleanly: 1.79× → 2.32× → 3.02×).
That is the headline, and on its own it reads as "AA's regional network is
more weather-fragile than peers in this market."

**Decomposing the gap changes the question, not the fact pattern.** When
the same disruption is broken out by BTS's own self-reported cause code,
the gap is not concentrated in carrier-attributed ("Air Carrier" /
controllable) causes — if anything the opposite:

- AA's *controllable* cancellation rate runs *below* peers at every weather
  level, and sharply below in adverse weather: 0.15% vs. a 0.67% peer
  average (0.22×).
- AA's *controllable* severe-delay rate also runs below peers throughout
  (0.53×–0.95×, with the adverse-weather figure provisional on a thin peer
  cell).
- Independently, basket-wide cancellation-code attribution shows the same
  thing a different way: AA regional charges 81.8% of its cancellations to
  weather and only 6.5% to "Air Carrier," versus 55.8% / 30.4% for the
  combined peers.
- What *is* elevated for AA is the late-arriving-aircraft (cascade)
  severe-delay rate — 1.74×–2.0× peers — and it is elevated even in benign
  weather, not only when weather is bad.

**The CEO-level question this raises, stated as a question, not an
answer:** is AA's elevated weather-driven disruption in this market (a)
evidence of a real network/scheduling fragility — e.g., less schedule
buffer or connectivity resilience at these spokes than peers carry on
their equivalent spokes — that happens to get coded as Weather/NAS rather
than Carrier because that is genuinely where the disruption originates;
or (b) at least partly an artifact of how liberally AA's regional
operation applies the Weather/NAS cause codes compared to how UA/DL's
regional partners apply them in comparable circumstances? The study's
data is consistent with either, or both in different proportions, and
cannot adjudicate between them — see `flight_fragility_ii_machine_addon_spec.md`,
"Self-reported cause data." A leadership read-out should pose this as the
open question it is, not resolve it with the data in hand.

**Why this is the most defensible top-line framing.** It is the one part
of the result that is symmetric and hard for any reader — including AA's
own analysts — to dispute: the BTS cause-code split is public, carrier-
agnostic, and computed identically for AA and its peers. The interpretive
gap (real fragility vs. coding convention) is exactly where outside
scrutiny is most useful and least already answered.

### B. Executive discipline head notes (AA)

These are outside-in observations, not presumptions about who owns what.
Several disciplines may find one or more of these relevant; the final
read-out should let each discipline head decide what, if anything, is
theirs to follow up.

- **Network Planning / Scheduling.** AA's cascade (late-arriving-aircraft)
  severe-delay rate is elevated even in *benign* weather (4.43% vs. 2.55%
  peer average) — this is not purely a weather story. A network with
  comparatively little benign-weather cascade exposure would not show this.
  Worth knowing: is scheduled turn time / block time at these specific
  spokes tighter, relative to peers' equivalent spokes, independent of
  weather?
- **Integrated Operations Control / Hub Ops (DFW).** AA's weather-coded
  cancellation share (81.8%) is markedly higher than peers' (55.8%) on a
  basket that funnels into a single hub (DFW) versus peers' IAH/ATL. Worth
  knowing: is there a DFW-specific or spoke-airport-specific infrastructure
  factor (de-icing capacity, ramp/gate constraints) that would make the
  same weather event more disruptive into DFW than into IAH or ATL for a
  comparable regional spoke?
- **Dispatch / Meteorology.** The escalating cancellation ratio with
  weather severity (rather than a flat ratio) is consistent with — though
  not proof of — a more conservative or more sensitive cancellation
  decision threshold for this network under marginal/adverse conditions
  than peers apply to comparable circumstances. Worth knowing: how does
  the proactive-cancellation decision process for this basket compare to
  UA/DL's for their basket, independent of any cause-coding question?
- **Customer Experience / DOT Compliance / Regulatory Affairs.** The cause-
  code split has a compliance dimension independent of the operational
  question: cause-code assignment affects consumer refund eligibility and
  DOT on-time reporting. If AA's coding convention is more liberal toward
  Weather/NAS than peers', that is worth an internal coding-practice audit
  on its own, regardless of what it implies operationally.
- **Regional / Express Division oversight.** This study's peer-comparison
  design uses SkyWest's presence across all three baskets (AA, UA, DL
  contracts) as a control for operator-wide effects. The operator-level
  breakdown (Entry 1, section C below) suggests SkyWest's own
  controllable/cascade signature travels with the operator, not the AA
  contract specifically — which argues *against* an AA-contract-specific
  explanation for SkyWest's segment of the basket, but says nothing about
  Envoy's or PSA's segments, which have no cross-contract comparison
  available in this data.
- **Maintenance & Engineering and Crew Resources — explicitly not
  implicated by this data.** Worth stating plainly in any read-out: the
  controllable/cascade decomposition argues *against*, not for, a
  maintenance- or crew-quality explanation for the basket-level gap. These
  functions should not be drawn into the narrative on the strength of this
  study; if anything, this study's self-reported-cause data shows AA's
  controllable rate as comparatively low.

### C. Envoy Air CEO and discipline head notes

**Attribution caveat, stated up front.** This study's BTS-based pipeline
cannot, by itself, attribute any given flight to a specific tail number or
confirm which legal entity dispatched it — the operator identification
below relies on BTS's `Reporting_Airline` field, which is the carrier that
files the on-time-performance report. For these routes that is reliably
the regional partner itself (the AA mainline does not operate these
markets), but it is still public BTS data, not Envoy's or AA's internal
operational records, and should be cross-checked against those records
before being treated as confirmed.

**What the operator-level breakdown actually shows.** Within the AA
regional basket, Envoy Air (MQ, 7,530 flights) and PSA Airlines (OH, 5,357
flights) carry the basket's low-controllable / high-and-escalating-cascade
profile:

| Operator | Benign cascade | Marginal cascade | Adverse cascade | Benign controllable | Adverse controllable |
|---|---|---|---|---|---|
| Envoy (MQ) | 3.82% | 5.41% | 9.73% | 1.48% | 2.28% |
| PSA (OH) | 8.60% | 10.38% | 11.36% | 2.54% | 4.29% |
| SkyWest (OO, AA contract) | 1.06% | 0.82% | 1.32% | 5.23% | 8.88% |

SkyWest, flying the same basket under the same AA contract terms, shows
close to the opposite profile — low, flat cascade exposure and a higher,
weather-escalating controllable rate — and that same profile (high
controllable, ~zero cascade) also appears for SkyWest flying under its DL
contract elsewhere in this study. That consistency suggests the SkyWest
profile is closer to an operator-level characteristic than an AA-contract
effect. Envoy and PSA, by contrast, fly only under the AA contract in this
study's baskets, so there is no equivalent cross-contract comparison to
test whether their profile is operator-specific, AA-contract-specific, or
something about the particular spokes they fly versus the spokes SkyWest
flies within the same basket.

**Questions this raises for Envoy specifically, stated as questions:**

- **Network / Scheduling.** Envoy's cascade rate nearly triples from
  benign to adverse conditions (3.82% → 9.73%) while its controllable rate
  barely moves (1.48% → 2.28%). Is the AA-assigned block schedule — turn
  times, aircraft/crew rotations through DFW — giving Envoy's operation
  enough recovery buffer to absorb an upstream delay before it cascades
  into the next leg, relative to what SkyWest is scheduled to absorb on
  the same basket? This sits at the boundary of Envoy's operational
  control and AA's network-planning/contract terms, and likely needs a
  joint look rather than a purely internal one.
- **Station Operations at the spoke airports.** PSA's cascade rate is the
  highest of the three operators even in benign weather (8.60%) — worth
  understanding whether that reflects spoke-station turnaround execution,
  fleet/equipment differences, or something else entirely about PSA's
  specific routes within the basket.
- **Dispatch / OCC.** Given the controllable/cascade split looks
  structurally different for Envoy and PSA than for SkyWest on the same
  basket, is there a meaningful difference in how proactively each
  operator's own dispatch function manages an aircraft that is already
  running late, before it becomes a cascading severe delay?
- **Safety & Quality / Regulatory.** Envoy's and PSA's controllable rates
  are the *lowest* of the three operators in this basket (1.48%–4.29%
  versus SkyWest's 5.23%–8.88%) — worth confirming this reflects genuinely
  fewer self-attributed controllable events rather than a more
  conservative internal cause-coding convention, since that distinction
  matters for how much weight the rest of this finding can bear.

**What this data does *not* support saying to Envoy.** It does not support
a claim that Envoy's (or PSA's) maintenance or crew performance is worse
than SkyWest's — the controllable-cause data points the opposite direction.
The more defensible framing is narrower: Envoy's and PSA's segments of this
basket show a schedule-resilience-to-upstream-disruption (cascade) signature
that SkyWest's segment of the same basket does not show, and this study
cannot determine whether that is a scheduling/network factor, a station-
execution factor, a route-specific factor, or some combination.

### Open items / caveats to carry into any final read-out

- All caveats already disclosed in `flight_fragility_ii_machine_addon_spec.md`
  ("Risks, threats to validity, and alternative explanations") apply with
  equal force to the operator-level breakdown, and arguably more force
  given smaller per-operator-per-weather-bucket samples.
- The operator breakdown combines the 2024/2025 periods to preserve sample
  size; a period-level operator breakdown was not computed and would need
  smaller-cell handling if it becomes useful later.
- The `controllable_cancel_rate` series by weather bucket (AA 0.20%/0.28%/0.15%
  vs. peer average 0.26%/0.36%/0.67%) is already computed in
  `output/fragility_ii_machine_summary.json` but not yet promoted into the
  formal written summary or AAR — flagged here as a candidate addition for
  the final read-out, since it is one of the cleaner pieces of evidence for
  the "not controllable" framing.
- Fragility III scope and any further pass are not yet defined; this file
  should gain a new dated entry, not a rewrite of this one, when that work
  produces results worth carrying into the final read-out.

---

## Entry 2 — Fragility III synthesis (2026-06-16)

### Source data

- `AAR.md` "Fragility III: Economic Impact Estimation (Iteration 4)."
- `output/fragility_iii_summary.md` (full write-up and caveats).
- `output/fragility_iii_chart_data.csv`, `output/fragility_iii_summary.json`
  (weather-stratified and scenario-level detail behind the headline figures
  below).
- `config/economic_scenarios.yaml` (scenario assumptions and benchmark
  sourcing pointers).

### A. Top-level (CEO-level) read-out notes

**What this adds to Entry 1.** Fragility III attaches a defensible,
benchmark-based dollar range to the controllable/cascade pattern Entry 1
described qualitatively. Base case: an estimated **$1.99M** excess economic
burden over the two-year study window (range **$1.56M–$2.42M** across
low/high cost-benchmark scenarios), computed as AA regional's excess
controllable + cascade delay-minute burden relative to what the UA/DL
peer-average rate would predict for AA's own flight volume, plus a
separately-scenario'd cancellation-equivalent burden. This is a public-
benchmark proxy (A4A airline block-time cost, DOT/FAA value-of-time
guidance) — not audited revenue, voucher, or reaccommodation expense, and
not scaled by an actual passenger count, since no passenger-manifest data
exists in this pipeline's public sources.

**The sharper CEO-level question this raises.** Decomposing the dollar
figure by weather bucket shows it is not a weather-stress cost: essentially
all of the net positive burden (+18,891 excess minutes basis; ~$3.6M
base-case burden on that bucket alone) is concentrated in the
*benign*-weather bucket, while marginal and adverse weather each run
*negative* on this same basis — AA's combined controllable+cascade minutes
fall *below* the peer-average expectation once weather deteriorates. Put
plainly: the dollar exposure this study can measure is a baseline /
everyday-conditions cost, not a foul-weather cost. That is a sharper and,
arguably, a less comfortable framing than "AA's network struggles when
weather is bad" — it says AA's regional spokes in this basket carry a
measurable structural cost under *normal* operating conditions, and weather
stress does not meaningfully add to it on this basis. As in Entry 1, this
study's data cannot say why (schedule buffer, connection design, station
execution, or something else) — only that the pattern, now denominated in
dollars, is concentrated where a "weather fragility" framing would not
predict it to be.

**Why this strengthens, not just restates, Entry 1's framing.** The
controllable component of the cost basis is negative (AA's carrier-
attributed delay minutes run below the peer-average expectation), which is
the same direction as Fragility II's controllable-rate finding and
continues to argue against a maintenance/crew explanation. The cascade
component is the larger, positive driver. Both observations now carry a
dollar magnitude a CEO-level reader can weigh against remediation cost,
rather than only a percentage-point comparison.

### B. Executive discipline head notes (AA)

- **Finance / Corporate Planning.** This is the first point in the study
  where a dollar figure exists to weigh against any proposed remediation
  spend. Worth knowing: the figure is most useful as an order-of-magnitude
  prioritization signal (cascade-side schedule resilience is the
  dollar-material lever; the controllable side is already a net positive
  for AA in this comparison), not as a budget line — see caveats below.
- **Network Planning / Scheduling.** Entry 1 asked whether scheduled turn
  time or block time at these spokes is tighter than peers' independent of
  weather. Fragility III sharpens the stakes of that question: the dollar
  exposure is concentrated in benign-weather operations specifically, which
  is exactly the condition under which a schedule-buffer or connectivity-
  resilience gap (rather than a weather-contingency gap) would be expected
  to show up.
- **Integrated Operations Control / Hub Ops (DFW) and Dispatch /
  Meteorology.** No new dollar-specific finding for these disciplines
  beyond Entry 1's; the cost lens does not change which hub- or dispatch-
  level questions are open, since this pass did not decompose the cost
  basis by airport or by time-of-day.
- **Scope note for all AA discipline heads.** This pass computed the cost
  proxy at the AA-regional-basket level only. It does not break the dollar
  figure out by regional operator (Envoy/PSA/SkyWest) — see section C
  below for why that matters specifically for Envoy, and the "Open items"
  note on a possible operator-level extension.

### C. Envoy Air CEO and discipline head notes

**What this study has not computed, stated plainly.** Fragility III's cost
proxy was built at the AA-regional-basket level, the same grain as
Fragility I and II's headline tables — it does not allocate any portion of
the $1.99M base-case (or $1.56M–$2.42M range) figure to Envoy, PSA, or
SkyWest specifically. No operator-level dollar breakdown exists yet.

**What can be inferred, with appropriate hedging, from Entry 1's operator
table.** Entry 1 already showed Envoy (MQ) and PSA (OH) carrying the AA
basket's high-and-escalating-cascade profile, while SkyWest (OO) within the
same basket showed a low, flat cascade rate. Since Fragility III's net
positive cost basis is driven by the basket's cascade component, it is
*consistent with* — though this study has not directly tested — that
component being disproportionately attributable to Envoy's and PSA's
segments of the network rather than SkyWest's. This is an inference worth
testing, not a finding; the appropriate next step, if useful, is an
operator-level extension of the cost-proxy calculation (grouping by
`carrier_code` the same way Fragility II's operator breakdown does),
which has not been built in this pass and should not be presented to
Envoy without that direct computation.

**Questions this raises for Envoy specifically, stated as questions, pending
that direct computation:**

- **Network / Scheduling and Finance (joint).** If an operator-level cost
  breakdown confirms the inference above, does AA's block-schedule
  allocation to Envoy's routes in this basket carry a quantifiable
  recovery-buffer gap relative to SkyWest's allocation on the same basket —
  and if so, what would closing that gap plausibly be worth against the
  dollar figure here?
- **Safety & Quality / Regulatory.** The caveat from Entry 1 still applies
  at full force: this data does not support a claim that Envoy's or PSA's
  maintenance or crew performance is worse than SkyWest's, and that remains
  true with a dollar figure attached — the controllable-cost component
  points the opposite direction.

### Open items / caveats to carry into any final read-out

- **Candidate addition, not yet built**: an operator-level (`carrier_code`)
  extension of `scripts/32_analyze_fragility_money.py`, mirroring Fragility
  II's `aggregate_by_operator()`, would let the dollar figure be split
  across Envoy/PSA/SkyWest the same way the rate-based metrics already are
  in `output/fragility_ii_operator_breakdown.csv`. Flagged here as the most
  directly useful next computation for the Envoy-specific read-out, not
  authorized or implemented in this pass.
- All caveats in `output/fragility_iii_summary.md` section 5 apply with
  full force to every dollar figure in this entry, in particular: these are
  benchmark-based proxies, not audited financials; the passenger-time
  component is a flight-level proxy not scaled by actual passenger counts;
  and the cancellation-equivalent-minutes assumption is a scenario lever,
  not an observed fact.
- Any further pass beyond Fragility III (not yet defined) should gain its
  own new dated entry below this one, per the same append-only convention
  used for this entry.
