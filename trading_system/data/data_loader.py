"""
Data Loader: Load OHLCV candles from CSV or Binance API.

Supports:
- CSV loading (for backtesting with existing data)
- Binance API loading (for real live data)
"""

from typing import List, Optional
from datetime import datetime
import pandas as pd
from trading_system.models import Candle
from trading_system.utils.logger import get_logger

logger = get_logger(__name__)


class DataLoader:
    """Load historical OHLCV data from CSV or Binance API."""

    @staticmethod
    def load_csv(
        filepath: str,
        pair: str,
        timeframe: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Candle]:
        """
        Load candles from CSV file.
        
        Args:
            filepath: Path to CSV file
            pair: Trading pair (BTCUSDT, etc.)
            timeframe: Candle timeframe (1h, 4h, etc.)
            start_date: Optional filter start
            end_date: Optional filter end
        
        Returns:
            List of Candle objects
        """
        logger.info(f"Loading data from {filepath}...")
        
        df = pd.read_csv(filepath)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        
        if start_date:
            df = df[df["timestamp"] >= start_date]
        if end_date:
            df = df[df["timestamp"] <= end_date]
        
        candles = []
        for _, row in df.iterrows():
            candle = Candle(
                timestamp=row["timestamp"],
                open=row["open"],
                high=row["high"],
                low=row["low"],
                close=row["close"],
                volume=row["volume"],
                pair=pair,
                timeframe=timeframe,
            )
            candles.append(candle)
        
        logger.info(f"Loaded {len(candles)} candles from CSV")
        return candles

    @staticmethod
    def load_from_binance_api(
        pair: str,
        timeframe: str,
        start_date: datetime,
        end_date: datetime,
        api_key: str = None,
        api_secret: str = None,
    ) -> List[Candle]:
        """
        Load candles from Binance API (real data).
        
        Args:
            pair: Trading pair (BTCUSDT, ETHUSDT, etc.)
            timeframe: Candle interval (1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w)
            start_date: Start datetime for historical data
            end_date: End datetime for historical data
            api_key: Binance API key (optional for public data)
            api_secret: Binance API secret (optional for public data)
        
        Returns:
            List of Candle objects with real Binance data
        """
        from trading_system.connectors.binance_connector import BinanceConnector
        
        logger.info(f"Loading {pair} {timeframe} from Binance API...")
        
        connector = BinanceConnector(api_key=api_key, api_secret=api_secret)
        
        # Validate pair exists
        if not connector.validate_pair(pair):
            raise ValueError(f"Invalid pair: {pair}")
        
        # Fetch real data from Binance
        candles = connector.fetch_klines(
            pair=pair,
            timeframe=timeframe,
            start_date=start_date,
            end_date=end_date,
        )
        
        logger.info(f"Loaded {len(candles)} real candles from Binance API")
        return candles
