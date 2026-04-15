from pydantic import BaseModel


class BacktestRequest(BaseModel):
    ticker: str = "SPY"
    initial_capital: float = 100.0
    days: int = 730  # 2 years
    stop_loss_pct: float = 0.03
    take_profit_pct: float = 0.06
    max_position_pct: float = 0.20
    max_positions: int = 5


class BacktestTradeResponse(BaseModel):
    ticker: str
    entry_date: str
    entry_price: float
    exit_date: str | None
    exit_price: float | None
    direction: str
    pnl: float
    pnl_pct: float


class BacktestMetricsResponse(BaseModel):
    total_return_pct: float
    annualized_return_pct: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown_pct: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    profit_factor: float
    avg_win_pct: float
    avg_loss_pct: float
    final_equity: float
    initial_capital: float


class BacktestResponse(BaseModel):
    metrics: BacktestMetricsResponse
    trades: list[BacktestTradeResponse]
    equity_curve: list[dict]
