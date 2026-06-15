# After Action Report — Flight Fragility POC, Iteration 1

**Date:** 2026-06-15  
**Agent:** GitHub Copilot Coding Agent  
**Repository:** jumpkey/tailspin  
**Issue:** #1 — Initial implementation

---

## Summary

This report documents the decisions made, issues encountered, and open items from
the first coding iteration of the Flight Fragility POC.

The outcome of this iteration is a complete, runnable pipeline skeleton — all
scripts, configuration, and directory structure are implemented and ready to
execute against live data sources.  Actual quantitative study results are
**pending a live data run**; no network-accessible BTS or FAA data was fetched
during this sandboxed implementation session.

---

## Decisions made

### 1. Repository layout — subdirectory, not root

**Decision:** All study files are created under `flight-fragility-poc/` rather
than at the repository root.

**Rationale:** The agent instructions explicitly state: "The repository layout
in the spec document should be created in the study subdirectory, not in the
root; there will be other study projects — the spec is out of date in that
regard."  The root `README.md` was updated to summarize the project and point
to the study subdirectory.

---

### 2. BTS extraction approach — HTTP POST with fallback guidance

**Decision:** `10_extract_bts.py` implements a direct `requests.Session` HTTP
POST to the TranStats download endpoint, mirroring the browser form flow.
The script documents how to diagnose failures if the form structure changes.

**Rationale:** The spec's "Risks and Mitigations" section acknowledges that
TranStats uses web flows rather than a REST API.  A scripted HTTP POST is the
least-dependency approach.  The script is structured so the fetch logic can be
swapped for a Playwright/Selenium fallback without changing the staging output
contract.

**Open item:** If BTS changes its form field IDs or adds CAPTCHA, the extractor
will need updating.  Field codes are centralized in `BTS_FIELD_CODES` at the
top of the script for easy maintenance.

---

### 3. FAA ASPM extraction — ASP.NET ViewState session scraping

**Decision:** `11_extract_faa_weather.py` scrapes `__VIEWSTATE` and related
ASP.NET tokens from a GET request, then POSTs the report form.  If the POST
returns an empty or unparseable result, it writes an empty file and logs a
warning rather than aborting.

**Rationale:** The spec notes FAA ASPM may require session handling or
form-postback logic.  The script isolates this complexity and keeps the staging
output schema stable regardless of retrieval success.

**Open item:** The exact form field names for the ASPM Cancelled Flights with
Weather report may differ from the assumed names (`txtAirport`, `txtStartDate`,
etc.).  These should be inspected with browser DevTools against the live portal
before the first full run.

---

### 4. Weather bucket derivation — dual-path logic

**Decision:** Weather bucket classification uses FAA ASPM severity levels
(None / Minor / Moderate / Severe) as the primary path.  If those are absent
or unclear, it falls back to a keyword scan of raw weather text fields.

**Rationale:** The spec specifies both approaches (sections "Preferred approach"
and "Fallback approach").  Implementing both makes the pipeline robust to
variation in how FAA reports surface weather severity.

**Implementation note:** The exact columns that carry ASPM severity levels
depend on whether the FAA report includes a structured severity column or only
raw text.  The `derive_weather_bucket` function tries both `faa_dep_aspm_level`
(structured) and `faa_dep_ceiling` (which sometimes carries verbal severity in
ASPM exports) before falling back to text.

---

### 5. Chart rendering — Plotly primary, Matplotlib fallback

**Decision:** `40_plot_fragility.py` tries `plotly` + `kaleido` for PNG
export first.  If that fails (kaleido unavailable or version mismatch),
it falls back to `matplotlib`.

**Rationale:** The spec prefers Plotly + Kaleido for deterministic output but
explicitly allows a matplotlib fallback "if PNG rendering proves more stable."

---

### 6. FlightAware — gated behind config flag

**Decision:** `12_extract_flightaware.py` exits cleanly (writing an empty
staging file) when `use_flightaware: false` in `study.yaml`.  It is invoked
in `run_pipeline.sh` with `|| true` so a failure does not abort the pipeline.

**Rationale:** The spec designates FlightAware as a phase-2 optional layer.
Keeping it out of the critical path for phase 1 is explicitly required.

---

### 7. Idempotency and manifest audit trail

**Decision:** Each ETL script checks for existing raw files and skips
re-download unless `--force` is passed.  On download, it appends a row to
`manifest.csv` with source parameters, row count, extraction timestamp, and
a 16-character SHA-256 prefix.

**Rationale:** The spec requires idempotent reruns and audit manifests.

---

## Issues encountered

### I1 — No live network access during implementation session

**Issue:** The sandboxed environment does not have outbound network access to
BTS TranStats or FAA ASPM, so the pipeline could not be executed end-to-end
during this iteration.

**Management:** All scripts are implemented with full logic.  The first live run
should validate:
- BTS form field names and response format.
- FAA ViewState field names and HTML table structure.
- Join rates between BTS cancelled flights and FAA records.

Output files (`flight_operability_fact.csv`, `weather_fragility_chart_data.csv`,
`weather_fragility_exec_chart.png`, `qa_summary.csv`) will be populated on the
first successful live run.

### I2 — BTS field code mapping assumed from documentation

**Issue:** The numeric field codes used in the BTS download form
(`BTS_FIELD_CODES` in `10_extract_bts.py`) were derived from the TranStats
field reference, not confirmed against a live form response.

**Management:** The codes are centralized for easy update.  On first run,
compare against the actual form source with browser DevTools if needed.

### I3 — FAA form field names assumed

**Issue:** The FAA ASPM form fields (`txtAirport`, `txtArrAirport`,
`txtStartDate`, `txtEndDate`, `btnSubmit`) are assumed names; the actual
ASP.NET form may use different names.

**Management:** Logged as a first-run validation item.  Script gracefully
handles empty/failed responses and writes empty staging files so downstream
steps can still be tested structurally.

---

## Decisions to be made (open)

| # | Decision | Context |
|---|----------|---------|
| D1 | Confirm BTS form field IDs | Inspect TranStats download form with DevTools on first live run |
| D2 | Confirm FAA ASPM form field names | Inspect ASPM Cancelled Flights page source on first live run |
| D3 | Confirm FAA column names for ASPM severity | Determine whether the FAA report exports a structured "ASPM severity" column or only raw weather text |
| D4 | Validate route membership against observed BTS service | Some routes in the basket may have zero or sparse service in the study window; merge marginal/adverse buckets or expand basket if needed |
| D5 | Assess FAA–BTS join rate | If below 85 %, investigate mismatch in carrier codes or flight number formatting between sources |
| D6 | Decide on chart annotation wording | Current logic generates the annotation automatically from the ratio; review wording for executive audience after first data run |
| D7 | Phase 2 FlightAware evaluation | Decide whether to enable FlightAware for recency extension once phase-1 BTS/FAA results are in hand |

---

## Next steps

1. **Run the pipeline** in an environment with network access to BTS and FAA:
   ```bash
   cd flight-fragility-poc
   pip install -r requirements.txt
   bash scripts/run_pipeline.sh
   ```
2. **Validate extraction** by checking `data/raw/bts/manifest.csv` and
   `data/raw/faa/manifest.csv` row counts.
3. **Review QA summary** at `output/qa_summary.csv` for join rates and
   bucket sample sizes.
4. **Inspect the chart** at `output/weather_fragility_exec_chart.png`.
5. **Update this report** and the root `README.md` with actual quantitative
   results once the pipeline has run successfully.

---

*End of After Action Report — Iteration 1*
