from datetime import datetime

from pydantic import BaseModel

from app.db.models import StrategyType, TradeDirection, TradeStatus


class TradeCreate(BaseModel):
    ticker: str
    direction: TradeDirection
    strategy: StrategyType
    quantity: float
    entry_price: float | None = None
    stop_loss: float | None = None
    take_profit: float | None = None
    notes: str | None = None


class TradeResponse(BaseModel):
    id: int
    broker_order_id: str | None
    ticker: str
    direction: TradeDirection
    status: TradeStatus
    strategy: StrategyType
    quantity: float
    entry_price: float | None
    exit_price: float | None
    stop_loss: float | None
    take_profit: float | None
    pnl: float | None
    pnl_pct: float | None
    fees: float
    signal_id: int | None
    notes: str | None
    created_at: datetime
    filled_at: datetime | None
    closed_at: datetime | None

    model_config = {"from_attributes": True}
