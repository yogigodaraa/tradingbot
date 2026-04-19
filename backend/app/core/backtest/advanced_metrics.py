"""Advanced performance metrics beyond the Sharpe ratio.

Sharpe is necessary but not sufficient. These are the metrics a quant
fund's risk committee actually looks at — they each answer a question
Sharpe alone doesn't.

Every function here takes an equity series (or daily returns) and
returns a scalar. Pure-numpy, no pandas dep — plug into any backtest
engine.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

TRADING_DAYS = 252


def to_returns(equity: np.ndarray) -> np.ndarray:
    """Convert an equity curve to simple per-period returns."""
    if len(equity) < 2:
        return np.array([])
    return np.diff(equity) / equity[:-1]


# ─── Core risk-adjusted ratios ───────────────────────────────────────────

def sharpe_ratio(returns: np.ndarray, *, rf: float = 0.0, periods_per_year: int = TRADING_DAYS) -> float:
    """Excess return per unit of volatility, annualised.

    `rf` is the per-period risk-free rate (already adjusted for the
    periodicity of `returns`). Pass 0 if you don't want to net it out.
    """
    if len(returns) < 2:
        return 0.0
    excess = returns - rf
    sd = float(np.std(excess, ddof=1))
    if sd == 0:
        return 0.0
    return float(np.mean(excess) / sd * np.sqrt(periods_per_year))


def sortino_ratio(
    returns: np.ndarray,
    *,
    rf: float = 0.0,
    target: float = 0.0,
    periods_per_year: int = TRADING_DAYS,
) -> float:
    """Like Sharpe, but only penalises *downside* volatility.

    Rewards strategies that are volatile on the upside but steady on the
    downside — exactly what most investors want. Uses below-target
    semi-deviation (López de Prado 2018, Eq. 8.1).
    """
    if len(returns) < 2:
        return 0.0
    excess = returns - rf
    downside = excess[excess < target]
    if len(downside) == 0:
        return float("inf")
    dd = float(np.sqrt(np.mean((downside - target) ** 2)))
    if dd == 0:
        return 0.0
    return float(np.mean(excess - target) / dd * np.sqrt(periods_per_year))


def calmar_ratio(returns: np.ndarray, *, periods_per_year: int = TRADING_DAYS) -> float:
    """CAGR divided by absolute max drawdown.

    Intuitive interpretation: "how many years of drawdown am I accepting
    per year of return?" Below 0.5 = painful. Above 1.0 = strong.
    """
    if len(returns) < 2:
        return 0.0
    equity = np.cumprod(1 + returns)
    years = len(returns) / periods_per_year
    if years <= 0:
        return 0.0
    cagr = float(equity[-1] ** (1 / years) - 1)
    mdd = float(max_drawdown(equity))
    if mdd == 0:
        return 0.0
    return cagr / abs(mdd)


def information_ratio(
    returns: np.ndarray,
    benchmark_returns: np.ndarray,
    *,
    periods_per_year: int = TRADING_DAYS,
) -> float:
    """Active return per unit of tracking error vs a benchmark."""
    n = min(len(returns), len(benchmark_returns))
    if n < 2:
        return 0.0
    active = returns[-n:] - benchmark_returns[-n:]
    te = float(np.std(active, ddof=1))
    if te == 0:
        return 0.0
    return float(np.mean(active) / te * np.sqrt(periods_per_year))


def omega_ratio(returns: np.ndarray, *, threshold: float = 0.0) -> float:
    """Ratio of gains above threshold to losses below threshold.

    Omega > 1 at threshold=0 means the strategy makes money. Omega > 1.5
    at your required-return threshold means the strategy meaningfully
    beats it. Unlike Sharpe, Omega uses the full return distribution so
    it's resistant to non-normality.
    """
    if len(returns) == 0:
        return 0.0
    gains = np.sum(np.maximum(returns - threshold, 0))
    losses = np.sum(np.maximum(threshold - returns, 0))
    if losses == 0:
        return float("inf")
    return float(gains / losses)


# ─── Drawdown ────────────────────────────────────────────────────────────

def max_drawdown(equity: np.ndarray) -> float:
    """Deepest peak-to-trough loss in the equity series."""
    if len(equity) < 2:
        return 0.0
    peaks = np.maximum.accumulate(equity)
    drawdowns = (equity - peaks) / peaks
    return float(drawdowns.min())


def ulcer_index(equity: np.ndarray) -> float:
    """Quadratic-mean of drawdown depths — penalises both depth AND duration.

    Martin (1989). Used in the Martin ratio (CAGR / Ulcer Index) as an
    alternative to Calmar that rewards short, shallow drawdowns over
    deep-but-brief ones.
    """
    if len(equity) < 2:
        return 0.0
    peaks = np.maximum.accumulate(equity)
    dd = (equity - peaks) / peaks
    return float(np.sqrt(np.mean(dd * dd)))


# ─── Trade-level ─────────────────────────────────────────────────────────

def win_rate(trade_pnls: np.ndarray) -> float:
    if len(trade_pnls) == 0:
        return 0.0
    return float(np.mean(trade_pnls > 0))


def profit_factor(trade_pnls: np.ndarray) -> float:
    """Sum of winning trades divided by |sum of losing trades|.

    PF > 1.5 is generally considered viable. < 1 means the strategy lost money.
    """
    gains = float(trade_pnls[trade_pnls > 0].sum())
    losses = float(-trade_pnls[trade_pnls < 0].sum())
    if losses == 0:
        return float("inf") if gains > 0 else 0.0
    return gains / losses


def expectancy(trade_pnls: np.ndarray) -> float:
    """Average dollars made per trade. Sanity check: is this strategy worth trading?"""
    if len(trade_pnls) == 0:
        return 0.0
    return float(np.mean(trade_pnls))


# ─── VaR / CVaR ──────────────────────────────────────────────────────────

def value_at_risk(returns: np.ndarray, *, confidence: float = 0.95) -> float:
    """Historical VaR — the worst 1-period loss you expect (1-confidence) of the time."""
    if len(returns) == 0:
        return 0.0
    return float(np.quantile(returns, 1 - confidence))


def conditional_var(returns: np.ndarray, *, confidence: float = 0.95) -> float:
    """Expected loss on the worst (1-confidence) of periods. Always ≤ VaR."""
    if len(returns) == 0:
        return 0.0
    threshold = value_at_risk(returns, confidence=confidence)
    tail = returns[returns <= threshold]
    return float(tail.mean()) if len(tail) else 0.0


# ─── Full report ─────────────────────────────────────────────────────────

@dataclass
class AdvancedMetrics:
    sharpe: float = 0.0
    sortino: float = 0.0
    calmar: float = 0.0
    omega: float = 0.0
    max_drawdown: float = 0.0
    ulcer_index: float = 0.0
    value_at_risk_95: float = 0.0
    cvar_95: float = 0.0
    total_return: float = 0.0
    annualised_return: float = 0.0
    annualised_volatility: float = 0.0
    skew: float = 0.0
    kurtosis: float = 0.0
    trade_win_rate: float = 0.0
    trade_profit_factor: float = 0.0
    trade_expectancy: float = 0.0
    benchmark_information_ratio: float | None = None
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {k: (round(v, 4) if isinstance(v, float) else v) for k, v in vars(self).items()}


def compute_advanced_metrics(
    equity: np.ndarray,
    *,
    trade_pnls: np.ndarray | None = None,
    benchmark_returns: np.ndarray | None = None,
    rf: float = 0.0,
    periods_per_year: int = TRADING_DAYS,
) -> AdvancedMetrics:
    """Compute every metric at once and return as a structured dataclass."""
    m = AdvancedMetrics()
    if len(equity) < 2:
        m.notes.append("Insufficient data — need ≥ 2 equity observations.")
        return m

    returns = to_returns(equity)
    m.sharpe = sharpe_ratio(returns, rf=rf, periods_per_year=periods_per_year)
    m.sortino = sortino_ratio(returns, rf=rf, periods_per_year=periods_per_year)
    m.calmar = calmar_ratio(returns, periods_per_year=periods_per_year)
    m.omega = omega_ratio(returns)
    m.max_drawdown = max_drawdown(equity)
    m.ulcer_index = ulcer_index(equity)
    m.value_at_risk_95 = value_at_risk(returns, confidence=0.95)
    m.cvar_95 = conditional_var(returns, confidence=0.95)
    m.total_return = float(equity[-1] / equity[0] - 1)
    years = len(returns) / periods_per_year
    m.annualised_return = float((1 + m.total_return) ** (1 / max(years, 1e-9)) - 1) if years > 0 else 0.0
    m.annualised_volatility = float(np.std(returns, ddof=1) * np.sqrt(periods_per_year))
    m.skew = float(_moment(returns, 3))
    m.kurtosis = float(_moment(returns, 4))

    if trade_pnls is not None and len(trade_pnls):
        tp = np.asarray(trade_pnls)
        m.trade_win_rate = win_rate(tp)
        m.trade_profit_factor = profit_factor(tp)
        m.trade_expectancy = expectancy(tp)

    if benchmark_returns is not None and len(benchmark_returns) >= len(returns):
        m.benchmark_information_ratio = information_ratio(
            returns, benchmark_returns, periods_per_year=periods_per_year
        )

    return m


def _moment(returns: np.ndarray, order: int) -> float:
    """Standardised moment (skew = 3, kurtosis = 4). Robust to small samples."""
    if len(returns) < 2:
        return 0.0
    mu = returns.mean()
    sd = returns.std(ddof=1)
    if sd == 0:
        return 0.0
    return float(np.mean(((returns - mu) / sd) ** order))
