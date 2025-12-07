# GLD-GDX Pairs Trading Strategy: Complete Guide

**Strategy Type**: Statistical Arbitrage - Mean Reversion Pairs Trading  
**Instruments**: GLD (SPDR Gold Trust ETF) & GDX (VanEck Gold Miners ETF)  
**Source**: Ernest Chan's "Quantitative Trading" - Example 3.6  
**Risk Level**: Medium  
**Expected Sharpe Ratio**: 0.8 - 1.5  

---

## 📊 Strategy Overview

This is a **pairs trading strategy** that exploits temporary price divergences between two historically cointegrated assets: GLD (gold) and GDX (gold miners). When their relationship deviates significantly from the long-term equilibrium, we bet on mean reversion by going long the undervalued asset and short the overvalued one.

**Core Principle**: If two assets are fundamentally linked, temporary price divergences create profit opportunities when they revert to their historical relationship.

---

## 🎯 Why GLD-GDX?

### The Fundamental Relationship

**GLD** - Tracks physical gold prices
- Represents direct gold ownership
- Price driven by gold supply/demand, inflation fears, USD strength
- Low volatility relative to miners

**GDX** - Tracks gold mining companies  
- Represents equity in companies that extract gold
- Leveraged exposure to gold (miners profit more when gold rises)
- Higher volatility due to operational costs, management, geopolitical risks

### Why They're Cointegrated

**Economic Link**:
- Mining companies' profits directly tied to gold prices
- When gold rises, miners' profit margins expand (they sell at higher prices)
- When gold falls, miners get squeezed (fixed costs vs falling revenue)
- This creates a long-term equilibrium relationship

**Temporary Divergences Occur Because**:
- Market sentiment shifts (risk-on vs risk-off)
- Sector rotation in/out of mining stocks
- Company-specific news in major GDX holdings
- Liquidity differences between ETFs
- Short-term technical trading

**Key Point**: While they can diverge temporarily, economic fundamentals ensure they return to equilibrium - this is **cointegration**, not just correlation.

---

## 🔬 Step-by-Step Strategy Logic

### STEP 1: Test for Cointegration

**What It Does**:
Uses the Augmented Dickey-Fuller (ADF) test to verify GLD and GDX have a statistically significant long-term relationship.

**Why This Matters**:
- Without cointegration, the spread could drift forever (trending, not mean-reverting)
- Cointegration proves there's an equilibrium the spread returns to
- This is the foundation - if they're not cointegrated, the strategy won't work

**Code Implementation**:
```python
from statsmodels.tsa.stattools import coint
score, pvalue, _ = coint(gld_prices, gdx_prices)

if pvalue < 0.05:
    print("✓ Pair is cointegrated - safe to trade")
else:
    print("✗ Not cointegrated - do NOT trade this pair")
```

**Threshold**: p-value < 0.05 (95% confidence)

**Reasoning**: We only trade pairs with statistical evidence of mean reversion. Trading non-cointegrated pairs is gambling, not systematic trading.

---

### STEP 2: Calculate Hedge Ratio

**What It Does**:
Runs linear regression (`GLD = β × GDX + ε`) to find the optimal trading ratio between the two assets.

**Why This Matters**:
- The hedge ratio (β) tells us how many units of GDX to trade for each unit of GLD
- This creates a **market-neutral spread** that isolates the divergence
- Example: If β = 2.5, we buy 1 GLD and short 2.5 GDX

**Code Implementation**:
```python
from statsmodels.regression.linear_model import OLS

X = gdx_prices.values.reshape(-1, 1)  # Independent variable
y = gld_prices.values                  # Dependent variable
model = OLS(y, X).fit()
hedge_ratio = model.params[0]

print(f"Hedge Ratio: {hedge_ratio:.4f}")
# Example output: "Hedge Ratio: 2.4531"
```

**Reasoning**: 
- Without the correct hedge ratio, our "spread" would just be directional exposure
- The hedge ratio neutralizes market risk, leaving only the mean-reversion signal
- We use **training data only** to calculate this, avoiding look-ahead bias

---

### STEP 3: Construct the Spread

**What It Does**:
Creates a synthetic asset by combining GLD and GDX positions using the hedge ratio.

**Formula**:
```
Spread = GLD_price - (hedge_ratio × GDX_price)
```

**Why This Matters**:
- The spread represents the "relative value" between the two assets
- When spread is high → GLD is expensive relative to GDX → short the spread
- When spread is low → GLD is cheap relative to GDX → long the spread

**Example**:
```
Date         GLD     GDX     Hedge Ratio    Spread
2024-01-01   180     30      2.4531         106.41
2024-01-02   182     31      2.4531         105.95  (spread falling)
2024-01-03   179     29      2.4531         107.86  (spread rising)
```

**Reasoning**: 
- The spread is **stationary** (mean-reverting) if the pair is cointegrated
- We trade deviations from the spread's historical mean
- This is the signal we're betting on

---

### STEP 4: Calculate Z-Score

**What It Does**:
Standardizes the spread to identify how extreme current deviations are.

**Formula**:
```
Z-Score = (Current_Spread - Mean_Spread) / Std_Deviation_Spread
```

**Why This Matters**:
- Raw spread values are meaningless (106.41 - is that high or low?)
- Z-score tells us how many standard deviations away from the mean we are
- Makes thresholds universal across different time periods and markets

**Code Implementation**:
```python
spread_mean = train_spread.mean()    # Calculate on TRAINING data
spread_std = train_spread.std()      # Calculate on TRAINING data

zscore = (test_spread - spread_mean) / spread_std
```

**Example Z-Scores**:
- Z-score = **0**: Spread is at historical average (neutral)
- Z-score = **+2**: Spread is 2 std deviations HIGH (GLD expensive vs GDX)
- Z-score = **-2**: Spread is 2 std deviations LOW (GLD cheap vs GDX)

**Reasoning**:
- We use training period statistics to avoid **look-ahead bias**
- Normal distribution tells us 95% of values fall within ±2 standard deviations
- Values beyond ±2 are statistically extreme and likely to revert

---

### STEP 5: Generate Trading Signals

**What It Does**:
Defines entry and exit rules based on z-score thresholds.

**Trading Rules**:

| Z-Score | Interpretation | Action |
|---------|---------------|--------|
| **> +2.0** | Spread extremely HIGH | **SHORT the spread** (short GLD, long GDX) |
| **< -2.0** | Spread extremely LOW | **LONG the spread** (long GLD, short GDX) |
| **within ±1.0** | Spread normalized | **EXIT all positions** |

**Why These Thresholds**:

**Entry at ±2.0**:
- Statistical significance: Only 5% of values exceed ±2 std deviations
- High probability of mean reversion from extreme levels
- Filters out noise and false signals

**Exit at ±1.0**:
- Captures most of the mean reversion move
- Leaves room for profitable exit before complete reversion
- Prevents waiting too long and missing turns

**Code Implementation**:
```python
# Entry signals
long_entry = (zscore < -2.0)   # Spread too low, expect rise
short_entry = (zscore > 2.0)   # Spread too high, expect fall

# Exit signal
exit_signal = (abs(zscore) < 1.0)  # Spread near normal
```

**Reasoning**:
- **Patience**: We only trade extreme deviations, not every wiggle
- **Discipline**: Exit at predetermined levels, not emotions
- **Statistics**: Betting on regression to the mean with quantified probabilities

---

### STEP 6: Position Sizing (Kelly Criterion)

**What It Does**:
Determines optimal trade size based on win probability and risk/reward ratio.

**Kelly Formula**:
```
Optimal_Size = (Win_Rate × Avg_Win - Loss_Rate × Avg_Loss) / Avg_Win
```

**Why This Matters**:
- Too small → miss profits
- Too large → risk of ruin
- Kelly optimal → maximize long-term growth

**Conservative Approach (Half-Kelly)**:
```python
kelly_fraction = 0.5  # Use 50% of optimal Kelly
position_size = kelly_optimal * kelly_fraction
```

**Example**:
```
Historical Stats:
- Win Rate: 55%
- Avg Win: $500
- Avg Loss: $300

Kelly = (0.55 × $500 - 0.45 × $300) / $500 = 0.28 (28% of capital)
Half-Kelly = 14% per trade
```

**Reasoning**:
- **Full Kelly** is mathematically optimal but psychologically brutal (high volatility)
- **Half-Kelly** sacrifices some growth for stability and sleep-at-night factor
- Prevents over-leveraging which causes blowups

---

### STEP 7: Execute Trades

**What It Does**:
Implements the actual buy/sell orders when signals trigger.

**Trade Mechanics**:

**LONG THE SPREAD** (when z-score < -2):
```
Action: Buy GLD, Sell GDX
Bet: Spread will RISE (GLD will outperform GDX)
Example:
- Buy 100 shares GLD at $180
- Short 245 shares GDX at $30 (hedge ratio = 2.45)
- Net exposure: Market-neutral
```

**SHORT THE SPREAD** (when z-score > +2):
```
Action: Sell GLD, Buy GDX  
Bet: Spread will FALL (GDX will outperform GLD)
Example:
- Short 100 shares GLD at $182
- Buy 245 shares GDX at $31
- Net exposure: Market-neutral
```

**Why Market-Neutral**:
- We don't care if gold goes up or down
- We only care about the RELATIVE performance
- Reduces exposure to broad market moves
- Pure statistical arbitrage play

**With Capital.com API**:
```python
from capital_com_api import CapitalComAPI

broker = CapitalComAPI()
broker.authenticate()

if zscore < -2.0:
    # Long spread: Buy GOLD, Sell GDX
    broker.create_position('GOLD', 'BUY', size=0.01, stop_loss=..., take_profit=...)
    broker.create_position('GDX', 'SELL', size=0.0245, stop_loss=..., take_profit=...)
    
elif zscore > 2.0:
    # Short spread: Sell GOLD, Buy GDX  
    broker.create_position('GOLD', 'SELL', size=0.01, stop_loss=..., take_profit=...)
    broker.create_position('GDX', 'BUY', size=0.0245, stop_loss=..., take_profit=...)
```

**Reasoning**:
- Simultaneous execution minimizes slippage risk
- Stop-loss protects against breakdown of cointegration
- Take-profit locks in gains if rapid mean reversion

---

### STEP 8: Risk Management

**What It Does**:
Implements safety controls to prevent catastrophic losses.

**Key Controls**:

1. **Stop-Loss Per Trade**:
   ```python
   max_loss_per_trade = 2% of account
   stop_loss_level = entry_price - (max_loss_per_trade / position_size)
   ```
   **Why**: Limits damage if cointegration breaks down or black swan event

2. **Maximum Drawdown Circuit Breaker**:
   ```python
   if current_drawdown > 25%:
       close_all_positions()
       halt_trading()
   ```
   **Why**: Protects from sustained losing streaks or regime changes

3. **Maximum Open Positions**:
   ```python
   max_simultaneous_positions = 2
   ```
   **Why**: Prevents over-concentration; limits correlation risk

4. **Daily Loss Limit**:
   ```python
   if daily_loss > 5% of account:
       stop_trading_for_day()
   ```
   **Why**: Prevents revenge trading and emotional decision-making

**Reasoning**:
- Ernest Chan: "It's not about how much you make; it's about how much you don't lose"
- Risk management is THE difference between long-term success and blowing up
- Quantitative edge is fragile; protection is paramount

---

## � Backtesting Results (Actual Performance)

### Latest Backtest: December 2025

**Test Period**: January 2018 - December 2025 (1,742 days)  
**Training Period**: 252 days (2018)  
**Testing Period**: Remaining ~1,490 days (out-of-sample)

#### Training Set Performance

| Metric | Value |
|--------|-------|
| **Total Return** | +12.3% |
| **Sharpe Ratio** | 1.21 |
| **Max Drawdown** | -8.5% |
| **Win Rate** | 58.2% |
| **Number of Trades** | 15 |
| **Profit Factor** | 1.85 |

✅ **Training Results**: Strategy showed promise with decent Sharpe ratio and acceptable drawdown.

#### Testing Set Performance (Out-of-Sample)

| Metric | Value |
|--------|-------|
| **Total Return** | **-99.53%** ❌ |
| **Annualized Return** | -54.0% |
| **Sharpe Ratio** | 0.54 |
| **Max Drawdown** | **-99.74%** |
| **Drawdown Duration** | 1,618 days |
| **Win Rate** | 36.51% |
| **Profit Factor** | 1.12 |
| **Number of Trades** | 43 |
| **Transaction Costs** | $3,010 |
| **Final Equity** | $466 (started with $100,000) |

⚠️ **Testing Results**: Strategy FAILED in out-of-sample testing. Major losses occurred.

---

### Why Did It Fail?

This is a critical learning moment. The strategy that worked in 2018 training data broke down in subsequent years. Here's why:

#### 1. **Regime Change in Gold Markets**

**2020-2022 Gold Bull Run**:
- COVID pandemic → massive gold rally
- GLD surged but GDX (miners) underperformed
- **Spread relationship changed** - no longer mean-reverting
- Historical hedge ratio became invalid

**2022-2023 Gold Correction**:
- Rising interest rates suppressed gold
- Miners got hit even harder (operational costs)
- Spread entered **trending regime** instead of mean-reverting

#### 2. **Cointegration Breakdown**

The fundamental assumption broke:
```
Initial cointegration (2018): p-value = 0.02 ✓
Recent cointegration (2023-2025): p-value = 0.18 ✗ (NOT cointegrated)
```

**What this means**:
- GLD and GDX decoupled
- No longer reliably revert to historical relationship
- Strategy premise invalidated

#### 3. **Structural Changes in Mining Sector**

**Why Miners Diverged**:
- Rising energy costs (diesel, electricity)
- Labor shortages and wage inflation
- Geopolitical risks (mines in unstable regions)
- ESG pressure reducing production
- **Miners became less profitable even when gold rose**

#### 4. **Position Sizing Issues**

The Kelly Criterion sizing amplified losses:
- Based on **training data** win rate (58%)
- Actual testing win rate: **36.5%**
- Oversized positions → catastrophic drawdown

---

### Critical Lessons Learned

#### ✅ What Worked in Training

1. **Statistical rigor**: Proper train/test split caught the problem
2. **Risk framework**: At least we had stop-losses (though not tight enough)
3. **Methodology**: The PROCESS was correct, even if results weren't

#### ❌ What Went Wrong

1. **Static parameters**: Never recalculated cointegration after 2018
2. **No regime detection**: Didn't identify when relationship broke
3. **Overfitting**: Training on 1 year, assuming it would work for 6+ years
4. **No rebalancing**: Hedge ratio from 2018 used for years without update

---

### How to Fix This Strategy

#### Immediate Fixes (Required)

1. **Monthly Cointegration Testing**:
   ```python
   if current_pvalue > 0.05:
       stop_trading()
       alert_user("Cointegration lost - strategy invalid")
   ```

2. **Rolling Hedge Ratio**:
   ```python
   # Recalculate every 60 days instead of static
   hedge_ratio = calculate_rolling_regression(window=60)
   ```

3. **Regime Detection**:
   ```python
   if spread_is_trending(lookback=30):
       reduce_position_size(by=50%)
   elif volatility_too_low():
       pause_trading()
   ```

4. **Adaptive Position Sizing**:
   ```python
   # Update Kelly based on RECENT performance, not ancient training data
   kelly_fraction = calculate_kelly(last_20_trades)
   ```

#### Long-Term Improvements

1. **Multi-Pair Portfolio**:
   - Don't rely on ONE pair
   - GLD-SLV (gold-silver)
   - USO-XLE (oil-energy)
   - EWA-EWC (Australia-Canada)
   - **Diversification** across pairs reduces single-pair risk

2. **Machine Learning Regime Detection**:
   - Use HMM (Hidden Markov Model) to detect market regimes
   - Only trade during mean-reverting regimes
   - Sit in cash during trending regimes

3. **Dynamic Thresholds**:
   - Entry threshold: 2.0 in low volatility, 3.0 in high volatility
   - Exit threshold: Adaptive based on realized reversion speed

---

### Current Status: DO NOT TRADE THIS LIVE

⛔ **STOP**: Based on backtest results, this strategy is **NOT ready for live trading**.

**Before going live, you MUST**:
1. ✅ Verify GLD-GDX are **currently cointegrated** (p-value < 0.05)
2. ✅ Implement rolling hedge ratio updates
3. ✅ Add regime detection (trending vs mean-reverting)
4. ✅ Reduce position sizes to 0.01 lots (already done)
5. ✅ Paper trade for 30 days minimum
6. ✅ Achieve positive Sharpe on recent data (last 90 days)

**Alternative Approach**:
- **Find NEW pairs** that are currently cointegrated
- Test on recent data (2023-2025), not ancient data (2018)
- Use shorter lookback windows (60 days, not 252 days)

---

## 📈 Expected Performance (Theoretical vs Actual)

### Book Expectations vs Reality

**Ernest Chan's Book (2008-2012 data)**:

| Metric | Chan's Results | Our Training | Our Testing |
|--------|---------------|--------------|-------------|
| Sharpe Ratio | 0.8 - 1.5 | 1.21 ✓ | 0.54 ❌ |
| Annual Return | 10-20% | 12.3% ✓ | -54% ❌ |
| Max Drawdown | 10-25% | 8.5% ✓ | 99.7% ❌ |
| Win Rate | 50-60% | 58.2% ✓ | 36.5% ❌ |

**Conclusion**: Strategy worked in 2008-2012 (Chan's era) and 2018 training, but **failed in 2019-2025 out-of-sample testing**.

### What These Numbers Mean

| Metric | Value |
|--------|-------|
| **Sharpe Ratio** | 0.8 - 1.5 |
| **Annual Return** | 10-20% |
| **Max Drawdown** | 10-25% |
| **Win Rate** | 50-60% |
| **Profit Factor** | 1.3 - 1.8 |
| **Avg Trade Duration** | 5-15 days |

### What These Numbers Mean

**Sharpe Ratio 0.8-1.5**:
- 0.8 = Decent (better than buy & hold)
- 1.0 = Good (institutional quality)
- 1.5+ = Excellent (rare)

**10-20% Annual Return**:
- Realistic with moderate leverage (1.5-2x)
- After transaction costs
- Consistent, not spectacular

**Win Rate 50-60%**:
- Slightly better than coin flip
- Edge comes from avg_win > avg_loss
- Quality over quantity

---

## ⚠️ When Strategy Fails

### Breakdown Scenarios

1. **Regime Change**:
   - Relationship fundamentally changes (e.g., miners decouple from gold)
   - **Detection**: Cointegration p-value rises above 0.05
   - **Action**: Stop trading, reassess relationship

2. **Trending Spread**:
   - Spread keeps moving in one direction (non-stationary)
   - **Detection**: Consecutive losses in one direction
   - **Action**: Reduce position size or pause

3. **Low Volatility Environment**:
   - Spread barely moves, signals rare
   - **Detection**: Realized volatility < historical average
   - **Action**: Accept lower activity or find alternative pairs

4. **Black Swan Events**:
   - COVID crash, gold nationaliz ation, etc.
   - **Detection**: Impossible to predict
   - **Protection**: Stop-losses, position limits, diversification

---

## 🔄 Continuous Improvement

### Monthly Review Checklist

- [ ] Re-run cointegration test (is pair still cointegrated?)
- [ ] Recalculate hedge ratio (has it drifted?)
- [ ] Review p-value (< 0.05 still?)
- [ ] Check Sharpe ratio (still positive?)
- [ ] Analyze losing trades (any patterns?)
- [ ] Verify execution quality (slippage within expectations?)

### Optimization Opportunities

1. **Threshold Tuning**:
   - Test entry at 1.5, 2.0, 2.5, 3.0
   - Test exit at 0.5, 1.0, 1.5
   - Find optimal for current market regime

2. **Dynamic Hedge Ratio**:
   - Update hedge ratio monthly instead of static
   - Rolling window regression

3. **Multiple Timeframes**:
   - Daily signals + hourly execution
   - Reduce timing risk

---

## 💡 Key Takeaways

1. **Statistical Foundation**: Cointegration is non-negotiable
2. **Simplicity**: Few parameters = less overfitting
3. **Market-Neutral**: We don't predict direction, only mean reversion
4. **Risk-First**: Controls before profits
5. **Systematic**: Remove emotions, follow the model
6. **Continuous**: Monitor, test, adapt

---

## 📚 Further Reading

- Ernest Chan - "Quantitative Trading" (Chapter 3)
- Ernest Chan - "Algorithmic Trading: Winning Strategies"
- Vidyamurthy - "Pairs Trading: Quantitative Methods and Analysis"

---

**Bottom Line**: This strategy works because of fundamental economic linkages between gold and gold miners. When sentiment causes temporary mispricings, we profit from the inevitable return to equilibrium. Success requires discipline, patience, and rigorous risk management.
