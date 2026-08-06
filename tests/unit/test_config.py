"""Config & live-gate unit tests."""
from __future__ import annotations
import pytest
from signal_bot.config.settings import Settings
from signal_bot.domain.enums import AppEnv

def test_default_settings_safe():
    s = Settings(app_env=AppEnv.UNIT, live_trading_enabled=False)
    assert s.is_live_allowed() is False

def test_live_gate_requires_both():
    assert Settings(app_env=AppEnv.LIVE, live_trading_enabled=False).is_live_allowed() is False
    assert Settings(app_env=AppEnv.TESTNET_DEMO, live_trading_enabled=True).is_live_allowed() is False
    assert Settings(app_env=AppEnv.LIVE, live_trading_enabled=True).is_live_allowed() is True

def test_require_safe_mode_raises_on_mismatched_live():
    s = Settings(app_env=AppEnv.LIVE, live_trading_enabled=False)
    with pytest.raises(RuntimeError, match="Refusing to start"):
        s.require_safe_mode()

def test_require_safe_mode_ok_when_unit():
    Settings(app_env=AppEnv.UNIT, live_trading_enabled=False).require_safe_mode()
