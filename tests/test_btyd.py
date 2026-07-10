"""Tests for python/04_model/btyd.py — likelihood correctness, parameter
recovery from seeded simulations, and boundary validation."""
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python" / "04_model"))

import btyd

PARAMS_TRUE = {"r": 0.5, "alpha": 6.0, "a": 0.8, "b": 2.5}


def simulate_bgnbd(rng, n, r, alpha, a, b, T):
    lam = rng.gamma(r, 1.0 / alpha, size=n)
    p = rng.beta(a, b, size=n)
    x = np.zeros(n)
    t_x = np.zeros(n)
    for i in range(n):
        t = 0.0
        while True:
            t += rng.exponential(1.0 / lam[i]) if lam[i] > 0 else np.inf
            if t > T:
                break
            x[i] += 1
            t_x[i] = t
            if rng.random() < p[i]:
                break
    return x, t_x, np.full(n, float(T))


def test_bgnbd_loglik_zero_freq_closed_form():
    # x=0: L = A2 * alpha^r / (alpha+T)^r with A2 = 1 (beta terms cancel)
    r, alpha, a, b = 0.7, 5.0, 0.9, 2.0
    ll = btyd.bgnbd_loglik((r, alpha, a, b), [0.0], [0.0], [10.0])
    expected = r * np.log(alpha) - r * np.log(alpha + 10.0)
    assert np.isclose(ll[0], expected)


def test_bgnbd_param_recovery():
    rng = np.random.default_rng(42)
    x, t_x, T = simulate_bgnbd(rng, 4000, T=52.0, **PARAMS_TRUE)
    fitted = btyd.fit_bgnbd(x, t_x, T)
    for k, true in PARAMS_TRUE.items():
        assert abs(fitted[k] - true) / true < 0.25, (k, fitted[k], true)


def test_p_alive_bounds_and_monotonicity():
    params = PARAMS_TRUE
    p = btyd.bgnbd_p_alive(params, [0, 3, 3], [0, 50, 10], [52, 52, 52])
    assert ((p > 0) & (p <= 1)).all()
    assert p[0] == 1.0  # x=0 carries no dropout evidence in BG/NBD
    assert p[1] > p[2]  # more recent last purchase => more likely alive


def test_expected_purchases_positive_and_increasing_in_horizon():
    params = PARAMS_TRUE
    e13 = btyd.bgnbd_expected_purchases(params, [2.0], [40.0], [52.0], 13.0)
    e52 = btyd.bgnbd_expected_purchases(params, [2.0], [40.0], [52.0], 52.0)
    assert 0 < e13[0] < e52[0]


def test_bgnbd_input_validation():
    with pytest.raises(ValueError):
        btyd.bgnbd_loglik((1, 1, 1, 1), [1.0], [5.0], [4.0])  # t_x > T
    with pytest.raises(ValueError):
        btyd.bgnbd_loglik((1, 1, 1, 1), [0.0], [2.0], [4.0])  # x=0, t_x>0
    with pytest.raises(ValueError):
        btyd.fit_bgnbd([-1.0], [0.0], [4.0])  # negative count


def test_gg_param_recovery():
    rng = np.random.default_rng(7)
    p, q, g = 6.0, 4.0, 15.0
    n = 4000
    x = rng.integers(1, 8, size=n).astype(float)
    nu = rng.gamma(q, 1.0 / g, size=n)
    m_x = np.array([rng.gamma(p * xi, 1.0 / (nu_i * xi))
                    for xi, nu_i in zip(x, nu)])
    fitted = btyd.fit_gg(x, m_x)
    for k, true in zip(("p", "q", "gamma"), (p, q, g)):
        assert abs(fitted[k] - true) / true < 0.25, (k, fitted[k], true)


def test_gg_expected_value_shrinks_toward_prior():
    params = {"p": 6.0, "q": 4.0, "gamma": 15.0}
    prior_mean = params["p"] * params["gamma"] / (params["q"] - 1)
    m_lo, m_hi = prior_mean * 0.25, prior_mean * 4.0
    e = btyd.gg_expected_value(params, [1.0, 1.0], [m_lo, m_hi])
    assert m_lo < e[0] < prior_mean  # pulled up toward prior
    assert prior_mean < e[1] < m_hi  # pulled down toward prior
    # more observations => less shrinkage
    e1 = btyd.gg_expected_value(params, [1.0], [m_hi])
    e9 = btyd.gg_expected_value(params, [9.0], [m_hi])
    assert abs(e9[0] - m_hi) < abs(e1[0] - m_hi)


def test_gg_input_validation():
    with pytest.raises(ValueError):
        btyd.gg_loglik((1, 1, 1), [0.0], [10.0])  # x must be >= 1
    with pytest.raises(ValueError):
        btyd.fit_gg([2.0], [0.0])  # non-positive value
