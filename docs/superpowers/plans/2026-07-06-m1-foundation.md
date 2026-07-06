# Milestone 1 (Foundation) Implementation Plan — Phase 0 Setup + Phase 1 Data Generation

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A reproducible project skeleton (venv, config, MySQL `shopsphere_dw` with bronze layer) plus ~2.4M rows of calibrated synthetic e-commerce data generated, dirtied, loaded to bronze, and verified against realism benchmarks.

**Architecture:** Python generators (numpy/faker, seeded) produce nine interlinked DataFrames obeying the behavioral rules in the spec (`docs/superpowers/specs/2026-07-06-ecommerce-cis-design.md` §4). A dirty-data injector adds known defects and writes a manifest. Data is saved to `data/raw/*.csv` and loaded into constraint-free `bronze_*` MySQL tables. A calibration script is the hard gate: it fails the build if KPIs drift outside benchmark ranges.

**Tech Stack:** Python 3.11+, pandas, numpy, Faker, SQLAlchemy + PyMySQL, MySQL 8, pytest.

## Global Constraints

- All commands run from repo root: `C:\Users\victo\Desktop\Cowork\PROJECTS\E-commerce Customer Intelligence System`
- Python venv at `.venv`; invoke as `.venv/Scripts/python` (Git Bash) — never system Python
- `RANDOM_SEED = 42` everywhere; generation must be fully reproducible (same seed → identical CSVs)
- No credentials in code or git: DB creds only in `.env` (gitignored); `.env.example` is the committed template
- Date range: `2024-07-01` → `2026-06-30`; dates `YYYY-MM-DD`, timestamps `YYYY-MM-DD HH:MM:SS`
- Bronze tables have NO primary keys, NO foreign keys, NO NOT NULL (raw layer must accept dirty data)
- Conventional commits (`feat:`, `test:`, `docs:`, `chore:`); commit at the end of every task
- Internal helper columns are prefixed `_` (e.g. `_stage`, `_popularity`) and are dropped before CSV/bronze save

---

### Task 1: Project scaffolding + environment

**Files:**
- Create: `.gitignore`, `.env.example`, `requirements.txt`, `pytest.ini`
- Create (empty keeper): `tests/__init__.py`
- Create dirs: `python/config`, `python/utils`, `python/01_generate`, `sql/00_setup`, `sql/10_bronze`, `data/raw`, `docs`, `linkedin`, `reports/figures`, `tasks`, `notebooks`, `powerbi`, `excel`

**Interfaces:**
- Produces: working venv at `.venv` with all pinned deps installed; directory tree matching spec §7.

- [ ] **Step 1: Create `.gitignore`**

```gitignore
.env
.venv/
data/
__pycache__/
*.pyc
.pytest_cache/
.ipynb_checkpoints/
*.pbix.tmp
```

- [ ] **Step 2: Create `.env.example`**

```ini
DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=shopsphere_dw
DB_USER=shopsphere_app
DB_PASSWORD=change_me
```

- [ ] **Step 3: Create `requirements.txt`**

```text
pandas==2.2.3
numpy==2.1.3
SQLAlchemy==2.0.36
PyMySQL==1.1.1
cryptography==44.0.0
python-dotenv==1.0.1
Faker==33.1.0
pytest==8.3.4
```

- [ ] **Step 4: Create `pytest.ini`**

```ini
[pytest]
testpaths = tests
addopts = -q
```

- [ ] **Step 5: Create directory tree**

Run (Git Bash):
```bash
mkdir -p python/config python/utils python/01_generate sql/00_setup sql/10_bronze data/raw docs linkedin reports/figures tasks notebooks powerbi excel tests
touch tests/__init__.py
```

- [ ] **Step 6: Create venv and install deps**

```bash
python -m venv .venv
.venv/Scripts/python -m pip install --upgrade pip
.venv/Scripts/python -m pip install -r requirements.txt
.venv/Scripts/python -c "import pandas, numpy, sqlalchemy, pymysql, faker; print('deps OK')"
```
Expected final output: `deps OK`

- [ ] **Step 7: Commit**

```bash
git add .gitignore .env.example requirements.txt pytest.ini tests/__init__.py
git commit -m "chore: project scaffolding, pinned dependencies, pytest config"
```

---

### Task 2: Config module (settings + engine factory)

**Files:**
- Create: `python/config/__init__.py` (empty), `python/config/settings.py`, `python/config/db.py`
- Test: `tests/conftest.py`, `tests/test_settings.py`

**Interfaces:**
- Produces: `settings.py` constants used by ALL later tasks (exact names below); `db.get_engine() -> sqlalchemy.Engine`; `settings.build_db_url() -> str`.

- [ ] **Step 1: Write `tests/conftest.py` (path bootstrap used by every test)**

```python
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))
sys.path.insert(0, str(ROOT / "python" / "01_generate"))
```

- [ ] **Step 2: Write the failing test `tests/test_settings.py`**

```python
from datetime import date


def test_core_constants():
    from config import settings
    assert settings.RANDOM_SEED == 42
    assert settings.DATA_START == date(2024, 7, 1)
    assert settings.DATA_END == date(2026, 6, 30)
    assert settings.N_CUSTOMERS == 12_000
    assert settings.N_SESSIONS == 800_000
    assert abs(sum(settings.ACQUISITION_MIX.values()) - 1.0) < 1e-9


def test_funnel_math_hits_conversion_target():
    from config import settings
    conv = (settings.P_PRODUCT_VIEW * settings.P_CART_GIVEN_VIEW
            * settings.P_CHECKOUT_GIVEN_CART * settings.P_BUY_GIVEN_CHECKOUT)
    assert 0.023 <= conv <= 0.027


def test_db_url_shape():
    from config import settings
    url = settings.build_db_url()
    assert url.startswith("mysql+pymysql://")
    assert "shopsphere_dw" in url
```

- [ ] **Step 3: Run test to verify it fails**

Run: `.venv/Scripts/python -m pytest tests/test_settings.py -v`
Expected: FAIL / ERROR with `ModuleNotFoundError: No module named 'config'` (or ImportError inside it)

- [ ] **Step 4: Write `python/config/__init__.py`** (empty file) **and `python/config/settings.py`**

```python
"""Central configuration: volumes, behavior targets, DB connection."""
from __future__ import annotations

import os
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

RANDOM_SEED = 42
DATA_START = date(2024, 7, 1)
DATA_END = date(2026, 6, 30)

# ---- volumes -------------------------------------------------------------
N_CUSTOMERS = 12_000
N_PRODUCTS = 500
N_SESSIONS = 800_000
N_AB_SESSIONS = 60_000     # total assignments (2 arms)
REVIEW_RATE = 0.25         # share of completed orders that get a review

# ---- retention behavior ---------------------------------------------------
# P(customer places another order | has placed k orders so far)
REPEAT_LADDER = {1: 0.31, 2: 0.45}
REPEAT_LADDER_DEFAULT = 0.55
MAX_ORDERS_PER_CUSTOMER = 12
CUSTOMER_LIFETIME_DAYS_MEAN = 330   # exponential lifetime → natural churn

# ---- funnel (conditional step probabilities) ------------------------------
P_PRODUCT_VIEW = 0.65          # of sessions
P_CART_GIVEN_VIEW = 0.128      # of product viewers
P_CHECKOUT_GIVEN_CART = 0.40   # of carts
P_BUY_GIVEN_CHECKOUT = 0.75    # of checkouts  → net ≈ 2.5% conversion

ORDER_STATUS_PROBS = {"completed": 0.92, "cancelled": 0.05, "returned": 0.03}

# ---- channels --------------------------------------------------------------
ACQUISITION_MIX = {
    "organic": 0.25, "paid_search": 0.22, "paid_social": 0.20,
    "display": 0.13, "email": 0.12, "affiliate": 0.08,
}
PAID_CHANNELS = ["paid_search", "paid_social", "display", "email", "affiliate"]
CHANNEL_CAC = {"paid_search": 70, "paid_social": 95, "display": 110, "email": 25, "affiliate": 45}
CHANNEL_CPC = {"paid_search": 1.2, "paid_social": 0.6, "display": 0.4, "email": 0.05, "affiliate": 0.3}
CHANNEL_CTR = {"paid_search": 0.04, "paid_social": 0.012, "display": 0.005, "email": 0.03, "affiliate": 0.02}

# ---- A/B test ---------------------------------------------------------------
AB_TEST_NAME = "free_shipping_threshold"
AB_START = date(2026, 2, 15)
AB_END = date(2026, 4, 30)
AB_TREATMENT_LIFT = 1.15   # relative conversion lift in treatment

# ---- database ---------------------------------------------------------------
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_NAME = os.getenv("DB_NAME", "shopsphere_dw")
DB_USER = os.getenv("DB_USER", "shopsphere_app")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")


def build_db_url() -> str:
    return (f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@"
            f"{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4")
```

- [ ] **Step 5: Write `python/config/db.py`**

```python
"""SQLAlchemy engine factory."""
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from config import settings

_engine: Engine | None = None


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = create_engine(settings.build_db_url(), pool_pre_ping=True)
    return _engine
```

- [ ] **Step 6: Run test to verify it passes**

Run: `.venv/Scripts/python -m pytest tests/test_settings.py -v`
Expected: 3 passed

- [ ] **Step 7: Commit**

```bash
git add python/config tests/conftest.py tests/test_settings.py
git commit -m "feat: central settings with behavior targets and DB engine factory"
```

---

### Task 3: Shared generator helpers + DB I/O utilities

**Files:**
- Create: `python/utils/__init__.py` (empty), `python/utils/db_io.py`, `python/utils/run_sql.py`, `python/01_generate/_common.py`
- Test: `tests/test_common.py`

**Interfaces:**
- Produces (used by all generators):
  - `_common.rng() -> numpy.random.Generator` (module-level singleton, seeded 42)
  - `_common.reset_rng() -> None`
  - `_common.fake() -> Faker` (seeded)
  - `_common.all_days() -> pd.DatetimeIndex` (every day in DATA_START..DATA_END)
  - `_common.season_multiplier(days: pd.DatetimeIndex) -> np.ndarray`
  - `_common.growth_trend(days: pd.DatetimeIndex) -> np.ndarray`
  - `_common.weighted_day_sample(n: int) -> pd.Series` (seasonal+growth-weighted random dates)
  - `db_io.load_dataframe(df, table: str, engine, chunksize=10_000, truncate=True) -> int`
  - `run_sql.run_sql_file(path, engine) -> int` (statements executed)

- [ ] **Step 1: Write the failing test `tests/test_common.py`**

```python
import numpy as np
import pandas as pd


def test_rng_reproducible():
    import _common
    _common.reset_rng()
    a = _common.rng().random(5)
    _common.reset_rng()
    b = _common.rng().random(5)
    assert np.allclose(a, b)


def test_season_multiplier_shape_and_peaks():
    import _common
    days = _common.all_days()
    m = _common.season_multiplier(days)
    assert len(m) == len(days)
    nov_dec = m[np.isin(days.month, [11, 12])].mean()
    jan = m[days.month == 1].mean()
    assert nov_dec > 1.5 * jan / 0.9  # Nov-Dec clearly above January


def test_weighted_day_sample_within_range():
    import _common
    from config import settings
    _common.reset_rng()
    s = _common.weighted_day_sample(10_000)
    assert s.min().date() >= settings.DATA_START
    assert s.max().date() <= settings.DATA_END


def test_load_dataframe_roundtrip_sqlite():
    from sqlalchemy import create_engine, text
    from utils.db_io import load_dataframe
    eng = create_engine("sqlite:///:memory:")
    with eng.begin() as c:
        c.execute(text("CREATE TABLE t (a INTEGER, b TEXT)"))
    df = pd.DataFrame({"a": [1, 2], "b": ["x", "y"]})
    n = load_dataframe(df, "t", eng, truncate=False)
    assert n == 2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python -m pytest tests/test_common.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named '_common'`

- [ ] **Step 3: Write `python/01_generate/_common.py`**

```python
"""Shared seeded randomness + calendar weighting for all generators."""
from __future__ import annotations

import numpy as np
import pandas as pd
from faker import Faker

from config import settings

_rng: np.random.Generator | None = None


def rng() -> np.random.Generator:
    global _rng
    if _rng is None:
        _rng = np.random.default_rng(settings.RANDOM_SEED)
    return _rng


def reset_rng() -> None:
    global _rng
    _rng = None


def fake() -> Faker:
    f = Faker()
    Faker.seed(settings.RANDOM_SEED)
    return f


def all_days() -> pd.DatetimeIndex:
    return pd.date_range(settings.DATA_START, settings.DATA_END, freq="D")


def season_multiplier(days: pd.DatetimeIndex) -> np.ndarray:
    m = np.ones(len(days))
    month = days.month
    m[np.isin(month, [11, 12])] = 1.8   # holiday peak
    m[month == 1] = 0.75                # January slump
    m[np.isin(month, [7, 8])] = 0.9     # summer dip
    m = m * np.where(days.dayofweek >= 5, 0.85, 1.05)  # weekday > weekend
    return m


def growth_trend(days: pd.DatetimeIndex) -> np.ndarray:
    t = np.linspace(0.0, 1.0, len(days))
    return 1.0 + 0.5 * t   # store grows ~50% across the 24 months


def weighted_day_sample(n: int) -> pd.Series:
    days = all_days()
    w = season_multiplier(days) * growth_trend(days)
    idx = rng().choice(len(days), size=n, p=w / w.sum())
    return pd.Series(days[idx])
```

- [ ] **Step 4: Write `python/utils/__init__.py`** (empty), **`python/utils/db_io.py`**

```python
"""Chunked DataFrame -> MySQL loading."""
from sqlalchemy import text


def load_dataframe(df, table: str, engine, chunksize: int = 10_000, truncate: bool = True) -> int:
    if truncate:
        with engine.begin() as conn:
            conn.execute(text(f"TRUNCATE TABLE {table}"))
    df.to_sql(table, engine, if_exists="append", index=False,
              chunksize=chunksize, method="multi")
    return len(df)
```

- [ ] **Step 5: Write `python/utils/run_sql.py`**

```python
"""Execute a .sql file statement-by-statement (splits on ';', strips -- comments)."""
from pathlib import Path

from sqlalchemy import text


def run_sql_file(path, engine) -> int:
    raw = Path(path).read_text(encoding="utf-8")
    lines = [ln for ln in raw.splitlines() if not ln.strip().startswith("--")]
    statements = [s.strip() for s in "\n".join(lines).split(";") if s.strip()]
    with engine.begin() as conn:
        for stmt in statements:
            conn.execute(text(stmt))
    return len(statements)
```

- [ ] **Step 6: Run test to verify it passes**

Run: `.venv/Scripts/python -m pytest tests/test_common.py -v`
Expected: 4 passed

- [ ] **Step 7: Commit**

```bash
git add python/utils python/01_generate/_common.py tests/test_common.py
git commit -m "feat: seeded RNG/calendar helpers and SQL/DataFrame IO utilities"
```

---

### Task 4: MySQL database, app user, smoke test  ⚠ USER ACTION REQUIRED

**Files:**
- Create: `sql/00_setup/00_create_database.sql`, `python/00_smoke_test.py`
- Modify: `.env` (user creates from `.env.example` — NOT committed)

**Interfaces:**
- Produces: reachable `shopsphere_dw` database; `shopsphere_app` least-privilege user; verified connectivity via `python/00_smoke_test.py` printing `SMOKE TEST PASSED`.

- [ ] **Step 1: Write `sql/00_setup/00_create_database.sql`**

```sql
-- Run this ONCE as MySQL root:  mysql -u root -p < sql/00_setup/00_create_database.sql
-- Replace CHANGE_ME with the same password you put in .env
CREATE DATABASE IF NOT EXISTS shopsphere_dw
  CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;

CREATE USER IF NOT EXISTS 'shopsphere_app'@'localhost' IDENTIFIED BY 'CHANGE_ME';
CREATE USER IF NOT EXISTS 'shopsphere_app'@'127.0.0.1' IDENTIFIED BY 'CHANGE_ME';

GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, DROP, INDEX, ALTER,
      CREATE VIEW, SHOW VIEW
  ON shopsphere_dw.* TO 'shopsphere_app'@'localhost';
GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, DROP, INDEX, ALTER,
      CREATE VIEW, SHOW VIEW
  ON shopsphere_dw.* TO 'shopsphere_app'@'127.0.0.1';

FLUSH PRIVILEGES;
```

- [ ] **Step 2: Write `python/00_smoke_test.py`**

```python
"""Connectivity smoke test: run before anything else touches the DB."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sqlalchemy import text

from config.db import get_engine


def main() -> int:
    eng = get_engine()
    with eng.begin() as conn:
        version = conn.execute(text("SELECT VERSION()")).scalar()
        conn.execute(text("CREATE TABLE IF NOT EXISTS _smoke (id INT)"))
        conn.execute(text("INSERT INTO _smoke VALUES (1)"))
        n = conn.execute(text("SELECT COUNT(*) FROM _smoke")).scalar()
        conn.execute(text("DROP TABLE _smoke"))
    print(f"MySQL version: {version}, roundtrip rows: {n}")
    print("SMOKE TEST PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 3: USER ACTION — create DB and `.env`**

PAUSE and ask the user to:
1. Copy `.env.example` → `.env`, set a real password for `DB_PASSWORD`.
2. Edit `sql/00_setup/00_create_database.sql` replacing `CHANGE_ME` with that same password (do NOT commit the edited password — restore `CHANGE_ME` after running, or run via stdin).
3. Run it as root: `mysql -u root -p < sql/00_setup/00_create_database.sql` (or execute the statements in MySQL Workbench).

- [ ] **Step 4: Run the smoke test**

Run: `.venv/Scripts/python python/00_smoke_test.py`
Expected output ends with: `SMOKE TEST PASSED`
If it fails with an auth error: re-check `.env` password matches the created user.

- [ ] **Step 5: Commit** (the SQL keeps the `CHANGE_ME` placeholder)

```bash
git add sql/00_setup/00_create_database.sql python/00_smoke_test.py
git commit -m "feat: database bootstrap script and connectivity smoke test"
```

---

### Task 5: Bronze DDL + apply script

**Files:**
- Create: `sql/10_bronze/01_bronze_tables.sql`, `python/01_generate/apply_bronze_ddl.py`
- Test: `tests/test_bronze_ddl.py`

**Interfaces:**
- Produces: 9 `bronze_*` tables in MySQL (no constraints); `apply_bronze_ddl.py` runnable any time (idempotent DROP/CREATE).
- Table names consumed by Task 12 loader: `bronze_customers`, `bronze_products`, `bronze_orders`, `bronze_order_items`, `bronze_web_sessions`, `bronze_web_events`, `bronze_marketing_spend`, `bronze_ab_test_assignments`, `bronze_reviews_nps`.

- [ ] **Step 1: Write `sql/10_bronze/01_bronze_tables.sql`**

```sql
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
```

- [ ] **Step 2: Write `python/01_generate/apply_bronze_ddl.py`**

```python
"""Create (or recreate) all bronze tables."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import settings
from config.db import get_engine
from utils.run_sql import run_sql_file


def main() -> None:
    ddl = settings.PROJECT_ROOT / "sql" / "10_bronze" / "01_bronze_tables.sql"
    n = run_sql_file(ddl, get_engine())
    print(f"Executed {n} statements from {ddl.name}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Write the failing test `tests/test_bronze_ddl.py`** (integration — needs the DB from Task 4)

```python
from sqlalchemy import text

EXPECTED = {
    "bronze_customers", "bronze_products", "bronze_orders", "bronze_order_items",
    "bronze_web_sessions", "bronze_web_events", "bronze_marketing_spend",
    "bronze_ab_test_assignments", "bronze_reviews_nps",
}


def test_all_bronze_tables_exist():
    from config.db import get_engine
    with get_engine().connect() as conn:
        rows = conn.execute(text(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = DATABASE() AND table_name LIKE 'bronze_%'"
        )).fetchall()
    assert EXPECTED <= {r[0] for r in rows}
```

- [ ] **Step 4: Run test to verify it fails**

Run: `.venv/Scripts/python -m pytest tests/test_bronze_ddl.py -v`
Expected: FAIL (tables don't exist yet)

- [ ] **Step 5: Apply DDL, re-run test**

```bash
.venv/Scripts/python python/01_generate/apply_bronze_ddl.py
.venv/Scripts/python -m pytest tests/test_bronze_ddl.py -v
```
Expected: `Executed 18 statements...` then 1 passed

- [ ] **Step 6: Commit**

```bash
git add sql/10_bronze python/01_generate/apply_bronze_ddl.py tests/test_bronze_ddl.py
git commit -m "feat: bronze layer DDL (constraint-free raw tables) with apply script"
```

---

### Task 6: Generators — customers & products

**Files:**
- Create: `python/01_generate/gen_customers.py`, `python/01_generate/gen_products.py`
- Test: `tests/test_customers_products.py`

**Interfaces:**
- Produces:
  - `gen_customers.generate_customers() -> pd.DataFrame` — columns exactly: `customer_id, signup_date, acquisition_channel, country, city, birth_year, gender, email, marketing_opt_in`
  - `gen_products.generate_products() -> pd.DataFrame` — columns: `product_id, product_name, category, subcategory, unit_price, unit_cost, launch_date, _popularity` (internal)

- [ ] **Step 1: Write the failing test `tests/test_customers_products.py`**

```python
import pandas as pd
import pytest


@pytest.fixture(scope="module")
def data():
    import _common
    _common.reset_rng()
    import gen_customers, gen_products
    return gen_customers.generate_customers(), gen_products.generate_products()


def test_customers_shape_and_columns(data):
    from config import settings
    customers, _ = data
    assert len(customers) == settings.N_CUSTOMERS
    assert list(customers.columns) == [
        "customer_id", "signup_date", "acquisition_channel", "country", "city",
        "birth_year", "gender", "email", "marketing_opt_in"]
    assert customers["customer_id"].is_unique


def test_customers_domains(data):
    from config import settings
    customers, _ = data
    assert set(customers["acquisition_channel"]) <= set(settings.ACQUISITION_MIX)
    assert customers["signup_date"].min() >= settings.DATA_START
    assert customers["signup_date"].max() <= settings.DATA_END
    assert customers["email"].str.contains("@").all()


def test_products_shape_and_price_sanity(data):
    from config import settings
    _, products = data
    assert len(products) == settings.N_PRODUCTS
    assert products["product_id"].is_unique
    assert (products["unit_price"] > 0).all()
    assert (products["unit_cost"] < products["unit_price"]).all()
    assert (products["_popularity"] > 0).all()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python -m pytest tests/test_customers_products.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'gen_customers'`

- [ ] **Step 3: Write `python/01_generate/gen_customers.py`**

```python
"""Generate the customers table (one row per customer)."""
import numpy as np
import pandas as pd

from config import settings
from _common import fake, rng, weighted_day_sample

COUNTRIES = ["United Kingdom", "Germany", "France", "Romania",
             "Netherlands", "Spain", "Italy", "United States"]
COUNTRY_P = [0.22, 0.16, 0.13, 0.12, 0.10, 0.10, 0.09, 0.08]


def generate_customers() -> pd.DataFrame:
    n = settings.N_CUSTOMERS
    r = rng()
    f = fake()
    return pd.DataFrame({
        "customer_id": [f"C{100000 + i}" for i in range(n)],
        "signup_date": weighted_day_sample(n).dt.date.values,
        "acquisition_channel": r.choice(list(settings.ACQUISITION_MIX), n,
                                        p=list(settings.ACQUISITION_MIX.values())),
        "country": r.choice(COUNTRIES, n, p=COUNTRY_P),
        "city": [f.city() for _ in range(n)],
        "birth_year": np.clip(r.normal(1988, 12, n).astype(int), 1955, 2007),
        "gender": r.choice(["F", "M", "Other"], n, p=[0.48, 0.48, 0.04]),
        "email": [f.unique.email() for _ in range(n)],
        "marketing_opt_in": (r.random(n) < 0.62).astype(int),
    })
```

- [ ] **Step 4: Write `python/01_generate/gen_products.py`**

```python
"""Generate the products catalog."""
import numpy as np
import pandas as pd

from config import settings
from _common import fake, rng

# category: (min_price, max_price, assortment_share)
CATEGORIES = {
    "Electronics":             (30, 400, 0.12),
    "Computers & Accessories": (20, 500, 0.08),
    "Home & Living":           (15, 250, 0.18),
    "Kitchen":                 (12, 200, 0.15),
    "Sports & Outdoors":       (18, 300, 0.12),
    "Beauty & Personal Care":  (8,  90,  0.15),
    "Toys & Games":            (10, 120, 0.12),
    "Office Supplies":         (5,  80,  0.08),
}


def generate_products() -> pd.DataFrame:
    n = settings.N_PRODUCTS
    r = rng()
    f = fake()
    names = list(CATEGORIES)
    cats = r.choice(names, n, p=[CATEGORIES[c][2] for c in names])
    lo = np.array([CATEGORIES[c][0] for c in cats], float)
    hi = np.array([CATEGORIES[c][1] for c in cats], float)
    price = np.exp(r.uniform(np.log(lo), np.log(hi)))  # log-uniform in range
    launch_lo = pd.Timestamp("2023-01-01").value
    launch_hi = (pd.Timestamp(settings.DATA_END) - pd.Timedelta(days=90)).value
    launch = pd.to_datetime(r.uniform(launch_lo, launch_hi, n).astype("int64"))
    words = [f.word() for _ in range(n)]
    return pd.DataFrame({
        "product_id": [f"P{10000 + i}" for i in range(n)],
        "product_name": [f.catch_phrase()[:60] for _ in range(n)],
        "category": cats,
        "subcategory": [f"{c} - {w.title()}" for c, w in zip(cats, words)],
        "unit_price": price.round(2),
        "unit_cost": (price * r.uniform(0.45, 0.70, n)).round(2),
        "launch_date": launch.date,
        "_popularity": r.pareto(1.5, n) + 1.0,
    })
```

- [ ] **Step 5: Run test to verify it passes**

Run: `.venv/Scripts/python -m pytest tests/test_customers_products.py -v`
Expected: 3 passed

- [ ] **Step 6: Commit**

```bash
git add python/01_generate/gen_customers.py python/01_generate/gen_products.py tests/test_customers_products.py
git commit -m "feat: customers and products generators with seasonal signups and log-uniform pricing"
```

---

### Task 7: Generator — orders & order_items (the retention engine)

**Files:**
- Create: `python/01_generate/gen_orders.py`
- Test: `tests/test_orders.py`

**Interfaces:**
- Consumes: `generate_customers()`, `generate_products()` outputs.
- Produces: `gen_orders.generate_orders(customers, products) -> tuple[pd.DataFrame, pd.DataFrame]`
  - orders columns: `order_id, customer_id, order_ts, order_status, payment_method, shipping_country, discount_amount, shipping_fee`
  - items columns: `order_item_id, order_id, product_id, quantity, unit_price_at_sale, line_discount`

- [ ] **Step 1: Write the failing test `tests/test_orders.py`**

```python
import numpy as np
import pandas as pd
import pytest


@pytest.fixture(scope="module")
def data():
    import _common
    _common.reset_rng()
    import gen_customers, gen_products, gen_orders
    customers = gen_customers.generate_customers()
    products = gen_products.generate_products()
    orders, items = gen_orders.generate_orders(customers, products)
    return customers, products, orders, items


def test_repeat_ladder_produces_target_one_time_share(data):
    _, _, orders, _ = data
    per_cust = orders.groupby("customer_id").size()
    one_time = (per_cust == 1).mean()
    assert 0.66 <= one_time <= 0.72


def test_orders_after_signup_and_in_range(data):
    from config import settings
    customers, _, orders, _ = data
    signup = customers.set_index("customer_id")["signup_date"]
    order_dates = pd.to_datetime(orders["order_ts"]).dt.date
    cust_signup = orders["customer_id"].map(signup)
    assert (order_dates >= cust_signup).all()
    assert order_dates.max() <= settings.DATA_END


def test_statuses_and_referential_integrity(data):
    from config import settings
    customers, products, orders, items = data
    assert set(orders["order_status"]) <= set(settings.ORDER_STATUS_PROBS)
    assert items["order_id"].isin(orders["order_id"]).all()
    assert items["product_id"].isin(products["product_id"]).all()
    assert orders["order_id"].is_unique


def test_aov_in_realistic_band(data):
    _, _, orders, items = data
    rev = items["quantity"] * items["unit_price_at_sale"] - items["line_discount"]
    order_rev = rev.groupby(items["order_id"]).sum()
    completed = orders.loc[orders["order_status"] == "completed", "order_id"]
    aov = order_rev.reindex(completed).dropna().mean()
    assert 70 <= aov <= 115
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python -m pytest tests/test_orders.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'gen_orders'`

- [ ] **Step 3: Write `python/01_generate/gen_orders.py`**

```python
"""Generate orders + order_items driven by the repeat-purchase ladder."""
import numpy as np
import pandas as pd

from config import settings
from _common import all_days, growth_trend, rng, season_multiplier

PAYMENT_METHODS = ["card", "paypal", "apple_pay", "google_pay", "bank_transfer"]
PAYMENT_P = [0.55, 0.20, 0.10, 0.08, 0.07]
ITEM_COUNT = [1, 2, 3, 4]
ITEM_COUNT_P = [0.60, 0.25, 0.10, 0.05]
QTY = [1, 2, 3]
QTY_P = [0.90, 0.08, 0.02]

_h = np.ones(24)
_h[[19, 20, 21]] = 3.0
_h[[12, 13, 18, 22]] = 2.0
_h[2:6] = 0.3
HOUR_P = _h / _h.sum()


def _order_counts(r, n: int) -> np.ndarray:
    """Markov ladder: P(next order | k orders) from settings.REPEAT_LADDER."""
    counts = np.ones(n, dtype=int)
    active = np.ones(n, dtype=bool)
    for k in range(1, settings.MAX_ORDERS_PER_CUSTOMER):
        p = settings.REPEAT_LADDER.get(k, settings.REPEAT_LADDER_DEFAULT)
        active &= r.random(n) < p
        counts += active
    return counts


def generate_orders(customers: pd.DataFrame, products: pd.DataFrame):
    r = rng()
    days = all_days()
    day_w = season_multiplier(days) * growth_trend(days)
    day_vals = days.values

    n_cust = len(customers)
    counts = _order_counts(r, n_cust)
    lifetime = r.exponential(settings.CUSTOMER_LIFETIME_DAYS_MEAN, n_cust)
    signup = pd.to_datetime(customers["signup_date"]).values
    end = np.datetime64(settings.DATA_END)

    cust_pos, date_list = [], []
    for i in range(n_cust):
        lo = int(np.searchsorted(day_vals, signup[i]))
        window_end = min(signup[i] + np.timedelta64(int(lifetime[i]), "D"), end)
        hi = int(np.searchsorted(day_vals, window_end, side="right"))
        hi = max(hi, lo + 1)
        w = day_w[lo:hi]
        picks = np.sort(r.choice(np.arange(lo, hi), size=counts[i], p=w / w.sum()))
        cust_pos.extend([i] * counts[i])
        date_list.append(day_vals[picks])

    order_dates = np.concatenate(date_list)
    cust_pos = np.array(cust_pos)
    n_orders = len(order_dates)

    ts = (pd.to_datetime(order_dates)
          + pd.to_timedelta(r.choice(24, n_orders, p=HOUR_P), unit="h")
          + pd.to_timedelta(r.integers(0, 60, n_orders), unit="m"))

    cust_ids = customers["customer_id"].values[cust_pos]
    countries = customers["country"].values[cust_pos]
    ship = np.where(r.random(n_orders) < 0.90, countries,
                    r.choice(customers["country"].unique(), n_orders))

    orders = pd.DataFrame({
        "order_id": [f"O{1000000 + i}" for i in range(n_orders)],
        "customer_id": cust_ids,
        "order_ts": ts,
        "order_status": r.choice(list(settings.ORDER_STATUS_PROBS), n_orders,
                                 p=list(settings.ORDER_STATUS_PROBS.values())),
        "payment_method": r.choice(PAYMENT_METHODS, n_orders, p=PAYMENT_P),
        "shipping_country": ship,
    })

    # ---- items -------------------------------------------------------------
    sizes = r.choice(ITEM_COUNT, n_orders, p=ITEM_COUNT_P)
    order_rep = np.repeat(np.arange(n_orders), sizes)
    n_items = len(order_rep)
    pop = products["_popularity"].values
    prod_pos = r.choice(len(products), n_items, p=pop / pop.sum())
    qty = r.choice(QTY, n_items, p=QTY_P)
    price = (products["unit_price"].values[prod_pos]
             * r.uniform(0.95, 1.05, n_items)).round(2)
    line_disc = np.where(r.random(n_items) < 0.10, (price * qty * 0.10).round(2), 0.0)

    items = pd.DataFrame({
        "order_item_id": [f"OI{2000000 + i}" for i in range(n_items)],
        "order_id": orders["order_id"].values[order_rep],
        "product_id": products["product_id"].values[prod_pos],
        "quantity": qty,
        "unit_price_at_sale": price,
        "line_discount": line_disc,
    })

    subtotal = (pd.Series(price * qty - line_disc)
                .groupby(order_rep).sum().reindex(range(n_orders), fill_value=0).values)
    orders["discount_amount"] = np.minimum(
        np.where(r.random(n_orders) < 0.20, r.uniform(5, 20, n_orders), 0.0),
        0.5 * subtotal).round(2)
    orders["shipping_fee"] = np.where(subtotal >= 75, 0.0, 4.99)
    return orders, items
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/Scripts/python -m pytest tests/test_orders.py -v`
Expected: 4 passed (takes ~10-30s — full 12k-customer generation)

- [ ] **Step 5: Commit**

```bash
git add python/01_generate/gen_orders.py tests/test_orders.py
git commit -m "feat: orders/items generator with repeat ladder, lifetimes and seasonality"
```

---

### Task 8: Generator — web sessions & events (the funnel engine)

**Files:**
- Create: `python/01_generate/gen_sessions_events.py`
- Test: `tests/test_sessions_events.py`

**Interfaces:**
- Consumes: customers, orders DataFrames.
- Produces: `generate_sessions_events(customers, orders) -> tuple[pd.DataFrame, pd.DataFrame]`
  - sessions columns: `session_id, customer_id, session_start_ts, device_type, traffic_source, landing_page, campaign_id, _stage, _order_id` (last two internal; `_stage` ∈ bounce/product_view/add_to_cart/begin_checkout/purchase)
  - events columns: `event_id, session_id, event_type, event_ts, product_id, order_id`

- [ ] **Step 1: Write the failing test `tests/test_sessions_events.py`**

```python
import numpy as np
import pandas as pd
import pytest


@pytest.fixture(scope="module")
def data():
    import _common
    _common.reset_rng()
    import gen_customers, gen_products, gen_orders, gen_sessions_events
    customers = gen_customers.generate_customers()
    products = gen_products.generate_products()
    orders, _ = gen_orders.generate_orders(customers, products)
    sessions, events = gen_sessions_events.generate_sessions_events(customers, orders)
    return orders, sessions, events


def test_session_count_and_conversion(data):
    from config import settings
    orders, sessions, _ = data
    assert len(sessions) == settings.N_SESSIONS
    conv = (sessions["_stage"] == "purchase").mean()
    assert 0.020 <= conv <= 0.029


def test_every_order_has_a_converting_session(data):
    orders, sessions, _ = data
    purch = sessions.loc[sessions["_stage"] == "purchase", "_order_id"]
    assert set(purch) == set(orders["order_id"])


def test_funnel_monotonic_and_abandonment(data):
    _, _, events = data
    c = events["event_type"].value_counts()
    assert c["page_view"] >= c["product_view"] >= c["add_to_cart"] \
           >= c["begin_checkout"] >= c["purchase"]
    abandon = 1 - c["purchase"] / c["add_to_cart"]
    assert 0.62 <= abandon <= 0.78


def test_events_reference_sessions_and_types(data):
    _, sessions, events = data
    assert set(events["event_type"]) == {
        "page_view", "product_view", "add_to_cart", "begin_checkout", "purchase"}
    assert events["session_id"].isin(sessions["session_id"]).all()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python -m pytest tests/test_sessions_events.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'gen_sessions_events'`

- [ ] **Step 3: Write `python/01_generate/gen_sessions_events.py`**

```python
"""Generate web sessions + funnel events. One converting session per order,
plus anonymous/known non-converting traffic to reach N_SESSIONS."""
import numpy as np
import pandas as pd

from config import settings
from _common import rng, weighted_day_sample

TRAFFIC_CONV = {"organic": 0.24, "paid_search": 0.20, "email": 0.18, "direct": 0.15,
                "paid_social": 0.10, "affiliate": 0.07, "display": 0.06}
TRAFFIC_NONCONV = {"organic": 0.22, "paid_search": 0.18, "email": 0.08, "direct": 0.14,
                   "paid_social": 0.20, "affiliate": 0.05, "display": 0.13}
DEVICES = ["mobile", "desktop", "tablet"]
LANDING = ["/", "/sale", "/category/electronics", "/category/home-living",
           "/category/beauty", "/product"]
LANDING_P = [0.30, 0.15, 0.15, 0.15, 0.10, 0.15]
PAID = {"paid_search", "paid_social", "display", "affiliate", "email"}

_h = np.ones(24)
_h[[12, 13, 18, 19, 20, 21, 22]] = 2.5
_h[1:6] = 0.3
HOUR_P = _h / _h.sum()


def generate_sessions_events(customers: pd.DataFrame, orders: pd.DataFrame):
    r = rng()
    n_conv = len(orders)
    n_non = settings.N_SESSIONS - n_conv

    # ---- converting sessions (one per order) --------------------------------
    conv_start = (pd.to_datetime(orders["order_ts"])
                  - pd.to_timedelta(r.integers(25, 45, n_conv), unit="m"))
    conv = pd.DataFrame({
        "customer_id": orders["customer_id"].values,
        "session_start_ts": conv_start.values,
        "device_type": r.choice(DEVICES, n_conv, p=[0.48, 0.42, 0.10]),
        "traffic_source": r.choice(list(TRAFFIC_CONV), n_conv,
                                   p=list(TRAFFIC_CONV.values())),
        "_stage": "purchase",
        "_order_id": orders["order_id"].values,
    })

    # ---- non-converting sessions --------------------------------------------
    p_pv = settings.P_PRODUCT_VIEW
    p_cart = p_pv * settings.P_CART_GIVEN_VIEW
    p_co = p_cart * settings.P_CHECKOUT_GIVEN_CART
    p_buy = p_co * settings.P_BUY_GIVEN_CHECKOUT
    shares = np.array([1 - p_pv, p_pv - p_cart, p_cart - p_co, p_co - p_buy])
    shares = shares / (1 - p_buy)
    stages = r.choice(["bounce", "product_view", "add_to_cart", "begin_checkout"],
                      n_non, p=shares)
    non_start = (weighted_day_sample(n_non)
                 + pd.to_timedelta(r.choice(24, n_non, p=HOUR_P), unit="h")
                 + pd.to_timedelta(r.integers(0, 60, n_non), unit="m"))
    known = r.random(n_non) < 0.25
    cust = np.where(known, r.choice(customers["customer_id"].values, n_non), None)
    non = pd.DataFrame({
        "customer_id": cust,
        "session_start_ts": non_start.values,
        "device_type": r.choice(DEVICES, n_non, p=[0.58, 0.32, 0.10]),
        "traffic_source": r.choice(list(TRAFFIC_NONCONV), n_non,
                                   p=list(TRAFFIC_NONCONV.values())),
        "_stage": stages,
        "_order_id": None,
    })

    sessions = pd.concat([conv, non], ignore_index=True)
    n = len(sessions)
    sessions.insert(0, "session_id", [f"S{5000000 + i}" for i in range(n)])
    sessions["landing_page"] = r.choice(LANDING, n, p=LANDING_P)
    month = pd.to_datetime(sessions["session_start_ts"]).dt.strftime("%Y%m")
    is_paid = sessions["traffic_source"].isin(PAID)
    sessions["campaign_id"] = np.where(
        is_paid,
        "CMP-" + sessions["traffic_source"].str[:4].str.upper() + "-" + month,
        None)

    # ---- events ---------------------------------------------------------------
    STAGE_RANK = {"bounce": 0, "product_view": 1, "add_to_cart": 2,
                  "begin_checkout": 3, "purchase": 4}
    rank = sessions["_stage"].map(STAGE_RANK).values
    start = pd.to_datetime(sessions["session_start_ts"])
    frames = []
    for evt, minrank, offset in [("page_view", 0, 0), ("product_view", 1, 2),
                                 ("add_to_cart", 2, 6), ("begin_checkout", 3, 12),
                                 ("purchase", 4, 18)]:
        m = rank >= minrank
        k = int(m.sum())
        sub = pd.DataFrame({
            "session_id": sessions.loc[m, "session_id"].values,
            "event_type": evt,
            "event_ts": (start[m] + pd.to_timedelta(
                offset + r.integers(0, 4, k), unit="m")).values,
            "product_id": None,
            "order_id": sessions.loc[m, "_order_id"].values if evt == "purchase" else None,
        })
        frames.append(sub)
    events = pd.concat(frames, ignore_index=True)
    events = events.sort_values(["session_id", "event_ts"], kind="stable",
                                ignore_index=True)
    events.insert(0, "event_id", [f"E{10000000 + i}" for i in range(len(events))])
    return sessions, events
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/Scripts/python -m pytest tests/test_sessions_events.py -v`
Expected: 4 passed (this one takes ~1-3 min — 800k sessions, ~1.4M events)

- [ ] **Step 5: Commit**

```bash
git add python/01_generate/gen_sessions_events.py tests/test_sessions_events.py
git commit -m "feat: sessions/events generator with calibrated funnel decay"
```

---

### Task 9: Generator — marketing spend

**Files:**
- Create: `python/01_generate/gen_marketing.py`
- Test: `tests/test_marketing.py`

**Interfaces:**
- Consumes: customers DataFrame.
- Produces: `generate_marketing(customers) -> pd.DataFrame` — columns: `spend_date, channel, spend_amount, impressions, clicks, attributed_signups`; one row per day per paid channel; spend reconciles to per-channel CAC targets.

- [ ] **Step 1: Write the failing test `tests/test_marketing.py`**

```python
import pandas as pd
import pytest


@pytest.fixture(scope="module")
def data():
    import _common
    _common.reset_rng()
    import gen_customers, gen_marketing
    customers = gen_customers.generate_customers()
    return customers, gen_marketing.generate_marketing(customers)


def test_grain_days_x_channels(data):
    from config import settings
    import _common
    _, mkt = data
    assert len(mkt) == len(_common.all_days()) * len(settings.PAID_CHANNELS)
    assert not mkt.duplicated(["spend_date", "channel"]).any()


def test_ctr_within_channel_bands(data):
    _, mkt = data
    ctr = mkt.groupby("channel").apply(
        lambda g: g["clicks"].sum() / g["impressions"].sum(), include_groups=False)
    assert ((ctr > 0.002) & (ctr < 0.08)).all()
    assert (mkt["impressions"] >= mkt["clicks"]).all()


def test_blended_cac_near_target(data):
    from config import settings
    customers, mkt = data
    paid_customers = customers["acquisition_channel"].isin(settings.PAID_CHANNELS).sum()
    cac = mkt["spend_amount"].sum() / paid_customers
    assert 55 <= cac <= 100
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python -m pytest tests/test_marketing.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'gen_marketing'`

- [ ] **Step 3: Write `python/01_generate/gen_marketing.py`**

```python
"""Generate daily marketing spend per paid channel, reconciled to CAC targets."""
import numpy as np
import pandas as pd

from config import settings
from _common import all_days, rng


def generate_marketing(customers: pd.DataFrame) -> pd.DataFrame:
    r = rng()
    days = all_days()
    cust = customers.assign(signup=pd.to_datetime(customers["signup_date"]))
    frames = []
    for ch in settings.PAID_CHANNELS:
        daily = (cust[cust["acquisition_channel"] == ch]
                 .groupby("signup").size().reindex(days, fill_value=0))
        smooth = daily.rolling(7, min_periods=1).mean()
        spend = (smooth * settings.CHANNEL_CAC[ch]
                 * r.normal(1.0, 0.12, len(days))).clip(lower=15.0).round(2)
        clicks = np.maximum(
            (spend / settings.CHANNEL_CPC[ch] * r.uniform(0.85, 1.15, len(days)))
            .astype(int), 1)
        imps = np.maximum(
            (clicks / settings.CHANNEL_CTR[ch] * r.uniform(0.9, 1.1, len(days)))
            .astype(int), clicks)
        frames.append(pd.DataFrame({
            "spend_date": days.date, "channel": ch,
            "spend_amount": spend.values, "impressions": imps,
            "clicks": clicks, "attributed_signups": daily.values,
        }))
    return pd.concat(frames, ignore_index=True)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/Scripts/python -m pytest tests/test_marketing.py -v`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add python/01_generate/gen_marketing.py tests/test_marketing.py
git commit -m "feat: marketing spend generator reconciled to per-channel CAC/CTR targets"
```

---

### Task 10: Generators — A/B test assignments & reviews/NPS

**Files:**
- Create: `python/01_generate/gen_ab_test.py`, `python/01_generate/gen_reviews.py`
- Test: `tests/test_ab_reviews.py`

**Interfaces:**
- Consumes: sessions (WITH `_stage`/`_order_id`), orders, customers.
- Produces:
  - `gen_ab_test.generate_ab_test(sessions) -> pd.DataFrame` — columns: `assignment_id, session_id, customer_id, test_name, variant, assigned_date, converted_flag, order_id`
  - `gen_reviews.generate_reviews(orders) -> pd.DataFrame` — columns: `review_id, customer_id, order_id, review_ts, star_rating, nps_score, review_channel`

- [ ] **Step 1: Write the failing test `tests/test_ab_reviews.py`**

```python
import pandas as pd
import pytest


@pytest.fixture(scope="module")
def data():
    import _common
    _common.reset_rng()
    import gen_customers, gen_products, gen_orders, gen_sessions_events
    import gen_ab_test, gen_reviews
    customers = gen_customers.generate_customers()
    products = gen_products.generate_products()
    orders, _ = gen_orders.generate_orders(customers, products)
    sessions, _ = gen_sessions_events.generate_sessions_events(customers, orders)
    ab = gen_ab_test.generate_ab_test(sessions)
    reviews = gen_reviews.generate_reviews(orders)
    return orders, ab, reviews


def test_ab_size_balance_and_lift(data):
    from config import settings
    _, ab, _ = data
    assert len(ab) == settings.N_AB_SESSIONS
    counts = ab["variant"].value_counts()
    assert counts["control"] == counts["treatment"]
    rates = ab.groupby("variant")["converted_flag"].mean()
    lift = rates["treatment"] / rates["control"] - 1
    assert 0.05 <= lift <= 0.30
    assert not ab["session_id"].duplicated().any()


def test_reviews_reference_completed_orders(data):
    orders, _, reviews = data
    completed = set(orders.loc[orders["order_status"] == "completed", "order_id"])
    assert set(reviews["order_id"]) <= completed
    assert reviews["star_rating"].between(1, 5).all()
    assert reviews["nps_score"].between(0, 10).all()


def test_review_volume_matches_rate(data):
    from config import settings
    orders, _, reviews = data
    n_completed = (orders["order_status"] == "completed").sum()
    assert abs(len(reviews) - settings.REVIEW_RATE * n_completed) <= 2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python -m pytest tests/test_ab_reviews.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'gen_ab_test'`

- [ ] **Step 3: Write `python/01_generate/gen_ab_test.py`**

```python
"""Session-level A/B test with a real (small) treatment effect, built by
stratified sampling from the in-window traffic."""
import pandas as pd

from config import settings


def generate_ab_test(sessions: pd.DataFrame) -> pd.DataFrame:
    s = sessions.copy()
    s["_date"] = pd.to_datetime(s["session_start_ts"]).dt.date
    window = s[(s["_date"] >= settings.AB_START) & (s["_date"] <= settings.AB_END)]
    conv = window[window["_stage"] == "purchase"]
    nonc = window[window["_stage"] != "purchase"]

    n_arm = settings.N_AB_SESSIONS // 2
    p0 = len(conv) / len(window)
    n_conv_c = round(n_arm * p0)
    n_conv_t = round(n_arm * p0 * settings.AB_TREATMENT_LIFT)
    if n_conv_c + n_conv_t > len(conv):
        raise ValueError(
            f"Not enough converting sessions in AB window: need "
            f"{n_conv_c + n_conv_t}, have {len(conv)}. Widen AB window.")

    conv_pool = conv.sample(frac=1.0, random_state=settings.RANDOM_SEED)
    nonc_pool = nonc.sample(frac=1.0, random_state=settings.RANDOM_SEED)
    parts = [
        ("control", conv_pool.iloc[:n_conv_c],
         nonc_pool.iloc[:n_arm - n_conv_c]),
        ("treatment", conv_pool.iloc[n_conv_c:n_conv_c + n_conv_t],
         nonc_pool.iloc[n_arm - n_conv_c:(n_arm - n_conv_c) + (n_arm - n_conv_t)]),
    ]
    frames = []
    for variant, cdf, ndf in parts:
        d = pd.concat([cdf, ndf])
        frames.append(pd.DataFrame({
            "session_id": d["session_id"].values,
            "customer_id": d["customer_id"].values,
            "test_name": settings.AB_TEST_NAME,
            "variant": variant,
            "assigned_date": d["_date"].values,
            "converted_flag": (d["_stage"] == "purchase").astype(int).values,
            "order_id": d["_order_id"].values,
        }))
    out = pd.concat(frames, ignore_index=True)
    out.insert(0, "assignment_id", [f"AB{100000 + i}" for i in range(len(out))])
    return out
```

- [ ] **Step 4: Write `python/01_generate/gen_reviews.py`**

```python
"""Reviews + NPS for a sample of completed orders. Loyal repeat customers
skew positive — satisfaction correlates with retention."""
import numpy as np
import pandas as pd

from config import settings
from _common import rng

STAR_BASE = [0.06, 0.07, 0.15, 0.32, 0.40]
STAR_LOYAL = [0.02, 0.04, 0.10, 0.34, 0.50]
NPS_LO = {1: 0, 2: 3, 3: 6, 4: 8, 5: 9}
NPS_HI = {1: 4, 2: 6, 3: 8, 4: 9, 5: 10}


def generate_reviews(orders: pd.DataFrame) -> pd.DataFrame:
    r = rng()
    completed = orders[orders["order_status"] == "completed"]
    n = int(len(completed) * settings.REVIEW_RATE)
    sample = completed.sample(n=n, random_state=settings.RANDOM_SEED)

    orders_per_cust = orders.groupby("customer_id").size()
    loyal = sample["customer_id"].map(orders_per_cust).values >= 3
    stars = np.where(loyal,
                     r.choice([1, 2, 3, 4, 5], n, p=STAR_LOYAL),
                     r.choice([1, 2, 3, 4, 5], n, p=STAR_BASE))
    nps = np.array([r.integers(NPS_LO[s], NPS_HI[s] + 1) for s in stars])

    return pd.DataFrame({
        "review_id": [f"R{300000 + i}" for i in range(n)],
        "customer_id": sample["customer_id"].values,
        "order_id": sample["order_id"].values,
        "review_ts": (pd.to_datetime(sample["order_ts"])
                      + pd.to_timedelta(r.integers(3, 21, n), unit="D")).values,
        "star_rating": stars,
        "nps_score": nps,
        "review_channel": r.choice(["email_survey", "onsite", "app"], n,
                                   p=[0.6, 0.3, 0.1]),
    })
```

- [ ] **Step 5: Run test to verify it passes**

Run: `.venv/Scripts/python -m pytest tests/test_ab_reviews.py -v`
Expected: 3 passed (slow — regenerates the session chain)

- [ ] **Step 6: Commit**

```bash
git add python/01_generate/gen_ab_test.py python/01_generate/gen_reviews.py tests/test_ab_reviews.py
git commit -m "feat: A/B test assignments with real lift and behavior-linked reviews/NPS"
```

---

### Task 11: Dirty-data injector + manifest

**Files:**
- Create: `python/01_generate/dirty_data.py`
- Test: `tests/test_dirty_data.py`

**Interfaces:**
- Consumes: dict of the 9 final DataFrames keyed by table name (`customers`, `products`, `orders`, `order_items`, `web_sessions`, `web_events`, `marketing_spend`, `ab_test_assignments`, `reviews_nps`).
- Produces:
  - `dirty_data.inject_defects(tables: dict) -> tuple[dict, dict]` — returns (modified copies, manifest counts dict with keys: `duplicate_orders, missing_emails, malformed_emails, messy_countries, bad_quantities, fat_finger_prices, events_before_session, orders_before_signup, orphan_order_items`)
  - `dirty_data.write_manifest(manifest: dict, path) -> None` — markdown table

- [ ] **Step 1: Write the failing test `tests/test_dirty_data.py`** (uses small synthetic frames — fast)

```python
import numpy as np
import pandas as pd


def _tiny_tables():
    n = 2000
    customers = pd.DataFrame({
        "customer_id": [f"C{i}" for i in range(n)],
        "signup_date": pd.date_range("2024-07-01", periods=n, freq="h").date,
        "country": ["United Kingdom"] * n,
        "email": [f"u{i}@x.com" for i in range(n)],
    })
    orders = pd.DataFrame({
        "order_id": [f"O{i}" for i in range(n)],
        "customer_id": [f"C{i}" for i in range(n)],
        "order_ts": pd.date_range("2025-01-01", periods=n, freq="h"),
    })
    items = pd.DataFrame({
        "order_item_id": [f"OI{i}" for i in range(n)],
        "order_id": [f"O{i}" for i in range(n)],
        "quantity": np.ones(n, int),
        "unit_price_at_sale": np.full(n, 20.0),
    })
    events = pd.DataFrame({
        "event_id": [f"E{i}" for i in range(4000)],
        "event_ts": pd.date_range("2025-01-01", periods=4000, freq="min"),
    })
    return {"customers": customers, "orders": orders,
            "order_items": items, "web_events": events}


def test_inject_defects_counts_match_manifest():
    import _common
    _common.reset_rng()
    from dirty_data import inject_defects
    tables, manifest = inject_defects(_tiny_tables())
    assert len(tables["orders"]) == 2000 + manifest["duplicate_orders"]
    assert tables["customers"]["email"].isna().sum() == manifest["missing_emails"]
    bad_qty = (tables["order_items"]["quantity"] <= 0).sum()
    assert bad_qty == manifest["bad_quantities"]
    assert manifest["fat_finger_prices"] == 15
    assert (tables["order_items"]["order_id"] == "O9999999").sum() \
           == manifest["orphan_order_items"]


def test_originals_not_mutated():
    import _common
    _common.reset_rng()
    from dirty_data import inject_defects
    originals = _tiny_tables()
    email_before = originals["customers"]["email"].copy()
    inject_defects(originals)
    pd.testing.assert_series_equal(originals["customers"]["email"], email_before)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python -m pytest tests/test_dirty_data.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'dirty_data'`

- [ ] **Step 3: Write `python/01_generate/dirty_data.py`**

```python
"""Inject known data-quality defects and record them in a manifest so the
Phase 2 cleaning results can be verified against ground truth."""
from pathlib import Path

import numpy as np
import pandas as pd

from _common import rng

UK_VARIANTS = {"United Kingdom": "UK"}


def inject_defects(tables: dict) -> tuple[dict, dict]:
    r = rng()
    t = {k: v.copy() for k, v in tables.items()}
    manifest: dict[str, int] = {}
    cust, items, events = t["customers"], t["order_items"], t["web_events"]

    # 1. duplicate order rows (double-loaded)
    n_dup = int(len(t["orders"]) * 0.015)
    t["orders"] = pd.concat(
        [t["orders"], t["orders"].sample(n=n_dup, random_state=1)],
        ignore_index=True)
    manifest["duplicate_orders"] = n_dup

    # 2. missing + malformed emails
    miss = cust.sample(frac=0.02, random_state=2).index
    cust.loc[miss, "email"] = None
    bad = cust.drop(index=miss).sample(frac=0.01, random_state=3).index
    cust.loc[bad, "email"] = cust.loc[bad, "email"].str.replace("@", "_at_", regex=False)
    manifest["missing_emails"] = len(miss)
    manifest["malformed_emails"] = len(bad)

    # 3. messy country strings
    mess = cust.sample(frac=0.04, random_state=4).index
    variants = []
    for c in cust.loc[mess, "country"]:
        variants.append(r.choice([c.lower(), c.upper(), f"  {c} ",
                                  UK_VARIANTS.get(c, c.lower())]))
    cust.loc[mess, "country"] = variants
    manifest["messy_countries"] = len(mess)

    # 4. zero/negative quantities
    q = items.sample(frac=0.005, random_state=5).index
    items.loc[q, "quantity"] = r.choice([0, -1, -2], len(q))
    manifest["bad_quantities"] = len(q)

    # 5. fat-finger prices (x100)
    fp = items.drop(index=q).sample(n=15, random_state=6).index
    items.loc[fp, "unit_price_at_sale"] = items.loc[fp, "unit_price_at_sale"] * 100
    manifest["fat_finger_prices"] = 15

    # 6. events timestamped before their session started
    ev = events.sample(n=min(2000, len(events)), random_state=7).index
    events.loc[ev, "event_ts"] = (pd.to_datetime(events.loc[ev, "event_ts"])
                                  - pd.Timedelta(hours=2))
    manifest["events_before_session"] = len(ev)

    # 7. orders timestamped before customer signup
    ob = t["orders"].sample(n=min(100, len(t["orders"])), random_state=8).index
    signup = cust.set_index("customer_id")["signup_date"]
    mapped = t["orders"].loc[ob, "customer_id"].map(signup)
    t["orders"].loc[ob, "order_ts"] = (
        pd.to_datetime(mapped.values)
        - pd.to_timedelta(r.integers(1, 30, len(ob)), unit="D"))
    manifest["orders_before_signup"] = len(ob)

    # 8. orphan order_items
    orph = items.sample(frac=0.002, random_state=9).index
    items.loc[orph, "order_id"] = "O9999999"
    manifest["orphan_order_items"] = len(orph)

    return t, manifest


def write_manifest(manifest: dict, path) -> None:
    lines = ["# Dirty Data Manifest (ground truth for Phase 2 cleaning)", "",
             "| Defect | Rows |", "|---|---|"]
    lines += [f"| {k} | {v} |" for k, v in manifest.items()]
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/Scripts/python -m pytest tests/test_dirty_data.py -v`
Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add python/01_generate/dirty_data.py tests/test_dirty_data.py
git commit -m "feat: dirty-data injector with ground-truth manifest"
```

---

### Task 12: Orchestrator (run_all) + bronze load + calibration gate

**Files:**
- Create: `python/01_generate/run_all.py`, `python/01_generate/calibration_check.py`

**Interfaces:**
- Consumes: every generator from Tasks 6-11, `db_io.load_dataframe`, bronze tables from Task 5.
- Produces: `data/raw/*.csv` (9 files), `docs/dirty_data_manifest.md`, loaded `bronze_*` tables, `docs/calibration_report.md`; `calibration_check.py` exits 1 on any FAIL (hard gate).

- [ ] **Step 1: Write `python/01_generate/run_all.py`**

```python
"""Phase 1 orchestrator: generate -> dirty -> CSV -> bronze."""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import settings
from config.db import get_engine
from utils.db_io import load_dataframe

import _common
import dirty_data
import gen_ab_test
import gen_customers
import gen_marketing
import gen_orders
import gen_reviews
import gen_sessions_events
import gen_products


def main() -> None:
    t0 = time.time()
    _common.reset_rng()

    customers = gen_customers.generate_customers()
    products = gen_products.generate_products()
    orders, items = gen_orders.generate_orders(customers, products)
    sessions, events = gen_sessions_events.generate_sessions_events(customers, orders)
    marketing = gen_marketing.generate_marketing(customers)
    ab = gen_ab_test.generate_ab_test(sessions)
    reviews = gen_reviews.generate_reviews(orders)

    tables = {"customers": customers, "products": products, "orders": orders,
              "order_items": items, "web_sessions": sessions, "web_events": events,
              "marketing_spend": marketing, "ab_test_assignments": ab,
              "reviews_nps": reviews}
    tables, manifest = dirty_data.inject_defects(tables)
    dirty_data.write_manifest(manifest,
                              settings.PROJECT_ROOT / "docs" / "dirty_data_manifest.md")

    tables["web_sessions"] = tables["web_sessions"].drop(columns=["_stage", "_order_id"])
    tables["products"] = tables["products"].drop(columns=["_popularity"])

    raw_dir = settings.PROJECT_ROOT / "data" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    engine = get_engine()
    for name, df in tables.items():
        df.to_csv(raw_dir / f"{name}.csv", index=False)
        n = load_dataframe(df, f"bronze_{name}", engine)
        print(f"  {name:<22} {n:>9,} rows -> bronze_{name}")
    print(f"Done in {time.time() - t0:,.0f}s")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Write `python/01_generate/calibration_check.py`**

```python
"""Hard gate: verify the generated store behaves like a real one.
Reads data/raw CSVs, writes docs/calibration_report.md, exit 1 on any FAIL."""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import settings

LO, HI = 0, 1  # readability indices


def main() -> int:
    raw = settings.PROJECT_ROOT / "data" / "raw"
    orders = pd.read_csv(raw / "orders.csv", parse_dates=["order_ts"])
    items = pd.read_csv(raw / "order_items.csv")
    sessions = pd.read_csv(raw / "web_sessions.csv", usecols=["session_id"])
    events = pd.read_csv(raw / "web_events.csv", usecols=["event_type"])
    ab = pd.read_csv(raw / "ab_test_assignments.csv")
    mkt = pd.read_csv(raw / "marketing_spend.csv")
    cust = pd.read_csv(raw / "customers.csv")

    o = orders.drop_duplicates("order_id")
    completed = o[o["order_status"] == "completed"]
    items_ok = items[(items["quantity"] > 0) & (items["unit_price_at_sale"] < 2000)
                     & (items["order_id"] != "O9999999")]
    rev = items_ok["quantity"] * items_ok["unit_price_at_sale"] - items_ok["line_discount"]
    order_rev = rev.groupby(items_ok["order_id"]).sum()
    comp_rev = order_rev.reindex(completed["order_id"]).dropna()

    per_cust = o.groupby("customer_id").size()
    cust_rev = (completed.set_index("order_id")
                .join(order_rev.rename("rev"))
                .groupby("customer_id")["rev"].sum().sort_values(ascending=False))
    top20 = cust_rev.head(int(len(cust_rev) * 0.2)).sum() / cust_rev.sum()

    daily = completed.set_index("order_ts").join(order_rev.rename("rev"),
                                                 on="order_id")["rev"].resample("D").sum()
    season = daily[daily.index.month.isin([11, 12])].mean() / daily.mean()

    ec = events["event_type"].value_counts()
    ab_rates = ab.groupby("variant")["converted_flag"].mean()
    paid_n = cust["acquisition_channel"].isin(settings.PAID_CHANNELS).sum()

    checks = [
        ("One-time buyer share", (per_cust == 1).mean(), 0.66, 0.72),
        ("Session->order conversion", len(o) / len(sessions), 0.021, 0.028),
        ("Cart abandonment", 1 - ec["purchase"] / ec["add_to_cart"], 0.64, 0.76),
        ("AOV (completed)", comp_rev.mean(), 78, 108),
        ("Top-20% revenue share", top20, 0.50, 0.68),
        ("Nov-Dec revenue multiplier", season, 1.35, 2.10),
        ("A/B relative lift", ab_rates["treatment"] / ab_rates["control"] - 1,
         0.05, 0.30),
        ("Blended paid CAC", mkt["spend_amount"].sum() / paid_n, 55, 100),
    ]

    lines = ["# Calibration Report", "",
             "| Check | Value | Target | Result |", "|---|---|---|---|"]
    failed = False
    for name, val, lo, hi in checks:
        ok = lo <= val <= hi
        failed |= not ok
        lines.append(f"| {name} | {val:.3f} | {lo}-{hi} | "
                     f"{'PASS' if ok else '**FAIL**'} |")
        print(f"{'PASS' if ok else 'FAIL'}  {name}: {val:.3f} (target {lo}-{hi})")
    (settings.PROJECT_ROOT / "docs" / "calibration_report.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 3: Run the full pipeline**

```bash
.venv/Scripts/python python/01_generate/run_all.py
```
Expected: 9 lines of `... rows -> bronze_...` (customers ~12,000; orders ~19,000-20,300 incl. duplicates; web_sessions 800,000; web_events ~1,430,000) and `Done in ...s`. Runtime ~5-15 min (MySQL load dominates).

- [ ] **Step 4: Run the calibration gate**

```bash
.venv/Scripts/python python/01_generate/calibration_check.py
echo "exit: $?"
```
Expected: 8 `PASS` lines, `exit: 0`.
**If any check FAILs:** adjust the responsible constant in `python/config/settings.py` (e.g. AOV low → raise category price floors in `gen_products.CATEGORIES`; seasonality low → raise the 1.8 Nov-Dec factor in `_common.season_multiplier`), rerun `run_all.py` then the gate. Do not widen the target band.

- [ ] **Step 5: Verify bronze row counts in MySQL**

```bash
.venv/Scripts/python -c "
from sqlalchemy import text
import sys; sys.path.insert(0, 'python')
from config.db import get_engine
with get_engine().connect() as c:
    for t in ['customers','orders','web_sessions','web_events']:
        print(t, c.execute(text(f'SELECT COUNT(*) FROM bronze_{t}')).scalar())
"
```
Expected: counts matching the run_all output.

- [ ] **Step 6: Run the whole test suite once**

Run: `.venv/Scripts/python -m pytest -v`
Expected: all tests pass.

- [ ] **Step 7: Commit**

```bash
git add python/01_generate/run_all.py python/01_generate/calibration_check.py docs/dirty_data_manifest.md docs/calibration_report.md
git commit -m "feat: phase-1 orchestrator, bronze load and calibration hard gate"
```

---

### Task 13: Milestone docs + LinkedIn drafts (P0 + P1)

**Files:**
- Create: `docs/SETUP.md`, `docs/01_DATA_MODEL_AND_DICTIONARY.md`, `README.md`, `linkedin/p00_project_announcement.md`, `linkedin/p01_synthetic_data.md`, `tasks/todo.md`

**Interfaces:**
- Consumes: everything built in Tasks 1-12 (documents it).
- Produces: the M1 communication deliverables; checkpoint package for user review.

- [ ] **Step 1: Write `docs/SETUP.md`** — full reproduction guide containing exactly: prerequisites (Python 3.11+, MySQL 8, Power BI Desktop), clone + venv + `pip install -r requirements.txt`, `.env` creation from `.env.example`, root DDL run (`mysql -u root -p < sql/00_setup/00_create_database.sql`), smoke test command, `apply_bronze_ddl.py`, `run_all.py`, `calibration_check.py`, and a **Power BI connectivity check** section: install "MySQL Connector/NET", Get Data → MySQL database → server `127.0.0.1:3306`, database `shopsphere_dw`, user `shopsphere_app`, confirm the 9 bronze tables are visible. Include a Troubleshooting table (auth plugin error → `ALTER USER ... IDENTIFIED WITH mysql_native_password`; connector missing → download link text).

- [ ] **Step 2: Write `docs/01_DATA_MODEL_AND_DICTIONARY.md`** — for each of the 9 tables: purpose, grain, row count (actual from run), every column with type + meaning + example value; the relationship diagram (ASCII, from spec §4); the behavioral realism rules and where each is implemented (file + function name).

- [ ] **Step 3: Write `README.md`** — project title, one-paragraph pitch (the ShopSphere retention problem), tool badges line, architecture diagram (from spec §3), current status table (M1 ✅, M2-M8 planned), quickstart pointing at `docs/SETUP.md`, and a "Data is synthetic, calibrated to 2026 industry benchmarks" honesty note.

- [ ] **Step 4: Write `linkedin/p00_project_announcement.md` and `linkedin/p01_synthetic_data.md`** — each following the 7-part template from spec §8 (hook with a real stat; what was built; why it matters; how — tools/techniques; what the data said; suggested visual; what's next + hashtags). P00 announces the series and the retention problem (~31% average retention, CAC up ~40%). P01 tells the synthetic-data story: why synthetic, the 8 realism rules, the calibration gate with actual PASS numbers from `docs/calibration_report.md`.

- [ ] **Step 5: Write `tasks/todo.md`** — M1 tasks all checked, M2 (P2 cleaning, P3 EDA) listed as next, per CLAUDE.md task-management convention.

- [ ] **Step 6: Commit and tag the milestone**

```bash
git add docs/SETUP.md docs/01_DATA_MODEL_AND_DICTIONARY.md README.md linkedin/ tasks/todo.md
git commit -m "docs: M1 setup guide, data dictionary, README and LinkedIn drafts P0-P1"
git tag m1-foundation
```

- [ ] **Step 7: CHECKPOINT — user review**

Present to the user: calibration report numbers, row counts, one sample of each LinkedIn draft, and the plain-language phase explanation (why/objective/implementation/impact/deliverables). Get approval before starting the M2 plan.
