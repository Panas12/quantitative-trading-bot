"""
Capital.com API Connector for Automated Trading

This module provides a Python interface to the Capital.com REST API,
enabling automated trading, market data retrieval, and account management.

Official API Documentation: https://open-api.capital.com/

Created: December 2025
"""

import os
import logging
import time
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import requests
from dotenv import load_dotenv
from functools import wraps

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CapitalComAPIError(Exception):
    """Custom exception for Capital.com API errors"""
    pass


class CapitalComAPI:
    """
    Capital.com API connector for automated trading.
    
    Features:
    - Session authentication and management
    - Market data retrieval (historical prices, real-time quotes)
    - Order execution (market orders, limit orders)
    - Position management (open, modify, close)
    - Account information and balance tracking
    
    Usage:
        api = CapitalComAPI()
        api.authenticate()
        balance = api.get_account_balance()
        prices = api.get_historical_prices('GOLD', 'HOUR', max_points=100)
    """
    
    def __init__(self, environment: str = None):
        """
        Initialize Capital.com API connector.
        
        Args:
            environment: 'DEMO' or 'LIVE'. If None, reads from .env file
        """
        # Load credentials from environment
        self.api_key = os.getenv('CAPITAL_API_KEY')
        self.api_password = os.getenv('CAPITAL_API_PASSWORD')
        self.identifier = os.getenv('CAPITAL_EMAIL')  # Login email
        
        if not self.api_key or not self.api_password or not self.identifier:
            raise CapitalComAPIError(
                "API credentials not found. Ensure CAPITAL_API_KEY, CAPITAL_API_PASSWORD, "
                "and CAPITAL_EMAIL are set in your .env file."
            )
        
        # Set environment (demo vs live)
        env = environment or os.getenv('CAPITAL_ENVIRONMENT', 'DEMO')
        self.environment = env.upper()
        
        if self.environment == 'DEMO':
            self.base_url = os.getenv('CAPITAL_DEMO_URL', 
                                     'https://demo-api-capital.backend-capital.com')
        else:
            self.base_url = os.getenv('CAPITAL_LIVE_URL', 
                                     'https://api-capital.backend-capital.com')
        
        logger.info(f"Initialized Capital.com API in {self.environment} mode")
        logger.info(f"Base URL: {self.base_url}")
        
        # Session tokens (set after authentication)
        self.cst_token = None
        self.x_security_token = None
        self.session = None
        self.account_id = None
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 0.1  # 100ms between requests (10 req/sec)
        
        # Retry configuration
        self.max_retries = 3
        self.retry_delay = 1.0  # Initial retry delay in seconds
        
    def _wait_for_rate_limit(self):
        """Ensure we don't exceed rate limits (10 req/sec)"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()
    
    def _is_transient_error(self, status_code: int, error_msg: str = "") -> bool:
        """
        Determine if an error is transient and worth retrying.
        
        Args:
            status_code: HTTP status code
            error_msg: Error message if available
        
        Returns:
            True if error is likely transient
        """
        # Network/server errors that are worth retrying
        transient_codes = {
            408,  # Request Timeout
            429,  # Too Many Requests
            500,  # Internal Server Error
            502,  # Bad Gateway
            503,  # Service Unavailable
            504,  # Gateway Timeout
        }
        return status_code in transient_codes
    
    def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        headers: Dict = None,
        params: Dict = None,
        data: Dict = None,
        use_auth: bool = True,
        retry: bool = True
    ) -> requests.Response:
        """
        Make HTTP request to Capital.com API with rate limiting and retry logic.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (e.g., '/api/v1/session')
            headers: Additional headers
            params: Query parameters
            data: Request body (JSON)
            use_auth: Whether to include authentication tokens
            retry: Whether to retry on transient errors
        
        Returns:
            Response object
        """
        attempt = 0
        last_exception = None
        
        while attempt < (self.max_retries if retry else 1):
            try:
                self._wait_for_rate_limit()
                
                url = f"{self.base_url}{endpoint}"
                
                # Build headers
                req_headers = {
                    'Content-Type': 'application/json',
                    'X-CAP-API-KEY': self.api_key
                }
                
                # Add authentication tokens if available and requested
                if use_auth and self.cst_token and self.x_security_token:
                    req_headers['CST'] = self.cst_token
                    req_headers['X-SECURITY-TOKEN'] = self.x_security_token
                
                # Merge additional headers
                if headers:
                    req_headers.update(headers)
                
                # Log request (without sensitive data)
                logger.debug(f"{method} {endpoint} (attempt {attempt + 1})")
                
                response = requests.request(
                    method=method,
                    url=url,
                    headers=req_headers,
                    params=params,
                    json=data,
                    timeout=30
                )
                
                # Log response status
                logger.debug(f"Response: {response.status_code}")
                
                # Check if we should retry on this status code
                if retry and self._is_transient_error(response.status_code):
                    attempt += 1
                    if attempt < self.max_retries:
                        delay = self.retry_delay * (2 ** (attempt - 1))  # Exponential backoff
                        logger.warning(f"Transient error {response.status_code}, retrying in {delay}s...")
                        time.sleep(delay)
                        continue
                
                return response
                
            except requests.exceptions.Timeout as e:
                attempt += 1
                last_exception = e
                if attempt < self.max_retries and retry:
                    delay = self.retry_delay * (2 ** (attempt - 1))
                    logger.warning(f"Request timeout, retrying in {delay}s...")
                    time.sleep(delay)
                else:
                    logger.error(f"Request failed after {attempt} attempts: {e}")
                    raise CapitalComAPIError(f"API request timeout: {e}")
                    
            except requests.exceptions.ConnectionError as e:
                attempt += 1
                last_exception = e
                if attempt < self.max_retries and retry:
                    delay = self.retry_delay * (2 ** (attempt - 1))
                    logger.warning(f"Connection error, retrying in {delay}s...")
                    time.sleep(delay)
                else:
                    logger.error(f"Connection failed after {attempt} attempts: {e}")
                    raise CapitalComAPIError(f"API connection failed: {e}")
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed: {e}")
                raise CapitalComAPIError(f"API request failed: {e}")
        
        # If we've exhausted all retries
        if last_exception:
            raise CapitalComAPIError(f"Request failed after {self.max_retries} retries: {last_exception}")
    
    def authenticate(self) -> bool:
        """
        Authenticate with Capital.com API and obtain session tokens.
        
        Sessions are valid for 10 minutes of inactivity. This method uses
        the simpler plain-text password authentication method.
        
        Returns:
            True if authentication successful
        
        Raises:
            CapitalComAPIError: If authentication fails
        """
        logger.info("Authenticating with Capital.com API...")
        
        endpoint = '/api/v1/session'
        
        # Identifier is your Capital.com login email, NOT the API key
        auth_data = {
            'identifier': self.identifier,  # This is your email
            'password': self.api_password,  # This is the custom API password
            'encryptedPassword': False
        }
        
        try:
            response = self._make_request(
                'POST', 
                endpoint, 
                data=auth_data,
                use_auth=False  # Don't use auth for login
            )
            
            if response.status_code == 200:
                # Extract session tokens from headers
                self.cst_token = response.headers.get('CST')
                self.x_security_token = response.headers.get('X-SECURITY-TOKEN')
                
                if not self.cst_token or not self.x_security_token:
                    raise CapitalComAPIError("Authentication succeeded but tokens not found in response")
                
                # Get session details
                session_data = response.json()
                self.account_id = session_data.get('currentAccountId')
                
                logger.info("✓ Authentication successful")
                logger.info(f"Account ID: {self.account_id}")
                
                return True
            else:
                error_msg = response.json().get('errorCode', 'Unknown error')
                raise CapitalComAPIError(
                    f"Authentication failed: {response.status_code} - {error_msg}"
                )
                
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            raise
    
    def get_accounts(self) -> List[Dict]:
        """
        Get list of all trading accounts.
        
        Returns:
            List of account dictionaries with details
        """
        if not self.cst_token:
            raise CapitalComAPIError("Not authenticated. Call authenticate() first.")
        
        response = self._make_request('GET', '/api/v1/accounts')
        
        if response.status_code == 200:
            accounts = response.json().get('accounts', [])
            logger.info(f"Retrieved {len(accounts)} account(s)")
            return accounts
        else:
            raise CapitalComAPIError(f"Failed to get accounts: {response.status_code}")
    
    def get_account_balance(self) -> Dict:
        """
        Get current account balance and equity.
        
        Returns:
            Dictionary with balance, available funds, P&L, etc.
        """
        if not self.cst_token:
            raise CapitalComAPIError("Not authenticated. Call authenticate() first.")
        
        accounts = self.get_accounts()
        
        if not accounts:
            raise CapitalComAPIError("No accounts found")
        
        # Get the current account (first one or match account_id)
        account = accounts[0]
        
        balance_info = {
            'account_id': account.get('accountId'),
            'account_name': account.get('accountName'),
            'balance': account.get('balance', {}).get('balance', 0),
            'deposit': account.get('balance', {}).get('deposit', 0),
            'profit_loss': account.get('balance', {}).get('profitLoss', 0),
            'available': account.get('balance', {}).get('available', 0),
            'currency': account.get('currency', 'USD')
        }
        
        logger.info(f"Balance: {balance_info['balance']} {balance_info['currency']}")
        logger.info(f"Available: {balance_info['available']} {balance_info['currency']}")
        
        return balance_info
    
    def get_historical_prices(
        self, 
        epic: str, 
        resolution: str = 'HOUR',
        max_points: int = 100,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None
    ) -> List[Dict]:
        """
        Get historical price data for an instrument.
        
        Args:
            epic: Instrument identifier (e.g., 'GOLD', 'US500', 'EURUSD')
            resolution: Price resolution - MINUTE, MINUTE_5, MINUTE_15, MINUTE_30,
                       HOUR, HOUR_4, DAY, WEEK
            max_points: Maximum number of data points (default 100, max 1000)
            from_date: Start date in format 'YYYY-MM-DDTHH:MM:SS'
            to_date: End date in format 'YYYY-MM-DDTHH:MM:SS'
        
        Returns:
            List of price dictionaries with OHLC data
        """
        if not self.cst_token:
            raise CapitalComAPIError("Not authenticated. Call authenticate() first.")
        
        endpoint = f'/api/v1/prices/{epic}'
        
        params = {
            'resolution': resolution,
            'max': min(max_points, 1000)  # Cap at API limit
        }
        
        if from_date:
            params['from'] = from_date
        if to_date:
            params['to'] = to_date
        
        response = self._make_request('GET', endpoint, params=params)
        
        if response.status_code == 200:
            data = response.json()
            prices = data.get('prices', [])
            logger.info(f"Retrieved {len(prices)} price bars for {epic}")
            return prices
        else:
            raise CapitalComAPIError(
                f"Failed to get prices for {epic}: {response.status_code}"
            )
    
    def get_market_details(self, epic: str) -> Dict:
        """
        Get detailed information about a specific market.
        
        Args:
            epic: Instrument identifier
        
        Returns:
            Dictionary with market details, trading hours, margins, etc.
        """
        if not self.cst_token:
            raise CapitalComAPIError("Not authenticated. Call authenticate() first.")
        
        endpoint = f'/api/v1/markets/{epic}'
        response = self._make_request('GET', endpoint)
        
        if response.status_code == 200:
            market_data = response.json()
            logger.info(f"Retrieved market details for {epic}")
            return market_data
        else:
            raise CapitalComAPIError(
                f"Failed to get market details: {response.status_code}"
            )
    
    def get_positions(self) -> List[Dict]:
        """
        Get all open positions.
        
        Returns:
            List of position dictionaries
        """
        if not self.cst_token:
            raise CapitalComAPIError("Not authenticated. Call authenticate() first.")
        
        response = self._make_request('GET', '/api/v1/positions')
        
        if response.status_code == 200:
            positions = response.json().get('positions', [])
            logger.info(f"Retrieved {len(positions)} open position(s)")
            return positions
        else:
            raise CapitalComAPIError(
                f"Failed to get positions: {response.status_code}"
            )
    
    def create_position(
        self,
        epic: str,
        direction: str,
        size: float,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        guaranteed_stop: bool = False
    ) -> Dict:
        """
        Create a new market position.
        
        Args:
            epic: Instrument identifier
            direction: 'BUY' or 'SELL'
            size: Position size in lots/units
            stop_loss: Stop loss level (price)
            take_profit: Take profit level (price)
            guaranteed_stop: Use guaranteed stop loss (may have premium)
        
        Returns:
            Dictionary with deal reference and status
        """
        if not self.cst_token:
            raise CapitalComAPIError("Not authenticated. Call authenticate() first.")
        
        # Validate direction
        direction = direction.upper()
        if direction not in ['BUY', 'SELL']:
            raise ValueError("direction must be 'BUY' or 'SELL'")
        
        # Build position request
        position_data = {
            'epic': epic,
            'direction': direction,
            'size': size,
            'guaranteedStop': guaranteed_stop
        }
        
        # Add stop loss if provided
        if stop_loss:
            position_data['stopLevel'] = stop_loss
        
        # Add take profit if provided
        if take_profit:
            position_data['profitLevel'] = take_profit
        
        logger.info(f"Creating {direction} position: {epic} size={size}")
        
        response = self._make_request('POST', '/api/v1/positions', data=position_data)
        
        if response.status_code == 200:
            result = response.json()
            deal_reference = result.get('dealReference')
            logger.info(f"✓ Position created: {deal_reference}")
            return result
        else:
            error = response.json() if response.text else {}
            raise CapitalComAPIError(
                f"Failed to create position: {response.status_code} - {error}"
            )
    
    def close_position(self, deal_id: str) -> Dict:
        """
        Close an existing position.
        
        Args:
            deal_id: Deal ID of the position to close
        
        Returns:
            Dictionary with deal reference
        """
        if not self.cst_token:
            raise CapitalComAPIError("Not authenticated. Call authenticate() first.")
        
        endpoint = f'/api/v1/positions/{deal_id}'
        
        logger.info(f"Closing position: {deal_id}")
        
        response = self._make_request('DELETE', endpoint)
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"✓ Position closed: {deal_id}")
            return result
        else:
            raise CapitalComAPIError(
                f"Failed to close position: {response.status_code}"
            )
    
    def update_position(
        self,
        deal_id: str,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None
    ) -> Dict:
        """
        Update stop loss and/or take profit for an existing position.
        
        Args:
            deal_id: Deal ID of position to update
            stop_loss: New stop loss level
            take_profit: New take profit level
        
        Returns:
            Dictionary with deal reference
        """
        if not self.cst_token:
            raise CapitalComAPIError("Not authenticated. Call authenticate() first.")
        
        endpoint = f'/api/v1/positions/{deal_id}'
        
        update_data = {}
        if stop_loss is not None:
            update_data['stopLevel'] = stop_loss
        if take_profit is not None:
            update_data['profitLevel'] = take_profit
        
        if not update_data:
            raise ValueError("Must provide at least stop_loss or take_profit")
        
        logger.info(f"Updating position {deal_id}: {update_data}")
        
        response = self._make_request('PUT', endpoint, data=update_data)
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"✓ Position updated: {deal_id}")
            return result
        else:
            raise CapitalComAPIError(
                f"Failed to update position: {response.status_code}"
            )
    
    def validate_order_parameters(
        self,
        epic: str,
        direction: str,
        size: float,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None
    ) -> Tuple[bool, str]:
        """
        Validate order parameters before submission.
        
        Args:
            epic: Instrument identifier
            direction: 'BUY' or 'SELL'
            size: Position size
            stop_loss: Stop loss level
            take_profit: Take profit level
        
        Returns:
            (is_valid, error_message) tuple
        """
        # Check direction
        if direction.upper() not in ['BUY', 'SELL']:
            return False, f"Invalid direction: {direction}"
        
        # Check size
        if size <= 0:
            return False, f"Invalid size: {size} (must be > 0)"
        
        if size > 100:  # Sanity check
            return False, f"Size {size} seems unusually large"
        
        # Check stop loss vs take profit logic
        if stop_loss and take_profit:
            if direction.upper() == 'BUY':
                if stop_loss >= take_profit:
                    return False, f"For BUY: stop_loss ({stop_loss}) must be < take_profit ({take_profit})"
            else:  # SELL
                if stop_loss <= take_profit:
                    return False, f"For SELL: stop_loss ({stop_loss}) must be > take_profit ({take_profit})"
        
        return True, ""
    
    def check_api_health(self) -> bool:
        """
        Check if API connection is healthy.
        
        Returns:
            True if API is accessible and responsive
        """
        try:
            # Try to get account info as a health check
            if not self.cst_token:
                return False
            
            response = self._make_request('GET', '/api/v1/accounts', retry=False)
            return response.status_code == 200
        except:
            return False
    
    def logout(self):
        """Close the current session"""
        if not self.cst_token:
            logger.info("Not authenticated, no session to close")
            return
        
        try:
            response = self._make_request('DELETE', '/api/v1/session', retry=False)
            if response.status_code == 200:
                logger.info("✓ Session closed successfully")
            self.cst_token = None
            self.x_security_token = None
        except Exception as e:
            logger.warning(f"Error closing session: {e}")


# Example usage and testing
if __name__ == '__main__':
    """
    Demo script showing basic Capital.com API usage.
    This runs in DEMO mode by default (safe to test).
    """
    print("=" * 60)
    print("Capital.com API Connector - Demo")
    print("=" * 60)
    
    try:
        # Initialize API (uses DEMO environment from .env)
        api = CapitalComAPI()
        
        # Step 1: Authenticate
        print("\n1. Authenticating...")
        api.authenticate()
        
        # Step 2: Get account balance
        print("\n2. Getting account balance...")
        balance = api.get_account_balance()
        print(f"   Balance: {balance['balance']} {balance['currency']}")
        print(f"   Available: {balance['available']} {balance['currency']}")
        print(f"   P&L: {balance['profit_loss']} {balance['currency']}")
        
        # Step 3: Get market data for Gold
        print("\n3. Fetching historical prices for GOLD...")
        prices = api.get_historical_prices('GOLD', resolution='HOUR', max_points=5)
        if prices:
            print(f"   Latest 5 hourly prices:")
            for price in prices[-5:]:
                print(f"   {price.get('snapshotTime')} - "
                      f"O:{price['openPrice']['bid']} "
                      f"H:{price['highPrice']['bid']} "
                      f"L:{price['lowPrice']['bid']} "
                      f"C:{price['closePrice']['bid']}")
        
        # Step 4: Get current positions
        print("\n4. Checking open positions...")
        positions = api.get_positions()
        if positions:
            print(f"   Found {len(positions)} open position(s)")
            for pos in positions:
                print(f"   - {pos['market']['instrumentName']}: "
                      f"{pos['position']['direction']} "
                      f"size={pos['position']['size']}")
        else:
            print("   No open positions")
        
        # Step 5: Clean up
        print("\n5. Logging out...")
        api.logout()
        
        print("\n" + "=" * 60)
        print("✓ Demo completed successfully!")
        print("=" * 60)
        
    except CapitalComAPIError as e:
        print(f"\n❌ API Error: {e}")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
