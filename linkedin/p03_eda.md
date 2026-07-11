# P03 — Six Numbers That Describe an Entire Store

**1. Hook**

Before any model, any dashboard, any recommendation — a business needs its
vital signs read. Six numbers told me everything about where ShopSphere makes
money and where it bleeds.

**2. What I built this week**

The first exploratory analysis of the cleaned silver layer: a headless-executed
notebook and six publication-ready figures — monthly revenue, order-value
distribution, the purchase funnel, customer revenue concentration, CAC by
channel, and the repeat-purchase ladder.

**3. Why it matters**

EDA isn't a formality; it's where you find both the story and the bugs. One
month showed a +65% order jump that looked like a data defect — tracing it
back proved it was the growth curve's in-month ramp, not an error. That's the
difference between checking your data and trusting your data.

**4. How**

- Notebook executed headlessly end-to-end (no stale cells, no hidden state)
- Every headline number asserted against the calibration bands from M1 —
  the notebook *fails* if a number drifts out of range
- Figures saved as versioned artifacts, ready for the final report

**5. What the data said**

- AOV **$93.96** · cart abandonment **70.6%** · one-time buyers **69.2%**
- Top 20% of buyers hold **56.9%** of revenue
- Nov–Dec seasonal peak: **1.40×** baseline
- Blended paid CAC: **$73.89** — with email converting ~3× paid social

The pattern: acquisition is expensive, the funnel leaks, and most customers
never return. Everything downstream attacks those three facts.

**6. Suggested visual**

`reports/figures/monthly_revenue.png` — 24 months of revenue with the
seasonal peaks annotated.

**7. What's next**

Moving the KPI layer out of pandas and into pure SQL — window functions,
cohort retention, and a gate that proves SQL and Python agree to the cent.
Synthetic data, calibrated to real 2026 benchmarks.

#DataAnalytics #Ecommerce #Python #EDA #DataVisualization #CustomerRetention
