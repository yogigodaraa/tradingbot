import enum
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class TradeDirection(str, enum.Enum):
    LONG = "long"
    SHORT = "short"


class TradeStatus(str, enum.Enum):
    PENDING = "pending"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class SignalAction(str, enum.Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


class StrategyType(str, enum.Enum):
    SWING = "swing"
    LONGTERM = "longterm"


class Trade(Base):
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, autoincrement=True)
    broker_order_id = Column(String(100), nullable=True, index=True)
    ticker = Column(String(10), nullable=False, index=True)
    direction = Column(Enum(TradeDirection), nullable=False)
    status = Column(Enum(TradeStatus), nullable=False, default=TradeStatus.PENDING)
    strategy = Column(Enum(StrategyType), nullable=False)

    # Order details
    quantity = Column(Float, nullable=False)
    entry_price = Column(Float, nullable=True)
    exit_price = Column(Float, nullable=True)
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)

    # P&L
    pnl = Column(Float, nullable=True)
    pnl_pct = Column(Float, nullable=True)
    fees = Column(Float, default=0.0)

    # Metadata
    signal_id = Column(Integer, nullable=True)
    notes = Column(Text, nullable=True)

    # Timestamps (UTC)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    filled_at = Column(DateTime, nullable=True)
    closed_at = Column(DateTime, nullable=True)


class Signal(Base):
    __tablename__ = "signals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(10), nullable=False, index=True)
    action = Column(Enum(SignalAction), nullable=False)
    strategy = Column(Enum(StrategyType), nullable=False)
    confidence = Column(Float, nullable=False)

    # Signal details
    entry_price = Column(Float, nullable=True)
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)

    # Model outputs
    model_prediction = Column(Float, nullable=True)
    sentiment_score = Column(Float, nullable=True)
    technical_score = Column(Float, nullable=True)

    # Was it acted on?
    executed = Column(Boolean, default=False)
    trade_id = Column(Integer, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class PriceBar(Base):
    __tablename__ = "price_bars"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(10), nullable=False, index=True)
    timeframe = Column(String(10), nullable=False)  # 1min, 5min, 1h, 1d

    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)

    timestamp = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class SentimentRecord(Base):
    __tablename__ = "sentiment_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(10), nullable=False, index=True)

    # Article info
    headline = Column(Text, nullable=False)
    source = Column(String(100), nullable=True)
    url = Column(Text, nullable=True)

    # FinBERT scores
    positive = Column(Float, nullable=False)
    negative = Column(Float, nullable=False)
    neutral = Column(Float, nullable=False)
    composite_score = Column(Float, nullable=False)  # -1 to 1

    published_at = Column(DateTime, nullable=True)
    analyzed_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class PortfolioSnapshot(Base):
    __tablename__ = "portfolio_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    total_value = Column(Float, nullable=False)
    cash = Column(Float, nullable=False)
    positions_value = Column(Float, nullable=False)
    daily_pnl = Column(Float, nullable=False)
    daily_pnl_pct = Column(Float, nullable=False)
    total_pnl = Column(Float, nullable=False)
    total_pnl_pct = Column(Float, nullable=False)
    drawdown_pct = Column(Float, nullable=False)

    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)


class WatchlistItem(Base):
    __tablename__ = "watchlist"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(10), nullable=False, unique=True, index=True)
    name = Column(String(200), nullable=True)
    sector = Column(String(100), nullable=True)
    active = Column(Boolean, default=True)
    added_at = Column(DateTime, default=datetime.utcnow, nullable=False)
