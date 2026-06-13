"""
Service 6: Execution Engine & Trade Manager

Purpose: Open positions only after ALL checkpoints pass.
Responsibility: Execute trades and manage open positions.

Pre-Execution Checklist:
1. Signal detected ✓
2. Signal validated ✓
3. Breakout strength scored ✓
4. Risk engine approved ✓
5. Dynamic parameters calculated ✓
6. No other position open on this pair
7. Account margin sufficient
8. Order placement won't exceed daily risk
"""

from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime
from trading_system.models import TradeLog, TradeStatus, TradeDirection, ExitReason
from trading_system.utils.logger import get_logger

logger = get_logger(__name__)


class ExecutionEngine:
    """Executes trades and manages open positions."""

    def __init__(self):
        self.open_trades: dict = {}  # {trade_id: TradeLog}
        self.trade_counter = 0

    def execute_trade(
        self,
        pair: str,
        timeframe: str,
        direction: str,  # LONG or SHORT
        entry_price: float,
        stop_loss: float,
        take_profit_primary: float,
        take_profit_scaled: List[float],
        position_size_usdt: float,
        position_size_contracts: float,
        notional_risk: float,
        breakout_grade: str,
        rr_ratio: float,
        signal_type: str,
    ) -> TradeLog:
        """
        Execute a new trade.
        
        Args:
            All trade parameters from previous services
        
        Returns:
            TradeLog object (status=OPEN)
        """
        self.trade_counter += 1
        trade_id = f"trade_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{pair}_{self.trade_counter}"

        trade = TradeLog(
            trade_id=trade_id,
            entry_time=datetime.now(),
            pair=pair,
            timeframe=timeframe,
            direction=TradeDirection.LONG if direction == "LONG" else TradeDirection.SHORT,
            status=TradeStatus.OPEN,
            entry_price=entry_price,
            position_size_usdt=position_size_usdt,
            position_size_contracts=position_size_contracts,
            stop_loss=stop_loss,
            take_profit_primary=take_profit_primary,
            take_profit_scaled=take_profit_scaled,
            rr_ratio=rr_ratio,
            notional_risk=notional_risk,
            notional_risk_pct=notional_risk / 10000,  # Placeholder
            breakout_grade=breakout_grade,
            signal_type=signal_type,
        )

        self.open_trades[trade_id] = trade
        logger.info(
            f"Trade opened: {trade_id} {direction} {pair} @ {entry_price} "
            f"(SL={stop_loss}, TP={take_profit_primary})"
        )

        return trade

    def close_trade(
        self,
        trade_id: str,
        exit_price: float,
        exit_reason: ExitReason,
    ) -> Optional[TradeLog]:
        """
        Close an open trade.
        
        Args:
            trade_id: Trade to close
            exit_price: Exit price
            exit_reason: Why trade is closing
        
        Returns:
            Closed TradeLog with P&L calculated
        """
        if trade_id not in self.open_trades:
            logger.warning(f"Trade not found: {trade_id}")
            return None

        trade = self.open_trades[trade_id]

        # Calculate P&L
        if trade.direction == TradeDirection.LONG:
            pnl = (exit_price - trade.entry_price) * trade.position_size_contracts
            pnl_pct = ((exit_price - trade.entry_price) / trade.entry_price) * 100
        else:  # SHORT
            pnl = (trade.entry_price - exit_price) * trade.position_size_contracts
            pnl_pct = ((trade.entry_price - exit_price) / trade.entry_price) * 100

        trade.exit_time = datetime.now()
        trade.exit_price = exit_price
        trade.exit_reason = exit_reason
        trade.pnl = pnl
        trade.pnl_pct = pnl_pct
        trade.status = TradeStatus.CLOSED

        logger.info(
            f"Trade closed: {trade_id} @ {exit_price} "
            f"P&L: ${pnl:.2f} ({pnl_pct:+.2f}%) [{exit_reason.value}]"
        )

        return trade

    def get_open_trades(self) -> List[TradeLog]:
        """Return all open trades."""
        return list(self.open_trades.values())

    def has_open_position(self, pair: str) -> bool:
        """Check if there's an open position on pair."""
        for trade in self.open_trades.values():
            if trade.pair == pair and trade.status == TradeStatus.OPEN:
                return True
        return False
