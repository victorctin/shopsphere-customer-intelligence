"""Central configuration: volumes, behavior targets, DB connection."""
from __future__ import annotations

import os
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

RANDOM_SEED = 42
DATA_START = date(2024, 7, 1)
DATA_END = date(2026, 6, 30)

# ---- volumes -------------------------------------------------------------
N_CUSTOMERS = 12_000
N_PRODUCTS = 500
N_SESSIONS = 800_000
N_AB_SESSIONS = 60_000     # total assignments (2 arms)
REVIEW_RATE = 0.25         # share of completed orders that get a review

# ---- retention behavior ---------------------------------------------------
# P(customer places another order | has placed k orders so far)
REPEAT_LADDER = {1: 0.31, 2: 0.45}
REPEAT_LADDER_DEFAULT = 0.55
MAX_ORDERS_PER_CUSTOMER = 12
CUSTOMER_LIFETIME_DAYS_MEAN = 330   # exponential lifetime → natural churn

# ---- funnel (conditional step probabilities) ------------------------------
P_PRODUCT_VIEW = 0.65          # of sessions
P_CART_GIVEN_VIEW = 0.128      # of product viewers
P_CHECKOUT_GIVEN_CART = 0.40   # of carts
P_BUY_GIVEN_CHECKOUT = 0.75    # of checkouts  → net ≈ 2.5% conversion

ORDER_STATUS_PROBS = {"completed": 0.92, "cancelled": 0.05, "returned": 0.03}

# ---- channels --------------------------------------------------------------
ACQUISITION_MIX = {
    "organic": 0.25, "paid_search": 0.22, "paid_social": 0.20,
    "display": 0.13, "email": 0.12, "affiliate": 0.08,
}
PAID_CHANNELS = ["paid_search", "paid_social", "display", "email", "affiliate"]
CHANNEL_CAC = {"paid_search": 70, "paid_social": 95, "display": 110, "email": 25, "affiliate": 45}
CHANNEL_CPC = {"paid_search": 1.2, "paid_social": 0.6, "display": 0.4, "email": 0.05, "affiliate": 0.3}
CHANNEL_CTR = {"paid_search": 0.04, "paid_social": 0.012, "display": 0.005, "email": 0.03, "affiliate": 0.02}

# ---- A/B test ---------------------------------------------------------------
AB_TEST_NAME = "free_shipping_threshold"
AB_START = date(2026, 2, 15)
AB_END = date(2026, 4, 30)
AB_TREATMENT_LIFT = 1.15   # relative conversion lift in treatment

# ---- database ---------------------------------------------------------------
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_NAME = os.getenv("DB_NAME", "shopsphere_dw")
DB_USER = os.getenv("DB_USER", "shopsphere_app")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")


def build_db_url() -> str:
    return (f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@"
            f"{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4")
