"""Unit tests for Neutral Core (Phase 5) – pure, no I/O, no network."""
from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest

from signal_bot.core import (
    ConflictAction,
    ConflictResolver,
    EntryPlanner,
    OpenTradeRef,
    ProtectionPlanner,
    RiskDecision,
    RiskEngine,
    TradeStateMachine,
)
from signal_bot.domain.enums import (
    ConflictPolicy,
    EntryType,
    Side,
    SlMode,
    TradeStatus,
)
from signal_bot.domain.models import (
    EffectiveConfigSnapshot,
    NormalizedSignal,
    SymbolRules,
    TakeProfitLevel,
)


@pytest.fixture
def signal() -> NormalizedSignal:
    return NormalizedSignal(
        source_id="src_alpha",
        parser_id="generic_v1",
        parser_version="1.0.0",
        symbol="BTCUSDT",
        side=Side.LONG,
        entry_type=EntryType.MARKET,
        entry_price=Decimal("65000"),
        stop_loss=Decimal("64000"),
        take_profits=(
            TakeProfitLevel(index=1, price=Decimal("66000")),
            TakeProfitLevel(index=2, price=Decimal("67000")),
        ),
        leverage=10,
    )


@pytest.fixture
def snapshot() -> EffectiveConfigSnapshot:
    return EffectiveConfigSnapshot(
        source_id="src_alpha",
        account_id="acc_1",
        profile_id="profile_default",
        profile_version="1.0.0",
        max_leverage=20,
        max_notional_usdt=Decimal("500"),
        max_loss_usdt=Decimal("10"),
        config_hash="abc123",
    )


@pytest.fixture
def rules() -> SymbolRules:
    return SymbolRules(
        symbol="BTCUSDT",
        min_qty=Decimal("0.001"),
        min_notional=Decimal("5"),
        step_size=Decimal("0.001"),
        tick_size=Decimal("0.01"),
    )


class TestRiskEngine:
    def test_allows_valid_signal(self, signal, snapshot, rules):
        eng = RiskEngine()
        d = eng.evaluate(signal, snapshot, symbol_rules=rules, mark_price=Decimal("65000"))
        assert d.allowed is True
        assert d.reason == "ok"
        assert d.leverage == 10
        assert d.quantity is not None and d.quantity > 0
        assert d.notional_usdt > 0

    def test_caps_leverage_to_snapshot(self, signal, snapshot, rules):
        signal = signal.model_copy(update={"leverage": 50})
        eng = RiskEngine()
        d = eng.evaluate(signal, snapshot, symbol_rules=rules, mark_price=Decimal("65000"))
        assert d.allowed is True
        assert d.leverage == 20

    def test_rejects_max_open_positions(self, signal, snapshot):
        eng = RiskEngine()
        d = eng.evaluate(signal, snapshot, open_position_count=5, max_open_positions=5)
        assert d.allowed is False
        assert "max_open_positions" in d.reason

    def test_rejects_exposure_limit(self, signal, snapshot, rules):
        eng = RiskEngine()
        d = eng.evaluate(
            signal,
            snapshot,
            symbol_rules=rules,
            current_exposure_usdt=Decimal("500"),
            mark_price=Decimal("65000"),
        )
        assert d.allowed is False
        assert "exposure" in d.reason

    def test_qty_below_min_rejected(self, signal, snapshot):
        rules = SymbolRules(
            symbol="BTCUSDT", min_qty=Decimal("1"), step_size=Decimal("1"), min_notional=Decimal("5")
        )
        eng = RiskEngine()
        d = eng.evaluate(signal, snapshot, symbol_rules=rules, mark_price=Decimal("65000"))
        assert d.allowed is False


class TestEntryPlanner:
    def test_plans_market_entry(self, signal, snapshot):
        risk = RiskDecision(
            allowed=True,
            reason="ok",
            leverage=10,
            notional_usdt=Decimal("100"),
            quantity=Decimal("0.001"),
            max_loss_usdt=Decimal("10"),
        )
        planner = EntryPlanner()
        tid = uuid4()
        plan = planner.plan(trade_id=tid, signal=signal, snapshot=snapshot, risk=risk)
        assert plan.blocked is False
        assert plan.quantity == Decimal("0.001")
        assert plan.client_order_id.startswith("sst-")
        assert plan.snapshot_hash == "abc123"
        assert plan.price is None

    def test_blocked_when_risk_rejects(self, signal, snapshot):
        risk = RiskDecision(
            allowed=False, reason="exposure limit", leverage=1, notional_usdt=Decimal("0")
        )
        planner = EntryPlanner()
        plan = planner.plan(trade_id=uuid4(), signal=signal, snapshot=snapshot, risk=risk)
        assert plan.blocked is True
        assert plan.block_reason == "exposure limit"
        assert plan.quantity == Decimal("0")

    def test_late_entry_block_long(self, signal, snapshot):
        signal = signal.model_copy(
            update={"entry_type": EntryType.LIMIT, "entry_price": Decimal("65000")}
        )
        risk = RiskDecision(
            allowed=True,
            reason="ok",
            leverage=10,
            notional_usdt=Decimal("100"),
            quantity=Decimal("0.001"),
        )
        planner = EntryPlanner()
        plan = planner.plan(
            trade_id=uuid4(),
            signal=signal,
            snapshot=snapshot,
            risk=risk,
            mark_price=Decimal("66000"),
        )
        assert plan.blocked is True
        assert "late entry" in (plan.block_reason or "")

    def test_deterministic_client_order_id(self, signal, snapshot):
        risk = RiskDecision(
            allowed=True,
            reason="ok",
            leverage=10,
            notional_usdt=Decimal("100"),
            quantity=Decimal("0.001"),
        )
        tid = uuid4()
        planner = EntryPlanner()
        p1 = planner.plan(trade_id=tid, signal=signal, snapshot=snapshot, risk=risk, attempt=0)
        p2 = planner.plan(trade_id=tid, signal=signal, snapshot=snapshot, risk=risk, attempt=0)
        assert p1.client_order_id == p2.client_order_id
        p3 = planner.plan(trade_id=tid, signal=signal, snapshot=snapshot, risk=risk, attempt=1)
        assert p3.client_order_id != p1.client_order_id


class TestProtectionPlanner:
    def test_initial_stop_from_signal(self, signal, snapshot):
        pp = ProtectionPlanner()
        plan = pp.initial_stop(signal, snapshot)
        assert plan.is_protected is True
        assert plan.initial_stop == Decimal("64000")
        assert plan.safer_stop == Decimal("64000")

    def test_missing_sl_not_protected(self, signal, snapshot):
        signal = signal.model_copy(update={"stop_loss": None})
        pp = ProtectionPlanner()
        plan = pp.initial_stop(signal, snapshot)
        assert plan.is_protected is False
        assert "missing" in plan.reason

    def test_sl_mode_none_allows_unprotected(self, signal, snapshot):
        signal = signal.model_copy(update={"stop_loss": None})
        snapshot = snapshot.model_copy(update={"sl_mode": SlMode.NONE})
        pp = ProtectionPlanner()
        plan = pp.initial_stop(signal, snapshot)
        assert plan.is_protected is False
        assert plan.reason == "sl_mode=none"

    def test_after_tp_break_even_never_worsens(self, snapshot):
        pp = ProtectionPlanner()
        plan = pp.after_tp(
            side=Side.LONG,
            current_stop=Decimal("64000"),
            entry_price=Decimal("65000"),
            hit_tp=TakeProfitLevel(index=1, price=Decimal("66000")),
            snapshot=snapshot.model_copy(update={"sl_mode": SlMode.BREAK_EVEN}),
        )
        assert plan.safer_stop == Decimal("65000")
        assert plan.is_protected is True

    def test_never_worsen_long(self):
        pp = ProtectionPlanner()
        assert pp.never_worsen(Side.LONG, Decimal("64000"), Decimal("63000")) == Decimal("64000")
        assert pp.never_worsen(Side.LONG, Decimal("64000"), Decimal("64500")) == Decimal("64500")

    def test_never_worsen_short(self):
        pp = ProtectionPlanner()
        assert pp.never_worsen(Side.SHORT, Decimal("66000"), Decimal("67000")) == Decimal("66000")
        assert pp.never_worsen(Side.SHORT, Decimal("66000"), Decimal("65500")) == Decimal("65500")


class TestConflictResolver:
    def test_no_open_accepts(self, signal):
        r = ConflictResolver()
        d = r.resolve(signal, policy=ConflictPolicy.REJECT_SECOND, open_trades=[])
        assert d.action == ConflictAction.ACCEPT

    def test_opposite_always_reject(self, signal):
        r = ConflictResolver()
        open_t = [
            OpenTradeRef(
                trade_id="t1", source_id="other", symbol="BTCUSDT", side=Side.SHORT, account_id="a1"
            )
        ]
        d = r.resolve(
            signal, policy=ConflictPolicy.ALLOW_SAME_DIRECTION_SCALE_IN, open_trades=open_t
        )
        assert d.action == ConflictAction.REJECT
        assert "opposite" in d.reason

    def test_reject_second_policy(self, signal):
        r = ConflictResolver()
        open_t = [
            OpenTradeRef(
                trade_id="t1", source_id="src_alpha", symbol="BTCUSDT", side=Side.LONG, account_id="a1"
            )
        ]
        d = r.resolve(signal, policy=ConflictPolicy.REJECT_SECOND, open_trades=open_t)
        assert d.action == ConflictAction.REJECT

    def test_scale_in_allowed(self, signal):
        r = ConflictResolver()
        open_t = [
            OpenTradeRef(
                trade_id="t1", source_id="src_alpha", symbol="BTCUSDT", side=Side.LONG, account_id="a1"
            )
        ]
        d = r.resolve(
            signal, policy=ConflictPolicy.ALLOW_SAME_DIRECTION_SCALE_IN, open_trades=open_t
        )
        assert d.action == ConflictAction.SCALE_IN

    def test_source_priority(self, signal):
        r = ConflictResolver()
        open_t = [
            OpenTradeRef(
                trade_id="t1", source_id="src_high", symbol="BTCUSDT", side=Side.LONG, account_id="a1"
            )
        ]
        d = r.resolve(
            signal,
            policy=ConflictPolicy.SOURCE_PRIORITY,
            open_trades=open_t,
            source_priority={"src_high": 10, "src_alpha": 5},
        )
        assert d.action == ConflictAction.REJECT

    def test_manual_review_policy(self, signal):
        r = ConflictResolver()
        open_t = [
            OpenTradeRef(
                trade_id="t1", source_id="x", symbol="BTCUSDT", side=Side.LONG, account_id="a1"
            )
        ]
        d = r.resolve(signal, policy=ConflictPolicy.MANUAL_REVIEW, open_trades=open_t)
        assert d.action == ConflictAction.MANUAL_REVIEW


class TestTradeStateMachine:
    def test_valid_transitions(self):
        sm = TradeStateMachine()
        assert sm.can_transition(TradeStatus.PENDING_ENTRY, TradeStatus.OPEN) is True
        assert sm.can_transition(TradeStatus.OPEN, TradeStatus.CLOSING) is True
        assert sm.can_transition(TradeStatus.CLOSING, TradeStatus.CLOSED) is True
        assert sm.can_transition(TradeStatus.CLOSED, TradeStatus.ARCHIVED) is True

    def test_illegal_transition_raises(self):
        sm = TradeStateMachine()
        assert sm.can_transition(TradeStatus.CLOSED, TradeStatus.OPEN) is False
        with pytest.raises(ValueError, match="illegal transition"):
            sm.transition(TradeStatus.CLOSED, TradeStatus.OPEN)

    def test_archived_terminal(self):
        sm = TradeStateMachine()
        assert sm.can_transition(TradeStatus.ARCHIVED, TradeStatus.OPEN) is False
