"""
SignalIngestionPipeline – pure, no network, no exchange actions.

Flow:
1. Resolve SourceConfig (enabled?)
2. Dedup (source_id + message_id)
3. Resolve parser from source.parser_id / version
4. can_parse → parse → validate
5. Return IngestResult + optional NormalizedSignal

Never submits orders, never touches adapters. Safe for Phase < 6.
"""
from __future__ import annotations

import hashlib
from typing import NamedTuple

from signal_bot.domain.models import NormalizedSignal
from signal_bot.ingestion.dedup import InMemoryDedupStore
from signal_bot.ingestion.models import IngestOutcome, IngestResult, RawInboundMessage
from signal_bot.parsers.interfaces import SignalParser
from signal_bot.parsers.registry import ParserRegistry
from signal_bot.sources.registry import SourceRegistry


def _compute_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:32]


class PipelineOutput(NamedTuple):
    result: IngestResult
    signal: NormalizedSignal | None


class SignalIngestionPipeline:
    """
    Stateless processing of one RawInboundMessage.
    Dedup store is injectable (in-memory for Phase 2; DB later).
    """

    def __init__(
        self,
        source_registry: SourceRegistry,
        parser_registry: ParserRegistry,
        dedup: InMemoryDedupStore | None = None,
    ) -> None:
        self._sources = source_registry
        self._parsers = parser_registry
        self._dedup = dedup or InMemoryDedupStore()

    @property
    def dedup(self) -> InMemoryDedupStore:
        return self._dedup

    def process(self, msg: RawInboundMessage) -> PipelineOutput:
        """Process a single inbound message. Idempotent for duplicates."""
        # Ensure hash present for downstream
        if msg.raw_hash is None and msg.text:
            msg = msg.model_copy(update={"raw_hash": _compute_hash(msg.text)})

        # 1) Source lookup
        source = self._sources.get(msg.source_id)
        if source is None:
            return self._out(
                IngestOutcome.SOURCE_UNKNOWN,
                msg,
                detail=f"unknown source_id={msg.source_id}",
            )
        if not source.enabled:
            return self._out(
                IngestOutcome.SOURCE_DISABLED,
                msg,
                detail=f"source {msg.source_id} disabled",
            )

        # 2) Dedup
        if self._dedup.is_duplicate(msg):
            return self._out(
                IngestOutcome.DUPLICATE,
                msg,
                detail="already seen (source_id, message_id)",
            )
        self._dedup.mark_seen(msg)

        # 3) Parser binding from source
        parser = self._resolve_parser(source.parser_id, source.parser_version)
        if parser is None:
            return self._out(
                IngestOutcome.PARSE_SKIPPED,
                msg,
                detail=f"no parser for {source.parser_id}@{source.parser_version}",
            )

        # 4) can_parse / parse / validate
        if not parser.can_parse(msg.text):
            return self._out(
                IngestOutcome.PARSE_SKIPPED,
                msg,
                parser_id=parser.parser_id,
                parser_version=parser.parser_version,
                detail="can_parse=false",
            )

        try:
            signal = parser.parse(
                msg.text,
                source_id=msg.source_id,
                message_id=msg.message_id,
                raw_hash=msg.raw_hash,
            )
            if signal is None:
                return self._out(
                    IngestOutcome.PARSE_SKIPPED,
                    msg,
                    parser_id=parser.parser_id,
                    parser_version=parser.parser_version,
                    detail="parse returned None",
                )
            signal = parser.validate(signal)
        except Exception as exc:  # noqa: BLE001 – capture for result, no raise to caller
            return self._out(
                IngestOutcome.PARSE_FAILED,
                msg,
                parser_id=parser.parser_id,
                parser_version=parser.parser_version,
                detail=f"{type(exc).__name__}: {exc}",
            )

        return PipelineOutput(
            result=IngestResult(
                outcome=IngestOutcome.PARSED,
                source_id=msg.source_id,
                message_id=msg.message_id,
                signal_id=signal.signal_id,
                parser_id=parser.parser_id,
                parser_version=parser.parser_version,
                detail=None,
            ),
            signal=signal,
        )

    def _resolve_parser(self, parser_id: str, version: str) -> SignalParser | None:
        p = self._parsers.get(parser_id, version)
        if p is not None:
            return p
        # fallback: id only (latest)
        return self._parsers.get(parser_id)

    @staticmethod
    def _out(
        outcome: IngestOutcome,
        msg: RawInboundMessage,
        *,
        parser_id: str | None = None,
        parser_version: str | None = None,
        detail: str | None = None,
    ) -> PipelineOutput:
        return PipelineOutput(
            result=IngestResult(
                outcome=outcome,
                source_id=msg.source_id,
                message_id=msg.message_id,
                parser_id=parser_id,
                parser_version=parser_version,
                detail=detail,
            ),
            signal=None,
        )
