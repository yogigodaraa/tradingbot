from fastapi import APIRouter

from app.api.v1.backtest import router as backtest_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.market import router as market_router
from app.api.v1.news import router as news_router
from app.api.v1.signals import router as signals_router
from app.api.v1.trades import router as trades_router
from app.api.v1.ws import router as ws_router

router = APIRouter()
router.include_router(dashboard_router, prefix="/dashboard", tags=["dashboard"])
router.include_router(market_router, prefix="/market", tags=["market"])
router.include_router(news_router, prefix="/news", tags=["news"])
router.include_router(signals_router, prefix="/signals", tags=["signals"])
router.include_router(trades_router, prefix="/trades", tags=["trades"])
router.include_router(backtest_router, prefix="/backtest", tags=["backtest"])
router.include_router(ws_router, prefix="/ws", tags=["websocket"])
