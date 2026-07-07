import numpy as np
import pandas as pd
import pytest


def test_rng_reproducible():
    import _common
    _common.reset_rng()
    a = _common.rng().random(5)
    _common.reset_rng()
    b = _common.rng().random(5)
    assert np.allclose(a, b)


def test_season_multiplier_shape_and_peaks():
    import _common
    days = _common.all_days()
    m = _common.season_multiplier(days)
    assert len(m) == len(days)
    nov_dec = m[np.isin(days.month, [11, 12])].mean()
    jan = m[days.month == 1].mean()
    assert nov_dec > 1.5 * jan / 0.9  # Nov-Dec clearly above January


def test_weighted_day_sample_within_range():
    import _common
    from config import settings
    _common.reset_rng()
    s = _common.weighted_day_sample(10_000)
    assert s.min().date() >= settings.DATA_START
    assert s.max().date() <= settings.DATA_END


def test_load_dataframe_roundtrip_sqlite():
    from sqlalchemy import create_engine, text
    from utils.db_io import load_dataframe
    eng = create_engine("sqlite:///:memory:")
    with eng.begin() as c:
        c.execute(text("CREATE TABLE t (a INTEGER, b TEXT)"))
    df = pd.DataFrame({"a": [1, 2], "b": ["x", "y"]})
    n = load_dataframe(df, "t", eng, truncate=False)
    assert n == 2


@pytest.mark.parametrize("bad_name", [
    "t; DROP TABLE t", "t--", "t`", "bronze customers", "", "1t"])
def test_load_dataframe_rejects_invalid_table_name(bad_name):
    from sqlalchemy import create_engine
    from utils.db_io import load_dataframe
    eng = create_engine("sqlite:///:memory:")
    df = pd.DataFrame({"a": [1]})
    with pytest.raises(ValueError):
        load_dataframe(df, bad_name, eng)
