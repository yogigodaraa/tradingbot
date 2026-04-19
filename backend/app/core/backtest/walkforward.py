"""Walk-forward backtesting — the correct way to evaluate a trading strategy.

A single train/test split dramatically overstates performance: once you
tune on the test set, you've leaked information into the model. Walk-
forward validation slides a training window across the series and
evaluates on the *next* window, rolling forward. The aggregate of the
out-of-sample folds is the honest performance estimate.

Two scheme variants are supported:

1. **Anchored (expanding)** — training window grows over time. Good for
   strategies that benefit from more data and don't face non-stationarity.
2. **Rolling (sliding)** — training window has fixed size. Correct choice
   when market regimes change (volatility clusters, macro shifts).

Both emit per-fold metrics plus an aggregate.

References:
    - Pardo, R. (1992). *Design, Testing, and Optimization of Trading Systems.*
    - López de Prado (2018). *Advances in Financial Machine Learning* Ch. 11
      (Backtest Statistics / Overfitting).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable

import numpy as np
import pandas as pd

from app.core.backtest.metrics import BacktestMetrics


@dataclass
class WalkForwardFold:
    """Results from one fold of walk-forward validation."""

    fold_index: int
    train_start: datetime
    train_end: datetime
    test_start: datetime
    test_end: datetime
    metrics: BacktestMetrics
    train_size: int
    test_size: int


@dataclass
class WalkForwardReport:
    """Aggregate of a walk-forward run — the honest view of strategy skill."""

    folds: list[WalkForwardFold] = field(default_factory=list)
    aggregate: BacktestMetrics | None = None
    scheme: str = "rolling"
    train_window_days: int = 252
    test_window_days: int = 63

    @property
    def fold_sharpes(self) -> list[float]:
        return [f.metrics.sharpe_ratio for f in self.folds]

    @property
    def stability(self) -> float:
        """Sharpe stability = mean(sharpe) / std(sharpe) across folds.

        High value (>1.5) = consistent skill. Low value = skill comes
        from a few lucky folds and will likely decay live.
        """
        s = self.fold_sharpes
        if len(s) < 2:
            return 0.0
        sd = float(np.std(s))
        return float(np.mean(s)) / sd if sd else 0.0

    def to_dict(self) -> dict:
        return {
            "scheme": self.scheme,
            "train_window_days": self.train_window_days,
            "test_window_days": self.test_window_days,
            "folds": [
                {
                    "fold_index": f.fold_index,
                    "train": [f.train_start.isoformat(), f.train_end.isoformat()],
                    "test": [f.test_start.isoformat(), f.test_end.isoformat()],
                    "train_size": f.train_size,
                    "test_size": f.test_size,
                    "metrics": f.metrics.to_dict() if hasattr(f.metrics, "to_dict") else vars(f.metrics),
                }
                for f in self.folds
            ],
            "aggregate": (
                self.aggregate.to_dict() if self.aggregate and hasattr(self.aggregate, "to_dict") else None
            ),
            "stability": round(self.stability, 3),
            "fold_count": len(self.folds),
        }


BacktestFn = Callable[[pd.DataFrame, pd.DataFrame], BacktestMetrics]
"""Callable that takes (train_df, test_df) and returns BacktestMetrics for the test window."""


def walk_forward(
    data: pd.DataFrame,
    backtest_fn: BacktestFn,
    *,
    train_window_days: int = 252,
    test_window_days: int = 63,
    scheme: str = "rolling",
    step_days: int | None = None,
    min_folds: int = 3,
) -> WalkForwardReport:
    """Run walk-forward validation over a time-indexed DataFrame.

    Args:
        data: Time-indexed DataFrame. Index must be datetime-like.
        backtest_fn: Callable that runs a strategy on (train, test) and
            returns BacktestMetrics for the test window. The strategy
            may train models on `train` but must NOT peek at `test`.
        train_window_days: Calendar-day width of the training window.
        test_window_days: Calendar-day width of the out-of-sample test window.
        scheme: ``"rolling"`` (fixed-size training window) or
            ``"anchored"`` (expanding training window from the beginning).
        step_days: Days to advance the window per fold. Defaults to
            ``test_window_days`` (non-overlapping test windows).
        min_folds: Raise if the series is too short to produce this many folds.

    Returns:
        WalkForwardReport with per-fold metrics + aggregate + stability.
    """
    if step_days is None:
        step_days = test_window_days

    if not isinstance(data.index, pd.DatetimeIndex):
        raise ValueError("data.index must be a DatetimeIndex for walk-forward backtesting")
    if data.empty:
        raise ValueError("data is empty")

    folds: list[WalkForwardFold] = []
    start = data.index.min()
    end = data.index.max()
    cursor = start + pd.Timedelta(days=train_window_days)
    fold_idx = 0

    while cursor + pd.Timedelta(days=test_window_days) <= end:
        train_end = cursor
        train_start = (
            start if scheme == "anchored" else cursor - pd.Timedelta(days=train_window_days)
        )
        test_start = cursor
        test_end = cursor + pd.Timedelta(days=test_window_days)

        train = data.loc[train_start:train_end]
        test = data.loc[test_start:test_end]
        if len(train) < 20 or len(test) < 5:
            cursor += pd.Timedelta(days=step_days)
            continue

        metrics = backtest_fn(train, test)
        folds.append(
            WalkForwardFold(
                fold_index=fold_idx,
                train_start=train_start.to_pydatetime() if hasattr(train_start, "to_pydatetime") else train_start,
                train_end=train_end.to_pydatetime() if hasattr(train_end, "to_pydatetime") else train_end,
                test_start=test_start.to_pydatetime() if hasattr(test_start, "to_pydatetime") else test_start,
                test_end=test_end.to_pydatetime() if hasattr(test_end, "to_pydatetime") else test_end,
                metrics=metrics,
                train_size=len(train),
                test_size=len(test),
            )
        )
        fold_idx += 1
        cursor += pd.Timedelta(days=step_days)

    if len(folds) < min_folds:
        raise ValueError(
            f"Only {len(folds)} folds produced (need ≥ {min_folds}). "
            f"Shorten the window or lengthen the data."
        )

    # Aggregate = equal-weight average across folds (simple, defensible)
    agg = _aggregate_metrics([f.metrics for f in folds])

    return WalkForwardReport(
        folds=folds,
        aggregate=agg,
        scheme=scheme,
        train_window_days=train_window_days,
        test_window_days=test_window_days,
    )


def _aggregate_metrics(metrics: list[BacktestMetrics]) -> BacktestMetrics:
    """Equal-weight averaging of per-fold BacktestMetrics.

    We try to stay duck-typed — copy every attribute the source type
    exposes, assuming it's either a numeric scalar (average it) or a
    list / dict (pass through from the last fold).
    """
    if not metrics:
        raise ValueError("empty metrics list")

    # Get a template from the first instance.
    template = metrics[0]
    try:
        fields = list(vars(template).keys())
    except TypeError:
        # dataclass fields
        from dataclasses import fields as _fields

        fields = [f.name for f in _fields(template)]

    aggregated: dict = {}
    for field_name in fields:
        values = [getattr(m, field_name, None) for m in metrics]
        numeric = [v for v in values if isinstance(v, (int, float)) and not isinstance(v, bool)]
        if numeric and len(numeric) == len(values):
            aggregated[field_name] = float(np.mean(numeric))
        else:
            aggregated[field_name] = values[-1]

    # Rebuild. BacktestMetrics is typically a dataclass.
    return type(template)(**aggregated)
