# ETF Rotation Strategy

## Overview

This strategy implements a **factor-based ETF rotation** system that dynamically allocates capital to the highest-scoring ETF from a predefined pool. Multiple factors are evaluated, including trend strength, momentum, and risk-adjusted metrics. A dynamic drawdown-based risk control mechanism is incorporated to enhance performance and reduce tail risk.

---

## Strategy Logic

### 1. Asset Universe

The strategy rotates among the following ETFs:

| ETF | Ticker | Asset Class |
|-----|--------|-------------|
| 红利ETF (Dividend ETF) | 510880.SH | Domestic Equity - Dividend |
| 创业板ETF (ChiNext ETF) | 519915.SH | Domestic Equity - Growth |
| 沪深300ETF (CSI 300 ETF) | 510300.SH | Domestic Equity - Large Cap |
| 黄金ETF (Gold ETF) | 518880.SH | Commodity - Precious Metal |

---

### 2. Scoring Factors

#### (a) Trend Score

| Component | Description |
|-----------|-------------|
| **slope** | Linear regression slope of multi-day closing prices |
| **R²** | Coefficient of determination (trend stability) |
| **e^(252 × slope) - 1** | Annualized trend strength |

This factor rewards ETFs with **strong** and **stable** price trends.

#### (b) Momentum Factors

| Variant | Data Used |
|---------|-----------|
| `momentum_close` | Closing price momentum |
| `momentum_open` | Opening price momentum |

#### (c) Risk-Off Adjusted Trend Score

Adjusts the trend score by incorporating:
- Volatility (penalizes high volatility)
- Turnover stability (rewards consistent trading volume)

#### (d) Sharpe Momentum

Combines price momentum with volatility adjustment for risk-aware positioning.

---

### 3. Trading Logic

#### Signal Generation (Daily after close)

1. Calculate factor scores for all 4 ETFs using end-of-day data
2. Rank ETFs by factor score
3. Generate signal: **Go long the highest-scoring ETF**
4. Hold **100% allocation** to the selected ETF

#### Execution (Next day at open)

1. Close existing position at opening price
2. Open new position in the target ETF at opening price

#### Portfolio Valuation (Daily at close)

All positions are marked-to-market using closing prices.

---

### 4. Dynamic Risk Control Enhancement

**Trigger Condition:**

1. Track historical portfolio drawdown sequence
2. If **3 consecutive days** of new drawdowns exceed the **95th percentile** of historical drawdowns:
   - **Force liquidate** all positions at next open
   - Enter a **3-day cooling period**
   - Resume normal rotation after cooling period

**Purpose:**

- Prevents prolonged drawdown periods
- Reduces maximum drawdown and improves Calmar ratio
- Preserves capital during extreme market stress

---

## Performance Results

### 1. Pre-Optimization Results

**Parameters:**
- Transaction fee: 0.05% (万0.5)
- Slippage: 0.5%
- Initial capital: ¥1,000,000

| Factor | CAGR | Volatility | Sharpe | MDD | Calmar |
|--------|------|------------|--------|-----|--------|
| trend_score | 33.31% | 26.09% | 1.275 | -30.72% | 1.084 |
| trend_score_riskoff | 29.30% | 25.37% | 1.180 | -35.50% | 0.825 |
| sharpe_momentum | 27.41% | 24.70% | 1.141 | -27.45% | 0.998 |
| momentum_close | 32.12% | 26.41% | 1.227 | -27.77% | 1.157 |
| momentum_open | 29.61% | 27.02% | 1.131 | -28.50% | 1.039 |

---

### 2. Post-Optimization Results

**Enhanced with Drawdown-Based Risk Control (95th percentile threshold + 3-day cooling)**

| Factor | CAGR | Volatility | Sharpe | MDD | Calmar |
|--------|------|------------|--------|-----|--------|
| trend_score | 34.21% | 25.39% | 1.33 | -23.71% | 1.44 |
| trend_score_riskoff | 27.70% | 24.81% | 1.15 | -31.60% | 0.88 |
| sharpe_momentum | 24.29% | 24.09% | 1.06 | -25.20% | 0.96 |
| momentum_close | 21.57% | 24.78% | 0.94 | -49.54% | 0.44 |
| momentum_open | 28.43% | 26.58% | 1.11 | -27.06% | 1.05 |

---

### 3. Performance Comparison

| Factor | CAGR Change | MDD Change | Calmar Change | Result |
|--------|-------------|------------|---------------|--------|
| **trend_score** | +0.90% | -7.01% | +0.356 | ✅ Improved |
| trend_score_riskoff | -1.60% | -3.90% | +0.055 | Mixed |
| sharpe_momentum | -3.12% | -2.25% | -0.038 | Degraded |
| momentum_close | -10.55% | +21.77% | -0.717 | ❌ Degraded |
| momentum_open | -1.18% | -1.44% | +0.011 | Mixed |

---

## Results Analysis

### Factor Performance Ranking

| Rank | Factor | Key Strengths | Weaknesses |
|------|--------|---------------|------------|
| 1 | **trend_score** | Highest CAGR, best Sharpe, best Calmar, lowest MDD after optimization | None significant |
| 2 | momentum_close | Strong CAGR pre-optimization | Vulnerable to drawdown; degraded with risk control |
| 3 | momentum_open | Consistent moderate performance | Average across all metrics |
| 4 | sharpe_momentum | Stable volatility | Lower returns, poor Calmar |
| 5 | trend_score_riskoff | Risk-aware construction | Highest MDD, lowest Calmar |

### Key Observations

1. **trend_score is the superior factor**
   - Combines trend strength (slope) with trend quality (R²)
   - Benefits most from dynamic risk control
   - Best risk-adjusted returns across all metrics

2. **Risk control enhancement is factor-dependent**
   - Works well for factors with strong trend persistence (trend_score)
   - Hurts factors that rely on frequent re-entry (momentum_close)
   - Cooling periods can cause momentum strategies to miss recoveries

3. **Dynamic drawdown control effectively reduces tail risk**
   - trend_score MDD reduced from -30.72% to -23.71%
   - Calmar ratio improved from 1.08 to 1.44
   - Protects capital during extreme market stress

4. **Risk-off adjustment did not improve performance**
   - Volatility and turnover adjustments added noise
   - Trend quality (R²) already captures stability

---

## Risk Management

### Position-Level Risk

| Control | Description |
|---------|-------------|
| **Full Allocation** | 100% of capital in top-scoring ETF |
| **Daily Rebalancing** | Signal generated daily, executed next open |

### Portfolio-Level Risk (Enhanced)

| Control | Threshold | Action |
|---------|-----------|--------|
| **Drawdown Watch** | 3 consecutive days of new drawdowns | Trigger risk control |
| **Extreme Drawdown** | > 95th percentile historical | Force liquidation |
| **Cooling Period** | 3 days | No trading during cooling |
