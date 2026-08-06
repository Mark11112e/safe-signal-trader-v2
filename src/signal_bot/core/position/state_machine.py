"""
Position / Trade state machine – pure transitions.

Valid transitions only; illegal ones raise or return False.
Uses domain TradeStatus.
"""
from __future__ import annotations

from signal_bot.domain.enums import TradeStatus

# Allowed transitions: from → set of to
_TRANSITIONS: dict[TradeStatus, frozenset[TradeStatus]] = {
    TradeStatus.PENDING_ENTRY: frozenset(
        {TradeStatus.OPEN, TradeStatus.CLOSED, TradeStatus.MANUAL_REVIEW}
    ),
    TradeStatus.OPEN: frozenset(
        {TradeStatus.CLOSING, TradeStatus.CLOSED, TradeStatus.MANUAL_REVIEW}
    ),
    TradeStatus.CLOSING: frozenset(
        {TradeStatus.CLOSED, TradeStatus.MANUAL_REVIEW, TradeStatus.OPEN}
    ),
    TradeStatus.CLOSED: frozenset({TradeStatus.ARCHIVED}),
    TradeStatus.ARCHIVED: frozenset(),
    TradeStatus.MANUAL_REVIEW: frozenset(
        {TradeStatus.OPEN, TradeStatus.CLOSED, TradeStatus.ARCHIVED}
    ),
}


class TradeStateMachine:
    def can_transition(self, current: TradeStatus, target: TradeStatus) -> bool:
        return target in _TRANSITIONS.get(current, frozenset())

    def transition(self, current: TradeStatus, target: TradeStatus) -> TradeStatus:
        if not self.can_transition(current, target):
            raise ValueError(f"illegal transition {current.value} → {target.value}")
        return target
