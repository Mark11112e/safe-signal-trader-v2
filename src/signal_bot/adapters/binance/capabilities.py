"""Binance (Futures) capabilities – pure data, no I/O."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class BinanceCapabilities:
    """Reference capabilities for Binance USD-M Futures (testnet + live)."""

    exchange_id: str = "binance_futures"
    supports_user_stream: bool = True
    supports_reduce_only: bool = True
    supports_trailing_stop: bool = True
    supports_position_mode_hedge: bool = True
    max_leverage: int = 125

    def supports_protection_replace(self) -> bool:
        # Binance allows cancel+replace; atomic replace is not guaranteed → we treat as supported
        # via cancel then place with verification (caller responsibility).
        return True


BINANCE_CAPABILITIES = BinanceCapabilities()
