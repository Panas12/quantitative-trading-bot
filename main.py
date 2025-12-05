"""
Main Application for Quantitative Trading Bot
Based on Ernest Chan's "Quantitative Trading"

Orchestrates the complete trading workflow: data fetching, cointegration analysis,
strategy execution, backtesting, and performance reporting.
"""

import argparse
import logging
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import sys

# Import our modules
from config import *
from data_fetcher import DataFetcher
from cointegration_test import CointegrationAnalyzer
from pairs_trading_strategy import PairsTradingStrategy
from backtest_engine import BacktestEngine
from risk_manager import RiskManager
from utils import print_performance_summary

# Set up logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class QuantTradingBot:
    """
    Main trading bot class that orchestrates the entire workflow.
    
    From Ernest Chan's "Quantitative Trading":
    - Always validate strategy with cointegration tests
    - Backtest on train/test split
    - Use proper risk management
    - Minimize manual intervention
    """
    
    def __init__(self, symbol1: str = SYMBOL_1, symbol2: str = SYMBOL_2,
                 initial_capital: float = INITIAL_CAPITAL):
        """
        Initialize the trading bot.
        
        Args:
            symbol1: First trading symbol
            symbol2: Second trading symbol
            initial_capital: Starting capital
        """
        self.symbol1 = symbol1
        self.symbol2 = symbol2
        self.initial_capital = initial_capital
        
        # Initialize components
        self.data_fetcher = DataFetcher(symbol1, symbol2)
        self.strategy = PairsTradingStrategy(
            entry_threshold=ENTRY_THRESHOLD,
            exit_threshold=EXIT_THRESHOLD
        )
        self.backtest_engine = BacktestEngine(
            transaction_cost_bps=TRANSACTION_COST_BPS,
            slippage_bps=SLIPPAGE_BPS
        )
        self.risk_manager = RiskManager(
            initial_capital=initial_capital,
            kelly_fraction=KELLY_FRACTION,
            max_leverage=MAX_LEVERAGE,
            max_drawdown_pct=MAX_DRAWDOWN_PCT
        )
        
        logger.info(f"Initialized QuantTradingBot for {symbol1}-{symbol2}")
        logger.info(f"Initial capital: ${initial_capital:,.2f}")
    
    def run_analysis(self, start_date: str = START_DATE, 
                    end_date: str = None) -> dict:
        """
        Run complete analysis workflow.
        
        From Chan's methodology:
        1. Fetch and validate data
        2. Test for cointegration
        3. Split into train/test sets
        4. Backtest on both periods
        5. Compare results
        
        Args:
            start_date: Start date for historical data
            end_date: End date (None for current)
        
        Returns:
            Dictionary with all analysis results
        """
        logger.info("="*80)
        logger.info("STARTING QUANTITATIVE TRADING ANALYSIS")
        logger.info(f"Pair: {self.symbol1}-{self.symbol2}")
        logger.info(f"Date range: {start_date} to {end_date or 'present'}")
        logger.info("="*80)
        
        # Step 1: Fetch data
        logger.info("\n" + "="*60)
        logger.info("STEP 1: FETCHING HISTORICAL DATA")
        logger.info("="*60)
        data1, data2 = self.data_fetcher.fetch_data(
            start_date=start_date,
            end_date=end_date,
            min_history_days=MIN_HISTORY_DAYS
        )
        
        # Step 2: Split into train/test
        logger.info("\n" + "="*60)
        logger.info("STEP 2: SPLITTING DATA (TRAIN/TEST)")
        logger.info("="*60)
        (train1, train2), (test1, test2) = self.data_fetcher.split_train_test(
            train_days=LOOKBACK_PERIOD
        )
        
        # Step 3: Cointegration analysis on training data
        logger.info("\n" + "="*60)
        logger.info("STEP 3: COINTEGRATION ANALYSIS (TRAINING SET)")
        logger.info("="*60)
        coint_analyzer = CointegrationAnalyzer(
            train1['close'], train2['close'],
            self.symbol1, self.symbol2
        )
        coint_results = coint_analyzer.full_analysis()
        
        # Visualize cointegration
        coint_fig = coint_analyzer.plot_analysis()
        coint_fig.savefig('cointegration_analysis.png', dpi=150, bbox_inches='tight')
        logger.info("Saved cointegration analysis plot: cointegration_analysis.png")
        
        # Check if pair is suitable
        if not coint_results['is_cointegrated']:
            logger.warning("⚠ WARNING: Pair is not cointegrated!")
            logger.warning("  Trading this pair may not be profitable.")
        
        if coint_results['half_life'] > MAX_HALF_LIFE:
            logger.warning(f"⚠ WARNING: Half-life ({coint_results['half_life']:.1f} days) "
                         f"exceeds maximum ({MAX_HALF_LIFE} days)")
            logger.warning("  Mean reversion may be too slow for this strategy.")
        
        # Step 4: Backtest on training data
        logger.info("\n" + "="*60)
        logger.info("STEP 4: BACKTESTING ON TRAINING DATA")
        logger.info("="*60)
        train_strategy_results = self.strategy.run_strategy(
            prices1=train1['close'],
            prices2=train2['close'],
            train_prices1=train1['close'],  # Use same data for calibration
            train_prices2=train2['close']
        )
        
        train_backtest_results = self.backtest_engine.run_backtest(
            prices1=train1['close'],
            prices2=train2['close'],
            positions=train_strategy_results['positions'],
            hedge_ratio=train_strategy_results['hedge_ratio'],
            initial_capital=self.initial_capital
        )
        
        # Step 5: Backtest on testing data (out-of-sample)
        logger.info("\n" + "="*60)
        logger.info("STEP 5: BACKTESTING ON TESTING DATA (OUT-OF-SAMPLE)")
        logger.info("="*60)
        test_strategy_results = self.strategy.run_strategy(
            prices1=test1['close'],
            prices2=test2['close'],
            train_prices1=train1['close'],  # Use training data for calibration
            train_prices2=train2['close']
        )
        
        test_backtest_results = self.backtest_engine.run_backtest(
            prices1=test1['close'],
            prices2=test2['close'],
            positions=test_strategy_results['positions'],
            hedge_ratio=test_strategy_results['hedge_ratio'],
            initial_capital=self.initial_capital
        )
        
        # Step 6: Compare train vs test performance
        logger.info("\n" + "="*60)
        logger.info("STEP 6: COMPARING TRAINING VS TESTING PERFORMANCE")
        logger.info("="*60)
        self.backtest_engine.compare_train_test(
            train_backtest_results,
            test_backtest_results
        )
        
        # Step 7: Visualize results
        logger.info("\n" + "="*60)
        logger.info("STEP 7: GENERATING VISUALIZATIONS")
        logger.info("="*60)
        
        # Training results plot
        train_fig = self.backtest_engine.plot_results(
            train_backtest_results,
            title=f"{self.symbol1}-{self.symbol2} Pairs Trading - TRAINING SET"
        )
        train_fig.savefig('backtest_training.png', dpi=150, bbox_inches='tight')
        logger.info("Saved training backtest plot: backtest_training.png")
        
        # Testing results plot
        test_fig = self.backtest_engine.plot_results(
            test_backtest_results,
            title=f"{self.symbol1}-{self.symbol2} Pairs Trading - TESTING SET"
        )
        test_fig.savefig('backtest_testing.png', dpi=150, bbox_inches='tight')
        logger.info("Saved testing backtest plot: backtest_testing.png")
        
        # Step 8: Final assessment
        logger.info("\n" + "="*80)
        logger.info("FINAL ASSESSMENT")
        logger.info("="*80)
        
        test_sharpe = test_backtest_results['sharpe_ratio']
        test_return = test_backtest_results['annualized_return']
        test_dd = test_backtest_results['max_drawdown']
        
        logger.info(f"Out-of-Sample Sharpe Ratio: {test_sharpe:.2f}")
        logger.info(f"Out-of-Sample Annual Return: {test_return*100:.2f}%")
        logger.info(f"Out-of-Sample Max Drawdown: {test_dd*100:.2f}%")
        
        if test_sharpe >= 1.5:
            logger.info("✓✓✓ EXCELLENT strategy! Sharpe >= 1.5")
        elif test_sharpe >= 1.0:
            logger.info("✓✓ GOOD strategy! Sharpe >= 1.0")
        elif test_sharpe >= 0.5:
            logger.info("✓ MARGINAL strategy. Sharpe >= 0.5")
        else:
            logger.info("✗ POOR strategy. Sharpe < 0.5")
            logger.warning("  Not recommended for live trading.")
        
        logger.info("="*80)
        
        return {
            'cointegration': coint_results,
            'train_backtest': train_backtest_results,
            'test_backtest': test_backtest_results,
            'hedge_ratio': test_strategy_results['hedge_ratio']
        }
    
    def run_full_period_backtest(self, start_date: str = START_DATE,
                                end_date: str = None) -> dict:
        """
        Run backtest on the entire historical period (for final validation).
        
        Args:
            start_date: Start date
            end_date: End date (None for current)
        
        Returns:
            Backtest results dictionary
        """
        logger.info("\n" + "="*80)
        logger.info("RUNNING FULL-PERIOD BACKTEST")
        logger.info("="*80)
        
        # Fetch all data
        data1, data2 = self.data_fetcher.fetch_data(start_date, end_date)
        
        # Use first LOOKBACK_PERIOD for training
        train1 = data1.iloc[:LOOKBACK_PERIOD]
        train2 = data2.iloc[:LOOKBACK_PERIOD]
        
        # Run strategy on full period
        strategy_results = self.strategy.run_strategy(
            prices1=data1['close'],
            prices2=data2['close'],
            train_prices1=train1['close'],
            train_prices2=train2['close']
        )
        
        # Backtest
        backtest_results = self.backtest_engine.run_backtest(
            prices1=data1['close'],
            prices2=data2['close'],
            positions=strategy_results['positions'],
            hedge_ratio=strategy_results['hedge_ratio'],
            initial_capital=self.initial_capital
        )
        
        # Plot
        fig = self.backtest_engine.plot_results(
            backtest_results,
            title=f"{self.symbol1}-{self.symbol2} Pairs Trading - FULL PERIOD"
        )
        fig.savefig('backtest_full_period.png', dpi=150, bbox_inches='tight')
        logger.info("Saved full period backtest plot: backtest_full_period.png")
        
        return backtest_results


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Quantitative Trading Bot based on Ernest Chan\'s methodology'
    )
    parser.add_argument('--mode', type=str, default='analysis',
                       choices=['analysis', 'backtest', 'full'],
                       help='Mode: analysis (train/test split), backtest (same), full (entire period)')
    parser.add_argument('--symbol1', type=str, default=SYMBOL_1,
                       help=f'First symbol (default: {SYMBOL_1})')
    parser.add_argument('--symbol2', type=str, default=SYMBOL_2,
                       help=f'Second symbol (default: {SYMBOL_2})')
    parser.add_argument('--start', type=str, default=START_DATE,
                       help=f'Start date YYYY-MM-DD (default: {START_DATE})')
    parser.add_argument('--end', type=str, default=None,
                       help='End date YYYY-MM-DD (default: current date)')
    parser.add_argument('--capital', type=float, default=INITIAL_CAPITAL,
                       help=f'Initial capital (default: ${INITIAL_CAPITAL:,.0f})')
    
    args = parser.parse_args()
    
    # Create bot
    bot = QuantTradingBot(
        symbol1=args.symbol1,
        symbol2=args.symbol2,
        initial_capital=args.capital
    )
    
    # Run based on mode
    if args.mode in ['analysis', 'backtest']:
        results = bot.run_analysis(start_date=args.start, end_date=args.end)
    elif args.mode == 'full':
        results = bot.run_full_period_backtest(start_date=args.start, end_date=args.end)
    
    logger.info("\n" + "="*80)
    logger.info("ANALYSIS COMPLETE!")
    logger.info("="*80)
    logger.info("Generated files:")
    logger.info("  - cointegration_analysis.png")
    logger.info("  - backtest_training.png")
    logger.info("  - backtest_testing.png")
    logger.info(f"  - {LOG_FILE} (log file)")
    logger.info("="*80)
    
    # Keep plots open
    plt.show()


if __name__ == "__main__":
    main()
