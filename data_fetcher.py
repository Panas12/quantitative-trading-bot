"""
Data Fetcher Module for Quantitative Trading Bot
Based on Ernest Chan's "Quantitative Trading" methodology

Downloads and manages historical price data for trading pairs.
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class DataFetcher:
    """
    Fetches and manages historical price data for pairs trading.
    
    From Chan's book: Quality data is essential for backtesting.
    Always use adjusted close prices to account for splits and dividends.
    """
    
    def __init__(self, symbol1: str, symbol2: str):
        """
        Initialize DataFetcher.
        
        Args:
            symbol1: First symbol (e.g., 'GLD')
            symbol2: Second symbol (e.g., 'GDX')
        """
        self.symbol1 = symbol1
        self.symbol2 = symbol2
        self.data1 = None
        self.data2 = None
        
    def fetch_data(self, start_date: str, end_date: Optional[str] = None,
                   min_history_days: int = 500) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Fetch historical data for both symbols from Yahoo Finance.
        
        Args:
            start_date: Start date in 'YYYY-MM-DD' format
            end_date: End date in 'YYYY-MM-DD' format (None for current date)
            min_history_days: Minimum number of trading days required
        
        Returns:
            Tuple of (data1, data2) as DataFrames with adjusted close prices
        """
        logger.info(f"Fetching data for {self.symbol1} and {self.symbol2}")
        logger.info(f"Date range: {start_date} to {end_date or 'present'}")
        
        try:
            # Download data
            data1 = yf.download(self.symbol1, start=start_date, end=end_date, 
                               progress=False)
            data2 = yf.download(self.symbol2, start=start_date, end=end_date, 
                               progress=False)
            
            # Extract adjusted close prices
            if 'Adj Close' in data1.columns:
                prices1 = pd.DataFrame(data1['Adj Close'])
                prices1.columns = ['close']
            else:
                prices1 = pd.DataFrame(data1['Close'])
                prices1.columns = ['close']
                
            if 'Adj Close' in data2.columns:
                prices2 = pd.DataFrame(data2['Adj Close'])
                prices2.columns = ['close']
            else:
                prices2 = pd.DataFrame(data2['Close'])
                prices2.columns = ['close']
            
            # Align the data (get common trading days)
            common_dates = prices1.index.intersection(prices2.index)
            common_dates = common_dates.sort_values()
            
            prices1 = prices1.loc[common_dates]
            prices2 = prices2.loc[common_dates]
            
            # Check if we have enough data
            if len(prices1) < min_history_days:
                logger.warning(f"Only {len(prices1)} days of data available. "
                             f"Minimum recommended: {min_history_days}")
            
            # Remove any NaN values
            prices1 = prices1.dropna()
            prices2 = prices2.dropna()
            
            # Final alignment
            common_dates = prices1.index.intersection(prices2.index)
            prices1 = prices1.loc[common_dates]
            prices2 = prices2.loc[common_dates]
            
            logger.info(f"Successfully fetched {len(prices1)} days of aligned data")
            logger.info(f"Date range: {prices1.index[0]} to {prices1.index[-1]}")
            
            self.data1 = prices1
            self.data2 = prices2
            
            return prices1, prices2
            
        except Exception as e:
            logger.error(f"Error fetching data: {str(e)}")
            raise
    
    def split_train_test(self, train_pct: float = 0.67, 
                        train_days: Optional[int] = None) -> Tuple[Tuple[pd.DataFrame, pd.DataFrame],
                                                                    Tuple[pd.DataFrame, pd.DataFrame]]:
        """
        Split data into training and testing sets.
        
        From Chan's Example 3.6: Use first 252 days (1 year) for training,
        rest for testing. This prevents overfitting.
        
        Args:
            train_pct: Percentage of data for training (if train_days is None)
            train_days: Specific number of days for training (overrides train_pct)
        
        Returns:
            Tuple of ((train_data1, train_data2), (test_data1, test_data2))
        """
        if self.data1 is None or self.data2 is None:
            raise ValueError("No data available. Call fetch_data() first.")
        
        total_days = len(self.data1)
        
        if train_days is not None:
            split_idx = min(train_days, total_days)
        else:
            split_idx = int(total_days * train_pct)
        
        # Split both datasets at the same point
        train_data1 = self.data1.iloc[:split_idx]
        test_data1 = self.data1.iloc[split_idx:]
        
        train_data2 = self.data2.iloc[:split_idx]
        test_data2 = self.data2.iloc[split_idx:]
        
        logger.info(f"Data split - Training: {len(train_data1)} days, "
                   f"Testing: {len(test_data1)} days")
        logger.info(f"Training period: {train_data1.index[0]} to {train_data1.index[-1]}")
        logger.info(f"Testing period: {test_data1.index[0]} to {test_data1.index[-1]}")
        
        return (train_data1, train_data2), (test_data1, test_data2)
    
    def get_latest_prices(self) -> Tuple[float, float]:
        """
        Get the most recent prices for both symbols.
        
        Returns:
            Tuple of (price1, price2)
        """
        if self.data1 is None or self.data2 is None:
            raise ValueError("No data available. Call fetch_data() first.")
        
        price1 = self.data1['close'].iloc[-1]
        price2 = self.data2['close'].iloc[-1]
        
        return price1, price2
    
    def add_technical_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Add common technical indicators to the data.
        
        Args:
            data: DataFrame with 'close' column
        
        Returns:
            DataFrame with additional indicator columns
        """
        df = data.copy()
        
        # Simple moving averages
        df['sma_20'] = df['close'].rolling(window=20).mean()
        df['sma_50'] = df['close'].rolling(window=50).mean()
        
        # Volatility (20-day rolling standard deviation)
        df['volatility'] = df['close'].pct_change().rolling(window=20).std()
        
        return df


if __name__ == "__main__":
    # Test the data fetcher
    logging.basicConfig(level=logging.INFO)
    
    print("Testing Data Fetcher...")
    print("="*60)
    
    # Fetch GLD-GDX data
    fetcher = DataFetcher('GLD', 'GDX')
    data1, data2 = fetcher.fetch_data(start_date='2018-01-01')
    
    print(f"\n{fetcher.symbol1} data shape: {data1.shape}")
    print(data1.head())
    
    print(f"\n{fetcher.symbol2} data shape: {data2.shape}")
    print(data2.head())
    
    # Split into train/test
    (train1, train2), (test1, test2) = fetcher.split_train_test(train_days=252)
    
    print(f"\nTraining set: {len(train1)} days")
    print(f"Test set: {len(test1)} days")
