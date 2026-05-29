"""
Cointegration Testing Module for Quantitative Trading Bot
Based on Ernest Chan's "Quantitative Trading" Chapter 7

Tests whether two time series are cointegrated (move together in the long term).
This is essential for pairs trading strategies.
"""

import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import adfuller, coint
from statsmodels.regression.linear_model import OLS
import matplotlib.pyplot as plt
import logging
from typing import Tuple, Optional

logger = logging.getLogger(__name__)


class CointegrationAnalyzer:
    """
    Analyzes cointegration between two price series.
    
    From Chan's Chapter 7: Cointegration is more reliable than correlation
    for pairs trading. Two series can be uncorrelated but cointegrated.
    """
    
    def __init__(self, prices1: pd.Series, prices2: pd.Series, 
                 symbol1: str = "Symbol1", symbol2: str = "Symbol2"):
        """
        Initialize CointegrationAnalyzer.
        
        Args:
            prices1: Price series for first symbol
            prices2: Price series for second symbol
            symbol1: Name of first symbol
            symbol2: Name of second symbol
        """
        self.prices1 = prices1.squeeze() if isinstance(prices1, pd.DataFrame) else prices1
        self.prices2 = prices2.squeeze() if isinstance(prices2, pd.DataFrame) else prices2
        self.symbol1 = symbol1
        self.symbol2 = symbol2
        self.hedge_ratio = None
        self.spread = None
        
    def calculate_hedge_ratio(self) -> float:
        """
        Calculate the hedge ratio using linear regression.
        
        From Chan's Example 3.6: The hedge ratio determines how many units
        of symbol2 to trade for each unit of symbol1.
        
        Returns:
            Hedge ratio (beta coefficient from regression)
        """
        # Perform regression: prices1 = alpha + beta * prices2
        # We want to find beta (hedge ratio)
        
        X = self.prices2.values.reshape(-1, 1)
        y = self.prices1.values
        
        # Use OLS regression
        model = OLS(y, X).fit()
        self.hedge_ratio = model.params[0]
        
        logger.info(f"Calculated hedge ratio: {self.hedge_ratio:.4f}")
        logger.info(f"Interpretation: 1 unit of {self.symbol1} = "
                   f"{self.hedge_ratio:.4f} units of {self.symbol2}")
        
        return self.hedge_ratio
    
    def calculate_spread(self, hedge_ratio: Optional[float] = None) -> pd.Series:
        """
        Calculate the spread between the two series.
        
        Spread = prices1 - hedge_ratio * prices2
        
        Args:
            hedge_ratio: Hedge ratio to use (if None, calculate it)
        
        Returns:
            Spread series
        """
        if hedge_ratio is None:
            if self.hedge_ratio is None:
                hedge_ratio = self.calculate_hedge_ratio()
            else:
                hedge_ratio = self.hedge_ratio
        else:
            self.hedge_ratio = hedge_ratio
        
        self.spread = self.prices1 - hedge_ratio * self.prices2
        
        logger.info(f"Spread mean: {self.spread.mean():.4f}, "
                   f"std: {self.spread.std():.4f}")
        
        return self.spread
    
    def test_stationarity(self, series: Optional[pd.Series] = None, 
                         confidence_level: float = 0.05) -> Tuple[bool, float, dict]:
        """
        Test if a series is stationary using Augmented Dickey-Fuller test.
        
        From Chan's Chapter 7: A spread must be stationary (mean-reverting)
        for pairs trading to work.
        
        Args:
            series: Time series to test (if None, use the spread)
            confidence_level: Significance level (default 0.05 for 95% confidence)
        
        Returns:
            Tuple of (is_stationary, p_value, adf_results)
        """
        if series is None:
            if self.spread is None:
                self.calculate_spread()
            series = self.spread
        
        # Perform ADF test
        adf_result = adfuller(series, autolag='AIC')
        
        adf_statistic = adf_result[0]
        p_value = adf_result[1]
        critical_values = adf_result[4]
        
        is_stationary = p_value < confidence_level
        
        logger.info("Augmented Dickey-Fuller Test Results:")
        logger.info(f"  ADF Statistic: {adf_statistic:.4f}")
        logger.info(f"  p-value: {p_value:.4f}")
        logger.info(f"  Critical Values:")
        for key, value in critical_values.items():
            logger.info(f"    {key}: {value:.4f}")
        
        if is_stationary:
            logger.info(f"✓ Spread is STATIONARY (p-value {p_value:.4f} < {confidence_level})")
            logger.info("  This is good for mean-reversion trading!")
        else:
            logger.warning(f"✗ Spread is NOT stationary (p-value {p_value:.4f} >= {confidence_level})")
            logger.warning("  Pairs trading may not be profitable for this pair.")
        
        results = {
            'adf_statistic': adf_statistic,
            'p_value': p_value,
            'critical_values': critical_values,
            'is_stationary': is_stationary
        }
        
        return is_stationary, p_value, results
    
    def test_cointegration(self, confidence_level: float = 0.05) -> Tuple[bool, float]:
        """
        Test if the two price series are cointegrated.
        
        From Chan's Chapter 7: Use Engle-Granger cointegration test.
        
        Args:
            confidence_level: Significance level (default 0.05)
        
        Returns:
            Tuple of (is_cointegrated, p_value)
        """
        # Perform Engle-Granger cointegration test
        score, p_value, _ = coint(self.prices1, self.prices2)
        
        is_cointegrated = p_value < confidence_level
        
        logger.info("Engle-Granger Cointegration Test Results:")
        logger.info(f"  Test Statistic: {score:.4f}")
        logger.info(f"  p-value: {p_value:.4f}")
        
        if is_cointegrated:
            logger.info(f"✓ Series are COINTEGRATED (p-value {p_value:.4f} < {confidence_level})")
            logger.info("  This pair is suitable for statistical arbitrage!")
        else:
            logger.warning(f"✗ Series are NOT cointegrated (p-value {p_value:.4f} >= {confidence_level})")
            logger.warning("  This pair may not be suitable for pairs trading.")
        
        return is_cointegrated, p_value
    
    def calculate_half_life(self, spread: Optional[pd.Series] = None) -> float:
        """
        Calculate the half-life of mean reversion.
        
        From Chan's Chapter 7: Half-life tells us how long it takes for
        the spread to revert halfway back to its mean. Typical values are
        1-60 days for daily data.
        
        Args:
            spread: Spread series (if None, use self.spread)
        
        Returns:
            Half-life in days
        """
        if spread is None:
            if self.spread is None:
                self.calculate_spread()
            spread = self.spread
        
        # Calculate lagged spread
        spread_lag = spread.shift(1)
        spread_lag = spread_lag.dropna()
        
        # Calculate change in spread
        spread_delta = spread - spread_lag
        spread_delta = spread_delta.dropna()
        
        # Align the series
        common_idx = spread_lag.index.intersection(spread_delta.index)
        spread_lag = spread_lag.loc[common_idx]
        spread_delta = spread_delta.loc[common_idx]
        
        # Regression: delta(spread) = lambda * spread_lag + error
        # lambda = -log(2) / half_life
        model = OLS(spread_delta.values, spread_lag.values).fit()
        lambda_coef = model.params[0]
        
        if lambda_coef >= 0:
            logger.warning("Spread is not mean-reverting (lambda >= 0)")
            return np.inf
        
        half_life = -np.log(2) / lambda_coef
        
        logger.info(f"Half-life of mean reversion: {half_life:.2f} days")
        
        if half_life < 1:
            logger.info("  Very fast mean reversion - may need high-frequency trading")
        elif half_life <= 30:
            logger.info("  Good half-life for daily trading")
        elif half_life <= 60:
            logger.info("  Moderate half-life - still tradeable")
        else:
            logger.warning("  Half-life too long - spread may not revert quickly enough")
        
        return half_life
    
    def plot_analysis(self):
        """
        Create comprehensive visualization of cointegration analysis.
        """
        if self.spread is None:
            self.calculate_spread()
        
        fig, axes = plt.subplots(3, 1, figsize=(14, 12))
        
        # Plot 1: Both price series (normalized)
        norm_prices1 = self.prices1 / self.prices1.iloc[0] * 100
        norm_prices2 = self.prices2 / self.prices2.iloc[0] * 100
        
        axes[0].plot(norm_prices1.index, norm_prices1.values, 
                    label=self.symbol1, linewidth=2)
        axes[0].plot(norm_prices2.index, norm_prices2.values, 
                    label=self.symbol2, linewidth=2)
        axes[0].set_title('Normalized Price Series', fontsize=14, fontweight='bold')
        axes[0].set_ylabel('Normalized Price (100 = start)', fontsize=12)
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)
        
        # Plot 2: Spread
        axes[1].plot(self.spread.index, self.spread.values, 
                    linewidth=1.5, color='green')
        axes[1].axhline(y=self.spread.mean(), color='red', linestyle='--', 
                       label='Mean', linewidth=2)
        axes[1].axhline(y=self.spread.mean() + 2*self.spread.std(), 
                       color='orange', linestyle='--', label='±2σ', alpha=0.7)
        axes[1].axhline(y=self.spread.mean() - 2*self.spread.std(), 
                       color='orange', linestyle='--', alpha=0.7)
        axes[1].set_title(f'Spread ({self.symbol1} - {self.hedge_ratio:.4f} × {self.symbol2})', 
                         fontsize=14, fontweight='bold')
        axes[1].set_ylabel('Spread Value', fontsize=12)
        axes[1].legend()
        axes[1].grid(True, alpha=0.3)
        
        # Plot 3: Z-score of spread
        zscore = (self.spread - self.spread.mean()) / self.spread.std()
        axes[2].plot(zscore.index, zscore.values, linewidth=1.5, color='blue')
        axes[2].axhline(y=0, color='black', linestyle='-', alpha=0.5)
        axes[2].axhline(y=2, color='red', linestyle='--', label='Entry Threshold (±2σ)')
        axes[2].axhline(y=-2, color='red', linestyle='--')
        axes[2].axhline(y=1, color='orange', linestyle='--', 
                       label='Exit Threshold (±1σ)', alpha=0.7)
        axes[2].axhline(y=-1, color='orange', linestyle='--', alpha=0.7)
        axes[2].set_title('Z-Score of Spread', fontsize=14, fontweight='bold')
        axes[2].set_xlabel('Date', fontsize=12)
        axes[2].set_ylabel('Z-Score', fontsize=12)
        axes[2].legend()
        axes[2].grid(True, alpha=0.3)
        
        plt.tight_layout()
        return fig
    
    def full_analysis(self) -> dict:
        """
        Perform complete cointegration analysis.
        
        Returns:
            Dictionary with all analysis results
        """
        logger.info("="*60)
        logger.info(f"COINTEGRATION ANALYSIS: {self.symbol1} vs {self.symbol2}")
        logger.info("="*60)
        
        # Calculate hedge ratio and spread
        hedge_ratio = self.calculate_hedge_ratio()
        spread = self.calculate_spread()
        
        # Test cointegration
        is_cointegrated, coint_pvalue = self.test_cointegration()
        
        # Test stationarity of spread
        is_stationary, adf_pvalue, adf_results = self.test_stationarity()
        
        # Calculate half-life
        half_life = self.calculate_half_life()
        
        results = {
            'hedge_ratio': hedge_ratio,
            'spread_mean': spread.mean(),
            'spread_std': spread.std(),
            'is_cointegrated': is_cointegrated,
            'cointegration_pvalue': coint_pvalue,
            'is_stationary': is_stationary,
            'adf_pvalue': adf_pvalue,
            'adf_statistic': adf_results['adf_statistic'],
            'half_life': half_life
        }
        
        logger.info("="*60)
        logger.info("ANALYSIS SUMMARY:")
        logger.info(f"  Hedge Ratio: {hedge_ratio:.4f}")
        logger.info(f"  Cointegrated: {'YES' if is_cointegrated else 'NO'} "
                   f"(p-value: {coint_pvalue:.4f})")
        logger.info(f"  Spread Stationary: {'YES' if is_stationary else 'NO'} "
                   f"(p-value: {adf_pvalue:.4f})")
        logger.info(f"  Half-Life: {half_life:.2f} days")
        
        if is_cointegrated and is_stationary and 1 <= half_life <= 60:
            logger.info("✓ This pair is EXCELLENT for pairs trading!")
        elif is_cointegrated or is_stationary:
            logger.info("⚠ This pair is MARGINAL for pairs trading")
        else:
            logger.info("✗ This pair is NOT suitable for pairs trading")
        logger.info("="*60)
        
        return results


if __name__ == "__main__":
    # Test the cointegration analyzer
    from data_fetcher import DataFetcher
    
    logging.basicConfig(level=logging.INFO, 
                       format='%(levelname)s - %(message)s')
    
    print("\n" + "="*60)
    print("TESTING COINTEGRATION ANALYZER")
    print("="*60 + "\n")
    
    # Fetch data
    fetcher = DataFetcher('GLD', 'GDX')
    data1, data2 = fetcher.fetch_data(start_date='2018-01-01')
    
    # Use only training period for analysis (first 252 days)
    train_data1 = data1.iloc[:252]['close']
    train_data2 = data2.iloc[:252]['close']
    
    # Analyze cointegration
    analyzer = CointegrationAnalyzer(train_data1, train_data2, 'GLD', 'GDX')
    results = analyzer.full_analysis()
    
    # Plot analysis
    fig = analyzer.plot_analysis()
    plt.savefig('cointegration_analysis.png', dpi=150, bbox_inches='tight')
    print(f"\nPlot saved as 'cointegration_analysis.png'")
    plt.show()
