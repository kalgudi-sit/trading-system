"""
Service 5: Dynamic Parameters Engine

Purpose: Calculate take profit levels based on breakout strength.
Responsibility: Assign R:R ratios dynamically.

R:R Ratio Mapping:
WEAK: 1.0
MODERATE: 1.5
STRONG: 2.0
EXCEPTIONAL: 2.5-3.0

Optional: Multi-level take profit for STRONG/EXCEPTIONAL.
"""

from dataclasses import dataclass
from typing import List
from trading_system.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ParametersEngineResult:
    """Output from parameters engine."""
    entry_price: float
    stop_loss_price: float
    take_profit_primary: float
    take_profit_scaled: List[float]  # Multi-level TP prices
    rr_ratio: float
    stop_distance: float


class ParametersEngine:
    """Calculates dynamic TP/SL based on breakout strength."""

    RR_RATIOS = {
        "WEAK": 1.0,
        "MODERATE": 1.5,
        "STRONG": 2.0,
        "EXCEPTIONAL": 2.5,  # Can go up to 3.0
    }

    def calculate_parameters(
        self,
        entry_price: float,
        stop_loss_price: float,
        breakout_grade: str,
        direction: str,  # LONG or SHORT
    ) -> ParametersEngineResult:
        """
        Calculate take profit based on breakout grade.
        
        Args:
            entry_price: Entry price
            stop_loss_price: Stop loss price
            breakout_grade: WEAK/MODERATE/STRONG/EXCEPTIONAL
            direction: LONG or SHORT
        
        Returns:
            ParametersEngineResult with TP and SL
        """
        # Calculate risk
        stop_distance = abs(entry_price - stop_loss_price)

        # Get R:R ratio for grade
        rr_ratio = self.RR_RATIOS.get(breakout_grade, 1.0)

        # Calculate primary take profit
        if direction == "LONG":
            take_profit_primary = entry_price + (stop_distance * rr_ratio)
        else:  # SHORT
            take_profit_primary = entry_price - (stop_distance * rr_ratio)

        # Calculate multi-level TP for STRONG/EXCEPTIONAL
        take_profit_scaled = self._calculate_scaled_tp(
            entry_price, stop_distance, breakout_grade, direction
        )

        logger.debug(
            f"Parameters: Entry={entry_price}, SL={stop_loss_price}, "
            f"TP={take_profit_primary} (RR={rr_ratio}), "
            f"Scaled TP={take_profit_scaled}"
        )

        return ParametersEngineResult(
            entry_price=entry_price,
            stop_loss_price=stop_loss_price,
            take_profit_primary=take_profit_primary,
            take_profit_scaled=take_profit_scaled,
            rr_ratio=rr_ratio,
            stop_distance=stop_distance,
        )

    def _calculate_scaled_tp(
        self, entry: float, risk: float, grade: str, direction: str
    ) -> List[float]:
        """Calculate multi-level TP for STRONG/EXCEPTIONAL."""
        if grade not in ["STRONG", "EXCEPTIONAL"]:
            return []

        scaled = []
        if direction == "LONG":
            scaled.append(entry + (risk * 0.5))  # Level 1: 0.5R
            scaled.append(entry + (risk * 2.0))  # Level 2: 2.0R
        else:  # SHORT
            scaled.append(entry - (risk * 0.5))  # Level 1: 0.5R
            scaled.append(entry - (risk * 2.0))  # Level 2: 2.0R

        return scaled
