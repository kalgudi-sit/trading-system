"""
Backtest Runner: Simulates trading over historical data.

Walk-forward backtester:
1. Load historical OHLCV candles
2. For each candle:
   a. Process indicators
   b. Run all 6 services (Signal → Validation → Score → Risk → Parameters → Execution)
   c. Manage open trades
   d. Record results
3. Generate charts and report

All in-memory, no database.
"""

from typing import List, Optional
from datetime import datetime
import numpy as np

from trading_system.data import DataLoader, CandleProcessor
from trading_system.models import (
    Candle,
    CandleData,
    Signal,
    TradeLog,
    TradeStatus,
    ExitReason,
)
from trading_system.services import (
    SignalGenerator,
    SignalValidator,
    StrengthScorer,
    RiskEngine,
    ParametersEngine,
    ExecutionEngine,
)
from trading_system.visualization import BacktestCharts
from trading_system.utils.logger import get_logger

logger = get_logger(__name__)


class Backtester:
    """Main backtesting engine."""

    def __init__(self, account_equity: float = 10000.0):
        """
        Initialize backtester.
        
        Args:
            account_equity: Starting account balance
        """
        self.account_equity = account_equity
        self.current_equity = account_equity
        
        # Services
        self.signal_gen = SignalGenerator()
        self.validator = SignalValidator()
        self.scorer = StrengthScorer()
        self.risk_engine = RiskEngine(account_equity)
        self.params_engine = ParametersEngine()
        self.executor = ExecutionEngine()
        
        # Results tracking
        self.closed_trades: List[TradeLog] = []
        self.equity_history: List[float] = [account_equity]
        self.signals_generated: List[Signal] = []
        self.signals_validated: int = 0
        self.signals_rejected: int = 0

    def run_backtest(
        self,
        pair: str,
        timeframe: str,
        csv_file: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> dict:
        """
        Run complete backtest.
        
        Args:
            pair: Trading pair (BTCUSDT, etc.)
            timeframe: Candle timeframe (1h, 4h, etc.)
            csv_file: Path to historical data CSV
            start_date: Optional backtest start
            end_date: Optional backtest end
        
        Returns:
            Dictionary with backtest statistics
        """
        logger.info(f"Starting backtest for {pair} {timeframe}...")
        
        # Load data
        raw_candles = DataLoader.load_csv(
            csv_file, pair, timeframe, start_date, end_date
        )
        
        # Process indicators
        candles = CandleProcessor.process(raw_candles)
        
        logger.info(f"Backtesting {len(candles)} candles...")
        
        # Walk forward through each candle
        for i, current_candle in enumerate(candles):
            # Need at least 50 candles for all indicators
            if i < 50:
                continue
            
            previous_candles = candles[max(0, i-50):i]
            
            # === PIPELINE START ===
            
            # Service 1: Generate signals
            signals = self.signal_gen.detect_signals(
                current_candle, previous_candles, pair, timeframe
            )
            self.signals_generated.extend(signals)
            
            # Service 2: Validate each signal
            for signal in signals:
                validation = self.validator.validate(
                    signal, current_candle, previous_candles
                )
                
                if validation.validation_result == "REJECTED":
                    self.signals_rejected += 1
                    continue
                
                self.signals_validated += 1
                
                # Service 3: Score breakout strength
                strength_result = self.scorer.score(
                    signal, current_candle, previous_candles
                )
                
                # Service 4: Calculate position size
                risk_result = self.risk_engine.calculate_position_size(
                    current_candle.candle.close,
                    current_candle.candle.close * 0.995,  # Example: 0.5% stop
                    strength_result.grade,
                )
                
                if not risk_result.approved:
                    logger.debug(f"Trade rejected: {risk_result.rejection_reason}")
                    continue
                
                # Service 5: Calculate parameters
                params = self.params_engine.calculate_parameters(
                    current_candle.candle.close,
                    current_candle.candle.close * 0.995,
                    strength_result.grade,
                    signal.direction.value,
                )
                
                # Service 6: Execute trade
                trade = self.executor.execute_trade(
                    pair=pair,
                    timeframe=timeframe,
                    direction=signal.direction.value,
                    entry_price=params.entry_price,
                    stop_loss=params.stop_loss_price,
                    take_profit_primary=params.take_profit_primary,
                    take_profit_scaled=params.take_profit_scaled,
                    position_size_usdt=risk_result.position_size_usdt,
                    position_size_contracts=risk_result.position_size_contracts,
                    notional_risk=risk_result.notional_risk,
                    breakout_grade=strength_result.grade,
                    rr_ratio=params.rr_ratio,
                    signal_type=signal.signal_type.value,
                )
            
            # === CHECK OPEN TRADES ===
            self._update_trades(current_candle)
            
            # Update equity
            self.equity_history.append(self.current_equity)
        
        # === GENERATE REPORT ===
        stats = self._calculate_statistics()
        
        logger.info(f"Backtest complete. Generated {len(self.closed_trades)} trades.")
        
        return stats

    def _update_trades(self, current_candle: CandleData) -> None:
        """Update open trades, check for exits."""
        # TODO: Implement trade management (check SL/TP, update equity)
        pass

    def _calculate_statistics(self) -> dict:
        """Calculate backtest statistics."""
        if not self.closed_trades:
            return {"status": "No trades executed"}
        
        winners = [t for t in self.closed_trades if t.is_winner]
        losers = [t for t in self.closed_trades if not t.is_winner]
        
        total_pnl = sum(t.pnl for t in self.closed_trades)
        
        stats = {
            "total_trades": len(self.closed_trades),
            "winning_trades": len(winners),
            "losing_trades": len(losers),
            "win_rate": len(winners) / len(self.closed_trades) * 100,
            "avg_win": sum(t.pnl for t in winners) / len(winners) if winners else 0,
            "avg_loss": sum(t.pnl for t in losers) / len(losers) if losers else 0,
            "total_pnl": total_pnl,
            "final_equity": self.current_equity,
            "return_pct": (self.current_equity - self.account_equity) / self.account_equity * 100,
        }
        
        return stats
