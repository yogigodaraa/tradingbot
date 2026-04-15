import logging

import numpy as np
import pandas as pd

from app.core.models.base import Prediction, PredictionModel
from app.core.models.features import build_features

logger = logging.getLogger(__name__)


class LongTermFactorModel(PredictionModel):
    """Factor-based ranking model for long-term positions (weeks to months).

    Uses momentum + mean-reversion + volatility factors to rank stocks.
    No ML training needed - purely rule-based quantitative factors.
    """

    def __init__(self, horizon_days: int = 30):
        self.horizon_days = horizon_days
        self._trained = True  # No training needed for factor model

    def is_trained(self) -> bool:
        return True

    async def predict(self, ticker: str, features: pd.DataFrame) -> Prediction:
        """Score a ticker using quantitative factors."""
        if len(features) < 200:
            return Prediction(
                ticker=ticker,
                direction="neutral",
                confidence=0.0,
                expected_return=0.0,
                horizon_days=self.horizon_days,
            )

        latest = features.iloc[-1]
        scores = []

        # Factor 1: Momentum (20-day return)
        # Positive momentum is bullish
        roc20 = latest.get("roc_20", 0)
        if roc20 is not None and not np.isnan(roc20):
            momentum_score = np.clip(roc20 / 20, -1, 1)  # normalize
            scores.append(("momentum", momentum_score, 0.30))

        # Factor 2: Trend alignment (price above SMAs)
        trend_score = 0
        above_sma20 = latest.get("price_vs_sma20", 0)
        above_sma50 = latest.get("price_vs_sma50", 0)
        above_sma200 = latest.get("price_vs_sma200", 0)
        if not any(np.isnan(x) for x in [above_sma20, above_sma50, above_sma200]):
            trend_score = (
                (1 if above_sma20 > 0 else -1) * 0.2 +
                (1 if above_sma50 > 0 else -1) * 0.3 +
                (1 if above_sma200 > 0 else -1) * 0.5
            )
        scores.append(("trend", trend_score, 0.25))

        # Factor 3: RSI mean reversion
        # Oversold (RSI < 30) is bullish, overbought (RSI > 70) is bearish
        rsi = latest.get("rsi_14", 50)
        if rsi is not None and not np.isnan(rsi):
            rsi_score = (50 - rsi) / 50  # -1 to 1
            scores.append(("rsi_reversion", rsi_score, 0.15))

        # Factor 4: Volatility (lower vol preferred for long-term)
        vol = latest.get("volatility_20d", 0)
        if vol is not None and not np.isnan(vol) and vol > 0:
            vol_score = np.clip(1 - vol * 50, -1, 1)  # penalize high vol
            scores.append(("low_vol", vol_score, 0.15))

        # Factor 5: Volume confirmation
        vol_ratio = latest.get("volume_ratio", 1)
        if vol_ratio is not None and not np.isnan(vol_ratio):
            # Above-average volume on up moves is bullish
            ret_1d = latest.get("return_1d", 0)
            if ret_1d > 0 and vol_ratio > 1.2:
                vol_confirm = 0.5
            elif ret_1d < 0 and vol_ratio > 1.5:
                vol_confirm = -0.5
            else:
                vol_confirm = 0.0
            scores.append(("volume_confirm", vol_confirm, 0.15))

        if not scores:
            return Prediction(
                ticker=ticker,
                direction="neutral",
                confidence=0.0,
                expected_return=0.0,
                horizon_days=self.horizon_days,
            )

        # Weighted composite
        total_weight = sum(w for _, _, w in scores)
        composite = sum(s * w for _, s, w in scores) / total_weight

        confidence = abs(composite)
        direction = "long" if composite > 0 else "short" if composite < 0 else "neutral"

        return Prediction(
            ticker=ticker,
            direction=direction,
            confidence=min(confidence, 1.0),
            expected_return=composite * 0.05,
            horizon_days=self.horizon_days,
            features_used={name: float(score) for name, score, _ in scores},
        )

    async def predict_batch(
        self, tickers: list[str], features: dict[str, pd.DataFrame]
    ) -> list[Prediction]:
        results = []
        for ticker in tickers:
            if ticker in features:
                pred = await self.predict(ticker, features[ticker])
                results.append(pred)
        return results

    async def train(self, data: pd.DataFrame) -> dict:
        """Factor model doesn't need training - returns stats instead."""
        return {
            "model_type": "factor_ranking",
            "factors": ["momentum", "trend", "rsi_reversion", "low_vol", "volume_confirm"],
            "horizon_days": self.horizon_days,
            "note": "Rule-based factor model, no training required",
        }
