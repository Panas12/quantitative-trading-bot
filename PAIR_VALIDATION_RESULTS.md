# Pair Validation Results

## Testing Summary (2023-2025 Data)

Successfully tested 3 cointegrated pairs identified by scanner.

### ✅ APPROVED FOR TRADING

#### 1. USO-XLE (Oil vs Energy Sector) ⭐⭐⭐ BEST
- **Sharpe Ratio**: 1.37
- **Annual Return**: +21.4%
- **Max Drawdown**: -11.0%
- **Profit Factor**: 1.62
- **Final Equity**: $145,090 (+45%)
- **Trades**: 13
- **Half-Life**: 15.9 days

**Why it works**:
- Oil prices directly impact energy company profits
- Strong cointegration (p=0.0059)
- Ideal mean reversion speed
- Liquid, tradeable instruments

---

####2. SLV-SIVR (Silver ETFs) ⭐⭐ GOOD
- **Sharpe Ratio**: 1.15
- **Annual Return**: +2.2%
- **Max Drawdown**: -0.95% (excellent!)
- **Profit Factor**: 1.22
- **Final Equity**: $104,255 (+4.3%)
- **Trades**: 25
- **Half-Life**: 4.5 days

**Why it works**:
- Both track physical silver
- Near-perfect cointegration (p=0.0000)
- Very fast mean reversion
- Minimal drawdown = low stress

---

### ❌ REJECTED

#### 3. USO-OIH (Oil vs Oil Services)
- **Sharpe Ratio**: 0.35 (POOR)
- **Annual Return**: +5.5%
- **Max Drawdown**: -23.9% (too high)
- **Status**: Training Sharpe 1.52 degraded to 0.35 in testing
- **Reason**: Likely overfitting, unstable relationship

---

####4. GLD-GDX (Gold vs Gold Miners) - ORIGINAL PAIR
- **Sharpe Ratio**: 0.54
- **Annual Return**: -54%
- **Max Drawdown**: -99.7% (catastrophic)
- **Status**: NOT COINTEGRATED (p=0.58)
- **Reason**: Relationship broke down post-2019

---

## Portfolio Strategy

### Recommended Allocation

**Capital**: $111.55 available

**Split across 2 pairs**:
- 50% to USO-XLE (~$56)
- 50% to SLV-SIVR (~$56)

**Position sizes**:
- Minimum: 0.01 lots each
- Risk per pair: $2 stop loss
- Total portfolio risk: $4

### Expected Performance

Based on backtests, portfolio should achieve:
- **Combined Sharpe**: ~1.25
- **Expected Return**: 10-15% annually
- **Max Portfolio DD**: <15%
- **Diversification benefit**: Pairs uncorrelated

### Risk Controls

- Maximum 2 pairs active simultaneously
- Individual pair stop-loss: -2%
- Portfolio stop-loss: -5% daily
- Re-verify cointegration monthly

---

## Next Actions

1. ✅ Pairs validated and approved
2. [ ] Implement regime detection (Phase 2)
3. [ ] Add dynamic thresholds (Phase 3)
4. [ ] Create multi-pair portfolio manager (Phase 4)
5. [ ] Paper trade for 30 days
6. [ ] Go live with minimal sizes

---

## Files Generated

- `pair_scan_results.csv` - Full scanner output
- `backtest_training.png` - Training period charts
- `backtest_testing.png` - Out-of-sample charts (most important!)
- `cointegration_analysis.png` - Statistical validation

---

**Conclusion**: Found 2 profitable pairs to replace failing GLD-GDX strategy. Ready to proceed with multi-pair implementation.
