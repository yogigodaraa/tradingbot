"""Tests for RiskManager, the mandatory gate in front of every order.

Each test exercises one rule in `RiskManager.check_signal`, in the order the rules run.
Limits are passed explicitly so the tests don't depend on `.env` values.
"""

from datetime import date

import pytest

from app.core.execution.base import AccountInfo, PositionInfo
from app.core.risk import manager as manager_module
from app.core.risk.manager import RiskManager
from app.core.signals.generator import TradingSignal


def make_manager(**overrides) -> RiskManager:
    limits = dict(
        max_position_pct=0.20,
        max_open_positions=5,
        max_daily_loss_pct=0.03,
        max_drawdown_pct=0.10,
        min_signal_confidence=0.65,
    )
    limits.update(overrides)
    return RiskManager(**limits)


def make_signal(action="buy", ticker="AAPL", confidence=0.8, entry_price=100.0) -> TradingSignal:
    return TradingSignal(
        ticker=ticker,
        action=action,
        strategy="swing",
        confidence=confidence,
        entry_price=entry_price,
    )


def make_account(equity=10_000.0, cash=10_000.0) -> AccountInfo:
    return AccountInfo(equity=equity, cash=cash, buying_power=cash, portfolio_value=equity)


def make_position(ticker="MSFT", market_value=1_000.0) -> PositionInfo:
    return PositionInfo(
        ticker=ticker,
        quantity=10,
        avg_entry_price=100.0,
        current_price=market_value / 10,
        market_value=market_value,
        unrealized_pnl=0.0,
        unrealized_pnl_pct=0.0,
        side="long",
    )


async def test_approves_valid_buy_sized_to_max_position_pct():
    result = await make_manager().check_signal(make_signal(), make_account(), [])

    assert result.approved
    # 20% of $10,000 equity at $100/share = 20 shares
    assert result.adjusted_quantity == pytest.approx(20.0)


async def test_rejects_low_confidence_signal():
    result = await make_manager().check_signal(make_signal(confidence=0.5), make_account(), [])

    assert not result.approved
    assert "Confidence" in result.reason


async def test_rejects_new_buy_when_max_open_positions_reached():
    positions = [make_position(ticker=f"T{i}") for i in range(5)]

    result = await make_manager().check_signal(make_signal(), make_account(), positions)

    assert not result.approved
    assert "Max open positions" in result.reason


async def test_max_open_positions_does_not_block_sells():
    positions = [make_position(ticker=f"T{i}") for i in range(5)]

    result = await make_manager().check_signal(
        make_signal(action="sell", ticker="T0"), make_account(), positions
    )

    assert result.approved


async def test_rejects_buy_when_existing_position_already_at_max_size():
    existing = make_position(ticker="AAPL", market_value=2_000.0)  # = 20% of equity

    result = await make_manager().check_signal(make_signal(), make_account(), [existing])

    assert not result.approved
    assert "already at max size" in result.reason


async def test_tops_up_existing_position_only_to_the_limit():
    existing = make_position(ticker="AAPL", market_value=1_500.0)  # $500 of headroom left

    result = await make_manager().check_signal(make_signal(), make_account(), [existing])

    assert result.approved
    assert result.adjusted_quantity == pytest.approx(5.0)


async def test_reduces_quantity_to_available_cash():
    result = await make_manager().check_signal(
        make_signal(), make_account(equity=10_000.0, cash=500.0), []
    )

    assert result.approved
    assert result.adjusted_quantity == pytest.approx(5.0)


async def test_rejects_when_cash_below_minimum_order():
    result = await make_manager().check_signal(
        make_signal(), make_account(equity=10_000.0, cash=0.5), []
    )

    assert not result.approved
    assert "Insufficient cash" in result.reason


async def test_daily_loss_trips_circuit_breaker_and_it_stays_tripped():
    rm = make_manager()
    account = make_account()
    rm.update_pnl(realized_pnl=-300.0, current_equity=account.equity)  # -3% of $10k

    first = await rm.check_signal(make_signal(), account, [])
    second = await rm.check_signal(make_signal(), account, [])

    assert not first.approved
    assert "Daily loss limit" in first.reason
    assert not second.approved
    assert "Circuit breaker active" in second.reason


async def test_circuit_breaker_resets_on_a_new_day(monkeypatch):
    rm = make_manager()
    account = make_account()
    rm.update_pnl(realized_pnl=-300.0, current_equity=account.equity)
    assert not (await rm.check_signal(make_signal(), account, [])).approved

    class Tomorrow(date):
        @classmethod
        def today(cls):
            return date.fromordinal(date.today().toordinal() + 1)

    monkeypatch.setattr(manager_module, "date", Tomorrow)

    assert (await rm.check_signal(make_signal(), account, [])).approved


async def test_rejects_when_drawdown_from_peak_exceeds_limit():
    rm = make_manager()
    await rm.check_signal(make_signal(), make_account(equity=10_000.0), [])  # sets the peak

    result = await rm.check_signal(make_signal(), make_account(equity=8_900.0, cash=8_900.0), [])

    assert not result.approved
    assert "Max drawdown" in result.reason
