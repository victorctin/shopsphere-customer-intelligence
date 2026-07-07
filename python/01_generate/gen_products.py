"""Generate the products catalog."""
import numpy as np
import pandas as pd

from config import settings
from _common import fake, rng

# category: (min_price, max_price, assortment_share)
CATEGORIES = {
    "Electronics":             (30, 400, 0.12),
    "Computers & Accessories": (20, 500, 0.08),
    "Home & Living":           (15, 250, 0.18),
    "Kitchen":                 (12, 200, 0.15),
    "Sports & Outdoors":       (18, 300, 0.12),
    "Beauty & Personal Care":  (8,  90,  0.15),
    "Toys & Games":            (10, 120, 0.12),
    "Office Supplies":         (5,  80,  0.08),
}


def generate_products() -> pd.DataFrame:
    n = settings.N_PRODUCTS
    r = rng()
    f = fake()
    names = list(CATEGORIES)
    cats = r.choice(names, n, p=[CATEGORIES[c][2] for c in names])
    lo = np.array([CATEGORIES[c][0] for c in cats], float)
    hi = np.array([CATEGORIES[c][1] for c in cats], float)
    price = np.exp(r.uniform(np.log(lo), np.log(hi)))  # log-uniform in range
    launch_lo = pd.Timestamp("2023-01-01").value
    launch_hi = (pd.Timestamp(settings.DATA_END) - pd.Timedelta(days=90)).value
    launch = pd.to_datetime(r.uniform(launch_lo, launch_hi, n).astype("int64"))
    words = [f.word() for _ in range(n)]
    return pd.DataFrame({
        "product_id": [f"P{10000 + i}" for i in range(n)],
        "product_name": [f.catch_phrase()[:60] for _ in range(n)],
        "category": cats,
        "subcategory": [f"{c} - {w.title()}" for c, w in zip(cats, words)],
        "unit_price": price.round(2),
        "unit_cost": (price * r.uniform(0.45, 0.70, n)).round(2),
        "launch_date": launch.date,
        "_popularity": r.pareto(1.5, n) + 1.0,
    })
