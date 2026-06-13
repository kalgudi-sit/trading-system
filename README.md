# Trading System: Binance Futures

**A production-grade, resilient trading system for BTC/ETH futures on Binance.**

Built with:
- 6 core microservices (Signal → Validation → Strength → Risk → Parameters → Execution)
- In-memory backtesting with chart visualization
- Live Binance Futures trading capability
- 0.7% hard risk cap per trade
- Dynamic R:R ratios based on breakout strength

## Quick Start

### 1. Setup
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure
```bash
cp .env.example .env
# Edit .env with your Binance API keys (for live trading)
```

### 3. Run Backtest
```bash
python scripts/backtest_runner.py --pair BTCUSDT --timeframe 1h --csv data/btcusdt_1h.csv
```

### 4. View Results
Backtest results are saved as interactive HTML charts in `./charts/`

## Architecture

See [SYSTEM_ARCHITECTURE.md](./SYSTEM_ARCHITECTURE.md) for complete design documentation.

### 6 Services
1. **Signal Generator** — Detects all breakout signals
2. **Signal Validator** — Volume-based filtering (>1.5x)
3. **Breakout Strength Scorer** — 0-100 strength assessment
4. **Risk Engine** — Position sizing, 0.7% hard cap
5. **Dynamic Parameters** — TP/SL calculation based on strength
6. **Execution Engine** — Trade management & Binance API integration

## Directory Structure

```
trading-system/
├── trading_system/
│   ├── __init__.py
│   ├── config.py                 # Configuration loading
│   ├── backtest.py               # Backtest runner
│   ├── live_trader.py            # Live trading runner
│   ├── models/
│   │   ├── __init__.py
│   │   ├── signal.py             # Signal data models
│   │   ├── trade.py              # Trade data models
│   │   └── candle.py             # OHLCV candle models
│   ├── services/
│   │   ├── __init__.py
│   │   ├── signal_generator.py   # Service 1
│   │   ├── signal_validator.py   # Service 2
│   │   ├── strength_scorer.py    # Service 3
│   │   ├── risk_engine.py        # Service 4
│   │   ├── parameters_engine.py  # Service 5
│   │   └── execution_engine.py   # Service 6
│   ├── data/
│   │   ├── __init__.py
│   │   ├── data_loader.py        # Load OHLCV from CSV/API
│   │   └── candle_processor.py   # Calculate indicators (EMA, ATR, etc.)
│   ├── connectors/
│   │   ├── __init__.py
│   │   └── binance_connector.py  # Binance API integration
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── logger.py             # Logging setup
│   │   ├── constants.py          # Magic numbers
│   │   └── validators.py         # Input validation
│   └── visualization/
│       ├── __init__.py
│       ├── backtest_charts.py    # Plotly chart generation
│       └── trade_plotter.py      # Trade visualization
├── tests/
│   ├── __init__.py
│   ├── test_signal_generator.py
│   ├── test_signal_validator.py
│   ├── test_strength_scorer.py
│   ├── test_risk_engine.py
│   └── test_integration.py
├── scripts/
│   ├── download_data.py          # Fetch historical OHLCV
│   ├── backtest_runner.py        # CLI backtest entry point
│   └── live_trader_runner.py     # CLI live trading entry point
├── charts/                        # Output directory for backtest charts
├── logs/                          # Application logs
├── .env.example
├── .gitignore
├── requirements.txt
├── README.md
└── SYSTEM_ARCHITECTURE.md
```

## Configuration

### .env.example
```
# Binance API (for live trading only)
BINANCE_API_KEY=your_api_key
BINANCE_API_SECRET=your_api_secret

# Trading Parameters
ACCOUNT_EQUITY=10000  # Starting balance for backtest
RISK_PER_TRADE=0.007  # 0.7% hard cap

# Data
DATA_DIR=./data
CHARTS_DIR=./charts
LOGS_DIR=./logs

# Trading
TRADE_PAIRS=BTCUSDT,ETHUSDT
TRADING_TIMEFRAMES=1h,4h
LEVERAGE=5
```

## Running Backtests

### Simple Backtest (6 months of data)
```bash
python scripts/backtest_runner.py \
  --pair BTCUSDT \
  --timeframe 1h \
  --csv data/btcusdt_1h.csv
```

### Output
- Interactive HTML chart showing:
  - Price chart with buy/sell signals
  - Equity curve (growing/shrinking account balance)
  - Drawdown visualization
  - Trade-by-trade P&L breakdown
- Console summary:
  - Win rate
  - Profit factor
  - Max drawdown
  - Avg trade

## Running Live (Binance)

### DANGER: Read First
- Start with **small position sizes** (0.1% account)
- Test on **testnet first** (not implemented yet, but easy to add)
- Monitor manually for first 10+ trades
- **API keys should NEVER be committed to git**

### Start Live Trading
```bash
python scripts/live_trader_runner.py \
  --pair BTCUSDT \
  --timeframe 1h \
  --mode live
```

## Key Files to Understand First

1. **models/signal.py** — Signal structure
2. **models/trade.py** — Trade structure
3. **services/signal_generator.py** — How signals are detected
4. **services/signal_validator.py** — How signals are validated
5. **backtest.py** — Main backtesting loop

## Development Workflow

1. Implement service on `dev/phase-X` branch
2. Add unit tests
3. Run backtest
4. Review results
5. Merge to main

## Next Phase

- [ ] Implement Signal Generator (Phase 2)
- [ ] Implement Signal Validator (Phase 2)
- [ ] Implement backtester with chart output (Phase 2)
- [ ] Implement Strength Scorer (Phase 3)
- [ ] Implement Risk Engine (Phase 3)
- [ ] Implement Parameters Engine (Phase 3)
- [ ] Integrate Binance API (Phase 4)
- [ ] Live trading (Phase 4)

## Support

For issues or questions, check SYSTEM_ARCHITECTURE.md for design decisions.
