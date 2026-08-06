"""Adapter interfaces are Protocols."""
from signal_bot.adapters.interfaces import (
    AccountAdapter, ExchangeCapabilities, ExecutionAdapter, MarketDataAdapter,
    PnLAdapter, ProtectionAdapter, StreamingAdapter,
)
def test_protocols_importable():
    for p in (MarketDataAdapter, AccountAdapter, ExecutionAdapter, ProtectionAdapter,
              StreamingAdapter, PnLAdapter, ExchangeCapabilities):
        assert p is not None
