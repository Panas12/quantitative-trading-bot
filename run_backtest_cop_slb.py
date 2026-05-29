import logging
import matplotlib.pyplot as plt
from data_fetcher import DataFetcher
from pairs_trading_strategy import PairsTradingStrategy
from backtest_engine import BacktestEngine
from config import TRANSACTION_COST_BPS, SLIPPAGE_BPS

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

fetcher = DataFetcher('COP', 'SLB')
# Fetch 1.5 years of data (approx Nov 2024 to May 2026)
data1, data2 = fetcher.fetch_data(start_date='2024-11-29')

# Use 1 year (252 days) for training, leaving the last 6 months (~126 days) for testing
(train1, train2), (test1, test2) = fetcher.split_train_test(train_days=252)

strategy = PairsTradingStrategy(entry_threshold=1.5, exit_threshold=0.5)
strategy_results = strategy.run_strategy(
    prices1=test1['close'],
    prices2=test2['close'],
    train_prices1=train1['close'],
    train_prices2=train2['close']
)

engine = BacktestEngine(transaction_cost_bps=TRANSACTION_COST_BPS, slippage_bps=SLIPPAGE_BPS)
results = engine.run_backtest(
    prices1=test1['close'],
    prices2=test2['close'],
    positions=strategy_results['positions'],
    hedge_ratio=strategy_results['hedge_ratio'],
    initial_capital=136.70
)

fig = engine.plot_results(results, title="COP-SLB 6-Month Backtest (Trained on Prior 12 Months)")
plt.savefig('cop_slb_backtest.png', dpi=150, bbox_inches='tight')
print("Plot saved as 'cop_slb_backtest.png'")
