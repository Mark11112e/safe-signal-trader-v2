"""Source domain models – stable source_id + versioned parser/profile refs."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from signal_bot.domain.enums import ConflictPolicy


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class SourceConfig(BaseModel):
    """Immutable view of a signal source (mirrors signal_sources table)."""

    model_config = ConfigDict(frozen=True)

    source_id: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=128)
    telegram_chat_id: str | None = None
    telegram_topic_id: int | None = None
    parser_id: str
    parser_version: str = "1.0.0"
    account_id: str
    profile_id: str
    conflict_policy: ConflictPolicy = ConflictPolicy.REJECT_SECOND
    enabled: bool = True
    limits: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=_utcnow)
