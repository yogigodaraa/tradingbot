import logging
from datetime import datetime, timedelta

import pandas as pd
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest, StockLatestBarRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit

from app.config import settings
from app.core.data.base import DataProvider

logger = logging.getLogger(__name__)

TIMEFRAME_MAP = {
    "1min": TimeFrame(1, TimeFrameUnit.Minute),
    "5min": TimeFrame(5, TimeFrameUnit.Minute),
    "15min": TimeFrame(15, TimeFrameUnit.Minute),
    "1h": TimeFrame(1, TimeFrameUnit.Hour),
    "1d": TimeFrame(1, TimeFrameUnit.Day),
    "1w": TimeFrame(1, TimeFrameUnit.Week),
}


class AlpacaDataProvider(DataProvider):
    """Market data provider using Alpaca Data API (free with account)."""

    def __init__(self):
        # Data client doesn't need keys for free tier (IEX feed)
        # With keys you get SIP (all exchanges) feed
        if settings.alpaca_api_key:
            self.client = StockHistoricalDataClient(
                api_key=settings.alpaca_api_key,
                secret_key=settings.alpaca_secret_key,
            )
        else:
            self.client = StockHistoricalDataClient()

    async def get_bars(
        self,
        ticker: str,
        timeframe: str = "1d",
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> pd.DataFrame:
        """Fetch OHLCV bars from Alpaca."""
        if start is None:
            start = datetime.utcnow() - timedelta(days=730)  # 2 years default

        tf = TIMEFRAME_MAP.get(timeframe, TimeFrame(1, TimeFrameUnit.Day))

        request = StockBarsRequest(
            symbol_or_symbols=ticker,
            timeframe=tf,
            start=start,
            end=end,
        )

        bars = self.client.get_stock_bars(request)
        df = bars.df

        if df.empty:
            logger.warning(f"No bars returned for {ticker}")
            return pd.DataFrame()

        # Reset multi-index (symbol, timestamp) to flat DataFrame
        if isinstance(df.index, pd.MultiIndex):
            df = df.reset_index()
            df = df.drop(columns=["symbol"], errors="ignore")
            df = df.rename(columns={"timestamp": "timestamp"})
        else:
            df = df.reset_index()

        # Standardize column names
        col_map = {
            "open": "open",
            "high": "high",
            "low": "low",
            "close": "close",
            "volume": "volume",
            "trade_count": "trade_count",
            "vwap": "vwap",
        }
        df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})

        return df

    async def get_latest_price(self, ticker: str) -> float:
        """Get latest price for a single ticker."""
        request = StockLatestBarRequest(symbol_or_symbols=ticker)
        bars = self.client.get_stock_latest_bar(request)

        if ticker in bars:
            return float(bars[ticker].close)
        raise ValueError(f"No price data for {ticker}")

    async def get_latest_prices(self, tickers: list[str]) -> dict[str, float]:
        """Get latest prices for multiple tickers in one call."""
        request = StockLatestBarRequest(symbol_or_symbols=tickers)
        bars = self.client.get_stock_latest_bar(request)

        prices = {}
        for ticker in tickers:
            if ticker in bars:
                prices[ticker] = float(bars[ticker].close)
        return prices
