"""In-memory Mock Binance Futures adapter – zero network, deterministic, for unit/demo/TESTNET_DEMO simulation.

Implements all adapter Protocols. Safe for Phase 6 scaffolding; real HTTP client comes later
behind explicit env + Startup-Gate and only when APP_ENV=TESTNET_DEMO or LIVE + flag.
"""
from __future__ import annotations

import itertools
import time
from decimal import Decimal
from typing import Any

from signal_bot.adapters.binance.capabilities import BINANCE_CAPABILITIES, BinanceCapabilities
from signal_bot.domain.enums import OrderSide
from signal_bot.domain.models import SymbolRules


class MockBinanceAdapter:
    """
    Full in-memory implementation of MarketData + Account + Execution + Protection + Streaming + PnL.

    - No network calls ever.
    - Deterministic order IDs when client_order_id provided.
    - Tracks balances, positions, open orders, protection stops.
    - Suitable for unit tests, offline demo and as stand-in before real Testnet client.
    """

    def __init__(
        self,
        *,
        initial_balance_usdt: Decimal = Decimal("10000"),
        default_mark_price: Decimal = Decimal("50000"),
        exchange_id: str = "binance_futures_mock",
    ) -> None:
        self.exchange_id = exchange_id
        self.capabilities: BinanceCapabilities = BINANCE_CAPABILITIES
        self._balance = {"USDT": initial_balance_usdt}
        self._mark_prices: dict[str, Decimal] = {}
        self._default_mark = default_mark_price
        self._positions: dict[str, dict[str, Any]] = {}
        self._orders: dict[str, dict[str, Any]] = {}
        self._order_id_seq = itertools.count(1)
        self._client_to_order: dict[str, str] = {}
        self._protections: dict[str, dict[str, Any]] = {}
        self._connected = False
        self._realized_pnl = Decimal("0")

    # ── Capabilities (also satisfies ExchangeCapabilities) ──────────────
    @property
    def supports_user_stream(self) -> bool:
        return self.capabilities.supports_user_stream

    @property
    def supports_reduce_only(self) -> bool:
        return self.capabilities.supports_reduce_only

    @property
    def supports_trailing_stop(self) -> bool:
        return self.capabilities.supports_trailing_stop

    @property
    def supports_position_mode_hedge(self) -> bool:
        return self.capabilities.supports_position_mode_hedge

    @property
    def max_leverage(self) -> int:
        return self.capabilities.max_leverage

    def supports_protection_replace(self) -> bool:
        return self.capabilities.supports_protection_replace()

    # ── MarketDataAdapter ───────────────────────────────────────────────
    async def get_symbol_rules(self, symbol: str) -> SymbolRules:
        base = symbol.upper().replace("USDT", "")
        tick = Decimal("0.01") if base in {"BTC", "ETH"} else Decimal("0.0001")
        step = Decimal("0.001") if base == "BTC" else Decimal("0.01")
        prec_price = 2 if base in {"BTC", "ETH"} else 4
        prec_qty = 3 if base == "BTC" else 2
        return SymbolRules(
            symbol=symbol.upper(),
            price_precision=prec_price,
            quantity_precision=prec_qty,
            min_qty=step,
            min_notional=Decimal("5"),
            tick_size=tick,
            step_size=step,
        )

    async def get_mark_price(self, symbol: str) -> Decimal:
        return self._mark_prices.get(symbol.upper(), self._default_mark)

    async def get_ticker(self, symbol: str) -> dict[str, Any]:
        mark = await self.get_mark_price(symbol)
        return {
            "symbol": symbol.upper(),
            "markPrice": str(mark),
            "lastPrice": str(mark),
            "timestamp": int(time.time() * 1000),
        }

    def set_mark_price(self, symbol: str, price: Decimal) -> None:
        """Test helper – not part of Protocol."""
        self._mark_prices[symbol.upper()] = price

    # ── AccountAdapter ──────────────────────────────────────────────────
    async def get_balance(self) -> dict[str, Decimal]:
        return dict(self._balance)

    async def get_positions(self, symbol: str | None = None) -> list[dict[str, Any]]:
        if symbol:
            pos = self._positions.get(symbol.upper())
            return [pos] if pos else []
        return list(self._positions.values())

    async def set_leverage(self, symbol: str, leverage: int) -> None:
        if leverage < 1 or leverage > self.max_leverage:
            raise ValueError(f"leverage {leverage} out of range 1..{self.max_leverage}")

    # ── ExecutionAdapter ────────────────────────────────────────────────
    async def place_order(
        self,
        *,
        symbol: str,
        side: OrderSide,
        order_type: str,
        quantity: Decimal,
        price: Decimal | None = None,
        client_order_id: str,
        reduce_only: bool = False,
        extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        symbol = symbol.upper()
        if client_order_id in self._client_to_order:
            oid = self._client_to_order[client_order_id]
            return self._orders[oid]

        order_id = str(next(self._order_id_seq))
        mark = await self.get_mark_price(symbol)
        fill_price = price if order_type.upper() == "LIMIT" and price is not None else mark
        status = "FILLED" if order_type.upper() == "MARKET" else "NEW"

        order = {
            "orderId": order_id,
            "clientOrderId": client_order_id,
            "symbol": symbol,
            "side": side.value,
            "type": order_type.upper(),
            "origQty": str(quantity),
            "executedQty": str(quantity) if status == "FILLED" else "0",
            "price": str(fill_price),
            "avgPrice": str(fill_price) if status == "FILLED" else "0",
            "status": status,
            "reduceOnly": reduce_only,
            "updateTime": int(time.time() * 1000),
        }
        self._orders[order_id] = order
        self._client_to_order[client_order_id] = order_id

        if status == "FILLED":
            await self._apply_fill(symbol, side, quantity, fill_price, reduce_only)

        return order

    async def cancel_order(
        self,
        *,
        symbol: str,
        order_id: str | None = None,
        client_order_id: str | None = None,
    ) -> dict[str, Any]:
        oid = order_id or (self._client_to_order.get(client_order_id or "") if client_order_id else None)
        if not oid or oid not in self._orders:
            raise KeyError(f"order not found: order_id={order_id} client={client_order_id}")
        order = self._orders[oid]
        order["status"] = "CANCELED"
        order["updateTime"] = int(time.time() * 1000)
        return order

    async def get_order(
        self,
        *,
        symbol: str,
        order_id: str | None = None,
        client_order_id: str | None = None,
    ) -> dict[str, Any] | None:
        oid = order_id or (self._client_to_order.get(client_order_id or "") if client_order_id else None)
        if not oid:
            return None
        return self._orders.get(oid)

    # ── ProtectionAdapter ───────────────────────────────────────────────
    async def place_stop(
        self,
        *,
        symbol: str,
        side: OrderSide,
        stop_price: Decimal,
        quantity: Decimal,
        client_order_id: str,
        reduce_only: bool = True,
    ) -> dict[str, Any]:
        symbol = symbol.upper()
        order_id = str(next(self._order_id_seq))
        order = {
            "orderId": order_id,
            "clientOrderId": client_order_id,
            "symbol": symbol,
            "side": side.value,
            "type": "STOP_MARKET",
            "stopPrice": str(stop_price),
            "origQty": str(quantity),
            "status": "NEW",
            "reduceOnly": reduce_only,
            "updateTime": int(time.time() * 1000),
        }
        self._orders[order_id] = order
        self._client_to_order[client_order_id] = order_id
        self._protections[symbol] = order
        return order

    async def replace_stop(
        self,
        *,
        symbol: str,
        existing_order_id: str,
        new_stop_price: Decimal,
        quantity: Decimal,
        client_order_id: str,
    ) -> dict[str, Any]:
        old = self._orders.get(existing_order_id)
        if old:
            old["status"] = "CANCELED"
        side = OrderSide(old["side"]) if old else OrderSide.SELL
        return await self.place_stop(
            symbol=symbol,
            side=side,
            stop_price=new_stop_price,
            quantity=quantity,
            client_order_id=client_order_id,
            reduce_only=True,
        )

    async def cancel_protection(
        self,
        *,
        symbol: str,
        order_id: str | None = None,
        client_order_id: str | None = None,
    ) -> None:
        symbol = symbol.upper()
        if symbol in self._protections:
            del self._protections[symbol]
        if order_id or client_order_id:
            await self.cancel_order(symbol=symbol, order_id=order_id, client_order_id=client_order_id)

    # ── StreamingAdapter ────────────────────────────────────────────────
    async def connect(self) -> None:
        self._connected = True

    async def disconnect(self) -> None:
        self._connected = False

    async def subscribe_orders(self) -> None:
        if not self._connected:
            raise RuntimeError("not connected")

    # ── PnLAdapter ──────────────────────────────────────────────────────
    async def get_realized_pnl(self, symbol: str | None = None) -> Decimal:
        return self._realized_pnl

    async def get_unrealized_pnl(self, symbol: str | None = None) -> Decimal:
        total = Decimal("0")
        positions = await self.get_positions(symbol)
        for pos in positions:
            qty = Decimal(str(pos.get("positionAmt", "0")))
            if qty == 0:
                continue
            entry = Decimal(str(pos.get("entryPrice", "0")))
            mark = await self.get_mark_price(pos["symbol"])
            total += (mark - entry) * qty
        return total

    # ── Internal helpers ────────────────────────────────────────────────
    async def _apply_fill(
        self,
        symbol: str,
        side: OrderSide,
        quantity: Decimal,
        price: Decimal,
        reduce_only: bool,
    ) -> None:
        pos = self._positions.get(symbol)
        signed_qty = quantity if side == OrderSide.BUY else -quantity

        if pos is None:
            if reduce_only:
                return
            self._positions[symbol] = {
                "symbol": symbol,
                "positionAmt": str(signed_qty),
                "entryPrice": str(price),
                "unrealizedProfit": "0",
                "leverage": "10",
            }
            return

        current = Decimal(pos["positionAmt"])
        new_qty = current + signed_qty
        if new_qty == 0:
            entry = Decimal(pos["entryPrice"])
            pnl = (price - entry) * current
            self._realized_pnl += pnl
            del self._positions[symbol]
        else:
            if (current > 0 and signed_qty > 0) or (current < 0 and signed_qty < 0):
                old_notional = abs(current) * Decimal(pos["entryPrice"])
                add_notional = abs(signed_qty) * price
                new_entry = (old_notional + add_notional) / abs(new_qty)
                pos["entryPrice"] = str(new_entry)
            pos["positionAmt"] = str(new_qty)
