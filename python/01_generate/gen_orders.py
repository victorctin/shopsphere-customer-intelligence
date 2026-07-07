"""Generate orders + order_items driven by the repeat-purchase ladder."""
import numpy as np
import pandas as pd

from config import settings
from _common import all_days, growth_trend, rng, season_multiplier

PAYMENT_METHODS = ["card", "paypal", "apple_pay", "google_pay", "bank_transfer"]
PAYMENT_P = [0.55, 0.20, 0.10, 0.08, 0.07]
ITEM_COUNT = [1, 2, 3, 4]
ITEM_COUNT_P = [0.60, 0.25, 0.10, 0.05]
QTY = [1, 2, 3]
QTY_P = [0.90, 0.08, 0.02]

_h = np.ones(24)
_h[[19, 20, 21]] = 3.0
_h[[12, 13, 18, 22]] = 2.0
_h[2:6] = 0.3
HOUR_P = _h / _h.sum()


def _order_counts(r, n: int) -> np.ndarray:
    """Markov ladder: P(next order | k orders) from settings.REPEAT_LADDER."""
    counts = np.ones(n, dtype=int)
    active = np.ones(n, dtype=bool)
    for k in range(1, settings.MAX_ORDERS_PER_CUSTOMER):
        p = settings.REPEAT_LADDER.get(k, settings.REPEAT_LADDER_DEFAULT)
        active &= r.random(n) < p
        counts += active
    return counts


def generate_orders(customers: pd.DataFrame, products: pd.DataFrame):
    r = rng()
    days = all_days()
    day_w = season_multiplier(days) * growth_trend(days)
    day_vals = days.values

    n_cust = len(customers)
    counts = _order_counts(r, n_cust)
    lifetime = r.exponential(settings.CUSTOMER_LIFETIME_DAYS_MEAN, n_cust)
    signup = pd.to_datetime(customers["signup_date"]).values
    end = np.datetime64(settings.DATA_END)

    cust_pos, date_list = [], []
    for i in range(n_cust):
        lo = int(np.searchsorted(day_vals, signup[i]))
        window_end = min(signup[i] + np.timedelta64(int(lifetime[i]), "D"), end)
        hi = int(np.searchsorted(day_vals, window_end, side="right"))
        hi = max(hi, lo + 1)
        w = day_w[lo:hi]
        picks = np.sort(r.choice(np.arange(lo, hi), size=counts[i], p=w / w.sum()))
        cust_pos.extend([i] * counts[i])
        date_list.append(day_vals[picks])

    order_dates = np.concatenate(date_list)
    cust_pos = np.array(cust_pos)
    n_orders = len(order_dates)

    ts = (pd.to_datetime(order_dates)
          + pd.to_timedelta(r.choice(24, n_orders, p=HOUR_P), unit="h")
          + pd.to_timedelta(r.integers(0, 60, n_orders), unit="m"))

    cust_ids = customers["customer_id"].values[cust_pos]
    countries = customers["country"].values[cust_pos]
    ship = np.where(r.random(n_orders) < 0.90, countries,
                    r.choice(customers["country"].unique(), n_orders))

    orders = pd.DataFrame({
        "order_id": [f"O{1000000 + i}" for i in range(n_orders)],
        "customer_id": cust_ids,
        "order_ts": ts,
        "order_status": r.choice(list(settings.ORDER_STATUS_PROBS), n_orders,
                                 p=list(settings.ORDER_STATUS_PROBS.values())),
        "payment_method": r.choice(PAYMENT_METHODS, n_orders, p=PAYMENT_P),
        "shipping_country": ship,
    })

    # ---- items -------------------------------------------------------------
    sizes = r.choice(ITEM_COUNT, n_orders, p=ITEM_COUNT_P)
    order_rep = np.repeat(np.arange(n_orders), sizes)
    n_items = len(order_rep)
    # Demand is price-elastic: raw popularity alone yields AOV ~140-175,
    # far above the 78-108 calibration band; /price^0.7 centers AOV near 95.
    pop = products["_popularity"].values / products["unit_price"].values ** 0.7
    prod_pos = r.choice(len(products), n_items, p=pop / pop.sum())
    qty = r.choice(QTY, n_items, p=QTY_P)
    price = (products["unit_price"].values[prod_pos]
             * r.uniform(0.95, 1.05, n_items)).round(2)
    line_disc = np.where(r.random(n_items) < 0.10, (price * qty * 0.10).round(2), 0.0)

    items = pd.DataFrame({
        "order_item_id": [f"OI{2000000 + i}" for i in range(n_items)],
        "order_id": orders["order_id"].values[order_rep],
        "product_id": products["product_id"].values[prod_pos],
        "quantity": qty,
        "unit_price_at_sale": price,
        "line_discount": line_disc,
    })

    subtotal = (pd.Series(price * qty - line_disc)
                .groupby(order_rep).sum().reindex(range(n_orders), fill_value=0).values)
    orders["discount_amount"] = np.minimum(
        np.where(r.random(n_orders) < 0.20, r.uniform(5, 20, n_orders), 0.0),
        0.5 * subtotal).round(2)
    orders["shipping_fee"] = np.where(subtotal >= 75, 0.0, 4.99)
    return orders, items
