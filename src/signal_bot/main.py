"""FastAPI application entry – Dashboard UI + Health / Status / Docs + Offline Demo."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from signal_bot import __version__
from signal_bot.api.dashboard import router as dashboard_router
from signal_bot.api.health import router as health_router
from signal_bot.config import get_settings
from signal_bot.infrastructure.logging import configure_logging, get_logger


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(json_logs=settings.log_json, level=settings.log_level)
    log = get_logger("signal_bot.main")
    settings.require_safe_mode()
    log.info(
        "app_starting",
        version=__version__,
        env=settings.app_env.value,
        live_allowed=settings.is_live_allowed(),
    )
    yield
    log.info("app_shutdown")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Safe Signal Trader",
        description=(
            "Modular, safety-first Telegram signal trading bot. "
            "Offline demo UI: parse signals, risk check, queue playground – no live exchange."
        ),
        version=__version__,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )
    app.include_router(dashboard_router)
    app.include_router(health_router)
    # Offline demo API (optional – skip if module not present in partial downloads)
    try:
        from signal_bot.api.demo import router as demo_router

        app.include_router(demo_router)
    except ImportError:
        pass
    return app


app = create_app()
