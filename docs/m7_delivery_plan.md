# M7 — Delivery Plan (written 2026-07-10, before implementation)

Goal in one line: turn the gold layer into two stakeholder artifacts — an Excel
executive workbook built and validated programmatically, and a 5-page Power BI
product built live into Power BI Desktop via the modeling tools.

## Decisions already made (Victor, 2026-07-10)

- openpyxl approved as a new pinned dependency (Excel engine).
- Power BI route: live build via MCP into an open Power BI Desktop instance
  (Store version 2.155.756.0 confirmed installed); Victor opens a blank file.
  Page visuals are placed by Victor from a per-page checklist — the modeling
  tools build the semantic model (tables, relationships, DAX measures), not
  the report canvas.

## Deliverable 1 — Excel executive workbook

- Builder: `python/05_delivery/build_excel_workbook.py` (new dir `05_delivery`).
- Output: `reports/shopsphere_executive_workbook.xlsx`.
- Source of truth: gold views only, read via the existing engine factory
  (`python/config/db.py`). No writes to the database of any kind.
- Sheets:
  1. `Executive Summary` — headline KPIs: total completed revenue, AOV,
     one-time buyer rate, cart abandonment, paid CAC, NPS, A/B lift.
  2. `Monthly Trend` — `gold_revenue_trend` + line chart (revenue, MoM).
  3. `Funnel` — `gold_funnel` + bar chart.
  4. `Channel CAC` — `gold_channel_cac_monthly` aggregated per channel + bar chart.
  5. `Cohort Retention` — `gold_cohort_retention` pivoted to a matrix with a
     color scale.
  6. `Top Products` — `gold_top_products` top 10 per category.
  7. `RFM Segments` — same 9-rule (R,F) grid as notebook 02 (rule logic
     mirrored; drift guarded by the validation gate below).
  8. `AB Test` — free_shipping_threshold summary (same pooled z-test /
     delta-method formulas as notebook 04).
- Validation gate (in the same script, after writing): re-open the workbook
  and assert key cells equal freshly SQL-computed values — total revenue
  1,664,813.13, AOV within ±0.5% of 93.9564, RFM buyer total 11,323, A/B lift
  within 0.005 of 0.151. Non-zero exit on any mismatch.

## Deliverable 2 — Power BI 5-page product

- Model built live via powerbi-modeling tools into the open Desktop instance;
  data source = MySQL `shopsphere_dw` gold views (Victor's existing MySQL
  connector / ODBC).
- Import-mode tables: gold_monthly_kpis, gold_revenue_trend, gold_funnel,
  gold_channel_cac_monthly, gold_customer_summary, gold_cohort_retention,
  gold_top_products, gold_nps_monthly + a Calendar table.
- DAX measure set: Total Revenue, AOV, Orders, Buyers, Repeat Rate, One-time
  Rate, Abandonment %, CAC (paid), NPS, MoM Revenue %, Cumulative Revenue,
  Retention % (cohort). Exact formulas mirror the gold KPI contract
  (completed orders only; revenue = qty × unit price − discount).
- Pages (visuals placed by Victor from the checklist doc):
  1. Executive Overview — KPI cards + revenue trend.
  2. Funnel & Acquisition — funnel chart, CAC by channel, spend vs revenue.
  3. Customers & Segments — RFM/pareto, one-time vs repeat.
  4. Retention Cohorts — cohort matrix heatmap.
  5. Experiment — A/B result cards + CI visual.
- Checklist doc: `docs/m7_powerbi_page_checklist.md`.

## Gates before claiming done

- Excel: builder script exits 0 including its internal assert gate; numbers
  pasted into the report.
- Power BI: DAX queries executed against the built model return Total Revenue
  = 1,664,813.13 and AOV within ±0.5% of 93.9564 (run via dax_query tools).
- Standard gates re-run: pytest (count never drops from 55), calibration 8/8.

## Out of scope for M7

- Final PDF and LinkedIn wrap-up (M8).
- Publishing to Power BI Service (local Desktop file only).
