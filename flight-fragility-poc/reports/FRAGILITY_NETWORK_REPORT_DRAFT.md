# Schedule Fragility in the American Airlines Branded Network: What Public Records Show

**DRAFT for internal review — not for distribution.**
Compiled 2026-06-21 from a national-scale ("bigrun") analysis of public U.S. DOT
and weather data, Jan 2024 – Dec 2025. See
[BIGRUN-FINDINGS-GUIDE.md](../BIGRUN-FINDINGS-GUIDE.md) for the summary and
reproduction instructions.

---

## Executive summary

Using only publicly available records — the U.S. Department of Transportation's
Bureau of Transportation Statistics (BTS) On-Time Performance database and NOAA
ASOS surface-weather observations — it is possible for an independent observer to
map schedule fragility across American Airlines' entire hub network and to
identify the specific routes and operators where cancellation and cascading-delay
risk concentrates.

This analysis covers **6,152,599 flights** across **American's nine hubs** and
**255 connected spoke airports** over **24 months**. It scores **1,668**
(hub, spoke, operator) cells on a transparent, equally-weighted composite of
cancellation, severe-delay, controllable-delay, cascade-delay, weather-
sensitivity, and economic-burden signals.

Three findings stand out:

1. **Fragility is real, measurable, and concentrated.** A minority of cells carry
   a disproportionate share of the network's disruption signal, and the
   concentration is stable across alternate scoring assumptions.
2. **It is disproportionately associated with one operating structure.** Cells
   operated by **PSA Airlines** — a wholly-owned American regional subsidiary —
   are over-represented among the most fragile cells by roughly **4×** relative to
   their share of flights, while a second wholly-owned regional (Envoy) is
   *under*-represented. This is an operating-structure pattern, not a
   regional-carrier pattern.
3. **It is visible from outside the airline.** The entire analysis reproduces in
   about one hour on commodity hardware from free public data.

The report makes **associational, not causal** claims, and is explicit about its
limitations. Its purpose is to put a fair, hard-to-dismiss question on the table:
*if an outside observer can see this with public data, is it being seen and acted
on inside?*

---

## 1. Method in brief

- **Data.** BTS On-Time Performance (every scheduled U.S. domestic flight, with
  cancellation and delay-cause fields) joined to NOAA ASOS hourly weather at
  origin/destination. 100% of analyzed flights matched to a weather observation.
- **Unit of analysis.** The (hub family, spoke airport, operator class) cell,
  further split by weather bucket (benign/marginal/adverse) and period
  (2024 baseline / 2025 recent).
- **Operator classes.** Flights are attributed to AA mainline, Envoy (wholly-
  owned regional), PSA (wholly-owned regional), or — where route context cannot
  disambiguate a multi-brand regional (SkyWest, Republic) — to an explicit
  *unresolved* class that is **excluded** from operator comparisons rather than
  guessed.
- **Score.** A composite "hotspot score" combines six normalized components with
  equal weights; three alternate weightings (weather-emphasis, controllable/
  cascade-emphasis, economic-emphasis) are computed to test robustness.
- **Thresholds.** 60-minute severe-delay definition (DOT-standard, arrival-based);
  100-flight minimum for a cell to be ranked; 30-flight floor below which rates
  are flagged indicative-only.

Full mechanics, code, and data manifests are in the repository.

## 2. Scope and scale

| | Value |
|---|---|
| Hubs | DFW, CLT, ORD, PHL, MIA, PHX, DCA, LAX, JFK |
| Spoke airports discovered | 255 |
| Flights analyzed | 6,152,599 |
| Period | Jan 2024 – Dec 2025 (24 months) |
| Cells scored / ranked | 2,093 / 1,668 (≥100 flights) |
| Weather match rate | 100.0% |

## 3. Findings

### 3.1 Fragility concentrates

The top-20 cells by composite score sit overwhelmingly at three hubs — **DFW
(40%), ORD (40%), DCA (10%)** — with the remainder at CLT and MIA. The largest
hubs by raw traffic (LAX, PHX, JFK) contribute **none** of the top-20. Traffic
volume and fragility are decoupled; the signal lives in thin, short-haul regional
spokes, not in the big gateways.

### 3.2 The operating-structure association (the central result)

Measured across non-arbitrary cutoffs (not just the top-20), PSA-operated cells
are sharply over-represented among the worst cells:

| Operator class | Worst 5% | Worst 10% | Worst 25% | Share of flights | Mean score |
|---|---|---|---|---|---|
| **PSA_operated** | 51.8% | 43.7% | 33.3% | 12.2% | 0.683 |
| AA_mainline | 31.3% | 40.1% | 42.9% | 50.0% | 0.575 |
| Envoy_operated | 2.4% | 1.2% | 3.1% | 14.6% | 0.346 |

PSA carries ~12% of flights but ~52% of the worst-5% cells — a **4.25×**
over-representation. American mainline tracks roughly with its volume. Envoy, a
second wholly-owned regional, is **under**-represented at every cutoff.

**Interpretation discipline.** That PSA and Envoy — structurally similar
wholly-owned regionals — land at opposite ends is the strongest evidence that
this is *not* a "regional carriers are worse" artifact and *not* an analysis
biased against regional operations. It is specific to particular operating
structures (route assignments, equipment routing, schedule banks) within
American's branded product. Because both regionals fly American's schedule under
American's brand, the structural questions are American's to answer.

### 3.3 The signature is cascade, not weather

Among the highest-scoring cells the dominant component is **cascade
(late-arriving-aircraft) delay** and **economic burden**, not weather
sensitivity. Fragility here looks like disruption *propagating through the
schedule* — a flight late because its inbound aircraft was late — more than
weather exposure per se.

### 3.4 A representative corridor: DFW–LFT

DFW–Lafayette is a useful illustration because it is small, ordinary, and
nonetheless clearly fragile when PSA-operated:

| Operator | Flights | Cancel | Severe-delay | Cascade | Rank of 1,668 |
|---|---|---|---|---|---|
| PSA_operated | 2,827 | 4.1% | 14.4% | 9.5% | **#63 (top 3.8%)** |
| SkyWest (unresolved) | 1,748 | 3.4% | 7.2% | 0.9% | #809 |
| Envoy_operated | 2,171 | 1.9% | 7.3% | 3.4% | #1,060 |

The PSA-operated cell ranks in the network's worst 4% on the same cascade
signature seen at the top of the table; the other operators on the *identical*
route are far milder. The corridor is not exotic and the airport is not the
explanation — the operating structure is the differentiator.

## 4. What this report does not claim

This is an associational analysis of public outcome data. It does **not**
establish causation, does **not** evaluate crews, maintenance, or local station
performance, and does **not** isolate a single driver. Cancellation and delay
outcomes reflect schedule design, fleet and crew routing, weather, ATC, and
execution together. The consistent finding across hubs and 24 months is that
certain operating structures carry materially more of the disruption signal — a
result that warrants internal examination, which public data cannot itself
perform.

## 5. Limitations

- **14.7% operator-ambiguity** (904,924 SkyWest/Republic flights) excluded rather
  than guessed; this includes the rank-1 cell. A licensed historical data source
  would resolve these (see the $100-key analysis in the findings guide).
- **Small-cell noise** below 30 flights; flagged, not hidden.
- **Hub totals** are run-mode-dependent (origin-priority attribution) and not
  cross-comparable; cell rankings are unaffected.
- **Conservative economic baseline** (pooled, not leave-one-out) that under-states
  rather than over-states a high-volume operator's own excess.

## 6. The governance question

Every input here is public. The pipeline is open and runs in an hour. That makes
the central question less "what is wrong with route X" and more institutional:

> Is equivalent, systematic schedule-fragility stress-testing being performed
> inside American and its regional subsidiaries — and if so, do these same cells
> appear on it? If a frequent flyer with public data and a laptop can locate the
> worst 4% of the network, the relevant parties inside almost certainly can do
> better. The open question is whether they are, and what follows when they do.

## 7. Suggested next steps

1. Decide whether to license historical operator resolution to name the rank-1
   and other currently-unresolved top cells.
2. Finalize report framing and audience.
3. Review the draft stakeholder letters
   ([AA](letters/letter_AA_stakeholders_DRAFT.md),
   [PSA/Envoy](letters/letter_PSA_Envoy_stakeholders_DRAFT.md)).

---

*Appendix data: `output/fragility_v_hotspot_rankings.csv`,
`output/fragility_v_summary.md`, `output/fragility_iv_summary.json`,
`output/qa_summary_hubspoke.csv`. Method history: `AAR.md`.*
