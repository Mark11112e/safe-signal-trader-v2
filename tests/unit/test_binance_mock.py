"""Unit tests for MockBinanceAdapter – pure, zero network, Protocol conformance."""
from __future__ import annotations

from decimal import Decimal

import pytest

from signal_bot.adapters.binance import BINANCE_CAPABILITIES, MockBinanceAdapter
from signal_bot.adapters.interfaces import (
    AccountAdapter,
    ExchangeCapabilities,
    ExecutionAdapter,
    MarketDataAdapter,
    PnLAdapter,
    ProtectionAdapter,
    StreamingAdapter,
)
from signal_bot.domain.enums import OrderSide


@pytest.fixture
def adapter() -> MockBinanceAdapter:
    return MockBinanceAdapter(initial_balance_usdt=Decimal("10000"))


def test_implements_all_protocols(adapter: MockBinanceAdapter) -> None:
    assert isinstance(adapter, MarketDataAdapter)
    assert isinstance(adapter, AccountAdapter)
    assert isinstance(adapter, ExecutionAdapter)
    assert isinstance(adapter, ProtectionAdapter)
    assert isinstance(adapter, StreamingAdapter)
    assert isinstance(adapter, PnLAdapter)
    assert isinstance(adapter, ExchangeCapabilities)


def test_capabilities() -> None:
    assert BINANCE_CAPABILITIES.exchange_id == "binance_futures"
    assert BINANCE_CAPABILITIES.supports_user_stream is True
    assert BINANCE_CAPABILITIES.max_leverage == 125
    assert BINANCE_CAPABILITIES.supports_protection_replace() is True


@pytest.mark.asyncio
async def test_market_data(adapter: MockBinanceAdapter) -> None:
    rules = await adapter.get_symbol_rules("BTCUSDT")
    assert rules.symbol == "BTCUSDT"
    assert rules.tick_size == Decimal("0.01")
    assert rules.step_size == Decimal("0.001")

    mark = await adapter.get_mark_price("BTCUSDT")
    assert mark == Decimal("50000")

    adapter.set_mark_price("BTCUSDT", Decimal("51000"))
    assert await adapter.get_mark_price("BTCUSDT") == Decimal("51000")

    ticker = await adapter.get_ticker("BTCUSDT")
    assert ticker["symbol"] == "BTCUSDT"
    assert ticker["markPrice"] == "51000"


@pytest.mark.asyncio
async def test_account(adapter: MockBinanceAdapter) -> None:
    bal = await adapter.get_balance()
    assert bal["USDT"] == Decimal("10000")

    positions = await adapter.get_positions()
    assert positions == []

    await adapter.set_leverage("BTCUSDT", 10)
    with pytest.raises(ValueError):
        await adapter.set_leverage("BTCUSDT", 200)


@pytest.mark.asyncio
async def test_place_market_order_idempotent(adapter: MockBinanceAdapter) -> None:
    coid = "test-entry-001"
    order1 = await adapter.place_order(
        symbol="BTCUSDT",
        side=OrderSide.BUY,
        order_type="MARKET",
        quantity=Decimal("0.01"),
        client_order_id=coid,
    )
    assert order1["status"] == "FILLED"
    assert order1["clientOrderId"] == coid
    assert order1["executedQty"] == "0.01"

    # Idempotent re-submit
    order2 = await adapter.place_order(
        symbol="BTCUSDT",
        side=OrderSide.BUY,
        order_type="MARKET",
        quantity=Decimal("0.01"),
        client_order_id=coid,
    )
    assert order2["orderId"] == order1["orderId"]

    positions = await adapter.get_positions("BTCUSDT")
    assert len(positions) == 1
    assert Decimal(positions[0]["positionAmt"]) == Decimal("0.01")


@pytest.mark.asyncio
async def test_protection_stop(adapter: MockBinanceAdapter) -> None:
    await adapter.place_order(
        symbol="BTCUSDT",
        side=OrderSide.BUY,
        order_type="MARKET",
        quantity=Decimal("0.01"),
        client_order_id="entry-1",
    )

    stop = await adapter.place_stop(
        symbol="BTCUSDT",
        side=OrderSide.SELL,
        stop_price=Decimal("49000"),
        quantity=Decimal("0.01"),
        client_order_id="sl-1",
    )
    assert stop["type"] == "STOP_MARKET"
    assert stop["status"] == "NEW"
    assert stop["stopPrice"] == "49000"

    new_stop = await adapter.replace_stop(
        symbol="BTCUSDT",
        existing_order_id=stop["orderId"],
        new_stop_price=Decimal("49500"),
        quantity=Decimal("0.01"),
        client_order_id="sl-2",
    )
    assert new_stop["stopPrice"] == "49500"

    await adapter.cancel_protection(symbol="BTCUSDT", client_order_id="sl-2")


@pytest.mark.asyncio
async def test_streaming_lifecycle(adapter: MockBinanceAdapter) -> None:
    assert adapter._connected is False
    await adapter.connect()
    assert adapter._connected is True
    await adapter.subscribe_orders()
    await adapter.disconnect()
    assert adapter._connected is False


@pytest.mark.asyncio
async def test_pnl_empty(adapter: MockBinanceAdapter) -> None:
    assert await adapter.get_realized_pnl() == Decimal("0")
    assert await adapter.get_unrealized_pnl() == Decimal("0")


@pytest.mark.asyncio
async def test_get_order_and_cancel(adapter: MockBinanceAdapter) -> None:
    order = await adapter.place_order(
        symbol="ETHUSDT",
        side=OrderSide.BUY,
        order_type="LIMIT",
        quantity=Decimal("0.1"),
        price=Decimal("3000"),
        client_order_id="limit-1",
    )
    assert order["status"] == "NEW"

    fetched = await adapter.get_order(symbol="ETHUSDT", client_order_id="limit-1")
    assert fetched is not None
    assert fetched["orderId"] == order["orderId"]

    canceled = await adapter.cancel_order(symbol="ETHUSDT", client_order_id="limit-1")
    assert canceled["status"] == "CANCELED"
