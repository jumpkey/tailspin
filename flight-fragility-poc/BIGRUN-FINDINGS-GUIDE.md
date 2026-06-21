# BIGRUN Findings Guide

**Read this first.** This is the top-level entry point to the national-scale
("bigrun") execution of the Flight Fragility study. It summarizes what was run,
what was found, how confident we are, and where to go for detail. Every number
here is reproducible from public data using the scripts in this repository.

- **Run date:** 2026-06-20 (Frankenserver, local high-memory server)
- **Read-out compiled:** 2026-06-21
- **Data vintage:** BTS On-Time Performance + NOAA ASOS weather, Jan 2024 – Dec 2025
- **Reproducibility:** `bash scripts/run_bigrun.sh` (see [§9](#9-how-to-reproduce))

> **One-sentence finding.** Using only public U.S. DOT and weather records, an
> outside observer can identify specific, repeatable schedule-fragility
> pressure points in American Airlines' branded network — concentrated in a
> measurable minority of hub-spoke cells, disproportionately those operated by
> one of American's wholly-owned regional subsidiaries — and the corridor a
> single frequent flyer experiences as chronically unreliable (DFW–LFT) sits in
> the worst ~4% of the entire 1,668-cell network.

---

## 1. What was run

| Dimension | Local baseline (prior) | **Bigrun (this run)** |
|---|---|---|
| Hubs | 4 (DFW, CLT, ORD, PHL) | **9** (DFW, CLT, ORD, PHL, MIA, PHX, DCA, LAX, JFK) |
| Airports covered | ~243 | **264** (9 hubs + 255 discovered spokes) |
| Months | 24 (Jan 2024–Dec 2025) | 24 (same) |
| Flights analyzed | 3,587,814 | **6,152,599** (1.71×) |
| Backend | pandas | **duckdb** (parallel) |
| FlightAware key | none | none (deliberately) |
| Wall-clock | — | **~63 min** (I–III 23m · IV 39m · V <1m) |
| Weather match | 96.6% | **100.0%** (0.0% null rate) |

The run executed the full pipeline end-to-end with no failures: Fragility I–III
(focal-corridor baseline), Fragility IV (operator attribution), and Fragility V
(network hotspot engine). The 9-hub set is American Airlines' complete hub
network. Compute was never the bottleneck; the only material cost was data
download.

---

## 2. Headline findings

**A. The core finding is robust to scale — it did not move.** The single most
fragile cell is the same as in the 4-hub baseline:
- **Fragility IV top cell:** PSA-operated flights at **ORD in adverse weather,
  2025** (combined fragility score 0.187; 22.6% cancellation, 30.7% severe-delay,
  cascade-dominated). Was 0.225 at 4 hubs — the small shift is renormalization,
  not a change in finding.
- **Fragility V rank-1 hotspot:** **ORD–SPI** (base score 0.982, robustness 1.00)
  — identical to the baseline's rank-1.

Adding five hubs and 2.6 million flights *confirmed* the existing signal rather
than diluting or overturning it.

**B. The pattern is widespread, not anecdotal.** The hotspot engine scored
**2,093** distinct (hub, spoke, operator) cells; **1,668** met the 100-flight
threshold for ranking. Fragility is not one bad route — it is a distributed
pattern with identifiable concentration.

**C. One operator class is sharply over-represented in the worst cells — and the
comparison is fair.** Across the worst-scoring cells (equal-weight base score):

| | Share of worst 5% | Share of worst 10% | Share of all ranked flights | Over-representation (worst 5%) |
|---|---|---|---|---|
| **PSA_operated** | **51.8%** (43 cells) | 43.7% | 12.2% | **4.25×** |
| AA_mainline | 31.3% (26 cells) | 40.1% | 50.0% | 0.63× |
| Envoy_operated | 2.4% (2 cells) | 1.2% | 14.6% | **0.16×** |

The mean base score by operator class (full ranked universe): PSA 0.683 >
AA_mainline 0.575 > SkyWest(unresolved) 0.487 > Republic(unresolved) 0.360 >
**Envoy 0.346**.

Why this is *fair and not anti-regional*: **Envoy Air and PSA Airlines are both
wholly-owned American regional subsidiaries** flying as American Eagle under
American's schedule and brand. One (PSA) is heavily over-represented in the
worst cells; the other (Envoy) is *under*-represented. A finding that singled out
"regional carriers" would implicate both. This one does not — it is **cell- and
operator-specific**, which is precisely what makes it defensible. And American
mainline itself is present throughout the worst cells (50% of flights, ~0.6–0.9×
across cuts), so the mainline is not being shielded either.

**D. Volume is not fragility.** The largest *new* hubs by traffic — LAX (687K),
PHX (722K), JFK (401K) — contributed **zero** top-20 hotspots. Fragility
concentrates in thin, short-haul regional spokes at DFW, ORD, and DCA, not in
the big gateways.

**E. A new hotspot hub emerged at national scale: DCA.** Reagan National
surfaces 2 of the top-20 cells (DCA–LAN, DCA–CVG); it was absent from the 4-hub
set. PHL dropped out of the top-20. Top-20 hub concentration: DFW 40%, ORD 40%,
DCA 10%, CLT 5%, MIA 5%.

---

## 3. The DFW–LFT corridor (honest placement)

DFW–LFT (Dallas/Fort Worth ↔ Lafayette, LA) is part of the study's original
focal corridor and is the corridor of direct personal interest. Its honest
placement in the national ranking:

| Operator on DFW–LFT | Flights | Cancel | Severe-delay | Cascade (late-arriving) | Base score | **Rank of 1,668** |
|---|---|---|---|---|---|---|
| **PSA_operated** | 2,827 | 4.1% | 14.4% | 9.5% | 0.869 | **#63 (top 3.8%)** |
| SkyWest (unresolved) | 1,748 | 3.4% | 7.2% | 0.9% | 0.502 | #809 |
| Envoy_operated | 2,171 | 1.9% | 7.3% | 3.4% | 0.407 | #1,060 |

**What this says, stated carefully:** The PSA-operated DFW–LFT cell is **not the
single worst in the network**, but it sits firmly in the **worst ~4%** — driven
by cascade (late-arriving aircraft) delay, the same signature as the network's
top cells. The lived experience of chronic disruption on this corridor is
**confirmed by public data**, not explained away. And within the *same corridor*,
the Envoy and SkyWest cells are markedly milder — reinforcing that this is a
specific operating-structure pattern, not "Lafayette is just a hard airport" and
not "all regionals are unreliable." The human anchor and the network pattern
point the same direction.

---

## 3a. 2026 carve-out — does the pattern persist? (Jan–Apr, season-matched)

A follow-on run extended the data through the BTS-published 2026 months (Jan–Apr)
with a clean `baseline = 2024-25` / `recent = 2026` split, written to separate
`*_2026` curated paths (committed analysis untouched). 2026 is compared
**season-matched** to the same months of 2024–25 to remove winter bias.

**The pattern persists, and on several measures worsens:**
- **PSA remained the worst operator and worsened** season-matched (Jan–Apr): cancel
  4.2% → 6.3%, severe-delay 9.5% → 11.2%. **Envoy remained the cleanest and stable**
  (cancel 2.4% → 2.7%, severe 6.3% → 6.6%). AA mainline cancellations more than
  doubled (1.5% → 3.4%) while its delay rate held.
- **The worst hubs stayed worst and climbed:** ORD severe-delay 9.3% → 11.6%, DCA
  9.1% → 10.5% — the top two, both rising. LAX/PHX remained the cleanest (~5.5–5.9%).
- **DFW–LFT did not improve;** it shifted to near-total PSA operation in 2026 and its
  knock-on-delay rate rose ~39% season-matched (small-sample caveat applies). See
  [reports/DFW_LFT_FOCAL_REPORT.md](reports/DFW_LFT_FOCAL_REPORT.md).

Caveat: 2026 is a four-month partial year; cell-level weather-stratified samples are
small and treated as directional. Network operator/hub aggregates are well-sampled.

## 4. What is observably true vs. what we do not claim

This study reports **associations in public data**. It is deliberately
conservative about causation.

**We state:**
- Specific (hub, spoke, operator) cells exhibit elevated, repeatable cancellation
  and cascade-delay rates over 24 months.
- These cells are disproportionately PSA-operated, concentrated at DFW/ORD/DCA.
- The pattern is reproducible by anyone with public data in about an hour.

**We do NOT state:**
- That any carrier's crews, maintenance, or local operations "perform poorly."
  The signal is consistent with **schedule and network structure** (turn times,
  bank architecture, equipment routing, thin-spoke exposure) at least as much as
  with execution — and American designs the schedule its Eagle subsidiaries fly.
- That weather is the cause. The dominant components in the highest-scoring cells
  are **cascade and economic burden**, not weather sensitivity.
- Any single-cause explanation. The composite score blends four equally-weighted,
  fully-disclosed components.

This restraint is a feature: the message survives scrutiny precisely because it
does not overreach.

---

## 5. Why this analysis is hard to dismiss

Built-in defensibility properties (each is a deliberate design choice):

1. **Public data only.** BTS On-Time Performance + NOAA ASOS. No proprietary,
   leaked, or insider data. Sources and download manifests are in the repo.
2. **Transparent method.** Equal component weights, disclosed thresholds
   (60-min severe-delay, 100-flight minimum cell), and four alternate weighting
   scenarios reported for robustness.
3. **Conservative on ambiguity.** 904,924 flights (14.7%) whose operator could
   not be resolved from route context are **excluded** from operator comparisons,
   not guessed. The findings rest on resolved data only.
4. **Coherent metrics.** Severe-delay sub-metrics are strict subsets of the
   parent; all four score components share one denominator (all scheduled
   flights), so no cancellation-strategy artifact (see AAR Iterations 8–9).
5. **Built-in fairness test.** Two wholly-owned regional subsidiaries land on
   opposite ends (PSA hot, Envoy benign); the mainline appears throughout. The
   result cannot be characterized as anti-regional or as mainline-protective.
6. **Reproducible.** One command, ~1 hour, commodity hardware.

---

## 6. Limitations (stated plainly, before anyone else states them)

- **Operator ambiguity (14.7%).** SkyWest and Republic fly for multiple mainline
  brands; 904,924 flights can't be attributed from route context alone and are
  excluded. 12 of the worst-83 cells — including the rank-1 hotspot (ORD–SPI) —
  are in this excluded set. See [§7](#7-the-100-flightaware-key-decision).
- **Small cells.** 30 cells fall below the 30-flight reliability floor (flagged
  "indicative only"); many high-ranked cells have <30 adverse-weather flights, so
  their weather-sensitivity component is not scored (shown as dominant component
  "unknown").
- **Hub totals not comparable across run modes.** The hub-attribution rule
  assigns a flight to its origin hub when both endpoints are hubs, so DFW/ORD
  counts are slightly lower than the 4-hub run. This affects hub *totals*, not
  the cell-level rankings.
- **Baseline pooling.** The economic-burden baseline (`aa_system_average`) pools
  all resolved operators in a cell rather than leave-one-out, which slightly
  *suppresses* a high-volume operator's own excess signal — i.e., it is
  conservative against, not toward, the headline finding.
- **Association, not causation** (see [§4](#4-what-is-observably-true-vs-what-we-do-not-claim)).

---

## 7. The $100 FlightAware key decision

**Question:** Does paying for FlightAware AeroAPI change the outcome?

**What it would buy.** AeroAPI's Standard tier ($100/month *minimum spend* — not
a flat fee; historical data is gated to Standard, so the free Personal tier
cannot serve these historical queries) would let the pipeline resolve the
904,924 ambiguous SkyWest/Republic flights to specific mainline contracts. The
run itself uses ~200 capped queries (~$4 of usage, absorbed within the $100
floor). Per-call cost is **not** zero; the $100 is a monthly minimum you draw
down against.

**Would it change the message? No — it would complete it.**
- The headline (PSA over-representation; widespread, structural fragility) is
  already established **on resolved data only**, with the ambiguous flights
  conservatively excluded. The key does not create or overturn that.
- It *would* let us **name the rank-1 hotspot** (ORD–SPI, currently
  "SkyWest_unresolved") and attribute 12 of the worst-83 cells — useful if a
  specific letter needs to name an operator on a specific route.
- The conservative exclusion is itself a **defensibility asset**: we are not
  guessing. Buying the key trades a little of that "we refused to guess" high
  ground for completeness.

**Recommendation.** Optional, not decision-critical. Defer unless/until a
specific external communication needs to name the operator on an
otherwise-unresolved top cell. If purchased, set a hard monthly cap in the
AeroAPI portal and re-run with `max_queries` raised deliberately. Full cost
mechanics are in this guide's companion analysis and the FRANKENSERVER notes.

---

## 8. Questions this puts on the table

The analytical contribution is not just "here are some bad routes." It is that
**this was done from the outside, cheaply, from public records** — which raises
governance questions that are fair to ask out loud:

1. Does American (and do PSA/Envoy) run **equivalent schedule-fragility
   stress-testing internally**, across the full hub-spoke-operator-weather grid?
2. If so, do **these same cells** — ORD–SPI, the PSA-at-ORD adverse cell,
   DFW–LFT — appear on that internal radar, and what is being done about them?
3. If not, **why is a one-hour public-data analysis surfacing them first**, and
   what is the cost of *not* knowing?
4. Where fragility concentrates in a **wholly-owned subsidiary's** operation
   under the parent's brand and schedule, where does accountability for the
   schedule design sit?

These are framed to invite examination, not to assign blame. The strongest
version of this work makes the recipient want to check their own data.

---

## 9. How to reproduce

```bash
cd ~/projects/tailspin/flight-fragility-poc
nohup bash scripts/run_bigrun.sh >/dev/null 2>&1 &   # ~1 hour, cold cache
tail -f logs/bigrun.latest.log
```

Configuration is in [config/study.yaml](config/study.yaml) (`run_mode: bigrun`,
`backend: duckdb`, the 9-hub list). The batch driver
[scripts/run_bigrun.sh](scripts/run_bigrun.sh) runs all three phases with
prerequisite gating and a stable log symlink.

---

## 10. Where to go next

| If you want… | Read |
|---|---|
| **Executive charts (the visual punch)** | **`output/exec/` — A1–A3 (corridor), B1–B2 (network)** |
| **The DFW–LFT single-corridor case study** | **[reports/DFW_LFT_FOCAL_REPORT.md](reports/DFW_LFT_FOCAL_REPORT.md)** |
| The formal network write-up framing | [reports/FRAGILITY_NETWORK_REPORT_DRAFT.md](reports/FRAGILITY_NETWORK_REPORT_DRAFT.md) |
| Plain-language exec chart specs (awaiting approval) | [reports/CHART_SPECS_DRAFT.md](reports/CHART_SPECS_DRAFT.md) |
| Draft outreach to the AA CEO (strategic) | [reports/letters/letter_AA_CEO_DRAFT.md](reports/letters/letter_AA_CEO_DRAFT.md) |
| Draft outreach to AA operational leadership | [reports/letters/letter_AA_stakeholders_DRAFT.md](reports/letters/letter_AA_stakeholders_DRAFT.md) |
| Draft outreach to PSA / Envoy leadership | [reports/letters/letter_PSA_Envoy_stakeholders_DRAFT.md](reports/letters/letter_PSA_Envoy_stakeholders_DRAFT.md) |
| Stakeholder-segmented talking points | [LEADERSHIP_READOUT_NOTES.md](LEADERSHIP_READOUT_NOTES.md) Entry 4 |
| Engineering / methodology history | [AAR.md](AAR.md) Iteration 10 |
| Raw numbers | `output/fragility_v_hotspot_rankings.csv`, `output/fragility_v_summary.md`, `output/fragility_iv_summary.json`, `output/qa_summary_hubspoke.csv` |

> **Status of the report and letters:** these are **drafts for your review**, not
> sent or published. They are written to be fair, measured, and data-grounded so
> that the message cannot be dismissed as biased or weak. Decide framing and
> recipients before anything leaves your hands.
