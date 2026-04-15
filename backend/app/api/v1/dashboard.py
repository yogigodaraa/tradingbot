from datetime import datetime

from fastapi import APIRouter

from app.config import settings
from app.schemas import BotSettings, PortfolioOverview

router = APIRouter()


@router.get("/portfolio", response_model=PortfolioOverview)
async def get_portfolio():
    """Get current portfolio overview including positions and P&L."""
    # TODO: Wire to real Alpaca account data
    return PortfolioOverview(
        total_value=100.0,
        cash=100.0,
        positions_value=0.0,
        daily_pnl=0.0,
        daily_pnl_pct=0.0,
        total_pnl=0.0,
        total_pnl_pct=0.0,
        drawdown_pct=0.0,
        positions=[],
        updated_at=datetime.utcnow(),
    )


@router.get("/settings", response_model=BotSettings)
async def get_settings():
    """Get current bot configuration."""
    return BotSettings(
        paper_trading=settings.alpaca_paper,
        max_position_pct=settings.max_position_pct,
        max_open_positions=settings.max_open_positions,
        max_daily_loss_pct=settings.max_daily_loss_pct,
        max_drawdown_pct=settings.max_drawdown_pct,
        min_signal_confidence=settings.min_signal_confidence,
        watchlist=settings.default_watchlist,
    )
