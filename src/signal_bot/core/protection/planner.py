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
    """Return True if candidate is equal or better (more protective) than current."""
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
        if sl is None and snapshot.sl_mode == SlMode.NONE:
            return ProtectionPlan(
                initial_stop=None,
                safer_stop=None,
                reason="sl_mode=none",
                is_protected=False,
            )
        if sl is None:
            return ProtectionPlan(
                initial_stop=None,
                safer_stop=None,
                reason="missing stop_loss",
                is_protected=False,
            )
        return ProtectionPlan(
            initial_stop=sl,
            safer_stop=sl,
            reason="signal SL",
            is_protected=True,
        )

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
        """Move SL according to sl_mode; never worsen."""
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

        return ProtectionPlan(
            initial_stop=current_stop,
            safer_stop=candidate,
            reason=f"after_tp mode={mode.value}",
            is_protected=True,
        )

    def never_worsen(self, side: Side, current: Decimal, proposed: Decimal) -> Decimal:
        """Clamp proposed SL so it never worsens protection."""
        if _is_safer(side, current, proposed):
            return proposed
        return current
