# M2 — Trust the Data (P2 Cleaning + P3 EDA)

Spec: `docs/superpowers/specs/2026-07-06-ecommerce-cis-design.md` §6 (M2), §4.2 (defects).
Working mode: TDD per task, commit per task, checkpoint at milestone end.
Environment note: MySQL credentials are user-local; every task below is built and
verified against the `data/raw/*.csv` outputs of M1 (same content as bronze).
`run_clean.py` performs the bronze→silver DB load when `.env` exists.

## Ground truth to beat (docs/dirty_data_manifest.md)

duplicate_orders 290 · missing_emails 240 · malformed_emails 118 ·
messy_countries 480 · bad_quantities 155 · fat_finger_prices 15 ·
events_before_session 2000 · orders_before_signup 100 · orphan_order_items 62

## Cleaning philosophy (rule-by-rule, every action counted)

Each rule does exactly one of: **drop** (unusable row), **fix** (recoverable
value), or **flag** (keep + mark, business decides later). The audit records
rows affected per rule; `docs/data_quality_report.md` grades found-vs-manifest.

| # | Rule | Action | Target defect |
|---|---|---|---|
| R1 | Duplicate `order_id` rows | drop (keep first) | duplicate_orders |
| R2 | Missing / malformed emails | flag `email_valid=0` (malformed also nulled) | missing+malformed_emails |
| R3 | Messy country strings | fix: trim, canonical case, `UK`→`United Kingdom` | messy_countries |
| R4 | Quantity ≤ 0 | drop line | bad_quantities |
| R5 | Fat-finger price (≥ 20x median price of same product) | fix: ÷100 | fat_finger_prices |
| R6 | Event before session start | fix: clamp to session_start_ts | events_before_session |
| R7 | Order before customer signup | flag `ts_conflict=1` | orders_before_signup |
| R8 | Order item referencing missing order | drop line | orphan_order_items |

### Task 1: Cleaning rules engine — `python/02_clean/clean_rules.py`
- Test: `tests/test_clean_rules.py` (small synthetic frames per rule, red first)
- Pure functions: each `rule_*(df, ...) -> tuple[DataFrame, int]` (new copy + rows affected);
  `clean_all(tables: dict) -> tuple[dict, dict]` returns silver frames + audit dict
  with the 8 rule keys (+ passthrough counts for sessions/products/etc.).
- Silver frames add columns: `customers.email_valid`, `orders.ts_conflict`.

### Task 2: Quality report — `python/02_clean/quality_report.py`
- Test: `tests/test_quality_report.py`
- `grade(audit: dict, manifest: dict) -> DataFrame` (defect, injected, found, delta, verdict)
- `write_report(grade_df, path)` → `docs/data_quality_report.md`; PERFECT when all deltas 0.
- Manifest parser reads `docs/dirty_data_manifest.md`.

### Task 3: Silver DDL + orchestrator
- `sql/20_silver/01_silver_tables.sql`: 9 typed `silver_*` tables — proper types,
  NOT NULL on keys, CHECK constraints (quantity > 0, star_rating 1–5, nps 0–10),
  PRIMARY KEYs; FKs documented but not enforced (bulk-load friendly, medallion norm).
- `python/02_clean/run_clean.py`: read `data/raw/*.csv` → `clean_all` → write
  `data/silver/*.csv` + quality report; `--load-db` flag applies DDL + loads
  `silver_*` tables via `db_io.load_dataframe` when credentials exist.
- Verify: run without `--load-db`; quality report deltas all 0.

### Task 4: P3 EDA — figures + summary
- `python/utils/plotting.py`: one style helper (LinkedIn-friendly 1200×675, consistent palette).
- `python/03_eda/run_eda.py`: reads `data/silver/*.csv`, emits 9 figures to
  `reports/figures/` + `docs/eda_summary.md` with one insight sentence per chart:
  1. monthly revenue (completed orders) — seasonality
  2. AOV distribution — log-normal shape
  3. revenue by category (top 8)
  4. top 15 products by revenue
  5. revenue by country (top 10)
  6. customer concentration Pareto curve
  7. new vs returning revenue by month
  8. basket size distribution
  9. orders by weekday × hour heatmap
- Test: `tests/test_eda.py` — smoke: figures exist + non-empty, summary has 9 insight lines.
- Add `matplotlib` to `requirements.txt`.

### Task 5: M2 docs + LinkedIn + tag
- `linkedin/p02_data_cleaning.md` (7-part template §8: graded-against-ground-truth story)
- `linkedin/p03_eda.md` (7-part template: what the store's data says)
- Update `tasks/todo.md` (M2 checked, M3 next); README status table M2 ✅.
- Commit; tag `m2-trust-the-data`. CHECKPOINT: present quality report + figures to user.
