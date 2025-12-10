"""
Live Trading Execution Script

Integrates portfolio manager with Capital.com broker to execute real trades.
This is the production script that runs the complete system.

USAGE:
    python live_trading.py --mode check    # Check signals only (dry run)
    python live_trading.py --mode execute  # Execute trades (REAL MONEY!)
    python live_trading.py --mode monitor  # Monitor existing positions

WARNING: This trades with REAL MONEY. Only run after thorough testing.
"""

import argparse
import logging
from datetime import datetime
import time
from typing import Dict, List
import pandas as pd

from portfolio_manager import MultiPairPortfolio, PairConfig
from capital_com_api import CapitalComAPI, CapitalComAPIError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('live_trading.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class LiveTradingExecutor:
    """
    Live trading executor that connects portfolio manager to broker.
    """
    
    def __init__(self, capital: float = 111.55, dry_run: bool = True):
        """
        Initialize live trading executor.
        
        Args:
            capital: Total trading capital
            dry_run: If True, only simulate trades without executing
        """
        self.capital = capital
        self.dry_run = dry_run
        
        # Initialize portfolio manager
        pairs = [
            PairConfig(symbol1='SLV', symbol2='SIVR', allocation=0.5, max_position_size=0.5),
            PairConfig(symbol1='USO', symbol2='XLE', allocation=0.5, max_position_size=0.5),
        ]
        
        self.portfolio = MultiPairPortfolio(pairs=pairs, total_capital=capital)
        
        # Initialize broker (only if not dry run)
        self.broker = None
        if not dry_run:
            self.broker = CapitalComAPI()
            
        logger.info(f"Initialized LiveTradingExecutor (dry_run={dry_run})")
        
    def connect_broker(self):
        """Connect to broker API"""
        if self.dry_run:
            logger.info("DRY RUN mode - skipping broker connection")
            return True
            
        try:
            logger.info("Connecting to Capital.com...")
            self.broker.authenticate()
            
            # Verify balance
            balance = self.broker.get_account_balance()
            logger.info(f"✓ Connected. Balance: ${balance['balance']:.2f}")
            
            if abs(balance['balance'] - self.capital) > 1.0:
                logger.warning(f"Balance mismatch: Expected ${self.capital}, Got ${balance['balance']}")
                
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to broker: {e}")
            return False
    
    def initialize_portfolio(self):
        """Initialize portfolio manager with current data"""
        logger.info("Initializing portfolio...")
        self.portfolio.initialize_all_pairs()
        logger.info("✓ Portfolio initialized")
    
    def get_current_signals(self) -> pd.DataFrame:
        """
        Get current trading signals for all pairs.
        
        Returns:
            DataFrame with signals and status
        """
        return self.portfolio.get_portfolio_status()
    
    def execute_signal(self, pair_name: str, signal: str, zscore: float, regime: str):
        """
        Execute a trading signal with validation and verification.
        
        Args:
            pair_name: Pair identifier (e.g., 'SLV-SIVR')
            signal: 'LONG', 'SHORT', 'EXIT', or 'HOLD'
            zscore: Current z-score
            regime: Current market regime
        """
        if signal == 'HOLD':
            logger.info(f"{pair_name}: No action (HOLD)")
            return
        
        # Parse pair symbols
        symbol1, symbol2 = pair_name.split('-')
        
        # Get pair configuration for position size
        pair_config = next((p for p in self.portfolio.pairs if f"{p.symbol1}-{p.symbol2}" == pair_name), None)
        position_size = pair_config.max_position_size if pair_config else 0.01
        
        # Get hedge ratio and thresholds
        hedge_ratio = self.portfolio.strategies[pair_name].hedge_ratio
        entry_thresh, exit_thresh = self.portfolio.get_dynamic_thresholds(pair_name)
        
        logger.info(f"\n{'='*70}")
        logger.info(f"SIGNAL: {pair_name} - {signal}")
        logger.info(f"{'='*70}")
        logger.info(f"Z-Score: {zscore:.2f}")
        logger.info(f"Regime: {regime}")
        logger.info(f"Hedge Ratio: {hedge_ratio:.4f}")
        logger.info(f"Thresholds: Entry={entry_thresh:.2f}, Exit={exit_thresh:.2f}")
        
        if self.dry_run:
            logger.info("DRY RUN - Trade NOT executed")
            logger.info(f"Would execute: {signal} on {pair_name}")
            return
        
        # Get current market prices for stop-loss/take-profit
        try:
            # Check API health before proceeding
            if not self.broker.check_api_health():
                logger.error("API health check failed - aborting trade")
                return
            
            market1 = self.broker.get_market_details(symbol1)
            current_price1 = float(market1['snapshot']['bid'])
            
            # Calculate stop-loss and take-profit levels
            if signal == 'LONG':
                # Long spread: Buy symbol1, Short symbol2
                stop_loss = current_price1 - 2  # $2 risk
                take_profit = current_price1 + 5  # $5 profit target
                
                # Validate order parameters before submitting
                valid, error_msg = self.broker.validate_order_parameters(
                    symbol1, 'BUY', position_size, stop_loss, take_profit
                )
                if not valid:
                    logger.error(f"Order validation failed: {error_msg}")
                    return
                
                logger.info(f"\nExecuting LONG spread:")
                logger.info(f"  Buy {symbol1} at ~${current_price1:.2f}")
                logger.info(f"  Short {symbol2}")
                logger.info(f"  Stop Loss: ${stop_loss:.2f}")
                logger.info(f"  Take Profit: ${take_profit:.2f}")
                
                # Execute trades
                result1 = self.broker.create_position(
                    epic=symbol1,
                    direction='BUY',
                    size=position_size,
                    stop_loss=stop_loss,
                    take_profit=take_profit
                )
                
                # Verify first position was created
                deal_ref1 = result1.get('dealReference')
                logger.info(f"✓ Position 1 created: {deal_ref1}")
                
                # Wait briefly for position to register
                import time
                time.sleep(1)
                
                # Short symbol2 with inverse SL/TP logic
                result2 = self.broker.create_position(
                    epic=symbol2,
                    direction='SELL',
                    size=position_size
                )
                
                deal_ref2 = result2.get('dealReference')
                logger.info(f"✓ Position 2 created: {deal_ref2}")
                
                # Verify both positions are open
                self.verify_positions_opened([deal_ref1, deal_ref2])
                
            elif signal == 'SHORT':
                # Short spread: Short symbol1, Buy symbol2
                stop_loss = current_price1 + 2
                take_profit = current_price1 - 5
                
                # Validate order parameters
                valid, error_msg = self.broker.validate_order_parameters(
                    symbol1, 'SELL', position_size, stop_loss, take_profit
                )
                if not valid:
                    logger.error(f"Order validation failed: {error_msg}")
                    return
                
                logger.info(f"\nExecuting SHORT spread:")
                logger.info(f"  Short {symbol1} at ~${current_price1:.2f}")
                logger.info(f"  Buy {symbol2}")
                
                result1 = self.broker.create_position(
                    epic=symbol1,
                    direction='SELL',
                    size=position_size,
                    stop_loss=stop_loss,
                    take_profit=take_profit
                )
                
                deal_ref1 = result1.get('dealReference')
                logger.info(f"✓ Position 1 created: {deal_ref1}")
                
                import time
                time.sleep(1)
                
                result2 = self.broker.create_position(
                    epic=symbol2,
                    direction='BUY',
                    size=position_size
                )
                
                deal_ref2 = result2.get('dealReference')
                logger.info(f"✓ Position 2 created: {deal_ref2}")
                
                # Verify both positions are open
                self.verify_positions_opened([deal_ref1, deal_ref2])
                
            elif signal == 'EXIT':
                logger.info(f"\nClosing {pair_name} positions...")
                
                # Get all open positions
                positions = self.broker.get_positions()
                closed_count = 0
                
                for pos in positions:
                    pos_data = pos['position']
                    pos_epic = pos['market']['epic']
                    
                    if pos_epic in [symbol1, symbol2]:
                        deal_id = pos_data['dealId']
                        logger.info(f"  Closing {pos_epic} position {deal_id}")
                        self.broker.close_position(deal_id)
                        closed_count += 1
                
                logger.info(f"✓ Closed {closed_count} position(s)")
                
        except CapitalComAPIError as e:
            logger.error(f"Failed to execute trade: {e}")
        except Exception as e:
            logger.error(f"Unexpected error executing trade: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def verify_positions_opened(self, deal_references: list):
        """
        Verify that positions were actually opened after order submission.
        
        Args:
            deal_references: List of deal reference IDs to verify
        """
        try:
            import time
            time.sleep(2)  # Wait for positions to register
            
            positions = self.broker.get_positions()
            opened_deals = set()
            
            for pos in positions:
                pos_ref = pos['position'].get('dealReference', '')
                if pos_ref:
                    opened_deals.add(pos_ref)
            
            verified = 0
            for deal_ref in deal_references:
                if deal_ref in opened_deals:
                    logger.info(f"  ✓ Verified position opened: {deal_ref}")
                    verified += 1
                else:
                    logger.warning(f"  ⚠ Position not found: {deal_ref}")
            
            if verified == len(deal_references):
                logger.info(f"✓ All {verified} position(s) verified")
            else:
                logger.warning(f"⚠ Only {verified}/{len(deal_references)} positions verified")
                
        except Exception as e:
            logger.error(f"Failed to verify positions: {e}")
    
    def check_and_execute_signals(self):
        """
        Main trading loop - check signals and execute.
        """
        logger.info("\n" + "="*70)
        logger.info("CHECKING SIGNALS")
        logger.info("="*70)
        
        # Get current signals
        signals_df = self.get_current_signals()
        
        logger.info(f"\n{signals_df.to_string(index=False)}\n")
        
        # Execute each signal
        for _, row in signals_df.iterrows():
            if row['signal'] in ['LONG', 'SHORT', 'EXIT']:
                self.execute_signal(
                    pair_name=row['pair'],
                    signal=row['signal'],
                    zscore=row['zscore'],
                    regime=row['regime']
                )
    
    def monitor_positions(self):
        """Monitor existing positions"""
        if self.dry_run:
            logger.info("DRY RUN - No positions to monitor")
            return
        
        try:
            positions = self.broker.get_positions()
            
            if not positions:
                logger.info("No open positions")
                return
            
            logger.info(f"\n{'='*70}")
            logger.info(f"OPEN POSITIONS ({len(positions)})")
            logger.info(f"{'='*70}\n")
            
            for pos in positions:
                market = pos['market']
                position = pos['position']
                
                logger.info(f"{market['instrumentName']} ({market['epic']})")
                logger.info(f"  Direction: {position['direction']}")
                logger.info(f"  Size: {position['size']}")
                logger.info(f"  Level: {position['level']}")
                logger.info(f"  P&L: ${position.get('profit', 0):.2f}")
                logger.info("")
                
        except Exception as e:
            logger.error(f"Failed to retrieve positions: {e}")
    
    def run(self, mode: str = 'check'):
        """
        Main execution method.
        
        Args:
            mode: 'check', 'execute', or 'monitor'
        """
        logger.info(f"\n{'='*70}")
        logger.info(f"LIVE TRADING BOT - MODE: {mode.upper()}")
        logger.info(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Capital: ${self.capital:.2f}")
        logger.info(f"{'='*70}\n")
        
        # Initialize
        if not self.connect_broker():
            logger.error("Failed to connect to broker - ABORTING")
            return
        
        self.initialize_portfolio()
        
        # Check portfolio risk
        risk = self.portfolio.check_portfolio_risk()
        logger.info(f"\nRisk Metrics:")
        logger.info(f"  Drawdown: {risk['drawdown']:.1%}")
        logger.info(f"  Leverage: {risk['leverage']:.2f}x")
        logger.info(f"  Positions: {risk['num_positions']}\n")
        
        if risk['max_drawdown_breached']:
            logger.error("MAX DRAWDOWN BREACHED - EMERGENCY STOP")
            return
        
        # Execute based on mode
        if mode == 'check':
            logger.info("CHECK MODE - Signals only, no execution\n")
            signals_df = self.get_current_signals()
            print(f"\n{signals_df.to_string(index=False)}\n")
            
        elif mode == 'execute':
            if self.dry_run:
                logger.warning("Cannot execute in dry_run mode!")
                return
            logger.info("EXECUTE MODE - Will place real trades!\n")
            self.check_and_execute_signals()
            
        elif mode == 'monitor':
            logger.info("MONITOR MODE - Checking positions\n")
            self.monitor_positions()
        
        # Cleanup
        if self.broker and not self.dry_run:
            logger.info("\nLogging out...")
            self.broker.logout()
        
        logger.info(f"\n{'='*70}")
        logger.info("SESSION COMPLETE")
        logger.info(f"{'='*70}\n")


def main():
    parser = argparse.ArgumentParser(description='Live Trading Bot')
    parser.add_argument('--mode', choices=['check', 'execute', 'monitor'], 
                       default='check',
                       help='Trading mode: check signals, execute trades, or monitor positions')
    parser.add_argument('--dry-run', action='store_true',
                       help='Dry run mode (no real trades)')
    parser.add_argument('--capital', type=float, default=111.55,
                       help='Total trading capital')
    
    args = parser.parse_args()
    
    # Safety check
    if args.mode == 'execute' and not args.dry_run:
        print("\n" + "="*70)
        print("⚠️  WARNING: LIVE TRADING MODE")
        print("="*70)
        print("This will execute REAL trades with REAL money!")
        print(f"Capital at risk: ${args.capital:.2f}")
        print("")
        confirm = input("Type 'YES' to proceed: ")
        
        if confirm != 'YES':
            print("Aborted.")
            return
    
    # Run executor
    executor = LiveTradingExecutor(
        capital=args.capital,
        dry_run=args.dry_run or args.mode != 'execute'
    )
    
    executor.run(mode=args.mode)


if __name__ == '__main__':
    main()
