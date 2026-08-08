"""Binance Futures adapter package (Phase 6).

Mock adapter is always available (no network).
Real Testnet / Live HTTP client will be added behind explicit gates only.
"""
from signal_bot.adapters.binance.capabilities import BINANCE_CAPABILITIES, BinanceCapabilities
from signal_bot.adapters.binance.mock import MockBinanceAdapter

__all__ = [
    "BINANCE_CAPABILITIES",
    "BinanceCapabilities",
    "MockBinanceAdapter",
]
