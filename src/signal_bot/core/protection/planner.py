"""
Protection planner – safer stop, never worsen SL, pure.

Principle 10: Position never unprotected.
Principle: SL may only move in the protective direction.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from signal_bot.domain.enums import Side, SlMode
from signal_bot.domain.models import EffectiveConfigSnapshot, NormalizedSignal, TakeProfitLevel


@dataclass(frozen=True)
class ProtectionPlan:
    initial_stop: Decimal | None
    safer_stop: Decimal | None
    reason: str
    is_protected: bool


def _is_safer(side: Side, current: Decimal, candidate: Decimal) -> bool:
    if side == Side.LONG:
        return candidate >= current
    return candidate <= current


class ProtectionPlanner:
    def initial_stop(
        self,
        signal: NormalizedSignal,
        snapshot: EffectiveConfigSnapshot,
        *,
        entry_price: Decimal | None = None,
    ) -> ProtectionPlan:
        sl = signal.stop_loss
        if sl is None and snapshot.sl_mode == or_none(snapshot):
            return ProtectionPlan(None, None, "sl_mode=none", False)
        if sl is None:
            return ProtectionPlan(None, None, "missing stop_loss", False)
        return ProtectionPlan(sl, sl, "signal SL", True)

    def after_tp(
        self,
        *,
        side: Side,
        current_stop: Decimal,
        entry_price: Decimal,
        hit_tp: TakeProfitLevel,
        snapshot: EffectiveConfigSnapshot,
        previous_tp_price: Decimal | None = None,
    ) -> ProtectionPlan:
        candidate = current_stop
        mode = snapshot.sl_mode
        if mode == SlMode.BREAK_EVEN:
            candidate = entry_price
        elif mode == SlMode.MOVE_TO_PREVIOUS_TP and previous_tp_price is not None:
            candidate = previous_tp_price
        elif mode == SlMode.LOCK_PROFIT_USDT:
            candidate = entry_price
        elif mode == SlMode.NONE:
            candidate = current_stop
        if not _is_safer(side, current_stop, candidate):
            candidate = current_stop
        return ProtectionPlan(current_stop, candidate, f"after_tp mode={mode.value}", True)

    def never_worsen(self, side: Side, current: Decimal, proposed: Decimal) -> Decimal:
        if _is_safer(side, current, proposed):
            return proposed
        return current


def or_none(snapshot: EffectiveConfigSnapshot) -> bool:
    return snapshot.sl_mode == SlMode.NONE
