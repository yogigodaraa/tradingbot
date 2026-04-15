from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass
class OrderRequest:
    ticker: str
    quantity: float
    side: str  # "buy" or "sell"
    order_type: str = "market"  # "market", "limit"
    limit_price: float | None = None
    stop_price: float | None = None
    time_in_force: str = "day"  # "day", "gtc", "ioc"


@dataclass
class OrderResult:
    order_id: str
    ticker: str
    side: str
    quantity: float
    status: str  # "pending", "filled", "cancelled", "rejected"
    filled_price: float | None = None
    filled_at: datetime | None = None
    message: str = ""


@dataclass
class PositionInfo:
    ticker: str
    quantity: float
    avg_entry_price: float
    current_price: float
    market_value: float
    unrealized_pnl: float
    unrealized_pnl_pct: float
    side: str  # "long" or "short"


@dataclass
class AccountInfo:
    equity: float
    cash: float
    buying_power: float
    portfolio_value: float
    currency: str = "USD"


class Broker(ABC):
    """Abstract interface for broker execution (Alpaca, OANDA, etc.)."""

    @abstractmethod
    async def submit_order(self, order: OrderRequest) -> OrderResult:
        """Submit an order to the broker."""
        ...

    @abstractmethod
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel a pending order. Returns True if cancelled successfully."""
        ...

    @abstractmethod
    async def get_positions(self) -> list[PositionInfo]:
        """Get all open positions."""
        ...

    @abstractmethod
    async def get_account(self) -> AccountInfo:
        """Get account information (equity, cash, buying power)."""
        ...

    @abstractmethod
    async def get_order_status(self, order_id: str) -> OrderResult:
        """Get the current status of an order."""
        ...
