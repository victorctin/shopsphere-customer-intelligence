"""BG/NBD and Gamma-Gamma models (Fader-Hardie), implemented directly on
numpy/scipy. Inputs follow the standard BTYD summary format per customer:
  x   - number of REPEAT transactions in (0, T]
  t_x - recency: time of last repeat transaction (0 when x == 0)
  T   - total observation time since first transaction
  m_x - mean transaction value across the customer's x transactions (x >= 1)
Time units are whatever the caller uses consistently (weeks recommended).
References: Fader, Hardie & Lee (2005) "Counting Your Customers the Easy Way";
Fader & Hardie (2013) "The Gamma-Gamma Model of Monetary Value".
"""
import numpy as np
from scipy.optimize import minimize
from scipy.special import gammaln, hyp2f1


def _validate_bgnbd(x, t_x, T):
    x, t_x, T = (np.asarray(a, dtype=float) for a in (x, t_x, T))
    if not (x.shape == t_x.shape == T.shape):
        raise ValueError("x, t_x, T must have identical shapes")
    if (x < 0).any():
        raise ValueError("x must be >= 0")
    if (t_x < 0).any() or (t_x > T).any():
        raise ValueError("t_x must satisfy 0 <= t_x <= T")
    if (T <= 0).any():
        raise ValueError("T must be > 0")
    if ((x == 0) & (t_x != 0)).any():
        raise ValueError("t_x must be 0 when x == 0")
    return x, t_x, T


def bgnbd_loglik(params, x, t_x, T):
    """Per-customer BG/NBD log-likelihood; params = (r, alpha, a, b) > 0."""
    r, alpha, a, b = params
    x, t_x, T = _validate_bgnbd(x, t_x, T)
    ln_a1 = gammaln(r + x) - gammaln(r) + r * np.log(alpha)
    ln_a2 = (gammaln(a + b) + gammaln(b + x)
             - gammaln(b) - gammaln(a + b + x))
    ln_alive = -(r + x) * np.log(alpha + T)
    with np.errstate(divide="ignore"):
        ln_dead = np.where(
            x > 0,
            np.log(a) - np.log(np.where(x > 0, b + x - 1, 1.0))
            - (r + x) * np.log(alpha + t_x),
            -np.inf)
    return ln_a1 + ln_a2 + np.logaddexp(ln_alive, ln_dead)


def fit_bgnbd(x, t_x, T):
    """MLE for (r, alpha, a, b). Raises RuntimeError if optimizer fails."""
    x, t_x, T = _validate_bgnbd(x, t_x, T)

    def nll(log_params):
        return -bgnbd_loglik(np.exp(log_params), x, t_x, T).mean()

    res = minimize(nll, x0=np.zeros(4), method="Nelder-Mead",
                   options={"maxiter": 4000, "xatol": 1e-8, "fatol": 1e-8})
    if not res.success:
        raise RuntimeError(f"BG/NBD fit did not converge: {res.message}")
    return dict(zip(("r", "alpha", "a", "b"), np.exp(res.x)))


def bgnbd_p_alive(params, x, t_x, T):
    """P(customer still active | x, t_x, T)."""
    r, alpha, a, b = (params[k] for k in ("r", "alpha", "a", "b"))
    x, t_x, T = _validate_bgnbd(x, t_x, T)
    dead_odds = np.where(
        x > 0,
        a / np.where(x > 0, b + x - 1, 1.0)
        * ((alpha + T) / (alpha + t_x)) ** (r + x),
        0.0)
    return 1.0 / (1.0 + dead_odds)


def bgnbd_expected_purchases(params, x, t_x, T, horizon):
    """E[# transactions in (T, T + horizon] | x, t_x, T]."""
    r, alpha, a, b = (params[k] for k in ("r", "alpha", "a", "b"))
    x, t_x, T = _validate_bgnbd(x, t_x, T)
    if horizon <= 0:
        raise ValueError("horizon must be > 0")
    h2f1 = hyp2f1(r + x, b + x, a + b + x - 1, horizon / (alpha + T + horizon))
    numer = ((a + b + x - 1) / (a - 1)) * (
        1 - ((alpha + T) / (alpha + T + horizon)) ** (r + x) * h2f1)
    dead_odds = np.where(
        x > 0,
        a / np.where(x > 0, b + x - 1, 1.0)
        * ((alpha + T) / (alpha + t_x)) ** (r + x),
        0.0)
    return numer / (1.0 + dead_odds)


def _validate_gg(x, m_x):
    x, m_x = np.asarray(x, dtype=float), np.asarray(m_x, dtype=float)
    if x.shape != m_x.shape:
        raise ValueError("x and m_x must have identical shapes")
    if (x < 1).any():
        raise ValueError("Gamma-Gamma requires x >= 1 (buyers only)")
    if (m_x <= 0).any():
        raise ValueError("m_x must be > 0")
    return x, m_x


def gg_loglik(params, x, m_x):
    """Per-customer Gamma-Gamma log-likelihood; params = (p, q, gamma) > 0."""
    p, q, g = params
    x, m_x = _validate_gg(x, m_x)
    return (gammaln(p * x + q) - gammaln(p * x) - gammaln(q)
            + q * np.log(g) + (p * x - 1) * np.log(m_x)
            + p * x * np.log(x) - (p * x + q) * np.log(g + m_x * x))


def fit_gg(x, m_x):
    """MLE for (p, q, gamma). Raises RuntimeError if optimizer fails."""
    x, m_x = _validate_gg(x, m_x)

    def nll(log_params):
        return -gg_loglik(np.exp(log_params), x, m_x).mean()

    res = minimize(nll, x0=np.zeros(3), method="Nelder-Mead",
                   options={"maxiter": 4000, "xatol": 1e-8, "fatol": 1e-8})
    if not res.success:
        raise RuntimeError(f"Gamma-Gamma fit did not converge: {res.message}")
    return dict(zip(("p", "q", "gamma"), np.exp(res.x)))


def gg_expected_value(params, x, m_x):
    """E[mean transaction value | x, m_x] — shrinks m_x toward the prior."""
    p, q, g = (params[k] for k in ("p", "q", "gamma"))
    x, m_x = _validate_gg(x, m_x)
    return (g + m_x * x) * p / (p * x + q - 1)
