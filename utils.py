"""
Utility functions for the Quantitative Trading Bot
Based on Ernest Chan's "Quantitative Trading" methodology
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Tuple, Optional
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def calculate_sharpe_ratio(returns: pd.Series, periods_per_year: int = 252) -> float:
    """
    Calculate annualized Sharpe ratio.
    
    From Chan's book Chapter 3: Sharpe ratio is the most important metric
    for risk-adjusted returns.
    
    Args:
        returns: Series of period returns
        periods_per_year: Number of periods per year (252 for daily)
    
    Returns:
        Annualized Sharpe ratio
    """
    if len(returns) == 0 or returns.std() == 0:
        return 0.0
    
    mean_return = returns.mean()
    std_return = returns.std()
    sharpe = np.sqrt(periods_per_year) * (mean_return / std_return)
    
    return sharpe


def calculate_max_drawdown(cumulative_returns: pd.Series) -> Tuple[float, int]:
    """
    Calculate maximum drawdown and its duration.
    
    From Chan's book Chapter 3: Maximum drawdown is critical for understanding
    worst-case scenarios.
    
    Args:
        cumulative_returns: Series of cumulative returns
    
    Returns:
        Tuple of (max_drawdown, max_drawdown_duration_days)
    """
    if len(cumulative_returns) == 0:
        return 0.0, 0
    
    # Calculate running maximum (high watermark)
    running_max = cumulative_returns.cummax()
    
    # Calculate drawdown
    drawdown = (cumulative_returns - running_max) / (1 + running_max)
    
    # Find maximum drawdown
    max_dd = drawdown.min()
    
    # Calculate drawdown duration
    is_in_drawdown = drawdown < 0
    drawdown_duration = 0
    current_duration = 0
    
    for in_dd in is_in_drawdown:
        if in_dd:
            current_duration += 1
            drawdown_duration = max(drawdown_duration, current_duration)
        else:
            current_duration = 0
    
    return max_dd, drawdown_duration


def calculate_win_rate(returns: pd.Series) -> float:
    """
    Calculate the percentage of profitable periods.
    
    Args:
        returns: Series of period returns
    
    Returns:
        Win rate as a decimal (0.0 to 1.0)
    """
    if len(returns) == 0:
        return 0.0
    
    winning_periods = (returns > 0).sum()
    total_periods = len(returns)
    
    return winning_periods / total_periods


def calculate_profit_factor(returns: pd.Series) -> float:
    """
    Calculate profit factor (gross profit / gross loss).
    
    Args:
        returns: Series of period returns
    
    Returns:
        Profit factor
    """
    profits = returns[returns > 0].sum()
    losses = abs(returns[returns < 0].sum())
    
    if losses == 0:
        return np.inf if profits > 0 else 0.0
    
    return profits / losses


def calculate_calmar_ratio(cumulative_returns: pd.Series, periods_per_year: int = 252) -> float:
    """
    Calculate Calmar ratio (annualized return / max drawdown).
    
    Args:
        cumulative_returns: Series of cumulative returns
        periods_per_year: Number of periods per year
    
    Returns:
        Calmar ratio
    """
    if len(cumulative_returns) == 0:
        return 0.0
    
    total_return = cumulative_returns.iloc[-1]
    periods = len(cumulative_returns)
    annualized_return = (1 + total_return) ** (periods_per_year / periods) - 1
    
    max_dd, _ = calculate_max_drawdown(cumulative_returns)
    
    if max_dd == 0:
        return np.inf if annualized_return > 0 else 0.0
    
    return annualized_return / abs(max_dd)


def align_data(data1: pd.DataFrame, data2: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Align two dataframes by their indices (dates).
    
    From Chan's Example 3.6: Need to align trading days between instruments.
    
    Args:
        data1: First dataframe
        data2: Second dataframe
    
    Returns:
        Tuple of aligned dataframes
    """
    # Find common dates
    common_index = data1.index.intersection(data2.index)
    
    # Sort by date
    common_index = common_index.sort_values()
    
    # Align both dataframes
    aligned_data1 = data1.loc[common_index]
    aligned_data2 = data2.loc[common_index]
    
    logger.info(f"Aligned data: {len(common_index)} common dates")
    
    return aligned_data1, aligned_data2


def plot_equity_curve(cumulative_returns: pd.Series, title: str = "Equity Curve"):
    """
    Plot the equity curve over time.
    
    Args:
        cumulative_returns: Series of cumulative returns
        title: Plot title
    """
    plt.figure(figsize=(14, 6))
    
    # Convert to percentage
    equity = (1 + cumulative_returns) * 100
    
    plt.plot(equity.index, equity.values, linewidth=2)
    plt.title(title, fontsize=14, fontweight='bold')
    plt.xlabel('Date', fontsize=12)
    plt.ylabel('Equity (% of initial capital)', fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    return plt.gcf()


def plot_drawdown(cumulative_returns: pd.Series, title: str = "Drawdown Over Time"):
    """
    Plot drawdown over time.
    
    Args:
        cumulative_returns: Series of cumulative returns
        title: Plot title
    """
    plt.figure(figsize=(14, 6))
    
    # Calculate drawdown
    running_max = cumulative_returns.cummax()
    drawdown = (cumulative_returns - running_max) / (1 + running_max)
    
    plt.fill_between(drawdown.index, drawdown.values * 100, 0, 
                     color='red', alpha=0.3)
    plt.plot(drawdown.index, drawdown.values * 100, 
             color='darkred', linewidth=2)
    plt.title(title, fontsize=14, fontweight='bold')
    plt.xlabel('Date', fontsize=12)
    plt.ylabel('Drawdown (%)', fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    return plt.gcf()


def plot_spread_and_zscore(spread: pd.Series, zscore: pd.Series, 
                           entry_threshold: float = 2.0,
                           exit_threshold: float = 1.0):
    """
    Plot the spread and its z-score with entry/exit thresholds.
    
    From Chan's Example 3.6: Visualizing the spread helps understand
    trading opportunities.
    
    Args:
        spread: Series of spread values
        zscore: Series of z-score values
        entry_threshold: Entry threshold (standard deviations)
        exit_threshold: Exit threshold (standard deviations)
    """
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
    
    # Plot spread
    ax1.plot(spread.index, spread.values, linewidth=1.5, color='blue')
    ax1.axhline(y=spread.mean(), color='black', linestyle='--', 
                label='Mean', alpha=0.7)
    ax1.set_title('Price Spread', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Spread Value', fontsize=12)
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot z-score
    ax2.plot(zscore.index, zscore.values, linewidth=1.5, color='green')
    ax2.axhline(y=0, color='black', linestyle='-', alpha=0.5)
    ax2.axhline(y=entry_threshold, color='red', linestyle='--', 
                label=f'Entry Threshold (±{entry_threshold}σ)')
    ax2.axhline(y=-entry_threshold, color='red', linestyle='--')
    ax2.axhline(y=exit_threshold, color='orange', linestyle='--', 
                label=f'Exit Threshold (±{exit_threshold}σ)', alpha=0.7)
    ax2.axhline(y=-exit_threshold, color='orange', linestyle='--', alpha=0.7)
    ax2.set_title('Z-Score of Spread', fontsize=14, fontweight='bold')
    ax2.set_xlabel('Date', fontsize=12)
    ax2.set_ylabel('Z-Score', fontsize=12)
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    return fig


def print_performance_summary(returns: pd.Series, cumulative_returns: pd.Series,
                              strategy_name: str = "Strategy"):
    """
    Print a comprehensive performance summary.
    
    Args:
        returns: Series of period returns
        cumulative_returns: Series of cumulative returns
        strategy_name: Name of the strategy
    """
    sharpe = calculate_sharpe_ratio(returns)
    max_dd, dd_duration = calculate_max_drawdown(cumulative_returns)
    win_rate = calculate_win_rate(returns)
    profit_factor = calculate_profit_factor(returns)
    calmar = calculate_calmar_ratio(cumulative_returns)
    
    total_return = cumulative_returns.iloc[-1] if len(cumulative_returns) > 0 else 0
    
    print("\n" + "="*60)
    print(f"PERFORMANCE SUMMARY: {strategy_name}")
    print("="*60)
    print(f"Total Return:        {total_return*100:>10.2f}%")
    print(f"Sharpe Ratio:        {sharpe:>10.2f}")
    print(f"Calmar Ratio:        {calmar:>10.2f}")
    print(f"Max Drawdown:        {max_dd*100:>10.2f}%")
    print(f"Drawdown Duration:   {dd_duration:>10d} days")
    print(f"Win Rate:            {win_rate*100:>10.2f}%")
    print(f"Profit Factor:       {profit_factor:>10.2f}")
    print(f"Number of Trades:    {len(returns):>10d}")
    print("="*60 + "\n")
