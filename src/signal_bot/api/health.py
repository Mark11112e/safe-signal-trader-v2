"""Health, readiness and status endpoints."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter
from pydantic import BaseModel

from signal_bot import __version__
from signal_bot.config import get_settings

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    env: str
    live_trading_enabled: bool
    live_allowed: bool
    timestamp: str


class StatusResponse(BaseModel):
    status: str
    phase: str
    message: str
    components: dict[str, str]


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="ok",
        service=settings.service_name,
        version=__version__,
        env=settings.app_env.value,
        live_trading_enabled=settings.live_trading_enabled,
        live_allowed=settings.is_live_allowed(),
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@router.get("/ready", response_model=HealthResponse)
async def ready() -> HealthResponse:
    return await health()


@router.get("/status", response_model=StatusResponse)
async def status() -> StatusResponse:
    settings = get_settings()
    return StatusResponse(
        status="ok",
        phase="6-binance-prep",
        message=(
            "Phase 5 complete (Neutral Core). Phase 6 started: "
            "Binance Mock Adapter + Capabilities available (zero network). "
            "Real Testnet client gated; live trading remains OFF by default."
        ),
        components={
            "api": "up",
            "config": "loaded",
            "live_gate": "active" if not settings.is_live_allowed() else "LIVE_ALLOWED",
            "exchange_adapters": "binance-mock + interfaces",
            "binance_mock": "ready",
            "queue": "memory-claim-lease",
            "parsers": "generic_structured@1.0.0",
            "source_registry": "in-memory",
            "ingestion": "pipeline+dedup",
            "core": "risk+entry+protection+conflict+sm",
            "profiles": "snapshots+hash",
        },
    )
