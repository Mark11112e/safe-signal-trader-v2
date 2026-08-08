"""Exchange adapter contracts and concrete adapters.

Core never imports exchange-specific fields. All I/O goes through Protocols.
Phase 6 starts with Binance mock (zero network) + capabilities.
"""
from signal_bot.adapters.interfaces import (
    AccountAdapter,
    ExchangeCapabilities,
    ExecutionAdapter,
    MarketDataAdapter,
    PnLAdapter,
    ProtectionAdapter,
    StreamingAdapter,
)
from signal_bot.adapters.binance import (
    BINANCE_CAPABILITIES,
    BinanceCapabilities,
    MockBinanceAdapter,
)

__all__ = [
    "AccountAdapter",
    "ExchangeCapabilities",
    "ExecutionAdapter",
    "MarketDataAdapter",
    "PnLAdapter",
    "ProtectionAdapter",
    "StreamingAdapter",
    "BINANCE_CAPABILITIES",
    "BinanceCapabilities",
    "MockBinanceAdapter",
]
