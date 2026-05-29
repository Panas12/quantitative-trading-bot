"""
Risk Management Module
Based on Ernest Chan's "Quantitative Trading" Chapter 6

Implements position sizing using Kelly Criterion and risk controls.
"""

import numpy as np
import pandas as pd
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class RiskManager:
    """
    Manages position sizing and risk controls.
    
    From Chan's Chapter 6:
    - Use Kelly Criterion for optimal position sizing
    - Half-Kelly is more conservative and recommended
    - Monitor drawdowns and implement stop-losses
    """
    
    def __init__(self, initial_capital: float = 100000,
                 kelly_fraction: float = 0.5,
                 max_leverage: float = 2.0,
                 max_drawdown_pct: float = 0.25,
                 max_position_size: float = 0.95):
        """
        Initialize Risk Manager.
        
        Args:
            initial_capital: Starting capital
            kelly_fraction: Fraction of Kelly to use (0.5 = half-Kelly, recommended)
            max_leverage: Maximum allowed leverage
            max_drawdown_pct: Maximum drawdown before emergency stop (0.25 = 25%)
            max_position_size: Maximum position as fraction of capital
        """
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.kelly_fraction = kelly_fraction
        self.max_leverage = max_leverage
        self.max_drawdown_pct = max_drawdown_pct
        self.max_position_size = max_position_size
        self.high_watermark = initial_capital
        
    def calculate_kelly_fraction(self, win_rate: float, 
                                 avg_win: float, avg_loss: float) -> float:
        """
        Calculate Kelly Criterion for position sizing.
        
        From Chan's Chapter 6 Appendix:
        Kelly formula: f = (p × b - q) / b
        where:
            f = fraction of capital to bet
            p = probability of winning
            q = probability of losing = 1 - p
            b = ratio of avg_win to avg_loss
        
        Args:
            win_rate: Probability of winning (0 to 1)
            avg_win: Average win size
            avg_loss: Average loss size (positive number)
        
        Returns:
            Kelly fraction (fraction of capital to risk)
        """
        if avg_loss == 0:
            return 0.0
        
        p = win_rate
        q = 1 - p
        b = avg_win / avg_loss
        
        # Kelly formula
        kelly_f = (p * b - q) / b
        
        # Apply fraction (e.g., half-Kelly for safety)
        adjusted_kelly = kelly_f * self.kelly_fraction
        
        # Cap at maximum position size
        final_fraction = min(adjusted_kelly, self.max_position_size)
        final_fraction = max(final_fraction, 0)  # Don't allow negative
        
        logger.info(f"Kelly Calculation:")
        logger.info(f"  Win Rate: {win_rate*100:.2f}%")
        logger.info(f"  Avg Win/Loss Ratio: {b:.2f}")
        logger.info(f"  Full Kelly: {kelly_f*100:.2f}%")
        logger.info(f"  Adjusted Kelly ({self.kelly_fraction}x): {adjusted_kelly*100:.2f}%")
        logger.info(f"  Final Position Size: {final_fraction*100:.2f}%")
        
        return final_fraction
    
    def calculate_position_size_from_returns(self, returns: pd.Series) -> float:
        """
        Calculate position size based on historical returns.
        
        Args:
            returns: Series of historical returns
        
        Returns:
            Position size as fraction of capital
        """
        if len(returns) == 0:
            return 0.0
        
        # Calculate statistics
        winning_trades = returns[returns > 0]
        losing_trades = returns[returns < 0]
        
        if len(winning_trades) == 0 or len(losing_trades) == 0:
            logger.warning("Insufficient trade history for Kelly calculation")
            return 0.1  # Conservative default
        
        win_rate = len(winning_trades) / len(returns)
        avg_win = winning_trades.mean()
        avg_loss = abs(losing_trades.mean())
        
        position_size = self.calculate_kelly_fraction(win_rate, avg_win, avg_loss)
        
        return position_size
    
    def calculate_position_value(self, signal: float, position_size_fraction: float,
                                 price1: float, price2: float, 
                                 hedge_ratio: float) -> Tuple[float, float]:
        """
        Calculate the dollar amounts to trade for each symbol.
        
        Args:
            signal: +1 for long spread, -1 for short spread, 0 for no position
            position_size_fraction: Fraction of capital to use (from Kelly)
            price1: Current price of symbol 1
            price2: Current price of symbol 2
            hedge_ratio: Hedge ratio between symbols
        
        Returns:
            Tuple of (quantity1, quantity2) - negative means short
        """
        if signal == 0:
            return 0.0, 0.0
        
        # Calculate capital to allocate
        position_capital = self.current_capital * position_size_fraction
        
        # Limit by leverage
        max_capital = self.current_capital * self.max_leverage
        position_capital = min(position_capital, max_capital)
        
        # For long spread: buy symbol1, sell symbol2
        # For short spread: sell symbol1, buy symbol2
        
        # Calculate quantities
        # Total position value = price1 * qty1 + hedge_ratio * price2 * qty2
        # We want to split position_capital between the two legs
        
        qty1 = signal * position_capital / (2 * price1)
        qty2 = -signal * hedge_ratio * position_capital / (2 * price2)
        
        logger.debug(f"Position sizing: Signal={signal}, Capital=${position_capital:.2f}")
        logger.debug(f"  Symbol1: qty={qty1:.2f} @ ${price1:.2f} = ${qty1*price1:.2f}")
        logger.debug(f"  Symbol2: qty={qty2:.2f} @ ${price2:.2f} = ${qty2*price2:.2f}")
        
        return qty1, qty2
    
    def update_capital(self, pnl: float):
        """
        Update current capital based on P&L.
        
        Args:
            pnl: Profit or loss from trades
        """
        self.current_capital += pnl
        
        # Update high watermark
        if self.current_capital > self.high_watermark:
            self.high_watermark = self.current_capital
    
    def check_drawdown(self) -> Tuple[bool, float]:
        """
        Check current drawdown level.
        
        From Chan's Chapter 6: Monitor drawdowns to prevent catastrophic losses.
        
        Returns:
            Tuple of (is_emergency_stop, current_drawdown_pct)
        """
        if self.high_watermark == 0:
            return False, 0.0
        
        drawdown = (self.current_capital - self.high_watermark) / self.high_watermark
        
        is_emergency = drawdown < -self.max_drawdown_pct
        
        if is_emergency:
            logger.error(f"EMERGENCY STOP: Drawdown {drawdown*100:.2f}% "
                        f"exceeds limit {self.max_drawdown_pct*100:.2f}%")
        elif drawdown < -self.max_drawdown_pct * 0.5:
            logger.warning(f"WARNING: Drawdown at {drawdown*100:.2f}%")
        
        return is_emergency, drawdown
    
    def get_status(self) -> dict:
        """
        Get current risk management status.
        
        Returns:
            Dictionary with current status
        """
        drawdown = (self.current_capital - self.high_watermark) / self.high_watermark
        
        return {
            'initial_capital': self.initial_capital,
            'current_capital': self.current_capital,
            'high_watermark': self.high_watermark,
            'drawdown': drawdown,
            'return': (self.current_capital - self.initial_capital) / self.initial_capital,
            'max_position_size': self.max_position_size,
            'max_leverage': self.max_leverage
        }
    
    def print_status(self):
        """Print current risk management status."""
        status = self.get_status()
        
        print("\n" + "="*60)
        print("RISK MANAGEMENT STATUS")
        print("="*60)
        print(f"Initial Capital:     ${status['initial_capital']:>12,.2f}")
        print(f"Current Capital:     ${status['current_capital']:>12,.2f}")
        print(f"High Watermark:      ${status['high_watermark']:>12,.2f}")
        print(f"Return:              {status['return']*100:>12.2f}%")
        print(f"Current Drawdown:    {status['drawdown']*100:>12.2f}%")
        print(f"Max Allowed DD:      {self.max_drawdown_pct*100:>12.2f}%")
        print("="*60 + "\n")


if __name__ == "__main__":
    # Test risk manager
    logging.basicConfig(level=logging.INFO,
                       format='%(levelname)s - %(message)s')
    
    print("\n" + "="*60)
    print("TESTING RISK MANAGER")
    print("="*60 + "\n")
    
    # Initialize
    risk_mgr = RiskManager(initial_capital=100000, kelly_fraction=0.5)
    
    # Simulate some returns
    returns = pd.Series([0.02, -0.01, 0.015, 0.025, -0.015, 0.01, -0.02, 0.03])
    
    # Calculate position size
    position_size = risk_mgr.calculate_position_size_from_returns(returns)
    
    print(f"\nRecommended position size: {position_size*100:.2f}% of capital")
    
    # Calculate positions for a trade
    qty1, qty2 = risk_mgr.calculate_position_value(
        signal=1,  # Long spread
        position_size_fraction=position_size,
        price1=180.0,  # GLD price
        price2=30.0,   # GDX price
        hedge_ratio=1.5
    )
    
    print(f"\nFor a long spread position:")
    print(f"  Buy {abs(qty1):.2f} units of Symbol1 @ $180")
    print(f"  Sell {abs(qty2):.2f} units of Symbol2 @ $30")
    
    # Check status
    risk_mgr.print_status()
