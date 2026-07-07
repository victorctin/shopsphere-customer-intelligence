# Project Tasks

## M1 — Foundation ✅

- [x] Task 1: Project scaffolding + environment
- [x] Task 2: Config module (settings + engine factory)
- [x] Task 3: Shared generator helpers + DB I/O utilities
- [x] Task 4: MySQL database, app user, smoke test *(DB application deferred — needs local `.env`)*
- [x] Task 5: Bronze DDL + apply script
- [x] Task 6: Generators — customers & products
- [x] Task 7: Generator — orders & order_items (retention engine)
- [x] Task 8: Generator — web sessions & events (funnel engine)
- [x] Task 9: Generator — marketing spend (CAC-reconciled)
- [x] Task 10: Generators — A/B test assignments & reviews/NPS
- [x] Task 11: Dirty-data injector + manifest
- [x] Task 12: Orchestrator (run_all) + calibration hard gate — 8/8 PASS
      *(bronze MySQL load pending local `.env` credentials)*
- [x] Task 13: Milestone docs + LinkedIn drafts (P0 + P1)

### Security hardening (post-audit)

- [x] Table-name allowlist validation before `TRUNCATE TABLE` (`db_io.py`)
- [x] Fail fast on missing `DB_PASSWORD` (`settings.py`)
- [x] `URL.create()` connection URL — escaped credentials, masked in logs

## M2 — Trust the Data (next)

- [ ] P2: Cleaning pipeline bronze → silver; data-quality report graded
      against `docs/dirty_data_manifest.md`
- [ ] P3: EDA notebook + first figures for `reports/figures/`

## Review

- M1 built a seeded synthetic store (~2.36M rows, 24 months) with 8 verified
  behavioral realism rules and a calibration hard gate (8/8 PASS: one-time
  buyers 69.2%, conversion 2.4%, abandonment 70.6%, AOV $94.30, top-20% share
  57.0%, seasonality 1.40x, A/B lift 15.1%, CAC $73.89).
- Full pytest suite: 34 passing; 1 integration test (`test_bronze_ddl.py`)
  blocked on local MySQL credentials — will pass once `.env` exists.
- Outstanding user action: create `.env` + run `sql/00_setup/00_create_database.sql`,
  then `run_all.py` to load bronze (see docs/SETUP.md).
