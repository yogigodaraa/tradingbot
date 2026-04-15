from abc import ABC, abstractmethod
from dataclasses import dataclass

import pandas as pd


@dataclass
class Prediction:
    """Output from a prediction model."""
    ticker: str
    direction: str  # "long", "short", "neutral"
    confidence: float  # 0-1
    expected_return: float  # predicted return (e.g. 0.05 = 5%)
    horizon_days: int  # prediction horizon in days
    features_used: dict | None = None  # for interpretability


class PredictionModel(ABC):
    """Abstract interface for prediction models (swing, long-term, etc.)."""

    @abstractmethod
    async def predict(self, ticker: str, features: pd.DataFrame) -> Prediction:
        """Generate a prediction for a ticker given features."""
        ...

    @abstractmethod
    async def predict_batch(
        self, tickers: list[str], features: dict[str, pd.DataFrame]
    ) -> list[Prediction]:
        """Generate predictions for multiple tickers."""
        ...

    @abstractmethod
    def is_trained(self) -> bool:
        """Check if model has been trained."""
        ...

    @abstractmethod
    async def train(self, data: pd.DataFrame) -> dict:
        """Train/retrain the model. Returns training metrics."""
        ...
