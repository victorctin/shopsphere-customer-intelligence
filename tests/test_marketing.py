import pandas as pd
import pytest


@pytest.fixture(scope="module")
def data():
    import _common
    _common.reset_rng()
    import gen_customers, gen_marketing
    customers = gen_customers.generate_customers()
    return customers, gen_marketing.generate_marketing(customers)


def test_grain_days_x_channels(data):
    from config import settings
    import _common
    _, mkt = data
    assert len(mkt) == len(_common.all_days()) * len(settings.PAID_CHANNELS)
    assert not mkt.duplicated(["spend_date", "channel"]).any()


def test_ctr_within_channel_bands(data):
    _, mkt = data
    ctr = mkt.groupby("channel").apply(
        lambda g: g["clicks"].sum() / g["impressions"].sum(), include_groups=False)
    assert ((ctr > 0.002) & (ctr < 0.08)).all()
    assert (mkt["impressions"] >= mkt["clicks"]).all()


def test_blended_cac_near_target(data):
    from config import settings
    customers, mkt = data
    paid_customers = customers["acquisition_channel"].isin(settings.PAID_CHANNELS).sum()
    cac = mkt["spend_amount"].sum() / paid_customers
    assert 55 <= cac <= 100
