"""
Entry planner – deterministic clientOrderIds, no blind retry, pure.

Produces an EntryPlan that a later JobWorker can turn into order_jobs.
Never places orders itself (Phase < 6).
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from signal_bot.domain.enums import EntryType, Side
from signal_bot.domain.models import EffectiveConfigSnapshot, NormalizedSignal
from signal_bot.core.risk.engine import RiskDecision


@dataclass(frozen=True)
class EntryPlan:
    trade_id: UUID
    symbol: str
    side: Side
    entry_type: EntryType
    quantity: Decimal
    price: Decimal | None
    leverage: int
    client_order_id: str
    stop_loss: Decimal | None
    snapshot_hash: str
    blocked: bool = False
    block_reason: str | None = None


def _deterministic_client_order_id(trade_id: UUID, attempt: int = 0) -> str:
    """Stable, unique, exchange-safe client order id (no randomness)."""
    raw = f"sst-{trade_id.hex[:16]}-a{attempt}"
    return raw[:36]


class EntryPlanner:
    def plan(
        self,
        *,
        trade_id: UUID,
        signal: NormalizedSignal,
        snapshot: EffectiveConfigSnapshot,
        risk: RiskDecision,
        attempt: int = 0,
        mark_price: Decimal | None = None,
    ) -> EntryPlan:
        if not risk.allowed or risk.quantity is None or risk.quantity <= 0:
            return EntryPlan(
                trade_id=trade_id,
                symbol=signal.symbol,
                side=signal.side,
                entry_type=signal.entry_type,
                quantity=Decimal("0"),
                price=signal.entry_price,
                leverage=risk.leverage,
                client_order_id=_deterministic_client_order_id(trade_id, attempt),
                stop_loss=signal.stop_loss,
                snapshot_hash=snapshot.config_hash,
                blocked=True,
                block_reason=risk.reason,
            )

        price = signal.entry_price
        if signal.entry_type == EntryType.LIMIT and price is None:
            return EntryPlan(
                trade_id=trade_id,
                symbol=signal.symbol,
                side=signal.side,
                entry_type=signal.entry_type,
                quantity=risk.quantity,
                price=None,
                leverage=risk.leverage,
                client_order_id=_deterministic_client_order_id(trade_id, attempt),
                stop_loss=signal.stop_loss,
                snapshot_hash=snapshot.config_hash,
                blocked=True,
                block_reason="limit entry requires price",
            )

        if mark_price and price and signal.entry_type == EntryType.LIMIT:
            if signal.side == Side.LONG and mark_price > price * Decimal("1.01"):
                return EntryPlan(
                    trade_id=trade_id,
                    symbol=signal.symbol,
                    side=signal.side,
                    entry_type=signal.entry_type,
                    quantity=risk.quantity,
                    price=price,
                    leverage=risk.leverage,
                    client_order_id=_deterministic_client_order_id(trade_id, attempt),
                    stop_loss=signal.stop_loss,
                    snapshot_hash=snapshot.config_hash,
                    blocked=True,
                    block_reason="late entry: mark above limit for LONG",
                )
            if signal.side == Side.SHORT and mark_price < price * Decimal("0.99"):
                return EntryPlan(
                    trade_id=trade_id,
                    symbol=signal.symbol,
                    side=signal.side,
                    entry_type=signal.entry_type,
                    quantity=risk.quantity,
                    price=price,
                    leverage=risk.leverage,
                    client_order_id=_deterministic_client_order_id(trade_id, attempt),
                    stop_loss=signal.stop_loss,
                    snapshot_hash=snapshot.config_hash,
                    blocked=True,
                    block_reason="late entry: mark below limit for SHORT",
                )

        return EntryPlan(
            trade_id=trade_id,
            symbol=signal.symbol,
            side=signal.side,
            entry_type=signal.entry_type,
            quantity=risk.quantity,
            price=price if signal.entry_type == EntryType.LIMIT else None,
            leverage=risk.leverage,
            client_order_id=_deterministic_client_order_id(trade_id, attempt),
            stop_loss=signal.stop_loss,
            snapshot_hash=snapshot.config_hash,
            blocked=False,
        )
