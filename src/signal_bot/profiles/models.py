"""Versioned trading profiles – immutable, no credentials."""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from signal_bot.domain.enums import ConflictPolicy, LastTpMode, SlMode


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TradingProfile(BaseModel):
    """Immutable versioned profile bound to sources via profile_id + version."""

    model_config = ConfigDict(frozen=True)

    profile_id: str = Field(min_length=1, max_length=64)
    version: str = "1.0.0"
    name: str = Field(min_length=1, max_length=128)
    max_leverage: int = Field(default=20, ge=1, le=125)
    max_notional_usdt: Decimal | None = None
    max_loss_usdt: Decimal = Field(default=Decimal("10"))
    fixed_margin_usdt: Decimal | None = None
    fixed_notional_usdt: Decimal | None = None
    conflict_policy: ConflictPolicy = ConflictPolicy.REJECT_SECOND
    sl_mode: SlMode = SlMode.BREAK_EVEN
    last_tp_mode: LastTpMode = LastTpMode.TRAILING
    allow_partials: bool = False
    max_open_positions: int = Field(default=5, ge=1, le=50)
    max_legs_per_trade: int = Field(default=3, ge=1, le=10)
    entry_tolerance_pct: Decimal = Field(default=Decimal("0.5"))
    late_entry_block: bool = True
    extra: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=_utcnow)
