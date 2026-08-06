"""ProfileRegistry – versioned profiles, in-memory for Phase 3."""
from __future__ import annotations

from signal_bot.profiles.models import TradingProfile


class ProfileRegistry:
    def __init__(self) -> None:
        self._profiles: dict[str, TradingProfile] = {}

    def register(self, profile: TradingProfile) -> None:
        key = f"{profile.profile_id}@{profile.version}"
        self._profiles[key] = profile
        self._profiles[profile.profile_id] = profile  # latest by id

    def get(self, profile_id: str, version: str | None = None) -> TradingProfile | None:
        if version:
            return self._profiles.get(f"{profile_id}@{version}")
        return self._profiles.get(profile_id)

    def list_ids(self) -> list[str]:
        return sorted({p.profile_id for p in self._profiles.values()})


def build_default_profiles() -> ProfileRegistry:
    reg = ProfileRegistry()
    reg.register(
        TradingProfile(
            profile_id="profile_default",
            version="1.0.0",
            name="Default Safe Profile",
            max_leverage=10,
            max_loss_usdt=__import__("decimal").Decimal("10"),
            max_notional_usdt=__import__("decimal").Decimal("100"),
            max_open_positions=3,
        )
    )
    reg.register(
        TradingProfile(
            profile_id="profile_conservative",
            version="1.0.0",
            name="Conservative",
            max_leverage=5,
            max_loss_usdt=__import__("decimal").Decimal("5"),
            max_notional_usdt=__import__("decimal").Decimal("50"),
            max_open_positions=2,
        )
    )
    return reg
