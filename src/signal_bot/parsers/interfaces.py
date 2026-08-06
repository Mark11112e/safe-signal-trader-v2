"""Parser contracts – exchange-agnostic, pure text → NormalizedSignal."""
from __future__ import annotations

from typing import Protocol, runtime_checkable

from signal_bot.domain.models import NormalizedSignal


@runtime_checkable
class SignalParser(Protocol):
    """
    Versioned parser for one message format.

    - can_parse: cheap pre-check (no heavy work)
    - parse: extract NormalizedSignal or None if not applicable
    - validate: post-checks (raises ValueError on invalid); returns same or cleaned signal
    """

    parser_id: str
    parser_version: str

    def can_parse(self, text: str) -> bool: ...

    def parse(
        self,
        text: str,
        *,
        source_id: str,
        message_id: str | None = None,
        raw_hash: str | None = None,
    ) -> NormalizedSignal | None: ...

    def validate(self, signal: NormalizedSignal) -> NormalizedSignal: ...
