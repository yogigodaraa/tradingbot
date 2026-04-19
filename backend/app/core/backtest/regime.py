"""Market-regime detection for backtest-aware strategy evaluation.

A strategy's live performance depends heavily on the regime it runs
in. A mean-reversion model that shines in low-volatility sideways
markets can blow up in a trending crash. Reporting per-regime metrics
surfaces that *before* you go live.

Two detectors ship here:

1. **Volatility regime** — bucket each day as "low" / "medium" / "high"
   based on a rolling realized-vol estimate and its full-history
   quantile. Fast, transparent, doesn't need fitting.
2. **Hidden Markov 2-state regime** — a numpy-only implementation of a
   two-state Gaussian HMM fit by EM. State 0 = "calm" (low mean, low
   vol), state 1 = "stress" (anything else). Slower but catches regime
   *transitions* the rolling-vol heuristic often lags.

Reference:
    Hamilton (1989) — "A New Approach to the Economic Analysis of
    Nonstationary Time Series and the Business Cycle."
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class VolatilityRegimes:
    labels: np.ndarray  # shape (T,), values in {0, 1, 2} = low/med/high
    thresholds: tuple[float, float]
    volatility: np.ndarray  # rolling std


def classify_volatility(
    returns: np.ndarray,
    *,
    window: int = 21,
    low_quantile: float = 0.33,
    high_quantile: float = 0.67,
) -> VolatilityRegimes:
    """Label each day low/med/high based on rolling realized volatility."""
    if len(returns) < window:
        return VolatilityRegimes(
            labels=np.zeros(len(returns), dtype=int),
            thresholds=(0.0, 0.0),
            volatility=np.zeros(len(returns)),
        )

    # Rolling std
    rolling = np.zeros(len(returns))
    for i in range(len(returns)):
        start = max(0, i - window + 1)
        rolling[i] = np.std(returns[start : i + 1], ddof=1) if i + 1 - start >= 2 else 0.0

    lo = float(np.quantile(rolling[window:], low_quantile)) if len(rolling) > window else 0.0
    hi = float(np.quantile(rolling[window:], high_quantile)) if len(rolling) > window else 0.0

    labels = np.zeros(len(returns), dtype=int)
    labels[rolling >= hi] = 2
    labels[(rolling >= lo) & (rolling < hi)] = 1
    # rolling < lo stays 0
    return VolatilityRegimes(labels=labels, thresholds=(lo, hi), volatility=rolling)


@dataclass
class HMMRegimes:
    states: np.ndarray  # shape (T,), values in {0, 1}
    means: tuple[float, float]
    stds: tuple[float, float]
    transitions: np.ndarray  # shape (2, 2)
    log_likelihood: float
    iterations: int


def fit_two_state_hmm(
    returns: np.ndarray,
    *,
    max_iter: int = 100,
    tol: float = 1e-6,
) -> HMMRegimes:
    """Two-state Gaussian HMM fit by EM. Calm vs. stress states.

    Parameters initialised by splitting the data on median volatility —
    helps EM converge to the calm/stress decomposition instead of
    degenerate solutions.
    """
    x = np.asarray(returns, dtype=float)
    T = len(x)
    if T < 10:
        return HMMRegimes(
            states=np.zeros(T, dtype=int),
            means=(0.0, 0.0),
            stds=(1e-6, 1e-6),
            transitions=np.eye(2),
            log_likelihood=0.0,
            iterations=0,
        )

    # Initialise from median-split
    med_abs = float(np.median(np.abs(x - x.mean())))
    mask = np.abs(x - x.mean()) > med_abs
    mu0 = float(x[~mask].mean()) if (~mask).any() else 0.0
    mu1 = float(x[mask].mean()) if mask.any() else 0.0
    sd0 = float(x[~mask].std(ddof=1)) if (~mask).sum() > 1 else 0.01
    sd1 = float(x[mask].std(ddof=1)) if mask.sum() > 1 else 0.02
    mu = np.array([mu0, mu1])
    sd = np.array([max(sd0, 1e-6), max(sd1, 1e-6)])
    # Transition matrix — mild self-persistence
    A = np.array([[0.95, 0.05], [0.05, 0.95]])
    pi = np.array([0.5, 0.5])

    ll_prev = -np.inf
    for iteration in range(max_iter):
        # E-step: forward-backward
        alpha, scale = _forward(x, mu, sd, A, pi)
        beta = _backward(x, mu, sd, A, scale)
        gamma = alpha * beta
        gamma /= gamma.sum(axis=1, keepdims=True)

        xi = np.zeros((T - 1, 2, 2))
        for t in range(T - 1):
            for i in range(2):
                for j in range(2):
                    xi[t, i, j] = alpha[t, i] * A[i, j] * _gauss(x[t + 1], mu[j], sd[j]) * beta[t + 1, j]
            xi[t] /= xi[t].sum() + 1e-12

        # M-step
        pi = gamma[0]
        A = xi.sum(axis=0) / (gamma[:-1].sum(axis=0, keepdims=True).T + 1e-12)
        A /= A.sum(axis=1, keepdims=True)
        for i in range(2):
            w = gamma[:, i]
            mu[i] = (w * x).sum() / (w.sum() + 1e-12)
            sd[i] = float(np.sqrt((w * (x - mu[i]) ** 2).sum() / (w.sum() + 1e-12)))
            sd[i] = max(sd[i], 1e-6)

        ll = float(np.sum(np.log(scale + 1e-12)))
        if abs(ll - ll_prev) < tol:
            break
        ll_prev = ll

    # Viterbi-ish: take most likely state per step (posterior mode)
    states = gamma.argmax(axis=1).astype(int)
    # Canonicalise — state 0 = calm = smaller std
    if sd[0] > sd[1]:
        states = 1 - states
        mu = mu[::-1]
        sd = sd[::-1]
        A = A[::-1, ::-1]

    return HMMRegimes(
        states=states,
        means=(float(mu[0]), float(mu[1])),
        stds=(float(sd[0]), float(sd[1])),
        transitions=A,
        log_likelihood=ll_prev,
        iterations=iteration + 1,
    )


# ─── Per-regime metric breakdown ────────────────────────────────────────

def returns_by_regime(returns: np.ndarray, regime_labels: np.ndarray) -> dict[int, dict]:
    """Per-regime summary. Strategy alpha often hides in one regime and vanishes in another."""
    out: dict[int, dict] = {}
    for label in np.unique(regime_labels):
        r = returns[regime_labels == label]
        if len(r) == 0:
            continue
        out[int(label)] = {
            "count": int(len(r)),
            "mean": float(r.mean()),
            "std": float(r.std(ddof=1)) if len(r) > 1 else 0.0,
            "total": float(np.prod(1 + r) - 1),
            "win_rate": float(np.mean(r > 0)),
        }
    return out


# ─── Gaussian forward/backward helpers ──────────────────────────────────

def _gauss(x: float, mu: float, sd: float) -> float:
    z = (x - mu) / sd
    return np.exp(-0.5 * z * z) / (sd * np.sqrt(2 * np.pi))


def _forward(x, mu, sd, A, pi):
    T = len(x)
    alpha = np.zeros((T, 2))
    scale = np.zeros(T)
    for i in range(2):
        alpha[0, i] = pi[i] * _gauss(x[0], mu[i], sd[i])
    scale[0] = alpha[0].sum() + 1e-12
    alpha[0] /= scale[0]
    for t in range(1, T):
        for j in range(2):
            alpha[t, j] = sum(alpha[t - 1, i] * A[i, j] for i in range(2)) * _gauss(x[t], mu[j], sd[j])
        scale[t] = alpha[t].sum() + 1e-12
        alpha[t] /= scale[t]
    return alpha, scale


def _backward(x, mu, sd, A, scale):
    T = len(x)
    beta = np.zeros((T, 2))
    beta[-1] = 1.0
    for t in range(T - 2, -1, -1):
        for i in range(2):
            beta[t, i] = sum(
                A[i, j] * _gauss(x[t + 1], mu[j], sd[j]) * beta[t + 1, j] for j in range(2)
            )
        beta[t] /= scale[t]
    return beta
