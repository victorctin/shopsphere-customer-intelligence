-- Gold layer: window-function analyses. Depends on 01_gold_kpi_views.sql
-- (gold_monthly_kpis, gold_order_revenue, gold_customer_summary).

DROP VIEW IF EXISTS gold_revenue_trend;
CREATE VIEW gold_revenue_trend AS
SELECT order_month,
       revenue,
       revenue - LAG(revenue) OVER (ORDER BY order_month) AS revenue_change,
       revenue / LAG(revenue) OVER (ORDER BY order_month) - 1 AS mom_growth,
       SUM(revenue) OVER (ORDER BY order_month) AS cumulative_revenue,
       AVG(revenue) OVER (ORDER BY order_month
                          ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) AS revenue_3mo_avg
FROM gold_monthly_kpis;

DROP VIEW IF EXISTS gold_customer_pareto;
CREATE VIEW gold_customer_pareto AS
SELECT customer_id,
       revenue_completed,
       ROW_NUMBER() OVER (ORDER BY revenue_completed DESC, customer_id) AS revenue_rank,
       COUNT(*) OVER () AS buyer_count,
       SUM(revenue_completed) OVER (ORDER BY revenue_completed DESC, customer_id)
         / NULLIF(SUM(revenue_completed) OVER (), 0) AS cumulative_share
FROM gold_customer_summary
WHERE orders_completed > 0;

DROP VIEW IF EXISTS gold_customer_order_seq;
CREATE VIEW gold_customer_order_seq AS
SELECT customer_id, order_id, order_ts, order_status, order_revenue,
       ROW_NUMBER() OVER (PARTITION BY customer_id
                          ORDER BY order_ts, order_id) AS order_index,
       DATEDIFF(order_ts,
                LAG(order_ts) OVER (PARTITION BY customer_id
                                    ORDER BY order_ts, order_id)) AS days_since_prev_order
FROM gold_order_revenue;

DROP VIEW IF EXISTS gold_top_products;
CREATE VIEW gold_top_products AS
SELECT p.category, p.product_id, p.product_name,
       t.revenue, t.units,
       RANK() OVER (PARTITION BY p.category ORDER BY t.revenue DESC) AS category_rank,
       t.revenue / SUM(t.revenue) OVER (PARTITION BY p.category) AS category_share
FROM silver_products p
JOIN (
  SELECT i.product_id,
         SUM(i.quantity * i.unit_price_at_sale - COALESCE(i.line_discount, 0)) AS revenue,
         SUM(i.quantity) AS units
  FROM silver_order_items i
  JOIN silver_orders o ON o.order_id = i.order_id AND o.order_status = 'completed'
  GROUP BY i.product_id
) t ON t.product_id = p.product_id;
