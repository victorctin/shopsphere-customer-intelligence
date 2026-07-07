-- Bronze layer: raw landing tables. Deliberately NO PK/FK/NOT NULL,
-- because generated data contains injected quality defects.
DROP TABLE IF EXISTS bronze_customers;
CREATE TABLE bronze_customers (
  customer_id VARCHAR(16), signup_date DATE, acquisition_channel VARCHAR(32),
  country VARCHAR(64), city VARCHAR(80), birth_year INT, gender VARCHAR(8),
  email VARCHAR(160), marketing_opt_in TINYINT
) ENGINE=InnoDB;

DROP TABLE IF EXISTS bronze_products;
CREATE TABLE bronze_products (
  product_id VARCHAR(16), product_name VARCHAR(80), category VARCHAR(40),
  subcategory VARCHAR(80), unit_price DECIMAL(10,2), unit_cost DECIMAL(10,2),
  launch_date DATE
) ENGINE=InnoDB;

DROP TABLE IF EXISTS bronze_orders;
CREATE TABLE bronze_orders (
  order_id VARCHAR(16), customer_id VARCHAR(16), order_ts DATETIME,
  order_status VARCHAR(16), payment_method VARCHAR(24),
  shipping_country VARCHAR(64), discount_amount DECIMAL(10,2),
  shipping_fee DECIMAL(10,2)
) ENGINE=InnoDB;

DROP TABLE IF EXISTS bronze_order_items;
CREATE TABLE bronze_order_items (
  order_item_id VARCHAR(20), order_id VARCHAR(16), product_id VARCHAR(16),
  quantity INT, unit_price_at_sale DECIMAL(12,2), line_discount DECIMAL(10,2)
) ENGINE=InnoDB;

DROP TABLE IF EXISTS bronze_web_sessions;
CREATE TABLE bronze_web_sessions (
  session_id VARCHAR(16), customer_id VARCHAR(16), session_start_ts DATETIME,
  device_type VARCHAR(16), traffic_source VARCHAR(24),
  landing_page VARCHAR(80), campaign_id VARCHAR(40)
) ENGINE=InnoDB;

DROP TABLE IF EXISTS bronze_web_events;
CREATE TABLE bronze_web_events (
  event_id VARCHAR(20), session_id VARCHAR(16), event_type VARCHAR(24),
  event_ts DATETIME, product_id VARCHAR(16), order_id VARCHAR(16)
) ENGINE=InnoDB;

DROP TABLE IF EXISTS bronze_marketing_spend;
CREATE TABLE bronze_marketing_spend (
  spend_date DATE, channel VARCHAR(24), spend_amount DECIMAL(12,2),
  impressions BIGINT, clicks BIGINT, attributed_signups INT
) ENGINE=InnoDB;

DROP TABLE IF EXISTS bronze_ab_test_assignments;
CREATE TABLE bronze_ab_test_assignments (
  assignment_id VARCHAR(20), session_id VARCHAR(16), customer_id VARCHAR(16),
  test_name VARCHAR(48), variant VARCHAR(16), assigned_date DATE,
  converted_flag TINYINT, order_id VARCHAR(16)
) ENGINE=InnoDB;

DROP TABLE IF EXISTS bronze_reviews_nps;
CREATE TABLE bronze_reviews_nps (
  review_id VARCHAR(16), customer_id VARCHAR(16), order_id VARCHAR(16),
  review_ts DATETIME, star_rating INT, nps_score INT, review_channel VARCHAR(24)
) ENGINE=InnoDB;
