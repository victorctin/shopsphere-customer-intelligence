import numpy as np
import pandas as pd


def _tiny_tables():
    n = 2000
    customers = pd.DataFrame({
        "customer_id": [f"C{i}" for i in range(n)],
        "signup_date": pd.date_range("2024-07-01", periods=n, freq="h").date,
        "country": ["United Kingdom"] * n,
        "email": [f"u{i}@x.com" for i in range(n)],
    })
    orders = pd.DataFrame({
        "order_id": [f"O{i}" for i in range(n)],
        "customer_id": [f"C{i}" for i in range(n)],
        "order_ts": pd.date_range("2025-01-01", periods=n, freq="h"),
    })
    items = pd.DataFrame({
        "order_item_id": [f"OI{i}" for i in range(n)],
        "order_id": [f"O{i}" for i in range(n)],
        "quantity": np.ones(n, int),
        "unit_price_at_sale": np.full(n, 20.0),
    })
    events = pd.DataFrame({
        "event_id": [f"E{i}" for i in range(4000)],
        "event_ts": pd.date_range("2025-01-01", periods=4000, freq="min"),
    })
    return {"customers": customers, "orders": orders,
            "order_items": items, "web_events": events}


def test_inject_defects_counts_match_manifest():
    import _common
    _common.reset_rng()
    from dirty_data import inject_defects
    tables, manifest = inject_defects(_tiny_tables())
    assert len(tables["orders"]) == 2000 + manifest["duplicate_orders"]
    assert tables["customers"]["email"].isna().sum() == manifest["missing_emails"]
    bad_qty = (tables["order_items"]["quantity"] <= 0).sum()
    assert bad_qty == manifest["bad_quantities"]
    assert manifest["fat_finger_prices"] == 15
    assert (tables["order_items"]["order_id"] == "O9999999").sum() \
           == manifest["orphan_order_items"]


def test_originals_not_mutated():
    import _common
    _common.reset_rng()
    from dirty_data import inject_defects
    originals = _tiny_tables()
    email_before = originals["customers"]["email"].copy()
    inject_defects(originals)
    pd.testing.assert_series_equal(originals["customers"]["email"], email_before)
