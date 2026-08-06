"""Shared fixtures – no network, no real DB for unit tests."""
from __future__ import annotations
import pytest

@pytest.fixture
def sample_signal_kwargs():
    from decimal import Decimal
    from signal_bot.domain.enums import Side, EntryType
    from signal_bot.domain.models import TakeProfitLevel
    return {
        "source_id": "src_alpha", "parser_id": "generic_v1", "parser_version": "1.0.0",
        "symbol": "BTCUSDT", "side": Side.LONG, "entry_type": EntryType.MARKET,
        "entry_price": Decimal("65000"), "stop_loss": Decimal("64000"),
        "take_profits": (
            TakeProfitLevel(index=1, price=Decimal("66000")),
            TakeProfitLevel(index=2, price=Decimal("67000")),
            TakeProfitLevel(index=3, price=Decimal("68000")),
        ),
        "leverage": 10,
    }
