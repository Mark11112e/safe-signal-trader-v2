"""Signal parsers – versioned, pluggable, no exchange knowledge."""
from signal_bot.parsers.generic_structured import GenericStructuredParser, generic_structured_v1
from signal_bot.parsers.interfaces import SignalParser
from signal_bot.parsers.registry import ParserRegistry, build_default_registry

__all__ = [
    "SignalParser",
    "GenericStructuredParser",
    "generic_structured_v1",
    "ParserRegistry",
    "build_default_registry",
]
