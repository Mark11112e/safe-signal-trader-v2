"""Web dashboard UI (Phase 2 – Source + Parser status overview)."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from signal_bot import __version__
from signal_bot.config import get_settings

router = APIRouter(tags=["ui"])

_TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
templates = Jinja2Templates(directory=str(_TEMPLATES_DIR))


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request) -> HTMLResponse:
    settings = get_settings()
    components = {
        "api": "up",
        "config": "loaded",
        "live_gate": "active" if not settings.is_live_allowed() else "LIVE_ALLOWED",
        "exchange_adapters": "interfaces-only",
        "queue": "schema-ready",
        "parsers": "generic_structured@1.0.0",
        "source_registry": "in-memory",
        "ingestion": "pipeline+dedup",
        "ui": "dashboard",
    }
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "status": "ok",
            "service": settings.service_name,
            "version": __version__,
            "env": settings.app_env.value,
            "live_trading_enabled": settings.live_trading_enabled,
            "live_allowed": settings.is_live_allowed(),
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
            "phase": "2-source-parser",
            "components": components,
        },
    )
