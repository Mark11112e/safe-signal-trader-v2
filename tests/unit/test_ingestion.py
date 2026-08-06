"""Unit tests for ingestion pipeline + dedup (no network, no exchange)."""
from __future__ import annotations

from decimal import Decimal

import pytest

from signal_bot.domain.enums import Side
from signal_bot.domain.models import NormalizedSignal
from signal_bot.ingestion import (
    IngestOutcome,
    InMemoryDedupStore,
    RawInboundMessage,
    SignalIngestionPipeline,
)
from signal_bot.parsers import build_default_registry
from signal_bot.sources import SourceConfig, SourceRegistry, build_example_registry

GOLDEN_TEXT = """
SIGNAL LONG BTCUSDT
ENTRY 65000
SL 64000
TP1 66000
TP2 67000
TP3 68000
LEV 10
"""

GARBAGE_TEXT = "hello this is not a signal at all"


@pytest.fixture
def sources() -> SourceRegistry:
    return build_example_registry()


@pytest.fixture
def parsers():
    return build_default_registry()


@pytest.fixture
def pipeline(sources, parsers) -> SignalIngestionPipeline:
    return SignalIngestionPipeline(sources, parsers)


def _msg(
    text: str = GOLDEN_TEXT,
    source_id: str = "src_demo_alpha",
    message_id: str = "tg-1001",
    is_edit: bool = False,
) -> RawInboundMessage:
    return RawInboundMessage(
        source_id=source_id,
        message_id=message_id,
        text=text,
        is_edit=is_edit,
    )


# ── Dedup ────────────────────────────────────────────────────────────────────


def test_dedup_first_seen_not_duplicate():
    store = InMemoryDedupStore()
    msg = _msg()
    assert store.is_duplicate(msg) is False
    store.mark_seen(msg)
    assert store.is_duplicate(msg) is True
    assert store.size() == 1


def test_dedup_different_message_id_ok():
    store = InMemoryDedupStore()
    store.mark_seen(_msg(message_id="1"))
    assert store.is_duplicate(_msg(message_id="2")) is False


def test_dedup_different_source_ok():
    store = InMemoryDedupStore()
    store.mark_seen(_msg(source_id="src_a", message_id="1"))
    assert store.is_duplicate(_msg(source_id="src_b", message_id="1")) is False


# ── Pipeline outcomes ────────────────────────────────────────────────────────


def test_pipeline_parsed_happy_path(pipeline: SignalIngestionPipeline):
    out = pipeline.process(_msg())
    assert out.result.outcome == IngestOutcome.PARSED
    assert out.signal is not None
    assert isinstance(out.signal, NormalizedSignal)
    assert out.signal.symbol == "BTCUSDT"
    assert out.signal.side == Side.LONG
    assert out.signal.entry_price == Decimal("65000")
    assert out.signal.stop_loss == Decimal("64000")
    assert len(out.signal.take_profits) == 3
    assert out.signal.leverage == 10
    assert out.signal.source_id == "src_demo_alpha"
    assert out.signal.parser_id == "generic_structured"
    assert out.result.signal_id == out.signal.signal_id
    assert out.result.parser_id == "generic_structured"


def test_pipeline_duplicate(pipeline: SignalIngestionPipeline):
    msg = _msg()
    first = pipeline.process(msg)
    assert first.result.outcome == IngestOutcome.PARSED
    second = pipeline.process(msg)
    assert second.result.outcome == IngestOutcome.DUPLICATE
    assert second.signal is None


def test_pipeline_source_unknown(pipeline: SignalIngestionPipeline):
    out = pipeline.process(_msg(source_id="does_not_exist"))
    assert out.result.outcome == IngestOutcome.SOURCE_UNKNOWN
    assert out.signal is None


def test_pipeline_source_disabled(sources: SourceRegistry, parsers):
    sources.disable("src_demo_alpha")
    pipe = SignalIngestionPipeline(sources, parsers)
    out = pipe.process(_msg())
    assert out.result.outcome == IngestOutcome.SOURCE_DISABLED
    assert out.signal is None


def test_pipeline_parse_skipped_garbage(pipeline: SignalIngestionPipeline):
    out = pipeline.process(_msg(text=GARBAGE_TEXT, message_id="g1"))
    assert out.result.outcome == IngestOutcome.PARSE_SKIPPED
    assert out.signal is None
    assert out.result.parser_id == "generic_structured"


def test_pipeline_parser_bound_from_source(sources: SourceRegistry, parsers):
    """Source.parser_id is used; wrong preferred does not matter."""
    # register a source that points to generic_structured
    sources.register(
        SourceConfig(
            source_id="src_bound",
            name="Bound",
            parser_id="generic_structured",
            parser_version="1.0.0",
            account_id="acc_1",
            profile_id="p1",
            enabled=True,
        )
    )
    pipe = SignalIngestionPipeline(sources, parsers)
    out = pipe.process(_msg(source_id="src_bound", message_id="b1"))
    assert out.result.outcome == IngestOutcome.PARSED
    assert out.signal is not None
    assert out.signal.parser_id == "generic_structured"


def test_pipeline_idempotent_same_message_id(pipeline: SignalIngestionPipeline):
    m1 = _msg(message_id="same-id", text=GOLDEN_TEXT)
    m2 = _msg(message_id="same-id", text=GOLDEN_TEXT)  # same content
    assert pipeline.process(m1).result.outcome == IngestOutcome.PARSED
    assert pipeline.process(m2).result.outcome == IngestOutcome.DUPLICATE


def test_pipeline_edit_allowed_after_mark(pipeline: SignalIngestionPipeline):
    """Edits with same message_id are treated as duplicates by message_id (Telegram edit keeps id)."""
    original = _msg(message_id="edit-1", is_edit=False)
    assert pipeline.process(original).result.outcome == IngestOutcome.PARSED
    edited = _msg(message_id="edit-1", text=GOLDEN_TEXT + "\n#edit", is_edit=True)
    # same message_id → still duplicate (Telegram message_id unique per chat)
    assert pipeline.process(edited).result.outcome == IngestOutcome.DUPLICATE


def test_raw_message_frozen():
    msg = _msg()
    with pytest.raises(Exception):
        msg.text = "mutate"  # type: ignore[misc]


def test_pipeline_computes_raw_hash(pipeline: SignalIngestionPipeline):
    out = pipeline.process(_msg())
    assert out.signal is not None
    assert out.signal.raw_hash is not None
    assert len(out.signal.raw_hash) == 32
