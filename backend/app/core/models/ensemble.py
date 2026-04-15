import logging

import pandas as pd

from app.core.models.base import Prediction, PredictionModel

logger = logging.getLogger(__name__)


class EnsembleModel(PredictionModel):
    """Combines multiple prediction models via weighted voting."""

    def __init__(
        self,
        models: dict[str, PredictionModel],
        weights: dict[str, float] | None = None,
    ):
        self.models = models
        self.weights = weights or {name: 1.0 for name in models}

    def is_trained(self) -> bool:
        return any(m.is_trained() for m in self.models.values())

    async def predict(self, ticker: str, features: pd.DataFrame) -> Prediction:
        """Generate ensemble prediction by combining all sub-models."""
        predictions = []
        total_weight = 0.0

        for name, model in self.models.items():
            if not model.is_trained():
                continue

            pred = await model.predict(ticker, features)
            weight = self.weights.get(name, 1.0)

            # Convert direction to numeric score
            score = pred.confidence if pred.direction == "long" else -pred.confidence
            predictions.append((score * weight, weight, pred))
            total_weight += weight

        if not predictions or total_weight == 0:
            return Prediction(
                ticker=ticker,
                direction="neutral",
                confidence=0.0,
                expected_return=0.0,
                horizon_days=5,
            )

        composite = sum(s for s, _, _ in predictions) / total_weight
        confidence = abs(composite)
        direction = "long" if composite > 0 else "short" if composite < 0 else "neutral"

        # Use the longest horizon from sub-models
        max_horizon = max(p.horizon_days for _, _, p in predictions)

        return Prediction(
            ticker=ticker,
            direction=direction,
            confidence=min(confidence, 1.0),
            expected_return=composite * 0.05,
            horizon_days=max_horizon,
            features_used={"ensemble_score": composite, "num_models": len(predictions)},
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
        """Train all sub-models."""
        results = {}
        for name, model in self.models.items():
            try:
                metrics = await model.train(data)
                results[name] = metrics
            except Exception as e:
                logger.error(f"Failed to train {name}: {e}")
                results[name] = {"error": str(e)}
        return results
