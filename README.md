# Tailspin

Assorted ad-hoc studies across airline performance and scheduling data.

This repository collects small, targeted projects for airline-related data
collection and analysis. Each study lives in its own subdirectory; design
specifications live at the repository root.

---

## Projects

### [flight-fragility-poc](flight-fragility-poc/)

**Status: Analysis complete (national 9-hub run + 2026 carve-out); reporting and
stakeholder materials in draft.**

What began as a single question — *why is American's DFW–Lafayette service so
unreliable, especially in bad weather?* — grew into a reproducible, public-data
study of schedule fragility across American Airlines' entire hub network.

**Scope (current):**
- **6,152,599 flights** across American's **9 hubs** (DFW, CLT, ORD, PHL, MIA,
  PHX, DCA, LAX, JFK) and **264 airports**, Jan 2024 – Dec 2025, plus a
  **season-matched 2026 carve-out** (Jan–Apr 2026, the BTS-published months).
- **Public data only:** U.S. DOT BTS On-Time Performance + NOAA ASOS hourly
  weather (100% weather match). Fully reproducible; archived raw dataset ≈ 4.9 GB.
- Five analytical passes (**Fragility I–V**): focal-corridor baseline → operator
  attribution → a network hotspot-scoring engine ranking 1,668 route-operator
  cells.

**Headline findings (associational, not causal — see the report's weaknesses
section):**
- Schedule fragility is **concentrated and stable**, dominated by *knock-on*
  (late-inbound-aircraft) delays at thin regional spokes feeding DFW, ORD, and DCA.
- **PSA Airlines** (a wholly-owned American Eagle regional) is **~4.25×
  over-represented** in the worst-performing routes relative to its share of
  flights; **Envoy** (a second wholly-owned regional) is *under*-represented — a
  built-in fairness check that the finding is operating-structure-specific, not
  anti-regional.
- **Volume ≠ fragility:** the biggest hubs by traffic (LAX, PHX, JFK) are among
  the cleanest.
- **DFW–LFT** ranks in the **worst ~4%** of the network when PSA-operated and is
  now **~90% PSA** (the corridor rotated operators; Envoy has largely exited). The
  pattern **persisted into 2026**.

**Key documents:**
- 📌 [BIGRUN-FINDINGS-GUIDE.md](flight-fragility-poc/BIGRUN-FINDINGS-GUIDE.md) —
  top-level read-out; start here.
- [Full technical report](flight-fragility-poc/reports/FRAGILITY_FULL_REPORT.docx)
  (Word; [markdown source](flight-fragility-poc/reports/FRAGILITY_FULL_REPORT.md))
  — analyst-grade dossier incl. methodology, controls, and a candid
  structural-weaknesses section.
- [DFW–LFT focal report](flight-fragility-poc/reports/DFW_LFT_FOCAL_REPORT.md) ·
  [Network report draft](flight-fragility-poc/reports/FRAGILITY_NETWORK_REPORT_DRAFT.md)
- Draft stakeholder letters:
  [AA CEO](flight-fragility-poc/reports/letters/letter_AA_CEO_DRAFT.md) ·
  [AA leadership](flight-fragility-poc/reports/letters/letter_AA_stakeholders_DRAFT.md) ·
  [PSA/Envoy](flight-fragility-poc/reports/letters/letter_PSA_Envoy_stakeholders_DRAFT.md)
- Executive charts: [`flight-fragility-poc/output/exec/`](flight-fragility-poc/output/exec/)
  (specs: [CHART_SPECS_DRAFT.md](flight-fragility-poc/reports/CHART_SPECS_DRAFT.md))
- Engineering reference: [flight-fragility-poc/README.md](flight-fragility-poc/README.md) ·
  After-action history: [AAR.md](flight-fragility-poc/AAR.md) ·
  Server run guide: [FRANKENSERVER.md](flight-fragility-poc/FRANKENSERVER.md)
- Design specs (Fragility I–V): [flight-fragility-poc/spec/](flight-fragility-poc/spec/)

**Quick start:**
```bash
cd flight-fragility-poc
python3 -m venv .venv && source .venv/bin/activate   # repo-root .venv also works
pip install -r requirements.txt
bash scripts/run_bigrun.sh        # full Fragility I–V national run (~1 hr cold cache)
```
See [FRANKENSERVER.md](flight-fragility-poc/FRANKENSERVER.md) for the complete
run/restore workflow and [config/study.yaml](flight-fragility-poc/config/study.yaml)
for scope controls.

---

Design specifications are project-scoped and live with each project (e.g.
[flight-fragility-poc/spec/](flight-fragility-poc/spec/)).
