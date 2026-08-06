"""SQLAlchemy 2 async models – Phase 1 foundation tables."""
from __future__ import annotations
from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import uuid4
from sqlalchemy import Boolean, DateTime, Index, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from signal_bot.infrastructure.db.base import Base

def _uuid():
    return uuid4()

class SignalSourceORM(Base):
    __tablename__ = "signal_sources"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    telegram_chat_id: Mapped[str | None] = mapped_column(String(64))
    telegram_topic_id: Mapped[int | None] = mapped_column(Integer)
    parser_id: Mapped[str] = mapped_column(String(64), nullable=False)
    parser_version: Mapped[str] = mapped_column(String(32), nullable=False, default="1.0.0")
    account_id: Mapped[str] = mapped_column(String(64), nullable=False)
    profile_id: Mapped[str] = mapped_column(String(64), nullable=False)
    conflict_policy: Mapped[str] = mapped_column(String(64), default="reject_second")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    limits: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class SignalMessageORM(Base):
    __tablename__ = "signal_messages"
    __table_args__ = (UniqueConstraint("source_id", "message_id", name="uq_signal_msg_source_msgid"), Index("ix_signal_messages_raw_hash", "raw_hash"))
    id: Mapped[Any] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    source_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    message_id: Mapped[str] = mapped_column(String(64), nullable=False)
    raw_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    raw_text: Mapped[str | None] = mapped_column(Text)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    is_edit: Mapped[bool] = mapped_column(Boolean, default=False)
    meta: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)

class ParsedSignalORM(Base):
    __tablename__ = "parsed_signals"
    id: Mapped[Any] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    source_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    message_id: Mapped[Any | None] = mapped_column(UUID(as_uuid=True))
    parser_id: Mapped[str] = mapped_column(String(64), nullable=False)
    parser_version: Mapped[str] = mapped_column(String(32), nullable=False)
    symbol: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    side: Mapped[str] = mapped_column(String(8), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    signal_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class ExchangeAccountORM(Base):
    __tablename__ = "exchange_accounts"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    exchange_id: Mapped[str] = mapped_column(String(32), nullable=False)
    label: Mapped[str] = mapped_column(String(128), nullable=False)
    credential_ref: Mapped[str] = mapped_column(String(128), nullable=False)
    is_testnet: Mapped[bool] = mapped_column(Boolean, default=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class ProfileORM(Base):
    __tablename__ = "profiles"
    __table_args__ = (UniqueConstraint("profile_id", "version", name="uq_profile_id_ver"),)
    id: Mapped[Any] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    profile_id: Mapped[str] = mapped_column(String(64), nullable=False)
    version: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    config: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class EffectiveConfigSnapshotORM(Base):
    __tablename__ = "effective_config_snapshots"
    id: Mapped[Any] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    schema_version: Mapped[str] = mapped_column(String(16), nullable=False, default="1.0.0")
    source_id: Mapped[str] = mapped_column(String(64), nullable=False)
    account_id: Mapped[str] = mapped_column(String(64), nullable=False)
    profile_id: Mapped[str] = mapped_column(String(64), nullable=False)
    profile_version: Mapped[str] = mapped_column(String(32), nullable=False)
    config_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class TradeORM(Base):
    __tablename__ = "trades"
    id: Mapped[Any] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    source_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    account_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    symbol: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    side: Mapped[str] = mapped_column(String(8), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="PENDING_ENTRY", index=True)
    signal_id: Mapped[Any | None] = mapped_column(UUID(as_uuid=True))
    snapshot_id: Mapped[Any] = mapped_column(UUID(as_uuid=True), nullable=False)
    entry_price: Mapped[Decimal | None] = mapped_column(Numeric(24, 8))
    quantity: Mapped[Decimal | None] = mapped_column(Numeric(24, 8))
    stop_loss: Mapped[Decimal | None] = mapped_column(Numeric(24, 8))
    meta: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class OrderJobORM(Base):
    __tablename__ = "order_jobs"
    __table_args__ = (Index("ix_order_jobs_claim", "status", "lease_until"), Index("ix_order_jobs_trade", "trade_id"))
    id: Mapped[Any] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    trade_id: Mapped[Any] = mapped_column(UUID(as_uuid=True), nullable=False)
    job_type: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="PENDING", index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    client_order_id: Mapped[str | None] = mapped_column(String(64), unique=True)
    attempt: Mapped[int] = mapped_column(Integer, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, default=5)
    lease_owner: Mapped[str | None] = mapped_column(String(64))
    lease_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class ManualReviewORM(Base):
    __tablename__ = "manual_reviews"
    id: Mapped[Any] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    trade_id: Mapped[Any | None] = mapped_column(UUID(as_uuid=True), index=True)
    job_id: Mapped[Any | None] = mapped_column(UUID(as_uuid=True))
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    context: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    resolution: Mapped[str | None] = mapped_column(Text)
