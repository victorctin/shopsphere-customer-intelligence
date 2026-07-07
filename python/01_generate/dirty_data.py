"""Inject known data-quality defects and record them in a manifest so the
Phase 2 cleaning results can be verified against ground truth."""
from pathlib import Path

import numpy as np
import pandas as pd

from _common import rng

UK_VARIANTS = {"United Kingdom": "UK"}


def inject_defects(tables: dict) -> tuple[dict, dict]:
    r = rng()
    t = {k: v.copy() for k, v in tables.items()}
    manifest: dict[str, int] = {}
    cust, items, events = t["customers"], t["order_items"], t["web_events"]

    # 1. duplicate order rows (double-loaded)
    n_dup = int(len(t["orders"]) * 0.015)
    t["orders"] = pd.concat(
        [t["orders"], t["orders"].sample(n=n_dup, random_state=1)],
        ignore_index=True)
    manifest["duplicate_orders"] = n_dup

    # 2. missing + malformed emails
    miss = cust.sample(frac=0.02, random_state=2).index
    cust.loc[miss, "email"] = None
    bad = cust.drop(index=miss).sample(frac=0.01, random_state=3).index
    cust.loc[bad, "email"] = cust.loc[bad, "email"].str.replace("@", "_at_", regex=False)
    manifest["missing_emails"] = len(miss)
    manifest["malformed_emails"] = len(bad)

    # 3. messy country strings
    mess = cust.sample(frac=0.04, random_state=4).index
    variants = []
    for c in cust.loc[mess, "country"]:
        variants.append(r.choice([c.lower(), c.upper(), f"  {c} ",
                                  UK_VARIANTS.get(c, c.lower())]))
    cust.loc[mess, "country"] = variants
    manifest["messy_countries"] = len(mess)

    # 4. zero/negative quantities
    q = items.sample(frac=0.005, random_state=5).index
    items.loc[q, "quantity"] = r.choice([0, -1, -2], len(q))
    manifest["bad_quantities"] = len(q)

    # 5. fat-finger prices (x100)
    fp = items.drop(index=q).sample(n=15, random_state=6).index
    items.loc[fp, "unit_price_at_sale"] = items.loc[fp, "unit_price_at_sale"] * 100
    manifest["fat_finger_prices"] = 15

    # 6. events timestamped before their session started
    ev = events.sample(n=min(2000, len(events)), random_state=7).index
    events.loc[ev, "event_ts"] = (pd.to_datetime(events.loc[ev, "event_ts"])
                                  - pd.Timedelta(hours=2))
    manifest["events_before_session"] = len(ev)

    # 7. orders timestamped before customer signup
    ob = t["orders"].sample(n=min(100, len(t["orders"])), random_state=8).index
    signup = cust.set_index("customer_id")["signup_date"]
    mapped = t["orders"].loc[ob, "customer_id"].map(signup)
    t["orders"].loc[ob, "order_ts"] = (
        pd.to_datetime(mapped.values)
        - pd.to_timedelta(r.integers(1, 30, len(ob)), unit="D"))
    manifest["orders_before_signup"] = len(ob)

    # 8. orphan order_items
    orph = items.sample(frac=0.002, random_state=9).index
    items.loc[orph, "order_id"] = "O9999999"
    manifest["orphan_order_items"] = len(orph)

    return t, manifest


def write_manifest(manifest: dict, path) -> None:
    lines = ["# Dirty Data Manifest (ground truth for Phase 2 cleaning)", "",
             "| Defect | Rows |", "|---|---|"]
    lines += [f"| {k} | {v} |" for k, v in manifest.items()]
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")
