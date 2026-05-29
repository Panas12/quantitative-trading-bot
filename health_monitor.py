"""
Real-Time Health Monitor for Trading Bot

Monitors the trading system in real-time and alerts on issues.
Run this alongside your trading bot for continuous health monitoring.

USAGE:
    python health_monitor.py
    
    # Or with custom check interval
    python health_monitor.py --interval 60  # Check every 60 seconds
"""

import os
import sys
import time
import logging
from datetime import datetime
from typing import Dict, List
from dotenv import load_dotenv

from capital_com_api import CapitalComAPI, CapitalComAPIError

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TradingBotHealthMonitor:
    """Real-time health monitoring for the trading bot"""
    
    def __init__(self, check_interval: int = 300):
        """
        Initialize health monitor.
        
        Args:
            check_interval: Seconds between health checks (default: 300 = 5 minutes)
        """
        load_dotenv()
        self.check_interval = check_interval
        self.api = None
        self.last_balance = None
        self.alert_count = 0
        self.consecutive_errors = 0
        
    def connect_api(self) -> bool:
        """Connect to Capital.com API"""
        try:
            self.api = CapitalComAPI()
            self.api.authenticate()
            logger.info("\u2713 API connection established")
            return True
        except Exception as e:
            logger.error(f"\u2717 Failed to connect to API: {e}")
            return False
    
    def check_api_health(self) -> Dict:
        """Check API connection health"""
        status = {
            'healthy': False,
            'message': '',
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            if not self.api or not self.api.cst_token:
                # Try to reconnect
                if not self.connect_api():
                    status['message'] = "API not connected"
                    return status
            
            # Test API with a simple call
            is_healthy = self.api.check_api_health()
            
            if is_healthy:
                status['healthy'] = True
                status['message'] = "API connection healthy"
                self.consecutive_errors = 0
            else:
                status['message'] = "API health check failed"
                self.consecutive_errors += 1
                
        except Exception as e:
            status['message'] = f"API error: {e}"
            self.consecutive_errors += 1
            
        return status
    
    def check_account_status(self) -> Dict:
        """Check account balance and positions"""
        status = {
            'healthy': False,
            'balance': 0,
            'available': 0,
            'positions_count': 0,
            'message': ''
        }
        
        try:
            # Get account balance
            balance = self.api.get_account_balance()
            status['balance'] = balance.get('balance', 0)
            status['available'] = balance.get('available', 0)
            
            # Track balance changes
            if self.last_balance is not None:
                change = status['balance'] - self.last_balance
                change_pct = (change / self.last_balance * 100) if self.last_balance > 0 else 0
                status['balance_change'] = change
                status['balance_change_pct'] = change_pct
                
                # Alert on large losses
                if change_pct < -10:
                    status['message'] = f"\u26a0 Large loss detected: {change_pct:.1f}%"
                    self.alert_count += 1
            
            self.last_balance = status['balance']
            
            # Get positions
            positions = self.api.get_positions()
            status['positions_count'] = len(positions)
            
            # Check for too many positions (potential issue)
            if len(positions) > 6:
                status['message'] = f"\u26a0 Unusual number of positions: {len(positions)}"
                self.alert_count += 1
            
            status['healthy'] = True
            
        except Exception as e:
            status['message'] = f"Failed to get account status: {e}"
            
        return status
    
    def check_risk_limits(self, account_status: Dict) -> Dict:
        """Check if risk limits are being respected"""
        status = {
            'healthy': True,
            'warnings': []
        }
        
        try:
            balance = account_status.get('balance', 0)
            available = account_status.get('available', 0)
            
            if balance <= 0:
                return status  # Skip if no balance data
            
            # Check drawdown
            initial_capital = float(os.getenv('TRADING_CAPITAL', balance))
            current_drawdown = (initial_capital - balance) / initial_capital
            
            max_drawdown_limit = float(os.getenv('RISK_LIMIT_DRAWDOWN', 0.20))
            
            if current_drawdown > max_drawdown_limit:
                status['healthy'] = False
                status['warnings'].append(
                    f"\u26a0 CRITICAL: Drawdown {current_drawdown*100:.1f}% exceeds limit {max_drawdown_limit*100:.1f}%"
                )
                self.alert_count += 1
            elif current_drawdown > max_drawdown_limit * 0.75:
                status['warnings'].append(
                    f"\u26a0 WARNING: Drawdown {current_drawdown*100:.1f}% approaching limit"
                )
            
            # Check available funds
            if available < balance * 0.1:
                status['warnings'].append(
                    f"\u26a0 Low available funds: ${available:.2f} (only {available/balance*100:.1f}% of balance)"
                )
                
        except Exception as e:
            logger.error(f"Error checking risk limits: {e}")
            
        return status
    
    def print_status_report(self, api_health: Dict, account_status: Dict, risk_status: Dict):
        """Print a formatted status report"""
        print("\n" + "="*70)
        print(f"{'TRADING BOT HEALTH MONITOR':^70}")
        print("="*70)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # API Status
        api_icon = "\u2713" if api_health['healthy'] else "\u2717"
        print(f"API Connection:  {api_icon} {api_health['message']}")
        
        # Account Status
        if account_status['healthy']:
            print(f"Account Balance: ${account_status['balance']:.2f}")
            print(f"Available Funds: ${account_status['available']:.2f}")
            print(f"Open Positions:  {account_status['positions_count']}")
            
            if 'balance_change' in account_status:
                change = account_status['balance_change']
                change_pct = account_status['balance_change_pct']
                change_str = f"${abs(change):.2f}"
                change_icon = "\u2191" if change >= 0 else "\u2193"
                print(f"Since Last Check: {change_icon} {change_str} ({change_pct:+.2f}%)")
        else:
            print(f"Account Status:  \u2717 {account_status['message']}")
        
        print()
        
        # Risk Status
        if risk_status['warnings']:
            print("RISK ALERTS:")
            for warning in risk_status['warnings']:
                print(f"  {warning}")
            print()
        
        # Overall Status
        all_healthy = api_health['healthy'] and account_status['healthy'] and risk_status['healthy']
        
        if all_healthy and not risk_status['warnings']:
            print("\u2713 Overall Status: HEALTHY")
        elif risk_status['warnings']:
            print("\u26a0 Overall Status: WARNING - Review alerts above")
        else:
            print("\u2717 Overall Status: UNHEALTHY - Immediate attention needed")
        
        # Error tracking
        if self.consecutive_errors > 0:
            print(f"\u26a0 Consecutive errors: {self.consecutive_errors}")
        
        print("="*70)
    
    def run_health_check(self):
        """Run a single health check cycle"""
        api_health = self.check_api_health()
        
        if api_health['healthy']:
            account_status = self.check_account_status()
            risk_status = self.check_risk_limits(account_status)
        else:
            account_status = {'healthy': False, 'message': 'API unavailable'}
            risk_status = {'healthy': False, 'warnings': ['Cannot check - API offline']}
        
        self.print_status_report(api_health, account_status, risk_status)
        
        # Alert if too many consecutive errors
        if self.consecutive_errors >= 3:
            logger.error(f"\u26a0 CRITICAL: {self.consecutive_errors} consecutive API errors!")
            logger.error("Consider stopping the bot and investigating.")
    
    def run(self):
        """Main monitoring loop"""
        logger.info(f"Starting health monitor (checking every {self.check_interval}s)")
        logger.info("Press Ctrl+C to stop")
        
        # Initial connection
        if not self.connect_api():
            logger.error("Failed to connect to API. Exiting.")
            return
        
        try:
            while True:
                self.run_health_check()
                
                # Wait for next check
                logger.info(f"\nNext check in {self.check_interval} seconds...")
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            logger.info("\n\nHealth monitor stopped by user")
            if self.api:
                self.api.logout()
        except Exception as e:
            logger.error(f"Health monitor error: {e}")
            if self.api:
                self.api.logout()


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Real-time health monitor for trading bot')
    parser.add_argument('--interval', type=int, default=300,
                       help='Seconds between health checks (default: 300)')
    args = parser.parse_args()
    
    monitor = TradingBotHealthMonitor(check_interval=args.interval)
    monitor.run()


if __name__ == '__main__':
    main()
