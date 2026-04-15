import logging
from dataclasses import dataclass
from datetime import datetime, timedelta

import finnhub

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class NewsArticle:
    headline: str
    summary: str
    source: str
    url: str
    ticker: str
    published_at: datetime


class NewsFetcher:
    """Fetches financial news from Finnhub API.

    Free tier: 60 calls/min, provides company news, market news, and press releases.
    """

    def __init__(self):
        self.client = finnhub.Client(api_key=settings.finnhub_api_key)

    async def get_company_news(
        self,
        ticker: str,
        days_back: int = 3,
    ) -> list[NewsArticle]:
        """Fetch recent news for a specific company."""
        end = datetime.utcnow()
        start = end - timedelta(days=days_back)

        try:
            articles = self.client.company_news(
                ticker,
                _from=start.strftime("%Y-%m-%d"),
                to=end.strftime("%Y-%m-%d"),
            )

            results = []
            for a in articles:
                if not a.get("headline"):
                    continue
                results.append(
                    NewsArticle(
                        headline=a["headline"],
                        summary=a.get("summary", ""),
                        source=a.get("source", "unknown"),
                        url=a.get("url", ""),
                        ticker=ticker,
                        published_at=datetime.fromtimestamp(a.get("datetime", 0)),
                    )
                )

            logger.info(f"Fetched {len(results)} articles for {ticker}")
            return results

        except Exception as e:
            logger.error(f"Failed to fetch news for {ticker}: {e}")
            return []

    async def get_market_news(self, category: str = "general") -> list[NewsArticle]:
        """Fetch general market news.

        Categories: general, forex, crypto, merger
        """
        try:
            articles = self.client.general_news(category, min_id=0)

            results = []
            for a in articles:
                if not a.get("headline"):
                    continue
                results.append(
                    NewsArticle(
                        headline=a["headline"],
                        summary=a.get("summary", ""),
                        source=a.get("source", "unknown"),
                        url=a.get("url", ""),
                        ticker="MARKET",
                        published_at=datetime.fromtimestamp(a.get("datetime", 0)),
                    )
                )

            return results

        except Exception as e:
            logger.error(f"Failed to fetch market news: {e}")
            return []

    async def get_news_for_watchlist(
        self,
        tickers: list[str],
        days_back: int = 3,
    ) -> dict[str, list[NewsArticle]]:
        """Fetch news for all tickers in watchlist."""
        results = {}
        for ticker in tickers:
            articles = await self.get_company_news(ticker, days_back)
            if articles:
                results[ticker] = articles
        return results
