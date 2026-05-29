"""
Pairs Trading Strategy Module
Based on Ernest Chan's "Quantitative Trading" Example 3.6

Implements a mean-reversion pairs trading strategy using z-score thresholds.
"""

import numpy as np
import pandas as pd
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class PairsTradingStrategy:
    """
    Implements pairs trading strategy based on mean-reverting spreads.
    
    From Chan's Example 3.6:
    - Enter when z-score > 2 or < -2
    - Exit when z-score returns to within ±1
    - Include transaction costs in performance evaluation
    """
    
    def __init__(self, entry_threshold: float = 2.0, 
                 exit_threshold: float = 1.0,
                 hedge_ratio: Optional[float] = None):
        """
        Initialize Pairs Trading Strategy.
        
        Args:
            entry_threshold: Z-score threshold for entering trades (default: 2.0)
            exit_threshold: Z-score threshold for exiting trades (default: 1.0)
            hedge_ratio: Hedge ratio between the two symbols (computed if None)
        """
        self.entry_threshold = entry_threshold
        self.exit_threshold = exit_threshold
        self.hedge_ratio = hedge_ratio
        self.spread = None
        self.spread_mean = None
        self.spread_std = None
        self.zscore = None
        
    def calculate_spread(self, prices1: pd.Series, prices2: pd.Series,
                        hedge_ratio: Optional[float] = None) -> pd.Series:
        """
        Calculate the spread between two price series.
        
        Spread = prices1 - hedge_ratio * prices2
        
        Args:
            prices1: Price series for symbol 1
            prices2: Price series for symbol 2
            hedge_ratio: Hedge ratio (if None, use regression)
        
        Returns:
            Spread series
        """
        prices1 = prices1.squeeze() if isinstance(prices1, pd.DataFrame) else prices1
        prices2 = prices2.squeeze() if isinstance(prices2, pd.DataFrame) else prices2
        
        if hedge_ratio is None:
            # Calculate hedge ratio using linear regression
            if self.hedge_ratio is None:
                from statsmodels.regression.linear_model import OLS
                X = prices2.values.reshape(-1, 1)
                y = prices1.values
                model = OLS(y, X).fit()
                self.hedge_ratio = model.params[0]
                logger.info(f"Calculated hedge ratio: {self.hedge_ratio:.4f}")
            hedge_ratio = self.hedge_ratio
        else:
            self.hedge_ratio = hedge_ratio
        
        self.spread = prices1 - hedge_ratio * prices2
        return self.spread
    
    def calculate_zscore(self, spread: pd.Series, 
                        training_mean: Optional[float] = None,
                        training_std: Optional[float] = None) -> pd.Series:
        """
        Calculate z-score of the spread.
        
        Z-score = (spread - mean) / std
        
        From Chan: Use training set statistics to avoid look-ahead bias.
        
        Args:
            spread: Spread series
            training_mean: Mean from training period (if None, use spread mean)
            training_std: Std from training period (if None, use spread std)
        
        Returns:
            Z-score series
        """
        if training_mean is None:
            self.spread_mean = spread.mean()
        else:
            self.spread_mean = training_mean
            
        if training_std is None:
            self.spread_std = spread.std()
        else:
            self.spread_std = training_std
        
        self.zscore = (spread - self.spread_mean) / self.spread_std
        
        return self.zscore
    
    def generate_signals(self, zscore: pd.Series) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Generate trading signals based on z-score.
        
        From Chan's Example 3.6:
        - Long signal: z-score < -entry_threshold (spread too low, expect mean reversion)
        - Short signal: z-score > entry_threshold (spread too high, expect mean reversion)
        - Exit signal: |z-score| < exit_threshold (spread returned to normal)
        
        Args:
            zscore: Z-score series
        
        Returns:
            Tuple of (long_entry, short_entry, exit_signal) boolean series
        """
        # Entry signals
        long_entry = zscore <= -self.entry_threshold
        short_entry = zscore >= self.entry_threshold
        
        # Exit signal - within exit threshold
        exit_signal = np.abs(zscore) <= self.exit_threshold
        
        return long_entry, short_entry, exit_signal
    
    def calculate_positions(self, long_entry: pd.Series, short_entry: pd.Series,
                           exit_signal: pd.Series) -> pd.Series:
        """
        Calculate position sizes over time.
        
        Position encoding:
        - +1: Long spread (long symbol1, short symbol2)
        - -1: Short spread (short symbol1, long symbol2)
        -  0: No position
        
        Args:
            long_entry: Boolean series for long entry signals
            short_entry: Boolean series for short entry signals
            exit_signal: Boolean series for exit signals
        
        Returns:
            Position series
        """
        positions = pd.Series(0, index=long_entry.index, dtype=float)
        current_position = 0
        
        for i in range(len(positions)):
            # Check for exit first
            if exit_signal.iloc[i] and current_position != 0:
                current_position = 0
            
            # Check for entry signals
            elif long_entry.iloc[i]:
                current_position = 1  # Long the spread
            elif short_entry.iloc[i]:
                current_position = -1  # Short the spread
            
            positions.iloc[i] = current_position
        
        return positions
    
    def run_strategy(self, prices1: pd.Series, prices2: pd.Series,
                    train_prices1: Optional[pd.Series] = None,
                    train_prices2: Optional[pd.Series] = None) -> dict:
        """
        Run the complete pairs trading strategy.
        
        From Chan: Always calibrate on training data, test on separate data.
        
        Args:
            prices1: Price series for symbol 1 (test period)
            prices2: Price series for symbol 2 (test period)
            train_prices1: Training prices for symbol 1 (for calibration)
            train_prices2: Training prices for symbol 2 (for calibration)
        
        Returns:
            Dictionary containing spread, zscore, signals, and positions
        """
        # If training data provided, use it to calculate hedge ratio and statistics
        if train_prices1 is not None and train_prices2 is not None:
            logger.info("Calibrating strategy on training data...")
            train_spread = self.calculate_spread(train_prices1, train_prices2)
            train_mean = train_spread.mean()
            train_std = train_spread.std()
            logger.info(f"Training spread - Mean: {train_mean:.4f}, Std: {train_std:.4f}")
        else:
            train_mean = None
            train_std = None
        
        # Calculate spread on test/live data using training hedge ratio
        logger.info("Generating signals on test data...")
        spread = self.calculate_spread(prices1, prices2)
        
        # Calculate z-score using training statistics
        zscore = self.calculate_zscore(spread, train_mean, train_std)
        
        # Generate signals
        long_entry, short_entry, exit_signal = self.generate_signals(zscore)
        
        # Calculate positions
        positions = self.calculate_positions(long_entry, short_entry, exit_signal)
        
        # Count trades
        position_changes = positions.diff().fillna(0)
        num_entries = (position_changes != 0).sum()
        
        logger.info(f"Generated {num_entries} position changes")
        logger.info(f"Long entries: {long_entry.sum()}")
        logger.info(f"Short entries: {short_entry.sum()}")
        
        return {
            'spread': spread,
            'zscore': zscore,
            'long_entry': long_entry,
            'short_entry': short_entry,
            'exit_signal': exit_signal,
            'positions': positions,
            'hedge_ratio': self.hedge_ratio
        }


if __name__ == "__main__":
    # Test the strategy
    from data_fetcher import DataFetcher
    
    logging.basicConfig(level=logging.INFO, 
                       format='%(levelname)s - %(message)s')
    
    print("\n" + "="*60)
    print("TESTING PAIRS TRADING STRATEGY")
    print("="*60 + "\n")
    
    # Fetch data
    fetcher = DataFetcher('GLD', 'GDX')
    data1, data2 = fetcher.fetch_data(start_date='2018-01-01')
    
    # Split into train/test (252 days training as per Chan's example)
    (train1, train2), (test1, test2) = fetcher.split_train_test(train_days=252)
    
    # Initialize strategy
    strategy = PairsTradingStrategy(entry_threshold=2.0, exit_threshold=1.0)
    
    # Run strategy
    results = strategy.run_strategy(
        prices1=test1['close'],
        prices2=test2['close'],
        train_prices1=train1['close'],
        train_prices2=train2['close']
    )
    
    print("\n" + "="*60)
    print("STRATEGY RESULTS SUMMARY")
    print("="*60)
    print(f"Hedge Ratio: {results['hedge_ratio']:.4f}")
    print(f"Number of Position Changes: {(results['positions'].diff() != 0).sum()}")
    print(f"Final Position: {results['positions'].iloc[-1]}")
    print("="*60)
