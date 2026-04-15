import logging
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import TimeSeriesSplit
from xgboost import XGBClassifier

from app.core.models.base import Prediction, PredictionModel
from app.core.models.features import build_features

logger = logging.getLogger(__name__)

MODEL_PATH = Path(__file__).parent.parent.parent.parent / "ml" / "models" / "swing_xgb.joblib"

# Features used by the model (subset of what build_features produces)
FEATURE_COLS = [
    "rsi_14", "macd", "macd_histogram", "adx",
    "bb_width", "bb_pct", "atr_pct",
    "price_vs_sma20", "price_vs_sma50", "price_vs_sma200",
    "sma20_above_sma50", "sma50_above_sma200",
    "stoch_k", "stoch_d",
    "roc_5", "roc_10", "roc_20",
    "volume_ratio", "volatility_20d",
    "return_1d", "return_5d",
]


class SwingTradingModel(PredictionModel):
    """XGBoost classifier for swing trading signals (5-day horizon).

    Predicts: Will the price be higher in 5 trading days? (binary)
    Features: Technical indicators + sentiment scores
    """

    def __init__(self, horizon_days: int = 5):
        self.horizon_days = horizon_days
        self.model: XGBClassifier | None = None
        self._trained = False

        # Try to load existing model
        if MODEL_PATH.exists():
            try:
                self.model = joblib.load(MODEL_PATH)
                self._trained = True
                logger.info(f"Loaded swing model from {MODEL_PATH}")
            except Exception as e:
                logger.warning(f"Failed to load model: {e}")

    def is_trained(self) -> bool:
        return self._trained

    async def predict(self, ticker: str, features: pd.DataFrame) -> Prediction:
        """Predict direction for next N days."""
        if not self._trained or self.model is None:
            return Prediction(
                ticker=ticker,
                direction="neutral",
                confidence=0.0,
                expected_return=0.0,
                horizon_days=self.horizon_days,
            )

        # Use latest row of features
        row = features[FEATURE_COLS].iloc[-1:].values

        # Get probability
        proba = self.model.predict_proba(row)[0]
        # proba[0] = P(down), proba[1] = P(up)
        prob_up = proba[1]

        if prob_up > 0.5:
            direction = "long"
            confidence = prob_up
        else:
            direction = "short"
            confidence = 1 - prob_up

        return Prediction(
            ticker=ticker,
            direction=direction,
            confidence=confidence,
            expected_return=(prob_up - 0.5) * 0.1,  # rough estimate
            horizon_days=self.horizon_days,
            features_used={col: float(features[col].iloc[-1]) for col in FEATURE_COLS[:5]},
        )

    async def predict_batch(
        self, tickers: list[str], features: dict[str, pd.DataFrame]
    ) -> list[Prediction]:
        """Predict for multiple tickers."""
        results = []
        for ticker in tickers:
            if ticker in features:
                pred = await self.predict(ticker, features[ticker])
                results.append(pred)
        return results

    async def train(self, data: pd.DataFrame) -> dict:
        """Train the XGBoost swing model.

        Args:
            data: OHLCV DataFrame. Will compute features and labels internally.

        Returns:
            Training metrics dict.
        """
        logger.info("Training swing model...")

        # Build features
        feat = build_features(data)

        # Create labels: 1 if price is higher in N days, 0 otherwise
        feat["target"] = (
            feat["close"].shift(-self.horizon_days) > feat["close"]
        ).astype(int)

        # Drop NaN
        feat = feat.dropna(subset=FEATURE_COLS + ["target"])

        X = feat[FEATURE_COLS].values
        y = feat["target"].values

        if len(X) < 100:
            raise ValueError(f"Not enough data to train: {len(X)} samples")

        # Time series cross-validation
        tscv = TimeSeriesSplit(n_splits=5)
        scores = []

        for train_idx, val_idx in tscv.split(X):
            X_train, X_val = X[train_idx], X[val_idx]
            y_train, y_val = y[train_idx], y[val_idx]

            model = XGBClassifier(
                n_estimators=200,
                max_depth=5,
                learning_rate=0.05,
                subsample=0.8,
                colsample_bytree=0.8,
                eval_metric="logloss",
                random_state=42,
            )
            model.fit(
                X_train, y_train,
                eval_set=[(X_val, y_val)],
                verbose=False,
            )
            score = model.score(X_val, y_val)
            scores.append(score)

        # Train final model on all data
        self.model = XGBClassifier(
            n_estimators=200,
            max_depth=5,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            eval_metric="logloss",
            random_state=42,
        )
        self.model.fit(X, y, verbose=False)
        self._trained = True

        # Save model
        MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.model, MODEL_PATH)
        logger.info(f"Swing model saved to {MODEL_PATH}")

        # Feature importance
        importances = dict(zip(FEATURE_COLS, self.model.feature_importances_))
        top_features = sorted(importances.items(), key=lambda x: x[1], reverse=True)[:10]

        metrics = {
            "cv_accuracy_mean": float(np.mean(scores)),
            "cv_accuracy_std": float(np.std(scores)),
            "num_samples": len(X),
            "num_features": len(FEATURE_COLS),
            "horizon_days": self.horizon_days,
            "top_features": {k: float(v) for k, v in top_features},
        }

        logger.info(f"Training complete: accuracy={metrics['cv_accuracy_mean']:.4f}")
        return metrics
