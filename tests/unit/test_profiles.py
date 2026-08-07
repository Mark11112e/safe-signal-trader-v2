"""Unit tests for Profiles + EffectiveConfigSnapshot (Phase 3)."""
from __future__ import annotations

from decimal import Decimal

import pytest

from signal_bot.domain.enums import ConflictPolicy, LastTpMode, SlMode
from signal_bot.profiles import (
    ProfileRegistry,
    TradingProfile,
    build_default_profiles,
    build_snapshot,
    compute_config_hash,
)
from signal_bot.sources.models import SourceConfig


def test_trading_profile_frozen():
    p = TradingProfile(profile_id="p1", name="Test")
    with pytest.raises(Exception):
        p.name = "changed"  # type: ignore[misc]


def test_profile_registry_register_get():
    reg = ProfileRegistry()
    p = TradingProfile(profile_id="p1", version="1.0.0", name="A")
    reg.register(p)
    assert reg.get("p1") is not None
    assert reg.get("p1", "1.0.0") is not None
    assert reg.get("p1", "9.9.9") is None
    assert "p1" in reg.list_ids()


def test_build_default_profiles():
    reg = build_default_profiles()
    assert reg.get("profile_default") is not None
    ids = reg.list_ids()
    assert "profile_default" in ids


def test_compute_config_hash_stable():
    payload = {"a": 1, "b": "x", "c": None}
    h1 = compute_config_hash(payload)
    h2 = compute_config_hash(payload)
    assert h1 == h2
    assert len(h1) == 32


def test_build_snapshot_hash_and_fields():
    src = SourceConfig(
        source_id="src_alpha",
        account_id="acc_1",
        name="Alpha",
        telegram_chat_id="-100123",
        parser_id="generic_v1",
        profile_id="profile_default",
    )
    profile = TradingProfile(
        profile_id="profile_default",
        version="1.0.0",
        name="Default",
        max_leverage=10,
        max_loss_usdt=Decimal("8"),
        conflict_policy=ConflictPolicy.REJECT_SECOND,
        sl_mode=SlMode.BREAK_EVEN,
        last_tp_mode=LastTpMode.TRAILING,
    )
    snap = build_snapshot(src, profile)
    assert snap.source_id == "src_alpha"
    assert snap.account_id == "acc_1"
    assert snap.profile_id == "profile_default"
    assert snap.max_leverage == 10
    assert snap.max_loss_usdt == Decimal("8")
    assert snap.config_hash
    assert len(snap.config_hash) == 32
    snap2 = build_snapshot(src, profile)
    assert snap.config_hash == snap2.config_hash
