import numpy as np
import pandas as pd
import pytest


@pytest.fixture(scope="module")
def data():
    import _common
    _common.reset_rng()
    import gen_customers, gen_products, gen_orders
    customers = gen_customers.generate_customers()
    products = gen_products.generate_products()
    orders, items = gen_orders.generate_orders(customers, products)
    return customers, products, orders, items


def test_repeat_ladder_produces_target_one_time_share(data):
    _, _, orders, _ = data
    per_cust = orders.groupby("customer_id").size()
    one_time = (per_cust == 1).mean()
    assert 0.66 <= one_time <= 0.72


def test_orders_after_signup_and_in_range(data):
    from config import settings
    customers, _, orders, _ = data
    signup = customers.set_index("customer_id")["signup_date"]
    order_dates = pd.to_datetime(orders["order_ts"]).dt.date
    cust_signup = orders["customer_id"].map(signup)
    assert (order_dates >= cust_signup).all()
    assert order_dates.max() <= settings.DATA_END


def test_statuses_and_referential_integrity(data):
    from config import settings
    customers, products, orders, items = data
    assert set(orders["order_status"]) <= set(settings.ORDER_STATUS_PROBS)
    assert items["order_id"].isin(orders["order_id"]).all()
    assert items["product_id"].isin(products["product_id"]).all()
    assert orders["order_id"].is_unique


def test_aov_in_realistic_band(data):
    _, _, orders, items = data
    rev = items["quantity"] * items["unit_price_at_sale"] - items["line_discount"]
    order_rev = rev.groupby(items["order_id"]).sum()
    completed = orders.loc[orders["order_status"] == "completed", "order_id"]
    aov = order_rev.reindex(completed).dropna().mean()
    assert 70 <= aov <= 115
