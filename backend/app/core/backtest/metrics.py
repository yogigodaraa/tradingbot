from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class BacktestMetrics:
    # Returns
    total_return_pct: float
    annualized_return_pct: float
    sharpe_ratio: float
    sortino_ratio: float

    # Drawdown
    max_drawdown_pct: float
    avg_drawdown_pct: float

    # Trades
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    profit_factor: float
    avg_win_pct: float
    avg_loss_pct: float
    largest_win_pct: float
    largest_loss_pct: float
    avg_holding_days: float

    # Final
    final_equity: float
    initial_capital: float


def compute_metrics(
    equity_df: pd.DataFrame,
    trades: list,
    initial_capital: float,
    risk_free_rate: float = 0.04,  # ~4% Australian cash rate
) -> BacktestMetrics:
    """Compute comprehensive backtest metrics from equity curve and trades."""

    if equity_df.empty or not trades:
        return BacktestMetrics(
            total_return_pct=0, annualized_return_pct=0, sharpe_ratio=0,
            sortino_ratio=0, max_drawdown_pct=0, avg_drawdown_pct=0,
            total_trades=0, winning_trades=0, losing_trades=0,
            win_rate=0, profit_factor=0, avg_win_pct=0, avg_loss_pct=0,
            largest_win_pct=0, largest_loss_pct=0, avg_holding_days=0,
            final_equity=initial_capital, initial_capital=initial_capital,
        )

    equity = equity_df["equity"].values
    final_equity = equity[-1]

    # Returns
    total_return_pct = (final_equity - initial_capital) / initial_capital * 100
    num_days = len(equity)
    annualized_return_pct = ((final_equity / initial_capital) ** (252 / max(num_days, 1)) - 1) * 100

    # Daily returns
    daily_returns = np.diff(equity) / equity[:-1]

    # Sharpe ratio (annualized)
    if len(daily_returns) > 1 and np.std(daily_returns) > 0:
        excess_returns = daily_returns - risk_free_rate / 252
        sharpe = np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(252)
    else:
        sharpe = 0.0

    # Sortino ratio (only penalize downside volatility)
    downside = daily_returns[daily_returns < 0]
    if len(downside) > 0 and np.std(downside) > 0:
        sortino = np.mean(daily_returns - risk_free_rate / 252) / np.std(downside) * np.sqrt(252)
    else:
        sortino = 0.0

    # Drawdown
    peak = np.maximum.accumulate(equity)
    drawdowns = (peak - equity) / peak * 100
    max_drawdown = np.max(drawdowns)
    avg_drawdown = np.mean(drawdowns[drawdowns > 0]) if np.any(drawdowns > 0) else 0

    # Trade stats
    winning = [t for t in trades if t.pnl > 0]
    losing = [t for t in trades if t.pnl <= 0]

    win_rate = len(winning) / len(trades) * 100 if trades else 0

    gross_profit = sum(t.pnl for t in winning)
    gross_loss = abs(sum(t.pnl for t in losing))
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else float("inf")

    win_pcts = [t.pnl_pct * 100 for t in winning]
    loss_pcts = [t.pnl_pct * 100 for t in losing]

    avg_win = np.mean(win_pcts) if win_pcts else 0
    avg_loss = np.mean(loss_pcts) if loss_pcts else 0
    largest_win = max(win_pcts) if win_pcts else 0
    largest_loss = min(loss_pcts) if loss_pcts else 0

    # Average holding period
    holding_days = []
    for t in trades:
        if t.entry_date and t.exit_date:
            delta = t.exit_date - t.entry_date
            holding_days.append(delta.days if hasattr(delta, "days") else 0)
    avg_hold = np.mean(holding_days) if holding_days else 0

    return BacktestMetrics(
        total_return_pct=round(total_return_pct, 2),
        annualized_return_pct=round(annualized_return_pct, 2),
        sharpe_ratio=round(sharpe, 2),
        sortino_ratio=round(sortino, 2),
        max_drawdown_pct=round(max_drawdown, 2),
        avg_drawdown_pct=round(avg_drawdown, 2),
        total_trades=len(trades),
        winning_trades=len(winning),
        losing_trades=len(losing),
        win_rate=round(win_rate, 2),
        profit_factor=round(profit_factor, 2),
        avg_win_pct=round(avg_win, 2),
        avg_loss_pct=round(avg_loss, 2),
        largest_win_pct=round(largest_win, 2),
        largest_loss_pct=round(largest_loss, 2),
        avg_holding_days=round(avg_hold, 1),
        final_equity=round(final_equity, 2),
        initial_capital=initial_capital,
    )
