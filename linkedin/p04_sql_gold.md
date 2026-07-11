# P04 — Making SQL and Python Agree to the Cent

**1. Hook**

"The dashboard says $1.66M, the notebook says $1.71M" — every analytics team
has lived this meeting. My rule for ShopSphere: two independent computations
of every KPI, and they must match exactly, or the build fails.

**2. What I built this week**

The gold layer: 12 SQL views on top of silver — headline KPIs, revenue trends,
customer Pareto ranking, purchase sequences, top products, and a full cohort
retention matrix. All pure SQL with window functions; pandas is not invited
to this layer.

**3. Why it matters**

The gold layer is the single source of truth every deliverable reads (Excel,
Power BI, the final report). If it's wrong, everything downstream is
confidently wrong. So it doesn't get to *claim* correctness — it has to prove
agreement with an independent implementation.

**4. How**

- Views only — zero writes to bronze or silver
- Window functions for ranking, sequencing, and cohort math
- A hard gate re-computes 5 headline KPIs in pandas from silver and compares
  (±0.5% tolerance)
- Adversarial extra check on the money logic: the SQL cohort retention matrix
  vs an independent pandas rebuild — cell by cell

**5. What the data said**

Gate: **5/5 PASS**. The cohort matrix matched in **267 of 267 cells** —
exactly. Cumulative completed revenue ties out to **$1,664,813.13** in both
worlds. That number is now the contract every later deliverable is audited
against — you'll see it again in this series.

**6. Suggested visual**

`reports/figures/customer_pareto.png` — cumulative revenue vs buyer rank,
straight from the gold view.

**7. What's next**

With trusted KPIs in place, the interesting question: *who* are these
customers? RFM segmentation on 11,323 buyers. Synthetic data, calibrated to
real 2026 benchmarks.

#DataAnalytics #SQL #DataEngineering #Ecommerce #MySQL #AnalyticsEngineering
