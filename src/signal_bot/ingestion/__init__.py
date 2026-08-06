"""Ingestion – raw message intake, dedup, parse. No exchange actions."""
from signal_bot.ingestion.dedup import InMemoryDedupStore
from signal_bot.ingestion.models import IngestOutcome, IngestResult, RawInboundMessage
from signal_bot.ingestion.pipeline import PipelineOutput, SignalIngestionPipeline

__all__ = [
    "IngestOutcome",
    "IngestResult",
    "RawInboundMessage",
    "InMemoryDedupStore",
    "PipelineOutput",
    "SignalIngestionPipeline",
]
