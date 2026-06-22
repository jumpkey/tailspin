# Executive Summary

This study asks a narrow, verifiable question: using only public records, can an outside observer locate where American Airlines' branded schedule is most likely to fail a passenger — by hub, spoke, operator, weather, and year? The answer is yes, and the result is specific enough to name routes.

**Data.** Two public sources only: U.S. DOT BTS On-Time Performance and NOAA ASOS hourly weather. The main study covers Jan 2024–Dec 2025 (24 months) across American's 9 hubs and 264 airports total (9 hubs plus 255 discovered spokes) — 6,152,599 flights, joined to weather at a 100.0% match rate (0.0% null). No proprietary, leaked, or insider data was used. A 2026 carve-out (Jan–Apr, the only BTS-published 2026 months) is always compared season-matched to the same months of 2024–25 to remove winter bias.

**Headline findings.**

| Finding | Evidence |
|---|---|
| Fragility is concentrated, not anecdotal | 2,093 (hub, spoke, operator) cells scored; 1,668 met the 100-flight ranking threshold. Top-20 hotspots cluster at DFW (40%) and ORD (40%), with DCA, CLT, MIA making up the rest. |
| One operator is sharply over-represented — and the test is fair | PSA-operated cells are 51.8% of the worst 5% of cells but only 12.2% of ranked flights: a **4.25x** over-representation. Envoy, also a wholly-owned American regional, is *under*-represented (0.16x). AA mainline sits near parity (0.63x). |
| Volume is not fragility | The largest new hubs by traffic — LAX, PHX, JFK — contribute **zero** top-20 hotspots. The signal lives in thin, short-haul regional spokes, dominated by cascade (late-aircraft) delay, not in big gateways or weather alone. |
| The personal anchor corridor confirms the pattern | PSA-operated DFW–LFT ranks **#63 of 1,668** (worst ~3.8%), cascade-driven. The same-corridor Envoy (#1,060) and SkyWest (#809) cells are markedly milder — so this is an operator-and-structure pattern, not "Lafayette is hard." |
| The pattern persists into 2026 | Season-matched, PSA stayed worst and worsened (cancel 4.2%→6.3%, severe 9.5%→11.2%); Envoy stayed cleanest and stable. ORD and DCA severe-delay rose (9.3%→11.6%, 9.1%→10.5%); LAX/PHX stayed cleanest. DFW–LFT is now ~90% PSA (up from ~42% in 2024) and did not improve. |

The Envoy counter-example is the methodological keystone: PSA and Envoy are both wholly-owned American regionals flying American Eagle under American's schedule and brand, yet they land at opposite ends of the fragility distribution. A finding that merely blamed "regional carriers" would implicate both; this one does not, and AA mainline appears throughout the worst cells, so the mainline is not shielded either.

**What we claim, and do not.** The study reports associations in public data, not causation: it has no internal operational data, leans on carriers' self-reported BTS delay-cause codes for cascade/controllable attribution, and conservatively *excludes* 904,924 flights (14.7%) whose operator could not be resolved from route context — including the rank-1 hotspot (ORD–SPI). These limitations are disclosed in full and, where they bite, run *against* the headline rather than toward it.

**The central governance question.** This entire analysis was reproduced from free public records in roughly one hour on commodity-relevant compute (~63 minutes wall-clock). The strongest, fair takeaway is therefore not "one route is bad" — it is this: if an outside observer can see exactly where this branded schedule concentrates its fragility, from public data alone, in an afternoon, the question worth answering is whether the same is being seen and acted on inside the airline — and if not, why not.
