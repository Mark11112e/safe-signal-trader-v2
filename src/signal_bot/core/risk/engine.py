"""
Neutral Risk Engine – pure calculations, no exchange I/O.

Decides whether a signal may open a trade and computes size / leverage
from EffectiveConfigSnapshot + optional account exposure.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_DOWN

from signal_bot.domain.models import EffectiveConfigSnapshot, NormalizedSignal, SymbolRules


@dataclass(frozen=True)
class RiskDecision:
    allowed: bool
    reason: str
    leverage: int
    notional_usdt: Decimal
    quantity: Decimal | None = None
    max_loss_usdt: Decimal | None = None


class RiskEngine:
    """Stateless risk checks against snapshot limits."""

    def evaluate(
        self,
        signal: NormalizedSignal,
        snapshot: EffectiveConfigSnapshot,
        *,
        symbol_rules: SymbolRules | None = None,
        current_exposure_usdt: Decimal = Decimal("0"),
        open_position_count: int = 0,
        max_open_positions: int = 5,
        mark_price: Decimal | None = None,
    ) -> RiskDecision:
        # 1) Max open positions
        if open_position_count >= max_open_positions:
            return RiskDecision(
                allowed=False,
                reason=f"max_open_positions={max_open_positions} reached",
                leverage=1,
                notional_usdt=Decimal("0"),
            )

        # 2) Leverage ladder – never exceed snapshot max
        lev = signal.leverage or 1
        lev = min(lev, snapshot.max_leverage)

        # 3) Notional from max_loss / max_notional
        max_loss = snapshot.max_loss_usdt or Decimal("10")
        notional = max_loss * Decimal(lev)
        if snapshot.max_notional_usdt is not None:
            notional = min(notional, snapshot.max_notional_usdt)

        # 4) Exposure limit
        if snapshot.max_notional_usdt is not None:
            if current_exposure_usdt + notional > snapshot.max_notional_usdt:
                remaining = snapshot.max_notional_usdt - current_exposure_usdt
                if remaining <= 0:
                    return RiskDecision(
                        allowed=False,
                        reason="exposure limit reached",
                        leverage=lev,
                        notional_usdt=Decimal("0"),
                    )
                notional = remaining

        # 5) Quantity from mark/entry + symbol rules
        price = mark_price or signal.entry_price
        qty: Decimal | None = None
        if price and price > 0:
            raw_qty = notional / price
            qty = raw_qty.quantize(Decimal("0.00000001"), rounding=ROUND_DOWN)
            if symbol_rules:
                step = symbol_rules.step_size
                if step > 0:
                    floored = (qty // step) * step
                    if floored <= 0 and raw_qty >= symbol_rules.min_qty:
                        floored = step
                    qty = floored
                if qty < symbol_rules.min_qty:
                    return RiskDecision(
                        allowed=False,
                        reason=f"qty {qty} < min_qty {symbol_rules.min_qty}",
                        leverage=lev,
                        notional_usdt=notional,
                        quantity=qty,
                        max_loss_usdt=max_loss,
                    )
                notional = (qty * price).quantize(Decimal("0.01"), rounding=ROUND_DOWN)
                if notional < symbol_rules.min_notional:
                    return RiskDecision(
                        allowed=False,
                        reason=f"notional {notional} < min_notional",
                        leverage=lev,
                        notional_usdt=notional,
                        quantity=qty,
                        max_loss_usdt=max_loss,
                    )

        if notional <= 0:
            return RiskDecision(
                allowed=False,
                reason="notional <= 0",
                leverage=lev,
                notional_usdt=Decimal("0"),
            )

        return RiskDecision(
            allowed=True,
            reason="ok",
            leverage=lev,
            notional_usdt=notional,
            quantity=qty,
            max_loss_usdt=max_loss,
        )
