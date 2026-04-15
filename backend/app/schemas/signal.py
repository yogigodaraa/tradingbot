from datetime import datetime

from pydantic import BaseModel

from app.db.models import SignalAction, StrategyType


class SignalResponse(BaseModel):
    id: int
    ticker: str
    action: SignalAction
    strategy: StrategyType
    confidence: float
    entry_price: float | None
    stop_loss: float | None
    take_profit: float | None
    model_prediction: float | None
    sentiment_score: float | None
    technical_score: float | None
    executed: bool
    trade_id: int | None
    created_at: datetime

    model_config = {"from_attributes": True}
