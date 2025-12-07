"""
Dynamic Thresholds Module

Adapts entry/exit z-score thresholds based on current market volatility.

Logic:
- Low volatility: Tighter thresholds (2.0) - Less extreme moves needed
- High volatility: Wider thresholds (3.0) - Wait for more extreme deviations
- Normal volatility: Standard thresholds (2.4)

This prevents false signals during choppy markets and catches real opportunities.
"""

import numpy as np
import pandas as pd
from typing import Tuple
import logging

logger = logging.getLogger(__name__)


class DynamicThresholds:
    """
    Calculate adaptive entry/exit thresholds based on market conditions.
    """
    
    def __init__(self, 
                 base_entry: float = 2.0,
                 base_exit: float = 1.0,
                 lookback_vol: int = 20,
                 lookback_reversion: int = 30):
        """
        Initialize dynamic threshold calculator.
        
        Args:
            base_entry: Base entry threshold (z-score)
            base_exit: Base exit threshold (z-score)
            lookback_vol: Window for volatility calculation
            lookback_reversion: Window for reversion speed calculation
        """
        self.base_entry = base_entry
        self.base_exit = base_exit
        self.lookback_vol = lookback_vol
        self.lookback_reversion = lookback_reversion
        
    def calculate_realized_volatility(self, spread: pd.Series, window: int = None) -> float:
        """
        Calculate realized volatility of spread.
        
        Args:
            spread: Spread series
            window: Lookback window (default: use self.lookback_vol)
            
        Returns:
            Realized volatility (annualized std of returns)
        """
        if window is None:
            window = self.lookback_vol
        
        returns = spread.pct_change().dropna()
        
        if len(returns) < window:
            logger.warning(f"Not enough data for volatility calc: {len(returns)} < {window}")
            return returns.std() if len(returns) > 0 else 0.01
        
        # Rolling realized volatility
        realized_vol = returns.tail(window).std()
        
        # Annualize (assuming daily data, 252 trading days)
        annualized_vol = realized_vol * np.sqrt(252)
        
        return annualized_vol
    
    def calculate_reversion_speed(self, spread: pd.Series, zscore: pd.Series, 
                                  window: int = None) -> float:
        """
        Calculate mean reversion speed.
        
        Measures how quickly spread returns to mean after extremes.
        
        Args:
            spread: Spread series
            zscore: Z-score series
            window: Lookback window
            
        Returns:
            Reversion speed metric (0-1, higher = faster reversion)
        """
        if window is None:
            window = self.lookback_reversion
        
        # Look at recent data
        recent_zscore = zscore.tail(window)
        
        if len(recent_zscore) < 10:
            return 0.5  # Default moderate speed
        
        # Calculate how often z-score crosses zero
        zero_crossings = ((recent_zscore[:-1] * recent_zscore[1:]) < 0).sum()
        
        # Normalize by window size
        reversion_rate = zero_crossings / len(recent_zscore)
        
        # Also check autocorrelation (negative = mean-reverting)
        autocorr = recent_zscore.autocorr(lag=1)
        
        # Combine metrics
        # High crossing rate + negative autocorr = fast reversion
        if autocorr < 0:
            speed_score = min(1.0, reversion_rate * 2 + abs(autocorr))
        else:
            speed_score = reversion_rate
        
        return speed_score
    
    def calculate_thresholds(self, spread: pd.Series, zscore: pd.Series) -> Tuple[float, float]:
        """
        Calculate adaptive entry and exit thresholds.
        
        Args:
            spread: Spread series
            zscore: Z-score series
            
        Returns:
            Tuple of (entry_threshold, exit_threshold)
        """
        # Calculate current volatility
        current_vol = self.calculate_realized_volatility(spread)
        
        # Calculate historical volatility for comparison
        if len(spread) > 100:
            historical_vol = self.calculate_realized_volatility(
                spread, 
                window=min(252, len(spread))  # Up to 1 year
            )
        else:
            historical_vol = current_vol
        
        # Volatility ratio
        if historical_vol > 0:
            vol_ratio = current_vol / historical_vol
        else:
            vol_ratio = 1.0
        
        logger.debug(f"Vol ratio: {vol_ratio:.2f} (current: {current_vol:.1%}, hist: {historical_vol:.1%})")
        
        # Adjust entry threshold based on volatility
        if vol_ratio < 0.7:
            # Low volatility - use tighter threshold
            entry_multiplier = 1.0
            logger.debug("Low volatility environment - tighter thresholds")
        elif vol_ratio > 1.3:
            # High volatility - use wider threshold
            entry_multiplier = 1.5
            logger.debug("High volatility environment - wider thresholds")
        else:
            # Normal volatility
            entry_multiplier = 1.2
            logger.debug("Normal volatility environment")
        
        entry_threshold = self.base_entry * entry_multiplier
        
        # Calculate reversion speed
        reversion_speed = self.calculate_reversion_speed(spread, zscore)
        
        logger.debug(f"Reversion speed: {reversion_speed:.2f}")
        
        # Adjust exit threshold based on reversion speed
        if reversion_speed > 0.5:
            # Fast reversion - exit earlier to lock in profits
            exit_multiplier = 0.8
            logger.debug("Fast reversion - earlier exits")
        else:
            # Slow reversion - wait longer
            exit_multiplier = 1.2
            logger.debug("Slow reversion - patient exits")
        
        exit_threshold = self.base_exit * exit_multiplier
        
        logger.info(f"Dynamic thresholds: Entry={entry_threshold:.2f}, Exit={exit_threshold:.2f}")
        
        return entry_threshold, exit_threshold
    
    def get_threshold_history(self, spread: pd.Series, zscore: pd.Series, 
                             window: int = 60) -> pd.DataFrame:
        """
        Calculate threshold history for backtesting/visualization.
        
        Args:
            spread: Full spread series
            zscore: Full z-score series
            window: Rolling window for calculation
            
        Returns:
            DataFrame with date, entry_threshold, exit_threshold
        """
        results = []
        
        # Need at least 'window' samples to start
        for i in range(window, len(spread)):
            date = spread.index[i]
            spread_window = spread.iloc[max(0, i-window):i]
            zscore_window = zscore.iloc[max(0, i-window):i]
            
            entry_thresh, exit_thresh = self.calculate_thresholds(
                spread_window,
                zscore_window
            )
            
            results.append({
                'date': date,
                'entry_threshold': entry_thresh,
                'exit_threshold': exit_thresh
            })
        
        df = pd.DataFrame(results)
        df.set_index('date', inplace=True)
        
        return df


if __name__ == '__main__':
    # Test dynamic thresholds
    from data_fetcher import DataFetcher
    from statsmodels.regression.linear_model import OLS
    
    logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
    
    print("\n" + "="*70)
    print("TESTING DYNAMIC THRESHOLDS")
    print("="*70 + "\n")
    
    # Test on SLV-SIVR (should have low volatility)
    print("1. Testing on SLV-SIVR (Low Volatility Pair)...")
    fetcher = DataFetcher('SLV', 'SIVR')
    data1, data2 = fetcher.fetch_data(start_date='2023-01-01')
    
    # Calculate spread
    X = data2['close'].values.reshape(-1, 1)
    y = data1['close'].values
    model = OLS(y, X).fit()
    hedge_ratio = model.params[0]
    
    spread = data1['close'] - hedge_ratio * data2['close']
    spread_mean = spread.mean()
    spread_std = spread.std()
    zscore = (spread - spread_mean) / spread_std
    
    # Calculate dynamic thresholds
    threshold_calc = DynamicThresholds(base_entry=2.0, base_exit=1.0)
    entry_thresh, exit_thresh = threshold_calc.calculate_thresholds(spread, zscore)
    
    print(f"\nSLV-SIVR Results:")
    print(f"  Entry Threshold: {entry_thresh:.2f}")
    print(f"  Exit Threshold: {exit_thresh:.2f}")
    
    # Test on USO-XLE (should have higher volatility)
    print("\n2. Testing on USO-XLE (Higher Volatility Pair)...")
    fetcher2 = DataFetcher('USO', 'XLE')
    data1, data2 = fetcher2.fetch_data(start_date='2023-01-01')
    
    X = data2['close'].values.reshape(-1, 1)
    y = data1['close'].values
    model = OLS(y, X).fit()
    hedge_ratio = model.params[0]
    
    spread2 = data1['close'] - hedge_ratio * data2['close']
    spread_mean2 = spread2.mean()
    spread_std2 = spread2.std()
    zscore2 = (spread2 - spread_mean2) / spread_std2
    
    entry_thresh2, exit_thresh2 = threshold_calc.calculate_thresholds(spread2, zscore2)
    
    print(f"\nUSO-XLE Results:")
    print(f"  Entry Threshold: {entry_thresh2:.2f}")
    print(f"  Exit Threshold: {exit_thresh2:.2f}")
    
    # Compare
    print("\n3. Comparison:")
    print(f"  SLV-SIVR entry: {entry_thresh:.2f} (stable pair)")
    print(f"  USO-XLE entry:  {entry_thresh2:.2f} (volatile pair)")
    print(f"\n  Difference: {abs(entry_thresh2 - entry_thresh):.2f} z-score units")
    
    if entry_thresh2 > entry_thresh:
        print("  ✓ System correctly widens thresholds for volatile pair")
    
    print("\n" + "="*70)
    print("✓ Test complete!")
    print("="*70)
