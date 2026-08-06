"""
Conflict resolver – pure decision, no side effects.

Policies from domain.enums.ConflictPolicy.
Opposite direction is always blocked (never implicit reverse/close).
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from signal_bot.domain.enums import ConflictPolicy, Side
from signal_bot.domain.models import NormalizedSignal


class ConflictAction(StrEnum):
    ACCEPT = "accept"
    REJECT = "reject"
    SCALE_IN = "scale_in"
    MANUAL_REVIEW = "manual_review"


@dataclass(frozen=True)
class ConflictDecision:
    action: ConflictAction
    reason: str


@dataclass(frozen=True)
class OpenTradeRef:
    """Minimal view of an active trade for conflict checks."""

    trade_id: str
    source_id: str
    symbol: str
    side: Side
    account_id: str


class ConflictResolver:
    def resolve(
        self,
        signal: NormalizedSignal,
        *,
        policy: ConflictPolicy,
        open_trades: list[OpenTradeRef],
        source_priority: dict[str, int] | None = None,
    ) -> ConflictDecision:
        same_symbol = [t for t in open_trades if t.symbol == signal.symbol]
        if not same_symbol:
            return ConflictDecision(ConflictAction.ACCEPT, "no conflict")

        opposite = [t for t in same_symbol if t.side != signal.side]
        if opposite:
            return ConflictDecision(
                ConflictAction.REJECT,
                f"opposite direction open on {signal.symbol}",
            )

        same_dir = [t for t in same_symbol if t.side == signal.side]
        if not same_dir:
            return ConflictDecision(ConflictAction.ACCEPT, "no same-direction conflict")

        if policy == ConflictPolicy.REJECT_SECOND:
            return ConflictDecision(ConflictAction.REJECT, "reject_second policy")

        if policy == ConflictPolicy.ALLOW_SAME_DIRECTION_SCALE_IN:
            return ConflictDecision(ConflictAction.SCALE_IN, "scale-in allowed")

        if policy == ConflictPolicy.DEDICATED_ACCOUNT:
            return ConflictDecision(ConflictAction.ACCEPT, "dedicated_account – caller scopes")

        if policy == ConflictPolicy.SOURCE_PRIORITY:
            pri = source_priority or {}
            sig_p = pri.get(signal.source_id, 0)
            for t in same_dir:
                if pri.get(t.source_id, 0) >= sig_p:
                    return ConflictDecision(
                        ConflictAction.REJECT,
                        f"existing source {t.source_id} has higher/equal priority",
                    )
            return ConflictDecision(ConflictAction.ACCEPT, "higher source priority")

        if policy == ConflictPolicy.MANUAL_REVIEW:
            return ConflictDecision(ConflictAction.MANUAL_REVIEW, "manual_review policy")

        return ConflictDecision(ConflictAction.REJECT, "unknown policy – fail closed")
