"""
Constants and magic numbers used throughout the system.
"""

# Risk Management
HARD_RISK_CAP = 0.007  # 0.7% per trade
MAX_LEVERAGE = 5.0

# Volume Validation
VOLUME_MULTIPLIER_MIN = 1.5

# ATR/Volatility
ATR_MULTIPLIER_MIN = 1.2

# Consecutive Candles
CONSECUTIVE_CANDLES_MIN = 2

# Technical Indicators
EMA_9_PERIOD = 9
EMA_21_PERIOD = 21
EMA_50_PERIOD = 50
ATR_PERIOD = 14
RSI_PERIOD = 14
VOLUME_MA_PERIOD = 20

# Swing Detection
SWING_HIGH_PERIOD_SHORT = 5
SWING_HIGH_PERIOD_LONG = 20

# R:R Ratios (Service 5)
RR_WEAK = 1.0
RR_MODERATE = 1.5
RR_STRONG = 2.0
RR_EXCEPTIONAL = 2.5

# Breakout Grades
GRADE_WEAK = "WEAK"
GRADE_MODERATE = "MODERATE"
GRADE_STRONG = "STRONG"
GRADE_EXCEPTIONAL = "EXCEPTIONAL"
