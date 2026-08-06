"""Ingestion domain models – raw inbound messages, no exchange knowledge."""
from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class IngestOutcome(StrEnum):
    """Result of processing one inbound message. Never triggers exchange actions."""

    DUPLICATE = "duplicate"
    SOURCE_DISABLED = "source_disabled"
    SOURCE_UNKNOWN = "source_unknown"
    PARSE_SKIPPED = "parse_skipped"  # no parser matched / can_parse false
    PARSE_FAILED = "parse_failed"  # exception / validate error
    PARSED = "parsed"


class RawInboundMessage(BaseModel):
    """
    Normalized raw message from any source (Telegram, webhook, …).
    Dedup key: (source_id, message_id). Optional raw_hash for content-level checks.
    """

    model_config = ConfigDict(frozen=True)

    source_id: str = Field(min_length=1, max_length=64)
    message_id: str = Field(min_length=1, max_length=128)
    text: str
    is_edit: bool = False
    received_at: datetime = Field(default_factory=_utcnow)
    raw_hash: str | None = None
    meta: dict[str, Any] = Field(default_factory=dict)


class IngestResult(BaseModel):
    """Outcome of one pipeline run. Contains signal only on PARSED."""

    model_config = ConfigDict(frozen=True)

    outcome: IngestOutcome
    source_id: str
    message_id: str
    signal_id: UUID | None = None
    parser_id: str | None = None
    parser_version: str | None = None
    detail: str | None = None
    # signal itself is returned separately by pipeline for type clarity
