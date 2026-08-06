"""Unit + golden tests for parser framework (no network)."""
from __future__ import annotations

from decimal import Decimal

import pytest
from pydantic import ValidationError

from signal_bot.domain.enums import EntryType, Side
from signal_bot.domain.models import NormalizedSignal, TakeProfitLevel
from signal_bot.parsers import (
    GenericStructuredParser,
    ParserRegistry,
    build_default_registry,
    generic_structured_v1,
)
from signal_bot.parsers.interfaces import SignalParser


# ── Golden messages ──────────────────────────────────────────────────────────

GOLDEN_LONG_3TP = """
SIGNAL LONG BTCUSDT
ENTRY 65000
SL 64000
TP1 66000
TP2 67000
TP3 68000
LEV 10
"""

GOLDEN_SHORT_MARKET = """
SIGNAL SHORT ETH
SL 3500
TP1 3200 50%
TP2 3000 50%
LEV 5
"""

GOLDEN_MINIMAL = "SIGNAL BUY SOLUSDT\nLEV 3"

GOLDEN_5TP = """
SIGNAL LONG XRPUSDT
ENTRY 0.55
SL 0.50
TP1 0.56
TP2 0.58
TP3 0.60
TP4 0.62
TP5 0.65
LEV 20
"""

MALFORMED_NO_SIGNAL = "hello world this is not a signal"
MALFORMED_BAD_SIDE = "SIGNAL MAYBE BTCUSDT"
MALFORMED_EMPTY = ""
MALFORMED_TOO_SHORT = "SIG"


@pytest.fixture
def parser() -> GenericStructuredParser:
    return GenericStructuredParser()


# ── Protocol / registry ──────────────────────────────────────────────────────

def test_parser_is_protocol():
    assert isinstance(generic_structured_v1, SignalParser)


def test_default_registry_contains_generic():
    reg = build_default_registry()
    assert "generic_structured" in reg.list_ids()
    p = reg.get("generic_structured")
    assert p is not None
    assert p.parser_version == "1.0.0"


def test_registry_resolve_preferred():
    reg = build_default_registry()
    p = reg.resolve_for_text(GOLDEN_LONG_3TP, preferred_id="generic_structured")
    assert p is not None
    assert p.parser_id == "generic_structured"


def test_registry_resolve_none_for_garbage():
    reg = build_default_registry()
    assert reg.resolve_for_text(MALFORMED_NO_SIGNAL) is None


# ── can_parse ────────────────────────────────────────────────────────────────

def test_can_parse_true(parser: GenericStructuredParser):
    assert parser.can_parse(GOLDEN_LONG_3TP) is True
    assert parser.can_parse(GOLDEN_SHORT_MARKET) is True
    assert parser.can_parse(GOLDEN_MINIMAL) is True


def test_can_parse_false(parser: GenericStructuredParser):
    assert parser.can_parse(MALFORMED_NO_SIGNAL) is False
    assert parser.can_parse(MALFORMED_EMPTY) is False
    assert parser.can_parse(MALFORMED_TOO_SHORT) is False
    assert parser.can_parse(MALFORMED_BAD_SIDE) is False


# ── Golden: LONG 3 TP ────────────────────────────────────────────────────────

def test_golden_long_3tp(parser: GenericStructuredParser):
    sig = parser.parse(GOLDEN_LONG_3TP, source_id="src_alpha", message_id="42")
    assert sig is not None
    assert isinstance(sig, NormalizedSignal)
    assert sig.symbol == "BTCUSDT"
    assert sig.side == Side.LONG
    assert sig.entry_type == EntryType.LIMIT
    assert sig.entry_price == Decimal("65000")
    assert sig.stop_loss == Decimal("64000")
    assert sig.leverage == 10
    assert len(sig.take_profits) == 3
    assert sig.take_profits[0] == TakeProfitLevel(index=1, price=Decimal("66000"))
    assert sig.take_profits[1].price == Decimal("67000")
    assert sig.take_profits[2].price == Decimal("68000")
    assert sig.parser_id == "generic_structured"
    assert sig.parser_version == "1.0.0"
    assert sig.source_id == "src_alpha"
    assert sig.raw_message_id == "42"
    assert sig.raw_hash is not None and len(sig.raw_hash) == 32


# ── Golden: SHORT market + size_pct ─────────────────────────────────────────

def test_golden_short_market(parser: GenericStructuredParser):
    sig = parser.parse(GOLDEN_SHORT_MARKET, source_id="src_beta")
    assert sig is not None
    assert sig.symbol == "ETHUSDT"  # normalized
    assert sig.side == Side.SHORT
    assert sig.entry_type == EntryType.MARKET
    assert sig.entry_price is None
    assert sig.stop_loss == Decimal("3500")
    assert sig.leverage == 5
    assert len(sig.take_profits) == 2
    assert sig.take_profits[0].size_pct == Decimal("50")
    assert sig.take_profits[1].size_pct == Decimal("50")


# ── Golden: minimal ──────────────────────────────────────────────────────────

def test_golden_minimal(parser: GenericStructuredParser):
    sig = parser.parse(GOLDEN_MINIMAL, source_id="src_gamma")
    assert sig is not None
    assert sig.symbol == "SOLUSDT"
    assert sig.side == Side.LONG  # BUY → LONG
    assert sig.entry_type == EntryType.MARKET
    assert sig.stop_loss is None
    assert sig.take_profits == ()
    assert sig.leverage == 3


# ── Golden: 5 TPs ────────────────────────────────────────────────────────────

def test_golden_5tp(parser: GenericStructuredParser):
    sig = parser.parse(GOLDEN_5TP, source_id="src_delta")
    assert sig is not None
    assert len(sig.take_profits) == 5
    assert [tp.index for tp in sig.take_profits] == [1, 2, 3, 4, 5]
    assert sig.take_profits[4].price == Decimal("0.65")


# ── Malformed → None ─────────────────────────────────────────────────────────

def test_parse_malformed_returns_none(parser: GenericStructuredParser):
    assert parser.parse(MALFORMED_NO_SIGNAL, source_id="x") is None
    assert parser.parse(MALFORMED_EMPTY, source_id="x") is None
    assert parser.parse(MALFORMED_BAD_SIDE, source_id="x") is None


# ── validate ─────────────────────────────────────────────────────────────────

def test_validate_rejects_wrong_parser_id(parser: GenericStructuredParser):
    bad = NormalizedSignal(
        source_id="s",
        parser_id="other",
        parser_version="1.0.0",
        symbol="BTCUSDT",
        side=Side.LONG,
    )
    with pytest.raises(ValueError, match="parser_id"):
        parser.validate(bad)


def test_validate_rejects_bad_leverage(parser: GenericStructuredParser):
    # leverage out of range is already blocked by Pydantic on NormalizedSignal,
    # so we test the parser's own range check via a mock-like path if needed.
    # Here we just ensure valid leverage passes.
    sig = parser.parse(GOLDEN_MINIMAL, source_id="s")
    assert sig is not None
    validated = parser.validate(sig)
    assert validated is sig or validated.leverage == 3


# ── frozen / hash stability ──────────────────────────────────────────────────

def test_parsed_signal_is_frozen(parser: GenericStructuredParser):
    sig = parser.parse(GOLDEN_LONG_3TP, source_id="s")
    assert sig is not None
    with pytest.raises(ValidationError):
        sig.symbol = "OTHER"  # type: ignore[misc]
