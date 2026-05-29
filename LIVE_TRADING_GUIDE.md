# Capital.com Live Trading Integration Guide

## ✅ Status: CONNECTED & READY

Your Capital.com account is **successfully connected** and ready for live trading!

- **Account Balance**: $111.55 USD
- **Environment**: LIVE
- **Account ID**: 170139588923315396
- **API Status**: ✓ Working

---

## Quick Reference

### Available Scripts

1. **`capital_com_api.py`** - Main API connector (run standalone to test connection)
2. **`minimal_live_trade_test.py`** - Place a minimal test trade (0.01 lots)
3. **`broker_integration_example.py`** - Full demo workflow
4. **`test_auth.py`** - Quick authentication test

###Run Commands

```bash
# Test connection
python capital_com_api.py

# Place minimal test trade (0.01 lots, ~$2 risk)
python minimal_live_trade_test.py

# Full integration demo
python broker_integration_example.py
```

---

## Integrating with Your Pairs Trading Strategy

### Option 1: Modify Existing Strategy

Update your `pairs_trading_strategy.py` to execute trades via Capital.com:

```python
from capital_com_api import CapitalComAPI

class PairsTradingStrategy:
    def __init__(self, use_live_broker=False):
        self.use_live_broker = use_live_broker
        if use_live_broker:
            self.broker = CapitalComAPI()
            self.broker.authenticate()
    
    def execute_trade(self, epic, direction, size=0.01):
        """Execute trade via Capital.com"""
        if not self.use_live_broker:
            print(f"BACKTEST: {direction} {epic} size={size}")
            return
        
        # Get current price
        market = self.broker.get_market_details(epic)
        current_price = float(market['snapshot']['bid'])
        
        # Set risk parameters
        if direction == 'BUY':
            stop_loss = current_price - 2
            take_profit = current_price + 5
        else:  # SELL
            stop_loss = current_price + 2
            take_profit = current_price - 5
        
        # Place order
        result = self.broker.create_position(
            epic=epic,
            direction=direction,
            size=size,
            stop_loss=stop_loss,
            take_profit=take_profit
        )
        
        print(f"✓ Order placed: {result['dealReference']}")
        return result
```

### Option 2: Create New Live Trading Script

Create `live_pairs_trading.py`:

```python
from capital_com_api import CapitalComAPI
from pairs_trading_strategy import PairsTradingStrategy
import pandas as pd

def main():
    # Initialize broker
    broker = CapitalComAPI()
    broker.authenticate()
    
    # Get account info
    balance = broker.get_account_balance()
    print(f"Balance: ${balance['balance']}")
    
    # Fetch live data for GLD and GDX
    gld_prices = broker.get_historical_prices('GOLD', 'DAY', max_points=100)
    gdx_prices = broker.get_historical_prices('GDX', 'DAY', max_points=100)
    
    # Convert to pandas
    gld_df = pd.DataFrame(gld_prices)
    gdx_df = pd.DataFrame(gdx_prices)
    
    # Run strategy
    strategy = PairsTradingStrategy()
    signals = strategy.generate_signals(gld_df, gdx_df)
    
    # Execute trades based on signals
    if signals['action'] == 'BUY_GLD':
        broker.create_position('GOLD', 'BUY', size=0.01)
    elif signals['action'] == 'SELL_GLD':
        broker.create_position('GOLD', 'SELL', size=0.01)
    
    broker.logout()

if __name__ == '__main__':
    main()
```

---

## Safety Settings for Live Trading

### Minimum Position Sizes (Capital.com)

- **Forex**: 0.01 lots
- **Commodities (Gold)**: 0.01 lots
- **Indices**: 0.01 lots
- **Stocks**: 1 share (minimum)

### Recommended Risk Parameters

With $111.55 balance, conservative settings:

```python
# Risk Management
MAX_RISK_PER_TRADE = 2.0  # $2 maximum loss per trade (2% of balance)
MAX_POSITION_SIZE = 0.01  # Minimum lot size
STOP_LOSS_DISTANCE = 2.0  # $2 stop loss
TAKE_PROFIT_DISTANCE = 5.0  # $5 take profit (2.5:1 reward/risk)
```

### Update `config.py`

Add live trading configuration:

```python
# Live Trading Settings
LIVE_TRADING = {
    'enabled': True,
    'min_position_size': 0.01,
    'max_risk_per_trade_usd': 2.0,
    'max_open_positions': 2,
    'default_stop_loss': 2.0,
    'default_take_profit': 5.0,
}
```

---

## Testing Workflow

### Step 1: Test Minimal Trade (RECOMMENDED FIRST)

```bash
python minimal_live_trade_test.py
```

This will:
- Show your balance
- Place a 0.01 lot BUY on GOLD
- Risk: ~$2, Potential: ~$5
- Ask if you want to close immediately

### Step 2: Monitor on TradingView (Optional)

1. Go to https://tradingview.capital.com
2. Log in with your Capital.com credentials
3. Your positions will appear automatically
4. Use for visual monitoring while bot trades programmatically

### Step 3: Run Pairs Strategy Live

Once comfortable with minimal trades, integrate with your strategy:

```bash
python live_pairs_trading.py
```

---

## Important Notes

### Market Hours
- **Forex**: 24/5 (Sunday 5pm EST - Friday 5pm EST)
- **Gold**: 24/5 (Sunday 6pm EST - Friday 5:15pm EST)
- **Stocks (GLD/GDX)**: NYSE hours (9:30am - 4pm EST)

### Current Time
It's Saturday (December 7, 2025) - **markets are CLOSED**. 

For full testing, wait until:
- **Gold/Forex**: Sunday evening (~6pm EST)
- **Stocks (GLD/GDX)**: Monday morning (9:30am EST)

However, **authentication and connection testing works 24/7**!

### Capital.com Instruments

Your pairs strategy uses GLD/GDX. On Capital.com:
- **GOLD**: Physical gold (available)
- **GLD**: SPDR Gold Trust ETF (check availability)
- **GDX**: VanEck Gold Miners ETF (check availability)

You may need to trade **GOLD directly** instead of GLD/GDX, or adjust your strategy.

---

## Next Steps

1. ✅ **Connection tested** - Capital.com is working
2. ⏳ **Wait for markets to open** (Sunday evening for Gold)
3. 🧪 **Run minimal trade test** when markets open
4. 📊 **Check instrument availability** (GLD/GDX vs GOLD)
5. 🤖 **Integrate with pairs strategy** after successful minimal trade
6. 📈 **Monitor via TradingView** (optional but recommended)

---

## Troubleshooting

### "Market closed" errors
- Normal outside trading hours
- Wait for market open times above

### Position size too small
- 0.01 is the minimum for most instruments
- This is correct for testing with ~$100 balance

### Insufficient margin
- Each 0.01 lot requires margin
- With $111.55, you can safely open 1-2 positions at 0.01 lots
- Don't exceed 2 simultaneous positions

---

## Summary

✅ **What's Working**:
- Capital.com authentication
- Account balance retrieval ($111.55)
- Market data fetching
- Position management API

⚠️ **To Test** (when markets open):
- Actual order execution
- Position monitoring
- Stop loss / take profit triggers

🔧 **To Build**:
- Integration with your pairs trading strategy
- Automated signal execution
- Risk management automation
