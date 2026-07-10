"""Apply gold-layer views and run the M3 gate: SQL KPI numbers must match the
pandas-verified P3 notebook values within tolerance. Exit 1 on any mismatch."""
import sys
from pathlib import Path

from sqlalchemy import bindparam, text

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import settings
from config.db import get_engine
from utils.run_sql import run_sql_file

GOLD_FILES = ["01_gold_kpi_views.sql", "02_gold_window_views.sql",
              "03_gold_cohort_retention.sql"]
REL_TOLERANCE = 0.005  # 0.5% — covers rounding of the published P3 numbers

# (name, sql, expected) — expectations are the P3 notebook values verified
# against calibration bands on 2026-07-10.
GATE_CHECKS = [
    ("AOV (completed)",
     "SELECT AVG(order_revenue) FROM gold_order_revenue "
     "WHERE order_status = 'completed'",
     93.96),
    ("One-time buyer share",
     "SELECT AVG(orders_all = 1) FROM gold_customer_summary "
     "WHERE orders_all > 0",
     0.692),
    ("Cart abandonment",
     "SELECT 1 - MAX(CASE WHEN event_type = 'purchase' THEN events END) "
     "/ MAX(CASE WHEN event_type = 'add_to_cart' THEN events END) "
     "FROM gold_funnel",
     0.706),
    ("Top-20% revenue share",
     "SELECT SUM(CASE WHEN revenue_rank <= FLOOR(buyer_count * 0.2) "
     "THEN revenue_completed ELSE 0 END) / SUM(revenue_completed) "
     "FROM gold_customer_pareto",
     0.569),
]


def main() -> int:
    engine = get_engine()
    gold_dir = settings.PROJECT_ROOT / "sql" / "30_gold"
    for fname in GOLD_FILES:
        n = run_sql_file(gold_dir / fname, engine)
        print(f"Applied {fname}: {n} statements")

    failed = False
    with engine.connect() as conn:
        results = []
        for name, sql, expected in GATE_CHECKS:
            value = float(conn.execute(text(sql)).scalar_one())
            results.append((name, value, expected))

        cac_sql = text(
            "SELECT (SELECT SUM(spend) FROM gold_channel_cac_monthly) / "
            "(SELECT COUNT(*) FROM silver_customers "
            "WHERE acquisition_channel IN :paid)"
        ).bindparams(bindparam("paid", expanding=True))
        cac = float(conn.execute(cac_sql, {"paid": settings.PAID_CHANNELS})
                    .scalar_one())
        results.append(("Blended paid CAC", cac, 73.89))

        for name, value, expected in results:
            ok = abs(value - expected) <= abs(expected) * REL_TOLERANCE
            failed = failed or not ok
            print(f"  {'PASS' if ok else 'FAIL'} {name}: "
                  f"{value:.4f} (expected {expected} +/-0.5%)")

        cohorts, max_offset, cells = conn.execute(text(
            "SELECT COUNT(DISTINCT cohort_month), MAX(months_since_first), "
            "COUNT(*) FROM gold_cohort_retention")).one()
        print(f"Cohort matrix: {cohorts} cohorts x up to "
              f"{max_offset} months, {cells} cells")

    print("M3 gate:", "FAIL" if failed else "PASS (5/5)")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
