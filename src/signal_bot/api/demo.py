"""Offline Demo API – no Telegram, Exchange, or DB required."""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from signal_bot.core.conflict.resolver import ConflictResolver
from signal_bot.core.entry.planner import EntryPlanner
from signal_bot.core.protection.planner import ProtectionPlanner
from signal_bot.core.risk.engine import RiskEngine
from signal_bot.domain.models import SymbolRules
from signal_bot.infrastructure.queue.memory import InMemoryJobQueue
from signal_bot.ingestion.models import RawInboundMessage
from signal_bot.ingestion.pipeline import SignalIngestionPipeline
from signal_bot.parsers import build_default_registry
from signal_bot.profiles import build_default_profiles, build_snapshot
from signal_bot.sources import build_example_registry

router = APIRouter(prefix="/api/demo", tags=["demo-offline"])

_sources = build_example_registry()
_parsers = build_default_registry()
_profiles = build_default_profiles()
_queue = InMemoryJobQueue()
_risk = RiskEngine()
_entry = EntryPlanner()
_protection = ProtectionPlanner()
_conflict = ConflictResolver()
_msg_counter = 0


class ParseRequest(BaseModel):
    text: str = Field(min_length=1, max_length=8000)
    source_id: str = "src_demo_alpha"


class RiskRequest(BaseModel):
    text: str = Field(min_length=1, max_length=8000)
    source_id: str = "src_demo_alpha"
    profile_id: str = "profile_default"
    mark_price: Decimal | None = None
    open_positions: int = 0


class QueueEnqueueRequest(BaseModel):
    job_type: str = "entry"
    client_order_id: str | None = None


def _dec(v: Any) -> Any:
    if isinstance(v, Decimal):
        return str(v)
    if isinstance(v, UUID):
        return str(v)
    if isinstance(v, datetime):
        return v.isoformat()
    if isinstance(v, tuple):
        return [_dec(x) for x in v]
    if isinstance(v, dict):
        return {k: _dec(val) for k, val in v.items()}
    if hasattr(v, "model_dump"):
        return _dec(v.model_dump())
    if hasattr(v, "value"):
        return v.value
    return v


@router.get("/overview")
async def overview() -> dict[str, Any]:
    from signal_bot.domain.enums import JobStatus
    return {
        "mode": "offline-demo",
        "live_trading": False,
        "exchange_connected": False,
        "telegram_connected": False,
        "database_required": False,
        "sources_count": len(_sources.list_all()),
        "sources_enabled": len(_sources.list_enabled()),
        "parsers": _parsers.list_ids(),
        "profiles": _profiles.list_ids(),
        "queue_size": _queue.size(),
        "queue_pending": len(_queue.list_by_status(JobStatus.PENDING)),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "capabilities": [
            "Signal parsen (GenericStructured)",
            "Risk-Check (neutral)",
            "Entry-Plan (clientOrderId)",
            "Protection / safer-stop",
            "Conflict-Resolver",
            "Queue Claim/Lease Demo",
            "Sources & Profiles ansehen",
        ],
    }


@router.get("/sources")
async def list_sources() -> list[dict[str, Any]]:
    return [_dec(s.model_dump()) for s in _sources.list_all()]


@router.get("/profiles")
async def list_profiles() -> list[dict[str, Any]]:
    out = []
    for pid in _profiles.list_ids():
        p = _profiles.get(pid)
        if p:
            out.append(_dec(p.model_dump()))
    return out


@router.post("/parse")
async def parse_signal(body: ParseRequest) -> dict[str, Any]:
    global _msg_counter
    _msg_counter += 1
    msg = RawInboundMessage(
        source_id=body.source_id,
        message_id=f"demo-{_msg_counter}",
        text=body.text,
    )
    out = SignalIngestionPipeline(_sources, _parsers).process(msg)
    result: dict[str, Any] = {
        "outcome": out.result.outcome.value,
        "detail": out.result.detail,
        "parser_id": out.result.parser_id,
        "parser_version": out.result.parser_version,
        "signal": None,
    }
    if out.signal is not None:
        result["signal"] = _dec(out.signal.model_dump())
    return result


@router.post("/analyze")
async def analyze_signal(body: RiskRequest) -> dict[str, Any]:
    global _msg_counter
    _msg_counter += 1
    msg = RawInboundMessage(
        source_id=body.source_id,
        message_id=f"demo-an-{_msg_counter}",
        text=body.text,
    )
    out = SignalIngestionPipeline(_sources, _parsers).process(msg)
    if out.signal is None:
        return {"ok": False, "outcome": out.result.outcome.value, "detail": out.result.detail}

    signal = out.signal
    source = _sources.get(body.source_id)
    profile = _profiles.get(body.profile_id)
    if source is None or profile is None:
        raise HTTPException(400, "unknown source or profile")

    snap = build_snapshot(source, profile)
    mark = body.mark_price or signal.entry_price or Decimal("65000")
    risk = _risk.evaluate(
        signal, snap,
        symbol_rules=SymbolRules(symbol=signal.symbol),
        mark_price=mark,
        open_position_count=body.open_positions,
        max_open_positions=profile.max_open_positions,
    )
    trade_id = uuid4()
    entry = _entry.plan(trade_id=trade_id, signal=signal, snapshot=snap, risk=risk, mark_price=mark)
    prot = _protection.initial_stop(signal, snap, entry_price=mark)
    conflict = _conflict.resolve(signal, policy=snap.conflict_policy, open_trades=[])

    return {
        "ok": True,
        "outcome": "parsed",
        "signal": _dec(signal.model_dump()),
        "snapshot": {
            "profile_id": snap.profile_id,
            "profile_version": snap.profile_version,
            "config_hash": snap.config_hash,
            "max_leverage": snap.max_leverage,
            "max_loss_usdt": str(snap.max_loss_usdt) if snap.max_loss_usdt else None,
            "sl_mode": snap.sl_mode.value,
            "conflict_policy": snap.conflict_policy.value,
        },
        "risk": {
            "allowed": risk.allowed,
            "reason": risk.reason,
            "leverage": risk.leverage,
            "notional_usdt": str(risk.notional_usdt),
            "quantity": str(risk.quantity) if risk.quantity is not None else None,
            "max_loss_usdt": str(risk.max_loss_usdt) if risk.max_loss_usdt else None,
        },
        "entry": {
            "blocked": entry.blocked,
            "block_reason": entry.block_reason,
            "client_order_id": entry.client_order_id,
            "quantity": str(entry.quantity),
            "price": str(entry.price) if entry.price else None,
            "leverage": entry.leverage,
            "entry_type": entry.entry_type.value,
        },
        "protection": {
            "is_protected": prot.is_protected,
            "initial_stop": str(prot.initial_stop) if prot.initial_stop else None,
            "reason": prot.reason,
        },
        "conflict": {"action": conflict.action.value, "reason": conflict.reason},
    }


@router.get("/queue")
async def queue_status() -> dict[str, Any]:
    from signal_bot.domain.enums import JobStatus
    return {
        "size": _queue.size(),
        "pending": len(_queue.list_by_status(JobStatus.PENDING)),
        "claimed": len(_queue.list_by_status(JobStatus.CLAIMED)),
        "completed": len(_queue.list_by_status(JobStatus.COMPLETED)),
        "manual_review": len(_queue.list_by_status(JobStatus.MANUAL_REVIEW)),
        "jobs": [
            {
                "job_id": str(j.job_id),
                "job_type": j.job_type,
                "status": j.status.value,
                "attempt": j.attempt,
                "client_order_id": j.client_order_id,
                "lease_owner": j.lease_owner,
                "last_error": j.last_error,
            }
            for j in list(_queue._jobs.values())[-20:]
        ],
    }


@router.post("/queue/enqueue")
async def queue_enqueue(body: QueueEnqueueRequest) -> dict[str, Any]:
    job = _queue.enqueue(
        trade_id=uuid4(),
        job_type=body.job_type,
        client_order_id=body.client_order_id or f"demo-{uuid4().hex[:10]}",
        payload={"demo": True},
    )
    return {"job_id": str(job.job_id), "status": job.status.value, "client_order_id": job.client_order_id}


@router.post("/queue/claim")
async def queue_claim(owner: str = "demo-worker") -> dict[str, Any]:
    job = _queue.claim(owner, lease_seconds=60)
    if job is None:
        return {"claimed": False, "job": None}
    return {
        "claimed": True,
        "job": {
            "job_id": str(job.job_id),
            "job_type": job.job_type,
            "status": job.status.value,
            "attempt": job.attempt,
            "client_order_id": job.client_order_id,
            "lease_owner": job.lease_owner,
        },
    }


@router.post("/queue/complete")
async def queue_complete(job_id: str, owner: str = "demo-worker") -> dict[str, Any]:
    return {"ok": _queue.complete(UUID(job_id), owner)}


@router.post("/queue/fail")
async def queue_fail(job_id: str, owner: str = "demo-worker", error: str = "demo fail") -> dict[str, Any]:
    return {"ok": _queue.fail(UUID(job_id), owner, error)}


@router.get("/examples")
async def signal_examples() -> list[dict[str, str]]:
    return [
        {"name": "LONG BTC 3 TPs", "text": "SIGNAL LONG BTCUSDT\nENTRY 65000\nSL 64000\nTP1 66000\nTP2 67000\nTP3 68000\nLEV 10"},
        {"name": "SHORT ETH Market", "text": "SIGNAL SHORT ETH\nSL 3500\nTP1 3200 50%\nTP2 3000 50%\nLEV 5"},
        {"name": "Minimal BUY SOL", "text": "SIGNAL BUY SOLUSDT\nLEV 3"},
        {"name": "LONG XRP 5 TPs", "text": "SIGNAL LONG XRPUSDT\nENTRY 0.55\nSL 0.50\nTP1 0.56\nTP2 0.58\nTP3 0.60\nTP4 0.62\nTP5 0.65\nLEV 20"},
        {"name": "Ungültig (kein Signal)", "text": "hello world this is not a signal"},
    ]
