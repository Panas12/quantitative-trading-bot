# Automation & Monitoring Guide

## 🤖 Automated Trading System

Your trading bot can now run fully automated with scheduled checks and email alerts!

---

## Features

### 1. Automated Scheduler (`scheduler.py`)

Runs daily signal checks automatically:
- **9:00 AM EST**: Pre-market check
- **9:35 AM EST**: Post-open check
- **12:00 PM EST**: Midday check
- **3:55 PM EST**: Pre-close check
- **Every 2 hours**: Position monitoring
- **4:05 PM EST**: Daily summary email

### 2. Email Alerts

Get notified when:
- Trading signals are detected
- Trades are executed
- Errors occur
- Daily performance summary

### 3. Performance Tracking (`performance_tracker.py`)

Logs all trades and calculates:
- Win rate
- Profit factor
- Average win/loss
- Max drawdown
- Per-pair performance

---

## Setup Instructions

### Step 1: Install Dependencies

```bash
pip install schedule openpyxl
```

### Step 2: Configure Email (Optional)

For Gmail:
1. Enable 2FA on your Gmail account
2. Generate an App Password:
   - Go to Google Account → Security
   - 2-Step Verification → App passwords
   - Select "Mail" and your device
   - Copy the 16-character password

3. Update `.env`:
```env
EMAIL_ALERTS=True
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=your@gmail.com
SENDER_PASSWORD=your_16_char_app_password
RECIPIENT_EMAIL=alerts@email.com
```

For other email providers:
- **Outlook**: smtp-mail.outlook.com, port 587
- **Yahoo**: smtp.mail.yahoo.com, port 587

### Step 3: Choose Your Mode

#### Option A: Manual Trading (Safest)
```env
DRY_RUN=True
AUTO_EXECUTE=False
```
- Scheduler sends alerts only
- You manually execute trades via `live_trading.py`

#### Option B: Semi-Automated
```env
DRY_RUN=False
AUTO_EXECUTE=False
```
- Receives live signals
- Sends email alerts
- You manually confirm execution

#### Option C: Fully Automated (⚠️ RISKY!)
```env
DRY_RUN=False
AUTO_EXECUTE=True
```
- **Automatically executes trades**
- Only use after extensive testing!
- Recommended: Start with small position sizes

---

## Running the Scheduler

### Start the Scheduler:
```bash
python scheduler.py
```

**Runs in foreground**. Keep terminal open or use:

### Background Execution (Windows):
```powershell
Start-Process python -ArgumentList "scheduler.py" -WindowStyle Hidden
```

### Background Execution (Linux/Mac):
```bash
nohup python scheduler.py > scheduler_output.log 2>&1 &
```

### As Windows Service (Advanced):
Use Task Scheduler:
1. Open Task Scheduler
2. Create Basic Task
3. Trigger: Daily at 8:00 AM
4. Action: Start Program → `python.exe`
5. Arguments: `c:\path\to\scheduler.py`

---

## Manual Commands

### Check Signals (Safe):
```bash
python live_trading.py --mode check
```

### Execute Trades (Requires Confirmation):
```bash
python live_trading.py --mode execute
```

### Monitor Positions:
```bash
python live_trading.py --mode monitor
```

### View Performance:
```bash
python -c "from performance_tracker import PerformanceTracker; t = PerformanceTracker(); print(t.generate_report())"
```

---

## Email Alert Examples

### Signal Alert:
```
Subject: 🚨 Trading Signal Alert - 2025-12-09 09:35

Active trading signals detected:

PAIR         REGIME           Z-SCORE  SIGNAL
SLV-SIVR     MEAN_REVERTING   -2.13    LONG
USO-XLE      VOLATILE          0.00    HOLD

Dry run mode: False
⚠️ LIVE MODE - Signals will auto-execute if scheduled!
```

### Daily Summary:
```
Subject: 📊 Daily Trading Summary - 2025-12-09

Current Signals:
...

Risk Metrics:
- Equity: $115.30
- Drawdown: -2.1%
- Leverage: 0.5x
- Open Positions: 1

Mode: LIVE TRADING
```

---

## Performance Reports

### Generate Report:
```python
from performance_tracker import PerformanceTracker

tracker = PerformanceTracker()
print(tracker.generate_report())
```

### Export to Excel:
```python
tracker.export_trades('my_trades.xlsx')
```

### Sample Report:
```
╔══════════════════════════════════════════════════════════════════╗
║                    TRADING PERFORMANCE REPORT                     ║
╚══════════════════════════════════════════════════════════════════╝

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

RISK METRICS
------------
Max Drawdown:        -$18.20
Avg Hold Time:       4.2 days

PAIR BREAKDOWN
--------------
SLV-SIVR     - Trades:   8 | Win Rate: 62.5% | P&L: $+85.20
USO-XLE      - Trades:   7 | Win Rate: 57.1% | P&L: $+42.30
```

---

## Monitoring & Logs

### Log Files:
- `scheduler.log` - Scheduler activity
- `live_trading.log` - Trade execution
- `trades.csv` - All completed trades
- `trading_bot.log` - General bot activity

### View Recent Activity:
```powershell
# Windows
Get-Content scheduler.log -Tail 50

# Linux/Mac
tail -f scheduler.log
```

---

## Safety Features

### Built-in Protections:
1. **Drawdown Limit**: Stops at 20% portfolio loss
2. **Leverage Limit**: Max 2x exposure
3. **Regime Filtering**: Only trades mean-reverting markets
4. **Position Limits**: Max 0.01 lots per trade
5. **Confirmation Required**: Manual approval for live execution

### Emergency Stop:
```bash
# Stop scheduler
Ctrl+C (in terminal)

# Close all positions
python live_trading.py --mode execute
# When prompted, it will show option to close all
```

---

## Troubleshooting

### Email Not Sending:
- Check SMTP credentials in `.env`
- For Gmail, use App Password (not account password)
- Check spam folder
- Enable "Less Secure App Access" (if not using App Password)

### Scheduler Not Running:
- Check system time zone (scheduler uses EST)
- Verify `schedule` library installed
- Check logs for errors

### Trades Not Executing:
- Verify `DRY_RUN=False` and `AUTO_EXECUTE=True`
- Check Capital.com API connection
- Ensure markets are open
- Check account balance

---

## Recommended Workflow

### Week 1-2: Paper Trading
```env
DRY_RUN=True
EMAIL_ALERTS=True
```
- Monitor signals via email
- Track hypothetical trades
- Verify strategy performs as expected

### Week 3-4: Manual Live Trading
```env
DRY_RUN=False
AUTO_EXECUTE=False
```
- Receive real signals
- Manually execute via `live_trading.py`
- Build confidence in system

### Month 2+: Automated (Optional)
```env
DRY_RUN=False
AUTO_EXECUTE=True
```
- Full automation
- Monitor daily summaries
- Intervene if performance degrades

---

## Next Steps

1. ✅ Configure `.env` with your preferences
2. ✅ Test email alerts: `python scheduler.py` (Ctrl+C after verification)
3. ✅ Run in dry-run mode for 1-2 weeks
4. ✅ Review performance reports
5. ✅ Gradually transition to live trading

**Remember**: Start small, monitor closely, and never risk more than you can afford to lose!
