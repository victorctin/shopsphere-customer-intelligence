"""Generate the customers table (one row per customer)."""
import numpy as np
import pandas as pd

from config import settings
from _common import fake, rng, weighted_day_sample

COUNTRIES = ["United Kingdom", "Germany", "France", "Romania",
             "Netherlands", "Spain", "Italy", "United States"]
COUNTRY_P = [0.22, 0.16, 0.13, 0.12, 0.10, 0.10, 0.09, 0.08]


def generate_customers() -> pd.DataFrame:
    n = settings.N_CUSTOMERS
    r = rng()
    f = fake()
    return pd.DataFrame({
        "customer_id": [f"C{100000 + i}" for i in range(n)],
        "signup_date": weighted_day_sample(n).dt.date.values,
        "acquisition_channel": r.choice(list(settings.ACQUISITION_MIX), n,
                                        p=list(settings.ACQUISITION_MIX.values())),
        "country": r.choice(COUNTRIES, n, p=COUNTRY_P),
        "city": [f.city() for _ in range(n)],
        "birth_year": np.clip(r.normal(1988, 12, n).astype(int), 1955, 2007),
        "gender": r.choice(["F", "M", "Other"], n, p=[0.48, 0.48, 0.04]),
        "email": [f.unique.email() for _ in range(n)],
        "marketing_opt_in": (r.random(n) < 0.62).astype(int),
    })
