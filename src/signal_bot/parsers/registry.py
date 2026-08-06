"""ParserRegistry – map parser_id → SignalParser instance. Extensible without core change."""
from __future__ import annotations

from signal_bot.parsers.generic_structured import GenericStructuredParser, generic_structured_v1
from signal_bot.parsers.interfaces import SignalParser


class ParserRegistry:
    """In-memory registry. Later: load from config / plugin entry points."""

    def __init__(self) -> None:
        self._parsers: dict[str, SignalParser] = {}

    def register(self, parser: SignalParser) -> None:
        key = f"{parser.parser_id}@{parser.parser_version}"
        self._parsers[key] = parser
        # also register by id alone (latest wins)
        self._parsers[parser.parser_id] = parser

    def get(self, parser_id: str, version: str | None = None) -> SignalParser | None:
        if version:
            return self._parsers.get(f"{parser_id}@{version}")
        return self._parsers.get(parser_id)

    def list_ids(self) -> list[str]:
        return sorted({p.parser_id for p in self._parsers.values()})

    def resolve_for_text(self, text: str, preferred_id: str | None = None) -> SignalParser | None:
        """Return first parser that can_parse the text (preferred first)."""
        if preferred_id:
            p = self.get(preferred_id)
            if p and p.can_parse(text):
                return p
        for p in self._unique_parsers():
            if p.can_parse(text):
                return p
        return None

    def _unique_parsers(self) -> list[SignalParser]:
        seen: set[int] = set()
        out: list[SignalParser] = []
        for p in self._parsers.values():
            i = id(p)
            if i not in seen:
                seen.add(i)
                out.append(p)
        return out


def build_default_registry() -> ParserRegistry:
    reg = ParserRegistry()
    reg.register(generic_structured_v1)
    return reg
