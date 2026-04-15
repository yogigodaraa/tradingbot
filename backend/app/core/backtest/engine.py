import logging
from dataclasses import dataclass, field
from datetime import datetime

import numpy as np
import pandas as pd

from app.core.backtest.metrics import compute_metrics, BacktestMetrics
from app.core.models.features import build_features

logger = logging.getLogger(__name__)


@dataclass
class BacktestTrade:
    ticker: str
    entry_date: datetime
    entry_price: float
    exit_date: datetime | None = None
    exit_price: float | None = None
    direction: str = "long"
    quantity: float = 0.0
    pnl: float = 0.0
    pnl_pct: float = 0.0
    stop_loss: float | None = None
    take_profit: float | None = None


@dataclass
class BacktestResult:
    metrics: BacktestMetrics
    trades: list[BacktestTrade]
    equity_curve: pd.DataFrame  # timestamp, equity, drawdown
    config: dict = field(default_factory=dict)


class BacktestEngine:
    """Event-driven backtesting engine.

    Mirrors live execution logic: iterates through bars, generates signals,
    checks risk, executes simulated trades.
    """

    def __init__(
        self,
        initial_capital: float = 100.0,
        max_position_pct: float = 0.20,
        max_positions: int = 5,
        stop_loss_pct: float = 0.03,
        take_profit_pct: float = 0.06,
        commission_pct: float = 0.0,  # Alpaca is $0 commission
        slippage_pct: float = 0.001,  # 0.1% slippage model
    ):
        self.initial_capital = initial_capital
        self.max_position_pct = max_position_pct
        self.max_positions = max_positions
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.commission_pct = commission_pct
        self.slippage_pct = slippage_pct

    def run(
        self,
        data: pd.DataFrame,
        signal_func=None,
    ) -> BacktestResult:
        """Run backtest on historical data.

        Args:
            data: OHLCV DataFrame with features already computed.
            signal_func: Optional callable(row) -> "buy"|"sell"|None
                        If None, uses a default RSI + SMA strategy.

        Returns:
            BacktestResult with metrics, trades, and equity curve.
        """
        if signal_func is None:
            signal_func = self._default_signal

        # Ensure features are built
        if "rsi_14" not in data.columns:
            data = build_features(data)
            data = data.dropna()

        cash = self.initial_capital
        positions: dict[str, BacktestTrade] = {}
        closed_trades: list[BacktestTrade] = []
        equity_history = []

        for i in range(len(data)):
            row = data.iloc[i]
            current_price = row["close"]
            timestamp = row.get("timestamp", data.index[i])

            # Check stop loss / take profit on open positions
            for ticker, trade in list(positions.items()):
                if trade.stop_loss and current_price <= trade.stop_loss:
                    # Stop loss hit
                    exit_price = trade.stop_loss * (1 - self.slippage_pct)
                    pnl = (exit_price - trade.entry_price) * trade.quantity
                    trade.exit_date = timestamp
                    trade.exit_price = exit_price
                    trade.pnl = pnl
                    trade.pnl_pct = pnl / (trade.entry_price * trade.quantity)
                    cash += exit_price * trade.quantity
                    closed_trades.append(trade)
                    del positions[ticker]

                elif trade.take_profit and current_price >= trade.take_profit:
                    # Take profit hit
                    exit_price = trade.take_profit * (1 - self.slippage_pct)
                    pnl = (exit_price - trade.entry_price) * trade.quantity
                    trade.exit_date = timestamp
                    trade.exit_price = exit_price
                    trade.pnl = pnl
                    trade.pnl_pct = pnl / (trade.entry_price * trade.quantity)
                    cash += exit_price * trade.quantity
                    closed_trades.append(trade)
                    del positions[ticker]

            # Generate signal
            signal = signal_func(row)

            if signal == "buy" and len(positions) < self.max_positions:
                # Calculate position size
                portfolio_value = cash + sum(
                    p.quantity * current_price for p in positions.values()
                )
                max_value = portfolio_value * self.max_position_pct
                buy_price = current_price * (1 + self.slippage_pct)
                quantity = min(max_value, cash) / buy_price

                if quantity * buy_price >= 1.0:  # Min $1 order
                    ticker = row.get("ticker", "BACKTEST")
                    if isinstance(ticker, float):
                        ticker = "BACKTEST"

                    trade = BacktestTrade(
                        ticker=ticker,
                        entry_date=timestamp,
                        entry_price=buy_price,
                        quantity=quantity,
                        stop_loss=buy_price * (1 - self.stop_loss_pct),
                        take_profit=buy_price * (1 + self.take_profit_pct),
                    )
                    positions[f"pos_{i}"] = trade
                    cash -= buy_price * quantity

            elif signal == "sell":
                # Close all positions
                for key, trade in list(positions.items()):
                    exit_price = current_price * (1 - self.slippage_pct)
                    pnl = (exit_price - trade.entry_price) * trade.quantity
                    trade.exit_date = timestamp
                    trade.exit_price = exit_price
                    trade.pnl = pnl
                    trade.pnl_pct = pnl / (trade.entry_price * trade.quantity)
                    cash += exit_price * trade.quantity
                    closed_trades.append(trade)
                    del positions[key]

            # Record equity
            position_value = sum(p.quantity * current_price for p in positions.values())
            total_equity = cash + position_value
            equity_history.append({
                "timestamp": timestamp,
                "equity": total_equity,
            })

        # Close any remaining positions at last price
        last_price = data.iloc[-1]["close"]
        for trade in positions.values():
            trade.exit_date = data.iloc[-1].get("timestamp", data.index[-1])
            trade.exit_price = last_price
            trade.pnl = (last_price - trade.entry_price) * trade.quantity
            trade.pnl_pct = trade.pnl / (trade.entry_price * trade.quantity)
            closed_trades.append(trade)

        equity_df = pd.DataFrame(equity_history)
        metrics = compute_metrics(equity_df, closed_trades, self.initial_capital)

        return BacktestResult(
            metrics=metrics,
            trades=closed_trades,
            equity_curve=equity_df,
            config={
                "initial_capital": self.initial_capital,
                "max_position_pct": self.max_position_pct,
                "max_positions": self.max_positions,
                "stop_loss_pct": self.stop_loss_pct,
                "take_profit_pct": self.take_profit_pct,
            },
        )

    @staticmethod
    def _default_signal(row: pd.Series) -> str | None:
        """Default strategy: RSI oversold + above SMA50 = buy, RSI overbought = sell."""
        rsi = row.get("rsi_14")
        above_sma50 = row.get("price_vs_sma50")

        if rsi is None or above_sma50 is None:
            return None
        if np.isnan(rsi) or np.isnan(above_sma50):
            return None

        if rsi < 30 and above_sma50 > 0:
            return "buy"
        elif rsi > 70:
            return "sell"
        return None
