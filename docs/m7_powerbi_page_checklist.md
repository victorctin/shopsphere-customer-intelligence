# M7 — Power BI 5-page build checklist

The semantic model (tables, relationships, DAX measures) is built into the open
Power BI Desktop instance by the orchestrator via the modeling tools. This doc
is the by-hand part: which visuals to place on each page and which fields and
measures they use.

## Model contents

- Tables (9): `gold_order_revenue` (order grain — feeds Total Revenue/AOV),
  `gold_customer_summary`, `gold_monthly_kpis`, `gold_revenue_trend`,
  `gold_funnel`, `gold_channel_cac_monthly`, `gold_cohort_retention`,
  `gold_top_products`, `gold_nps_monthly`.
- Measures (12), spread across tables: Total Revenue, Completed
  Orders, AOV, Unique Buyers, One-time Rate, Repeat Rate, Abandonment %,
  Paid CAC, NPS Overall (renamed — `gold_nps_monthly` already has a column
  `nps`), MoM Revenue %, Cumulative Revenue, AB Lift %.

## Page 1 — Executive Overview

- [ ] 5 KPI cards across the top: Total Revenue, AOV, Unique Buyers,
      One-time Rate, Paid CAC.
- [ ] Line chart: `gold_revenue_trend[order_month]` on X, Total Revenue on Y;
      add Cumulative Revenue as a second line (secondary axis optional).
- [ ] Column chart: `gold_monthly_kpis[order_month]` vs Completed Orders.
- [ ] Text box: one-sentence retention-trap framing (69% never reorder while
      CAC climbs).

## Page 2 — Funnel & Acquisition

- [ ] Funnel visual: `gold_funnel[event_type]` (sorted by `step_order`),
      values = `events`.
- [ ] Card: Abandonment %.
- [ ] Clustered bar: `gold_channel_cac_monthly[channel]` vs SUM of `spend`.
- [ ] Line chart: `spend_month` vs SUM `spend`, legend = `channel`.
- [ ] Table: channel, SUM spend, SUM attributed_signups, Paid CAC.

## Page 3 — Customers & Segments

- [ ] Histogram-style column chart: `gold_customer_summary[orders_completed]`
      (bin at 1,2,3,4,5+) vs count of customers — the one-time cliff.
- [ ] Cards: Unique Buyers, One-time Rate, Repeat Rate.
- [ ] Scatter or bar from `gold_customer_summary`: acquisition_channel vs
      AVG revenue_completed.
- [ ] Bar: `gold_top_products[product_name]` vs `revenue`, filter
      `category_rank` <= 5, small multiples or legend by `category`.

## Page 4 — Retention Cohorts

- [ ] Matrix visual: rows = `gold_cohort_retention[cohort_month]`, columns =
      `months_since_first`, values = AVERAGE `retention_rate`.
- [ ] Conditional formatting on values: background color scale white → blue,
      min 0, max 0.15.
- [ ] Card: cohort_size of the largest cohort (optional).
- [ ] Slicer: cohort_month range.

## Page 5 — Experiment (free_shipping_threshold)

- [ ] Cards: AB Lift % (+15.1%), p-value 7.9e-04, achieved power 91.9%
      (last two as static text boxes — they come from notebook 04, not the
      model).
- [ ] Clustered column: variant vs conversion rate (create a small table from
      Enter Data if preferred: control 3.43%, treatment 3.95%).
- [ ] Text box: guardrail caveat — converted-order revenue $88.80 vs $97.36,
      Welch p = 0.071 (suggestive basket shrink, not significant); revenue per
      assignment still favors treatment ($3.17 vs $3.00).
- [ ] Recommendation callout: ship, monitor basket size.

## Result Numbers

- Total Revenue card = 1,664,813.13
- AOV = 93.96 (±0.5%)
- Unique Buyers = 11,323
- One-time Rate = 69.2%
- Paid CAC = 73.89
