"""SourceRegistry – lookup by source_id, enable/disable, no Telegram I/O yet."""
from __future__ import annotations

from signal_bot.sources.models import SourceConfig


class SourceRegistry:
    """In-memory registry for Phase 2. Later: load from DB / config files."""

    def __init__(self) -> None:
        self._sources: dict[str, SourceConfig] = {}

    def register(self, source: SourceConfig) -> None:
        self._sources[source.source_id] = source

    def get(self, source_id: str) -> SourceConfig | None:
        return self._sources.get(source_id)

    def get_enabled(self, source_id: str) -> SourceConfig | None:
        src = self._sources.get(source_id)
        if src and src.enabled:
            return src
        return None

    def list_all(self) -> list[SourceConfig]:
        return list(self._sources.values())

    def list_enabled(self) -> list[SourceConfig]:
        return [s for s in self._sources.values() if s.enabled]

    def disable(self, source_id: str) -> bool:
        src = self._sources.get(source_id)
        if not src:
            return False
        # frozen → replace with updated copy
        self._sources[source_id] = src.model_copy(update={"enabled": False})
        return True

    def enable(self, source_id: str) -> bool:
        src = self._sources.get(source_id)
        if not src:
            return False
        self._sources[source_id] = src.model_copy(update={"enabled": True})
        return True


def build_example_registry() -> SourceRegistry:
    """Seed with one example source for tests / local demo (no real Telegram)."""
    reg = SourceRegistry()
    reg.register(
        SourceConfig(
            source_id="src_demo_alpha",
            name="Demo Structured Channel",
            telegram_chat_id=None,  # no real chat yet
            parser_id="generic_structured",
            parser_version="1.0.0",
            account_id="acc_demo_1",
            profile_id="profile_default",
            enabled=True,
        )
    )
    return reg
