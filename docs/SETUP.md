# Setup & Reproduction Guide

Everything needed to rebuild the ShopSphere data warehouse from a fresh clone.

## Prerequisites

- **Python 3.11+**
- **MySQL 8** (server running on `127.0.0.1:3306`)
- **Power BI Desktop** (for the BI phases; not needed to generate data)

## 1. Clone and create the environment

```bash
git clone <repo-url>
cd "E-commerce Customer Intelligence System"
python -m venv .venv
.venv/Scripts/activate        # Windows
pip install -r requirements.txt
```

## 2. Create your `.env`

Copy the template and fill in a real password (never commit `.env` — it is gitignored):

```bash
cp .env.example .env
```

```
DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=shopsphere_dw
DB_USER=shopsphere_app
DB_PASSWORD=<your-password>
```

The pipeline fails fast with `RuntimeError: DB_PASSWORD is not set` if this step is skipped.

## 3. Create the database and app user (as root)

```bash
mysql -u root -p < sql/00_setup/00_create_database.sql
```

This creates `shopsphere_dw` and the least-privilege `shopsphere_app` user.

## 4. Smoke test the connection

```bash
.venv/Scripts/python python/00_smoke_test.py
```

Expected: MySQL version printed and a `_smoke` round-trip confirmation.

## 5. Create the bronze tables

```bash
.venv/Scripts/python python/01_generate/apply_bronze_ddl.py
```

Expected: `Executed 9 statements from 01_bronze_tables.sql` (plus drops on re-run).

## 6. Generate and load the data

```bash
.venv/Scripts/python python/01_generate/run_all.py
```

Expected output (~5–15 min; the MySQL load dominates):

```
  customers                 12,000 rows -> bronze_customers
  products                     500 rows -> bronze_products
  orders                    19,687 rows -> bronze_orders
  order_items               30,980 rows -> bronze_order_items
  web_sessions             800,000 rows -> bronze_web_sessions
  web_events             1,431,441 rows -> bronze_web_events
  marketing_spend            3,650 rows -> bronze_marketing_spend
  ab_test_assignments       60,000 rows -> bronze_ab_test_assignments
  reviews_nps                4,452 rows -> bronze_reviews_nps
```

The run also writes `data/raw/*.csv` and `docs/dirty_data_manifest.md`
(the ground-truth defect counts for the Phase 2 cleaning).

## 7. Run the calibration gate

```bash
.venv/Scripts/python python/01_generate/calibration_check.py
echo $?    # must be 0
```

Expected: 8 `PASS` lines and `docs/calibration_report.md` refreshed. A non-zero
exit means the generated store no longer behaves like a real one — do not
proceed to later phases until it passes.

## 8. Power BI connectivity check

1. Install **MySQL Connector/NET** (required by Power BI's MySQL connector).
2. Open Power BI Desktop → **Get Data → MySQL database**.
3. Server: `127.0.0.1:3306` — Database: `shopsphere_dw`.
4. Credentials: Database tab, user `shopsphere_app` + your `.env` password.
5. Confirm the Navigator lists all **9 `bronze_*` tables**.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `Authentication plugin 'caching_sha2_password' cannot be loaded` (Power BI or old clients) | `ALTER USER 'shopsphere_app'@'localhost' IDENTIFIED WITH mysql_native_password BY '<password>';` then `FLUSH PRIVILEGES;` |
| Power BI: "This connector requires one or more additional components" | Download and install **MySQL Connector/NET** from dev.mysql.com/downloads/connector/net, then restart Power BI |
| `RuntimeError: DB_PASSWORD is not set` | Create `.env` from `.env.example` (Step 2) |
| `Access denied for user 'shopsphere_app'` | Re-run Step 3 as root; verify the password in `.env` matches the one granted |
| `Can't connect to MySQL server on '127.0.0.1'` | Start the MySQL 8 service; confirm port 3306 |
