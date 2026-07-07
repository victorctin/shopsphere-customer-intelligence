-- Silver layer: cleaned, typed tables. Keys NOT NULL + PRIMARY KEY,
-- CHECK constraints on business ranges. FKs documented in comments but not
-- enforced (bulk-load friendly; standard medallion practice).
DROP TABLE IF EXISTS silver_customers;
CREATE TABLE silver_customers (
  customer_id VARCHAR(16) NOT NULL, signup_date DATE NOT NULL,
  acquisition_channel VARCHAR(32) NOT NULL, country VARCHAR(64) NOT NULL,
  city VARCHAR(80), birth_year INT, gender VARCHAR(8),
  email VARCHAR(160), marketing_opt_in TINYINT NOT NULL,
  email_valid TINYINT NOT NULL,
  PRIMARY KEY (customer_id),
  CHECK (email_valid IN (0, 1))
) ENGINE=InnoDB;

DROP TABLE IF EXISTS silver_products;
CREATE TABLE silver_products (
  product_id VARCHAR(16) NOT NULL, product_name VARCHAR(80) NOT NULL,
  category VARCHAR(40) NOT NULL, subcategory VARCHAR(80),
  unit_price DECIMAL(10,2) NOT NULL, unit_cost DECIMAL(10,2) NOT NULL,
  launch_date DATE,
  PRIMARY KEY (product_id),
  CHECK (unit_price > 0), CHECK (unit_cost >= 0)
) ENGINE=InnoDB;

-- FK (documented): customer_id -> silver_customers.customer_id
DROP TABLE IF EXISTS silver_orders;
CREATE TABLE silver_orders (
  order_id VARCHAR(16) NOT NULL, customer_id VARCHAR(16) NOT NULL,
  order_ts DATETIME NOT NULL, order_status VARCHAR(16) NOT NULL,
  payment_method VARCHAR(24), shipping_country VARCHAR(64),
  discount_amount DECIMAL(10,2), shipping_fee DECIMAL(10,2),
  ts_conflict TINYINT NOT NULL,
  PRIMARY KEY (order_id),
  CHECK (ts_conflict IN (0, 1))
) ENGINE=InnoDB;

-- FKs (documented): order_id -> silver_orders, product_id -> silver_products
DROP TABLE IF EXISTS silver_order_items;
CREATE TABLE silver_order_items (
  order_item_id VARCHAR(20) NOT NULL, order_id VARCHAR(16) NOT NULL,
  product_id VARCHAR(16) NOT NULL, quantity INT NOT NULL,
  unit_price_at_sale DECIMAL(12,2) NOT NULL, line_discount DECIMAL(10,2),
  PRIMARY KEY (order_item_id),
  CHECK (quantity > 0), CHECK (unit_price_at_sale >= 0)
) ENGINE=InnoDB;

-- FK (documented): customer_id -> silver_customers (nullable: anonymous sessions)
DROP TABLE IF EXISTS silver_web_sessions;
CREATE TABLE silver_web_sessions (
  session_id VARCHAR(16) NOT NULL, customer_id VARCHAR(16),
  session_start_ts DATETIME NOT NULL, device_type VARCHAR(16),
  traffic_source VARCHAR(24), landing_page VARCHAR(80), campaign_id VARCHAR(40),
  PRIMARY KEY (session_id)
) ENGINE=InnoDB;

-- FK (documented): session_id -> silver_web_sessions
DROP TABLE IF EXISTS silver_web_events;
CREATE TABLE silver_web_events (
  event_id VARCHAR(20) NOT NULL, session_id VARCHAR(16) NOT NULL,
  event_type VARCHAR(24) NOT NULL, event_ts DATETIME NOT NULL,
  product_id VARCHAR(16), order_id VARCHAR(16),
  PRIMARY KEY (event_id)
) ENGINE=InnoDB;

DROP TABLE IF EXISTS silver_marketing_spend;
CREATE TABLE silver_marketing_spend (
  spend_date DATE NOT NULL, channel VARCHAR(24) NOT NULL,
  spend_amount DECIMAL(12,2) NOT NULL, impressions BIGINT NOT NULL,
  clicks BIGINT NOT NULL, attributed_signups INT NOT NULL,
  PRIMARY KEY (spend_date, channel),
  CHECK (spend_amount >= 0), CHECK (impressions >= 0), CHECK (clicks >= 0)
) ENGINE=InnoDB;

-- FKs (documented): session_id -> silver_web_sessions, customer_id -> silver_customers
DROP TABLE IF EXISTS silver_ab_test_assignments;
CREATE TABLE silver_ab_test_assignments (
  assignment_id VARCHAR(20) NOT NULL, session_id VARCHAR(16) NOT NULL,
  customer_id VARCHAR(16), test_name VARCHAR(48) NOT NULL,
  variant VARCHAR(16) NOT NULL, assigned_date DATE NOT NULL,
  converted_flag TINYINT NOT NULL, order_id VARCHAR(16),
  PRIMARY KEY (assignment_id),
  CHECK (converted_flag IN (0, 1))
) ENGINE=InnoDB;

-- FKs (documented): customer_id -> silver_customers, order_id -> silver_orders
DROP TABLE IF EXISTS silver_reviews_nps;
CREATE TABLE silver_reviews_nps (
  review_id VARCHAR(16) NOT NULL, customer_id VARCHAR(16) NOT NULL,
  order_id VARCHAR(16), review_ts DATETIME NOT NULL,
  star_rating INT, nps_score INT, review_channel VARCHAR(24),
  PRIMARY KEY (review_id),
  CHECK (star_rating BETWEEN 1 AND 5), CHECK (nps_score BETWEEN 0 AND 10)
) ENGINE=InnoDB;
