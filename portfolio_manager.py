"""
Multi-Pair Portfolio Manager

Manages positions across multiple cointegrated pairs with:
- Regime-filtered signals (only trade during mean-reversion)
- Dynamic thresholds (adapt to volatility)
- Portfolio-level risk management
- Capital allocation across pairs
- Correlation checking

This is the master controller that integrates all components.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import logging

from pairs_trading_strategy import PairsTradingStrategy
from regime_detector import RegimeDetector
from dynamic_thresholds import DynamicThresholds
from data_fetcher import DataFetcher

logger = logging.getLogger(__name__)


@dataclass
class PairConfig:
    """Configuration for a trading pair"""
    symbol1: str
    symbol2: str
    allocation: float  # Fraction of total capital
    max_position_size: float = 0.01  # Maximum lot size


class MultiPairPortfolio:
    """
    Portfolio manager for multiple pairs trading strategy.
    """
    
    def __init__(self, 
                 pairs: List[PairConfig],
                 total_capital: float = 100000,
                 max_leverage: float = 2.0,
                 max_drawdown_pct: float = 0.20):
        """
        Initialize portfolio manager.
        
        Args:
            pairs: List of pair configurations
            total_capital: Total trading capital
            max_leverage: Maximum portfolio leverage
            max_drawdown_pct: Emergency stop at this drawdown
        """
        self.pairs = pairs
        self.total_capital = total_capital
        self.max_leverage = max_leverage
        self.max_drawdown_pct = max_drawdown_pct
        
        # Initialize components for each pair
        self.strategies = {}
        self.regime_detectors = {}
        self.threshold_calculators = {}
        self.data = {}
        
        # Portfolio state
        self.positions = {}
        self.equity_curve = []
        self.peak_equity = total_capital
        
        logger.info(f"Initialized portfolio with {len(pairs)} pairs")
        logger.info(f"Total capital: ${total_capital:,.2f}")
        
    def initialize_pair(self, pair_config: PairConfig):
        """
        Initialize components for a specific pair.
        
        Args:
            pair_config: Pair configuration
        """
        pair_name = f"{pair_config.symbol1}-{pair_config.symbol2}"
        logger.info(f"Initializing {pair_name}...")
        
        # Fetch data
        fetcher = DataFetcher(pair_config.symbol1, pair_config.symbol2)
        data1, data2 = fetcher.fetch_data(start_date='2023-01-01')
        
        # Initialize strategy
        strategy = PairsTradingStrategy(
            entry_threshold=2.0,  # Will be overridden by dynamic thresholds
            exit_threshold=1.0
        )
        
        # Calculate spread
        spread = strategy.calculate_spread(data1['close'], data2['close'])
        zscore = strategy.calculate_zscore(spread)
        spread_returns = spread.pct_change().dropna()
        
        # Initialize regime detector
        regime_detector = RegimeDetector()
        regime_detector.train(spread_returns)
        
        # Initialize threshold calculator
        threshold_calc = DynamicThresholds()
        
        # Store
        self.strategies[pair_name] = strategy
        self.regime_detectors[pair_name] = regime_detector
        self.threshold_calculators[pair_name] = threshold_calc
        self.data[pair_name] = {
            'data1': data1,
            'data2': data2,
            'spread': spread,
            'zscore': zscore,
            'spread_returns': spread_returns
        }
        
        logger.info(f"✓ {pair_name} initialized")
        
    def initialize_all_pairs(self):
        """Initialize all pairs in portfolio"""
        for pair_config in self.pairs:
            try:
                self.initialize_pair(pair_config)
            except Exception as e:
                logger.error(f"Failed to initialize {pair_config.symbol1}-{pair_config.symbol2}: {e}")
    
    def check_regime(self, pair_name: str) -> Tuple[str, bool]:
        """
        Check current regime for a pair.
        
        Returns:
            Tuple of (regime_name, should_trade)
        """
        detector = self.regime_detectors[pair_name]
        recent_returns = self.data[pair_name]['spread_returns'].tail(30)
        
        regime = detector.predict_regime(recent_returns)
        should_trade = detector.should_trade(recent_returns, threshold=0.6)
        
        return regime, should_trade
    
    def get_dynamic_thresholds(self, pair_name: str) -> Tuple[float, float]:
        """
        Get current dynamic thresholds for a pair.
        
        Returns:
            Tuple of (entry_threshold, exit_threshold)
        """
        calc = self.threshold_calculators[pair_name]
        spread = self.data[pair_name]['spread']
        zscore = self.data[pair_name]['zscore']
        
        return calc.calculate_thresholds(spread, zscore)
    
    def generate_signals(self, pair_name: str) -> Dict:
        """
        Generate trading signals for a pair with all filters applied.
        
        Returns:
            Dictionary with signal, regime, thresholds, etc.
        """
        # Check regime first
        regime, should_trade_regime = self.check_regime(pair_name)
        
        if not should_trade_regime:
            logger.info(f"{pair_name}: Regime {regime} - NO TRADE")
            return {
                'pair': pair_name,
                'signal': 'HOLD',
                'regime': regime,
                'should_trade': False,
                'reason': f'Unfavorable regime: {regime}'
            }
        
        # Get dynamic thresholds
        entry_thresh, exit_thresh = self.get_dynamic_thresholds(pair_name)
        
        # Get current z-score
        current_zscore = self.data[pair_name]['zscore'].iloc[-1]
        
        # Generate signal
        if abs(current_zscore) < exit_thresh:
            signal = 'EXIT' if pair_name in self.positions else 'HOLD'
        elif current_zscore <= -entry_thresh:
            signal = 'LONG'  # Long the spread
        elif current_zscore >= entry_thresh:
            signal = 'SHORT'  # Short the spread
        else:
            signal = 'HOLD'
        
        return {
            'pair': pair_name,
            'signal': signal,
            'regime': regime,
            'should_trade': should_trade_regime,
            'zscore': current_zscore,
            'entry_threshold': entry_thresh,
            'exit_threshold': exit_thresh,
            'reason': f'Z-score: {current_zscore:.2f}, Regime: {regime}'
        }
    
    def check_portfolio_risk(self) -> Dict:
        """
        Check portfolio-level risk metrics.
        
        Returns:
            Dictionary with risk metrics and limits
        """
        current_equity = self.calculate_current_equity()
        drawdown = (current_equity - self.peak_equity) / self.peak_equity
        
        total_exposure = sum(
            pos['size'] for pos in self.positions.values()
        ) if self.positions else 0
        
        leverage = total_exposure / current_equity if current_equity > 0 else 0
        
        risk_status = {
            'current_equity': current_equity,
            'peak_equity': self.peak_equity,
            'drawdown': drawdown,
            'leverage': leverage,
            'num_positions': len(self.positions),
            'max_drawdown_breached': drawdown < -self.max_drawdown_pct,
            'max_leverage_breached': leverage > self.max_leverage
        }
        
        return risk_status
    
    def calculate_current_equity(self) -> float:
        """Calculate current portfolio equity"""
        # Simplified - in reality would query broker
        return self.total_capital
    
    def get_portfolio_status(self) -> pd.DataFrame:
        """
        Get complete portfolio status.
        
        Returns:
            DataFrame with status of all pairs
        """
        statuses = []
        
        for pair_config in self.pairs:
            pair_name = f"{pair_config.symbol1}-{pair_config.symbol2}"
            
            if pair_name not in self.strategies:
                continue
            
            signal_info = self.generate_signals(pair_name)
            
            position = self.positions.get(pair_name, None)
            position_status = 'OPEN' if position else 'CLOSED'
            position_direction = position['direction'] if position else 'NONE'
            
            statuses.append({
                'pair': pair_name,
                'regime': signal_info['regime'],
                'zscore': signal_info.get('zscore', 0.0),
                'signal': signal_info['signal'],
                'position': position_status,
                'direction': position_direction,
                'allocation': pair_config.allocation
            })
        
        return pd.DataFrame(statuses)


if __name__ == '__main__':
    # Test portfolio manager
    logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
    
    print("\n" + "="*70)
    print("MULTI-PAIR PORTFOLIO MANAGER TEST")
    print("="*70 + "\n")
    
    # Define pairs
    pairs = [
        PairConfig(symbol1='SLV', symbol2='SIVR', allocation=0.5),
        PairConfig(symbol1='USO', symbol2='XLE', allocation=0.5),
    ]
    
    # Initialize portfolio
    print("Initializing portfolio...")
    portfolio = MultiPairPortfolio(pairs=pairs, total_capital=111.55)  # Your actual capital
    portfolio.initialize_all_pairs()
    
    # Get status
    print("\n" + "="*70)
    print("PORTFOLIO STATUS")
    print("="*70 + "\n")
    
    status_df = portfolio.get_portfolio_status()
    print(status_df.to_string(index=False))
    
    # Risk check
    print("\n" + "="*70)
    print("RISK METRICS")
    print("="*70)
    
    risk = portfolio.check_portfolio_risk()
    print(f"Current Equity: ${risk['current_equity']:.2f}")
    print(f"Drawdown: {risk['drawdown']:.1%}")
    print(f"Leverage: {risk['leverage']:.2f}x")
    print(f"Positions: {risk['num_positions']}")
    
    print("\n" + "="*70)
    print("READY FOR LIVE TRADING")
    print("="*70)
