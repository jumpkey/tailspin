## 3. Study Design

### 3.1 Unit of analysis

The study's atomic observation is a scheduled flight, but every comparative claim is built on a single aggregation grain:

> **hub × spoke × operator_class × weather_bucket × period**

Each dimension is defined operationally and resolved entirely from public data:

| Dimension | Definition | Levels |
|---|---|---|
| `hub` | The American Airlines hub airport, assigned origin-priority (see §5) | DFW, CLT, ORD, PHL, MIA, PHX, DCA, LAX, JFK |
| `spoke` | The non-hub endpoint of a hub-touching flight | 255 discovered spokes (264 airports total incl. hubs) |
| `operator_class` | The carrier/regional operator inferred from BTS reporting + route context | AA_mainline, Envoy_operated, PSA_operated, SkyWest_unresolved, Republic_unresolved, Other_or_non_AA |
| `weather_bucket` | Endpoint ASOS-derived condition severity (§6) | benign (None/Minor), marginal (Moderate), adverse (Severe) |
| `period` | A binary split at `baseline_end`, set by `period_flag` in the fact builders | baseline vs. recent |

Holding four dimensions fixed and varying the fifth is what isolates an operator's behavior from confounds such as a hub's structural weather exposure or a corridor's traffic mix. The grain is also what makes the operator-attribution discipline enforceable: the 904,924 ambiguity-flagged flights (14.7% of 6,152,599) are excluded at this grain rather than guessed, and small cells (<30 flights, `min_sample_threshold`) are flagged indicative rather than dropped silently.

### 3.2 Hub and spoke universe

Hubs are not discovered — they are the fixed scope of the study (American's nine mainline operational hubs and gateways) and are listed explicitly in `run_mode_hubs`. **Spokes, by contrast, are discovered from the data.** Any airport that appears as the non-hub endpoint of a flight touching one of the nine hubs in the study window enters the spoke universe. No external route list is imposed; the network is reconstructed from the BTS On-Time records themselves. The big-run scope resolved to **264 airports (9 hubs + 255 spokes)** across **6,152,599 flights**, with a **100.0% weather match (0.0% null)** after the ASOS join.

A consequence worth flagging: because hub attribution uses origin-priority, hub-level totals are **not directly comparable across run modes** (a flight can only be charged to one hub). This is acceptable within a single run but means the 4-hub `local` baseline and the 9-hub `bigrun` cannot be differenced naively.

### 3.3 Main study and the 2026 carve-out

Two configs drive two temporally distinct runs over the same code path:

| | Main study (`study.yaml`) | 2026 carve-out (`study_2026.yaml`) |
|---|---|---|
| Study window | 2024-01-01 → 2025-12-31 (24 mo.) | 2024-01-01 → 2026-04-30 |
| `baseline` period | 2024 (Jan–Dec) | 2024–2025 |
| `recent` period | 2025 (Jan–Dec) | 2026 (Jan–Apr) |

The `period` split is implemented identically in both: `period_flag` is set at `baseline_end`, cleanly partitioning each fact row into baseline vs. recent. The carve-out reuses every threshold, weather rule, weight vector, and operator-class definition from the main study — **only the temporal split differs** — so any change between the two outputs is attributable to time, not method. The carve-out writes to separate `*_2026` curated paths (`run_2026_carveout.sh`) so the committed 2024-vs-2025 analysis is never overwritten.

The 2026 recent period is deliberately bounded at **Jan–Apr 2026**: these are the only BTS-published months as of June 2026. This is a four-month, winter-heavy partial year and is the single largest external-validity caveat in the carve-out.

### 3.4 Season-matching the partial year

Comparing a Jan–Apr 2026 partial year against a full 2024–25 baseline would conflate seasonality (winter operations are structurally worse) with genuine year-over-year change. To remove this, **every 2026 comparison is season-matched**: 2026 Jan–Apr is compared only against the **same Jan–Apr months of 2024–25**, never against the full baseline year. This does not eliminate the small-sample limitation, but it removes the dominant confound. All 2026 figures reported downstream (e.g., network-wide cancellation and severe-delay shifts, the DFW–LFT corridor) are season-matched on this basis.

### 3.5 Run modes

A single `run_mode` switch (`test` | `local` | `bigrun`) selects both the hub set and the time window, so the pipeline scales from a smoke test to the full network without code changes:

| Mode | Hubs | Window | Purpose |
|---|---|---|---|
| `test` | DFW | Jan 2024 (1 mo.) | Fast smoke test / CI |
| `local` | DFW, CLT, ORD, PHL | full window | Developer iteration on a laptop-sized slice |
| `bigrun` | all 9 hubs | full window | Canonical result (264 airports, 6.15M flights) |

`bigrun` must be set explicitly — an empty hub list raises `ValueError` in `resolve_scope()`, a guard against a silently empty canonical run. All headline figures in this report come from `bigrun` on the `duckdb` backend, completing in roughly **63 minutes of wall-clock on a 72-core / 503 GB host**.
