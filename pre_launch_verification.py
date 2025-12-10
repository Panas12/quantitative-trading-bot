"""
Pre-Launch Verification Script for Trading Bot

Comprehensive system check to ensure all components are ready for live trading.
Run this script BEFORE going live to catch configuration issues, API problems,
and other potential failures.

USAGE:
    python pre_launch_verification.py
    
    # Or with specific checks
    python pre_launch_verification.py --skip-email  # Skip email tests
    python pre_launch_verification.py --demo        # Test with demo account
"""

import os
import sys
import logging
from datetime import datetime
from typing import Dict, List, Tuple
from dotenv import load_dotenv

# Fix Windows console encoding for Unicode characters
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Import trading components
from capital_com_api import CapitalComAPI, CapitalComAPIError
from portfolio_manager import MultiPairPortfolio, PairConfig
from data_fetcher import DataFetcher
import smtplib
from email.mime.text import MIMEText

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'  # Simple format for verification output
)
logger = logging.getLogger(__name__)


class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


class VerificationResult:
    """Result of a verification check"""
    def __init__(self, passed: bool, message: str, details: str = ""):
        self.passed = passed
        self.message = message
        self.details = details


class PreLaunchVerifier:
    """Comprehensive pre-launch verification system"""
    
    def __init__(self, skip_email: bool = False):
        """
        Initialize verifier.
        
        Args:
            skip_email: Skip email alert tests
        """
        load_dotenv()
        self.skip_email = skip_email
        self.results: List[VerificationResult] = []
        self.errors: List[str] = []
        self.warnings: List[str] = []
        
    def print_header(self, text: str):
        """Print section header"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}{text:^70}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}\n")
    
    def print_check(self, name: str, passed: bool, details: str = ""):
        """Print check result"""
        icon = f"{Colors.GREEN}✓{Colors.RESET}" if passed else f"{Colors.RED}✗{Colors.RESET}"
        print(f"{icon} {name}")
        if details:
            print(f"  {Colors.YELLOW}→{Colors.RESET} {details}")
    
    def verify_environment(self) -> bool:
        """Verify all required environment variables are set"""
        self.print_header("ENVIRONMENT CONFIGURATION")
        
        required_vars = {
            'CAPITAL_API_KEY': 'Capital.com API key',
            'CAPITAL_API_PASSWORD': 'Capital.com API password',
            'CAPITAL_EMAIL': 'Capital.com account email',
            'CAPITAL_ENVIRONMENT': 'Environment (LIVE or DEMO)',
            'TRADING_CAPITAL': 'Trading capital amount',
            'DRY_RUN': 'Dry run mode setting'
        }
        
        all_good = True
        
        for var, description in required_vars.items():
            value = os.getenv(var)
            if not value:
                self.print_check(description, False, f"{var} not set")
                self.errors.append(f"Missing environment variable: {var}")
                all_good = False
            else:
                # Mask sensitive values
                if 'PASSWORD' in var or 'KEY' in var:
                    display_value = value[:4] + "..." + value[-4:] if len(value) > 8 else "***"
                else:
                    display_value = value
                self.print_check(description, True, f"{display_value}")
        
        # Validate specific values
        env = os.getenv('CAPITAL_ENVIRONMENT', '').upper()
        if env not in ['LIVE', 'DEMO']:
            self.print_check("Valid environment setting", False, f"Must be LIVE or DEMO, got: {env}")
            self.errors.append("Invalid CAPITAL_ENVIRONMENT")
            all_good = False
        else:
            if env == 'LIVE':
                self.warnings.append("⚠️  Running in LIVE mode - real money at risk!")
        
        try:
            capital = float(os.getenv('TRADING_CAPITAL', 0))
            if capital <= 0:
                self.print_check("Valid trading capital", False, f"Must be > 0, got: {capital}")
                self.errors.append("Invalid TRADING_CAPITAL")
                all_good = False
            else:
                self.print_check("Valid trading capital", True, f"${capital:.2f}")
        except ValueError:
            self.print_check("Valid trading capital", False, "Not a valid number")
            self.errors.append("TRADING_CAPITAL is not a number")
            all_good = False
        
        # Check DRY_RUN setting
        dry_run = os.getenv('DRY_RUN', 'True').lower()
        if dry_run == 'false' and env == 'LIVE':
            self.warnings.append("⚠️  DRY_RUN is disabled with LIVE account - will execute real trades!")
        
        return all_good
    
    def verify_api_connection(self) -> bool:
        """Test Capital.com API connection"""
        self.print_header("API CONNECTION")
        
        try:
            # Initialize API
            self.print_check("Initializing API client", True)
            api = CapitalComAPI()
            
            # Test authentication
            print(f"\n  {Colors.YELLOW}Testing authentication...{Colors.RESET}")
            api.authenticate()
            self.print_check("Authentication", True, "Session tokens obtained")
            
            # Get account info
            accounts = api.get_accounts()
            if accounts:
                acc = accounts[0]
                self.print_check("Account access", True, f"Account ID: {acc.get('accountId')}")
            
            # Get balance
            balance = api.get_account_balance()
            bal_amount = balance.get('balance', 0)
            avail_amount = balance.get('available', 0)
            self.print_check("Balance retrieval", True, 
                           f"Balance: ${bal_amount:.2f}, Available: ${avail_amount:.2f}")
            
            # Check if balance matches configured capital
            expected_capital = float(os.getenv('TRADING_CAPITAL', 0))
            if abs(bal_amount - expected_capital) > 5.0:
                self.warnings.append(
                    f"Balance mismatch: Configured ${expected_capital:.2f} but account has ${bal_amount:.2f}"
                )
            
            # Logout
            api.logout()
            self.print_check("Session cleanup", True, "Logged out")
            
            return True
            
        except CapitalComAPIError as e:
            self.print_check("API connection", False, str(e))
            self.errors.append(f"API connection failed: {e}")
            return False
        except Exception as e:
            self.print_check("API connection", False, f"Unexpected error: {e}")
            self.errors.append(f"API error: {e}")
            return False
    
    def verify_market_data(self) -> bool:
        """Test market data retrieval for configured pairs"""
        self.print_header("MARKET DATA ACCESS")
        
        # Default pairs from portfolio
        pairs = [
            ('SLV', 'SIVR'),
            ('USO', 'XLE')
        ]
        
        all_good = True
        
        try:
            fetcher = DataFetcher()
            
            for symbol1, symbol2 in pairs:
                print(f"\n  {Colors.YELLOW}Testing {symbol1}-{symbol2}...{Colors.RESET}")
                
                try:
                    # Fetch data
                    data1 = fetcher.fetch_data(symbol1, '2024-01-01', '2024-12-31')
                    data2 = fetcher.fetch_data(symbol2, '2024-01-01', '2024-12-31')
                    
                    if data1 is not None and data2 is not None and len(data1) > 0 and len(data2) > 0:
                        self.print_check(f"{symbol1} data", True, f"{len(data1)} bars")
                        self.print_check(f"{symbol2} data", True, f"{len(data2)} bars")
                        
                        # Check for missing data
                        if len(data1) < 200 or len(data2) < 200:
                            self.warnings.append(f"Limited data for {symbol1}-{symbol2} (less than 200 bars)")
                    else:
                        self.print_check(f"{symbol1}-{symbol2} data", False, "No data retrieved")
                        all_good = False
                        
                except Exception as e:
                    self.print_check(f"{symbol1}-{symbol2} data", False, str(e))
                    self.errors.append(f"Failed to fetch data for {symbol1}-{symbol2}: {e}")
                    all_good = False
            
            return all_good
            
        except Exception as e:
            self.print_check("Market data access", False, str(e))
            self.errors.append(f"Market data error: {e}")
            return False
    
    def verify_portfolio_initialization(self) -> bool:
        """Test portfolio manager initialization"""
        self.print_header("PORTFOLIO MANAGER")
        
        try:
            capital = float(os.getenv('TRADING_CAPITAL', 111.55))
            
            # Create portfolio
            pairs = [
                PairConfig('SLV', 'SIVR', allocation=0.5, max_position_size=0.01),
                PairConfig('USO', 'XLE', allocation=0.5, max_position_size=0.01)
            ]
            
            self.print_check("Portfolio configuration", True, f"{len(pairs)} pairs")
            
            portfolio = MultiPairPortfolio(pairs, total_capital=capital)
            self.print_check("Portfolio creation", True)
            
            # Initialize with data
            print(f"\n  {Colors.YELLOW}Initializing pairs...{Colors.RESET}")
            portfolio.initialize_all_pairs()
            self.print_check("Pair initialization", True, "All pairs ready")
            
            # Check signals
            for pair_config in pairs:
                pair_name = f"{pair_config.symbol1}-{pair_config.symbol2}"
                if pair_name in portfolio.strategies:
                    strategy = portfolio.strategies[pair_name]
                    hedge_ratio = strategy.hedge_ratio
                    self.print_check(f"{pair_name} strategy", True, 
                                   f"Hedge ratio: {hedge_ratio:.4f}")
                else:
                    self.print_check(f"{pair_name} strategy", False, "Not initialized")
                    return False
            
            return True
            
        except Exception as e:
            self.print_check("Portfolio initialization", False, str(e))
            self.errors.append(f"Portfolio error: {e}")
            return False
    
    def verify_email_system(self) -> bool:
        """Test email alert system"""
        if self.skip_email:
            self.print_header("EMAIL ALERTS (SKIPPED)")
            print("  Email tests skipped by user request")
            return True
        
        self.print_header("EMAIL ALERTS")
        
        email_enabled = os.getenv('EMAIL_ALERTS', 'False').lower() == 'true'
        
        if not email_enabled:
            print("  Email alerts disabled in configuration")
            return True
        
        required_vars = ['SMTP_SERVER', 'SMTP_PORT', 'SENDER_EMAIL', 'SENDER_PASSWORD', 'RECIPIENT_EMAIL']
        missing = [v for v in required_vars if not os.getenv(v)]
        
        if missing:
            self.print_check("Email configuration", False, f"Missing: {', '.join(missing)}")
            self.warnings.append("Email alerts enabled but configuration incomplete")
            return True  # Not critical
        
        try:
            # Test SMTP connection
            smtp_server = os.getenv('SMTP_SERVER')
            smtp_port = int(os.getenv('SMTP_PORT', 587))
            sender = os.getenv('SENDER_EMAIL')
            password = os.getenv('SENDER_PASSWORD')
            recipient = os.getenv('RECIPIENT_EMAIL')
            
            self.print_check("SMTP configuration", True)
            
            print(f"\n  {Colors.YELLOW}Testing SMTP connection...{Colors.RESET}")
            
            server = smtplib.SMTP(smtp_server, smtp_port, timeout=10)
            server.starttls()
            server.login(sender, password)
            
            self.print_check("SMTP connection", True, f"{smtp_server}:{smtp_port}")
            
            # Send test email
            msg = MIMEText(f"Test email from trading bot verification\nTimestamp: {datetime.now()}")
            msg['Subject'] = '🤖 Trading Bot - Verification Test'
            msg['From'] = sender
            msg['To'] = recipient
            
            server.send_message(msg)
            server.quit()
            
            self.print_check("Test email sent", True, f"Sent to {recipient}")
            print(f"\n  {Colors.YELLOW}→ Please check your email to confirm delivery{Colors.RESET}")
            
            return True
            
        except Exception as e:
            self.print_check("Email system", False, str(e))
            self.warnings.append(f"Email system error: {e}")
            return True  # Not critical
    
    def verify_risk_limits(self) -> bool:
        """Verify risk management settings"""
        self.print_header("RISK MANAGEMENT")
        
        all_good = True
        
        # Check drawdown limit
        drawdown_limit = float(os.getenv('RISK_LIMIT_DRAWDOWN', 0.20))
        if 0 < drawdown_limit <= 0.5:
            self.print_check("Drawdown limit", True, f"{drawdown_limit*100:.0f}%")
        else:
            self.print_check("Drawdown limit", False, f"{drawdown_limit*100:.0f}% (should be 0-50%)")
            self.warnings.append(f"Drawdown limit seems unusual: {drawdown_limit*100}%")
        
        # Check leverage limit
        leverage_limit = float(os.getenv('RISK_LIMIT_LEVERAGE', 2.0))
        if 1 <= leverage_limit <= 5:
            self.print_check("Leverage limit", True, f"{leverage_limit:.1f}x")
        else:
            self.print_check("Leverage limit", False, f"{leverage_limit:.1f}x (should be 1-5x)")
            self.warnings.append(f"Leverage limit seems unusual: {leverage_limit}x")
            all_good = False
        
        # Check position sizes
        capital = float(os.getenv('TRADING_CAPITAL', 111.55))
        position_size = 0.01  # Default from portfolio config
        estimated_exposure = position_size * 2600 * 2  # Rough estimate for gold pair
        
        self.print_check("Position sizing", True, 
                       f"Size: {position_size} lots, Est. exposure: ${estimated_exposure:.0f}")
        
        if estimated_exposure > capital * 2:
            self.warnings.append(
                f"Position size may be too large relative to capital (${estimated_exposure:.0f} vs ${capital:.0f})"
            )
        
        return all_good
    
    def run_all_checks(self) -> bool:
        """Run all verification checks"""
        print(f"\n{Colors.BOLD}{'='*70}{Colors.RESET}")
        print(f"{Colors.BOLD}{'TRADING BOT PRE-LAUNCH VERIFICATION':^70}{Colors.RESET}")
        print(f"{Colors.BOLD}{'='*70}{Colors.RESET}")
        print(f"\n{Colors.YELLOW}Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.RESET}")
        
        checks = [
            ("Environment Configuration", self.verify_environment),
            ("API Connection", self.verify_api_connection),
            ("Market Data Access", self.verify_market_data),
            ("Portfolio Initialization", self.verify_portfolio_initialization),
            ("Risk Management", self.verify_risk_limits),
            ("Email System", self.verify_email_system),
        ]
        
        results = {}
        for name, check_func in checks:
            try:
                results[name] = check_func()
            except Exception as e:
                results[name] = False
                self.errors.append(f"{name} check crashed: {e}")
                logger.error(f"Check failed: {name} - {e}")
        
        # Print summary
        self.print_header("VERIFICATION SUMMARY")
        
        passed = sum(1 for v in results.values() if v)
        total = len(results)
        
        for check_name, result in results.items():
            self.print_check(check_name, result)
        
        print(f"\n{Colors.BOLD}Results: {passed}/{total} checks passed{Colors.RESET}")
        
        # Print warnings
        if self.warnings:
            print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠️  WARNINGS:{Colors.RESET}")
            for warning in self.warnings:
                print(f"  {Colors.YELLOW}•{Colors.RESET} {warning}")
        
        # Print errors
        if self.errors:
            print(f"\n{Colors.RED}{Colors.BOLD}❌ ERRORS:{Colors.RESET}")
            for error in self.errors:
                print(f"  {Colors.RED}•{Colors.RESET} {error}")
        
        # Final verdict
        print(f"\n{'='*70}")
        all_passed = all(results.values())
        
        if all_passed and not self.errors:
            print(f"{Colors.GREEN}{Colors.BOLD}✓ SYSTEM READY FOR TRADING{Colors.RESET}")
            print(f"\nYou can proceed with:")
            print(f"  • DRY RUN: python live_trading.py --mode check --dry-run")
            print(f"  • LIVE: python live_trading.py --mode execute")
        elif not self.errors:
            print(f"{Colors.YELLOW}{Colors.BOLD}⚠️  SYSTEM READY WITH WARNINGS{Colors.RESET}")
            print(f"\nReview warnings above before proceeding")
        else:
            print(f"{Colors.RED}{Colors.BOLD}❌ SYSTEM NOT READY{Colors.RESET}")
            print(f"\nFix the errors above before proceeding")
        
        print(f"{'='*70}\n")
        
        return all_passed and not self.errors


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Pre-launch verification for trading bot')
    parser.add_argument('--skip-email', action='store_true', help='Skip email alert tests')
    args = parser.parse_args()
    
    verifier = PreLaunchVerifier(skip_email=args.skip_email)
    success = verifier.run_all_checks()
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
