import logging
import math
from datetime import datetime, timedelta

from app.core.sentiment.base import SentimentResult, TickerSentiment
from app.core.sentiment.finbert import FinBERTAnalyzer
from app.core.sentiment.news_fetcher import NewsFetcher, NewsArticle

logger = logging.getLogger(__name__)


class SentimentScorer:
    """Combines news fetching and FinBERT analysis into composite sentiment scores.

    Features:
    - Exponential decay weighting (recent news matters more)
    - Source credibility weighting
    - Sentiment momentum (rate of change)
    """

    # Source credibility weights (higher = more trustworthy)
    SOURCE_WEIGHTS = {
        "reuters": 1.0,
        "bloomberg": 1.0,
        "cnbc": 0.9,
        "wsj": 1.0,
        "ft": 1.0,
        "marketwatch": 0.8,
        "seekingalpha": 0.6,
        "benzinga": 0.7,
        "yahoo": 0.7,
    }

    def __init__(
        self,
        news_fetcher: NewsFetcher,
        analyzer: FinBERTAnalyzer,
        decay_hours: float = 48.0,
    ):
        self.news = news_fetcher
        self.analyzer = analyzer
        self.decay_hours = decay_hours

    def _source_weight(self, source: str) -> float:
        source_lower = source.lower()
        for key, weight in self.SOURCE_WEIGHTS.items():
            if key in source_lower:
                return weight
        return 0.5  # default for unknown sources

    def _recency_weight(self, published_at: datetime) -> float:
        """Exponential decay: recent articles weighted more heavily."""
        hours_ago = (datetime.utcnow() - published_at).total_seconds() / 3600
        return math.exp(-hours_ago / self.decay_hours)

    async def score_ticker(
        self,
        ticker: str,
        days_back: int = 3,
    ) -> TickerSentiment | None:
        """Compute composite sentiment for a ticker.

        1. Fetch news articles
        2. Analyze each with FinBERT
        3. Weight by recency and source credibility
        4. Return aggregated score
        """
        articles = await self.news.get_company_news(ticker, days_back)

        if not articles:
            return None

        # Analyze all headlines + summaries
        texts = [
            f"{a.headline}. {a.summary}" if a.summary else a.headline
            for a in articles
        ]
        sentiments = await self.analyzer.analyze_batch(texts)

        # Compute weighted composite
        weighted_scores = []
        total_weight = 0.0

        for article, sentiment in zip(articles, sentiments):
            w = self._recency_weight(article.published_at) * self._source_weight(article.source)
            weighted_scores.append(sentiment.composite_score * w)
            total_weight += w

        if total_weight == 0:
            return None

        composite = sum(weighted_scores) / total_weight

        # Calculate momentum (compare first half vs second half of articles)
        mid = len(sentiments) // 2
        if mid > 0:
            old_avg = sum(s.composite_score for s in sentiments[:mid]) / mid
            new_avg = sum(s.composite_score for s in sentiments[mid:]) / (len(sentiments) - mid)
            momentum = new_avg - old_avg
        else:
            momentum = 0.0

        return TickerSentiment(
            ticker=ticker,
            composite_score=max(-1.0, min(1.0, composite)),
            num_articles=len(articles),
            sentiment_momentum=momentum,
            avg_positive=sum(s.positive for s in sentiments) / len(sentiments),
            avg_negative=sum(s.negative for s in sentiments) / len(sentiments),
            avg_neutral=sum(s.neutral for s in sentiments) / len(sentiments),
        )

    async def score_watchlist(
        self,
        tickers: list[str],
        days_back: int = 3,
    ) -> dict[str, TickerSentiment]:
        """Score sentiment for all tickers in watchlist."""
        results = {}
        for ticker in tickers:
            try:
                score = await self.score_ticker(ticker, days_back)
                if score:
                    results[ticker] = score
            except Exception as e:
                logger.error(f"Sentiment scoring failed for {ticker}: {e}")
        return results
