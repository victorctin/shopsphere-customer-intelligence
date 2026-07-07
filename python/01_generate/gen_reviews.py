"""Reviews + NPS for a sample of completed orders. Loyal repeat customers
skew positive — satisfaction correlates with retention."""
import numpy as np
import pandas as pd

from config import settings
from _common import rng

STAR_BASE = [0.06, 0.07, 0.15, 0.32, 0.40]
STAR_LOYAL = [0.02, 0.04, 0.10, 0.34, 0.50]
NPS_LO = {1: 0, 2: 3, 3: 6, 4: 8, 5: 9}
NPS_HI = {1: 4, 2: 6, 3: 8, 4: 9, 5: 10}


def generate_reviews(orders: pd.DataFrame) -> pd.DataFrame:
    r = rng()
    completed = orders[orders["order_status"] == "completed"]
    n = int(len(completed) * settings.REVIEW_RATE)
    sample = completed.sample(n=n, random_state=settings.RANDOM_SEED)

    orders_per_cust = orders.groupby("customer_id").size()
    loyal = sample["customer_id"].map(orders_per_cust).values >= 3
    stars = np.where(loyal,
                     r.choice([1, 2, 3, 4, 5], n, p=STAR_LOYAL),
                     r.choice([1, 2, 3, 4, 5], n, p=STAR_BASE))
    nps = np.array([r.integers(NPS_LO[s], NPS_HI[s] + 1) for s in stars])

    return pd.DataFrame({
        "review_id": [f"R{300000 + i}" for i in range(n)],
        "customer_id": sample["customer_id"].values,
        "order_id": sample["order_id"].values,
        "review_ts": (pd.to_datetime(sample["order_ts"])
                      + pd.to_timedelta(r.integers(3, 21, n), unit="D")).values,
        "star_rating": stars,
        "nps_score": nps,
        "review_channel": r.choice(["email_survey", "onsite", "app"], n,
                                   p=[0.6, 0.3, 0.1]),
    })
