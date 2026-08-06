"""Core domain models – pure Pydantic, exchange-agnostic, no credentials."""
from __future__ import annotations
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from signal_bot.domain.enums import ConflictPolicy, EntryType, JobStatus, LastTpMode, Side, SlMode, TradeStatus

def _utcnow() -> datetime:
    return datetime.now(timezone.utc)

class TakeProfitLevel(BaseModel):
    model_config = ConfigDict(frozen=True)
    index: int = Field(ge=1, le=5)
    price: Decimal
    size_pct: Decimal | None = Field(default=None)
    @field_validator("size_pct")
    @classmethod
    def _pct_bounds(cls, v: Decimal | None) -> Decimal | None:
        if v is not None and (v <= 0 or v > 100):
            raise ValueError("size_pct must be in (0, 100]")
        return v

class NormalizedSignal(BaseModel):
    model_config = ConfigDict(frozen=True)
    signal_id: UUID = Field(default_factory=uuid4)
    source_id: str
    parser_id: str
    parser_version: str
    symbol: str
    side: Side
    entry_type: EntryType = EntryType.MARKET
    entry_price: Decimal | None = None
    stop_loss: Decimal | None = None
    take_profits: tuple[TakeProfitLevel, ...] = ()
    leverage: int | None = Field(default=None, ge=1, le=125)
    raw_message_id: str | None = None
    raw_hash: str | None = None
    received_at: datetime = Field(default_factory=_utcnow)
    extra: dict[str, Any] = Field(default_factory=dict)
    @model_validator(mode="after")
    def _tp_indices_unique(self) -> "NormalizedSignal":
        idxs = [tp.index for tp in self.take_profits]
        if len(idxs) != len(set(idxs)):
            raise ValueError("take_profits indices must be unique")
        return self

class EffectiveConfigSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True)
    schema_version: str = "1.0.0"
    snapshot_id: UUID = Field(default_factory=uuid4)
    source_id: str
    account_id: str
    profile_id: str
    profile_version: str
    conflict_policy: ConflictPolicy = ConflictPolicy.REJECT_SECOND
    max_leverage: int = Field(default=20, ge=1, le=125)
    max_notional_usdt: Decimal | None = None
    max_loss_usdt: Decimal | None = Field(default=Decimal("10"))
    sl_mode: SlMode = SlMode.BREAK_EVEN
    last_tp_mode: LastTpMode = LastTpMode.TRAILING
    allow_partials: bool = False
    created_at: datetime = Field(default_factory=_utcnow)
    config_hash: str = ""
    def with_hash(self, h: str) -> "EffectiveConfigSnapshot":
        return self.model_copy(update={"config_hash": h})

class Trade(BaseModel):
    model_config = ConfigDict(frozen=False)
    trade_id: UUID = Field(default_factory=uuid4)
    source_id: str
    account_id: str
    symbol: str
    side: Side
    status: TradeStatus = TradeStatus.PENDING_ENTRY
    signal_id: UUID | None = None
    snapshot: EffectiveConfigSnapshot
    entry_price: Decimal | None = None
    quantity: Decimal | None = None
    stop_loss: Decimal | None = None
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)

class OrderJob(BaseModel):
    model_config = ConfigDict(frozen=False)
    job_id: UUID = Field(default_factory=uuid4)
    trade_id: UUID
    job_type: str
    status: JobStatus = JobStatus.PENDING
    payload: dict[str, Any] = Field(default_factory=dict)
    client_order_id: str | None = None
    attempt: int = 0
    max_attempts: int = 5
    lease_owner: str | None = None
    lease_until: datetime | None = None
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)
    last_error: str | None = None

class ManualReview(BaseModel):
    model_config = ConfigDict(frozen=False)
    review_id: UUID = Field(default_factory=uuid4)
    trade_id: UUID | None = None
    job_id: UUID | None = None
    reason: str
    context: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=_utcnow)
    resolved_at: datetime | None = None
    resolution: str | None = None

class SymbolRules(BaseModel):
    model_config = ConfigDict(frozen=True)
    symbol: str
    price_precision: int = 2
    quantity_precision: int = 3
    min_qty: Decimal = Decimal("0.001")
    min_notional: Decimal = Decimal("5")
    tick_size: Decimal = Decimal("0.01")
    step_size: Decimal = Decimal("0.001")
