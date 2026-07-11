# P07 — The A/B Test That Almost Fooled Me (via Its Guardrail)

**1. Hook**

A +15% conversion lift with p = 0.0008 sounds like a slam dunk. The
interesting part of ShopSphere's free-shipping test wasn't the win — it was
the guardrail metric quietly whispering "check the basket sizes."

**2. What I built this week**

A power-aware analysis of the `free_shipping_threshold` experiment: 30,000
customers per arm, fixed-horizon z-test, sample-ratio-mismatch check, design
MDE and achieved power, plus a revenue guardrail.

**3. Why it matters**

Most A/B write-ups stop at the p-value. But a test you didn't power-check
can't distinguish "no effect" from "didn't look hard enough," a test without
an SRM check may be corrupted at randomization, and a conversion win can hide
a revenue loss. The boring checks are the analysis.

**4. How**

- SRM first: chi-square on assignment counts (a broken randomizer invalidates
  everything after it)
- Two-proportion z-test with a log-ratio CI for relative lift
- Design MDE at 80% power computed *before* judging the result
- Guardrail: revenue per converted order and per assignment, Welch's t

**5. What the data said**

- SRM p = **1.0000** — randomization clean
- Conversion **3.43% → 3.95%**: lift **+15.1%** (95% CI +6.0%…+24.9%),
  p = **7.9e-04**, achieved power **91.9%** vs a +12.5% design MDE
- Guardrail: converted-order revenue **$88.80 vs $97.36** (p = 0.071) — a
  *suggestive* basket shrink, not proven. Revenue per assignment still favors
  treatment ($3.17 vs $3.00)
- Verdict: **ship it — and monitor basket size in production**

**6. Suggested visual**

`reports/figures/ab_conversion_ci.png` — conversion by arm with 95% CIs.

**7. What's next**

Analysis nobody sees is analysis that didn't happen: packaging everything
into an Excel workbook, a Power BI model, and a final PDF — each with its own
validation gate. Synthetic data, calibrated to real 2026 benchmarks.

#ABTesting #Statistics #Ecommerce #DataScience #Experimentation #Python
