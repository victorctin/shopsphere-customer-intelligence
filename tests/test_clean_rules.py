import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python" / "02_clean"))


def test_dedupe_orders_keeps_first():
    from clean_rules import dedupe_orders
    orders = pd.DataFrame({"order_id": ["O1", "O2", "O1"], "x": [1, 2, 3]})
    out, n = dedupe_orders(orders)
    assert n == 1
    assert list(out["order_id"]) == ["O1", "O2"]
    assert list(out["x"]) == [1, 2]


def test_flag_emails_missing_and_malformed():
    from clean_rules import flag_emails
    cust = pd.DataFrame({"email": ["ok@x.com", None, "bad_at_x.com"]})
    out, n_missing, n_malformed = flag_emails(cust)
    assert (n_missing, n_malformed) == (1, 1)
    assert list(out["email_valid"]) == [1, 0, 0]
    assert pd.isna(out.loc[2, "email"])          # malformed nulled
    assert out.loc[0, "email"] == "ok@x.com"     # valid untouched


def test_normalize_countries():
    from clean_rules import normalize_countries
    cust = pd.DataFrame({"country": ["  United Kingdom ", "germany", "FRANCE",
                                     "UK", "Spain"]})
    out, n = normalize_countries(cust)
    assert n == 4
    assert list(out["country"]) == ["United Kingdom", "Germany", "France",
                                    "United Kingdom", "Spain"]


def test_clean_items_quantities_prices_orphans():
    from clean_rules import clean_items
    items = pd.DataFrame({
        "order_item_id": [f"OI{i}" for i in range(8)],
        "order_id": ["O1", "O1", "O1", "O1", "O1", "O1", "O9", "O9"],
        "quantity": [1, 1, 1, 1, 1, -1, 1, 0],
        "unit_price_at_sale": [20.0, 20.4, 19.8, 20.2, 2000.0, 20.0, 20.0, 20.0],
        "product_id": ["P1"] * 8,
    })
    out, audit = clean_items(items, valid_order_ids={"O1"})
    assert audit["bad_quantities"] == 2          # rows 5 and 7
    assert audit["fat_finger_prices"] == 1       # row 4: 2000 -> 20
    assert audit["orphan_order_items"] == 2      # rows 6 and 7 (7 counted in both)
    assert out["unit_price_at_sale"].max() < 100
    assert (out["quantity"] > 0).all()
    assert (out["order_id"] == "O1").all()
    assert len(out) == 5


def test_clean_events_clamped_to_session_start():
    from clean_rules import clean_events
    sessions = pd.DataFrame({"session_id": ["S1"],
                             "session_start_ts": [pd.Timestamp("2025-01-01 10:00")]})
    events = pd.DataFrame({
        "event_id": ["E1", "E2"],
        "session_id": ["S1", "S1"],
        "event_ts": [pd.Timestamp("2025-01-01 08:00"),
                     pd.Timestamp("2025-01-01 10:05")],
    })
    out, n = clean_events(events, sessions)
    assert n == 1
    assert out.loc[0, "event_ts"] == pd.Timestamp("2025-01-01 10:00")
    assert out.loc[1, "event_ts"] == pd.Timestamp("2025-01-01 10:05")


def test_flag_ts_conflicts_orders_before_signup():
    from clean_rules import flag_ts_conflicts
    cust = pd.DataFrame({"customer_id": ["C1", "C2"],
                         "signup_date": [pd.Timestamp("2025-01-10").date(),
                                         pd.Timestamp("2025-01-10").date()]})
    orders = pd.DataFrame({
        "order_id": ["O1", "O2"],
        "customer_id": ["C1", "C2"],
        "order_ts": [pd.Timestamp("2025-01-05 12:00"),    # before signup
                     pd.Timestamp("2025-01-10 00:30")],   # signup day is fine
    })
    out, n = flag_ts_conflicts(orders, cust)
    assert n == 1
    assert list(out["ts_conflict"]) == [1, 0]


def test_clean_all_audit_keys_and_immutability():
    from clean_rules import clean_all, MANIFEST_KEYS
    cust = pd.DataFrame({
        "customer_id": ["C1", "C2"],
        "signup_date": [pd.Timestamp("2025-01-01").date()] * 2,
        "country": ["germany", "United Kingdom"],
        "email": ["ok@x.com", "bad_at_x.com"],
    })
    orders = pd.DataFrame({
        "order_id": ["O1", "O1", "O2"],
        "customer_id": ["C1", "C1", "C2"],
        "order_ts": pd.to_datetime(["2025-02-01 10:00"] * 2 + ["2024-12-25 09:00"]),
    })
    items = pd.DataFrame({
        "order_item_id": ["OI1", "OI2"],
        "order_id": ["O1", "O404"],
        "quantity": [1, 1],
        "unit_price_at_sale": [20.0, 20.0],
        "product_id": ["P1", "P1"],
    })
    sessions = pd.DataFrame({"session_id": ["S1"],
                             "session_start_ts": [pd.Timestamp("2025-02-01 09:40")]})
    events = pd.DataFrame({"event_id": ["E1"], "session_id": ["S1"],
                           "event_ts": [pd.Timestamp("2025-02-01 07:00")]})
    tables = {"customers": cust, "orders": orders, "order_items": items,
              "web_sessions": sessions, "web_events": events}
    email_before = cust["email"].copy()

    silver, audit = clean_all(tables)

    assert set(MANIFEST_KEYS) <= set(audit)
    assert audit["duplicate_orders"] == 1
    assert audit["malformed_emails"] == 1
    assert audit["messy_countries"] == 1
    assert audit["orphan_order_items"] == 1
    assert audit["events_before_session"] == 1
    assert audit["orders_before_signup"] == 1
    assert len(silver["orders"]) == 2
    pd.testing.assert_series_equal(cust["email"], email_before)  # no mutation
