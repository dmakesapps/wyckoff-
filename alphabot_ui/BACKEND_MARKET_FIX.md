# 🚨 CRITICAL: Market Indicators Backend Fix

## Problem Summary

The `/api/market/overview` endpoint is returning **incorrect absolute stock counts** while the percentages appear correct. This indicates the calculations are being performed on a **subset of ~50-100 stocks** instead of the **full 5,000+ stock universe**.

### Current Bug Evidence:
| Metric | Shows | Expected (5,285 stocks) | Issue |
|--------|-------|------------------------|-------|
| Above SMA 50 | 54.5% / **48 stocks** | 54.5% / **~2,880 stocks** | ❌ Wrong count |
| Above SMA 200 | 30.7% / **27 stocks** | 30.7% / **~1,620 stocks** | ❌ Wrong count |
| New 52W Highs | **4 stocks** | **~45+ stocks** | ❌ Wrong count |
| New 52W Lows | **2 stocks** | **~23+ stocks** | ❌ Wrong count |

**Root Cause:** The SMA and 52W high/low calculations are likely running on a filtered subset (e.g., top gainers/losers only) instead of the full stock dataset.

---

## Required Fix

### Step 1: Ensure ALL Stocks Are Fetched

The market overview endpoint **MUST** analyze all stocks in the dataset. If you're fetching from Finviz or another source, ensure no limiting filters are applied:

```python
# ❌ WRONG - This only gets a subset
stocks = get_top_gainers(limit=50) + get_top_losers(limit=50)

# ✅ CORRECT - Get ALL stocks
stocks = get_all_stocks()  # Should return 5,000-7,000+ stocks
```

### Step 2: Calculate Metrics from Full Dataset

All breadth metrics **MUST** iterate over the complete stock list:

```python
def calculate_market_overview(all_stocks: list) -> dict:
    """
    Calculate market overview from the COMPLETE stock universe.
    
    Args:
        all_stocks: List of ALL stocks (5,000-7,000+), each with:
            - symbol: str
            - price: float (current price)
            - change_percent: float (today's % change)
            - week_52_high: float
            - week_52_low: float
            - sma_50: float (50-day simple moving average)
            - sma_200: float (200-day simple moving average)
            - volume: int
            - avg_volume: float (average volume)
    """
    total = len(all_stocks)
    
    # ========== MARKET BREADTH ==========
    advancing = sum(1 for s in all_stocks if s.get('change_percent', 0) > 0)
    declining = sum(1 for s in all_stocks if s.get('change_percent', 0) < 0)
    unchanged = total - advancing - declining
    
    # ========== 52-WEEK HIGHS/LOWS ==========
    # Stock is at 52W high if within 1% of the high
    new_highs = sum(1 for s in all_stocks 
                   if s.get('price', 0) >= s.get('week_52_high', float('inf')) * 0.99)
    # Stock is at 52W low if within 1% of the low
    new_lows = sum(1 for s in all_stocks 
                  if s.get('price', float('inf')) <= s.get('week_52_low', 0) * 1.01)
    
    # ========== SMA ANALYSIS (from ALL stocks) ==========
    stocks_with_sma50 = [s for s in all_stocks if s.get('sma_50') is not None]
    stocks_with_sma200 = [s for s in all_stocks if s.get('sma_200') is not None]
    
    above_sma50 = sum(1 for s in stocks_with_sma50 if s['price'] > s['sma_50'])
    above_sma200 = sum(1 for s in stocks_with_sma200 if s['price'] > s['sma_200'])
    
    total_sma50 = len(stocks_with_sma50)
    total_sma200 = len(stocks_with_sma200)
    
    return {
        "breadth": {
            "advancing": advancing,  # MUST be ~2000+ not ~40
            "declining": declining,  # MUST be ~3000+ not ~50
            "unchanged": unchanged,
            "total": total,          # MUST be 5000+
            "advance_decline_ratio": round(advancing / max(declining, 1), 2),
            "advance_percent": round((advancing / total) * 100, 1) if total > 0 else 0,
            "decline_percent": round((declining / total) * 100, 1) if total > 0 else 0,
            "new_highs": new_highs,  # MUST be counting ALL stocks, not subset
            "new_lows": new_lows     # MUST be counting ALL stocks, not subset
        },
        "sma_analysis": {
            "sma50": {
                "above": above_sma50,  # MUST match the percentage * total
                "below": total_sma50 - above_sma50,
                "above_percent": round((above_sma50 / total_sma50) * 100, 1) if total_sma50 > 0 else 50
            },
            "sma200": {
                "above": above_sma200,  # MUST match the percentage * total
                "below": total_sma200 - above_sma200,
                "above_percent": round((above_sma200 / total_sma200) * 100, 1) if total_sma200 > 0 else 50
            }
        },
        "stats": {
            "total_stocks": total  # CRITICAL: Must be 5000+
        }
    }
```

---

## Complete Market Indicators to Implement

The following indicators are **essential for traders** and should be included in the `/api/market/overview` response:

### 1. Market Breadth (REQUIRED - FIX NEEDED)
```json
{
  "breadth": {
    "advancing": 2036,
    "declining": 3110,
    "unchanged": 139,
    "total": 5285,
    "advance_decline_ratio": 0.65,
    "advance_percent": 38.5,
    "decline_percent": 58.8,
    "new_highs": 45,
    "new_lows": 23
  }
}
```

### 2. SMA Analysis (REQUIRED - FIX NEEDED)
```json
{
  "sma_analysis": {
    "sma50": {
      "above": 2880,
      "below": 2405,
      "above_percent": 54.5
    },
    "sma200": {
      "above": 1623,
      "below": 3662,
      "above_percent": 30.7
    }
  }
}
```

### 3. Volume Analysis (NEW - ADD THIS)
```python
def calculate_volume_metrics(all_stocks: list) -> dict:
    """Volume-based market indicators."""
    
    # Unusual volume = stocks trading 2x+ their average
    unusual_volume = [s for s in all_stocks 
                     if s.get('volume', 0) > s.get('avg_volume', 1) * 2]
    
    # Up on high volume (bullish)
    up_volume = sum(1 for s in all_stocks 
                   if s.get('change_percent', 0) > 0 
                   and s.get('volume', 0) > s.get('avg_volume', 1) * 1.5)
    
    # Down on high volume (bearish)
    down_volume = sum(1 for s in all_stocks 
                     if s.get('change_percent', 0) < 0 
                     and s.get('volume', 0) > s.get('avg_volume', 1) * 1.5)
    
    return {
        "unusual_volume_count": len(unusual_volume),
        "up_on_volume": up_volume,
        "down_on_volume": down_volume,
        "volume_ratio": round(up_volume / max(down_volume, 1), 2)
    }
```

**Response structure:**
```json
{
  "volume_analysis": {
    "unusual_volume_count": 127,
    "up_on_volume": 456,
    "down_on_volume": 678,
    "volume_ratio": 0.67
  }
}
```

### 4. Momentum Indicators (NEW - ADD THIS)
```python
def calculate_momentum_metrics(all_stocks: list) -> dict:
    """Momentum-based market indicators for traders."""
    
    total = len(all_stocks)
    
    # Big movers (stocks moving 5%+)
    big_gainers = sum(1 for s in all_stocks if s.get('change_percent', 0) >= 5)
    big_losers = sum(1 for s in all_stocks if s.get('change_percent', 0) <= -5)
    
    # Medium movers (2-5%)
    moderate_gainers = sum(1 for s in all_stocks if 2 <= s.get('change_percent', 0) < 5)
    moderate_losers = sum(1 for s in all_stocks if -5 < s.get('change_percent', 0) <= -2)
    
    # Stocks breaking out (new 20-day high)
    breakouts = sum(1 for s in all_stocks 
                   if s.get('price', 0) >= s.get('high_20d', float('inf')) * 0.99)
    
    # Stocks breaking down (new 20-day low)
    breakdowns = sum(1 for s in all_stocks 
                    if s.get('price', float('inf')) <= s.get('low_20d', 0) * 1.01)
    
    return {
        "big_gainers": big_gainers,
        "big_losers": big_losers,
        "moderate_gainers": moderate_gainers,
        "moderate_losers": moderate_losers,
        "breakouts_20d": breakouts,
        "breakdowns_20d": breakdowns,
        "momentum_score": round(((big_gainers - big_losers) / max(total, 1)) * 100, 2)
    }
```

**Response structure:**
```json
{
  "momentum": {
    "big_gainers": 156,
    "big_losers": 203,
    "moderate_gainers": 412,
    "moderate_losers": 567,
    "breakouts_20d": 89,
    "breakdowns_20d": 134,
    "momentum_score": -0.89
  }
}
```

### 5. Sector Performance (NEW - ADD THIS)
```python
def calculate_sector_performance(all_stocks: list) -> list:
    """Calculate performance by sector."""
    from collections import defaultdict
    
    sectors = defaultdict(lambda: {"stocks": [], "changes": []})
    
    for stock in all_stocks:
        sector = stock.get('sector', 'Unknown')
        sectors[sector]["stocks"].append(stock)
        sectors[sector]["changes"].append(stock.get('change_percent', 0))
    
    result = []
    for sector, data in sectors.items():
        changes = data["changes"]
        stocks = data["stocks"]
        
        advancing = sum(1 for c in changes if c > 0)
        
        result.append({
            "sector": sector,
            "stock_count": len(stocks),
            "avg_change": round(sum(changes) / len(changes), 2) if changes else 0,
            "percent_advancing": round((advancing / len(stocks)) * 100, 1) if stocks else 0,
            "best_performer": max(stocks, key=lambda x: x.get('change_percent', 0))['symbol'] if stocks else None,
            "worst_performer": min(stocks, key=lambda x: x.get('change_percent', 0))['symbol'] if stocks else None
        })
    
    # Sort by average change
    result.sort(key=lambda x: x['avg_change'], reverse=True)
    
    return result
```

**Response structure:**
```json
{
  "sectors": [
    {
      "sector": "Technology",
      "stock_count": 842,
      "avg_change": 1.23,
      "percent_advancing": 62.4,
      "best_performer": "NVDA",
      "worst_performer": "INTC"
    },
    {
      "sector": "Healthcare",
      "stock_count": 678,
      "avg_change": -0.45,
      "percent_advancing": 41.2,
      "best_performer": "LLY",
      "worst_performer": "PFE"
    }
  ]
}
```

### 6. Market Volatility (NEW - ADD THIS)
```python
def calculate_volatility_metrics(all_stocks: list) -> dict:
    """Calculate volatility-based market indicators."""
    
    total = len(all_stocks)
    changes = [abs(s.get('change_percent', 0)) for s in all_stocks]
    
    # Average absolute change (market volatility proxy)
    avg_volatility = sum(changes) / len(changes) if changes else 0
    
    # High volatility stocks (moving 3%+ either direction)
    high_vol_count = sum(1 for c in changes if c >= 3)
    
    # Low volatility stocks (moving less than 0.5%)
    low_vol_count = sum(1 for c in changes if c < 0.5)
    
    return {
        "avg_absolute_change": round(avg_volatility, 2),
        "high_volatility_stocks": high_vol_count,
        "low_volatility_stocks": low_vol_count,
        "high_vol_percent": round((high_vol_count / total) * 100, 1) if total > 0 else 0,
        "market_volatility_level": "High" if avg_volatility > 2 else "Normal" if avg_volatility > 1 else "Low"
    }
```

**Response structure:**
```json
{
  "volatility": {
    "avg_absolute_change": 1.67,
    "high_volatility_stocks": 423,
    "low_volatility_stocks": 1234,
    "high_vol_percent": 8.0,
    "market_volatility_level": "Normal"
  }
}
```

### 7. Fear & Greed Index (KEEP - Already calculated on frontend, but add backend version)
```python
def calculate_fear_greed(breadth: dict, sma_analysis: dict, momentum: dict) -> dict:
    """
    Composite Fear & Greed Index (0-100 scale).
    
    Components:
    - Market Breadth (Advance/Decline): 25%
    - SMA 50 Positioning: 20%
    - SMA 200 Positioning: 20%
    - New Highs vs Lows: 20%
    - Momentum (Big Gainers vs Losers): 15%
    """
    score = 0
    
    # 1. Advance/Decline (0-25 points)
    adv_pct = breadth.get('advance_percent', 50)
    score += min(25, max(0, (adv_pct - 30) * 0.625))
    
    # 2. SMA 50 (0-20 points)
    sma50_pct = sma_analysis.get('sma50', {}).get('above_percent', 50)
    score += min(20, max(0, (sma50_pct - 30) * 0.5))
    
    # 3. SMA 200 (0-20 points)
    sma200_pct = sma_analysis.get('sma200', {}).get('above_percent', 50)
    score += min(20, max(0, (sma200_pct - 30) * 0.5))
    
    # 4. High/Low Ratio (0-20 points)
    highs = breadth.get('new_highs', 0)
    lows = breadth.get('new_lows', 1) or 1
    hl_ratio = highs / lows
    score += min(20, max(0, (hl_ratio - 0.33) * 7.5))
    
    # 5. Momentum (0-15 points)
    big_gainers = momentum.get('big_gainers', 0)
    big_losers = momentum.get('big_losers', 1) or 1
    mom_ratio = big_gainers / big_losers
    score += min(15, max(0, (mom_ratio - 0.5) * 15))
    
    final_score = round(score)
    
    # Determine sentiment label
    if final_score >= 75:
        label = "Extreme Greed"
        color = "#00ff85"
    elif final_score >= 55:
        label = "Greed"
        color = "#22c55e"
    elif final_score >= 45:
        label = "Neutral"
        color = "#6b7280"
    elif final_score >= 25:
        label = "Fear"
        color = "#f59e0b"
    else:
        label = "Extreme Fear"
        color = "#ff3366"
    
    return {
        "score": final_score,
        "label": label,
        "color": color,
        "components": {
            "advance_decline": round(adv_pct, 1),
            "sma50_above": round(sma50_pct, 1),
            "sma200_above": round(sma200_pct, 1),
            "high_low_ratio": round(hl_ratio, 2),
            "momentum_ratio": round(mom_ratio, 2)
        }
    }
```

---

## Complete API Response Structure

The `/api/market/overview` endpoint should return:

```json
{
  "breadth": {
    "advancing": 2036,
    "declining": 3110,
    "unchanged": 139,
    "total": 5285,
    "advance_decline_ratio": 0.65,
    "advance_percent": 38.5,
    "decline_percent": 58.8,
    "new_highs": 45,
    "new_lows": 23
  },
  "sma_analysis": {
    "sma50": {
      "above": 2880,
      "below": 2405,
      "above_percent": 54.5
    },
    "sma200": {
      "above": 1623,
      "below": 3662,
      "above_percent": 30.7
    }
  },
  "volume_analysis": {
    "unusual_volume_count": 127,
    "up_on_volume": 456,
    "down_on_volume": 678,
    "volume_ratio": 0.67
  },
  "momentum": {
    "big_gainers": 156,
    "big_losers": 203,
    "moderate_gainers": 412,
    "moderate_losers": 567,
    "breakouts_20d": 89,
    "breakdowns_20d": 134,
    "momentum_score": -0.89
  },
  "volatility": {
    "avg_absolute_change": 1.67,
    "high_volatility_stocks": 423,
    "low_volatility_stocks": 1234,
    "high_vol_percent": 8.0,
    "market_volatility_level": "Normal"
  },
  "fear_greed": {
    "score": 37,
    "label": "Fear",
    "color": "#f59e0b",
    "components": {
      "advance_decline": 38.5,
      "sma50_above": 54.5,
      "sma200_above": 30.7,
      "high_low_ratio": 1.96,
      "momentum_ratio": 0.77
    }
  },
  "sectors": [
    {
      "sector": "Technology",
      "stock_count": 842,
      "avg_change": 1.23,
      "percent_advancing": 62.4
    }
  ],
  "stats": {
    "total_stocks": 5285,
    "unusual_volume_count": 127,
    "near_52w_high_count": 89,
    "big_gainers_count": 156,
    "big_losers_count": 203,
    "last_scan": "2024-01-25T08:46:00Z"
  },
  "updated_at": "2024-01-25T08:50:00Z"
}
```

---

## Validation Checklist

After implementing the fix, verify these conditions:

- [ ] `stats.total_stocks` equals 5,000+ (the full stock universe)
- [ ] `breadth.advancing + breadth.declining + breadth.unchanged` equals `stats.total_stocks`
- [ ] `sma_analysis.sma50.above + sma_analysis.sma50.below` is close to `stats.total_stocks`
- [ ] `sma_analysis.sma50.above` equals `sma_analysis.sma50.above_percent` × total ÷ 100
- [ ] `sma_analysis.sma200.above` equals `sma_analysis.sma200.above_percent` × total ÷ 100
- [ ] `breadth.new_highs` is reasonable (typically 20-100+ stocks daily)
- [ ] `breadth.new_lows` is reasonable (typically 10-50+ stocks daily)

---

## Data Sources

If you need SMA data and your primary source doesn't provide it:

### Option 1: Finviz Filters
```python
from finvizfinance.screener.overview import Overview

# Count stocks above SMA 50
screener_sma50 = Overview()
screener_sma50.set_filter(filters_dict={'ta_sma50_pa': 'Price above SMA50'})
above_sma50_count = len(screener_sma50.screener_view())

# Count stocks above SMA 200
screener_sma200 = Overview()
screener_sma200.set_filter(filters_dict={'ta_sma200_pa': 'Price above SMA200'})
above_sma200_count = len(screener_sma200.screener_view())
```

### Option 2: Barchart API
Barchart provides pre-calculated market breadth data.

### Option 3: Calculate from Yahoo Finance Historical Data
```python
import yfinance as yf

def get_stock_sma_data(symbol: str) -> dict:
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="1y")
        
        if len(hist) < 200:
            return None
            
        current_price = hist['Close'].iloc[-1]
        sma_50 = hist['Close'].rolling(window=50).mean().iloc[-1]
        sma_200 = hist['Close'].rolling(window=200).mean().iloc[-1]
        
        return {
            "price": current_price,
            "sma_50": sma_50,
            "sma_200": sma_200,
            "above_sma50": current_price > sma_50,
            "above_sma200": current_price > sma_200
        }
    except:
        return None
```

---

## Summary

**The critical fix is ensuring all metrics are calculated from the FULL stock universe (5,000+ stocks), not a subset of 50-100 stocks.**

The absolute counts (`above`, `below`, `new_highs`, `new_lows`) must mathematically match the percentages when multiplied by the total stock count.
