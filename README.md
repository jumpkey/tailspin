# Tailspin

Assorted ad-hoc studies across airline performance and scheduling data.

This repository collects small, targeted projects for airline-related data
collection and analysis. Each study lives in its own subdirectory.

---

## Projects

### [flight-fragility-poc](flight-fragility-poc/README.md)

**Status: Pipeline implemented — awaiting live data run**

A reproducible proof-of-concept analysis to determine whether American Airlines'
regional service in LFT and nearby spoke markets shows greater weather-related
schedule fragility than comparable peer markets.

**Business question:** Does AA regional service in LFT and nearby small-spoke
markets show a larger increase in cancellations and severe delays under marginal
or adverse weather than comparable peer markets?

**Approach:**
- BTS On-Time Performance data (2024–2025) for AA regional, UA peer, and DL peer
  route baskets out of LFT, BTR, AEX, MLU, GPT, and SHV.
- FAA ASPM cancelled-flights-with-weather data for independent weather
  classification at the route-hour level.
- Weather buckets: benign / marginal / adverse (FAA ASPM severity, with
  text-descriptor fallback).
- Deliverable: one executive-ready PNG chart plus supporting CSVs, produced
  by a single-command pipeline with no manual spreadsheet work.

**Quantitative results:** Pipeline smoke-tested with synthetic data; live data run
pending. See [`flight-fragility-poc/output/`](flight-fragility-poc/output/)
for placeholder artifacts and [`flight-fragility-poc/AAR.md`](flight-fragility-poc/AAR.md)
for the After Action Report.

**Quick start:**
```bash
cd flight-fragility-poc
pip install -r requirements.txt
bash scripts/run_pipeline.sh
```