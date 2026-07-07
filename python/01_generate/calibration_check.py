"""Hard gate: verify the generated store behaves like a real one.
Reads data/raw CSVs, writes docs/calibration_report.md, exit 1 on any FAIL."""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import settings


def main() -> int:
    raw = settings.PROJECT_ROOT / "data" / "raw"
    orders = pd.read_csv(raw / "orders.csv", parse_dates=["order_ts"])
    items = pd.read_csv(raw / "order_items.csv")
    sessions = pd.read_csv(raw / "web_sessions.csv", usecols=["session_id"])
    events = pd.read_csv(raw / "web_events.csv", usecols=["event_type"])
    ab = pd.read_csv(raw / "ab_test_assignments.csv")
    mkt = pd.read_csv(raw / "marketing_spend.csv")
    cust = pd.read_csv(raw / "customers.csv")

    o = orders.drop_duplicates("order_id")
    completed = o[o["order_status"] == "completed"]
    items_ok = items[(items["quantity"] > 0) & (items["unit_price_at_sale"] < 2000)
                     & (items["order_id"] != "O9999999")]
    rev = items_ok["quantity"] * items_ok["unit_price_at_sale"] - items_ok["line_discount"]
    order_rev = rev.groupby(items_ok["order_id"]).sum()
    comp_rev = order_rev.reindex(completed["order_id"]).dropna()

    per_cust = o.groupby("customer_id").size()
    cust_rev = (completed.set_index("order_id")
                .join(order_rev.rename("rev"))
                .groupby("customer_id")["rev"].sum().sort_values(ascending=False))
    top20 = cust_rev.head(int(len(cust_rev) * 0.2)).sum() / cust_rev.sum()

    daily = completed.set_index("order_ts").join(order_rev.rename("rev"),
                                                 on="order_id")["rev"].resample("D").sum()
    season = daily[daily.index.month.isin([11, 12])].mean() / daily.mean()

    ec = events["event_type"].value_counts()
    ab_rates = ab.groupby("variant")["converted_flag"].mean()
    paid_n = cust["acquisition_channel"].isin(settings.PAID_CHANNELS).sum()

    checks = [
        ("One-time buyer share", (per_cust == 1).mean(), 0.66, 0.72),
        ("Session->order conversion", len(o) / len(sessions), 0.021, 0.028),
        ("Cart abandonment", 1 - ec["purchase"] / ec["add_to_cart"], 0.64, 0.76),
        ("AOV (completed)", comp_rev.mean(), 78, 108),
        ("Top-20% revenue share", top20, 0.50, 0.68),
        ("Nov-Dec revenue multiplier", season, 1.35, 2.10),
        ("A/B relative lift", ab_rates["treatment"] / ab_rates["control"] - 1,
         0.05, 0.30),
        ("Blended paid CAC", mkt["spend_amount"].sum() / paid_n, 55, 100),
    ]

    lines = ["# Calibration Report", "",
             "| Check | Value | Target | Result |", "|---|---|---|---|"]
    failed = False
    for name, val, lo, hi in checks:
        ok = lo <= val <= hi
        failed |= not ok
        lines.append(f"| {name} | {val:.3f} | {lo}-{hi} | "
                     f"{'PASS' if ok else '**FAIL**'} |")
        print(f"{'PASS' if ok else 'FAIL'}  {name}: {val:.3f} (target {lo}-{hi})")
    (settings.PROJECT_ROOT / "docs" / "calibration_report.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
