"""
Configuration loader from .env file.
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration."""

    # Binance API
    BINANCE_API_KEY = os.getenv("BINANCE_API_KEY", "")
    BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET", "")
    BINANCE_USE_TESTNET = os.getenv("BINANCE_USE_TESTNET", "False") == "True"

    # Account
    ACCOUNT_EQUITY = float(os.getenv("ACCOUNT_EQUITY", "10000"))
    RISK_PER_TRADE = float(os.getenv("RISK_PER_TRADE", "0.007"))
    MAX_LEVERAGE = float(os.getenv("MAX_LEVERAGE", "5"))

    # Directories
    DATA_DIR = os.getenv("DATA_DIR", "./data")
    CHARTS_DIR = os.getenv("CHARTS_DIR", "./charts")
    LOGS_DIR = os.getenv("LOGS_DIR", "./logs")

    # Trading
    TRADE_PAIRS = os.getenv("TRADE_PAIRS", "BTCUSDT,ETHUSDT").split(",")
    TRADING_TIMEFRAMES = os.getenv("TRADING_TIMEFRAMES", "1h,4h").split(",")

    # System
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    DEBUG_MODE = os.getenv("DEBUG_MODE", "False") == "True"
    SKIP_WEAK_SIGNALS = os.getenv("SKIP_WEAK_SIGNALS", "True") == "True"

    @classmethod
    def validate(cls):
        """Validate config on startup."""
        os.makedirs(cls.DATA_DIR, exist_ok=True)
        os.makedirs(cls.CHARTS_DIR, exist_ok=True)
        os.makedirs(cls.LOGS_DIR, exist_ok=True)
