# M3 Plan — SQL Analytics Core (gold layer)

**Goal:** gold-layer KPI views, window-function analyses, and a cohort retention
matrix in pure SQL over the `silver_*` MySQL tables, with every headline number
cross-checked against the already-verified pandas values from the P3 notebook.

## Deliverables

| File | Contents |
|---|---|
| `sql/30_gold/01_gold_kpi_views.sql` | `gold_order_revenue` (per-order revenue base), `gold_monthly_kpis` (orders, revenue, AOV, buyers per month), `gold_funnel` (event counts, step conversion, cart abandonment), `gold_channel_cac_monthly` (spend, signups, CAC per channel/month), `gold_customer_summary` (per-customer orders/revenue/first/last — feeds M4 RFM), `gold_nps_monthly` |
| `sql/30_gold/02_gold_window_views.sql` | `gold_revenue_trend` (MoM growth via LAG, cumulative SUM OVER, 3-mo moving avg), `gold_customer_pareto` (revenue rank + cumulative share), `gold_customer_order_seq` (ROW_NUMBER order index, LAG days-between-orders), `gold_top_products` (RANK per category) |
| `sql/30_gold/03_gold_cohort_retention.sql` | `gold_cohort_retention`: cohort = first completed-order month, months-since via TIMESTAMPDIFF, cohort size + retained customers + retention rate |
| `python/03_gold/run_gold.py` | Applies the three SQL files via the existing `run_sql_file` helper, then runs the **M3 gate**: queries the views and asserts 5 numbers against the pandas-verified values — AOV $93.96, one-time buyer share 69.2%, cart abandonment 70.6%, top-20% revenue share 56.9%, blended paid CAC $73.89 (tolerance 0.5%). Exit 1 on any mismatch. |

## Defaults picked (technical forks)

- **All views, no materialized gold tables.** Data volume (1.4M events) aggregates
  in seconds; views are re-runnable and never stale. Revisit only if Power BI (M7)
  is slow.
- **Metric definitions mirror `calibration_check.py`:** revenue =
  `quantity * unit_price_at_sale - line_discount`, completed orders only.
  No dirty-data re-filtering in SQL — silver already dropped dupes/orphans/bad
  rows, so gold trusts silver (that is the point of the medallion).
- **Cohorts keyed to first completed-order month** (standard retention practice),
  not signup month.
- **CAC two ways:** blended paid CAC = total spend / customers acquired via
  `PAID_CHANNELS` (matches calibration), plus per-channel CAC from
  `attributed_signups` for the channel view.
- **DDL style:** `DROP VIEW IF EXISTS` + `CREATE VIEW`, applied through
  `run_sql_file` (same pattern as the silver DDL). No base-table writes anywhere.

