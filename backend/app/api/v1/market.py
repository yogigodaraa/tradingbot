import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, Query

from app.config import settings
from app.core.data.alpaca import AlpacaDataProvider

logger = logging.getLogger(__name__)
router = APIRouter()

_data_provider: AlpacaDataProvider | None = None


def get_data_provider() -> AlpacaDataProvider:
    global _data_provider
    if _data_provider is None:
        _data_provider = AlpacaDataProvider()
    return _data_provider


@router.get("/prices")
async def get_live_prices(
    tickers: str = Query(
        default=None,
        description="Comma-separated tickers. Defaults to watchlist.",
    ),
):
    """Get latest prices for all watchlist tickers (or custom list)."""
    ticker_list = (
        [t.strip().upper() for t in tickers.split(",")]
        if tickers
        else settings.default_watchlist
    )

    provider = get_data_provider()
    prices = await provider.get_latest_prices(ticker_list)

    results = []
    for ticker in ticker_list:
        if ticker in prices:
            results.append({
                "ticker": ticker,
                "price": prices[ticker],
            })

    return {"prices": results, "updated_at": datetime.utcnow().isoformat()}


@router.get("/chart/{ticker}")
async def get_price_chart(
    ticker: str,
    days: int = Query(default=90, ge=1, le=730),
    timeframe: str = Query(default="1d"),
):
    """Get OHLCV chart data for a ticker."""
    provider = get_data_provider()
    start = datetime.utcnow() - timedelta(days=days)

    df = await provider.get_bars(
        ticker=ticker.upper(),
        timeframe=timeframe,
        start=start,
    )

    if df.empty:
        return {"ticker": ticker, "bars": [], "error": "No data available"}

    bars = []
    for _, row in df.iterrows():
        bar = {
            "time": str(row.get("timestamp", "")),
            "open": round(float(row["open"]), 2),
            "high": round(float(row["high"]), 2),
            "low": round(float(row["low"]), 2),
            "close": round(float(row["close"]), 2),
            "volume": int(row["volume"]),
        }
        bars.append(bar)

    return {
        "ticker": ticker.upper(),
        "timeframe": timeframe,
        "bars": bars,
        "count": len(bars),
    }


@router.get("/movers")
async def get_movers():
    """Get top gainers and losers from the watchlist based on daily change."""
    provider = get_data_provider()
    tickers = settings.default_watchlist

    prices = await provider.get_latest_prices(tickers)

    # Get yesterday's close to calculate daily change
    end = datetime.utcnow()
    start = end - timedelta(days=5)  # fetch a few days to ensure we get prev close

    movers = []
    for ticker in tickers:
        if ticker not in prices:
            continue
        try:
            df = await provider.get_bars(ticker=ticker, timeframe="1d", start=start, end=end)
            if len(df) >= 2:
                prev_close = float(df.iloc[-2]["close"])
                current = prices[ticker]
                change = current - prev_close
                change_pct = (change / prev_close) * 100
                movers.append({
                    "ticker": ticker,
                    "price": round(current, 2),
                    "change": round(change, 2),
                    "change_pct": round(change_pct, 2),
                    "prev_close": round(prev_close, 2),
                })
        except Exception as e:
            logger.warning(f"Failed to get mover data for {ticker}: {e}")

    # Sort by absolute change percentage
    gainers = sorted([m for m in movers if m["change_pct"] > 0], key=lambda x: x["change_pct"], reverse=True)
    losers = sorted([m for m in movers if m["change_pct"] < 0], key=lambda x: x["change_pct"])

    return {
        "gainers": gainers[:10],
        "losers": losers[:10],
        "all": sorted(movers, key=lambda x: abs(x["change_pct"]), reverse=True),
        "updated_at": datetime.utcnow().isoformat(),
    }
