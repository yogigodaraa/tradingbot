import numpy as np
import pandas as pd
import ta


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """Build technical indicator features from OHLCV data.

    Args:
        df: DataFrame with columns: open, high, low, close, volume

    Returns:
        DataFrame with original columns plus technical indicator features.
    """
    feat = df.copy()

    # === Trend Indicators ===
    # SMA
    feat["sma_20"] = ta.trend.sma_indicator(feat["close"], window=20)
    feat["sma_50"] = ta.trend.sma_indicator(feat["close"], window=50)
    feat["sma_200"] = ta.trend.sma_indicator(feat["close"], window=200)

    # Price relative to SMAs
    feat["price_vs_sma20"] = feat["close"] / feat["sma_20"] - 1
    feat["price_vs_sma50"] = feat["close"] / feat["sma_50"] - 1
    feat["price_vs_sma200"] = feat["close"] / feat["sma_200"] - 1

    # SMA crossovers
    feat["sma20_above_sma50"] = (feat["sma_20"] > feat["sma_50"]).astype(int)
    feat["sma50_above_sma200"] = (feat["sma_50"] > feat["sma_200"]).astype(int)

    # MACD
    macd = ta.trend.MACD(feat["close"])
    feat["macd"] = macd.macd()
    feat["macd_signal"] = macd.macd_signal()
    feat["macd_histogram"] = macd.macd_diff()

    # ADX (trend strength)
    feat["adx"] = ta.trend.adx(feat["high"], feat["low"], feat["close"])

    # === Momentum Indicators ===
    # RSI
    feat["rsi_14"] = ta.momentum.rsi(feat["close"], window=14)

    # Stochastic
    stoch = ta.momentum.StochasticOscillator(feat["high"], feat["low"], feat["close"])
    feat["stoch_k"] = stoch.stoch()
    feat["stoch_d"] = stoch.stoch_signal()

    # ROC (Rate of Change)
    feat["roc_5"] = ta.momentum.roc(feat["close"], window=5)
    feat["roc_10"] = ta.momentum.roc(feat["close"], window=10)
    feat["roc_20"] = ta.momentum.roc(feat["close"], window=20)

    # === Volatility Indicators ===
    # Bollinger Bands
    bb = ta.volatility.BollingerBands(feat["close"])
    feat["bb_upper"] = bb.bollinger_hband()
    feat["bb_lower"] = bb.bollinger_lband()
    feat["bb_width"] = bb.bollinger_wband()
    feat["bb_pct"] = bb.bollinger_pband()

    # ATR
    feat["atr_14"] = ta.volatility.average_true_range(
        feat["high"], feat["low"], feat["close"], window=14
    )
    feat["atr_pct"] = feat["atr_14"] / feat["close"]

    # === Volume Indicators ===
    feat["volume_sma_20"] = ta.trend.sma_indicator(feat["volume"], window=20)
    feat["volume_ratio"] = feat["volume"] / feat["volume_sma_20"]

    # OBV
    feat["obv"] = ta.volume.on_balance_volume(feat["close"], feat["volume"])

    # === Returns ===
    feat["return_1d"] = feat["close"].pct_change(1)
    feat["return_5d"] = feat["close"].pct_change(5)
    feat["return_10d"] = feat["close"].pct_change(10)
    feat["return_20d"] = feat["close"].pct_change(20)

    # Volatility (rolling std of returns)
    feat["volatility_20d"] = feat["return_1d"].rolling(20).std()

    # === Calendar Features ===
    if "timestamp" in feat.columns:
        ts = pd.to_datetime(feat["timestamp"])
        feat["day_of_week"] = ts.dt.dayofweek
        feat["month"] = ts.dt.month

    # Drop NaN rows from indicator warm-up
    return feat
