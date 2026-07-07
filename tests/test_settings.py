from datetime import date


def test_core_constants():
    from config import settings
    assert settings.RANDOM_SEED == 42
    assert settings.DATA_START == date(2024, 7, 1)
    assert settings.DATA_END == date(2026, 6, 30)
    assert settings.N_CUSTOMERS == 12_000
    assert settings.N_SESSIONS == 800_000
    assert abs(sum(settings.ACQUISITION_MIX.values()) - 1.0) < 1e-9


def test_funnel_math_hits_conversion_target():
    from config import settings
    conv = (settings.P_PRODUCT_VIEW * settings.P_CART_GIVEN_VIEW
            * settings.P_CHECKOUT_GIVEN_CART * settings.P_BUY_GIVEN_CHECKOUT)
    assert 0.023 <= conv <= 0.027


def test_db_url_shape():
    from config import settings
    url = settings.build_db_url()
    assert url.startswith("mysql+pymysql://")
    assert "shopsphere_dw" in url
