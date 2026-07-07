"""Session-level A/B test with a real (small) treatment effect, built by
stratified sampling from the in-window traffic."""
import pandas as pd

from config import settings


def generate_ab_test(sessions: pd.DataFrame) -> pd.DataFrame:
    s = sessions.copy()
    s["_date"] = pd.to_datetime(s["session_start_ts"]).dt.date
    window = s[(s["_date"] >= settings.AB_START) & (s["_date"] <= settings.AB_END)]
    conv = window[window["_stage"] == "purchase"]
    nonc = window[window["_stage"] != "purchase"]

    n_arm = settings.N_AB_SESSIONS // 2
    p0 = len(conv) / len(window)
    n_conv_c = round(n_arm * p0)
    n_conv_t = round(n_arm * p0 * settings.AB_TREATMENT_LIFT)
    if n_conv_c + n_conv_t > len(conv):
        raise ValueError(
            f"Not enough converting sessions in AB window: need "
            f"{n_conv_c + n_conv_t}, have {len(conv)}. Widen AB window.")

    conv_pool = conv.sample(frac=1.0, random_state=settings.RANDOM_SEED)
    nonc_pool = nonc.sample(frac=1.0, random_state=settings.RANDOM_SEED)
    parts = [
        ("control", conv_pool.iloc[:n_conv_c],
         nonc_pool.iloc[:n_arm - n_conv_c]),
        ("treatment", conv_pool.iloc[n_conv_c:n_conv_c + n_conv_t],
         nonc_pool.iloc[n_arm - n_conv_c:(n_arm - n_conv_c) + (n_arm - n_conv_t)]),
    ]
    frames = []
    for variant, cdf, ndf in parts:
        d = pd.concat([cdf, ndf])
        frames.append(pd.DataFrame({
            "session_id": d["session_id"].values,
            "customer_id": d["customer_id"].values,
            "test_name": settings.AB_TEST_NAME,
            "variant": variant,
            "assigned_date": d["_date"].values,
            "converted_flag": (d["_stage"] == "purchase").astype(int).values,
            "order_id": d["_order_id"].values,
        }))
    out = pd.concat(frames, ignore_index=True)
    out.insert(0, "assignment_id", [f"AB{100000 + i}" for i in range(len(out))])
    return out
