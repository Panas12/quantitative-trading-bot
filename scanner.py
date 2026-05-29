import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
import itertools
from typing import List, Dict, Tuple, Optional

from data_fetcher import DataFetcher
from cointegration_test import CointegrationAnalyzer
from pairs_trading_strategy import PairsTradingStrategy
from backtest_engine import BacktestEngine
from config import LOOKBACK_PERIOD, TRANSACTION_COST_BPS, SLIPPAGE_BPS

logger = logging.getLogger(__name__)

class DynamicScanner:
    """
    Scans a universe of assets to find the most profitable, statistically 
    sound cointegrated pair for trading.
    """
    
    def __init__(self):
        # Define universe grouped by highly correlated sectors
        self.sectors = {
            'Financials': ['JPM', 'BAC', 'WFC', 'C', 'GS', 'MS', 'BK', 'STT'],
            'Energy': ['XOM', 'CVX', 'COP', 'OXY', 'SLB', 'HAL'],
            'Tech': ['AAPL', 'MSFT', 'GOOGL', 'META', 'AMD', 'INTC'],
            'Retail': ['WMT', 'TGT', 'COST', 'HD', 'LOW', 'MCD', 'SBUX'],
            'Healthcare': ['JNJ', 'UNH', 'PFE', 'ABBV', 'MRK', 'AMGN']
        }
        
        self.pairs_to_test = []
        for sector, symbols in self.sectors.items():
            # Generate all unique combinations within the sector
            self.pairs_to_test.extend(list(itertools.combinations(symbols, 2)))
            
    def scan_market(self, lookback_years: int = 2) -> Optional[Dict]:
        """
        Scan all pairs and return the most profitable one.
        
        Args:
            lookback_years: Years of historical data to fetch
        
        Returns:
            Dictionary with best pair details or None if no pair found
        """
        logger.info(f"Starting dynamic market scan on {len(self.pairs_to_test)} pairs...")
        start_date = (datetime.now() - timedelta(days=365 * lookback_years)).strftime('%Y-%m-%d')
        
        valid_candidates = []
        
        for sym1, sym2 in self.pairs_to_test:
            logger.info(f"Testing {sym1}-{sym2}...")
            try:
                # 1. Fetch Data
                fetcher = DataFetcher(sym1, sym2)
                data1, data2 = fetcher.fetch_data(start_date=start_date, min_history_days=300)
                
                # Check if enough data
                if len(data1) < LOOKBACK_PERIOD + 100:
                    continue
                    
                # Split train/test (Use first LOOKBACK_PERIOD for cointegration/training)
                train1 = data1.iloc[:LOOKBACK_PERIOD]
                train2 = data2.iloc[:LOOKBACK_PERIOD]
                test1 = data1.iloc[LOOKBACK_PERIOD:]
                test2 = data2.iloc[LOOKBACK_PERIOD:]
                
                # 2. Cointegration Analysis (on training data to prevent lookahead bias)
                analyzer = CointegrationAnalyzer(train1['close'], train2['close'], sym1, sym2)
                
                # Suppress plotting and standard logging for cleaner output
                old_level = logging.getLogger('cointegration_test').getEffectiveLevel()
                logging.getLogger('cointegration_test').setLevel(logging.ERROR)
                
                results = analyzer.full_analysis()
                logging.getLogger('cointegration_test').setLevel(old_level)
                
                # 3. Filter by realistic statistical criteria (90% confidence on AT LEAST ONE test)
                if results['cointegration_pvalue'] > 0.10 and results['adf_pvalue'] > 0.10:
                    continue
                if not (1 <= results['half_life'] <= 90):
                    continue
                    
                # 4. Backtest Out-of-Sample to verify profitability
                # Use slightly lower threshold to ensure we capture trades
                strategy = PairsTradingStrategy(entry_threshold=1.5, exit_threshold=0.5)
                
                strategy_results = strategy.run_strategy(
                    prices1=test1['close'],
                    prices2=test2['close'],
                    train_prices1=train1['close'],
                    train_prices2=train2['close']
                )
                
                engine = BacktestEngine(transaction_cost_bps=TRANSACTION_COST_BPS, slippage_bps=SLIPPAGE_BPS)
                
                # Suppress backtest logging
                old_level = logging.getLogger('backtest_engine').getEffectiveLevel()
                logging.getLogger('backtest_engine').setLevel(logging.ERROR)
                
                bt_results = engine.run_backtest(
                    prices1=test1['close'],
                    prices2=test2['close'],
                    positions=strategy_results['positions'],
                    hedge_ratio=strategy_results['hedge_ratio'],
                    initial_capital=1000  # Arbitrary for sharpe calculation
                )
                
                logging.getLogger('backtest_engine').setLevel(old_level)
                
                sharpe = bt_results.get('sharpe_ratio', 0)
                ret = bt_results.get('annualized_return', 0)
                trades = bt_results.get('total_trades', bt_results.get('num_trades', 0))
                
                # Require positive out of sample sharpe (or at least some profit)
                if sharpe > 0.1 and trades > 0:
                    candidate = {
                        'symbol1': sym1,
                        'symbol2': sym2,
                        'sharpe': sharpe,
                        'return': ret,
                        'half_life': results['half_life'],
                        'hedge_ratio': strategy_results['hedge_ratio'],
                        'eg_pvalue': results['cointegration_pvalue']
                    }
                    valid_candidates.append(candidate)
                    logger.info(f"✓ Found Valid Candidate: {sym1}-{sym2} | Sharpe: {sharpe:.2f} | Return: {ret*100:.2f}% | Half-life: {results['half_life']:.1f}")
                    
            except Exception as e:
                logger.debug(f"Failed to test {sym1}-{sym2}: {e}")
                continue
                
        if not valid_candidates:
            logger.warning("No mathematically sound and profitable pairs found in the current market environment.")
            return None
            
        # 5. Select Best Pair (Highest Sharpe)
        valid_candidates.sort(key=lambda x: x['sharpe'], reverse=True)
        best_pair = valid_candidates[0]
        
        logger.info("=" * 60)
        logger.info(f"🏆 BEST PAIR FOUND: {best_pair['symbol1']}-{best_pair['symbol2']}")
        logger.info(f"  Out-of-Sample Sharpe: {best_pair['sharpe']:.2f}")
        logger.info(f"  Out-of-Sample Return: {best_pair['return']*100:.2f}%")
        logger.info(f"  Half-life: {best_pair['half_life']:.1f} days")
        logger.info(f"  Cointegration p-value: {best_pair['eg_pvalue']:.4f}")
        logger.info("=" * 60)
        
        # Save to file for live_trading.py to use
        import json
        import os
        pair_file = os.path.join(os.path.dirname(__file__), 'current_pair.json')
        with open(pair_file, 'w') as f:
            json.dump(best_pair, f, indent=4)
        logger.info(f"Saved best pair to {pair_file}")
        
        return best_pair

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    scanner = DynamicScanner()
    scanner.scan_market()
