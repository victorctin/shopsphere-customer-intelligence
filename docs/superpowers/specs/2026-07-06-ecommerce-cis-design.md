# E-commerce Customer Intelligence System — Design Document

**Date:** 2026-07-06
**Author:** Victor Constantin Pavel
**Purpose:** Portfolio Project

---

## Executive Summary

An end-to-end customer analytics project for a fictional mid-size online retailer, **ShopSphere**, built the way a real analytics team would build it: raw data lands in a MySQL warehouse, is cleaned and modeled in layers, analyzed in Python, and delivered through a Power BI dashboard, an Excel executive workbook.

**Tools:** MySQL 8 (SQL) · Python 3.11+ (pandas, matplotlib, scikit-learn, lifetimes, scipy, statsmodels) · Power BI Desktop · Microsoft Excel (one targeted deliverable).

**Anchor business problem:** retention. ShopSphere acquires customers successfully, but ~70% never place a second order while customer acquisition cost keeps rising. The system answers three questions leadership cannot currently answer:

1. **Who are our valuable customers?** (segmentation, RFM, CLV)
2. **Who is about to leave, and why?** (churn analysis, cohorts, funnel leaks)
3. **Where should the next marketing dollar go?** (CAC vs CLV by channel, ROAS, A/B testing)

### Research grounding (why retention is THE e-commerce problem, 2025–2026)

- Average e-commerce customer retention rate: **~31%** (Envive, 2026 benchmarks) — the lowest of any major industry (media/insurance sit at ~84%).
- Average DTC repeat purchase rate: **25–30%**: top consumable brands reach 40–55% (Finsi, 2026).
- Average e-commerce CAC: **$68–84**, up **~40% in two years** (Ringly/Shopify Global Commerce Report, 2026).
- Retaining a customer costs **5–25x less** than acquiring a new one (HBR range, reconfirmed by Releva 2026 analysis).
- Typical session-to-order conversion: **~2–3%**: cart abandonment: **~70%** (Baymard Institute).

---

## Success Criteria

The project is done when ALL of the following are true:

1. A stranger can clone the repo, and reproduce the entire pipeline (generate → load → clean → analyze → export marts) with one orchestrator command per phase.
2. Every requested technique is present and business-framed: cleaning, EDA, RFM, funnel, feature engineering, combined segmentation, KPI analysis, A/B testing, CLV (historical + predictive), churn model, cohort analysis.
3. Power BI dashboard (5 pages) connects to MySQL gold marts and answers the three leadership questions.
4. All KPIs from the brief are computed and defined in a KPI dictionary: Conversion Rate, CTR, ROAS, CAC, AOV, Revenue, Retention Rate, Repeat Purchase Rate, CSAT/NPS, plus Churn Rate, CLV, CLV:CAC, Cart Abandonment Rate, Purchase Frequency, Avg Days Between Purchases, MER, New vs Returning Revenue Share.
5. A non-technical PDF explains the whole project in plain language (why / objective / implementation / impact / deliverables per stage).
6. Synthetic data passes its calibration checks, the store's KPIs land within realistic benchmark ranges.

---

## Architecture

**Approach chosen:** Layered warehouse pipeline (medallion-style), approved over notebook-centric and SQL-heavy alternatives.

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

**Division of labor (each tool does what it's best at, and each earns its CV line):**

- **SQL (MySQL 8):** DDL for all layers, cleaning constraints, the KPI layer as views/stored queries using window functions (RFM scoring in SQL, cohort matrix in SQL, retention by month in SQL); gold marts for BI.
- **Python:** data generation, cleaning orchestration, statistical analysis, ML (K-Means, churn classifier, BG/NBD + Gamma-Gamma).
- **Power BI:** the interactive product for stakeholders, star-schema model over gold marts, DAX measures, 5 report pages.
- **Excel:** one executive KPI workbook.

**Conventions:**

- Config in `python/config/settings.py` + `.env` (never hardcoded credentials: `.env.example` committed).
- Every phase has an orchestrator script (`run_*.py`) so each phase is one command.
- Random seed fixed (`RANDOM_SEED = 42`) — fully reproducible dataset.
- All figures saved to `reports/figures/` at LinkedIn-friendly resolution (1200×675 or square).

---

## Data Model & Dictionary

Nine linked tables, ~2.4M rows total (volumes derived from the behavioral rules in §4.1 so all benchmark rates hold simultaneously), covering **2024-07-01 → 2026-06-30** (24 months — enough for cohort and seasonality analysis). Dates use `YYYY-MM-DD`, timestamps `YYYY-MM-DD HH:MM:SS`.

| # | Table | Grain | ~Rows | Key columns |
|---|-------|-------|------:|-------------|
| 1 | `customers` | 1 row / customer | 12,000 | customer_id (PK), signup_date, acquisition_channel, country, city, birth_year, gender, email, marketing_opt_in |
| 2 | `products` | 1 row / SKU | 500 | product_id (PK), product_name, category (8 categories), subcategory, unit_price, unit_cost, launch_date |
| 3 | `orders` | 1 row / order | ~20,000 | order_id (PK), customer_id (FK), order_ts, order_status (completed/cancelled/returned), payment_method, shipping_country, discount_amount, shipping_fee |
| 4 | `order_items` | 1 row / product-in-order | ~32,000 | order_item_id (PK), order_id (FK), product_id (FK), quantity, unit_price_at_sale, line_discount |
| 5 | `web_sessions` | 1 row / session | 800,000 | session_id (PK), customer_id (FK, nullable = anonymous), session_start_ts, device_type, traffic_source, landing_page, campaign_id (nullable) |
| 6 | `web_events` | 1 row / funnel step | ~1,430,000 | event_id (PK), session_id (FK), event_type (page_view → product_view → add_to_cart → begin_checkout → purchase), event_ts, product_id (nullable), order_id (nullable, purchase only) |
| 7 | `marketing_spend` | 1 row / day / channel | ~3,650 | spend_date, channel (paid_search, paid_social, email, affiliate, display), spend_amount, impressions, clicks, attributed_signups |
| 8 | `ab_test_assignments` | 1 row / session in test window | 60,000 | assignment_id (PK), session_id (FK), customer_id (FK, nullable), test_name ('free_shipping_threshold'), variant (control/treatment), assigned_date, converted_flag, order_id (nullable) |
| 9 | `reviews_nps` | 1 row / review | ~4,600 | review_id (PK), customer_id (FK), order_id (FK), review_ts, star_rating (1–5), nps_score (0–10), review_channel |

**Relationships (star-friendly):** customers 1—N orders 1—N order_items N—1 products, customers 1—N web_sessions 1—N web_events, web_events.purchase links to orders, marketing_spend joins on date+channel to sessions.traffic_source and customers.acquisition_channel, ab_test_assignments hangs off web_sessions, reviews_nps hangs off customers/orders.

### Behavioral realism rules (baked into generators, verified by calibration checks)

- **Pareto concentration:** top ~20% of customers generate ~55–60% of revenue.
- **Retention reality:** ~69% of customers are one-time buyers, repeat-purchase probability increases with each successive order (2nd→3rd easier than 1st→2nd).
- **Funnel decay:** session → product_view 65% of sessions → add_to_cart ~13% of product viewers → begin_checkout 40% of carts → purchase 75% of checkouts (net session→order ≈ 2.5%, cart abandonment ≈ 70%).
- **Channel economics differ:** email traffic converts ~3x paid_social, paid channels have realistic CPC and CTR ranges, affiliate has high ROAS but low volume.
- **Seasonality:** November–December peak (~1.8x baseline), January slump, mild summer dip, weekday > weekend for B2C electronics.
- **Order values:** log-normal AOV around $85–95, category-dependent basket composition.
- **Satisfaction links behavior:** low star ratings / detractor NPS raise churn probability, promoters have higher repeat rates.
- **A/B test has a real (small) effect:** treatment (lower free-shipping threshold) lifts session conversion by a plausible ~15% relative, detectable at 30k sessions per arm but requiring a proper power-aware test — a deliberate teaching moment.

### Deliberate data-quality defects

Injected at generation time, documented in a manifest (`docs/dirty_data_manifest.md`) so cleaning results can be verified against ground truth:

- ~1.5% duplicate order rows (same order, double-loaded)
- ~2% missing emails, ~1% malformed emails, scattered NULL cities
- Mixed-case / whitespace country names ("uk", " United Kingdom ")
- ~0.5% negative or zero quantities, a handful of absurd prices (unit price ×100 fat-finger)
- Timestamps: some events before session start, some orders before signup (system clock issues)
- Orphan records: order_items pointing to a missing order_id (~0.2%)
- Cancelled/returned orders that must be excluded from revenue KPIs but kept for ops analysis

---

## KPI Dictionary (calculation contracts)

All KPIs computed in SQL (gold layer) unless noted. "Completed orders only" excludes cancelled/returned.

| KPI | Formula | Grain |
|-----|---------|-------|
| Revenue | Σ(quantity × unit_price_at_sale − line_discount) + shipping − order discounts, completed orders | day/month/channel/category |
| AOV | Revenue ÷ # completed orders | month/segment |
| Conversion Rate | # sessions with purchase ÷ # sessions | day/channel/device |
| CTR | clicks ÷ impressions (marketing_spend) | day/channel |
| ROAS | attributed revenue ÷ spend | month/channel |
| CAC | spend ÷ new customers acquired | month/channel |
| Retention Rate (monthly) | customers active in month M who were also active in M−1 ÷ customers active in M−1 | month |
| Repeat Purchase Rate | customers with ≥2 lifetime completed orders ÷ all customers with ≥1 | overall/cohort |
| Churn Rate | customer is "churned" if no completed order in trailing 180 days (category-appropriate for electronics/lifestyle) | month/segment |
| Cart Abandonment Rate | 1 − (checkouts completed ÷ carts created) | day/device |
| CLV (historical) | Σ customer margin to date | customer |
| CLV (predictive) | BG/NBD expected purchases × Gamma-Gamma expected value, 12-month horizon | customer |
| CLV:CAC | segment avg CLV ÷ blended CAC of acquisition channel | segment/channel |
| NPS | %promoters (9–10) − %detractors (0–6) | month |
| CSAT | avg star_rating | month/category |
| Purchase Frequency | completed orders ÷ distinct buying customers | period |
| Avg Days Between Purchases | mean inter-order gap per repeat customer | segment |
| MER (blended) | total revenue ÷ total marketing spend | month |
| New vs Returning Revenue Share | revenue split by first-order flag | month |

---

## Roadmap


### Foundation
- **Setup:** repo scaffolding, venv + `requirements.txt`, `.env` config, MySQL database `shopsphere_dw` + bronze DDL, smoke test (Python↔MySQL and Power BI↔MySQL connectivity verified early). 
- **Data generation:** 9 seeded generators + `run_all.py`: calibration test script asserts KPI targets (§4.1) within tolerance: dirty-data injection (§4.2): load to bronze. ~2.4M rows in MySQL, `docs/01_DATA_MODEL_AND_DICTIONARY.md`, calibration report.

### Trust the Data
- **Cleaning:** bronze→silver with explicit rule-by-rule audit (rows in/out per rule), typed silver DDL with constraints, data-quality report comparing found defects vs the manifest. silver layer, `docs/data_quality_report.md`.
- **EDA:** revenue over time, AOV distribution, top products/categories, geography, customer concentration (Pareto chart), new vs returning, basket size, weekday patterns. Each chart annotated with an insight sentence. 

### SQL Analytics Core
- **KPI layer in SQL:** every KPI in §5 as a documented SQL view/query in `sql/30_kpi/`, window functions showcased (running revenue, MoM growth, rank-by-category). Python validation notebook cross-checks 3 KPIs against pandas. *

### Who Are Our Customers
- **RFM segmentation:** R/F/M quintile scoring **in SQL** (NTILE window functions), 10 named business segments (Champions, Loyal, At Risk, Hibernating…), segment sizing + revenue share. 
- **Funnel analysis:** step conversion overall and by device/channel/new-vs-returning, identify the biggest leak, quantify the revenue upside of fixing it ("+1pp checkout completion = $X/yr"). 
- **Behavioral feature engineering:** Customer-360 table — ~25 features (recency, tenure, order stats, session intensity, cart-abandon count, category diversity, discount affinity, review sentiment proxy, channel preference…). 
- **Combined segmentation:** K-Means on scaled Customer-360 features (k chosen by elbow + silhouette, interpretability prioritized), cross-tab vs RFM segments, personas with names and marketing actions. 

### Value & Risk
- **Cohort analysis:** monthly acquisition cohorts × retention heatmap (SQL cohort matrix + Python viz), revenue cohorts (LTV curves by cohort), cohort quality by acquisition channel. 
- **CLV:** historical CLV distribution, predictive CLV with BG/NBD + Gamma-Gamma (`lifetimes`), validated on a holdout period, CLV by segment/channel, CLV:CAC economics per channel. 
- **Churn prediction:** label = churn definition  computed at a snapshot date with features strictly from before it (leakage-safe design explained explicitly), logistic regression baseline → random forest / gradient boosting comparison, evaluation with ROC-AUC + precision-recall + calibration, feature importance → actionable "who to save" list sized by expected value. 

### Experimentation
- **A/B test analysis:** free-shipping-threshold test, hypothesis → power analysis (was n sufficient?) → two-proportion z-test + confidence intervals → guardrail metrics (AOV, margin, did lower threshold hurt profitability?) → ship/no-ship recommendation with revenue projection. 

### Delivery
- **Gold marts:** star-schema mart set for BI (`gold_sales_daily`, `gold_customer_360`, `gold_funnel_daily`, `gold_cohort_retention`, `gold_marketing_channel_monthly`, `gold_ab_test_results`, dim tables), refresh script. 
- **Power BI dashboard (5 pages):**
  1. **Executive Overview** — revenue, AOV, orders, conversion, MER, NPS trend, YoY.
  2. **Customer Segments** — RFM + persona breakdown, segment revenue share, migration.
  3. **Funnel & Acquisition** — funnel viz, CAC/ROAS/CTR by channel, spend vs revenue.
  4. **Retention & Cohorts** — cohort heatmap, retention curves, repeat rate trends.
  5. **CLV & Churn Risk** — CLV distribution, CLV:CAC by channel, churn-risk deciles, "revenue at risk."
  Star schema + documented DAX measures, slicers for date/channel/segment/category. 

### Communication
- **Insights & recommendations + Excel:** consolidated top-10 insights, each: finding → evidence → recommended action → estimated impact, Excel executive KPI workbook .   `excel/shopsphere_executive_kpis.xlsx`.
- **Final packaging:** non-technical report

---

## Power BI Model Spec

- **Import mode** from MySQL, refreshable.
- Star schema: fact tables `gold_sales_daily`, `gold_funnel_daily`, `gold_marketing_channel_monthly`, dimensions `dim_date`, `dim_customer` (from customer_360: includes segment/persona/churn decile/CLV band), `dim_product`, `dim_channel`.
- DAX measure groups: Revenue & Orders, Rates (conversion/retention/repeat/abandon), Marketing (CAC/ROAS/CTR/MER), Customer Value (CLV, CLV:CAC), Satisfaction (NPS/CSAT).
- Design: consistent theme, top-left KPI cards, one key visual per page answering one question, every page titled as a question (e.g., "Where do we lose customers?").

## Excel Deliverable Spec

`excel/shopsphere_executive_kpis.xlsx` 

- Sheet 1 "Monthly KPIs": 24 months × core KPI table with conditional formatting and sparklines.
- Sheet 2 "Channel Economics": CAC, ROAS, CLV:CAC by channel, flagged winners/losers.
- Sheet 3 "Segment Summary": RFM/persona sizes, revenue share, recommended action per segment.
- Rationale: executives and finance consume Excel, this shows the analyst can meet stakeholders where they are.

## Final PDF Spec

`reports/final/ShopSphere_Customer_Intelligence_Report.pdf` — written for a non-technical reader:

- Structure: the problem → the data → each stage as a short chapter (*why it matters / business objective / what was done technically, in plain words / business impact ) → the 10 insights → the recommendations with expected impact → appendix (KPI definitions).
- Every chart has a one-sentence takeaway caption. No unexplained jargon, every technical term gets a parenthetical plain-language gloss on first use.

---

## 12. Environment & Tooling

- Windows 11, Python 3.11+ in project venv, MySQL 8.x local server, Power BI Desktop (installed), VS Code.
- Python deps (pinned in requirements.txt): pandas, numpy, SQLAlchemy, PyMySQL, python-dotenv, faker, matplotlib, seaborn, scikit-learn, scipy, statsmodels, lifetimes, openpyxl, jupyter.
- Secrets: `.env` only (DB user/password), `.env.example` committed, `.env` gitignored. DB user is a least-privilege `shopsphere_app` account, not root.

