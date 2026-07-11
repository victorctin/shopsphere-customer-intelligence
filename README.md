# ShopSphere — E-commerce Customer Intelligence System

**The problem:** ShopSphere, a mid-size online retailer, keeps buying growth it
cannot keep. **69.2% of its customers never place a second order** while
acquisition costs climb — the classic e-commerce retention trap. This project
builds the full analytics stack to diagnose and attack that problem: a layered
MySQL warehouse, SQL KPI contracts, Python statistics and ML (RFM, cohorts,
CLV, churn, A/B testing), and executive deliverables — end to end, from a
random seed to a boardroom PDF.

`Python 3.11` · `MySQL 8` · `SQLAlchemy` · `pandas / numpy / scipy / scikit-learn` · `pytest` · `Power BI` · `Excel`

## Architecture

```
┌─────────────────┐     ┌───────────────────────── MySQL: shopsphere_dw ─────────────────────────┐
│ Python          │     │                                                                         │
│ data generators │──►  │  BRONZE (raw, as-landed)  ──►  SILVER (clean, typed)  ──►  GOLD (marts) │
│ (faker+numpy,   │     │  bronze_* tables               silver_* tables             gold_* views │
│  seeded)        │     │                                                                         │
└─────────────────┘     └───────────────┬─────────────────────┬───────────────────────┬──────────┘
                                        │                     │                       │
                                        ▼                     ▼                       ▼
                                 Python cleaning        Python notebooks         Power BI semantic model
                                 + graded quality       (EDA, RFM, cohorts,      Excel executive workbook
                                 report                 CLV, churn, A/B)         Final PDF report
```

## Headline results

| Question | Answer |
|---|---|
| How much revenue, how many buyers? | **$1.66M** completed revenue · 17,811 orders · 11,323 buyers over 24 months |
| Where does it leak? | **70.6%** cart abandonment · **69.2%** one-time buyers · top 20% of buyers = **56.9%** of revenue |
| Who are the customers? | 9 RFM segments — Champions are **4% of buyers but 12% of revenue** ($487 avg); Hibernating holds 30% of buyers |
| What are they worth? | 12-month CLV **$282,875** (BG/NBD + Gamma-Gamma, backtest pred/actual = 1.06); churn AUC **0.81** |
| What should we ship? | Free-shipping threshold A/B: **+15.1% conversion** (p = 7.9e-04, power 91.9%, SRM clean) — ship with a basket-size guardrail |

Full analysis: [`reports/shopsphere_final_report.pdf`](reports/shopsphere_final_report.pdf) ·
15 figures in [`reports/figures/`](reports/figures/) ·
build-in-public write-ups in [`linkedin/`](linkedin/)

![Monthly revenue](reports/figures/monthly_revenue.png)

## What makes this different: everything is gated

No number ships unverified. Each layer has an automated gate that fails the
build on drift:

| Gate | What it proves | Result |
|---|---|---|
| Calibration (`calibration_check.py`) | Synthetic data matches 2026 industry benchmarks | **8/8 PASS** |
| Data-quality report vs manifest | Cleaning caught every injected defect class | **9/9 PERFECT** |
| Gold KPI gate (`run_gold.py`) | SQL views match independent pandas recomputation (cohort matrix exact in 267/267 cells) | **5/5 PASS** |
| Excel workbook self-validation | Written cells match fresh SQL | **5/5 PASS** |
| Power BI DAX acceptance | Loaded model matches contract KPIs | **8/8 PASS** |
| PDF report self-validation | Rendered KPIs match fresh SQL, all figures embedded | **6/6 PASS** |
| pytest suite | Unit + integration coverage | **66 passed** |

The same contract number — completed revenue **$1,664,813.13** — appears in
the SQL gate, the Excel workbook, the Power BI model, and the PDF report,
because each one is audited against the gold layer at build time.

## Milestones

| Milestone | Scope | Status |
|---|---|---|
| **M1 — Foundation** | Seeded data engine (8 realism rules), bronze layer, calibration gate | ✅ |
| **M2 — Trust the Data** | Bronze → silver cleaning, graded against a ground-truth defect manifest | ✅ |
| **M3 — SQL Analytics Core** | 12 gold views: KPIs, window functions, cohort matrix in pure SQL | ✅ |
| **M4 — Who Are Our Customers** | RFM scoring + 9-segment rule grid | ✅ |
| **M5 — Value & Risk** | CLV (BG/NBD + Gamma-Gamma on scipy) + churn model, time-split backtest | ✅ |
| **M6 — Experimentation** | Power-aware A/B analysis: SRM, MDE, achieved power, revenue guardrail | ✅ |
| **M7 — Delivery** | Excel executive workbook + Power BI semantic model (9 tables, 12 measures) | ✅ |
| **M8 — Communication** | Final PDF report + LinkedIn series (P00–P08) | ✅ |

## Quickstart

Full reproduction guide (MySQL setup, `.env`, pipeline, Power BI connectivity):
**[docs/SETUP.md](docs/SETUP.md)**. Short version:

```bash
pip install -r requirements.txt
cp .env.example .env                                   # set your own DB_PASSWORD
mysql -u root -p < sql/00_setup/00_create_database.sql # edit CHANGE_ME first
python python/01_generate/apply_bronze_ddl.py
python python/01_generate/run_all.py                   # generate + load ~2.36M rows
python python/01_generate/calibration_check.py         # hard gate: 8 checks must PASS
python python/02_clean/run_clean.py --load-db          # bronze -> silver, graded
python python/03_gold/run_gold.py                      # gold views + KPI gate
python python/05_delivery/build_excel_workbook.py      # Excel deliverable
python python/05_delivery/build_final_report.py        # HTML + PDF deliverable
```

Data model and column dictionary: [docs/01_DATA_MODEL_AND_DICTIONARY.md](docs/01_DATA_MODEL_AND_DICTIONARY.md).

## Repository map

```
python/
  01_generate/   seeded generators, dirty-data injector, calibration gate
  02_clean/      bronze -> silver cleaning + graded quality report
  03_gold/       gold view application + KPI gate
  04_model/      BG/NBD + Gamma-Gamma implementation (scipy)
  05_delivery/   Excel workbook + PDF report builders (self-validating)
notebooks/       4 executed analysis notebooks (EDA, RFM, CLV/churn, A/B)
sql/             DDL: setup, bronze, silver, 12 gold views
docs/            data model, setup, calibration + quality reports, milestone plans
reports/         figures, Excel workbook, Power BI .pbix, final PDF
linkedin/        the build-in-public series, P00–P08
tests/           66 pytest tests
```

## A note on the data

**All data is synthetic** — generated with a fixed seed, no real customers
anywhere. It is deliberately calibrated to 2026 industry benchmarks (retention,
funnel decay, AOV, CAC, seasonality) and passes an 8-check calibration gate
([docs/calibration_report.md](docs/calibration_report.md)), including a
documented layer of injected data-quality defects for the cleaning phase to
catch ([docs/dirty_data_manifest.md](docs/dirty_data_manifest.md)).

## License

MIT — see [LICENSE](LICENSE).
