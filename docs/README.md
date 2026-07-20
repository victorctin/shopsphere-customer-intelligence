# Data Model & Dictionary

Nine linked tables, ~2.36M rows, covering **2024-07-01 → 2026-06-30** (24 months).
Dates are `YYYY-MM-DD`, timestamps `YYYY-MM-DD HH:MM:SS`. Row counts are actuals
from the seeded run (`RANDOM_SEED = 42`) and include the injected data-quality
defects documented in [dirty_data_manifest.md](dirty_data_manifest.md)

## Relationships

```
customers 1──N orders 1──N order_items N──1 products
    │
    └─1──N web_sessions 1──N web_events ──(purchase events)──► orders
                │
                └─1──0..1 ab_test_assignments
marketing_spend ──(spend_date+channel)──► web_sessions.traffic_source,
                                          customers.acquisition_channel
reviews_nps N──1 customers, N──1 orders
```

## 1. `customers` — 1 row / customer — 12,000 rows

Who signed up, when, and through which channel. Generated in
`gen_customers.generate_customers()`.

| Column | Type | Meaning | Example |
|---|---|---|---|
| customer_id | str (PK) | Unique customer key | `C10042` |
| signup_date | date | Account creation date (seasonal + growth-weighted) | `2025-11-14` |
| acquisition_channel | str | First-touch channel (6 values) | `paid_search` |
| country | str | Customer country | `United Kingdom` |
| city | str | Customer city (scattered NULLs injected) | `London` |
| birth_year | int | Year of birth | `1993` |
| gender | str | Self-reported gender | `female` |
| email | str | Contact email (~2% missing, ~1% malformed injected) | `amy.chen@example.com` |
| marketing_opt_in | int | 1 = consented to marketing | `1` |

## 2. `products` — 1 row / SKU — 500 rows

The catalog. Generated in `gen_products.generate_products()` (log-uniform
pricing per category).

| Column | Type | Meaning | Example |
|---|---|---|---|
| product_id | str (PK) | Unique SKU key | `P2107` |
| product_name | str | Display name | `Aurora Wireless Earbuds` |
| category | str | One of 8 categories | `electronics` |
| subcategory | str | Category refinement | `audio` |
| unit_price | float | Current list price | `59.99` |
| unit_cost | float | Cost of goods | `31.20` |
| launch_date | date | First day sellable | `2024-09-02` |

## 3. `orders` — 1 row / order — 19,687 rows (incl. ~1.5% injected duplicates)

The retention engine's output: repeat-purchase ladder, customer lifetimes,
seasonality. Generated in `gen_orders.generate_orders()`.

| Column | Type | Meaning | Example |
|---|---|---|---|
| order_id | str (PK) | Unique order key | `O1004521` |
| customer_id | str (FK) | Ordering customer | `C10042` |
| order_ts | datetime | Order placement time (evening-peaked) | `2025-12-02 20:14:00` |
| order_status | str | `completed` (92%) / `cancelled` / `returned` | `completed` |
| payment_method | str | card / paypal / apple_pay / google_pay / bank_transfer | `card` |
| shipping_country | str | Destination (90% = customer country) | `United Kingdom` |
| discount_amount | float | Order-level discount (≤50% of subtotal) | `10.00` |
| shipping_fee | float | 0 when subtotal ≥ 75, else 4.99 | `4.99` |

## 4. `order_items` — 1 row / product-in-order — 30,980 rows

Basket lines with price-elastic product selection. Generated in
`gen_orders.generate_orders()` (same call as orders).

| Column | Type | Meaning | Example |
|---|---|---|---|
| order_item_id | str (PK) | Unique line key | `OI2019344` |
| order_id | str (FK) | Parent order (~0.2% orphaned to `O9999999`) | `O1004521` |
| product_id | str (FK) | Purchased SKU | `P2107` |
| quantity | int | Units (~0.5% zero/negative injected) | `1` |
| unit_price_at_sale | float | Price paid (±5% of list; 15 fat-finger ×100) | `57.10` |
| line_discount | float | Line-level discount (10% of lines) | `5.71` |

## 5. `web_sessions` — 1 row / session — 800,000 rows

All traffic, converting and not. Generated in
`gen_sessions_events.generate_sessions_events()`.

| Column | Type | Meaning | Example |
|---|---|---|---|
| session_id | str (PK) | Unique session key | `S5000123` |
| customer_id | str (FK, nullable) | NULL = anonymous visitor | `C10042` |
| session_start_ts | datetime | Session start (hour-of-day weighted) | `2025-12-02 19:49:00` |
| device_type | str | mobile / desktop / tablet | `mobile` |
| traffic_source | str | 7 sources; email converts ~3x paid_social | `email` |
| landing_page | str | Entry URL path | `/sale` |
| campaign_id | str (nullable) | Set for paid sources only | `CMP-PAID-202512` |

## 6. `web_events` — 1 row / funnel step — 1,431,441 rows

The funnel: page_view → product_view → add_to_cart → begin_checkout → purchase.
Generated in `gen_sessions_events.generate_sessions_events()` (same call).

| Column | Type | Meaning | Example |
|---|---|---|---|
| event_id | str (PK) | Unique event key | `E10004821` |
| session_id | str (FK) | Parent session | `S5000123` |
| event_type | str | Funnel step (5 values) | `add_to_cart` |
| event_ts | datetime | Event time (some pre-session times injected) | `2025-12-02 19:55:00` |
| product_id | str (nullable) | Reserved for product-level events | `NULL` |
| order_id | str (nullable) | Set on `purchase` events only | `O1004521` |

## 7. `marketing_spend` — 1 row / day / channel — 3,650 rows

Daily paid-channel spend reconciled to CAC targets. Generated in
`gen_marketing.generate_marketing()`.

| Column | Type | Meaning | Example |
|---|---|---|---|
| spend_date | date | Spend day | `2025-12-02` |
| channel | str | paid_search / paid_social / display / email / affiliate | `paid_search` |
| spend_amount | float | Daily spend (smoothed signups × CAC × noise) | `812.40` |
| impressions | int | Ad impressions (from clicks / CTR) | `24,310` |
| clicks | int | Ad clicks (from spend / CPC) | `677` |
| attributed_signups | int | Signups attributed that day | `9` |

## 8. `ab_test_assignments` — 1 row / session in test window — 60,000 rows

The `free_shipping_threshold` experiment (2026-02-15 → 2026-04-30), built with a
real ~15% relative lift. Generated in `gen_ab_test.generate_ab_test()`.

| Column | Type | Meaning | Example |
|---|---|---|---|
| assignment_id | str (PK) | Unique assignment key | `AB100042` |
| session_id | str (FK) | Assigned session (no duplicates) | `S5000123` |
| customer_id | str (FK, nullable) | NULL for anonymous sessions | `C10042` |
| test_name | str | Always `free_shipping_threshold` in M1 | `free_shipping_threshold` |
| variant | str | `control` or `treatment` (30,000 each) | `treatment` |
| assigned_date | date | Assignment day | `2026-03-08` |
| converted_flag | int | 1 = session ended in purchase | `1` |
| order_id | str (nullable) | Set when converted | `O1018777` |

## 9. `reviews_nps` — 1 row / review — 4,452 rows

Reviews for 25% of completed orders; loyal repeat customers skew positive.
Generated in `gen_reviews.generate_reviews()`.

| Column | Type | Meaning | Example |
|---|---|---|---|
| review_id | str (PK) | Unique review key | `R300042` |
| customer_id | str (FK) | Reviewer | `C10042` |
| order_id | str (FK) | Reviewed order (completed only) | `O1004521` |
| review_ts | datetime | 3–21 days after the order | `2025-12-14 20:14:00` |
| star_rating | int | 1–5 stars | `4` |
| nps_score | int | 0–10, correlated with stars | `9` |
| review_channel | str | email_survey / onsite / app | `email_survey` |

## Behavioral realism rules — where each lives

| Rule | Implementation |
|---|---|
| Pareto concentration (top 20% ≈ 55–60% of revenue) | Emergent from `gen_orders._order_counts()` (repeat ladder) + popularity weighting in `gen_orders.generate_orders()` — verified at 0.570 |
| ~69% one-time buyers; repeat gets easier per order | `settings.REPEAT_LADDER` consumed by `gen_orders._order_counts()` — verified at 0.692 |
| Funnel decay (net ≈ 2.5% conversion, ~70% cart abandonment) | `settings.P_PRODUCT_VIEW/P_CART_GIVEN_VIEW/P_CHECKOUT_GIVEN_CART/P_BUY_GIVEN_CHECKOUT` in `gen_sessions_events.generate_sessions_events()` — verified at 0.024 / 0.706 |
| Channel economics differ (email ≈ 3x paid_social) | `TRAFFIC_CONV` / `TRAFFIC_NONCONV` in `gen_sessions_events`; `settings.CHANNEL_CAC/CPC/CTR` in `gen_marketing` — CAC verified at 73.9 |
| Nov–Dec seasonality peak, January slump | `_common.season_multiplier()` — verified at 1.400x |
| AOV ≈ $85–95, price-elastic baskets | Log-uniform prices in `gen_products`; `/price^0.7` elasticity in `gen_orders` — verified at 94.30 |
| Satisfaction links to behavior | `STAR_LOYAL` vs `STAR_BASE` distributions in `gen_reviews.generate_reviews()` |
| A/B test has a real, small effect (~15% relative) | `settings.AB_TREATMENT_LIFT` in `gen_ab_test.generate_ab_test()` — verified at 0.151 |

Full PASS table: [calibration_report.md](calibration_report.md).
