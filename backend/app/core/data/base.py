from abc import ABC, abstractmethod
from datetime import datetime

import pandas as pd


class DataProvider(ABC):
    """Abstract interface for market data providers (Alpaca, Finnhub, etc.)."""

    @abstractmethod
    async def get_bars(
        self,
        ticker: str,
        timeframe: str,
        start: datetime,
        end: datetime | None = None,
    ) -> pd.DataFrame:
        """Fetch OHLCV bars for a ticker.

        Returns DataFrame with columns: open, high, low, close, volume, timestamp
        """
        ...

    @abstractmethod
    async def get_latest_price(self, ticker: str) -> float:
        """Get the latest price for a ticker."""
        ...

    @abstractmethod
    async def get_latest_prices(self, tickers: list[str]) -> dict[str, float]:
        """Get latest prices for multiple tickers."""
        ...
