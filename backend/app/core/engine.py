import asyncio
import logging
from datetime import datetime

from app.core.data.base import DataProvider
from app.core.execution.base import Broker, OrderRequest
from app.core.models.base import PredictionModel
from app.core.risk.manager import RiskManager
from app.core.sentiment.base import SentimentAnalyzer, TickerSentiment
from app.core.signals.generator import SignalGenerator, TradingSignal

logger = logging.getLogger(__name__)


class TradingEngine:
    """Main orchestrator that wires together all components.

    Flow: Data -> Features -> Predictions -> Signals -> Risk Check -> Execution
    """

    def __init__(
        self,
        data_provider: DataProvider,
        broker: Broker,
        signal_generator: SignalGenerator,
        risk_manager: RiskManager,
        sentiment_analyzer: SentimentAnalyzer | None = None,
        swing_model: PredictionModel | None = None,
        longterm_model: PredictionModel | None = None,
        watchlist: list[str] | None = None,
    ):
        self.data = data_provider
        self.broker = broker
        self.signals = signal_generator
        self.risk = risk_manager
        self.sentiment = sentiment_analyzer
        self.swing_model = swing_model
        self.longterm_model = longterm_model
        self.watchlist = watchlist or []

        self._running = False
        self._last_scan: datetime | None = None

    async def start(self) -> None:
        """Start the trading engine."""
        self._running = True
        logger.info(f"Trading engine started. Watching {len(self.watchlist)} tickers.")

    async def stop(self) -> None:
        """Stop the trading engine gracefully."""
        self._running = False
        logger.info("Trading engine stopped.")

    async def scan_watchlist(self) -> list[TradingSignal]:
        """Run a full scan of the watchlist: fetch data, analyze, generate signals.

        This is the main loop iteration - called by the scheduler.
        """
        if not self._running:
            return []

        logger.info(f"Scanning {len(self.watchlist)} tickers...")
        signals = []

        # Get current account state
        account = await self.broker.get_account()
        positions = await self.broker.get_positions()

        # Get latest prices for all tickers
        prices = await self.data.get_latest_prices(self.watchlist)

        for ticker in self.watchlist:
            try:
                price = prices.get(ticker)
                if not price:
                    continue

                # Get sentiment if available
                sentiment: TickerSentiment | None = None
                # TODO: Wire to sentiment scorer

                # Get model predictions if models are trained
                prediction = None
                if self.swing_model and self.swing_model.is_trained():
                    # TODO: Build features and predict
                    pass

                # Generate signal
                signal = await self.signals.generate(
                    ticker=ticker,
                    current_price=price,
                    prediction=prediction,
                    sentiment=sentiment,
                )

                if signal:
                    signals.append(signal)
                    logger.info(
                        f"Signal: {signal.action} {signal.ticker} "
                        f"@ ${signal.entry_price:.2f} conf={signal.confidence:.2f}"
                    )

            except Exception as e:
                logger.error(f"Error scanning {ticker}: {e}")

        # Process approved signals
        executed = 0
        for signal in signals:
            try:
                result = await self.risk.check_signal(signal, account, positions)

                if result.approved and result.adjusted_quantity:
                    await self._execute_signal(signal, result.adjusted_quantity)
                    executed += 1
                else:
                    logger.info(f"Signal rejected for {signal.ticker}: {result.reason}")

            except Exception as e:
                logger.error(f"Error executing signal for {signal.ticker}: {e}")

        self._last_scan = datetime.utcnow()
        logger.info(
            f"Scan complete: {len(signals)} signals, {executed} executed"
        )

        return signals

    async def _execute_signal(self, signal: TradingSignal, quantity: float) -> None:
        """Execute a trading signal through the broker."""
        order = OrderRequest(
            ticker=signal.ticker,
            quantity=quantity,
            side=signal.action,
            order_type="market",
            time_in_force="day",
        )

        result = await self.broker.submit_order(order)
        logger.info(
            f"Order submitted: {result.order_id} {signal.action} "
            f"{quantity:.4f} {signal.ticker} -> {result.status}"
        )

        # TODO: Save trade to database, link to signal

    @property
    def status(self) -> dict:
        return {
            "running": self._running,
            "watchlist_size": len(self.watchlist),
            "last_scan": self._last_scan.isoformat() if self._last_scan else None,
        }
