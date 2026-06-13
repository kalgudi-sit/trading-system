from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any


class SignalType(Enum):
    """Possible signal types (Service 1: Signal Generator)."""
    STRUCTURE_BREAK = "structure_break"
    EMA_CROSSOVER = "ema_crossover"
    VOLATILITY_EXPANSION = "volatility_expansion"
    MOMENTUM_DIVERGENCE = "momentum_divergence"
    TREND_CONTINUATION = "trend_continuation"
    VOLUME_SPIKE = "volume_spike"


class SignalDirection(Enum):
    """Signal direction."""
    LONG = "LONG"
    SHORT = "SHORT"


@dataclass
class Signal:
    """
    Raw signal from Service 1: Signal Generator.
    No validation, filtering, or risk assessment yet.
    """
    signal_id: str
    timestamp: datetime
    pair: str
    timeframe: str
    signal_type: SignalType
    direction: SignalDirection
    breakout_price: float
    signal_confidence: float = 0.0  # 0-1, initially low
    notes: str = ""


@dataclass
class SignalValidationResult:
    """
    Output from Service 2: Signal Validator.
    Contains all validation checks and final decision.
    """
    signal_id: str
    validation_result: str  # "VALID" or "REJECTED"
    validation_confidence: float  # 0-1
    
    # Individual checks
    volume_expansion_pass: bool
    volume_expansion_ratio: float
    
    structure_confirmation_pass: bool
    
    consecutive_strength_pass: bool
    consecutive_bullish_candles: int
    
    volatility_coherence_pass: bool
    atr_current: float
    atr_avg_20: float
    atr_ratio: float
    
    rejection_reason: Optional[str] = None
    
    @property
    def all_checks_pass(self) -> bool:
        """True only if ALL checks pass."""
        return (
            self.volume_expansion_pass
            and self.structure_confirmation_pass
            and self.consecutive_strength_pass
            and self.volatility_coherence_pass
        )
