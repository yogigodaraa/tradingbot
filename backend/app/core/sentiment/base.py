from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class SentimentResult:
    """Result from analyzing a single piece of text."""
    positive: float  # 0-1
    negative: float  # 0-1
    neutral: float   # 0-1
    composite_score: float  # -1 to 1 (negative to positive)
    text: str = ""


@dataclass
class TickerSentiment:
    """Aggregated sentiment for a ticker over a time period."""
    ticker: str
    composite_score: float  # -1 to 1
    num_articles: int
    sentiment_momentum: float  # rate of change
    avg_positive: float
    avg_negative: float
    avg_neutral: float


class SentimentAnalyzer(ABC):
    """Abstract interface for sentiment analysis models."""

    @abstractmethod
    async def analyze(self, text: str) -> SentimentResult:
        """Analyze sentiment of a single text."""
        ...

    @abstractmethod
    async def analyze_batch(self, texts: list[str]) -> list[SentimentResult]:
        """Analyze sentiment of multiple texts."""
        ...
