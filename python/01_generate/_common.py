"""Shared seeded randomness + calendar weighting for all generators."""
from __future__ import annotations

import numpy as np
import pandas as pd
from faker import Faker

from config import settings

_rng: np.random.Generator | None = None


def rng() -> np.random.Generator:
    global _rng
    if _rng is None:
        _rng = np.random.default_rng(settings.RANDOM_SEED)
    return _rng


def reset_rng() -> None:
    global _rng
    _rng = None


def fake() -> Faker:
    f = Faker()
    Faker.seed(settings.RANDOM_SEED)
    return f


def all_days() -> pd.DatetimeIndex:
    return pd.date_range(settings.DATA_START, settings.DATA_END, freq="D")


def season_multiplier(days: pd.DatetimeIndex) -> np.ndarray:
    m = np.ones(len(days))
    month = days.month
    m[np.isin(month, [11, 12])] = 1.8   # holiday peak
    m[month == 1] = 0.75                # January slump
    m[np.isin(month, [7, 8])] = 0.9     # summer dip
    m = m * np.where(days.dayofweek >= 5, 0.85, 1.05)  # weekday > weekend
    return m


def growth_trend(days: pd.DatetimeIndex) -> np.ndarray:
    t = np.linspace(0.0, 1.0, len(days))
    return 1.0 + 0.5 * t   # store grows ~50% across the 24 months


def weighted_day_sample(n: int) -> pd.Series:
    days = all_days()
    w = season_multiplier(days) * growth_trend(days)
    idx = rng().choice(len(days), size=n, p=w / w.sum())
    return pd.Series(days[idx])
