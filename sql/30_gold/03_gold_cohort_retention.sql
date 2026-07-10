-- Gold layer: cohort retention matrix. Cohort = month of a customer's first
-- COMPLETED order; months_since_first counts calendar months from that cohort
-- month. Row (cohort, 0) is the cohort itself, so FIRST_VALUE = cohort size.

DROP VIEW IF EXISTS gold_cohort_retention;
CREATE VIEW gold_cohort_retention AS
SELECT act.cohort_month,
       act.months_since_first,
       act.active_customers,
       FIRST_VALUE(act.active_customers) OVER (
         PARTITION BY act.cohort_month
         ORDER BY act.months_since_first) AS cohort_size,
       act.active_customers / FIRST_VALUE(act.active_customers) OVER (
         PARTITION BY act.cohort_month
         ORDER BY act.months_since_first) AS retention_rate
FROM (
  SELECT fc.cohort_month,
         TIMESTAMPDIFF(MONTH, fc.cohort_first_day,
                       DATE_FORMAT(o.order_ts, '%Y-%m-01')) AS months_since_first,
         COUNT(DISTINCT o.customer_id) AS active_customers
  FROM (
    SELECT customer_id,
           DATE_FORMAT(MIN(order_ts), '%Y-%m') AS cohort_month,
           DATE_FORMAT(MIN(order_ts), '%Y-%m-01') AS cohort_first_day
    FROM silver_orders
    WHERE order_status = 'completed'
    GROUP BY customer_id
  ) fc
  JOIN silver_orders o
    ON o.customer_id = fc.customer_id AND o.order_status = 'completed'
  GROUP BY fc.cohort_month, fc.cohort_first_day,
           TIMESTAMPDIFF(MONTH, fc.cohort_first_day,
                         DATE_FORMAT(o.order_ts, '%Y-%m-01'))
) act;
