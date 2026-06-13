"""
Service 2: Signal Validator

Purpose: Filter out false breakouts using volume conviction.
Responsibility: Reject signals that lack market participation.
Output: SignalValidationResult (VALID or REJECTED).

4 Mandatory Checks:
1. Volume Expansion (>1.5x)
2. Structure Confirmation
3. Consecutive Candle Strength (>=2 in direction)
4. Volatility Coherence (ATR >1.2x)

All must PASS for signal to be validated.
"""

from typing import List, Tuple
from trading_system.models import Signal, SignalValidationResult, CandleData
from trading_system.utils.logger import get_logger

logger = get_logger(__name__)


class SignalValidator:
    """Validates signals using volume and structure checks."""

    VOLUME_MULTIPLIER_MIN = 1.5  # Volume must be >=1.5x average
    ATR_MULTIPLIER_MIN = 1.2  # ATR must be >=1.2x average
    CONSECUTIVE_CANDLES_MIN = 2  # Need >=2 candles in direction

    def validate(
        self,
        signal: Signal,
        current_candle: CandleData,
        previous_candles: List[CandleData],
    ) -> SignalValidationResult:
        """
        Validate a signal against 4 mandatory checks.
        ALL must pass for signal to be valid.
        
        Args:
            signal: Signal to validate (from Service 1)
            current_candle: Latest CandleData
            previous_candles: Last 20+ candles
        
        Returns:
            SignalValidationResult with pass/fail for each check
        """
        # Check 1: Volume Expansion
        vol_pass, vol_ratio = self._check_volume_expansion(current_candle, previous_candles)

        # Check 2: Structure Confirmation
        struct_pass = self._check_structure_confirmation(signal, current_candle, previous_candles)

        # Check 3: Consecutive Candle Strength
        consec_pass, consec_count = self._check_consecutive_strength(
            signal, current_candle, previous_candles
        )

        # Check 4: Volatility Coherence
        (
            vol_coherence_pass,
            atr_current,
            atr_avg,
            atr_ratio,
        ) = self._check_volatility_coherence(current_candle, previous_candles)

        # All checks must pass
        all_pass = vol_pass and struct_pass and consec_pass and vol_coherence_pass

        validation_confidence = self._calculate_confidence(
            vol_pass, struct_pass, consec_pass, vol_coherence_pass
        )

        result = SignalValidationResult(
            signal_id=signal.signal_id,
            validation_result="VALID" if all_pass else "REJECTED",
            validation_confidence=validation_confidence,
            volume_expansion_pass=vol_pass,
            volume_expansion_ratio=vol_ratio,
            structure_confirmation_pass=struct_pass,
            consecutive_strength_pass=consec_pass,
            consecutive_bullish_candles=consec_count,
            volatility_coherence_pass=vol_coherence_pass,
            atr_current=atr_current,
            atr_avg_20=atr_avg,
            atr_ratio=atr_ratio,
            rejection_reason=self._get_rejection_reason(
                vol_pass, struct_pass, consec_pass, vol_coherence_pass
            ),
        )

        logger.debug(
            f"Signal {signal.signal_id}: "
            f"vol={vol_pass}, struct={struct_pass}, consec={consec_pass}, "
            f"vol_coh={vol_coherence_pass} -> {result.validation_result}"
        )
        return result

    def _check_volume_expansion(
        self, current_candle: CandleData, previous_candles: List[CandleData]
    ) -> Tuple[bool, float]:
        """Check: Volume >= 1.5x average."""
        # TODO: Implement
        pass_check = True
        ratio = 1.5
        return pass_check, ratio

    def _check_structure_confirmation(
        self, signal: Signal, current_candle: CandleData, previous_candles: List[CandleData]
    ) -> bool:
        """Check: Price closed above swing high (LONG) or below swing low (SHORT)."""
        # TODO: Implement
        return True

    def _check_consecutive_strength(
        self, signal: Signal, current_candle: CandleData, previous_candles: List[CandleData]
    ) -> Tuple[bool, int]:
        """Check: >=2 candles in breakout direction in last 3 candles."""
        # TODO: Implement
        return True, 2

    def _check_volatility_coherence(
        self, current_candle: CandleData, previous_candles: List[CandleData]
    ) -> Tuple[bool, float, float, float]:
        """Check: ATR >= 1.2x average."""
        # TODO: Implement
        return True, 100, 80, 1.2

    def _calculate_confidence(self, vol, struct, consec, vol_coh) -> float:
        """Calculate validation confidence (0-1)."""
        checks = [vol, struct, consec, vol_coh]
        return sum(checks) / len(checks)

    def _get_rejection_reason(self, vol, struct, consec, vol_coh) -> str:
        """Get human-readable rejection reason."""
        reasons = []
        if not vol:
            reasons.append("Insufficient volume")
        if not struct:
            reasons.append("Structure not confirmed")
        if not consec:
            reasons.append("Weak consecutive candle strength")
        if not vol_coh:
            reasons.append("Low volatility coherence")
        return "; ".join(reasons) if reasons else None
