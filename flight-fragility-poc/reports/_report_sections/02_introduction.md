## 1. Introduction & Motivation

This study began with a single, ordinary complaint: one frequent flyer's
recurring experience that flights between Dallas/Fort Worth (DFW) and Lafayette,
Louisiana (LFT) were chronically unreliable, and a working hypothesis that bad
weather was the proximate cause. That anecdote is not evidence. The purpose of
the work that follows is to test whether a lived impression survives contact with
the public record — and, having generalized the question, to map where schedule
fragility actually concentrates across an entire hub network.

The investigation deliberately uses only public data: the U.S. DOT Bureau of
Transportation Statistics (BTS) On-Time Performance database and NOAA ASOS hourly
surface-weather observations. No proprietary, leaked, or insider operational data
is used. The main study covers January 2024 through December 2025 (24 months); a
later carve-out extends through the BTS-published 2026 months (January–April),
always compared season-matched to the same months of 2024–25 to remove winter
bias. At national scale the analysis spans American Airlines' nine hubs (DFW,
CLT, ORD, PHL, MIA, PHX, DCA, LAX, JFK), 264 airports, and 6,152,599 flights,
with a 100.0% weather-match rate.

### What this report is

This is an observational study of public outcome data. Its unit of analysis is
the (hub, spoke, operator) cell, further stratified by weather bucket and period,
and scored on a transparent, equally-weighted six-component composite. It
generalizes the originating DFW–LFT question into a network-wide search for
repeatable cancellation and cascade-delay pressure points, and it places the
focal corridor honestly within that larger ranking rather than treating it as
special. The DFW–LFT PSA-operated cell ranks #63 of the 1,668 ranked cells (top
3.8%) — confirming the lived impression without inflating it.

### What this report is not

It is not a causal analysis. We observe associations in outcome records; we do
not have, and do not claim, access to the operational facts — crew routing,
maintenance status, dispatch decisions, ATC interactions — that would be needed
to assign cause. Notably, the original weather hypothesis is not the answer the
data returns: the dominant components in the highest-scoring cells are cascade
(late-arriving-aircraft) delay and economic burden, not weather sensitivity.
Weather sensitivity and absolute disruption level are distinct facts and are kept
separate throughout. This report does not evaluate any carrier's crews,
maintenance, or station performance, and it does not isolate a single driver of
disruption.

### How to read it

State the stance up front: **association, not causation.** Every finding here is
a statement about what public records show, framed conservatively. Where operator
attribution cannot be resolved from route context (14.7% of flights, including
the rank-1 cell), those flights are excluded from operator comparisons rather
than guessed. Where samples are thin (cells below 30 flights), results are flagged
indicative-only. The composite weighting is a disclosed, subjective choice, tested
against three alternate weightings and a robustness score.

Sections 3–8 document the data, design, and methodology in the detail a skeptical
reader needs to attack them; Sections 9–11 report network-wide, corridor, and
2026 findings; Sections 12–15 are candid about weaknesses and fully reproducible.
The intended contribution is not a list of bad routes but a fair, hard-to-dismiss
question: if an outside observer can locate the worst 4% of a national network in
about an hour from free data, is the same being seen and acted on inside?
