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

## M4 — Who Are Our Customers ✅

- [x] RFM scoring + segmentation delivered 2026-07-10:
      `notebooks/02_rfm_segmentation.ipynb` (executed headlessly, no cell
      errors) + 4 figures (rfm_segment_sizes, rfm_heatmap, rfm_segment_value,
      rfm_channel_value). Reads MySQL `gold_customer_summary` (M3 contract).
      11,323 buyers, 9 segments via ordered (R,F) rule grid; R quintiles,
      F fixed bins 1/2/3/4/5+, M quintiles. Headline: Hibernating 30% of
      buyers / 18% of revenue; Champions 4% of buyers / 12% of revenue
      (avg $487 vs $147 mean); F=1 buyers 70.4%. Validation cell asserts
      buyers == gold_customer_pareto and revenue == $1,664,813.13 ==
      gold_monthly_kpis (notebook fails on drift). No new dependencies —
      segmentation is quantile/rule-based, KMeans deferred (would need
      scikit-learn approval). Gates: pytest 47 passed, calibration 8/8.

## M5 — Value & Risk ✅

- [x] CLV + churn delivered 2026-07-10. New deps approved by Victor:
      scipy==1.18.0, scikit-learn==1.9.0 (pinned). `python/04_model/btyd.py`:
      BG/NBD + Gamma-Gamma implemented on numpy/scipy (the `lifetimes` lib is
      unmaintained); 8 unit tests in `tests/test_btyd.py` incl. seeded
      parameter recovery <25% rel. err. `notebooks/03_clv_churn.ipynb`
      (headless, no cell errors) + 3 figures (clv_distribution,
      churn_roc_calibration, churn_feature_importance). Numbers: 26-week
      time-split backtest pred/actual = 1.06 (1,180 vs 1,110 repeat
      purchases), corr(x,m_x)=0.001 (GG independence OK), 12-mo CLV total
      $282,875 / mean $25.09 / top decile 38.2%; churn (26w holdout label,
      pre-cutoff features, no leakage): AUC logistic 0.813, grad boosting
      0.793, base rate 89.9%. Validation cell asserts revenue ==
      $1,664,813.13 == gold and buyer gap (46) == zero-revenue buyers in
      gold (92 completed orders lost all items in cleaning — measured, not
      assumed). Gates: pytest 55 passed (was 47), calibration 8/8.

## M6 — Experimentation ✅

- [x] Power-aware A/B analysis delivered 2026-07-10:
      `notebooks/04_ab_test.ipynb` (headless, no cell errors) + 2 figures
      (ab_conversion_ci, ab_power_curve). Test `free_shipping_threshold`,
      30,000/arm: SRM chi-square p=1.0000 (clean randomization); conversion
      3.43% -> 3.95%, lift +15.06% (95% CI +6.0%..+24.9%), z=3.36,
      p=7.9e-04; design MDE @80% power = +12.5% relative, achieved power
      91.9%. Guardrail: converted-order revenue treatment $88.80 vs control
      $97.36, Welch p=0.071 — suggestive basket shrink, not significant;
      revenue/assignment still favors treatment ($3.17 vs $3.00). Validation
      asserts: n=60,000, SRM p>0.001, lift within 0.005 of calibration
      0.151, CI excludes 0, power >0.8. No new deps (scipy.stats only).
      Gates: pytest 55 passed, calibration 8/8.

## M7 — Delivery ✅

- [x] Plan first: `docs/m7_delivery_plan.md` (openpyxl + live Power BI build
      both approved by Victor). Excel lane 2026-07-10:
      `python/05_delivery/build_excel_workbook.py` →
      `reports/shopsphere_executive_workbook.xlsx`, 9 sheets, self-validation
      gate 5/5 PASS (revenue 1,664,813.13 exact vs SQL, AOV 93.9564,
      RFM buyers 11,323 == gold_customer_pareto, A/B lift 0.1506 within
      0.005 of calibration 0.151). Committed ec5104f.
- [x] Power BI lane 2026-07-11: semantic model built live via modeling MCP
      into `reports/shopsphere_dashboard.pbix` — 9 import tables, 1
      relationship (gold_order_revenue[customer_id] *→1
      gold_customer_summary[customer_id]), 12 DAX measures. Data lands over
      ODBC (`MySQL ODBC 9.7 Unicode Driver`), NOT Connector/NET — the
      Store-packaged Desktop never detects Connector/NET (proven twice, incl.
      after clean restart with 9.7.0 installed). DAX acceptance run on the
      loaded model: Total Revenue 1,664,813.13 exact, AOV 93.9564,
      Completed Orders 17,811, Unique Buyers 11,323, One-time 69.21%,
      Abandonment 70.60%, Paid CAC 73.89, order rows 19,397 — 8/8 targets.
      Page visuals are Victor's by-hand step per
      `docs/m7_powerbi_page_checklist.md` (45–60 min, not yet done).

## M8 — Communication ✅

- [x] Plan first: `docs/m8_communication_plan.md` (LinkedIn scope = full
      series P02–P08 and PDF via HTML → headless Edge, both chosen by Victor
      2026-07-11).
- [x] Final PDF report 2026-07-11: `python/05_delivery/build_final_report.py`
      + `report_template.html` → `reports/shopsphere_final_report.html`
      (self-contained, 15 figures base64) + `.pdf` (905,212 bytes, headless
      Edge print, zero new deps). KPIs queried live with the M3-gate SQL
      (reused from `build_excel_workbook.py`); self-validation gate 6/6 PASS
      (revenue 1,664,813.13 exact vs SQL, buyers 11,323, AOV 93.9564,
      lift 0.1506, 15/15 figures embedded, PDF size floor). Visual layout of
      the PDF NOT eyeballed (no poppler for page rendering) — Victor should
      open it once before sharing.
- [x] LinkedIn series completed: p02_data_cleaning, p03_eda, p04_sql_gold,
      p05_rfm_segmentation, p06_clv_churn, p07_ab_test, p08_delivery_wrapup —
      same 7-section template as P00/P01, every number from the verified
      board values. Drafts only; publishing is Victor's step.
- [x] Gates: pytest 62 passed / 0 failed (was 55; +7 unit tests in
      `tests/test_final_report.py`, no MySQL/Edge needed), calibration 8/8
      PASS, report gate 6/6.
- [x] Adversarial review (attack-the-claims, fresh zero-context agent —
      codex CLI still absent) 2026-07-11: 7 findings, all remediated except
      F6 (claim-wording only; M7↔M3 SQL hand-copy predates this diff,
      verified textually in sync). Fixed: stale-PDF mask (unlink + %PDF
      magic), stale-but-labeled-live narrative (cover wording + live
      $buyers/$ab_conv_* placeholders), placeholder check now
      Template.get_identifiers() (catches $Caps/${braced}), None data-window
      guard, find_edge() before artifact writes, PNG magic check. +4 pinning
      tests. Post-remediation gates re-run personally: report gate 6/6
      (PDF 905,311 bytes), pytest 66 passed / 0 failed, calibration 8/8.

## Review (written 2026-07-11, for a cold-started session)

- **State: M1–M8 complete — project delivered.** MySQL `shopsphere_dw` live
  (9 bronze_* + 9 silver_* tables + 12 gold_* views). Deliverables: 4 executed
  notebooks + 15 figures, Excel workbook (gate 5/5), Power BI pbix (model +
  data loaded), final PDF report (gate 6/6), LinkedIn drafts P00–P08. Gates
  green: pytest 66 passed, calibration 8/8, quality report PERFECT 9/9.
- Remaining Victor-only steps: Power BI report pages by hand
  (`docs/m7_powerbi_page_checklist.md`, 45–60 min), eyeball the final PDF
  layout once, publish the LinkedIn drafts.
- GOTCHAS for the next session:
  - Power BI modeling MCP: msmdsrv port CHANGES on every Desktop restart —
    always ListLocalInstances then Connect; "base version must not be
    negative" on refresh = stale handle → Disconnect + Connect and retry.
  - Store-packaged Power BI Desktop does not detect MySQL Connector/NET
    (any version) — partitions use ODBC `Odbc.Query`. Power Query REFUSES
    uid/pwd inside ODBC connection strings and Desktop doesn't support
    `CredentialConnectionString`; the credential lives in Desktop's data
    source settings (user `shopsphere_app`). If refresh says "Access denied
    for user 'shopsphere_dw'" the stored credential has the wrong username —
    fix via File → Options → Data source settings → Edit Permissions.
  - The pbix must be saved in Desktop (Ctrl+S) after XMLA changes — the
    model lives in the running process until saved.
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
