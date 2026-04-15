import logging
from dataclasses import dataclass
from datetime import datetime

from app.core.execution.base import Broker
from app.core.models.base import Prediction, PredictionModel
from app.core.sentiment.base import SentimentAnalyzer, TickerSentiment

logger = logging.getLogger(__name__)


@dataclass
class TradingSignal:
    """A generated trading signal combining model predictions and sentiment."""
    ticker: str
    action: str  # "buy", "sell", "hold"
    strategy: str  # "swing", "longterm"
    confidence: float  # 0-1
    entry_price: float
    stop_loss: float | None = None
    take_profit: float | None = None
    model_prediction: float | None = None
    sentiment_score: float | None = None
    technical_score: float | None = None
    timestamp: datetime | None = None


class SignalGenerator:
    """Combines model predictions, sentiment, and technical analysis into trading signals."""

    def __init__(
        self,
        swing_model: PredictionModel | None = None,
        longterm_model: PredictionModel | None = None,
        sentiment_analyzer: SentimentAnalyzer | None = None,
        min_confidence: float = 0.65,
    ):
        self.swing_model = swing_model
        self.longterm_model = longterm_model
        self.sentiment_analyzer = sentiment_analyzer
        self.min_confidence = min_confidence

        # Weights for combining signals
        self.weights = {
            "model": 0.50,
            "sentiment": 0.30,
            "technical": 0.20,
        }

    async def generate(
        self,
        ticker: str,
        current_price: float,
        prediction: Prediction | None = None,
        sentiment: TickerSentiment | None = None,
        technical_score: float | None = None,
    ) -> TradingSignal | None:
        """Generate a trading signal for a ticker by combining all inputs.

        Returns None if confidence is below threshold.
        """
        scores = []
        weights = []

        # Model prediction score
        model_score = 0.0
        if prediction:
            model_score = prediction.confidence if prediction.direction == "long" else -prediction.confidence
            scores.append(model_score)
            weights.append(self.weights["model"])

        # Sentiment score
        sentiment_score = 0.0
        if sentiment:
            sentiment_score = sentiment.composite_score
            scores.append(sentiment_score)
            weights.append(self.weights["sentiment"])

        # Technical score
        tech_score = 0.0
        if technical_score is not None:
            tech_score = technical_score
            scores.append(tech_score)
            weights.append(self.weights["technical"])

        if not scores:
            return None

        # Weighted composite score
        total_weight = sum(weights)
        composite = sum(s * w for s, w in zip(scores, weights)) / total_weight

        # Determine action
        confidence = abs(composite)
        if confidence < self.min_confidence:
            return None

        if composite > 0:
            action = "buy"
            # Stop loss at 3% below entry, take profit at 2x the risk
            stop_loss = current_price * 0.97
            take_profit = current_price * 1.06
        elif composite < 0:
            action = "sell"
            stop_loss = current_price * 1.03
            take_profit = current_price * 0.94
        else:
            return None

        strategy = "swing"
        if prediction and prediction.horizon_days > 20:
            strategy = "longterm"

        return TradingSignal(
            ticker=ticker,
            action=action,
            strategy=strategy,
            confidence=confidence,
            entry_price=current_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            model_prediction=model_score,
            sentiment_score=sentiment_score,
            technical_score=tech_score,
            timestamp=datetime.utcnow(),
        )
