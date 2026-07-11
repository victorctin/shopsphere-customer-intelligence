# P06 — Predicting Which Customers Come Back (and Proving It)

**1. Hook**

Any model can predict customer lifetime value. The question your CFO should
ask: *how do you know it's right?* Mine had to pass a time-travel exam before
its numbers were allowed in the report.

**2. What I built this week**

Probabilistic CLV (BG/NBD + Gamma-Gamma) and a churn classifier for
ShopSphere. The BG/NBD implementation is written directly on numpy/scipy —
the standard `lifetimes` library is unmaintained — with 8 unit tests,
including seeded parameter recovery.

**3. Why it matters**

CLV converts retention talk into budget math: if a customer's future value is
below acquisition cost, growth-by-acquisition is a treadmill. And a churn
score turns "we should do retention" into a ranked list of exactly whom to
save first.

**4. How**

- **Backtest before belief**: train on the first 18 months, predict repeat
  purchases in the held-out 26 weeks, compare to what actually happened
- Churn label from a 26-week holdout with strictly pre-cutoff features —
  leakage checked, not assumed
- Validation cell asserts totals against the gold layer ($1,664,813.13 again)

**5. What the data said**

- Backtest: predicted/actual repeat purchases = **1.06** (1,180 vs 1,110) —
  the model over-promises by 6%, and now we know that
- 12-month CLV: **$282,875** total, mean **$25.09**, with the **top decile
  holding 38.2%** of all future value
- Churn AUC **0.81** against a brutal 89.9% base churn rate
- Punchline: mean future CLV ($25) is far below blended CAC ($74) —
  acquisition only pays on multi-year value or high-CLV targeting

**6. Suggested visual**

`reports/figures/clv_distribution.png` — the CLV distribution with the top
decile shaded.

**7. What's next**

Prediction meets causation: the free-shipping A/B test, and the statistics
that keep you from shipping noise. Synthetic data, calibrated to real 2026
benchmarks.

#DataScience #CLV #ChurnPrediction #Ecommerce #Python #MachineLearning
