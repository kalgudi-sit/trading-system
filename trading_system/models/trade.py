from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List


class TradeStatus(Enum):
    """Trade lifecycle status."""
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"


class TradeDirection(Enum):
    """Trade direction."""
    LONG = "LONG"
    SHORT = "SHORT"


class ExitReason(Enum):
    """Reason for trade closure."""
    TAKE_PROFIT_LEVEL_1 = "TAKE_PROFIT_LEVEL_1"
    TAKE_PROFIT_LEVEL_2 = "TAKE_PROFIT_LEVEL_2"
    TAKE_PROFIT_FULL = "TAKE_PROFIT_FULL"
    STOP_LOSS = "STOP_LOSS"
    REVERSAL_SIGNAL = "REVERSAL_SIGNAL"
    TIME_BASED_EXIT = "TIME_BASED_EXIT"
    MANUAL_EXIT = "MANUAL_EXIT"
    LIQUIDATION = "LIQUIDATION"


@dataclass
class TradeLog:
    """
    Complete record of a single trade (open + close).
    Used for backtesting results and analytics.
    """
    trade_id: str
    entry_time: datetime
    exit_time: Optional[datetime] = None
    exit_reason: Optional[ExitReason] = None
    
    pair: str
    timeframe: str
    direction: TradeDirection
    status: TradeStatus = TradeStatus.OPEN
    
    # Entry
    entry_price: float = 0.0
    position_size_usdt: float = 0.0
    position_size_contracts: float = 0.0
    
    # Risk/Reward
    stop_loss: float = 0.0
    take_profit_primary: float = 0.0
    take_profit_scaled: List[float] = field(default_factory=list)
    rr_ratio: float = 0.0
    notional_risk: float = 0.0  # $ amount at risk (0.7% max)
    notional_risk_pct: float = 0.007
    
    # Breakout quality
    breakout_grade: str = ""  # WEAK/MODERATE/STRONG/EXCEPTIONAL
    breakout_score: Optional[float] = None
    signal_type: str = ""
    
    # Exit
    exit_price: Optional[float] = None
    pnl: float = 0.0  # $ profit/loss
    pnl_pct: float = 0.0  # % return
    
    # Metadata
    notes: str = ""
    
    @property
    def is_winner(self) -> bool:
        """True if trade is profitable."""
        return self.pnl > 0
    
    @property
    def is_open(self) -> bool:
        """True if trade is still open."""
        return self.status == TradeStatus.OPEN
