-- Gold layer: KPI contract views over silver_*. Read-only — no base-table
-- writes anywhere in this file. Revenue definition mirrors calibration_check.py:
-- quantity * unit_price_at_sale - line_discount, completed orders only for
-- money KPIs. Gold trusts silver: no dirty-data re-filtering here.

DROP VIEW IF EXISTS gold_order_revenue;
CREATE VIEW gold_order_revenue AS
SELECT o.order_id, o.customer_id, o.order_ts, o.order_status, o.payment_method,
       i.order_revenue, i.units, i.line_count
FROM silver_orders o
LEFT JOIN (
  SELECT order_id,
         SUM(quantity * unit_price_at_sale - COALESCE(line_discount, 0)) AS order_revenue,
         SUM(quantity) AS units,
         COUNT(*) AS line_count
  FROM silver_order_items
  GROUP BY order_id
) i ON i.order_id = o.order_id;

DROP VIEW IF EXISTS gold_monthly_kpis;
CREATE VIEW gold_monthly_kpis AS
SELECT DATE_FORMAT(order_ts, '%Y-%m') AS order_month,
       COUNT(*) AS completed_orders,
       SUM(order_revenue) AS revenue,
       AVG(order_revenue) AS aov,
       COUNT(DISTINCT customer_id) AS unique_buyers
FROM gold_order_revenue
WHERE order_status = 'completed'
GROUP BY DATE_FORMAT(order_ts, '%Y-%m');

DROP VIEW IF EXISTS gold_funnel;
CREATE VIEW gold_funnel AS
SELECT s.step_order, s.event_type, s.events,
       s.events / LAG(s.events) OVER (ORDER BY s.step_order) AS conversion_from_prev,
       s.events / FIRST_VALUE(s.events) OVER (ORDER BY s.step_order) AS conversion_from_top
FROM (
  SELECT CASE event_type
           WHEN 'page_view' THEN 1
           WHEN 'product_view' THEN 2
           WHEN 'add_to_cart' THEN 3
           WHEN 'begin_checkout' THEN 4
           WHEN 'purchase' THEN 5
         END AS step_order,
         event_type,
         COUNT(*) AS events
  FROM silver_web_events
  GROUP BY event_type
) s;

DROP VIEW IF EXISTS gold_channel_cac_monthly;
CREATE VIEW gold_channel_cac_monthly AS
SELECT DATE_FORMAT(spend_date, '%Y-%m') AS spend_month,
       channel,
       SUM(spend_amount) AS spend,
       SUM(impressions) AS impressions,
       SUM(clicks) AS clicks,
       SUM(attributed_signups) AS attributed_signups,
       SUM(spend_amount) / NULLIF(SUM(attributed_signups), 0) AS cac_attributed
FROM silver_marketing_spend
GROUP BY DATE_FORMAT(spend_date, '%Y-%m'), channel;

DROP VIEW IF EXISTS gold_customer_summary;
CREATE VIEW gold_customer_summary AS
SELECT c.customer_id, c.signup_date, c.acquisition_channel, c.country,
       COUNT(r.order_id) AS orders_all,
       COALESCE(SUM(r.order_status = 'completed'), 0) AS orders_completed,
       COALESCE(SUM(CASE WHEN r.order_status = 'completed'
                         THEN r.order_revenue END), 0) AS revenue_completed,
       MIN(CASE WHEN r.order_status = 'completed' THEN r.order_ts END) AS first_completed_ts,
       MAX(CASE WHEN r.order_status = 'completed' THEN r.order_ts END) AS last_completed_ts
FROM silver_customers c
LEFT JOIN gold_order_revenue r ON r.customer_id = c.customer_id
GROUP BY c.customer_id, c.signup_date, c.acquisition_channel, c.country;

DROP VIEW IF EXISTS gold_nps_monthly;
CREATE VIEW gold_nps_monthly AS
SELECT DATE_FORMAT(review_ts, '%Y-%m') AS review_month,
       COUNT(nps_score) AS nps_responses,
       AVG(nps_score) AS nps_mean,
       (SUM(nps_score >= 9) - SUM(nps_score <= 6)) / COUNT(nps_score) * 100 AS nps,
       COUNT(star_rating) AS star_responses,
       AVG(star_rating) AS star_mean
FROM silver_reviews_nps
GROUP BY DATE_FORMAT(review_ts, '%Y-%m');
