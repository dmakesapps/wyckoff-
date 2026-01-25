# 7-Category Indicator Architecture

## Overview

We need to calculate 7 indicator categories for 7,000+ stocks efficiently.

### The Challenge
- **SMAs require historical data** (50-200 days per stock)
- **Yahoo Finance rate limits** after ~600 requests
- **Can't fetch history for 7,000 stocks** in 30 minutes

### The Solution: Two-Tier Scan System

```
┌─────────────────────────────────────────────────────────────┐
│                    FAST SCAN (Every 30 min)                  │
│                    ~15 seconds for 7,000 stocks              │
│                                                              │
│  Uses: Alpaca Snapshots                                      │
│  Gets: Price, Volume, Change, Market Cap                     │
│                                                              │
│  Calculates:                                                 │
│  ✅ Market Breadth (advancing/declining)                     │
│  ✅ Volume Analysis (relative volume, up/down volume)        │
│  ✅ Momentum (gainers/losers)                                │
│  ✅ Sector Performance (aggregated)                          │
│  ✅ Fear & Greed (composite score)                           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                 HISTORICAL SCAN (Once per day)               │
│                 Runs overnight or on-demand                  │
│                                                              │
│  Uses: Yahoo Finance (batched, with delays)                  │
│  Gets: 200 days of OHLCV data per stock                      │
│                                                              │
│  Calculates:                                                 │
│  ✅ 50-day SMA                                               │
│  ✅ 200-day SMA                                              │
│  ✅ 20-day High/Low (breakout detection)                     │
│  ✅ ATR (volatility)                                         │
│  ✅ RSI                                                      │
└─────────────────────────────────────────────────────────────┘
```

---

## Implementation Plan

### Phase 1: Enhance Fast Scan (Can do NOW)

These indicators can be calculated from Alpaca data:

| Indicator | How to Calculate | Data Source |
|-----------|------------------|-------------|
| **Market Breadth** | Count stocks with change > 0 vs < 0 | Alpaca |
| **Up Volume** | Sum volume of advancing stocks | Alpaca |
| **Down Volume** | Sum volume of declining stocks | Alpaca |
| **Volume Ratio** | Up Volume / Down Volume | Calculated |
| **Big Gainers** | Stocks with change > 5% | Alpaca |
| **Big Losers** | Stocks with change < -5% | Alpaca |
| **Sector Rankings** | Avg change per sector | Alpaca |
| **Fear & Greed** | Composite of above metrics | Calculated |

### Phase 2: Add Historical Cache (Daily)

Store daily OHLCV in SQLite, update incrementally:

```sql
CREATE TABLE daily_history (
    symbol TEXT,
    date TEXT,
    open REAL,
    high REAL,
    low REAL,
    close REAL,
    volume INTEGER,
    PRIMARY KEY (symbol, date)
);

CREATE TABLE technical_indicators (
    symbol TEXT PRIMARY KEY,
    sma_50 REAL,
    sma_200 REAL,
    above_sma_50 BOOLEAN,
    above_sma_200 BOOLEAN,
    rsi_14 REAL,
    atr_14 REAL,
    high_20d REAL,
    low_20d REAL,
    is_breakout BOOLEAN,
    is_breakdown BOOLEAN,
    updated_at TEXT
);
```

---

## Fear & Greed Index Calculation

Composite score from 0 (Extreme Fear) to 100 (Extreme Greed):

```python
def calculate_fear_greed():
    # Each component scored 0-100
    
    # 1. Market Breadth (25%)
    breadth_score = (advancing / total) * 100
    
    # 2. Volume (25%)
    volume_score = (up_volume / (up_volume + down_volume)) * 100
    
    # 3. Momentum (25%)
    gainers_ratio = gainers / (gainers + losers)
    momentum_score = gainers_ratio * 100
    
    # 4. Stocks above SMA (25%) - from historical cache
    sma_score = (above_sma_50 / total) * 100
    
    # Weighted average
    fear_greed = (
        breadth_score * 0.25 +
        volume_score * 0.25 +
        momentum_score * 0.25 +
        sma_score * 0.25
    )
    
    return round(fear_greed)
```

**Interpretation:**
- 0-25: Extreme Fear 😱
- 25-45: Fear 😟
- 45-55: Neutral 😐
- 55-75: Greed 😊
- 75-100: Extreme Greed 🤑

---

## Updated API Endpoints

### `/api/market/indicators`

Returns all 7 indicator categories:

```json
{
  "timestamp": "2026-01-25T16:45:00Z",
  "indicators": {
    "market_breadth": {
      "advancing": 2036,
      "declining": 3110,
      "unchanged": 139,
      "ad_ratio": 0.65,
      "ad_line": -1074
    },
    "sma_analysis": {
      "above_sma_50": 3200,
      "above_sma_200": 2800,
      "pct_above_50": 45.2,
      "pct_above_200": 39.5,
      "golden_cross_count": 45,
      "death_cross_count": 23
    },
    "volume_analysis": {
      "up_volume": 2500000000,
      "down_volume": 3200000000,
      "volume_ratio": 0.78,
      "unusual_volume_count": 156
    },
    "momentum": {
      "gainers_5pct": 299,
      "losers_5pct": 516,
      "new_20d_highs": 234,
      "new_20d_lows": 89
    },
    "sector_performance": [
      {"sector": "Technology", "change": 1.23, "advancing": 85},
      {"sector": "Healthcare", "change": -0.45, "advancing": 42}
    ],
    "volatility": {
      "high_vol_stocks": 456,
      "low_vol_stocks": 2345,
      "avg_atr_percent": 2.3
    },
    "fear_greed": {
      "score": 42,
      "label": "Fear",
      "components": {
        "breadth": 38,
        "volume": 44,
        "momentum": 37,
        "sma": 49
      }
    }
  }
}
```

---

## Implementation Timeline

| Phase | What | Time to Implement | Scan Time |
|-------|------|-------------------|-----------|
| **1** | Enhance fast scan with breadth, volume, momentum, fear/greed | 2-3 hours | 15 seconds |
| **2** | Add daily historical cache | 4-5 hours | Overnight batch |
| **3** | Add SMA & volatility from cache | 2-3 hours | 15 seconds (reads cache) |

---

## Answer to Your Question

**Can we update this frequently without issues?**

| Indicator | Update Frequency | Issues? |
|-----------|------------------|---------|
| Market Breadth | Every 30 min | ✅ No issues |
| Volume Analysis | Every 30 min | ✅ No issues |
| Momentum | Every 30 min | ✅ No issues |
| Sector Performance | Every 30 min | ✅ No issues |
| Fear & Greed | Every 30 min | ✅ No issues |
| **SMA Analysis** | **Once per day** | ⚠️ Needs historical cache |
| **Volatility** | **Once per day** | ⚠️ Needs historical cache |

**5 out of 7 indicators can update every 30 minutes with NO issues!**

The SMA and Volatility indicators need historical data, so they would update once per day (overnight batch), but the values don't change much intraday anyway - a 50-day SMA only changes by a tiny amount each day.

---

## Recommendation

**Start with Phase 1** - add the 5 instant indicators now. This gives you:
- ✅ Fear & Greed Index
- ✅ Market Breadth
- ✅ Volume Analysis
- ✅ Momentum
- ✅ Sector Performance

Then add Phase 2 (SMA/Volatility) as a follow-up when you need it.

Want me to implement Phase 1 now?

