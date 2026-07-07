import pandas as pd
import pytest


@pytest.fixture(scope="module")
def data():
    import _common
    _common.reset_rng()
    import gen_customers, gen_products, gen_orders, gen_sessions_events
    import gen_ab_test, gen_reviews
    customers = gen_customers.generate_customers()
    products = gen_products.generate_products()
    orders, _ = gen_orders.generate_orders(customers, products)
    sessions, _ = gen_sessions_events.generate_sessions_events(customers, orders)
    ab = gen_ab_test.generate_ab_test(sessions)
    reviews = gen_reviews.generate_reviews(orders)
    return orders, ab, reviews


def test_ab_size_balance_and_lift(data):
    from config import settings
    _, ab, _ = data
    assert len(ab) == settings.N_AB_SESSIONS
    counts = ab["variant"].value_counts()
    assert counts["control"] == counts["treatment"]
    rates = ab.groupby("variant")["converted_flag"].mean()
    lift = rates["treatment"] / rates["control"] - 1
    assert 0.05 <= lift <= 0.30
    assert not ab["session_id"].duplicated().any()


def test_reviews_reference_completed_orders(data):
    orders, _, reviews = data
    completed = set(orders.loc[orders["order_status"] == "completed", "order_id"])
    assert set(reviews["order_id"]) <= completed
    assert reviews["star_rating"].between(1, 5).all()
    assert reviews["nps_score"].between(0, 10).all()


def test_review_volume_matches_rate(data):
    from config import settings
    orders, _, reviews = data
    n_completed = (orders["order_status"] == "completed").sum()
    assert abs(len(reviews) - settings.REVIEW_RATE * n_completed) <= 2
