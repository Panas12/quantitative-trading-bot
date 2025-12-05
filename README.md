# Quantitative Trading Bot

Based on Ernest Chan's "Quantitative Trading: How to Build Your Own Algorithmic Trading Business"

## Overview

This trading bot implements a **pairs trading strategy** for GLD (gold ETF) and GDX (gold miners ETF), following the methodology described in Ernest Chan's seminal book on quantitative trading. The strategy exploits mean-reversion in the spread between two cointegrated assets.

## Key Features

✅ **Statistical Arbitrage** - Pairs trading based on cointegration  
✅ **Rigorous Backtesting** - Train/test split to avoid overfitting  
✅ **Risk Management** - Kelly Criterion for optimal position sizing  
✅ **Transaction Costs** - Realistic modeling of trading costs and slippage  
✅ **Performance Metrics** - Sharpe ratio, max drawdown, win rate, profit factor  
✅ **Visualization** - Comprehensive charts for analysis

## Strategy Explained

### From Ernest Chan's Book (Example 3.6)

The strategy:

1. **Tests for Cointegration** - Ensures the two assets move together long-term
2. **Calculates Hedge Ratio** - Determines optimal trading ratio via linear regression
3. **Creates a Spread** - `spread = GLD - hedge_ratio × GDX`
4. **Normalizes to Z-Score** - Standardizes the spread for entry/exit signals
5. **Trading Rules**:
   - **Enter Long Spread** when z-score < -2 (buy GLD, short GDX)
   - **Enter Short Spread** when z-score > +2 (short GLD, buy GDX)
   - **Exit** when |z-score| < 1 (spread returns to mean)

### Why This Works

- GLD tracks physical gold prices
- GDX tracks gold mining companies
- They're fundamentally linked but can temporarily diverge
- When divergence is extreme (z-score > 2), they tend to revert to historical relationship
- This creates profitable trading opportunities

## Installation

```bash
# Clone or download the project
cd books

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Run Complete Analysis (Recommended for First Time)

```bash
python main.py --mode analysis
```

This will:
- Download GLD & GDX data from 2018
- Split into training (252 days) and testing sets
- Perform cointegration analysis
- Backtest on both periods
- Generate performance reports and charts

### Run Full Period Backtest

```bash
python main.py --mode full --start 2018-01-01
```

### Custom Pair Analysis

```bash
python main.py --symbol1 SPY --symbol2 QQQ --start 2020-01-01
```

### With Custom Capital

```bash
python main.py --capital 50000
```

## Configuration

Edit `config.py` to customize:

```python
# Trading Pairs
SYMBOL_1 = 'GLD'  # Change to your preferred pair
SYMBOL_2 = 'GDX'

# Strategy Parameters
ENTRY_THRESHOLD = 2.0  # Z-score entry threshold
EXIT_THRESHOLD = 1.0   # Z-score exit threshold
LOOKBACK_PERIOD = 252  # Training period (days)

# Risk Management
MAX_LEVERAGE = 2.0
KELLY_FRACTION = 0.5  # Use half-Kelly (conservative)
MAX_DRAWDOWN_PCT = 0.25  # Emergency stop at 25% drawdown

# Transaction Costs
TRANSACTION_COST_BPS = 5  # 5 basis points
SLIPPAGE_BPS = 2          # 2 basis points
```

## Output Files

After running, you'll get:

1. **cointegration_analysis.png** - Visual proof that the pair is cointegrated
2. **backtest_training.png** - Performance on training data
3. **backtest_testing.png** - Out-of-sample performance (most important!)
4. **trading_bot.log** - Detailed execution log

## Performance Metrics

The bot calculates:

- **Sharpe Ratio** - Risk-adjusted returns (target: > 1.0)
- **Maximum Drawdown** - Worst peak-to-trough decline
- **Win Rate** - Percentage of profitable trades
- **Profit Factor** - Gross profit / Gross loss
- **Calmar Ratio** - Return / Max Drawdown

### Expected Performance (GLD-GDX)

Based on Chan's book and historical analysis:
- **Sharpe Ratio**: 0.8 - 1.5
- **Annual Return**: 10-20% (with moderate leverage)
- **Max Drawdown**: 10-25%
- **Win Rate**: 50-60%

> ⚠️ **Important**: Past performance does not guarantee future results!

## Project Structure

```
books/
├── main.py                      # Main application
├── config.py                    # Configuration settings
├── data_fetcher.py             # Downloads historical data
├── cointegration_test.py       # Statistical cointegration tests
├── pairs_trading_strategy.py   # Trading strategy logic
├── risk_manager.py             # Kelly Criterion & risk controls
├── backtest_engine.py          # Backtesting with transaction costs
├── utils.py                    # Helper functions
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## Key Concepts from Ernest Chan's Book

### 1. Cointegration vs Correlation

- **Correlation** measures short-term co-movement
- **Cointegration** ensures long-term equilibrium relationship
- Pairs trading REQUIRES cointegration, not just correlation

### 2. Train/Test Split

- **Training Set** - Calibrate hedge ratio and spread statistics
- **Testing Set** - Validate strategy on unseen data
- Out-of-sample performance is the true test

### 3. Kelly Criterion

- Optimal position sizing based on win rate and risk/reward
- **Half-Kelly** (50%) is more conservative and recommended
- Prevents over-leveraging and catastrophic losses

### 4. Transaction Costs Matter

- Always include commissions and slippage in backtests
- A strategy with Sharpe 2.0 before costs might be < 1.0 after costs
- Short-term strategies are especially sensitive to costs

### 5. Risk Management

- Monitor drawdowns religiously
- Implement circuit breakers (emergency stops)
- "It's not about how much you make; it's about how much you don't lose"

## Extending the Bot

### Add More Pairs

```python
# In config.py
SYMBOL_1 = 'USO'  # Oil ETF
SYMBOL_2 = 'XLE'  # Energy sector ETF
```

### Add Live Trading

The bot is designed to be extended with broker APIs:

```python
# Broker integration (not included - requires API credentials)
from ib_insync import IB  # Interactive Brokers
# or
from alpaca_trade_api import REST  # Alpaca
```

### Optimize Parameters

Run parameter sweeps to find optimal thresholds:

```python
for entry_threshold in [1.5, 2.0, 2.5, 3.0]:
    for exit_threshold in [0.5, 1.0, 1.5]:
        # Run backtest
        # Compare results
```

## Warnings & Disclaimers

⚠️ **This is for educational purposes only**  
⚠️ **Not financial advice**  
⚠️ **Trading involves substantial risk of loss**  
⚠️ **Past performance does not guarantee future results**  
⚠️ **Always paper trade before risking real money**

## What Makes This Strategy Robust?

From Ernest Chan's book, this strategy is considered robust because:

1. ✅ **Simple** - Few parameters, less overfitting risk
2. ✅ **Statistically Grounded** - Based on cointegration theory
3. ✅ **Mean-Reverting** - Exploits natural price equilibrium
4. ✅ **Risk-Managed** - Kelly Criterion prevents over-betting
5. ✅ **Well-Tested** - Validated on out-of-sample data

## Common Issues

### "Pair is not cointegrated"

- Try a longer historical period
- The pair may have decouple - not suitable for this strategy
- Consider other pairs (e.g., XLE/XOP, EWA/EWC)

### "Sharpe ratio < 0.5"

- Strategy may not be profitable for this period
- Try adjusting entry/exit thresholds
- Transaction costs may be too high
- Market regime may have changed

### "ImportError: No module named..."

```bash
pip install -r requirements.txt
```

## References

- **Book**: "Quantitative Trading: How to Build Your Own Algorithmic Trading Business" by Ernest P. Chan
- **Blog**: epchan.blogspot.com
- **Website**: epchan.com

## License

Educational use only. Based on publicly available research and methodologies.

## Author

Built following the methodology in Ernest Chan's "Quantitative Trading" book, which emphasizes:
- Simple, robust strategies over complex ones
- Statistical rigor over curve-fitting
- Risk management over profit maximization
- Systematic testing over discretionary trading

---

**"The goal of quantitative trading is not to build the most sophisticated model, but to build the most profitable one."**  
*- Ernest P. Chan*
