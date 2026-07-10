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
- [x] P2 (DB lane) 2026-07-10: MySQL started + setup applied by Victor
      (password kept in tracked SQL by his decision, commit ffa235a).
      Bronze loaded from frozen data/raw (2,362,710 rows, 9 tables, 281s);
      silver via `run_clean.py --load-db` (quality gate 9/9, 285s).
      Verified by SQL COUNT(*): 18 tables, bronze/silver counts match CSVs
      exactly (e.g. orders 19,687 bronze vs 19,397 silver = 290 dupes
      dropped). pytest now 47 passed / 0 failed. GOTCHA (resolved): `CREATE
      USER IF NOT EXISTS` does not update an existing user's password —
      needed root `ALTER USER` because the user pre-existed from Jul 7.
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

## M3 — SQL Analytics Core ✅

- [x] Plan written first per CLAUDE.md rule: `docs/m3_gold_plan.md`.
- [x] Gold layer delivered 2026-07-10: 12 views in `sql/30_gold/`
      (01 KPI views: order_revenue, monthly_kpis, funnel, channel_cac_monthly,
      customer_summary, nps_monthly; 02 window views: revenue_trend,
      customer_pareto, customer_order_seq, top_products; 03 cohort_retention).
      Applied + gated by `python/03_gold/run_gold.py` — M3 gate 5/5 PASS:
      AOV 93.9564, one-time 0.6921, abandonment 0.7060, top-20% 0.5686,
      paid CAC 73.8937 (each ±0.5% vs P3 pandas values). Adversarial extra
      checks (scratchpad, money-logic review rule): cohort matrix SQL vs
      independent pandas 267/267 cells exact, cohort_size consistent, NPS
      8.201 / stars 4.048 vs notebook 8.20/4.05, cumulative revenue ties out
      to $1,664,813.13. Gates re-run: pytest 47 passed, calibration 8/8
      (exit 0). Views only — zero writes to bronze/silver.

## Review (written 2026-07-10, for a cold-started session)

- **State: M1 + M2 complete.** MySQL `shopsphere_dw` is live with 18 tables:
  9 bronze_* (2,362,710 rows, frozen raw) + 9 silver_* (cleaned). Gates all
  green: pytest 47/47, calibration 8/8 PASS, quality report PERFECT 9/9.
  EDA notebook `notebooks/01_eda_silver.ipynb` + 6 figures in
  `reports/figures/` (headline numbers in the P3 entry above).
- Next: M3 gold layer (see section above). Backend/schema → write the plan
  before implementing; new SQL goes under `sql/` following the
  `10_bronze`/`20_silver` numbering (gold = `30_gold`, verify before use).
- GOTCHAS for the next session:
  - MySQL80 Windows service may be stopped after reboot; starting needs an
    elevated shell (Victor action). Test connectivity before assuming code bugs.
  - `CREATE USER IF NOT EXISTS` never updates an existing user's password —
    use root `ALTER USER` (bit us 2026-07-10).
  - Real app password lives in `sql/00_setup/00_create_database.sql` by
    Victor's explicit decision (commit ffa235a) — do NOT revert to CHANGE_ME.
    See memory `credentials-in-setup-sql-by-decision`.
  - `run_all.py` REGENERATES data before loading bronze — for load-only use
    the pattern in this session's scratchpad (run_sql_file + load_dataframe
    from data/raw). Don't regenerate mid-batch (frozen-data rule).
  - 2026-06 (final month) orders are +65% vs May — real growth-curve ramp,
    not a defect; don't "fix" the generator for it.
  - `codex` CLI not installed — adversarial review fallback is a fresh
    zero-context agent.
