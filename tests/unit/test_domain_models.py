"""Unit tests for domain models – pure, no I/O."""
from __future__ import annotations
from decimal import Decimal
from uuid import UUID
import pytest
from pydantic import ValidationError
from signal_bot.domain.enums import ConflictPolicy, JobStatus, LastTpMode, Side, SlMode, TradeStatus
from signal_bot.domain.models import (
    EffectiveConfigSnapshot, ManualReview, NormalizedSignal, OrderJob, SymbolRules, TakeProfitLevel, Trade,
)

def test_take_profit_level_valid():
    tp = TakeProfitLevel(index=1, price=Decimal("100"), size_pct=Decimal("25"))
    assert tp.index == 1

def test_take_profit_level_invalid_pct():
    with pytest.raises(ValidationError):
        TakeProfitLevel(index=1, price=Decimal("100"), size_pct=Decimal("0"))

def test_normalized_signal_frozen(sample_signal_kwargs):
    sig = NormalizedSignal(**sample_signal_kwargs)
    assert sig.symbol == "BTCUSDT"
    with pytest.raises(ValidationError):
        sig.symbol = "ETHUSDT"

def test_normalized_signal_duplicate_tp_index(sample_signal_kwargs):
    kwargs = dict(sample_signal_kwargs)
    kwargs["take_profits"] = (TakeProfitLevel(index=1, price=Decimal("1")), TakeProfitLevel(index=1, price=Decimal("2")))
    with pytest.raises(ValidationError):
        NormalizedSignal(**kwargs)

def test_effective_config_snapshot_immutable():
    snap = EffectiveConfigSnapshot(source_id="s1", account_id="acc1", profile_id="p1", profile_version="1.0.0")
    assert snap.conflict_policy == ConflictPolicy.REJECT_SECOND
    with pytest.raises(ValidationError):
        snap.source_id = "other"

def test_snapshot_with_hash():
    snap = EffectiveConfigSnapshot(source_id="s1", account_id="acc1", profile_id="p1", profile_version="1.0.0")
    hashed = snap.with_hash("abc123")
    assert hashed.config_hash == "abc123"
    assert snap.config_hash == ""

def test_trade_defaults():
    snap = EffectiveConfigSnapshot(source_id="s1", account_id="acc1", profile_id="p1", profile_version="1.0.0")
    trade = Trade(source_id="s1", account_id="acc1", symbol="BTCUSDT", side=Side.LONG, snapshot=snap)
    assert trade.status == TradeStatus.PENDING_ENTRY
    assert isinstance(trade.trade_id, UUID)

def test_order_job_defaults():
    job = OrderJob(trade_id=UUID("00000000-0000-0000-0000-000000000001"), job_type="entry")
    assert job.status == JobStatus.PENDING

def test_manual_review():
    rev = ManualReview(reason="ambiguous_fill")
    assert rev.resolution is None

def test_symbol_rules():
    rules = SymbolRules(symbol="BTCUSDT")
    assert rules.min_notional == Decimal("5")
