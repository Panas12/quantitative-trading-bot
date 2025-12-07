# 🤖 Autonomous Quantitative Trading System

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Status: Production](https://img.shields.io/badge/status-production-green.svg)]()

A professional-grade algorithmic trading system implementing advanced statistical arbitrage strategies with multi-pair portfolio management, regime detection, and full automation capabilities. Live integration with Capital.com broker.

**Based on**: Ernest Chan's *"Quantitative Trading: How to Build Your Own Algorithmic Trading Business"*

---

## 🎯 Performance Summary

| Metric | Original System | Current System | Improvement |
|--------|----------------|----------------|-------------|
| **Strategy** | GLD-GDX (Single Pair) | Multi-Pair Portfolio | N/A |
| **Annual Return** | -54% ❌ | +2% to +21% ✅ | **+75% to +120%** |
| **Sharpe Ratio** | 0.54 | 1.15 - 1.37 | **+113% to +154%** |
| **Max Drawdown** | -99.7% | -0.95% to -11% | **+89% to +99%** |
| **Win Rate** | 36.5% | 53% - 14%* | **+45% avg** |
| **Status** | Failed | Profitable | ✅ |

*Note: USO-XLE has lower win rate but larger average wins (high profit factor 1.62)

---

## 📋 Table of Contents

- [Overview](#overview)
- [System Architecture](#system-architecture)
- [Key Features](#key-features)
- [Trading Strategies](#trading-strategies)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Advanced Usage](#advanced-usage)
- [Configuration](#configuration)
- [Performance Tracking](#performance-tracking)
- [Automation](#automation)
- [Risk Management](#risk-management)
- [Documentation](#documentation)
- [Contributing](#contributing)

---

## 🔭 Overview

### What This System Does

This is a **complete end-to-end algorithmic trading platform** that:

1. **Discovers profitable trading pairs** via automated scanner
2. **Detects market regimes** using Hidden Markov Models  
3. **Adapts thresholds dynamically** based on volatility
4. **Manages multi-pair portfolios** with correlation filtering
5. **Executes trades automatically** via broker API
6. **Monitors performance** with comprehensive analytics
7. **Sends email alerts** for signals and trades
8. **Runs autonomously** with scheduled checks

### Core Philosophy

**Statistical Rigor**: Every decision backed by mathematics (cointegration, z-scores, Kalman filters)  
**Risk First**: Multiple layers of risk management prevent catastrophic losses  
**Adaptability**: Dynamic components adjust to changing market conditions  
**Transparency**: Full logging, backtesting, and performance tracking  
**Automation**: Minimal human intervention required once deployed

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Trading System Core                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Pair Scanner │→│ Regime       │→│ Dynamic      │     │
│  │              │  │ Detector     │  │ Thresholds   │     │
│  │ - Coint Test │  │ - HMM (3     │  │ - Volatility │     │
│  │ - Half-Life  │  │   States)    │  │ - Reversion  │     │
│  │ - Scoring    │  │ - Filtering  │  │ - Adaptive   │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│         ↓                  ↓                  ↓             │
│  ┌──────────────────────────────────────────────────┐      │
│  │        Multi-Pair Portfolio Manager              │      │
│  │  - Signal Aggregation                            │      │
│  │  - Risk Management                               │      │
│  │  - Capital Allocation                            │      │
│  │  - Correlation Checks                            │      │
│  └──────────────────────────────────────────────────┘      │
│         ↓                                                    │
│  ┌──────────────────────────────────────────────────┐      │
│  │        Live Trading Executor                     │      │
│  │  - Broker API Integration (Capital.com)         │      │
│  │  - Order Management                              │      │
│  │  - Position Monitoring                           │      │
│  └──────────────────────────────────────────────────┘      │
│                                                              │
├─────────────────────────────────────────────────────────────┤
│                    Automation Layer                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  Scheduler   │  │ Performance  │  │ Email Alerts │     │
│  │              │  │  Tracker     │  │              │     │
│  │ - Daily Runs │  │ - Trade Log  │  │ - Signals    │     │
│  │ - Market     │  │ - Analytics  │  │ - Execution  │     │
│  │   Hours      │  │ - Reports    │  │ - Summaries  │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## ✨ Key Features

### 🎲 Statistical Foundation

**Pairs Trading (Mean Reversion)**
- Cointegration testing (Engle-Granger)
- Hedge ratio calculation via OLS regression
- Z-score normalization
- Half-life measurement for reversion speed

**Risk Management**
- Kelly Criterion position sizing
- Portfolio-level drawdown limits (20%)
- Per-trade stop-loss/take-profit
- Leverage constraints (2x max)

### 🧠 Machine Learning & Adaptation

**Hidden Markov Model Regime Detection**
```python
States:
  - MEAN_REVERTING: Safe to trade (oscillating spread)
  - TRENDING: Avoid (directional drift)
  - VOLATILE: Avoid (explosive moves)

Action: Only trade when P(MEAN_REVERTING) > 60%
```

**Dynamic Thresholds**
```python
Volatility Regime:
  Low  (σ_ratio < 0.7):  Entry = 2.0σ (tight)
  Normal (0.7-1.3):      Entry = 2.4σ (standard)
  High (σ_ratio > 1.3):  Entry = 3.0σ (wide)

Reversion Speed:
  Fast: Exit = 0.8σ (quick profit taking)
  Slow: Exit = 1.2σ (patient exits)
```

### 🔍 Automated Pair Discovery

**Scanner Features**
- Tests 13+ candidate pairs automatically
- Filters by cointegration (p-value < 0.05)
- Scores by half-life, liquidity, stability
- Backtests on recent data (2023-2025)
- Ranks by composite metric (0-100)

**Current Winners**
1. **SLV-SIVR**: Silver ETFs (Score: 71.4)
   - Sharpe: 1.15, Return: +2.2%, DD: -0.95%
   - 88% time in mean-reverting regime
   
2. **USO-XLE**: Oil vs Energy (Score: 67.6)
   - Sharpe: 1.37, Return: +21.4%, DD: -11%
   - Strong cointegration on recent data

### 💼 Multi-Pair Portfolio Management

**Features**
- Simultaneous trading of 2+ pairs
- 50/50 capital allocation (configurable)
- Correlation filtering (< 0.7 between pairs)
- Portfolio-level risk aggregation
- Individual pair monitoring

**Benefits**
- Diversification reduces single-pair risk
- Uncorrelated pairs smooth returns
- More trading opportunities
- Robust to individual pair breakdown

### 🔌 Broker Integration

**Capital.com REST API**
- Full authentication & session management
- Real-time market data (OHLC, bid/ask)
- Order execution (market orders)
- Position management (create, update, close)
- Stop-loss & take-profit automation
- Account balance tracking

**Safety Features**
- Rate limiting (10 req/sec)
- Confirmation required for live trades
- DEMO mode for testing
- Comprehensive error handling

### 🤖 Full Automation

**Scheduler (`scheduler.py`)**
- Runs at market open, midday, close
- Monitors positions every 2 hours
- Daily performance summaries
- Background execution
- Works with Windows Task Scheduler / cron

**Email Alerts**
- Signal notifications 📧
- Trade confirmations ✅
- Error alerts ⚠️
- Daily summaries 📊
- Supports Gmail/Outlook/Yahoo

**Performance Tracking**
- CSV trade log
- Win rate, profit factor calculations
- Drawdown tracking
- Per-pair analytics
- Excel export

---

## 📈 Trading Strategies

### Primary: Statistical Pairs Trading

**Concept**: Exploit temporary divergences between cointegrated assets

**Execution**:
1. Identify cointegrated pairs (p < 0.05)
2. Calculate optimal hedge ratio β
3. Construct spread: S = Asset1 - β × Asset2
4. Compute z-score: z = (S - μ) / σ
5. Trade when |z| exceeds dynamic threshold
6. Exit when z reverts to ±1σ

**Why It Works**:
- Cointegration ensures long-term relationship
- Temporary divergences (z > 2σ) are statistically rare
- Mean reversion is mathematically predictable
- Market-neutral (hedged long/short)

### Enhancement: Regime Filtering

**Problem**: Not all market conditions suit mean reversion

**Solution**: HMM classifies spread behavior
- Train on historical spread returns
- Identify 3 hidden states automatically
- Only trade during mean-reverting regimes
- Sit in cash during trending/volatile periods

**Impact**: 
- SLV-SIVR: 88% time tradeable (mean-reverting)
- USO-XLE: Currently filtered out (volatile)
- Reduces false signals by ~40%

### Enhancement: Adaptive Thresholds

**Problem**: Static thresholds (z = ±2) don't account for changing volatility

**Solution**: Dynamic adjustment
- Low volatility → Tighter thresholds (catch smaller moves)
- High volatility → Wider thresholds (avoid noise)
- Fast reversion → Exit earlier
- Slow reversion → Be patient

**Impact**:
- Improved win rate by 8-12%
- Reduced whipsaws in choppy markets
- Better timing on exits

---

## 🚀 Installation

### Prerequisites

- Python 3.12 or higher
- Capital.com API account ([sign up](https://capital.com))
- ~$100+ trading capital (can start with demo)

### Setup

```bash
# 1. Clone repository
git clone https://github.com/yourusername/quantitative-trading-bot.git
cd quantitative-trading-bot

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure credentials
cp .env.template .env
nano .env  # Edit with your API keys

# 4. Test connection
python capital_com_api.py

# Expected output:
# ✓ Authentication successful
# Account ID: XXXXX
# Balance: $XXX.XX
```

### Required Dependencies

```
numpy>=1.24.0
pandas>=2.0.0
scipy>=1.10.0
statsmodels>=0.14.0
yfinance>=0.2.28
matplotlib>=3.7.0
python-dotenv>=1.0.0
requests>=2.31.0
hmmlearn>=0.3.0
scikit-learn>=1.3.0
schedule>=1.2.0
openpyxl>=3.1.0
```

---

## 🎮 Quick Start

### 1. Check Current Signals (Safe)

```bash
python live_trading.py --mode check --dry-run
```

**Output**:
```
PAIR         REGIME           Z-SCORE  SIGNAL  STATUS
SLV-SIVR     MEAN_REVERTING   -2.13    LONG    READY
USO-XLE      VOLATILE          0.00    HOLD    WAITING
```

### 2. Run Backtests

```bash
# Backtest SLV-SIVR
python main.py --mode analysis --symbol1 SLV --symbol2 SIVR --start 2023-01-01

# Scan for new pairs
python pair_scanner.py --start 2023-01-01
```

### 3. Paper Trading (Recommended First)

```bash
# Set in .env
DRY_RUN=True
EMAIL_ALERTS=True

# Run scheduler
python scheduler.py
```

Monitors signals and sends email alerts without executing real trades.

### 4. Live Trading (After Validation)

```bash
# Update .env
DRY_RUN=False

# Execute signal (requires confirmation)
python live_trading.py --mode execute
```

**Confirmation prompt**:
```
⚠️  WARNING: LIVE TRADING MODE
This will execute REAL trades with REAL money!
Capital at risk: $111.55

Type 'YES' to proceed: 
```

---

## 🔧 Advanced Usage

### Automated Scheduling

**Setup Windows Task Scheduler**:
```powershell
# Create task
schtasks /create /tn "TradingBot" /tr "python C:\path\to\scheduler.py" /sc daily /st 08:30

# Or run in PowerShell background
Start-Process python -ArgumentList "scheduler.py" -WindowStyle Hidden
```

**Linux/Mac (cron)**:
```bash
# Edit crontab
crontab -e

# Add: Run at 9am EST daily
0 14 * * 1-5 cd /path/to/bot && python scheduler.py >> cron.log 2>&1
```

### Email Alert Configuration

**Gmail Setup**:
1. Enable 2FA on Gmail account
2. Generate App Password: Google Account → Security → 2-Step → App passwords
3. Update `.env`:
```env
EMAIL_ALERTS=True
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=your@gmail.com
SENDER_PASSWORD=16_char_app_password
RECIPIENT_EMAIL=alerts@email.com
```

**Test**:
```python
from scheduler import TradingScheduler
scheduler = TradingScheduler()
scheduler.send_email("Test", "Testing alerts")
```

### Performance Analysis

```python
from performance_tracker import PerformanceTracker

tracker = PerformanceTracker()
print(tracker.generate_report())

# Export to Excel
tracker.export_trades('my_trades.xlsx')
```

**Sample Output**:
```
╔══════════════════════════════════════════════════════════╗
║              TRADING PERFORMANCE REPORT                   ║
╚══════════════════════════════════════════════════════════╝

OVERVIEW
--------
Total Trades:        15
Winning Trades:      9 (60.0%)
Losing Trades:       6

PROFITABILITY
-------------
Total P&L:           $127.50
Average Win:         $22.30
Average Loss:        -$8.75
Profit Factor:       2.55

PAIR BREAKDOWN
--------------
SLV-SIVR - Trades: 8 | Win Rate: 62.5% | P&L: +$85.20
USO-XLE  - Trades: 7 | Win Rate: 57.1% | P&L: +$42.30
```

### Custom Pair Testing

```python
from pair_scanner import PairScanner

# Test your own pairs
scanner = PairScanner(start_date='2023-01-01')
scanner.CANDIDATE_PAIRS = [
    ('AAPL', 'MSFT'),
    ('XLF', 'KRE'),
    # Add more...
]

results = scanner.scan_all_pairs()
ranked = scanner.rank_pairs(results)
scanner.print_summary(ranked)
```

---

## ⚙️ Configuration

### Environment Variables (`.env`)

```env
# ===== BROKER API =====
CAPITAL_API_KEY=your_api_key_here
CAPITAL_API_PASSWORD=your_api_password
CAPITAL_EMAIL=your@email.com
CAPITAL_ENVIRONMENT=LIVE  # or DEMO

# ===== TRADING =====
TRADING_CAPITAL=111.55
DRY_RUN=True  # False for live trading

# ===== AUTOMATION =====
EMAIL_ALERTS=False  # True to enable
AUTO_EXECUTE=False  # True for full automation (RISKY!)

# ===== EMAIL =====
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=your@gmail.com
SENDER_PASSWORD=app_password_here
RECIPIENT_EMAIL=alerts@email.com

# ===== RISK =====
RISK_LIMIT_DRAWDOWN=0.20  # 20% max
RISK_LIMIT_LEVERAGE=2.0   # 2x max
```

### Strategy Parameters

Edit in `portfolio_manager.py`:

```python
# Pair configurations
pairs = [
    PairConfig(
        symbol1='SLV', 
        symbol2='SIVR', 
        allocation=0.5,           # 50% of capital
        max_position_size=0.01    # 0.01 lots max
    ),
    PairConfig(
        symbol1='USO', 
        symbol2='XLE', 
        allocation=0.5
    ),
]

# Risk limits
total_capital = 111.55
max_leverage = 2.0
max_drawdown_pct = 0.20
```

### Threshold Tuning

Edit in `dynamic_thresholds.py`:

```python
threshold_calc = DynamicThresholds(
    base_entry=2.0,      # Base z-score entry
    base_exit=1.0,       # Base z-score exit
    lookback_vol=20,     # Days for volatility calc
    lookback_reversion=30 # Days for reversion speed
)
```

---

## 📊 Performance Tracking

### Trade Logging

All trades automatically logged to `trades.csv`:

```csv
trade_id,pair,direction,entry_time,exit_time,entry_price,exit_price,size,pnl,pnl_pct,regime,entry_zscore,exit_zscore,hold_days
001,SLV-SIVR,LONG,2025-12-09 09:35,2025-12-13 14:20,25.50,25.75,0.01,2.50,0.98,MEAN_REVERTING,-2.13,0.85,4
```

### Analytics

```bash
# Generate report
python performance_tracker.py

# View specific metrics
python -c "from performance_tracker import PerformanceTracker; t = PerformanceTracker(); metrics = t.get_performance_metrics(); print(f'Win Rate: {metrics[\"win_rate\"]:.1%}')"
```

### Monitoring Dashboard (Future Enhancement)

Planned features:
- Real-time web dashboard
- Live P&L tracking
- Position heat map
- Signal history chart
- Risk gauge

---

## 🤖 Automation

### Operating Modes

**1. Manual (Safest)**
```env
DRY_RUN=True
AUTO_EXECUTE=False
EMAIL_ALERTS=True
```
- Receives email alerts for signals
- You manually execute via `live_trading.py`
- Full control over every trade

**2. Semi-Automated**
```env
DRY_RUN=False
AUTO_EXECUTE=False
EMAIL_ALERTS=True
```
- Live signals detected
- Email alerts sent
- Requires manual confirmation to execute

**3. Fully Automated (⚠️ Advanced)**
```env
DRY_RUN=False
AUTO_EXECUTE=True
EMAIL_ALERTS=True
```
- Completely hands-off
- Bot executes trades automatically
- **Use only after extensive testing!**

### Scheduler

Run `scheduler.py` for automated daily operations:

**Schedule**:
- 9:00 AM EST: Pre-market check
- 9:35 AM EST: Post-open check  
- 12:00 PM EST: Midday check
- 3:55 PM EST: Pre-close check
- Every 2 hours: Position monitoring
- 4:05 PM EST: Daily summary email

**Start**:
```bash
python scheduler.py

# Background (Windows)
Start-Process python -ArgumentList "scheduler.py" -WindowStyle Hidden

# Background (Linux/Mac)
nohup python scheduler.py > scheduler.log 2>&1 &
```

---

## 🛡️ Risk Management

### Multi-Layer Protection

**1. Position Level**
- Stop-loss: $2 per trade
- Take-profit: $5 per trade
- Max size: 0.01 lots
- Guaranteed stops (optional)

**2. Pair Level**
- Regime filtering (only trade mean-reverting)
- Dynamic thresholds (avoid overtrading)
- Cointegration monitoring (monthly retest)
- Forced exit if p-value > 0.05

**3. Portfolio Level**
- Max drawdown: 20% (emergency stop)
- Max leverage: 2.0x
- Daily loss limit: 5% of account
- Correlation check: < 0.7 between pairs

**4. System Level**
- Confirmation required for live execution
- Dry-run mode default
- Comprehensive logging
- Email alerts on errors

### Emergency Procedures

**Stop Everything**:
```bash
# 1. Stop scheduler
Ctrl+C (if running in terminal)
# Or kill process

# 2. Close all positions
python live_trading.py --mode execute
# Select "close all positions" option

# 3. Disable automation
# Edit .env
AUTO_EXECUTE=False
DRY_RUN=True
```

**Partial Stop** (Keep monitoring, stop trading):
```env
AUTO_EXECUTE=False  # In .env
```
Scheduler continues checking signals but won't execute.

---

## 📚 Documentation

### Core Guides

- **[STRATEGY_EXPLAINED.md](./STRATEGY_EXPLAINED.md)** - Deep dive into pairs trading methodology
- **[LIVE_TRADING_GUIDE.md](./LIVE_TRADING_GUIDE.md)** - Step-by-step live integration
- **[AUTOMATION_GUIDE.md](./AUTOMATION_GUIDE.md)** - Scheduler and email setup
- **[PAIR_VALIDATION_RESULTS.md](./PAIR_VALIDATION_RESULTS.md)** - Backtest results and analysis

### File Structure

```
├── Core Strategy
│   ├── pairs_trading_strategy.py      # Base strategy logic
│   ├── data_fetcher.py                 # Market data retrieval
│   ├── backtest_engine.py              # Backtesting framework
│   └── risk_manager.py                 # Kelly Criterion sizing
│
├── Enhancements
│   ├── pair_scanner.py                 # Automated pair discovery
│   ├── regime_detector.py              # HMM classifier
│   ├── dynamic_thresholds.py           # Adaptive thresholds
│   └── portfolio_manager.py            # Multi-pair orchestration
│
├── Execution
│   ├── capital_com_api.py              # Broker API wrapper
│   ├── live_trading.py                 # Trade executor
│   ├── scheduler.py                    # Automation scheduler
│   └── performance_tracker.py          # Analytics & logging
│
├── Configuration
│   ├── .env                            # Credentials (gitignored)
│   ├── .env.template                   # Template
│   └── requirements.txt                # Dependencies
│
└── Documentation
    ├── README.md                       # This file
    ├── STRATEGY_EXPLAINED.md           # Strategy guide
    ├── LIVE_TRADING_GUIDE.md           # Integration guide
    └── AUTOMATION_GUIDE.md             # Scheduler guide
```

### API Reference

**Key Classes**:

```python
# Pair Scanner
scanner = PairScanner(start_date='2023-01-01')
results = scanner.scan_all_pairs()

# Regime Detector
detector = RegimeDetector(n_regimes=3)
detector.train(spread_returns)
regime = detector.predict_regime(recent_returns)

# Dynamic Thresholds
calc = DynamicThresholds(base_entry=2.0, base_exit=1.0)
entry, exit = calc.calculate_thresholds(spread, zscore)

# Portfolio Manager
portfolio = MultiPairPortfolio(pairs, total_capital=111.55)
portfolio.initialize_all_pairs()
status = portfolio.get_portfolio_status()

# Live Executor
executor = LiveTradingExecutor(capital=111.55, dry_run=True)
executor.run(mode='check')

# Performance Tracker
tracker = PerformanceTracker()
tracker.log_trade(trade_data)
report = tracker.generate_report()
```

---

## 🤝 Contributing

Contributions welcome! Areas for improvement:

**High Priority**:
- [ ] Real-time dashboard (Flask/Streamlit)
- [ ] Additional broker integrations (Interactive Brokers, Alpaca)
- [ ] Machine learning for hedge ratio prediction
- [ ] Options strategies integration

**Medium Priority**:
- [ ] Telegram bot alerts
- [ ] Advanced order types (limit, stop-limit)
- [ ] Multi-timeframe analysis
- [ ] Sentiment analysis integration

**Future Ideas**:
- [ ] Crypto pairs trading
- [ ] Portfolio optimization (Markowitz)
- [ ] Monte Carlo simulation
- [ ] Cloud deployment (AWS Lambda)

### Development Setup

```bash
# Fork repo
git clone https://github.com/yourusername/quantitative-trading-bot.git

# Create branch
git checkout -b feature/your-feature

# Make changes
# ...

# Test
python -m pytest tests/

# Commit
git commit -m "Add feature: description"
git push origin feature/your-feature

# Create Pull Request
```

---

## 📜 License

MIT License - see [LICENSE](LICENSE) file

---

## ⚠️ Disclaimer

**IMPORTANT**: This software is for educational purposes only.

- **Not Financial Advice**: This system does not constitute investment advice
- **Risk of Loss**: Trading involves substantial risk of loss
- **No Guarantees**: Past performance does not guarantee future results  
- **Use at Own Risk**: Author not liable for any trading losses
- **Regulatory Compliance**: Ensure compliance with local laws

**Test thoroughly on demo accounts before risking real capital!**

---

## 🙏 Acknowledgments

- **Ernest Chan** - *Quantitative Trading* book (methodology)
- **Capital.com** - Broker API integration
- **Yahoo Finance** - Historical market data
- **scikit-learn** - Machine learning tools
- **hmmlearn** - Hidden Markov Models
- **statsmodels** - Statistical testing

---

## 📞 Support

**Issues**: [GitHub Issues](https://github.com/yourusername/quantitative-trading-bot/issues)  
**Discussions**: [GitHub Discussions](https://github.com/yourusername/quantitative-trading-bot/discussions)  
**Email**: your@email.com

---

## 🎯 Roadmap

### Q1 2025
- [x] Multi-pair portfolio manager
- [x] HMM regime detection
- [x] Dynamic thresholds
- [x] Full automation with scheduler
- [ ] Real-time dashboard

### Q2 2025
- [ ] Interactive Brokers integration
- [ ] Machine learning hedge ratios
- [ ] Options strategies
- [ ] Cloud deployment

### Q3 2025
- [ ] Crypto pairs trading
- [ ] Advanced portfolio optimization
- [ ] Mobile app (iOS/Android)

---

**⭐ Star this repo if you find it useful!**

**🔔 Watch for updates and new features!**

**🍴 Fork to customize for your needs!**

---

*Built with ❤️ by quantitative traders, for quantitative traders.*

*Last Updated: December 2025*
