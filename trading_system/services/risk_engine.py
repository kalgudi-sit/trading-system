"""
Service 4: Risk Engine

Purpose: Calculate position size, stop loss distance, capital allocation.
Responsibility: Enforce hard capital constraints (0.7% max loss).

Logic:
1. Calculate stop distance (entry - stop loss)
2. Calculate position size = Risk / StopDistance
3. Apply grade modifier (WEAK=0.6x, MODERATE=0.8x, STRONG=1.0x, EXCEPTIONAL=1.0x)
4. Enforce leverage limit (5x max)
5. Verify 0.7% hard cap
"""

from dataclasses import dataclass
from typing import Optional
from trading_system.models import Signal, CandleData
from trading_system.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class RiskEngineResult:
    """Output from risk engine."""
    position_size_usdt: float
    position_size_contracts: float
    notional_risk: float  # $ amount at risk
    notional_risk_pct: float  # Percentage of account
    effective_leverage: float
    approved: bool
    rejection_reason: Optional[str] = None


class RiskEngine:
    """Calculates position size and enforces risk limits."""

    HARD_RISK_CAP = 0.007  # 0.7% of account
    MAX_LEVERAGE = 5.0
    STOP_DISTANCE_MAX_PCT = 0.03  # Reject if stop > 3% away

    GRADE_MODIFIERS = {
        "WEAK": 0.6,
        "MODERATE": 0.8,
        "STRONG": 1.0,
        "EXCEPTIONAL": 1.0,
    }

    def __init__(self, account_equity: float):
        """
        Args:
            account_equity: Account balance in USDT
        """
        self.account_equity = account_equity

    def calculate_position_size(
        self,
        entry_price: float,
        stop_loss_price: float,
        breakout_grade: str,
    ) -> RiskEngineResult:
        """
        Calculate safe position size.
        
        Args:
            entry_price: Entry price for trade
            stop_loss_price: Stop loss price
            breakout_grade: WEAK/MODERATE/STRONG/EXCEPTIONAL
        
        Returns:
            RiskEngineResult with position size and approval
        """
        # Step 1: Calculate stop distance
        stop_distance = abs(entry_price - stop_loss_price)
        stop_distance_pct = (stop_distance / entry_price) * 100

        # Reject if stop too far
        if stop_distance_pct > self.STOP_DISTANCE_MAX_PCT:
            return RiskEngineResult(
                position_size_usdt=0,
                position_size_contracts=0,
                notional_risk=0,
                notional_risk_pct=0,
                effective_leverage=0,
                approved=False,
                rejection_reason=f"Stop loss too far: {stop_distance_pct:.2f}% > {self.STOP_DISTANCE_MAX_PCT*100:.1f}%",
            )

        # Step 2: Calculate max position size
        max_notional_risk = self.account_equity * self.HARD_RISK_CAP
        stop_distance_pct_decimal = stop_distance_pct / 100
        position_size_usdt = max_notional_risk / stop_distance_pct_decimal

        # Step 3: Apply grade modifier
        modifier = self.GRADE_MODIFIERS.get(breakout_grade, 1.0)
        position_size_usdt *= modifier

        # Step 4: Enforce leverage limit
        effective_leverage = position_size_usdt / self.account_equity
        if effective_leverage > self.MAX_LEVERAGE:
            position_size_usdt = self.account_equity * self.MAX_LEVERAGE
            effective_leverage = self.MAX_LEVERAGE

        # Calculate actual notional risk (may be < 0.7% if leverage limited)
        notional_risk = position_size_usdt * stop_distance_pct_decimal
        notional_risk_pct = notional_risk / self.account_equity

        # Position size in contracts (at entry price)
        position_size_contracts = position_size_usdt / entry_price

        # Verify hard cap still holds
        if notional_risk_pct > self.HARD_RISK_CAP:
            return RiskEngineResult(
                position_size_usdt=0,
                position_size_contracts=0,
                notional_risk=0,
                notional_risk_pct=0,
                effective_leverage=0,
                approved=False,
                rejection_reason="Risk exceeds hard cap (0.7%)",
            )

        logger.debug(
            f"Position size: {position_size_usdt:.2f} USDT "
            f"({position_size_contracts:.4f} contracts), "
            f"Risk: {notional_risk_pct*100:.2f}%, Leverage: {effective_leverage:.2f}x"
        )

        return RiskEngineResult(
            position_size_usdt=position_size_usdt,
            position_size_contracts=position_size_contracts,
            notional_risk=notional_risk,
            notional_risk_pct=notional_risk_pct,
            effective_leverage=effective_leverage,
            approved=True,
            rejection_reason=None,
        )
