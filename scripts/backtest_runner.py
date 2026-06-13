#!/usr/bin/env python
"""
CLI entry point for backtesting.

Usage:
    python scripts/backtest_runner.py --pair BTCUSDT --timeframe 1h --csv data/btcusdt_1h.csv
"""

import argparse
from datetime import datetime
from trading_system.config import Config
from trading_system.backtest import Backtester
from trading_system.utils.logger import get_logger

logger = get_logger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="Run trading system backtest"
    )
    parser.add_argument(
        "--pair",
        default="BTCUSDT",
        help="Trading pair (default: BTCUSDT)",
    )
    parser.add_argument(
        "--timeframe",
        default="1h",
        help="Candle timeframe (default: 1h)",
    )
    parser.add_argument(
        "--csv",
        default="data/btcusdt_1h.csv",
        help="Path to historical data CSV",
    )
    parser.add_argument(
        "--start",
        help="Start date (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--end",
        help="End date (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--equity",
        type=float,
        default=Config.ACCOUNT_EQUITY,
        help="Starting account equity (default: from .env)",
    )

    args = parser.parse_args()

    start_date = datetime.strptime(args.start, "%Y-%m-%d") if args.start else None
    end_date = datetime.strptime(args.end, "%Y-%m-%d") if args.end else None

    # Run backtest
    backtester = Backtester(account_equity=args.equity)
    stats = backtester.run_backtest(
        pair=args.pair,
        timeframe=args.timeframe,
        csv_file=args.csv,
        start_date=start_date,
        end_date=end_date,
    )

    # Print results
    print("\n" + "="*50)
    print("BACKTEST RESULTS")
    print("="*50)
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"{key}: {value:.2f}")
        else:
            print(f"{key}: {value}")
    print("="*50)


if __name__ == "__main__":
    main()
