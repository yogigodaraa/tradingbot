from pydantic import BaseModel


class BotSettings(BaseModel):
    """Current bot configuration (read-only view of risk + trading settings)."""
    paper_trading: bool
    max_position_pct: float
    max_open_positions: int
    max_daily_loss_pct: float
    max_drawdown_pct: float
    min_signal_confidence: float
    watchlist: list[str]


class WatchlistUpdate(BaseModel):
    tickers: list[str]
