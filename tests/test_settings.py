from datetime import date

import pytest


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


def test_db_url_shape(monkeypatch):
    from config import settings
    monkeypatch.setattr(settings, "DB_PASSWORD", "s3cret")
    url = settings.build_db_url()
    assert url.drivername == "mysql+pymysql"
    assert url.database == "shopsphere_dw"
    assert url.query["charset"] == "utf8mb4"


def test_db_url_handles_special_chars_and_masks_password(monkeypatch):
    from config import settings
    monkeypatch.setattr(settings, "DB_PASSWORD", "p@ss:w/rd#1")
    url = settings.build_db_url()
    assert url.password == "p@ss:w/rd#1"          # preserved, not mangled
    assert "p@ss:w/rd#1" not in repr(url)          # masked in repr/logs
    rendered = url.render_as_string(hide_password=False)
    assert "p%40ss%3Aw%2Frd%231" in rendered       # URL-escaped when rendered


def test_db_url_requires_password(monkeypatch):
    from config import settings
    monkeypatch.setattr(settings, "DB_PASSWORD", "")
    with pytest.raises(RuntimeError, match="DB_PASSWORD"):
        settings.build_db_url()
