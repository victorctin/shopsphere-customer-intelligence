# M8 — Communication Plan

Goal (one line): close the project with the two public-facing deliverables —
a final PDF report generated from the gold layer, and the LinkedIn series
completed through a wrap-up post.

Decisions resolved with Victor (2026-07-11):

- LinkedIn scope: **full series P02–P08** — one post per milestone
  (cleaning, EDA, SQL gold, RFM, CLV/churn, A/B test) plus P08 =
  delivery + series wrap-up. Same 7-section template as P00/P01.
  Drafts only; Victor publishes.
- PDF method: **HTML → headless Edge print-to-PDF**. Zero new Python
  dependencies; Edge is already on the machine. Repo-contained build
  script (same reproducibility standard as the M7 Excel builder).

## Lane 1 — Final PDF report

- `python/05_delivery/build_final_report.py` + `report_template.html`:
  - Headline KPIs queried live from gold views — SQL copied verbatim from
    `build_excel_workbook.py` (which copies the M3 gate) so the report
    states the contract numbers.
  - 15 figures from `reports/figures/` embedded as base64 (self-contained
    HTML, ~1 MB).
  - Narrative numbers (model metrics, gate results) are the verified
    values recorded on the board — they are milestone facts, not
    re-derivable from SQL.
  - Renders `reports/shopsphere_final_report.html`, then prints
    `reports/shopsphere_final_report.pdf` via
    `msedge --headless --print-to-pdf`.
- Self-validation gate (exit 1 on failure), mirroring the Excel gate:
  1. Re-open the written HTML, extract labeled KPI values, compare against
     fresh SQL (revenue exact, AOV ±0.5%, buyers exact).
  2. All 15 figure files embedded (count `data:image/png` occurrences).
  3. PDF exists and is > 300 KB (embedded figures make a thin PDF
     impossible).

## Lane 2 — LinkedIn series P02–P08

Seven drafts in `linkedin/`, each with the P00/P01 section structure
(Hook / What I built / Why it matters / How / What the data said /
Suggested visual / What's next + hashtags). Every number quoted must match
the board's verified values.

- P02 cleaning (quality gate 9/9, 290 dupes, 2.36M rows)
- P03 EDA (6 figures, AOV $93.96, abandonment 70.6%)
- P04 SQL gold (12 views, gate 5/5, cohort 267/267 cells vs pandas)
- P05 RFM (11,323 buyers, Champions 4%/12%, Hibernating 30%/18%)
- P06 CLV + churn (backtest 1.06, AUC 0.813, top decile 38.2%)
- P07 A/B (+15.06% lift, p=7.9e-04, power 91.9%, basket guardrail)
- P08 delivery + wrap-up (Excel 5/5, Power BI 8/8, series recap)

## Gates before "done"

- `build_final_report.py` exit 0 with gate lines printed.
- pytest count never drops (55 baseline) — new unit tests for the report
  builder's pure functions.
- Calibration 8/8 PASS (no generator changes expected — run anyway).
