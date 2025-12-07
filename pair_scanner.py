"""
Pair Scanner - Find Currently Cointegrated Trading Pairs

This module scans multiple asset pairs to identify those that are
currently cointegrated and suitable for pairs trading.

Usage:
    python pair_scanner.py --start 2023-01-01
"""

import pandas as pd
import numpy as np
from typing import List, Tuple, Dict
from statsmodels.tsa.stattools import coint
from statsmodels.regression.linear_model import OLS
import logging
from data_fetcher import DataFetcher
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class PairScanner:
    """
    Automated scanner to find cointegrated pairs across multiple assets.
    """
    
    # Candidate pairs to test
    CANDIDATE_PAIRS = [
        # Precious Metals
        ('GLD', 'SLV'),   # Gold vs Silver
        ('GLD', 'GDX'),   # Gold vs Gold Miners
        ('SLV', 'SIVR'),  # Silver ETFs
        
        # Energy
        ('USO', 'XLE'),   # Oil vs Energy Sector
        ('USO', 'OIH'),   # Oil vs Oil Services
        ('XLE', 'XOP'),   # Large vs Small Energy
        
        # Geographic (Commodity Economies)
        ('EWA', 'EWC'),   # Australia vs Canada
        ('EWG', 'EWU'),   # Germany vs UK
        
        # Tech
        ('QQQ', 'XLK'),   # Nasdaq vs Tech Sector
        ('SMH', 'SOXX'),  # Semiconductor ETFs
        
        # Financials
        ('XLF', 'KRE'),   # Large vs Regional Banks
        
        # International
        ('SPY', 'EFA'),   # US vs International
        ('EEM', 'VWO'),   # Emerging Markets
    ]
    
    def __init__(self, start_date: str = '2023-01-01', end_date: str = None):
        """
        Initialize pair scanner.
        
        Args:
            start_date: Start date for testing (YYYY-MM-DD)
            end_date: End date for testing (default: today)
        """
        self.start_date = start_date
        self.end_date = end_date or datetime.now().strftime('%Y-%m-%d')
        self.results = []
        
    def fetch_pair_data(self, symbol1: str, symbol2: str) -> Tuple[pd.Series, pd.Series]:
        """
        Fetch price data for a pair.
        
        Args:
            symbol1: First symbol
            symbol2: Second symbol
            
        Returns:
            Tuple of (prices1, prices2)
        """
        try:
            fetcher = DataFetcher(symbol1, symbol2)
            data1, data2 = fetcher.fetch_data(
                start_date=self.start_date,
                end_date=self.end_date
            )
            return data1['close'], data2['close']
        except Exception as e:
            logger.error(f"Error fetching {symbol1}-{symbol2}: {e}")
            return None, None
    
    def test_cointegration(self, prices1: pd.Series, prices2: pd.Series) -> Dict:
        """
        Test if two price series are cointegrated.
        
        Args:
            prices1: First price series
            prices2: Second price series
            
        Returns:
            Dictionary with cointegration test results
        """
        # Engle-Granger cointegration test
        score, pvalue, _ = coint(prices1, prices2)
        
        # Calculate hedge ratio (beta from linear regression)
        X = prices2.values.reshape(-1, 1)
        y = prices1.values
        model = OLS(y, X).fit()
        hedge_ratio = model.params[0]
        
        # Calculate spread
        spread = prices1 - hedge_ratio * prices2
        
        # Spread statistics
        spread_mean = spread.mean()
        spread_std = spread.std()
        spread_vol = spread.std() / spread.mean() if spread.mean() != 0 else np.inf
        
        # Half-life of mean reversion (Ornstein-Uhlenbeck process)
        spread_lag = spread.shift(1)
        spread_diff = spread - spread_lag
        spread_lag = spread_lag.dropna()
        spread_diff = spread_diff.dropna()
        
        # Align indices
        common_index = spread_lag.index.intersection(spread_diff.index)
        spread_lag = spread_lag.loc[common_index]
        spread_diff = spread_diff.loc[common_index]
        
        if len(spread_lag) > 0:
            X_hl = spread_lag.values.reshape(-1, 1)
            y_hl = spread_diff.values
            model_hl = OLS(y_hl, X_hl).fit()
            halflife = -np.log(2) / model_hl.params[0] if model_hl.params[0] < 0 else np.inf
        else:
            halflife = np.inf
        
        return {
            'score': score,
            'pvalue': pvalue,
            'hedge_ratio': hedge_ratio,
            'spread_mean': spread_mean,
            'spread_std': spread_std,
            'spread_volatility': spread_vol,
            'halflife_days': halflife,
            'cointegrated': pvalue < 0.05
        }
    
    def calculate_liquidity_score(self, prices1: pd.Series, prices2: pd.Series) -> float:
        """
        Estimate liquidity based on price stability.
        
        Higher score = more liquid (less volatile daily returns)
        """
        returns1 = prices1.pct_change().dropna()
        returns2 = prices2.pct_change().dropna()
        
        vol1 = returns1.std()
        vol2 = returns2.std()
        
        # Lower volatility = higher liquidity score
        liquidity_score = 1 / ((vol1 + vol2) / 2)
        
        return liquidity_score
    
    def test_pair(self, symbol1: str, symbol2: str) -> Dict:
        """
        Complete test of a single pair.
        
        Args:
            symbol1: First symbol
            symbol2: Second symbol
            
        Returns:
            Dictionary with all test results
        """
        logger.info(f"Testing {symbol1}-{symbol2}...")
        
        # Fetch data
        prices1, prices2 = self.fetch_pair_data(symbol1, symbol2)
        
        if prices1 is None or prices2 is None:
            return {
                'pair': f"{symbol1}-{symbol2}",
                'status': 'ERROR',
                'error': 'Failed to fetch data'
            }
        
        # Test cointegration
        coint_result = self.test_cointegration(prices1, prices2)
        
        # Calculate liquidity
        liquidity = self.calculate_liquidity_score(prices1, prices2)
        
        # Combine results
        result = {
            'pair': f"{symbol1}-{symbol2}",
            'symbol1': symbol1,
            'symbol2': symbol2,
            'status': 'SUCCESS',
            'cointegrated': coint_result['cointegrated'],
            'pvalue': coint_result['pvalue'],
            'hedge_ratio': coint_result['hedge_ratio'],
            'spread_volatility': coint_result['spread_volatility'],
            'halflife_days': coint_result['halflife_days'],
            'liquidity_score': liquidity,
            'data_points': len(prices1)
        }
        
        return result
    
    def scan_all_pairs(self) -> pd.DataFrame:
        """
        Scan all candidate pairs.
        
        Returns:
            DataFrame with results for all pairs
        """
        logger.info("=" * 70)
        logger.info("PAIR SCANNER - Finding Cointegrated Pairs")
        logger.info("=" * 70)
        logger.info(f"Test Period: {self.start_date} to {self.end_date}")
        logger.info(f"Testing {len(self.CANDIDATE_PAIRS)} pairs...")
        logger.info("")
        
        results = []
        
        for symbol1, symbol2 in self.CANDIDATE_PAIRS:
            result = self.test_pair(symbol1, symbol2)
            results.append(result)
            
            # Log result
            if result['status'] == 'SUCCESS':
                status_icon = "✓" if result['cointegrated'] else "✗"
                logger.info(
                    f"{status_icon} {result['pair']}: "
                    f"p-value={result['pvalue']:.4f}, "
                    f"halflife={result['halflife_days']:.1f} days"
                )
            else:
                logger.warning(f"✗ {result['pair']}: {result.get('error', 'Unknown error')}")
        
        # Convert to DataFrame
        df = pd.DataFrame(results)
        
        # Filter successful tests
        df = df[df['status'] == 'SUCCESS'].copy()
        
        if len(df) == 0:
            logger.error("No successful tests - check data availability")
            return df
        
        # Sort by cointegration strength (p-value)
        df = df.sort_values('pvalue')
        
        return df
    
    def rank_pairs(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Rank pairs by trading suitability.
        
        Scoring factors:
        1. Cointegration (p-value < 0.05)
        2. Short half-life (< 30 days preferred)
        3. Reasonable spread volatility
        4. High liquidity
        
        Args:
            df: DataFrame from scan_all_pairs
            
        Returns:
            DataFrame with ranking score
        """
        if len(df) == 0:
            return df
        
        df = df.copy()
        
        # Scoring components (0-100 each)
        
        # 1. Cointegration score (inverse p-value, capped at 0.05)
        df['coint_score'] = 100 * (1 - df['pvalue'].clip(0, 0.05) / 0.05)
        
        # 2. Half-life score (prefer 5-30 days)
        df['halflife_score'] = 100 * np.exp(-np.abs(df['halflife_days'] - 15) / 15)
        df.loc[df['halflife_days'] > 60, 'halflife_score'] = 0  # Too slow
        df.loc[df['halflife_days'] < 2, 'halflife_score'] = 0   # Too fast (noise)
        
        # 3. Volatility score (prefer moderate volatility)
        vol_median = df['spread_volatility'].median()
        df['volatility_score'] = 100 * np.exp(-np.abs(df['spread_volatility'] - vol_median) / vol_median)
        
        # 4. Liquidity score (normalize)
        liq_max = df['liquidity_score'].max()
        df['liquidity_score_norm'] = 100 * df['liquidity_score'] / liq_max
        
        # Total score (weighted average)
        df['total_score'] = (
            0.40 * df['coint_score'] +         # 40% weight on cointegration
            0.25 * df['halflife_score'] +      # 25% weight on half-life
            0.20 * df['volatility_score'] +    # 20% weight on volatility
            0.15 * df['liquidity_score_norm']  # 15% weight on liquidity
        )
        
        # Sort by total score
        df = df.sort_values('total_score', ascending=False)
        
        return df
    
    def print_summary(self, df: pd.DataFrame):
        """Print summary of scan results"""
        
        logger.info("")
        logger.info("=" * 70)
        logger.info("SCAN RESULTS SUMMARY")
        logger.info("=" * 70)
        
        if len(df) == 0:
            logger.info("No pairs tested successfully")
            return
        
        cointegrated = df[df['cointegrated'] == True]
        
        logger.info(f"Total Pairs Tested: {len(df)}")
        logger.info(f"Cointegrated Pairs (p < 0.05): {len(cointegrated)}")
        logger.info("")
        
        if len(cointegrated) > 0:
            logger.info("TOP 5 COINTEGRATED PAIRS:")
            logger.info("-" * 70)
            
            top5 = cointegrated.head(5)
            
            for idx, row in top5.iterrows():
                logger.info(f"\n{row['pair']}:")
                logger.info(f"  Score: {row['total_score']:.1f}/100")
                logger.info(f"  P-Value: {row['pvalue']:.4f} ✓")
                logger.info(f"  Hedge Ratio: {row['hedge_ratio']:.4f}")
                logger.info(f"  Half-Life: {row['halflife_days']:.1f} days")
                logger.info(f"  Spread Vol: {row['spread_volatility']:.2%}")
        else:
            logger.warning("⚠ NO cointegrated pairs found!")
            logger.warning("  Try:")
            logger.warning("  1. Different time period")
            logger.warning("  2. Different asset pairs")
            logger.warning("  3. Longer lookback window")
        
        logger.info("")
        logger.info("=" * 70)


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Scan for cointegrated pairs')
    parser.add_argument('--start', default='2023-01-01', help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end', default=None, help='End date (YYYY-MM-DD)')
    parser.add_argument('--output', default='pair_scan_results.csv', help='Output CSV file')
    
    args = parser.parse_args()
    
    # Run scanner
    scanner = PairScanner(start_date=args.start, end_date=args.end)
    results_df = scanner.scan_all_pairs()
    
    if len(results_df) > 0:
        # Rank pairs
        ranked_df = scanner.rank_pairs(results_df)
        
        # Print summary
        scanner.print_summary(ranked_df)
        
        # Save to CSV
        ranked_df.to_csv(args.output, index=False)
        logger.info(f"\n✓ Results saved to {args.output}")
    else:
        logger.error("No results to save")
