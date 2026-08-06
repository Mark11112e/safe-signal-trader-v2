"""Build immutable EffectiveConfigSnapshot + deterministic hash."""
from __future__ import annotations

import hashlib
import json
from decimal import Decimal

from signal_bot.domain.models import EffectiveConfigSnapshot
from signal_bot.profiles.models import TradingProfile
from signal_bot.sources.models import SourceConfig


def _dec_str(v: Decimal | None) -> str | None:
    return str(v) if v is not None else None


def compute_config_hash(payload: dict) -> str:
    """Stable SHA-256 over sorted JSON (no credentials)."""
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


def build_snapshot(
    source: SourceConfig,
    profile: TradingProfile,
    *,
    schema_version: str = "1.0.0",
) -> EffectiveConfigSnapshot:
    """
    Create immutable snapshot from source + profile.
    Active trades keep this snapshot forever (principle 6).
    """
    payload = {
        "schema_version": schema_version,
        "source_id": source.source_id,
        "account_id": source.account_id,
        "profile_id": profile.profile_id,
        "profile_version": profile.version,
        "conflict_policy": profile.conflict_policy.value,
        "max_leverage": profile.max_leverage,
        "max_notional_usdt": _dec_str(profile.max_notional_usdt),
        "max_loss_usdt": _dec_str(profile.max_loss_usdt),
        "sl_mode": profile.sl_mode.value,
        "last_tp_mode": profile.last_tp_mode.value,
        "allow_partials": profile.allow_partials,
    }
    h = compute_config_hash(payload)
    snap = EffectiveConfigSnapshot(
        schema_version=schema_version,
        source_id=source.source_id,
        account_id=source.account_id,
        profile_id=profile.profile_id,
        profile_version=profile.version,
        conflict_policy=profile.conflict_policy,
        max_leverage=profile.max_leverage,
        max_notional_usdt=profile.max_notional_usdt,
        max_loss_usdt=profile.max_loss_usdt,
        sl_mode=profile.sl_mode,
        last_tp_mode=profile.last_tp_mode,
        allow_partials=profile.allow_partials,
        config_hash=h,
    )
    return snap
