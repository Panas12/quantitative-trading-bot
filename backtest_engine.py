"""
Backtesting Engine for Quantitative Trading Bot
Based on Ernest Chan's "Quantitative Trading" Chapter 3

Backtests the pairs trading strategy with transaction costs.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from typing import Optional, Tuple
import logging
from utils import (calculate_sharpe_ratio, calculate_max_drawdown, calculate_win_rate,
                   calculate_profit_factor, print_performance_summary,
                   plot_equity_curve, plot_drawdown)

logger = logging.getLogger(__name__)


class BacktestEngine:
    """
    Backtests pairs trading strategies with realistic cost modeling.
    
    From Chan's Chapter 3:
    - Always split data into training and testing sets
    - Include transaction costs (commissions + slippage)
    - Calculate key metrics: Sharpe ratio, max drawdown, win rate
    """
    
    def __init__(self, transaction_cost_bps: float = 5.0,
                 slippage_bps: float = 2.0):
        """
        Initialize Backtest Engine.
        
        Args:
            transaction_cost_bps: Transaction cost in basis points (default: 5)
            slippage_bps: Slippage in basis points (default: 2)
        """
        self.transaction_cost_bps = transaction_cost_bps
        self.slippage_bps = slippage_bps
        self.total_cost_bps = transaction_cost_bps + slippage_bps
        
    def calculate_returns(self, prices1: pd.Series, prices2: pd.Series,
                         positions: pd.Series, hedge_ratio: float) -> pd.DataFrame:
        """
        Calculate returns from positions.
        
        From Chan: Returns are calculated on the spread, which is a portfolio
        of long symbol1 and short symbol2.
        
        Args:
            prices1: Price series for symbol 1
            prices2: Price series for symbol 2
            positions: Position series (+1 long spread, -1 short spread, 0 flat)
            hedge_ratio: Hedge ratio between symbols
        
        Returns:
            DataFrame with returns and other metrics
        """
        # Ensure data is properly aligned
        prices1 = prices1.squeeze() if isinstance(prices1, pd.DataFrame) else prices1
        prices2 = prices2.squeeze() if isinstance(prices2, pd.DataFrame) else prices2
        
        # Calculate price changes
        ret1 = prices1.pct_change()
        ret2 = prices2.pct_change()
        
        # Calculate spread returns
        # When long spread (positions=+1): long symbol1, short symbol2
        # Spread return = ret1 - hedge_ratio * ret2
        #
        # When short spread (positions=-1): short symbol1, long symbol2
        # Spread return = -(ret1 - hedge_ratio * ret2)
        
        spread_returns = positions.shift(1) * (ret1 - hedge_ratio * ret2)
        
        # Replace NaN and inf values
        spread_returns = spread_returns.replace([np.inf, -np.inf], 0).fillna(0)
        
        # Calculate transaction costs
        # Costs occur when position changes
        position_changes = positions.diff().fillna(0)
        has_transaction = (position_changes != 0).astype(float)
        
        # Transaction cost as percentage of capital
        # We trade both symbols, so cost is incurred on both legs
        transaction_costs = has_transaction * (self.total_cost_bps / 10000)
        
        # Net returns after costs
        net_returns = spread_returns - transaction_costs
        
        # Create results dataframe  
        results = pd.DataFrame({
            'gross_returns': spread_returns,
            'transaction_costs': transaction_costs,
            'net_returns': net_returns,
            'positions': positions,
            'position_changes': position_changes
        }, index=prices1.index)
        
        return results
    
    def run_backtest(self, prices1: pd.Series, prices2: pd.Series,
                    positions: pd.Series, hedge_ratio: float,
                    initial_capital: float = 100000) -> dict:
        """
        Run complete backtest and calculate performance metrics.
        
        Args:
            prices1: Price series for symbol 1
            prices2: Price series for symbol 2
            positions: Position series
            hedge_ratio: Hedge ratio
            initial_capital: Starting capital (default: $100,000)
        
        Returns:
            Dictionary with backtest results and metrics
        """
        logger.info("="*60)
        logger.info("RUNNING BACKTEST")
        logger.info("="*60)
        logger.info(f"Initial Capital: ${initial_capital:,.2f}")
        logger.info(f"Transaction Cost: {self.transaction_cost_bps} bps")
        logger.info(f"Slippage: {self.slippage_bps} bps")
        logger.info(f"Total Cost: {self.total_cost_bps} bps")
        logger.info(f"Period: {prices1.index[0]} to {prices1.index[-1]}")
        logger.info(f"Number of days: {len(prices1)}")
        
        # Calculate returns
        results = self.calculate_returns(prices1, prices2, positions, hedge_ratio)
        
        # Calculate cumulative returns
        cumulative_returns = (1 + results['net_returns']).cumprod() - 1
        cumulative_gross =  (1 + results['gross_returns']).cumprod() - 1
        
        # Calculate equity curve
        equity = initial_capital * (1 + cumulative_returns)
        
        # Performance metrics
        sharpe = calculate_sharpe_ratio(results['net_returns'], periods_per_year=252)
        sharpe_gross = calculate_sharpe_ratio(results['gross_returns'], periods_per_year=252)
        
        max_dd, dd_duration = calculate_max_drawdown(cumulative_returns)
        
        win_rate = calculate_win_rate(results['net_returns'])
        profit_factor = calculate_profit_factor(results['net_returns'])
        
        # Count trades
        num_trades = (results['position_changes'] != 0).sum()
        total_costs = results['transaction_costs'].sum() * initial_capital
        
        # Calculate returns
        total_return = cumulative_returns.iloc[-1]
        total_gross_return = cumulative_gross.iloc[-1]
        
        # Annualized returns
        years = len(prices1) / 252
        if years > 0:
            annualized_return = (1 + total_return) ** (1 / years) - 1
            annualized_gross = (1 + total_gross_return) ** (1 / years) - 1
        else:
            annualized_return = 0
            annualized_gross = 0
        
        logger.info("\n" + "="*60)
        logger.info("BACKTEST RESULTS")
        logger.info("="*60)
        logger.info(f"Total Return (Net):      {total_return*100:>10.2f}%")
        logger.info(f"Total Return (Gross):    {total_gross_return*100:>10.2f}%")
        logger.info(f"Annualized Return:       {annualized_return*100:>10.2f}%")
        logger.info(f"Sharpe Ratio (Net):      {sharpe:>10.2f}")
        logger.info(f"Sharpe Ratio (Gross):    {sharpe_gross:>10.2f}")
        logger.info(f"Max Drawdown:            {max_dd*100:>10.2f}%")
        logger.info(f"Drawdown Duration:       {dd_duration:>10d} days")
        logger.info(f"Win Rate:                {win_rate*100:>10.2f}%")
        logger.info(f"Profit Factor:           {profit_factor:>10.2f}")
        logger.info(f"Number of Trades:        {num_trades:>10d}")
        logger.info(f"Total Transaction Costs: ${total_costs:>10,.2f}")
        logger.info(f"Final Equity:            ${equity.iloc[-1]:>10,.2f}")
        logger.info("="*60)
        
        return {
            'results': results,
            'cumulative_returns': cumulative_returns,
            'cumulative_gross': cumulative_gross,
            'equity': equity,
            'sharpe_ratio': sharpe,
            'sharpe_gross': sharpe_gross,
            'max_drawdown': max_dd,
            'drawdown_duration': dd_duration,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'num_trades': num_trades,
            'total_return': total_return,
            'annualized_return': annualized_return,
            'total_costs': total_costs,
            'initial_capital': initial_capital,
            'final_capital': equity.iloc[-1]
        }
    
    def plot_results(self, backtest_results: dict, title: str = "Backtest Results"):
        """
        Create comprehensive visualization of backtest results.
        
        Args:
            backtest_results: Dictionary from run_backtest()
            title: Plot title
        """
        fig = plt.figure(figsize=(16, 12))
        gs = fig.add_gridspec(3, 2, hspace=0.3, wspace=0.3)
        
        # Plot 1: Equity curve
        ax1 = fig.add_subplot(gs[0, :])
        equity = backtest_results['equity']
        ax1.plot(equity.index, equity.values, linewidth=2, color='blue')
        ax1.axhline(y=backtest_results['initial_capital'], color='red', 
                   linestyle='--', label='Initial Capital', alpha=0.7)
        ax1.set_title(f'{title} - Equity Curve', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Portfolio Value ($)', fontsize=12)
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
        
        # Plot 2: Cumulative returns (net vs gross)
        ax2 = fig.add_subplot(gs[1, 0])
        cum_net = backtest_results['cumulative_returns'] * 100
        cum_gross = backtest_results['cumulative_gross'] * 100
        ax2.plot(cum_net.index, cum_net.values, linewidth=2, 
                label='Net Returns', color='green')
        ax2.plot(cum_gross.index, cum_gross.values, linewidth=2, 
                label='Gross Returns', color='blue', alpha=0.6)
        ax2.set_title('Cumulative Returns', fontsize=12, fontweight='bold')
        ax2.set_ylabel('Return (%)', fontsize=11)
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # Plot 3: Drawdown
        ax3 = fig.add_subplot(gs[1, 1])
        cum_ret = backtest_results['cumulative_returns']
        running_max = cum_ret.cummax()
        drawdown = ((cum_ret - running_max) / (1 + running_max)) * 100
        ax3.fill_between(drawdown.index, drawdown.values, 0, 
                        color='red', alpha=0.3)
        ax3.plot(drawdown.index, drawdown.values, color='darkred', linewidth=2)
        ax3.set_title('Drawdown', fontsize=12, fontweight='bold')
        ax3.set_ylabel('Drawdown (%)', fontsize=11)
        ax3.grid(True, alpha=0.3)
        
        # Plot 4: Positions over time
        ax4 = fig.add_subplot(gs[2, 0])
        positions = backtest_results['results']['positions']
        ax4.plot(positions.index, positions.values, linewidth=1.5, 
                color='purple', drawstyle='steps-post')
        ax4.set_title('Positions Over Time', fontsize=12, fontweight='bold')
        ax4.set_xlabel('Date', fontsize=11)
        ax4.set_ylabel('Position', fontsize=11)
        ax4.set_yticks([-1, 0, 1])
        ax4.set_yticklabels(['Short Spread', 'Flat', 'Long Spread'])
        ax4.grid(True, alpha=0.3)
        
        # Plot 5: Rolling Sharpe ratio (60-day)
        ax5 = fig.add_subplot(gs[2, 1])
        returns = backtest_results['results']['net_returns']
        rolling_sharpe = returns.rolling(60).mean() / returns.rolling(60).std() * np.sqrt(252)
        ax5.plot(rolling_sharpe.index, rolling_sharpe.values, linewidth=2, color='orange')
        ax5.axhline(y=0, color='black', linestyle='-', alpha=0.3)
        ax5.axhline(y=1, color='green', linestyle='--', alpha=0.5, label='Sharpe=1')
        ax5.set_title('Rolling Sharpe Ratio (60-day)', fontsize=12, fontweight='bold')
        ax5.set_xlabel('Date', fontsize=11)
        ax5.set_ylabel('Sharpe Ratio', fontsize=11)
        ax5.legend()
        ax5.grid(True, alpha=0.3)
        
        plt.suptitle(title, fontsize=16, fontweight='bold', y=0.995)
        
        return fig
    
    def compare_train_test(self, train_results: dict, test_results: dict):
        """
        Compare training and testing performance.
        
        From Chan: Out-of-sample performance is the true test of a strategy.
        
        Args:
            train_results: Backtest results on training data
            test_results: Backtest results on testing data
        """
        print("\n" + "="*60)
        print("TRAINING VS TESTING COMPARISON")
        print("="*60)
        print(f"{'Metric':<25} {'Training':>15} {'Testing':>15} {'Change':>10}")
        print("-"*60)
        
        metrics = [
            ('Total Return', 'total_return', 100),
            ('Annualized Return', 'annualized_return', 100),
            ('Sharpe Ratio', 'sharpe_ratio', 1),
            ('Max Drawdown', 'max_drawdown', 100),
            ('Win Rate', 'win_rate', 100),
            ('Profit Factor', 'profit_factor', 1),
            ('Num Trades', 'num_trades', 1)
        ]
        
        for name, key, multiplier in metrics:
            train_val = train_results[key] * multiplier if key != 'num_trades' else train_results[key]
            test_val = test_results[key] * multiplier if key != 'num_trades' else test_results[key]
            
            if train_val != 0 and key != 'num_trades':
                change = ((test_val - train_val) / abs(train_val)) * 100
                change_str = f"{change:+.1f}%"
            else:
                change_str = "-"
            
            if key in ['total_return', 'annualized_return', 'max_drawdown', 'win_rate']:
                print(f"{name:<25} {train_val:>14.2f}% {test_val:>14.2f}% {change_str:>10}")
            elif key == 'num_trades':
                print(f"{name:<25} {train_val:>15.0f} {test_val:>15.0f} {change_str:>10}")
            else:
                print(f"{name:<25} {train_val:>15.2f} {test_val:>15.2f} {change_str:>10}")
        
        print("="*60)
        
        # Determine if strategy degraded significantly
        sharpe_change = ((test_results['sharpe_ratio'] - train_results['sharpe_ratio']) / 
                        abs(train_results['sharpe_ratio'])) if train_results['sharpe_ratio'] != 0 else 0
        
        if sharpe_change < -0.5:
            logger.warning("⚠ Strategy performance degraded significantly in testing!")
            logger.warning("  This may indicate overfitting to training data.")
        elif test_results['sharpe_ratio'] > 0.5:
            logger.info("✓ Strategy shows good out-of-sample performance!")
        else:
            logger.info("⚠ Strategy shows marginal out-of-sample performance.")


if __name__ == "__main__":
    # Test the backtesting engine
    from data_fetcher import DataFetcher
    from pairs_trading_strategy import PairsTradingStrategy
    
    logging.basicConfig(level=logging.INFO,
                       format='%(levelname)s - %(message)s')
    
    print("\n" + "="*60)
    print("TESTING BACKTESTING ENGINE")
    print("="*60 + "\n")
    
    # Fetch data
    fetcher = DataFetcher('GLD', 'GDX')
    data1, data2 = fetcher.fetch_data(start_date='2018-01-01')
    
    # Split data
    (train1, train2), (test1, test2) = fetcher.split_train_test(train_days=252)
    
    # Run strategy
    strategy = PairsTradingStrategy(entry_threshold=2.0, exit_threshold=1.0)
    strategy_results = strategy.run_strategy(
        prices1=test1['close'],
        prices2=test2['close'],
        train_prices1=train1['close'],
        train_prices2=train2['close']
    )
    
    # Backtest
    backtest = BacktestEngine(transaction_cost_bps=5, slippage_bps=2)
    results = backtest.run_backtest(
        prices1=test1['close'],
        prices2=test2['close'],
        positions=strategy_results['positions'],
        hedge_ratio=strategy_results['hedge_ratio'],
        initial_capital=100000
    )
    
    # Plot
    fig = backtest.plot_results(results, title="GLD-GDX Pairs Trading Backtest")
    plt.savefig('backtest_results.png', dpi=150, bbox_inches='tight')
    print(f"\nPlot saved as 'backtest_results.png'")
    plt.show()
