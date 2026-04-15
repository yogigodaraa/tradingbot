from datetime import datetime

from pydantic import BaseModel


class Position(BaseModel):
    ticker: str
    quantity: float
    avg_entry_price: float
    current_price: float
    market_value: float
    unrealized_pnl: float
    unrealized_pnl_pct: float
    side: str  # "long" or "short"


class PortfolioOverview(BaseModel):
    total_value: float
    cash: float
    positions_value: float
    daily_pnl: float
    daily_pnl_pct: float
    total_pnl: float
    total_pnl_pct: float
    drawdown_pct: float
    positions: list[Position]
    updated_at: datetime


class PortfolioSnapshotResponse(BaseModel):
    id: int
    total_value: float
    cash: float
    positions_value: float
    daily_pnl: float
    daily_pnl_pct: float
    total_pnl: float
    total_pnl_pct: float
    drawdown_pct: float
    timestamp: datetime

    model_config = {"from_attributes": True}


class EquityCurvePoint(BaseModel):
    timestamp: datetime
    total_value: float
    daily_pnl_pct: float
