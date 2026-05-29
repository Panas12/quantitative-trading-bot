"""
Performance Tracker - Log and Analyze Trading Performance

Tracks all trades, calculates P&L, and generates performance reports.
"""

import pandas as pd
from datetime import datetime
import json
import os
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class PerformanceTracker:
    """
    Track trading performance and generate analytics.
    """
    
    def __init__(self, log_file: str = 'trades.csv'):
        self.log_file = log_file
        self.trades_df = self._load_trades()
    
    def _load_trades(self) -> pd.DataFrame:
        """Load existing trades from CSV"""
        if os.path.exists(self.log_file):
            return pd.read_csv(self.log_file, parse_dates=['entry_time', 'exit_time'])
        else:
            return pd.DataFrame(columns=[
                'trade_id', 'pair', 'direction', 'entry_time', 'exit_time',
                'entry_price', 'exit_price', 'size', 'pnl', 'pnl_pct',
                'regime', 'entry_zscore', 'exit_zscore', 'hold_days'
            ])
    
    def log_trade(self, trade_data: Dict):
        """
        Log a completed trade.
        
        Args:
            trade_data: Dictionary with trade details
        """
        # Calculate additional metrics
        if 'entry_time' in trade_data and 'exit_time' in trade_data:
            entry_dt = pd.to_datetime(trade_data['entry_time'])
            exit_dt = pd.to_datetime(trade_data['exit_time'])
            trade_data['hold_days'] = (exit_dt - entry_dt).days
        
        # Append to DataFrame
        new_trade = pd.DataFrame([trade_data])
        self.trades_df = pd.concat([self.trades_df, new_trade], ignore_index=True)
        
        # Save to CSV
        self.trades_df.to_csv(self.log_file, index=False)
        
        logger.info(f"Trade logged: {trade_data.get('pair')} {trade_data.get('direction')} - P&L: ${trade_data.get('pnl', 0):.2f}")
    
    def get_performance_metrics(self) -> Dict:
        """Calculate performance metrics"""
        if len(self.trades_df) == 0:
            return {'trades': 0, 'message': 'No trades yet'}
        
        df = self.trades_df.copy()
        
        # Basic stats
        total_trades = len(df)
        winning_trades = len(df[df['pnl'] > 0])
        losing_trades = len(df[df['pnl'] < 0])
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        # P&L stats
        total_pnl = df['pnl'].sum()
        avg_win = df[df['pnl'] > 0]['pnl'].mean() if winning_trades > 0 else 0
        avg_loss = df[df['pnl'] < 0]['pnl'].mean() if losing_trades > 0 else 0
        
        # Profit factor
        gross_profit = df[df['pnl'] > 0]['pnl'].sum()
        gross_loss = abs(df[df['pnl'] < 0]['pnl'].sum())
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        # Drawdown
        cumulative_pnl = df['pnl'].cumsum()
        running_max = cumulative_pnl.expanding().max()
        drawdown = cumulative_pnl - running_max
        max_drawdown = drawdown.min()
        
        # Average hold time
        avg_hold_days = df['hold_days'].mean() if 'hold_days' in df.columns else 0
        
        metrics = {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'max_drawdown': max_drawdown,
            'avg_hold_days': avg_hold_days,
            'last_trade_date': df['exit_time'].max() if 'exit_time' in df.columns else None
        }
        
        return metrics
    
    def generate_report(self) -> str:
        """Generate performance report"""
        metrics = self.get_performance_metrics()
        
        if metrics.get('trades') == 0:
            return "No trades to report."
        
        report = f"""
╔══════════════════════════════════════════════════════════════════╗
║                    TRADING PERFORMANCE REPORT                     ║
╚══════════════════════════════════════════════════════════════════╝

OVERVIEW
--------
Total Trades:        {metrics['total_trades']}
Winning Trades:      {metrics['winning_trades']} ({metrics['win_rate']:.1%})
Losing Trades:       {metrics['losing_trades']}

PROFITABILITY
-------------
Total P&L:           ${metrics['total_pnl']:.2f}
Average Win:         ${metrics['avg_win']:.2f}
Average Loss:        ${metrics['avg_loss']:.2f}
Profit Factor:       {metrics['profit_factor']:.2f}

RISK METRICS
------------
Max Drawdown:        ${metrics['max_drawdown']:.2f}
Avg Hold Time:       {metrics['avg_hold_days']:.1f} days

PAIR BREAKDOWN
--------------
"""
        # Per-pair stats
        if len(self.trades_df) > 0:
            for pair in self.trades_df['pair'].unique():
                pair_trades = self.trades_df[self.trades_df['pair'] == pair]
                pair_pnl = pair_trades['pnl'].sum()
                pair_wins = len(pair_trades[pair_trades['pnl'] > 0])
                pair_total = len(pair_trades)
                pair_wr = pair_wins / pair_total if pair_total > 0 else 0
                
                report += f"{pair:12} - Trades: {pair_total:3} | Win Rate: {pair_wr:.1%} | P&L: ${pair_pnl:+.2f}\n"
        
        report += "\n" + "="*70 + "\n"
        
        return report
    
    def export_trades(self, filename: str = 'trades_export.xlsx'):
        """Export trades to Excel"""
        if len(self.trades_df) > 0:
            self.trades_df.to_excel(filename, index=False)
            logger.info(f"Trades exported to {filename}")
        else:
            logger.info("No trades to export")


if __name__ == '__main__':
    # Test tracker
    tracker = PerformanceTracker()
    
    # Example trade
    example_trade = {
        'trade_id': '001',
        'pair': 'SLV-SIVR',
        'direction': 'LONG',
        'entry_time': '2025-12-09 09:35:00',
        'exit_time': '2025-12-13 14:20:00',
        'entry_price': 25.50,
        'exit_price': 25.75,
        'size': 0.01,
        'pnl': 2.50,
        'pnl_pct': 0.98,
        'regime': 'MEAN_REVERTING',
        'entry_zscore': -2.13,
        'exit_zscore': 0.85
    }
    
    tracker.log_trade(example_trade)
    
    print(tracker.generate_report())
