from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Trade
from app.db.session import get_session
from app.schemas import TradeResponse

router = APIRouter()


@router.get("/", response_model=list[TradeResponse])
async def list_trades(
    limit: int = 50,
    ticker: str | None = None,
    session: AsyncSession = Depends(get_session),
):
    """List recent trades, optionally filtered by ticker."""
    query = select(Trade).order_by(Trade.created_at.desc()).limit(limit)
    if ticker:
        query = query.where(Trade.ticker == ticker.upper())
    result = await session.execute(query)
    return result.scalars().all()
