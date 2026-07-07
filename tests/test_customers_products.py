import pandas as pd
import pytest


@pytest.fixture(scope="module")
def data():
    import _common
    _common.reset_rng()
    import gen_customers, gen_products
    return gen_customers.generate_customers(), gen_products.generate_products()


def test_customers_shape_and_columns(data):
    from config import settings
    customers, _ = data
    assert len(customers) == settings.N_CUSTOMERS
    assert list(customers.columns) == [
        "customer_id", "signup_date", "acquisition_channel", "country", "city",
        "birth_year", "gender", "email", "marketing_opt_in"]
    assert customers["customer_id"].is_unique


def test_customers_domains(data):
    from config import settings
    customers, _ = data
    assert set(customers["acquisition_channel"]) <= set(settings.ACQUISITION_MIX)
    assert customers["signup_date"].min() >= settings.DATA_START
    assert customers["signup_date"].max() <= settings.DATA_END
    assert customers["email"].str.contains("@").all()


def test_products_shape_and_price_sanity(data):
    from config import settings
    _, products = data
    assert len(products) == settings.N_PRODUCTS
    assert products["product_id"].is_unique
    assert (products["unit_price"] > 0).all()
    assert (products["unit_cost"] < products["unit_price"]).all()
    assert (products["_popularity"] > 0).all()
