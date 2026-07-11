# P05 — 4% of Customers, 12% of Revenue

**1. Hook**

Treating all customers the same is the most expensive default in e-commerce.
ShopSphere's 11,323 buyers turned out to contain nine very different
businesses.

**2. What I built this week**

RFM segmentation over the gold layer: every buyer scored on Recency,
Frequency and Monetary value, then mapped through an ordered rule grid into
9 named segments — Champions, Loyal, At Risk, Hibernating, and friends.

**3. Why it matters**

Segments turn averages into actions. "Average revenue per buyer is $147"
suggests nothing. "Champions average $487 and Hibernating holds 18% of your
historic revenue" tells you exactly where loyalty perks and win-back
campaigns should go — and where discounting would be a waste.

**4. How**

- R from recency quintiles; F from fixed order-count bins (1 / 2 / 3 / 4 / 5+);
  M from quintiles
- An ordered (R,F) rule grid assigns segments — deterministic and explainable
  to a marketer, unlike a k-means cluster
- Validation cell asserts buyer count and total revenue match the gold layer
  exactly (the notebook fails on drift)

**5. What the data said**

- **Champions: 4% of buyers → 12% of revenue** ($487 avg vs $147 overall)
- **Hibernating: 30% of buyers, 18% of historic revenue** — the win-back pool
- **70.4% of buyers have exactly one order** — the retention trap from P00,
  now with names and addresses
- All 11,323 buyers and $1,664,813.13 tie out to the gold layer to the cent

**6. Suggested visual**

`reports/figures/rfm_segment_value.png` — revenue share by segment, sorted.

**7. What's next**

Segments describe the past. Next: predicting the future — customer lifetime
value and churn risk, with a backtest to prove the model isn't lying.
Synthetic data, calibrated to real 2026 benchmarks.

#DataAnalytics #Ecommerce #RFM #CustomerSegmentation #Python #SQL
