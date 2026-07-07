"""Bronze -> silver cleaning rules. Every rule returns a new frame plus the
row count it affected, so the audit can be graded against the injection
manifest. Detection masks are computed on the input frame (before any drops)
to match how defects were injected independently of each other."""
import re

import pandas as pd

MANIFEST_KEYS = ["duplicate_orders", "missing_emails", "malformed_emails",
                 "messy_countries", "bad_quantities", "fat_finger_prices",
                 "events_before_session", "orders_before_signup",
                 "orphan_order_items"]

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_COUNTRY_MAP = {"UK": "United Kingdom"}
_FAT_FINGER_FACTOR = 10  # legit within-product price spread is ~1.1x


def dedupe_orders(orders: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    dup = orders.duplicated("order_id")
    return orders[~dup].reset_index(drop=True), int(dup.sum())


def flag_emails(customers: pd.DataFrame) -> tuple[pd.DataFrame, int, int]:
    c = customers.copy()
    missing = c["email"].isna()
    malformed = ~missing & ~c["email"].astype("string").str.match(_EMAIL_RE.pattern).fillna(False)
    c["email_valid"] = (~(missing | malformed)).astype(int)
    c.loc[malformed, "email"] = None
    return c, int(missing.sum()), int(malformed.sum())


def normalize_countries(customers: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    c = customers.copy()

    def canon(v: str) -> str:
        v = " ".join(str(v).split())
        return _COUNTRY_MAP.get(v.upper(), v.title())

    fixed = c["country"].map(canon)
    n = int((fixed != c["country"]).sum())
    c["country"] = fixed
    return c, n


def clean_items(items: pd.DataFrame, valid_order_ids: set) -> tuple[pd.DataFrame, dict]:
    i = items.copy()
    bad_qty = i["quantity"] <= 0
    orphan = ~i["order_id"].isin(valid_order_ids)
    median = i.groupby("product_id")["unit_price_at_sale"].transform("median")
    fat = i["unit_price_at_sale"] > _FAT_FINGER_FACTOR * median

    i.loc[fat, "unit_price_at_sale"] = (i.loc[fat, "unit_price_at_sale"] / 100).round(2)
    out = i[~(bad_qty | orphan)].reset_index(drop=True)
    audit = {"bad_quantities": int(bad_qty.sum()),
             "fat_finger_prices": int(fat.sum()),
             "orphan_order_items": int(orphan.sum())}
    return out, audit


def clean_events(events: pd.DataFrame, sessions: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    e = events.copy()
    start = e["session_id"].map(
        sessions.set_index("session_id")["session_start_ts"])
    early = pd.to_datetime(e["event_ts"]) < pd.to_datetime(start)
    e.loc[early, "event_ts"] = start[early]
    return e, int(early.sum())


def flag_ts_conflicts(orders: pd.DataFrame, customers: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    o = orders.copy()
    signup = o["customer_id"].map(customers.set_index("customer_id")["signup_date"])
    conflict = pd.to_datetime(o["order_ts"]) < pd.to_datetime(signup)
    o["ts_conflict"] = conflict.astype(int)
    return o, int(conflict.sum())


def clean_all(tables: dict) -> tuple[dict, dict]:
    silver = {k: v.copy() for k, v in tables.items()}
    audit: dict[str, int] = {}

    # detect timestamp conflicts on the raw (pre-dedupe) orders so the count
    # matches the injected rows even when a flagged duplicate gets dropped
    orders, audit["orders_before_signup"] = flag_ts_conflicts(
        silver["orders"], silver["customers"])
    orders, audit["duplicate_orders"] = dedupe_orders(orders)
    silver["orders"] = orders

    cust, audit["missing_emails"], audit["malformed_emails"] = flag_emails(
        silver["customers"])
    cust, audit["messy_countries"] = normalize_countries(cust)
    silver["customers"] = cust

    silver["order_items"], item_audit = clean_items(
        silver["order_items"], set(orders["order_id"]))
    audit.update(item_audit)

    silver["web_events"], audit["events_before_session"] = clean_events(
        silver["web_events"], silver["web_sessions"])
    return silver, audit
