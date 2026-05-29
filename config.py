"""
Configuration file for Quantitative Trading Bot
Based on Ernest Chan's "Quantitative Trading" methodology
"""

# Trading Pairs Configuration
SYMBOL_1 = 'GLD'  # iShares Gold Trust ETF
SYMBOL_2 = 'GDX'  # VanEck Vectors Gold Miners ETF

# Strategy Parameters (from Chan's Example 3.6)
ENTRY_THRESHOLD = 2.0  # Enter trade when z-score exceeds ±2 standard deviations
EXIT_THRESHOLD = 1.0   # Exit trade when z-score returns within ±1 standard deviation
LOOKBACK_PERIOD = 252  # Training period in trading days (approximately 1 year)

# Risk Management Parameters (from Chapter 6)
MAX_LEVERAGE = 2.0  # Maximum leverage allowed
KELLY_FRACTION = 0.5  # Use half-Kelly for more conservative position sizing
MAX_DRAWDOWN_PCT = 0.25  # Emergency stop if drawdown exceeds 25%
MAX_POSITION_SIZE = 0.95  # Maximum fraction of capital per position

# Transaction Cost Model (from Chapter 3)
TRANSACTION_COST_BPS = 5  # 5 basis points (0.05%) per trade
SLIPPAGE_BPS = 2  # Additional 2 basis points for market impact

# Backtesting Configuration
TRAIN_TEST_SPLIT = 0.67  # 67% training, 33% testing
MIN_HISTORY_DAYS = 500  # Minimum historical data required
START_DATE = '2018-01-01'  # Default backtest start date
END_DATE = None  # None means use current date

# Data Configuration
DATA_SOURCE = 'yfinance'  # Options: 'yfinance', 'ib', 'alpaca'
DATA_FREQUENCY = '1D'  # Daily data

# Cointegration Test Parameters (from Chapter 7)
COINTEGRATION_CONFIDENCE = 0.05  # 95% confidence level for ADF test
MIN_HALF_LIFE = 1  # Minimum half-life in days
MAX_HALF_LIFE = 60  # Maximum half-life in days

# Live Trading Configuration
PAPER_TRADING = True  # Start with paper trading
UPDATE_FREQUENCY = 60  # Check for signals every 60 seconds in live mode
TRADING_START_TIME = '09:35'  # Start trading 5 min after market open
TRADING_END_TIME = '15:55'  # Stop trading 5 min before market close

# Broker API Configuration (to be filled by user)
BROKER = 'paper'  # Options: 'ib', 'alpaca', 'paper'
IB_HOST = '127.0.0.1'
IB_PORT = 7497  # 7497 for paper, 7496 for live
IB_CLIENT_ID = 1
ALPACA_API_KEY = ''
ALPACA_SECRET_KEY = ''
ALPACA_BASE_URL = 'https://paper-api.alpaca.markets'  # Paper trading URL

# Performance Reporting
REPORT_FREQUENCY = 'daily'  # Options: 'trade', 'daily', 'weekly'
ALERT_EMAIL = None  # Set to email address for alerts

# Logging Configuration
LOG_LEVEL = 'INFO'  # Options: 'DEBUG', 'INFO', 'WARNING', 'ERROR'
LOG_FILE = 'trading_bot.log'

# Capital Allocation
INITIAL_CAPITAL = 100000  # Default $100k for backtesting
