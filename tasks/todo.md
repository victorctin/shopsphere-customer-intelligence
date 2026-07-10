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

- [x] Method bootstrap (2026-07-07): CLAUDE.md rewritten per Fable-5 handover
      (hard rules, gates, orchestration); `docs/review-rigor-policy.md` added.
      Verified independently: pytest 41 passed / 1 failed (known MySQL
      integration test — `.env` exists but `shopsphere_app` access denied;
      `sql/00_setup/00_create_database.sql` still needs running), calibration
      8/8 PASS. GOTCHA: `codex` CLI not installed — reviewer lane 2 (fresh
      zero-context agent) is the active fallback.
- [x] P2 (CSV lane): Cleaning pipeline bronze → silver + quality report.
      Verified independently 2026-07-10: `run_clean.py` exit 0, quality gate
      9/9 defect classes matched (PERFECT), calibration 8/8 PASS, pytest
      46 passed / 1 failed (known MySQL integration test — server down).
      Silver CSVs: 9 tables, 2,362,203 rows total.
- [ ] P2 (DB lane): blocked on Victor — MySQL80 service needs admin start
      (`net start MySQL80` in elevated shell), then run
      `sql/00_setup/00_create_database.sql` as root, then bronze load
      (`run_all.py`) and `run_clean.py --load-db` for silver tables.
      GOTCHA: working-tree `00_create_database.sql` contains the real app
      password — must NOT be committed; revert to CHANGE_ME after applying.
- [x] P3: EDA notebook + first figures (2026-07-10). `notebooks/01_eda_silver.ipynb`
      executed headlessly via nbclient, no cell errors; 6 PNGs in
      `reports/figures/` (monthly_revenue, aov_distribution, funnel_conversion,
      customer_pareto, cac_by_channel, repeat_purchase). All headline numbers
      inside calibration bands: AOV $93.96, one-time 69.2%, abandonment 70.6%,
      top-20% 56.9%, Nov-Dec 1.40x, CAC $73.89. New pinned deps (approved by
      Victor): matplotlib 3.11.0, nbformat 5.10.4, nbclient 0.11.0,
      ipykernel 7.3.0. Gates: pytest 46 passed / 1 failed (known MySQL),
      calibration 8/8 PASS. GOTCHA: 2026-06 orders +65% vs May — smooth
      in-month ramp from the growth curve, not a defect; noted in notebook.

## Review

- M1 built a seeded synthetic store (~2.36M rows, 24 months) with 8 verified
  behavioral realism rules and a calibration hard gate (8/8 PASS: one-time
  buyers 69.2%, conversion 2.4%, abandonment 70.6%, AOV $94.30, top-20% share
  57.0%, seasonality 1.40x, A/B lift 15.1%, CAC $73.89).
- Full pytest suite: 34 passing; 1 integration test (`test_bronze_ddl.py`)
  blocked on local MySQL credentials — will pass once `.env` exists.
- Outstanding user action: create `.env` + run `sql/00_setup/00_create_database.sql`,
  then `run_all.py` to load bronze (see docs/SETUP.md).
