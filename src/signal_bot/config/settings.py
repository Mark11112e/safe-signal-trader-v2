"""Application settings – Pydantic v2 Settings, no secrets in code."""
from __future__ import annotations
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from signal_bot.domain.enums import AppEnv

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore", case_sensitive=False)
    app_env: AppEnv = AppEnv.UNIT
    live_trading_enabled: bool = False
    database_url: str = "postgresql+asyncpg://signalbot:signalbot@localhost:5432/signalbot"
    log_level: str = "INFO"
    log_json: bool = True
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    service_name: str = "safe-signal-trader"
    service_version: str = "0.1.0"

    def is_live_allowed(self) -> bool:
        return self.live_trading_enabled and self.app_env == AppEnv.LIVE

    def require_safe_mode(self) -> None:
        if self.app_env == AppEnv.LIVE and not self.live_trading_enabled:
            raise RuntimeError(
                "APP_ENV=LIVE but LIVE_TRADING_ENABLED=false. "
                "Refusing to start. Set the flag explicitly only after review."
            )

@lru_cache
def get_settings() -> Settings:
    return Settings()
