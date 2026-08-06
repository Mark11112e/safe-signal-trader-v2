"""GenericStructuredParser v1 – deterministic line-based format for tests & bootstrap.

Supported (case-insensitive, whitespace tolerant):

    SIGNAL LONG BTCUSDT
    ENTRY 65000          # optional for MARKET
    SL 64000
    TP1 66000
    TP2 67000
    ...
    TP5 70000
    LEV 10

Side keywords: LONG / SHORT / BUY / SELL
Symbol: alphanum + optional USDT/USD suffix (normalized to upper, append USDT if missing)
"""
from __future__ import annotations

import hashlib
import re
from decimal import Decimal, InvalidOperation
from typing import Any

from signal_bot.domain.enums import EntryType, Side
from signal_bot.domain.models import NormalizedSignal, TakeProfitLevel
from signal_bot.parsers.interfaces import SignalParser

_SIDE_MAP = {
    "LONG": Side.LONG,
    "BUY": Side.LONG,
    "SHORT": Side.SHORT,
    "SELL": Side.SHORT,
}

_SIGNAL_RE = re.compile(
    r"^\s*SIGNAL\s+(?P<side>LONG|SHORT|BUY|SELL)\s+(?P<symbol>[A-Za-z0-9]+)\s*$",
    re.IGNORECASE | re.MULTILINE,
)
_ENTRY_RE = re.compile(r"^\s*ENTRY\s+(?P<price>[\d.]+)\s*$", re.IGNORECASE | re.MULTILINE)
_SL_RE = re.compile(r"^\s*SL\s+(?P<price>[\d.]+)\s*$", re.IGNORECASE | re.MULTILINE)
_TP_RE = re.compile(
    r"^\s*TP(?P<idx>[1-5])\s+(?P<price>[\d.]+)(?:\s+(?P<pct>[\d.]+)%?)?\s*$",
    re.IGNORECASE | re.MULTILINE,
)
_LEV_RE = re.compile(r"^\s*LEV(?:ERAGE)?\s+(?P<lev>\d+)\s*$", re.IGNORECASE | re.MULTILINE)


def _to_decimal(s: str) -> Decimal | None:
    try:
        return Decimal(s)
    except (InvalidOperation, ValueError):
        return None


def _normalize_symbol(raw: str) -> str:
    s = raw.upper().strip()
    if not s.endswith(("USDT", "USD", "USDC")):
        s = s + "USDT"
    return s


def _compute_raw_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:32]


class GenericStructuredParser:
    """Concrete SignalParser implementation (parser_id=generic_structured, version=1.0.0)."""

    parser_id: str = "generic_structured"
    parser_version: str = "1.0.0"

    def can_parse(self, text: str) -> bool:
        if not text or len(text.strip()) < 8:
            return False
        return bool(_SIGNAL_RE.search(text))

    def parse(
        self,
        text: str,
        *,
        source_id: str,
        message_id: str | None = None,
        raw_hash: str | None = None,
    ) -> NormalizedSignal | None:
        if not self.can_parse(text):
            return None

        m_sig = _SIGNAL_RE.search(text)
        if not m_sig:
            return None

        side = _SIDE_MAP[m_sig.group("side").upper()]
        symbol = _normalize_symbol(m_sig.group("symbol"))

        entry_price: Decimal | None = None
        m_entry = _ENTRY_RE.search(text)
        if m_entry:
            entry_price = _to_decimal(m_entry.group("price"))

        stop_loss: Decimal | None = None
        m_sl = _SL_RE.search(text)
        if m_sl:
            stop_loss = _to_decimal(m_sl.group("price"))

        tps: list[TakeProfitLevel] = []
        for m_tp in _TP_RE.finditer(text):
            idx = int(m_tp.group("idx"))
            price = _to_decimal(m_tp.group("price"))
            if price is None:
                continue
            pct_raw = m_tp.group("pct")
            size_pct = _to_decimal(pct_raw) if pct_raw else None
            tps.append(TakeProfitLevel(index=idx, price=price, size_pct=size_pct))
        tps.sort(key=lambda t: t.index)

        leverage: int | None = None
        m_lev = _LEV_RE.search(text)
        if m_lev:
            leverage = int(m_lev.group("lev"))

        entry_type = EntryType.LIMIT if entry_price is not None else EntryType.MARKET
        rh = raw_hash or _compute_raw_hash(text)

        signal = NormalizedSignal(
            source_id=source_id,
            parser_id=self.parser_id,
            parser_version=self.parser_version,
            symbol=symbol,
            side=side,
            entry_type=entry_type,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profits=tuple(tps),
            leverage=leverage,
            raw_message_id=message_id,
            raw_hash=rh,
        )
        return self.validate(signal)

    def validate(self, signal: NormalizedSignal) -> NormalizedSignal:
        if signal.parser_id != self.parser_id:
            raise ValueError(f"parser_id mismatch: expected {self.parser_id}")
        if not signal.symbol:
            raise ValueError("symbol required")
        if signal.side not in (Side.LONG, Side.SHORT):
            raise ValueError("invalid side")
        if signal.leverage is not None and (signal.leverage < 1 or signal.leverage > 125):
            raise ValueError("leverage out of range 1..125")
        # TPs already validated by Pydantic (unique indices, pct bounds)
        return signal


# Singleton for convenience
generic_structured_v1 = GenericStructuredParser()
