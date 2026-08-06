"""Structured JSON logging with correlation IDs."""
from __future__ import annotations
import logging, sys
from contextvars import ContextVar
from typing import Any
from uuid import uuid4
import structlog

correlation_id_var: ContextVar[str] = ContextVar("correlation_id", default="")

def get_correlation_id() -> str:
    cid = correlation_id_var.get()
    if not cid:
        cid = str(uuid4())
        correlation_id_var.set(cid)
    return cid

def bind_correlation_id(cid: str | None = None) -> str:
    value = cid or str(uuid4())
    correlation_id_var.set(value)
    return value

def _add_correlation(logger: logging.Logger, method_name: str, event_dict: dict[str, Any]) -> dict[str, Any]:
    event_dict["correlation_id"] = get_correlation_id()
    return event_dict

def configure_logging(*, json_logs: bool = True, level: str = "INFO") -> None:
    shared = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        _add_correlation,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]
    renderer = structlog.processors.JSONRenderer() if json_logs else structlog.dev.ConsoleRenderer(colors=True)
    structlog.configure(
        processors=shared + [structlog.stdlib.ProcessorFormatter.wrap_for_formatter],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[structlog.stdlib.ProcessorFormatter.remove_processors_meta, renderer]
    )
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level.upper())

def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)
