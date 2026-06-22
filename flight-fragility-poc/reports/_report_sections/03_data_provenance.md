## 2. Data & Provenance

This study uses **only public data**. There are two required sources — U.S. DOT
Bureau of Transportation Statistics (BTS) On-Time Performance and NOAA ASOS
hourly weather — and one optional, dormant source (FlightAware AeroAPI) used
solely for targeted operator-ambiguity resolution and not exercised in the
results reported here (no API key was set). No internal airline operational,
crew, maintenance, or passenger-manifest data is used or available.

### 2.1 What each source provides

| Source | Provides | Grain | Role |
|---|---|---|---|
| BTS TranStats On-Time Performance | Scheduled and actual departure/arrival times, cancellation flags, delay minutes, and BTS delay-cause codes (carrier, late-aircraft, weather, NAS, security) | One row per scheduled flight | Primary outcome data: cancellations, severe delays, controllable/cascade decomposition |
| NOAA ASOS hourly METAR (via Iowa Environmental Mesonet) | Hourly airport-level observations — visibility, ceiling, present-weather codes | One row per station per hour | Weather stratification at each flight's departure and arrival airport-hour |

BTS supplies every outcome the fragility framework measures. Because BTS
On-Time Performance carries no marketing-carrier field distinct from the
reporting/operating carrier code, operator attribution is derived from
`carrier_code` plus route-context inference (Section 5); the two genuinely
ambiguous codes (`OO` SkyWest, `YX` Republic) account for the 904,924 flights
(14.7%) conservatively excluded from operator comparisons. NOAA ASOS supplies
the weather classification. Weather is assigned at the **endpoint
airport-hours** (departure and arrival), not en route — a documented
simplification (Section 12) that is reasonable for short-haul spoke-to-hub legs
but does not capture in-flight frontal passage or turbulence.

### 2.2 Vintages and study windows

The main study covers **January 2024 through December 2025 (24 months)**. The
2026 carve-out covers **January–April 2026** — the only BTS-published months as
of June 2026 — and is always compared **season-matched** to the same Jan–Apr
months of 2024–25, mitigating (though not eliminating) the winter-heavy bias of
a four-month partial year. BTS monthly archives can be **revised upstream**;
the manifests (Section 2.4) fix the extraction vintage for reproducibility.

### 2.3 Acquisition method and public/licensing status

Both required sources are public and free to redistribute; neither requires
credentialed access.

- **BTS** is downloaded as BTS's pre-built **monthly PREZIP archives** rather
  than through the TranStats form, which would require ASP.NET ViewState/session
  tokens. The PREZIP path needs no session or form fields. At bigrun scale this
  is 24 national monthly files (~27 MB each, ~650 MB).
- **NOAA ASOS** is fetched **per station-month** from the Iowa Environmental
  Mesonet endpoint, with **retry-with-backoff** (30/60/120/240/480 s) to absorb
  429/503 rate-limit responses. The fetch is throttle-bound, not
  transfer-bound: the bigrun spanned 264 airports (9 hubs + 255 discovered
  spokes) across 24 months.

An earlier design called for FAA ASPM weather reports; that source was rejected
because it requires a restricted FAA-registered login and covers only cancelled
flights. NOAA ASOS replaced it and provides weather for all flights, cancelled
or not.

### 2.4 Manifests as audit log

Every ETL script writes a `manifest.csv` recording row counts, extraction
timestamps, source parameters, and **SHA-256 checksums** for each downloaded
file. Raw files are treated as immutable once downloaded (refreshed only with
`--force`), and all downstream steps are deterministic given the staged inputs
and config. No manual spreadsheet editing or copy/paste occurs at any step.
The manifests (`data/raw/bts_hubspoke/manifest.csv`,
`data/raw/faa_hubspoke/manifest.csv`) are committed even though the bulk raw
CSVs are gitignored, so the provenance trail survives without shipping
multi-gigabyte data in the repository.

### 2.5 Weather match and dataset footprint

The bigrun achieved a **100.0% weather match** — every one of the **6,152,599**
flights joined to a NOAA observation, with **0.0% null** on `weather_bucket`.
(For context, the smaller focal-corridor Module A run reported 99.3% departure /
99.8% arrival match, and the container local-mode run 96.6%; the national bigrun
attained complete coverage.) Unmatched flights, where they occur, fall into an
`unknown` bucket and are excluded from weather-stratified analysis rather than
imputed.

The full national bigrun ran in **~63 minutes** of wall-clock time on a
72-core / 503 GB host using the duckdb backend. The underlying raw + curated
dataset (~**4.9 GB**) was **archived** rather than committed; the repository
ships the committed result files in `output/` plus the manifests. Because the
sources are public and the manifests pin vintage and checksums, **the entire
study is reproducible from public sources** by re-running the documented
pipeline (`run_pipeline.sh` → `run_pipeline_iv.sh` → `run_pipeline_v.sh`).
