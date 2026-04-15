import logging
from datetime import datetime, timedelta

from fastapi import APIRouter

from app.core.backtest.engine import BacktestEngine
from app.core.data.alpaca import AlpacaDataProvider
from app.schemas.backtest import (
    BacktestRequest,
    BacktestResponse,
    BacktestMetricsResponse,
    BacktestTradeResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/run", response_model=BacktestResponse)
async def run_backtest(req: BacktestRequest):
    """Run a backtest on historical data using the default strategy."""

    # Fetch historical data
    data_provider = AlpacaDataProvider()
    end = datetime.utcnow()
    start = end - timedelta(days=req.days)

    data = await data_provider.get_bars(
        ticker=req.ticker,
        timeframe="1d",
        start=start,
        end=end,
    )

    if data.empty:
        return BacktestResponse(
            metrics=BacktestMetricsResponse(
                total_return_pct=0, annualized_return_pct=0, sharpe_ratio=0,
                sortino_ratio=0, max_drawdown_pct=0, total_trades=0,
                winning_trades=0, losing_trades=0, win_rate=0, profit_factor=0,
                avg_win_pct=0, avg_loss_pct=0, final_equity=req.initial_capital,
                initial_capital=req.initial_capital,
            ),
            trades=[],
            equity_curve=[],
        )

    # Run backtest
    engine = BacktestEngine(
        initial_capital=req.initial_capital,
        max_position_pct=req.max_position_pct,
        max_positions=req.max_positions,
        stop_loss_pct=req.stop_loss_pct,
        take_profit_pct=req.take_profit_pct,
    )

    result = engine.run(data)

    # Convert to response
    trades = []
    for t in result.trades:
        trades.append(
            BacktestTradeResponse(
                ticker=t.ticker,
                entry_date=str(t.entry_date),
                entry_price=round(t.entry_price, 2),
                exit_date=str(t.exit_date) if t.exit_date else None,
                exit_price=round(t.exit_price, 2) if t.exit_price else None,
                direction=t.direction,
                pnl=round(t.pnl, 2),
                pnl_pct=round(t.pnl_pct * 100, 2),
            )
        )

    m = result.metrics
    equity_curve = [
        {"timestamp": str(row["timestamp"]), "equity": round(row["equity"], 2)}
        for _, row in result.equity_curve.iterrows()
    ]

    return BacktestResponse(
        metrics=BacktestMetricsResponse(
            total_return_pct=m.total_return_pct,
            annualized_return_pct=m.annualized_return_pct,
            sharpe_ratio=m.sharpe_ratio,
            sortino_ratio=m.sortino_ratio,
            max_drawdown_pct=m.max_drawdown_pct,
            total_trades=m.total_trades,
            winning_trades=m.winning_trades,
            losing_trades=m.losing_trades,
            win_rate=m.win_rate,
            profit_factor=m.profit_factor,
            avg_win_pct=m.avg_win_pct,
            avg_loss_pct=m.avg_loss_pct,
            final_equity=m.final_equity,
            initial_capital=m.initial_capital,
        ),
        trades=trades,
        equity_curve=equity_curve,
    )
