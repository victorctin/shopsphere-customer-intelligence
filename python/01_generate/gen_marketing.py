"""Generate daily marketing spend per paid channel, reconciled to CAC targets."""
import numpy as np
import pandas as pd

from config import settings
from _common import all_days, rng


def generate_marketing(customers: pd.DataFrame) -> pd.DataFrame:
    r = rng()
    days = all_days()
    cust = customers.assign(signup=pd.to_datetime(customers["signup_date"]))
    frames = []
    for ch in settings.PAID_CHANNELS:
        daily = (cust[cust["acquisition_channel"] == ch]
                 .groupby("signup").size().reindex(days, fill_value=0))
        smooth = daily.rolling(7, min_periods=1).mean()
        spend = (smooth * settings.CHANNEL_CAC[ch]
                 * r.normal(1.0, 0.12, len(days))).clip(lower=15.0).round(2)
        clicks = np.maximum(
            (spend / settings.CHANNEL_CPC[ch] * r.uniform(0.85, 1.15, len(days)))
            .astype(int), 1)
        imps = np.maximum(
            (clicks / settings.CHANNEL_CTR[ch] * r.uniform(0.9, 1.1, len(days)))
            .astype(int), clicks)
        frames.append(pd.DataFrame({
            "spend_date": days.date, "channel": ch,
            "spend_amount": spend.values, "impressions": imps,
            "clicks": clicks, "attributed_signups": daily.values,
        }))
    return pd.concat(frames, ignore_index=True)
