# Data Quality Report (bronze -> silver)

**Grade: PERFECT **

Graded against `docs/dirty_data_manifest.md` (injection ground truth).
`delta` = found - injected; every class must be 0 or explicitly waived.

| Defect | Injected | Found | Delta | Verdict |
|---|---|---|---|---|
| duplicate_orders | 290 | 290 | 0 | PASS |
| missing_emails | 240 | 240 | 0 | PASS |
| malformed_emails | 118 | 118 | 0 | PASS |
| messy_countries | 480 | 480 | 0 | PASS |
| bad_quantities | 155 | 155 | 0 | PASS |
| fat_finger_prices | 15 | 15 | 0 | PASS |
| events_before_session | 2000 | 2000 | 0 | PASS |
| orders_before_signup | 100 | 100 | 0 | PASS |
| orphan_order_items | 62 | 62 | 0 | PASS |
