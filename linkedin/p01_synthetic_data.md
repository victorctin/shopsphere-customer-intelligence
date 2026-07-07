# P01 — Synthetic Data That Behaves Like a Real Store

**1. Hook**

Every data portfolio project faces the same credibility problem: real customer
data is confidential, and toy datasets teach toy lessons. My answer: build a
synthetic store so realistic it has to pass a calibration exam before any
analysis is allowed to touch it.

**2. What I built this week**

A seeded Python data engine that generates 24 months of e-commerce life:
12,000 customers, ~19,700 orders, 800,000 sessions, 1.43M funnel events,
daily marketing spend, a real A/B test, and 4,452 reviews — ~2.36M rows loaded
into a MySQL bronze layer, in one command.

**3. Why it matters**

If the data doesn't behave like a real business, every downstream insight is
fiction. Realism here isn't cosmetic — retention curves, funnel decay and
channel economics are the *subject* of the analysis, so they must be baked in
and then independently verified.

**4. How**

- 8 behavioral realism rules coded into the generators: Pareto revenue
  concentration, a repeat-purchase ladder (2nd→3rd order is easier than
  1st→2nd), calibrated funnel decay, channel economics (email converts ~3x
  paid social), Nov–Dec seasonality, price-elastic baskets, satisfaction
  linked to loyalty, and an A/B test with a real ~15% effect
- A **calibration gate** (`calibration_check.py`) that fails the whole build
  if any of 8 checks drifts out of its industry-benchmark band
- Test-driven: every generator was written against failing pytest tests first
- Plus a documented layer of injected data defects (duplicates, malformed
  emails, impossible timestamps) for the cleaning phase to catch — with a
  ground-truth manifest to grade the cleaning against

**5. What the data said**

The gate's verdict — 8/8 PASS: one-time buyers 69.2% (target 66–72%),
session→order conversion 2.4% (2.1–2.8%), cart abandonment 70.6% (64–76%),
AOV $94.30 ($78–108), top-20% revenue share 57.0% (50–68%), Nov–Dec revenue
1.40x baseline, A/B lift +15.1%, blended CAC $73.89 ($55–100).

**6. Suggested visual**

`reports/figures/p01_calibration_gate.png` — the 8 checks as a PASS/FAIL
scorecard with each value plotted inside its target band.

**7. What's next**

The data is realistic — and deliberately dirty. Next post: the cleaning
pipeline, and how I graded it against the known defect manifest. As always:
the data is synthetic, calibrated to real 2026 industry benchmarks.

#DataAnalytics #Ecommerce #SQL #Python #PowerBI #SyntheticData #DataQuality
