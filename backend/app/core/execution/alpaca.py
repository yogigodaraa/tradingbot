import logging
from datetime import datetime

from alpaca.trading.client import TradingClient
from alpaca.trading.enums import OrderSide, OrderType, TimeInForce
from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest

from app.config import settings
from app.core.execution.base import (
    AccountInfo,
    Broker,
    OrderRequest,
    OrderResult,
    PositionInfo,
)

logger = logging.getLogger(__name__)


class AlpacaBroker(Broker):
    """Broker implementation using Alpaca Trading API.

    Supports both paper and live trading via config toggle.
    """

    def __init__(self):
        self.client = TradingClient(
            api_key=settings.alpaca_api_key,
            secret_key=settings.alpaca_secret_key,
            paper=settings.alpaca_paper,
        )
        mode = "PAPER" if settings.alpaca_paper else "LIVE"
        logger.info(f"Alpaca broker initialized ({mode})")

    async def submit_order(self, order: OrderRequest) -> OrderResult:
        """Submit an order to Alpaca."""
        side = OrderSide.BUY if order.side == "buy" else OrderSide.SELL

        if order.order_type == "limit" and order.limit_price:
            request = LimitOrderRequest(
                symbol=order.ticker,
                qty=order.quantity,
                side=side,
                limit_price=order.limit_price,
                time_in_force=TimeInForce.DAY,
            )
        else:
            request = MarketOrderRequest(
                symbol=order.ticker,
                qty=order.quantity,
                side=side,
                time_in_force=TimeInForce.DAY,
            )

        try:
            alpaca_order = self.client.submit_order(request)
            logger.info(
                f"Order submitted: {alpaca_order.id} "
                f"{order.side} {order.quantity} {order.ticker}"
            )
            return OrderResult(
                order_id=str(alpaca_order.id),
                ticker=order.ticker,
                side=order.side,
                quantity=order.quantity,
                status=str(alpaca_order.status),
                filled_price=float(alpaca_order.filled_avg_price)
                if alpaca_order.filled_avg_price
                else None,
                filled_at=alpaca_order.filled_at,
            )
        except Exception as e:
            logger.error(f"Order failed: {e}")
            return OrderResult(
                order_id="",
                ticker=order.ticker,
                side=order.side,
                quantity=order.quantity,
                status="rejected",
                message=str(e),
            )

    async def cancel_order(self, order_id: str) -> bool:
        """Cancel a pending order."""
        try:
            self.client.cancel_order_by_id(order_id)
            return True
        except Exception as e:
            logger.error(f"Cancel failed for {order_id}: {e}")
            return False

    async def get_positions(self) -> list[PositionInfo]:
        """Get all open positions from Alpaca."""
        alpaca_positions = self.client.get_all_positions()

        positions = []
        for p in alpaca_positions:
            positions.append(
                PositionInfo(
                    ticker=p.symbol,
                    quantity=float(p.qty),
                    avg_entry_price=float(p.avg_entry_price),
                    current_price=float(p.current_price),
                    market_value=float(p.market_value),
                    unrealized_pnl=float(p.unrealized_pl),
                    unrealized_pnl_pct=float(p.unrealized_plpc),
                    side="long" if float(p.qty) > 0 else "short",
                )
            )
        return positions

    async def get_account(self) -> AccountInfo:
        """Get Alpaca account information."""
        acct = self.client.get_account()
        return AccountInfo(
            equity=float(acct.equity),
            cash=float(acct.cash),
            buying_power=float(acct.buying_power),
            portfolio_value=float(acct.portfolio_value),
            currency=acct.currency or "USD",
        )

    async def get_order_status(self, order_id: str) -> OrderResult:
        """Get current status of an order."""
        order = self.client.get_order_by_id(order_id)
        return OrderResult(
            order_id=str(order.id),
            ticker=order.symbol,
            side="buy" if order.side == OrderSide.BUY else "sell",
            quantity=float(order.qty),
            status=str(order.status),
            filled_price=float(order.filled_avg_price)
            if order.filled_avg_price
            else None,
            filled_at=order.filled_at,
        )
