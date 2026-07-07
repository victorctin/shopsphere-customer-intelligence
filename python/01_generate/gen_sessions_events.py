"""Generate web sessions + funnel events. One converting session per order,
plus anonymous/known non-converting traffic to reach N_SESSIONS."""
import numpy as np
import pandas as pd

from config import settings
from _common import rng, weighted_day_sample

TRAFFIC_CONV = {"organic": 0.24, "paid_search": 0.20, "email": 0.18, "direct": 0.15,
                "paid_social": 0.10, "affiliate": 0.07, "display": 0.06}
TRAFFIC_NONCONV = {"organic": 0.22, "paid_search": 0.18, "email": 0.08, "direct": 0.14,
                   "paid_social": 0.20, "affiliate": 0.05, "display": 0.13}
DEVICES = ["mobile", "desktop", "tablet"]
LANDING = ["/", "/sale", "/category/electronics", "/category/home-living",
           "/category/beauty", "/product"]
LANDING_P = [0.30, 0.15, 0.15, 0.15, 0.10, 0.15]
PAID = {"paid_search", "paid_social", "display", "affiliate", "email"}

_h = np.ones(24)
_h[[12, 13, 18, 19, 20, 21, 22]] = 2.5
_h[1:6] = 0.3
HOUR_P = _h / _h.sum()


def generate_sessions_events(customers: pd.DataFrame, orders: pd.DataFrame):
    r = rng()
    n_conv = len(orders)
    n_non = settings.N_SESSIONS - n_conv

    # ---- converting sessions (one per order) --------------------------------
    conv_start = (pd.to_datetime(orders["order_ts"])
                  - pd.to_timedelta(r.integers(25, 45, n_conv), unit="m"))
    conv = pd.DataFrame({
        "customer_id": orders["customer_id"].values,
        "session_start_ts": conv_start.values,
        "device_type": r.choice(DEVICES, n_conv, p=[0.48, 0.42, 0.10]),
        "traffic_source": r.choice(list(TRAFFIC_CONV), n_conv,
                                   p=list(TRAFFIC_CONV.values())),
        "_stage": "purchase",
        "_order_id": orders["order_id"].values,
    })

    # ---- non-converting sessions --------------------------------------------
    p_pv = settings.P_PRODUCT_VIEW
    p_cart = p_pv * settings.P_CART_GIVEN_VIEW
    p_co = p_cart * settings.P_CHECKOUT_GIVEN_CART
    p_buy = p_co * settings.P_BUY_GIVEN_CHECKOUT
    shares = np.array([1 - p_pv, p_pv - p_cart, p_cart - p_co, p_co - p_buy])
    shares = shares / (1 - p_buy)
    stages = r.choice(["bounce", "product_view", "add_to_cart", "begin_checkout"],
                      n_non, p=shares)
    non_start = (weighted_day_sample(n_non)
                 + pd.to_timedelta(r.choice(24, n_non, p=HOUR_P), unit="h")
                 + pd.to_timedelta(r.integers(0, 60, n_non), unit="m"))
    known = r.random(n_non) < 0.25
    cust = np.where(known, r.choice(customers["customer_id"].values, n_non), None)
    non = pd.DataFrame({
        "customer_id": cust,
        "session_start_ts": non_start.values,
        "device_type": r.choice(DEVICES, n_non, p=[0.58, 0.32, 0.10]),
        "traffic_source": r.choice(list(TRAFFIC_NONCONV), n_non,
                                   p=list(TRAFFIC_NONCONV.values())),
        "_stage": stages,
        "_order_id": None,
    })

    sessions = pd.concat([conv, non], ignore_index=True)
    n = len(sessions)
    sessions.insert(0, "session_id", [f"S{5000000 + i}" for i in range(n)])
    sessions["landing_page"] = r.choice(LANDING, n, p=LANDING_P)
    month = pd.to_datetime(sessions["session_start_ts"]).dt.strftime("%Y%m")
    is_paid = sessions["traffic_source"].isin(PAID)
    sessions["campaign_id"] = np.where(
        is_paid,
        "CMP-" + sessions["traffic_source"].str[:4].str.upper() + "-" + month,
        None)

    # ---- events ---------------------------------------------------------------
    STAGE_RANK = {"bounce": 0, "product_view": 1, "add_to_cart": 2,
                  "begin_checkout": 3, "purchase": 4}
    rank = sessions["_stage"].map(STAGE_RANK).values
    start = pd.to_datetime(sessions["session_start_ts"])
    frames = []
    for evt, minrank, offset in [("page_view", 0, 0), ("product_view", 1, 2),
                                 ("add_to_cart", 2, 6), ("begin_checkout", 3, 12),
                                 ("purchase", 4, 18)]:
        m = rank >= minrank
        k = int(m.sum())
        sub = pd.DataFrame({
            "session_id": sessions.loc[m, "session_id"].values,
            "event_type": evt,
            "event_ts": (start[m] + pd.to_timedelta(
                offset + r.integers(0, 4, k), unit="m")).values,
            "product_id": None,
            "order_id": sessions.loc[m, "_order_id"].values if evt == "purchase" else None,
        })
        frames.append(sub)
    events = pd.concat(frames, ignore_index=True)
    events = events.sort_values(["session_id", "event_ts"], kind="stable",
                                ignore_index=True)
    events.insert(0, "event_id", [f"E{10000000 + i}" for i in range(len(events))])
    return sessions, events
