## 4. Methodology: Operator Attribution

Every claim about a *specific* operator in this study depends on first answering a
deceptively hard question: who actually flew the flight? The U.S. DOT BTS On-Time
Performance feed records a single `Reporting_Airline` (carrier) code per flight and
has no separate marketing-carrier field. For a major like American that subcontracts
much of its regional flying to multiple operators — some wholly owned, some
independent — that one code is sometimes sufficient and sometimes fundamentally
ambiguous. Our attribution method is built to be exact where the code permits and
to *withhold judgment* where it does not, rather than guess.

### Operator classes and the wholly-owned-subsidiary framing

We classify all 6,152,599 in-scope flights into six operator classes. Three of these
resolve directly and unambiguously from the BTS carrier code (per
`config/operator_classes.yaml`, `as_of` 2026-06-16):

| Carrier code | Operator class | Resolution | Flights |
|---|---|---|---|
| `AA` | `AA_mainline` | Direct (high confidence) | 1,943,962 |
| `MQ` | `Envoy_operated` | Direct (high confidence) | 568,329 |
| `OH` | `PSA_operated` | Direct (high confidence) | 476,691 |

Envoy Air (`MQ`) and PSA Airlines (`OH`) are **wholly-owned regional subsidiaries of
American Airlines Group**, disclosed in American's public corporate filings as
operating *exclusively* as American Eagle under American's schedule and brand. This
matters for interpretation: when this report compares PSA against AA mainline against
Envoy, it is comparing *operating structures within the same parent company flying the
same brand*, not American against an outside competitor. Because each of these carriers
flies under one and only one mainline contract, its code maps to exactly one operator
class everywhere in the network, and no further inference is required.

### Genuinely ambiguous codes: route-context inference for OO and YX

Two regional codes cannot be resolved by code alone, because the operator flies for
more than one mainline brand simultaneously under separate capacity-purchase
agreements:

- **`OO` — SkyWest.** Per SkyWest's FY2024 Form 10-K, SkyWest operates concurrently
  as United Express (~890 daily departures), Delta Connection (~700), American Eagle
  (~380), and Alaska Airlines (~220). A bare `OO` row could be any of the four.
- **`YX` — Republic.** Republic operates as American Eagle, United Express, and Delta
  Connection.

For these, attribution proceeds in priority order. **Route-context inference**
(`scripts/lib/operator_classify.py`) is applied first: if a flight's route already
belongs to a pre-validated basket in `config/routes.yaml`, that basket assignment
implies the mainline contract and resolves the row deterministically. This works well
for Module A (the focal corridor, which has hand-validated baskets) but, by
construction, cannot resolve flights in the Module B hub-spoke expansion, where the
spoke universe is discovered from the data and no pre-built basket exists. Rows that
route-context inference cannot resolve retain the explicit holding labels
`SkyWest_unresolved` (606,125 flights) and `Republic_unresolved` (298,799 flights).

### The unresolved-ambiguity classes are excluded, not guessed

This is the most important defensive choice in the attribution layer. The two
unresolved labels together account for **904,924 flights — 14.7% of the 6,152,599-flight
universe** — and they are **conservatively excluded from every operator-class
comparison**, never imputed to a most-likely brand. We would rather report a
narrower-but-defensible operator comparison than inflate any single operator's count
with flights we cannot prove it flew.

| Operator class | Flights | Share | Status in operator comparisons |
|---|---|---|---|
| `Other_or_non_AA` | 2,258,693 | 36.7% | Excluded (peer/other carriers) |
| `AA_mainline` | 1,943,962 | 31.6% | Included |
| `SkyWest_unresolved` | 606,125 | 9.9% | **Excluded (ambiguous)** |
| `Envoy_operated` | 568,329 | 9.2% | Included |
| `PSA_operated` | 476,691 | 7.7% | Included |
| `Republic_unresolved` | 298,799 | 4.9% | **Excluded (ambiguous)** |

The exclusion is not cost-free, and we flag it candidly. The single highest-scoring
Fragility IV cell is `PSA_operated / ORD / adverse / 2025` (combined fragility score
0.187, 186 flights) — but the top *unresolved* cell would, if resolved, potentially
enter the same neighborhood. More directly, the Fragility V rank-1 network hotspot,
ORD–SPI, carries the `SkyWest_unresolved` label (base score 0.982, robustness 1.00):
it ranks first precisely because its disruption signature is severe, yet we cannot
attribute it to a specific mainline contract under the keyless configuration. Readers
should treat all SkyWest- and Republic-specific silence in the operator findings as a
deliberate abstention, not evidence of clean performance.

### The optional FlightAware AeroAPI validation path (kept off here)

The pipeline includes a second, targeted resolution method that was **deliberately
left disabled for this run**. `scripts/15_resolve_operator_ambiguity.py` can issue a
single-flight historical lookup (`GET /history/flights/{ident}`) against the FlightAware
AeroAPI for each otherwise-unresolved row, inspecting that flight's codeshares for an
`AA`/`UA`/`DL`/`AS`-prefixed identifier to recover the operating contract. It is a
narrow per-flight query — never a bulk pull — gated independently by
`resolve_operator_ambiguity.enabled` and a `max_queries` budget, and it no-ops safely
(writing an empty resolution file) when `FLIGHTAWARE_API_KEY` is unset, so no other
stage ever depends on a live key. Because the bigrun was executed **keyless**, this
path produced no resolutions, which is the direct and expected cause of the 14.7%
exclusion above. Enabling a key in future work would reassign most of those 904,924
flights to `American_Eagle`, `United_Express`, `Delta_Connection`, or `Alaska` contracts,
and would in particular let the ORD–SPI rank-1 hotspot and similar `OO`/`YX` cells be
attributed to a named operator — the single largest available improvement to attribution
coverage.
