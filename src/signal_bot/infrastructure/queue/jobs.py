"""Queue helpers – lease timing (full claim in later phase with DB)."""
from __future__ import annotations
from datetime import datetime, timedelta, timezone

def lease_deadline(seconds: int = 30) -> datetime:
    return datetime.now(timezone.utc) + timedelta(seconds=seconds)
