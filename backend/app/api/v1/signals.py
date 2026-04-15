from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Signal
from app.db.session import get_session
from app.schemas import SignalResponse

router = APIRouter()


@router.get("/", response_model=list[SignalResponse])
async def list_signals(
    limit: int = 50,
    ticker: str | None = None,
    session: AsyncSession = Depends(get_session),
):
    """List recent trading signals, optionally filtered by ticker."""
    query = select(Signal).order_by(Signal.created_at.desc()).limit(limit)
    if ticker:
        query = query.where(Signal.ticker == ticker.upper())
    result = await session.execute(query)
    return result.scalars().all()
