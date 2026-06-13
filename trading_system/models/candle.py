from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Candle:
    """
    OHLCV candle representation.
    """
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    pair: str
    timeframe: str  # e.g., '1h', '4h', 'daily'

    @property
    def body_size(self) -> float:
        """Absolute size of candle body."""
        return abs(self.close - self.open)

    @property
    def range(self) -> float:
        """High-low range of candle."""
        return self.high - self.low

    @property
    def is_bullish(self) -> bool:
        """True if close > open."""
        return self.close > self.open

    @property
    def is_bearish(self) -> bool:
        """True if close < open."""
        return self.close < self.open

    @property
    def upper_wick(self) -> float:
        """Distance from high to close."""
        return self.high - max(self.open, self.close)

    @property
    def lower_wick(self) -> float:
        """Distance from low to open."""
        return min(self.open, self.close) - self.low


@dataclass
class CandleData:
    """
    Computed indicators for a candle (EMA, ATR, RSI, etc.)
    Calculated by CandelProcessor.
    """
    candle: Candle
    ema_9: Optional[float] = None
    ema_21: Optional[float] = None
    ema_50: Optional[float] = None
    atr_14: Optional[float] = None
    rsi_14: Optional[float] = None
    volume_ma_20: Optional[float] = None
    swing_high_5: Optional[float] = None  # Highest high in last 5 candles
    swing_low_5: Optional[float] = None  # Lowest low in last 5 candles
    swing_high_20: Optional[float] = None
    swing_low_20: Optional[float] = None
