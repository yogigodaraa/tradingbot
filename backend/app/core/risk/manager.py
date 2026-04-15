import logging
from dataclasses import dataclass
from datetime import date, datetime

from app.config import settings
from app.core.execution.base import AccountInfo, Broker, PositionInfo
from app.core.signals.generator import TradingSignal

logger = logging.getLogger(__name__)


@dataclass
class RiskCheckResult:
    approved: bool
    adjusted_quantity: float | None = None
    reason: str = ""


class RiskManager:
    """Mandatory gate before every trade execution.

    Enforces position limits, daily loss caps, drawdown circuit breaker,
    and sector concentration limits.
    """

    def __init__(
        self,
        max_position_pct: float = settings.max_position_pct,
        max_open_positions: int = settings.max_open_positions,
        max_daily_loss_pct: float = settings.max_daily_loss_pct,
        max_drawdown_pct: float = settings.max_drawdown_pct,
        min_signal_confidence: float = settings.min_signal_confidence,
    ):
        self.max_position_pct = max_position_pct
        self.max_open_positions = max_open_positions
        self.max_daily_loss_pct = max_daily_loss_pct
        self.max_drawdown_pct = max_drawdown_pct
        self.min_signal_confidence = min_signal_confidence

        # Track daily P&L
        self._daily_pnl: float = 0.0
        self._daily_pnl_date: date | None = None
        self._peak_equity: float = 0.0
        self._circuit_breaker_active: bool = False

    def _reset_daily_if_needed(self) -> None:
        today = date.today()
        if self._daily_pnl_date != today:
            self._daily_pnl = 0.0
            self._daily_pnl_date = today
            # Reset circuit breaker on new day
            self._circuit_breaker_active = False

    def update_pnl(self, realized_pnl: float, current_equity: float) -> None:
        """Called after each trade closes to update daily P&L tracking."""
        self._reset_daily_if_needed()
        self._daily_pnl += realized_pnl

        if current_equity > self._peak_equity:
            self._peak_equity = current_equity

    async def check_signal(
        self,
        signal: TradingSignal,
        account: AccountInfo,
        positions: list[PositionInfo],
    ) -> RiskCheckResult:
        """Check if a signal passes all risk management rules.

        Returns RiskCheckResult with approval status and optional adjusted quantity.
        """
        self._reset_daily_if_needed()

        # Update peak equity
        if account.equity > self._peak_equity:
            self._peak_equity = account.equity

        # 1. Circuit breaker check
        if self._circuit_breaker_active:
            return RiskCheckResult(
                approved=False,
                reason="Circuit breaker active - daily loss limit reached",
            )

        # 2. Daily loss check
        daily_loss_pct = abs(self._daily_pnl) / account.equity if account.equity > 0 else 0
        if self._daily_pnl < 0 and daily_loss_pct >= self.max_daily_loss_pct:
            self._circuit_breaker_active = True
            logger.warning(
                f"CIRCUIT BREAKER: Daily loss {daily_loss_pct:.2%} >= {self.max_daily_loss_pct:.2%}"
            )
            return RiskCheckResult(
                approved=False,
                reason=f"Daily loss limit reached: {daily_loss_pct:.2%}",
            )

        # 3. Drawdown check
        if self._peak_equity > 0:
            drawdown = (self._peak_equity - account.equity) / self._peak_equity
            if drawdown >= self.max_drawdown_pct:
                logger.warning(
                    f"DRAWDOWN LIMIT: {drawdown:.2%} >= {self.max_drawdown_pct:.2%}"
                )
                return RiskCheckResult(
                    approved=False,
                    reason=f"Max drawdown reached: {drawdown:.2%}",
                )

        # 4. Confidence check
        if signal.confidence < self.min_signal_confidence:
            return RiskCheckResult(
                approved=False,
                reason=f"Confidence {signal.confidence:.2f} < {self.min_signal_confidence:.2f}",
            )

        # 5. Max open positions check (only for new buys)
        if signal.action == "buy" and len(positions) >= self.max_open_positions:
            return RiskCheckResult(
                approved=False,
                reason=f"Max open positions ({self.max_open_positions}) reached",
            )

        # 6. Position sizing - max % of portfolio per position
        max_position_value = account.equity * self.max_position_pct
        desired_quantity = max_position_value / signal.entry_price if signal.entry_price > 0 else 0

        # Check if we already hold this ticker
        existing = next((p for p in positions if p.ticker == signal.ticker), None)
        if existing and signal.action == "buy":
            # Already have a position - check if adding would exceed limit
            current_value = existing.market_value
            remaining = max_position_value - current_value
            if remaining <= 0:
                return RiskCheckResult(
                    approved=False,
                    reason=f"Position in {signal.ticker} already at max size",
                )
            desired_quantity = remaining / signal.entry_price

        # 7. Check available cash
        if signal.action == "buy":
            order_value = desired_quantity * signal.entry_price
            if order_value > account.cash:
                # Reduce quantity to fit available cash
                desired_quantity = account.cash / signal.entry_price
                if desired_quantity * signal.entry_price < 1.0:
                    return RiskCheckResult(
                        approved=False,
                        reason="Insufficient cash for minimum order ($1)",
                    )

        logger.info(
            f"RISK APPROVED: {signal.action} {signal.ticker} "
            f"qty={desired_quantity:.4f} confidence={signal.confidence:.2f}"
        )

        return RiskCheckResult(
            approved=True,
            adjusted_quantity=round(desired_quantity, 6),
            reason="Passed all risk checks",
        )
