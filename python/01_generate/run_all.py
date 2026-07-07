"""Phase 1 orchestrator: generate -> dirty -> CSV -> bronze."""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import settings
from config.db import get_engine
from utils.db_io import load_dataframe

import _common
import dirty_data
import gen_ab_test
import gen_customers
import gen_marketing
import gen_orders
import gen_reviews
import gen_sessions_events
import gen_products


def main() -> None:
    t0 = time.time()
    _common.reset_rng()

    customers = gen_customers.generate_customers()
    products = gen_products.generate_products()
    orders, items = gen_orders.generate_orders(customers, products)
    sessions, events = gen_sessions_events.generate_sessions_events(customers, orders)
    marketing = gen_marketing.generate_marketing(customers)
    ab = gen_ab_test.generate_ab_test(sessions)
    reviews = gen_reviews.generate_reviews(orders)

    tables = {"customers": customers, "products": products, "orders": orders,
              "order_items": items, "web_sessions": sessions, "web_events": events,
              "marketing_spend": marketing, "ab_test_assignments": ab,
              "reviews_nps": reviews}
    tables, manifest = dirty_data.inject_defects(tables)
    dirty_data.write_manifest(manifest,
                              settings.PROJECT_ROOT / "docs" / "dirty_data_manifest.md")

    tables["web_sessions"] = tables["web_sessions"].drop(columns=["_stage", "_order_id"])
    tables["products"] = tables["products"].drop(columns=["_popularity"])

    raw_dir = settings.PROJECT_ROOT / "data" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    engine = get_engine()
    for name, df in tables.items():
        df.to_csv(raw_dir / f"{name}.csv", index=False)
        n = load_dataframe(df, f"bronze_{name}", engine)
        print(f"  {name:<22} {n:>9,} rows -> bronze_{name}")
    print(f"Done in {time.time() - t0:,.0f}s")


if __name__ == "__main__":
    main()
