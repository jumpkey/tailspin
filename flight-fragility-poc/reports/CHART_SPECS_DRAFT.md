# Executive Chart Specs — Plain-Language Redesign (DRAFT for approval)

> **Render status (rendered to `output/exec/`):** A1 was split after review — A1 now
> shows **absolute** disruption only ("PSA least reliable in any weather"), and a new
> **A1b** isolates **weather sensitivity** (good→bad dumbbell + each operator's own
> multiplier) so absolute level and relative swing are never conflated. A3 was
> revised to show **Corridor vs PSA-only** side by side, attributing the corridor's
> 2026 decline to the operator **mix shift** (42%→89% PSA) rather than a single
> operator declining. Set is now A1, A1b, A2, A3, B1, B2.

**Purpose.** Replace the current jargon-dense charts with a small set where
**each chart carries exactly one sentence of meaning**, readable by a
non-technical executive in under ten seconds. No data-science vocabulary appears
on any chart. Specs first — nothing is rendered until you approve.

## What's wrong with the current charts (the one you flagged)

`output/fragility_v_exec_chart.png` fails on four counts:
- **Jargon axes:** "Composite Hotspot Score (sum of weighted normalized
  components)", "Robustness (fraction of scenarios)". Meaningless to an executive.
- **Coded labels:** `SkyWest_unresolved @ ORD-SPI`, `AA_mainline @ DFW-CID (P)`.
- **Too dense:** 20 rows × 6 stacked segments + a second dot panel = no single
  takeaway.
- **No "so what":** it shows a ranking, not a message.

The redesign below fixes all four. Shared rules for every chart:
- Title **is** the takeaway sentence (not "Fragility V Scorecard").
- Plain labels only: "Flights cancelled or delayed 1+ hour (%)", "Good / Marginal
  / Bad weather", "Share of flights" vs "Share of the worst trouble spots".
- Banned words on charts: *composite, score, normalized, component, hotspot cell,
  robustness, operator_class, cascade* (use "knock-on delays"), *fragility*
  (use "schedule reliability / disruption").
- ≤ 3 colors, ≤ 6 bars/groups per chart, large fonts, one idea each.
- Footer on every chart: "Source: U.S. DOT BTS On-Time data + NOAA weather,
  Jan 2024 – [period]. Reproducible: [repo URL]."

---

## SET A — DFW–Lafayette (the personal corridor)

### A1. "When the weather turns, the DFW–Lafayette schedule breaks."
*(THE LEAD CHART — answers the original question.)*
- **Type:** grouped vertical bars. X = Good weather / Marginal / Bad weather.
  Y = "Flights cancelled or delayed 1+ hour (%)". One bar group per operator
  (American Eagle–PSA, American Eagle–Envoy, American Eagle–SkyWest).
- **Message it must land:** every regional operator on this route degrades sharply
  in bad weather; the corridor has no operator that holds up.
- **Annotation:** a small "5× worse in bad weather" callout on the steepest
  operator (Envoy) and "highest overall" on PSA — the two true, distinct facts.
- **Data:** `flight_operability_fact*` / hub-spoke fact, DFW–LFT, by operator ×
  weather, 2025 (recent). Peer-backed: all three operators shown side by side.
- **Stakeholders:** all. This is the human anchor.

### A2. "The operator on your route keeps changing."
- **Type:** stacked vertical bars, one per month (Jan 2024 → latest 2026),
  three colors = the three operators, height = flights that month.
- **Message:** DFW–LFT rotates among three regional carriers month to month — no
  stable operator, no stable accountability. (PSA-heavy at the end of 2025.)
- **Data:** monthly operator counts, DFW–LFT.
- **Stakeholders:** Network Planning, Regional oversight.

### A3. "Is 2026 any better? Not yet." *(needs carve-out — in progress)*
- **Type:** simple paired bars. Two groups: "2024–2025" vs "2026 (Jan–Apr)".
  Y = "Flights cancelled or delayed 1+ hour in bad weather (%)" on DFW–LFT.
  Optionally split by operator if sample allows.
- **Message:** whether the bad-weather problem persisted into 2026.
- **Data:** 2026 carve-out fact (`*_2026`).
- **Stakeholders:** all — answers "is this still happening?"

---

## SET B — The network (the bigger picture)

### B1. "One operator flies 1 in 8 flights — but half the worst trouble spots."
*(THE NETWORK LEAD — the over-representation, made plain.)*
- **Type:** two side-by-side bars per operator: "Share of all flights" vs
  "Share of the worst-performing routes". Operators: PSA, American mainline,
  Envoy.
- **Message:** PSA's share of the worst routes (≈52%) dwarfs its share of flights
  (≈12%); Envoy's is the reverse (benign). The gap, not a score, tells it.
- **Annotation:** "PSA: 4× over-represented" / "Envoy: under-represented" — the
  built-in fairness check, shown not asserted.
- **Data:** worst-5% of ranked routes vs flight share, by operator.
- **Stakeholders:** CEO, Regional oversight.

### B2. "It's not the big airports."
- **Type:** paired bars for the 9 hubs: hub size (flights) vs number of worst-
  trouble-spot routes. Order hubs by size.
- **Message:** the biggest hubs by traffic (LAX, PHX, JFK) have *zero* worst spots;
  the trouble concentrates at DFW, ORD, and (newly) DCA.
- **Data:** hub flight totals + top-cell counts per hub.
- **Stakeholders:** Network Planning, Hub Ops.

---

## Optional / on request
- **B3. "The delays are knock-on, not weather."** Split of what drives the worst
  routes — share where the cause is a late *inbound* aircraft vs weather itself.
  (Plain framing of the cascade finding.) Hold unless you want it.

## Render plan (after you approve)
1. New module `scripts/45_plot_exec_storyline.py` rendering A1–A3, B1–B2 to
   `output/exec/` as standalone PNGs (matplotlib, the reliable backend here).
2. Each PNG sized for a slide and for phone viewing.
3. The report and letters reference these by message, not by file name.

**Approve the set as-is, or tell me which to cut/add/reword before I build it.**
