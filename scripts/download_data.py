#!/usr/bin/env python
"""
Download historical OHLCV data from Binance.

Fetches real market data directly from Binance Futures API.
No sample data - uses actual Binance klines.

Usage:
    python scripts/download_data.py --pair BTCUSDT --timeframe 1h --days 180
"""

import argparse
import os
from datetime import datetime, timedelta
from trading_system.data.data_loader import DataLoader
from trading_system.utils.logger import get_logger

logger = get_logger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="Download historical OHLCV data from Binance API"
    )
    parser.add_argument(
        "--pair",
        default="BTCUSDT",
        help="Trading pair (default: BTCUSDT)",
    )
    parser.add_argument(
        "--timeframe",
        default="1h",
        help="Candle timeframe: 1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w (default: 1h)",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=180,
        help="Number of days of historical data to fetch (default: 180)",
    )
    parser.add_argument(
        "--output",
        default="data",
        help="Output directory for CSV (default: data)",
    )
    parser.add_argument(
        "--api-key",
        help="Binance API key (optional for public data)",
    )
    parser.add_argument(
        "--api-secret",
        help="Binance API secret (optional for public data)",
    )

    args = parser.parse_args()

    # Create output directory if it doesn't exist
    os.makedirs(args.output, exist_ok=True)

    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=args.days)

    logger.info(
        f"Downloading {args.pair} {args.timeframe} data from "
        f"{start_date.date()} to {end_date.date()}"
    )

    try:
        # Fetch real data from Binance
        candles = DataLoader.load_from_binance_api(
            pair=args.pair,
            timeframe=args.timeframe,
            start_date=start_date,
            end_date=end_date,
            api_key=args.api_key,
            api_secret=args.api_secret,
        )

        if not candles:
            logger.warning("No candles fetched")
            return

        # Save to CSV
        csv_filename = f"{args.pair.lower()}_{args.timeframe}.csv"
        csv_path = os.path.join(args.output, csv_filename)

        # Convert to pandas and save
        import pandas as pd

        data = {
            "timestamp": [c.timestamp for c in candles],
            "open": [c.open for c in candles],
            "high": [c.high for c in candles],
            "low": [c.low for c in candles],
            "close": [c.close for c in candles],
            "volume": [c.volume for c in candles],
        }

        df = pd.DataFrame(data)
        df.to_csv(csv_path, index=False)

        logger.info(
            f"Successfully saved {len(candles)} candles to {csv_path}"
        )
        print(f"\n✓ Downloaded {len(candles)} real {args.pair} {args.timeframe} candles")
        print(f"✓ Saved to: {csv_path}")
        print(f"✓ Date range: {candles[0].timestamp.date()} to {candles[-1].timestamp.date()}")

    except Exception as e:
        logger.error(f"Error downloading data: {e}")
        print(f"\n✗ Error: {e}")
        raise


if __name__ == "__main__":
    main()
