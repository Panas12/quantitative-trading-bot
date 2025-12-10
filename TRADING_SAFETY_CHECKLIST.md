# Trading Safety Checklist

**Last Updated**: December 2025

This checklist ensures you've taken all necessary precautions before running your trading bot with real money.

---

## 🔴 Critical Pre-Launch Checks

### 1. Environment Configuration

- [ ] `.env` file is configured with correct API credentials
- [ ] `CAPITAL_ENVIRONMENT` is set to `DEMO` for testing (change to `LIVE` only when ready)
- [ ] `DRY_RUN=True` for initial testing
- [ ] `TRADING_CAPITAL` matches your actual account balance
- [ ] Risk limits are reasonable:
  - `RISK_LIMIT_DRAWDOWN` ≤ 0.20 (20% max recommended)
  - `RISK_LIMIT_LEVERAGE` ≤ 2.0 (2x max recommended)

### 2. Run Pre-Launch Verification

```bash
python pre_launch_verification.py
```

**All checks must pass** before proceeding. Address any errors or warnings.

### 3. Demo Account Testing

> [!IMPORTANT]
> **NEVER skip demo testing before going live!**

- [ ] Switch to demo account: `CAPITAL_ENVIRONMENT=DEMO` in `.env`
- [ ] Run verification: All checks pass in demo mode
- [ ] Execute test trades in demo account
- [ ] Verify trades appear correctly in Capital.com demo interface
- [ ] Test exit signals - ensure positions close properly
- [ ] Monitor for 24-48 hours in demo mode

### 4. Capital Requirements

- [ ] Minimum $100 in account (recommended $200+ for safety margin)
- [ ] Sufficient margin for 2 simultaneous pairs
- [ ] Buffer capital for drawdowns (at least 20% extra)

---

## ⚠️ First Live Trade Preparation

### Before Enabling Live Mode

- [ ] Demo testing completed successfully for at least 48 hours
- [ ] No errors in logs during demo testing
- [ ] Understand the strategy (read [`STRATEGY_EXPLAINED.md`](./STRATEGY_EXPLAINED.md))
- [ ] Email alerts configured and tested (optional but recommended)
- [ ] Know how to manually close positions in Capital.com web interface

### Going Live - Step by Step

**Step 1**: Test with minimal capital first

```bash
# In .env
CAPITAL_ENVIRONMENT=LIVE
DRY_RUN=False
TRADING_CAPITAL=100  # Start small
```

**Step 2**: Run pre-launch verification
```bash
python pre_launch_verification.py
```

**Step 3**: Manual first trade
```bash
python live_trading.py --mode check  # View signals
python live_trading.py --mode execute  # Execute with confirmation
```

**Step 4**: Verify execution
- [ ] Check Capital.com web interface - positions opened?
- [ ] Check logs - no errors?
- [ ] Verify stop-loss and take-profit are set correctly
- [ ] Note the deal references from logs

---

## 📊 Monitoring (First 48 Hours Critical)

### What to Monitor

**Every 2-4 Hours**:
- [ ] Check Capital.com account - any unexpected positions?
- [ ] Review `live_trading.log` - any errors?
- [ ] Verify bot is respecting risk limits
- [ ] Check P&L is within expectations

**Daily**:
- [ ] Review performance tracker data
- [ ] Ensure positions are being closed when signals reverse
- [ ] Verify email alerts are being sent (if enabled)
- [ ] Check that regime detection is filtering properly

### Red Flags - Stop Immediately If:

🛑 **STOP THE BOT AND CLOSE ALL POSITIONS IF**:
- Position sizes are larger than 0.01 lots
- More than 4 positions open simultaneously
- Drawdown exceeds 15%
- Same pair keeps opening/closing repeatedly (likely bug)
- API errors appearing repeatedly
- Positions opened without corresponding entries in log

**How to Emergency Stop**:
```bash
# 1. Stop the scheduler (Ctrl+C if running in terminal)
# 2. Set DRY_RUN=True in .env
# 3. Manually close all positions:
python live_trading.py --mode execute
# Select "EXIT" for all pairs
```

---

## 🔍 Common Issues & Solutions

### Issue: "Authentication Failed"
**Solution**: 
- Verify API credentials in `.env`
- Check that API key is for the correct environment (demo vs live)
- Regenerate API password in Capital.com if needed

### Issue: "Insufficient Funds"
**Solution**:
- Reduce position size in `portfolio_manager.py`
- Ensure `TRADING_CAPITAL` in `.env` matches actual balance
- Check margin requirements for your instruments

### Issue: "Position Not Found" after creation
**Solution**:
- This can happen if positions close very quickly
- Check Capital.com history - position may have hit SL immediately
- Review the entry price vs current market price
- Consider widening stop-loss if market is too volatile

### Issue: No trading signals for days
**Solution**:
- Run `python pair_scanner.py` to check if pairs are still cointegrated
- Check that regime detector isn't filtering out all opportunities
- Verify market data is being fetched correctly
- Review `PAIR_VALIDATION_RESULTS.md` for pair health

### Issue: Email alerts not sending
**Solution**:
- Test SMTP credentials manually
- For Gmail: ensure 2FA is enabled and using App Password
- Check firewall isn't blocking SMTP port 587
- Run verification script: `python pre_launch_verification.py`

---

## 📈 Performance Expectations

### Realistic Expectations

**Good Performance**:
- 2-5% monthly return
- Sharpe ratio > 1.0
- Win rate 45-60%
- Max drawdown < 10%

**Warning Signs**:
- Consistent daily losses for a week
- Win rate dropping below 35%
- Drawdown exceeding 15%
- Large number of trades in one day (overtrading)

### When to Pause Trading

Consider pausing the bot if:
- Major market events (Fed announcements, earnings, etc.)
- Cointegration breaks down (p-value > 0.05)
- Consecutive losing days > 5
- Strategy performance degrades significantly

---

## 🛠️ Maintenance Schedule

### Weekly
- Review performance tracker metrics
- Check logs for any warnings or errors
- Verify cointegration is still holding
- Run pair scanner to check for new opportunities

### Monthly
- Re-run backtests on recent data
- Update thresholds if needed
- Review and update pair configurations
- Download and backup trade history

### Quarterly
- Full system review
- Consider strategy adjustments
- Evaluate new pairs
- Review and update risk parameters

---

## 📞 Support & Resources

### Documentation
- [`README.md`](./README.md) - System overview
- [`STRATEGY_EXPLAINED.md`](./STRATEGY_EXPLAINED.md) - Strategy details
- [`LIVE_TRADING_GUIDE.md`](./LIVE_TRADING_GUIDE.md) - Integration guide
- [`AUTOMATION_GUIDE.md`](./AUTOMATION_GUIDE.md) - Automation setup

### Logs to Check
- `live_trading.log` - Trade execution logs
- `trading_bot.log` - General system logs
- `trades.csv` - Trade history (created by performance tracker)

### Capital.com Resources
- Web Platform: https://capital.com
- API Documentation: https://open-api.capital.com/
- Support: Via Capital.com website

---

## ✅ Final Pre-Flight Checklist

Before starting automated trading, confirm:

- [x] **Read and understand** STRATEGY_EXPLAINED.md
- [x] **Tested thoroughly** in demo account (48+ hours)
- [x] **Pre-launch verification** passed all checks
- [x] **Email alerts** configured and tested (optional)
- [x] **Risk limits** are conservative
- [x] **Emergency procedures** understood
- [x] **Monitoring plan** in place for first 48 hours
- [x] **Starting with minimal capital** ($100-200)
- [x] **Know how to stop** the bot immediately if needed

---

> [!CAUTION]
> **Trading involves risk of loss. Past performance does not guarantee future results.**
> 
> This bot is intended for educational purposes. Start with minimal capital and monitor closely. Never invest more than you can afford to lose.

---

**Ready to proceed?**

1. ✅ All checks complete → Run: `python scheduler.py`
2. ⚠️ Any doubts → Test more in demo mode
3. ❌ Checks failed → Fix issues before proceeding
