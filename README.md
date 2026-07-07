# ShopSphere — E-commerce Customer Intelligence System

**The problem:** ShopSphere, a mid-size online retailer, keeps buying growth it
cannot keep. Roughly 69% of its customers never place a second order, while
customer acquisition costs keep climbing — the classic e-commerce retention
trap. This project builds the full analytics stack to diagnose and attack that
problem: a layered MySQL warehouse, SQL KPI contracts, Python statistical and
ML analysis (RFM, cohorts, CLV, churn, A/B testing), and a Power BI product for
stakeholders — end to end, from raw data to boardroom PDF.

`Python 3.11` · `MySQL 8` · `SQLAlchemy` · `pandas / numpy` · `pytest` · `Power BI` · `Excel`

## Architecture

```
┌─────────────────┐     ┌───────────────────────── MySQL: shopsphere_dw ─────────────────────────┐
│ Python          │     │                                                                         │
│ data generators │──►  │  BRONZE (raw, as-landed)  ──►  SILVER (clean, typed)  ──►  GOLD (marts) │
│ (faker+numpy,   │     │  bronze_* tables               silver_* tables             gold_* views │
│  seeded)        │     │                                                            & tables     │
└─────────────────┘     └───────────────┬─────────────────────┬───────────────────────┬──────────┘
                                        │                     │                       │
                                        ▼                     ▼                       ▼
                                 Python cleaning        Python notebooks         Power BI (5 pages)
                                 + quality report       (EDA, RFM, funnel,       Excel exec workbook
                                                        segmentation, cohorts,   Final PDF report
                                                        CLV, churn, A/B)
```

## Status

| Milestone | Scope | Status |
|---|---|---|
| **M1 — Foundation** | Synthetic data engine, bronze layer, calibration gate | ✅ Done |
| M2 — Trust the Data | Cleaning to silver + data-quality report vs manifest | Planned |
| M3 — SQL Analytics Core | KPI views, window functions, cohort matrix in SQL | Planned |
| M4 — Who Are Our Customers | EDA, RFM, segmentation | Planned |
| M5 — Value & Risk | CLV (BG/NBD + Gamma-Gamma), churn model | Planned |
| M6 — Experimentation | Power-aware A/B test analysis | Planned |
| M7 — Delivery | Power BI (5 pages), Excel exec workbook | Planned |
| M8 — Communication | Final PDF + LinkedIn series wrap-up | Planned |

## Quickstart

Full reproduction guide (MySQL setup, `.env`, pipeline, Power BI connectivity):
**[docs/SETUP.md](docs/SETUP.md)**. Short version:

```bash
pip install -r requirements.txt
cp .env.example .env                                   # fill in DB_PASSWORD
mysql -u root -p < sql/00_setup/00_create_database.sql
python python/01_generate/apply_bronze_ddl.py
python python/01_generate/run_all.py                   # generate + load ~2.36M rows
python python/01_generate/calibration_check.py         # hard gate: 8 checks must PASS
```

Data model and column dictionary: [docs/01_DATA_MODEL_AND_DICTIONARY.md](docs/01_DATA_MODEL_AND_DICTIONARY.md).

## A note on the data

**All data is synthetic** — generated with a fixed seed, no real customers
anywhere. It is deliberately calibrated to 2026 industry benchmarks (retention,
funnel decay, AOV, CAC, seasonality) and passes an 8-check calibration gate
([docs/calibration_report.md](docs/calibration_report.md)) so every downstream
analysis exercises realistic patterns, including a documented layer of injected
data-quality defects for the cleaning phase to catch.
