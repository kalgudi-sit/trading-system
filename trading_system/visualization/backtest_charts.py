"""
Backtest Results Visualization using Plotly.

Generates interactive HTML charts showing:
- Price chart with buy/sell signals
- Equity curve (growing/shrinking account)
- Drawdown visualization
- Trade-by-trade P&L breakdown
"""

from typing import List
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from trading_system.models import TradeLog, CandleData
from trading_system.utils.logger import get_logger

logger = get_logger(__name__)


class BacktestCharts:
    """Generate interactive backtest visualizations."""

    @staticmethod
    def create_comprehensive_report(
        candles: List[CandleData],
        trades: List[TradeLog],
        account_equity_over_time: List[float],
        output_path: str,
    ) -> None:
        """
        Create comprehensive backtest report with multiple subplots.
        
        Args:
            candles: All processed candles
            trades: All closed trades
            account_equity_over_time: Account balance at each candle
            output_path: Where to save HTML file
        """
        logger.info(f"Generating backtest report to {output_path}...")

        # Create subplots
        fig = make_subplots(
            rows=3,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.08,
            row_heights=[0.5, 0.25, 0.25],
            subplot_titles=(
                "Price & Trades",
                "Account Equity",
                "Drawdown",
            ),
        )

        # TODO: Implement chart generation
        # 1. Price chart with buy/sell marks
        # 2. Equity curve
        # 3. Drawdown chart

        fig.write_html(output_path)
        logger.info(f"Report saved to {output_path}")

    @staticmethod
    def create_trades_summary(
        trades: List[TradeLog],
        output_path: str,
    ) -> None:
        """
        Create summary table of all trades.
        """
        # TODO: Implement
        pass
