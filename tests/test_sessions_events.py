import numpy as np
import pandas as pd
import pytest


@pytest.fixture(scope="module")
def data():
    import _common
    _common.reset_rng()
    import gen_customers, gen_products, gen_orders, gen_sessions_events
    customers = gen_customers.generate_customers()
    products = gen_products.generate_products()
    orders, _ = gen_orders.generate_orders(customers, products)
    sessions, events = gen_sessions_events.generate_sessions_events(customers, orders)
    return orders, sessions, events


def test_session_count_and_conversion(data):
    from config import settings
    orders, sessions, _ = data
    assert len(sessions) == settings.N_SESSIONS
    conv = (sessions["_stage"] == "purchase").mean()
    assert 0.020 <= conv <= 0.029


def test_every_order_has_a_converting_session(data):
    orders, sessions, _ = data
    purch = sessions.loc[sessions["_stage"] == "purchase", "_order_id"]
    assert set(purch) == set(orders["order_id"])


def test_funnel_monotonic_and_abandonment(data):
    _, _, events = data
    c = events["event_type"].value_counts()
    assert c["page_view"] >= c["product_view"] >= c["add_to_cart"] \
           >= c["begin_checkout"] >= c["purchase"]
    abandon = 1 - c["purchase"] / c["add_to_cart"]
    assert 0.62 <= abandon <= 0.78


def test_events_reference_sessions_and_types(data):
    _, sessions, events = data
    assert set(events["event_type"]) == {
        "page_view", "product_view", "add_to_cart", "begin_checkout", "purchase"}
    assert events["session_id"].isin(sessions["session_id"]).all()
