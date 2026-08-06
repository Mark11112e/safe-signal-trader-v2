"""Domain enumerations – exchange-agnostic."""
from enum import StrEnum

class Side(StrEnum):
    LONG = "LONG"
    SHORT = "SHORT"

class OrderSide(StrEnum):
    BUY = "BUY"
    SELL = "SELL"

class EntryType(StrEnum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"

class JobStatus(StrEnum):
    PENDING = "PENDING"
    CLAIMED = "CLAIMED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    MANUAL_REVIEW = "MANUAL_REVIEW"
    CANCELLED = "CANCELLED"

class TradeStatus(StrEnum):
    PENDING_ENTRY = "PENDING_ENTRY"
    OPEN = "OPEN"
    CLOSING = "CLOSING"
    CLOSED = "CLOSED"
    ARCHIVED = "ARCHIVED"
    MANUAL_REVIEW = "MANUAL_REVIEW"

class SlMode(StrEnum):
    NONE = "none"
    BREAK_EVEN = "break_even"
    FIXED_LOSS_USDT = "fixed_loss_usdt"
    LOCK_PROFIT_USDT = "lock_profit_usdt"
    MOVE_TO_PREVIOUS_TP = "move_to_previous_tp"
    CUSTOM = "custom"

class LastTpMode(StrEnum):
    TRAILING = "trailing"
    TAKE_PROFIT = "take_profit"
    NONE = "none"

class ConflictPolicy(StrEnum):
    REJECT_SECOND = "reject_second"
    ALLOW_SAME_DIRECTION_SCALE_IN = "allow_same_direction_scale_in"
    DEDICATED_ACCOUNT = "dedicated_account"
    SOURCE_PRIORITY = "source_priority"
    MANUAL_REVIEW = "manual_review"

class AppEnv(StrEnum):
    UNIT = "UNIT"
    INTEGRATION = "INTEGRATION"
    TESTNET_DEMO = "TESTNET_DEMO"
    LIVE = "LIVE"
