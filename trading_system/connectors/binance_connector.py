"""
Binance API Connector: Fetch real OHLCV data from Binance Futures.

Uses python-binance library to fetch actual market data.
No sample/mock data - all data comes directly from Binance.
"""

from typing import List, Optional
from datetime import datetime, timedelta
import time
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceRequestException
from trading_system.models import Candle
from trading_system.utils.logger import get_logger

logger = get_logger(__name__)

# Binance timeframe mapping
TIMEFRAME_MAPPING = {
    "1m": Client.KLINE_INTERVAL_1MINUTE,
    "5m": Client.KLINE_INTERVAL_5MINUTE,
    "15m": Client.KLINE_INTERVAL_15MINUTE,
    "30m": Client.KLINE_INTERVAL_30MINUTE,
    "1h": Client.KLINE_INTERVAL_1HOUR,
    "4h": Client.KLINE_INTERVAL_4HOUR,
    "1d": Client.KLINE_INTERVAL_1DAY,
    "1w": Client.KLINE_INTERVAL_1WEEK,
}


class BinanceConnector:
    """Fetch real OHLCV data from Binance Futures API."""

    def __init__(self, api_key: str = None, api_secret: str = None):
        """
        Initialize Binance connector.
        
        Args:
            api_key: Binance API key (optional for public data)
            api_secret: Binance API secret (optional for public data)
        """
        self.client = Client(api_key=api_key, api_secret=api_secret)
        self.rate_limit_delay = 0.1  # 100ms between requests to avoid rate limiting
        logger.info("Binance connector initialized")

    def fetch_klines(
        self,
        pair: str,
        timeframe: str,
        start_date: datetime,
        end_date: datetime,
        limit: int = 1000,
    ) -> List[Candle]:
        """
        Fetch OHLCV candles from Binance Futures API.
        
        Args:
            pair: Trading pair (BTCUSDT, ETHUSDT, etc.)
            timeframe: Candle interval (1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w)
            start_date: Start timestamp
            end_date: End timestamp
            limit: Max candles per request (max 1000)
        
        Returns:
            List of Candle objects with real market data
        
        Raises:
            ValueError: If timeframe not supported or invalid pair
            BinanceAPIException: If API returns error
        """
        if timeframe not in TIMEFRAME_MAPPING:
            raise ValueError(f"Unsupported timeframe: {timeframe}")
        
        binance_interval = TIMEFRAME_MAPPING[timeframe]
        candles: List[Candle] = []
        
        current_start = start_date
        request_count = 0
        
        logger.info(
            f"Fetching {pair} {timeframe} from {start_date} to {end_date} "
            f"(real Binance data)"
        )
        
        try:
            while current_start < end_date:
                # Respect rate limits
                if request_count > 0:
                    time.sleep(self.rate_limit_delay)
                
                logger.debug(
                    f"Requesting {pair} candles from {current_start} "
                    f"(batch #{request_count + 1})"
                )
                
                # Fetch batch from Binance
                klines = self.client.futures_klines(
                    symbol=pair,
                    interval=binance_interval,
                    startTime=int(current_start.timestamp() * 1000),
                    endTime=int(end_date.timestamp() * 1000),
                    limit=limit,
                )
                
                if not klines:
                    logger.info(f"No more data available for {pair} {timeframe}")
                    break
                
                # Convert Binance kline format to Candle objects
                for kline in klines:
                    # Binance kline format:
                    # [timestamp, open, high, low, close, volume, ...]
                    timestamp = datetime.fromtimestamp(kline[0] / 1000)
                    
                    candle = Candle(
                        timestamp=timestamp,
                        open=float(kline[1]),
                        high=float(kline[2]),
                        low=float(kline[3]),
                        close=float(kline[4]),
                        volume=float(kline[7]),  # Quote asset volume
                        pair=pair,
                        timeframe=timeframe,
                    )
                    candles.append(candle)
                
                request_count += 1
                
                # Move start time to last fetched candle
                if klines:
                    last_timestamp = datetime.fromtimestamp(klines[-1][0] / 1000)
                    current_start = last_timestamp + timedelta(minutes=1)
                else:
                    break
        
        except BinanceAPIException as e:
            logger.error(f"Binance API error: {e.status_code} - {e.message}")
            raise
        except BinanceRequestException as e:
            logger.error(f"Binance request error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching data: {e}")
            raise
        
        logger.info(
            f"Successfully fetched {len(candles)} real {pair} {timeframe} candles "
            f"({request_count} API requests)"
        )
        return candles

    def fetch_latest_candle(
        self,
        pair: str,
        timeframe: str,
    ) -> Optional[Candle]:
        """
        Fetch the latest candle for a pair.
        
        Args:
            pair: Trading pair (BTCUSDT, ETHUSDT, etc.)
            timeframe: Candle interval
        
        Returns:
            Latest Candle object or None if error
        """
        if timeframe not in TIMEFRAME_MAPPING:
            raise ValueError(f"Unsupported timeframe: {timeframe}")
        
        try:
            binance_interval = TIMEFRAME_MAPPING[timeframe]
            
            klines = self.client.futures_klines(
                symbol=pair,
                interval=binance_interval,
                limit=1,
            )
            
            if not klines:
                return None
            
            kline = klines[0]
            timestamp = datetime.fromtimestamp(kline[0] / 1000)
            
            candle = Candle(
                timestamp=timestamp,
                open=float(kline[1]),
                high=float(kline[2]),
                low=float(kline[3]),
                close=float(kline[4]),
                volume=float(kline[7]),
                pair=pair,
                timeframe=timeframe,
            )
            
            logger.debug(f"Fetched latest {pair} {timeframe}: {candle.close}")
            return candle
        
        except Exception as e:
            logger.error(f"Error fetching latest candle for {pair}: {e}")
            return None

    def get_account_balance(self) -> Optional[float]:
        """
        Get total account balance in USDT.
        
        Returns:
            Account balance or None if error
        """
        try:
            account = self.client.futures_account()
            total_balance = float(account["totalWalletBalance"])
            logger.info(f"Account balance: {total_balance} USDT")
            return total_balance
        except Exception as e:
            logger.error(f"Error fetching account balance: {e}")
            return None

    def validate_pair(self, pair: str) -> bool:
        """
        Validate if pair exists on Binance Futures.
        
        Args:
            pair: Trading pair to validate
        
        Returns:
            True if pair exists, False otherwise
        """
        try:
            exchange_info = self.client.futures_exchange_info()
            symbols = [s["symbol"] for s in exchange_info["symbols"]]
            exists = pair in symbols
            
            if exists:
                logger.debug(f"Pair {pair} validated")
            else:
                logger.warning(f"Pair {pair} not found on Binance Futures")
            
            return exists
        except Exception as e:
            logger.error(f"Error validating pair {pair}: {e}")
            return False
