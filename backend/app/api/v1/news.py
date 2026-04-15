import logging
from datetime import datetime

from fastapi import APIRouter, Query

from app.config import settings
from app.core.sentiment.finbert import FinBERTAnalyzer
from app.core.sentiment.news_fetcher import NewsFetcher

logger = logging.getLogger(__name__)
router = APIRouter()

_news_fetcher: NewsFetcher | None = None
_analyzer: FinBERTAnalyzer | None = None


def get_news_fetcher() -> NewsFetcher:
    global _news_fetcher
    if _news_fetcher is None:
        _news_fetcher = NewsFetcher()
    return _news_fetcher


def get_analyzer() -> FinBERTAnalyzer:
    global _analyzer
    if _analyzer is None:
        _analyzer = FinBERTAnalyzer()
    return _analyzer


@router.get("/feed")
async def get_news_feed(
    ticker: str = Query(default=None, description="Filter by ticker (e.g. AAPL)"),
    limit: int = Query(default=20, ge=1, le=100),
    analyze: bool = Query(default=True, description="Run FinBERT sentiment analysis"),
):
    """Get live news feed with optional FinBERT sentiment analysis.

    Shows real financial news and how AI scores each article as bullish/bearish/neutral.
    """
    fetcher = get_news_fetcher()

    if ticker:
        articles = await fetcher.get_company_news(ticker.upper(), days_back=3)
    else:
        # Get news for top tickers from watchlist
        articles = []
        for t in settings.default_watchlist[:10]:
            company_news = await fetcher.get_company_news(t, days_back=2)
            articles.extend(company_news[:3])  # 3 per ticker to stay in rate limits

    # Sort by date, newest first
    articles.sort(key=lambda a: a.published_at, reverse=True)
    articles = articles[:limit]

    results = []
    if analyze and articles:
        analyzer = get_analyzer()
        texts = [
            f"{a.headline}. {a.summary}" if a.summary else a.headline
            for a in articles
        ]
        sentiments = await analyzer.analyze_batch(texts)

        for article, sentiment in zip(articles, sentiments):
            # Determine label
            if sentiment.composite_score > 0.2:
                label = "bullish"
            elif sentiment.composite_score < -0.2:
                label = "bearish"
            else:
                label = "neutral"

            results.append({
                "headline": article.headline,
                "summary": article.summary[:300] if article.summary else "",
                "source": article.source,
                "url": article.url,
                "ticker": article.ticker,
                "published_at": article.published_at.isoformat(),
                "sentiment": {
                    "label": label,
                    "score": round(sentiment.composite_score, 3),
                    "positive": round(sentiment.positive, 3),
                    "negative": round(sentiment.negative, 3),
                    "neutral": round(sentiment.neutral, 3),
                },
            })
    else:
        for article in articles:
            results.append({
                "headline": article.headline,
                "summary": article.summary[:300] if article.summary else "",
                "source": article.source,
                "url": article.url,
                "ticker": article.ticker,
                "published_at": article.published_at.isoformat(),
                "sentiment": None,
            })

    return {
        "articles": results,
        "count": len(results),
        "analyzed": analyze,
        "updated_at": datetime.utcnow().isoformat(),
    }


@router.get("/sentiment/{ticker}")
async def get_ticker_sentiment(
    ticker: str,
    days: int = Query(default=3, ge=1, le=7),
):
    """Get aggregated sentiment analysis for a specific ticker.

    Shows overall sentiment, article count, and individual article scores.
    """
    fetcher = get_news_fetcher()
    analyzer = get_analyzer()

    articles = await fetcher.get_company_news(ticker.upper(), days_back=days)

    if not articles:
        return {
            "ticker": ticker.upper(),
            "overall_sentiment": "neutral",
            "overall_score": 0.0,
            "article_count": 0,
            "articles": [],
        }

    texts = [
        f"{a.headline}. {a.summary}" if a.summary else a.headline
        for a in articles
    ]
    sentiments = await analyzer.analyze_batch(texts)

    # Aggregate
    total_score = sum(s.composite_score for s in sentiments) / len(sentiments)

    if total_score > 0.15:
        overall = "bullish"
    elif total_score < -0.15:
        overall = "bearish"
    else:
        overall = "neutral"

    article_details = []
    for article, sentiment in zip(articles, sentiments):
        if sentiment.composite_score > 0.2:
            label = "bullish"
        elif sentiment.composite_score < -0.2:
            label = "bearish"
        else:
            label = "neutral"

        article_details.append({
            "headline": article.headline,
            "source": article.source,
            "published_at": article.published_at.isoformat(),
            "label": label,
            "score": round(sentiment.composite_score, 3),
        })

    return {
        "ticker": ticker.upper(),
        "overall_sentiment": overall,
        "overall_score": round(total_score, 3),
        "article_count": len(articles),
        "articles": article_details,
        "analyzed_at": datetime.utcnow().isoformat(),
    }


@router.get("/impact")
async def get_news_impact(
    ticker: str = Query(description="Ticker to analyze (e.g. AAPL)"),
):
    """Show how recent news correlates with price movement for a ticker.

    Combines news sentiment timeline with price data to visualize impact.
    """
    from app.core.data.alpaca import AlpacaDataProvider
    from datetime import timedelta

    fetcher = get_news_fetcher()
    analyzer = get_analyzer()
    data_provider = AlpacaDataProvider()

    # Get news
    articles = await fetcher.get_company_news(ticker.upper(), days_back=7)

    # Get price data
    end = datetime.utcnow()
    start = end - timedelta(days=7)
    df = await data_provider.get_bars(ticker=ticker.upper(), timeframe="1d", start=start, end=end)

    # Analyze news
    news_timeline = []
    if articles:
        texts = [
            f"{a.headline}. {a.summary}" if a.summary else a.headline
            for a in articles
        ]
        sentiments = await analyzer.analyze_batch(texts)

        for article, sentiment in zip(articles, sentiments):
            news_timeline.append({
                "date": article.published_at.strftime("%Y-%m-%d"),
                "headline": article.headline,
                "sentiment_score": round(sentiment.composite_score, 3),
                "source": article.source,
            })

    # Price timeline
    price_timeline = []
    if not df.empty:
        for _, row in df.iterrows():
            price_timeline.append({
                "date": str(row.get("timestamp", ""))[:10],
                "close": round(float(row["close"]), 2),
                "volume": int(row["volume"]),
            })

    # Daily sentiment average
    from collections import defaultdict
    daily_sentiment = defaultdict(list)
    for n in news_timeline:
        daily_sentiment[n["date"]].append(n["sentiment_score"])

    sentiment_by_day = [
        {
            "date": date,
            "avg_sentiment": round(sum(scores) / len(scores), 3),
            "article_count": len(scores),
        }
        for date, scores in sorted(daily_sentiment.items())
    ]

    return {
        "ticker": ticker.upper(),
        "price_timeline": price_timeline,
        "news_timeline": news_timeline,
        "sentiment_by_day": sentiment_by_day,
        "summary": {
            "total_articles": len(articles),
            "avg_sentiment": round(
                sum(n["sentiment_score"] for n in news_timeline) / len(news_timeline), 3
            ) if news_timeline else 0,
            "price_change_7d": round(
                ((price_timeline[-1]["close"] - price_timeline[0]["close"]) / price_timeline[0]["close"]) * 100, 2
            ) if len(price_timeline) >= 2 else 0,
        },
    }
