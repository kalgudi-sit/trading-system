"""
Service 3: Breakout Strength Scorer

Purpose: Quantify the conviction/power of the breakout (0-100 scale).
Responsibility: Score and assign grade (WEAK/MODERATE/STRONG/EXCEPTIONAL).

4 Weighted Factors:
1. Structure Significance (40%)
2. Volume Conviction (25%)
3. Momentum Strength (20%)
4. Candle Geometry (15%)

Grade Assignment:
0-25: WEAK
26-50: MODERATE
51-75: STRONG
76-100: EXCEPTIONAL
"""

from dataclasses import dataclass
from typing import List, Tuple
from trading_system.models import CandleData, Signal
from trading_system.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class StrengthScoreResult:
    """Result from strength scorer."""
    breakout_score: float  # 0-100
    grade: str  # WEAK, MODERATE, STRONG, EXCEPTIONAL
    structure_score: float
    volume_score: float
    momentum_score: float
    candle_geometry_score: float


class StrengthScorer:
    """Scores breakout strength 0-100."""

    def score(
        self,
        signal: Signal,
        current_candle: CandleData,
        previous_candles: List[CandleData],
    ) -> StrengthScoreResult:
        """
        Score breakout strength across 4 factors.
        
        Args:
            signal: Validated signal
            current_candle: Latest candle with indicators
            previous_candles: Historical candles for context
        
        Returns:
            StrengthScoreResult with score and grade
        """
        # Factor 1: Structure Significance (40%)
        structure_score = self._score_structure_significance(signal, previous_candles)

        # Factor 2: Volume Conviction (25%)
        volume_score = self._score_volume_conviction(current_candle, previous_candles)

        # Factor 3: Momentum Strength (20%)
        momentum_score = self._score_momentum_strength(current_candle, previous_candles)

        # Factor 4: Candle Geometry (15%)
        candle_score = self._score_candle_geometry(current_candle)

        # Weighted total
        breakout_score = (
            structure_score * 0.40
            + volume_score * 0.25
            + momentum_score * 0.20
            + candle_score * 0.15
        )

        grade = self._assign_grade(breakout_score)

        logger.debug(
            f"Breakout score: {breakout_score:.1f} ({grade}) - "
            f"struct={structure_score:.1f}, vol={volume_score:.1f}, "
            f"mom={momentum_score:.1f}, candle={candle_score:.1f}"
        )

        return StrengthScoreResult(
            breakout_score=breakout_score,
            grade=grade,
            structure_score=structure_score,
            volume_score=volume_score,
            momentum_score=momentum_score,
            candle_geometry_score=candle_score,
        )

    def _score_structure_significance(self, signal: Signal, previous_candles: List[CandleData]) -> float:
        """Score structure break level (local/weekly/monthly/support-resistance)."""
        # TODO: Implement
        return 0.0

    def _score_volume_conviction(self, current: CandleData, previous: List[CandleData]) -> float:
        """Score volume relative to average."""
        # TODO: Implement
        return 0.0

    def _score_momentum_strength(self, current: CandleData, previous: List[CandleData]) -> float:
        """Score price move distance + RSI divergence."""
        # TODO: Implement
        return 0.0

    def _score_candle_geometry(self, current: CandleData) -> float:
        """Score candle body size and wick ratio."""
        # TODO: Implement
        return 0.0

    def _assign_grade(self, score: float) -> str:
        """Assign grade based on score."""
        if score < 26:
            return "WEAK"
        elif score < 51:
            return "MODERATE"
        elif score < 76:
            return "STRONG"
        else:
            return "EXCEPTIONAL"
