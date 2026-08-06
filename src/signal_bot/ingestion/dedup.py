"""In-memory deduplication for inbound messages (Phase 2 skeleton).

Later: persist via SignalMessageORM + unique (source_id, message_id).
Safety: same message never processed twice in the same process lifetime.
"""
from __future__ import annotations

from signal_bot.ingestion.models import RawInboundMessage


class InMemoryDedupStore:
    """
    Tracks seen (source_id, message_id) pairs.
    Thread/async-safe for single-process unit tests; production uses DB unique constraint.
    """

    def __init__(self) -> None:
        self._seen: set[tuple[str, str]] = set()
        # content-level: (source_id, raw_hash) – used only for non-edit duplicates
        self._hashes: set[tuple[str, str]] = set()

    def is_duplicate(self, msg: RawInboundMessage) -> bool:
        key = (msg.source_id, msg.message_id)
        if key in self._seen:
            return True
        # Content-level only if same source and hash present (edits may share hash)
        if msg.raw_hash and (msg.source_id, msg.raw_hash) in self._hashes:
            # allow explicit edits through; edits keep same message_id usually
            if not msg.is_edit:
                return True
        return False

    def mark_seen(self, msg: RawInboundMessage) -> None:
        self._seen.add((msg.source_id, msg.message_id))
        if msg.raw_hash:
            self._hashes.add((msg.source_id, msg.raw_hash))

    def clear(self) -> None:
        self._seen.clear()
        self._hashes.clear()

    def size(self) -> int:
        return len(self._seen)
