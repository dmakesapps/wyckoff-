# Market Dashboard Backend Requirements

This document outlines what data your Python backend script needs to provide for the Market Dashboard indicators to accurately represent the **entire market** (all 7,000+ stocks).

---

## Overview

The Market Dashboard currently displays these indicators that need **market-wide data**:

| Indicator | Current Source | What It Needs |
|-----------|----------------|---------------|
| Advancing / Declining | `breadth.advancing`, `breadth.declining` | Count from ALL stocks |
| New 52W Highs / Lows | `breadth.new_highs`, `breadth.new_lows` | Count from ALL stocks |
| Above SMA 50 | `sma_analysis.sma50.above_percent` | % of ALL stocks above 50-day MA |
| Above SMA 200 | `sma_analysis.sma200.above_percent` | % of ALL stocks above 200-day MA |
| Fear & Greed Index | Calculated client-side from above | Needs accurate breadth + SMA data |
| Total Stocks | `stats.total_stocks` | Total count of stocks analyzed |

---

## Required API Response Structure

Your Python backend's `/api/market/overview` endpoint should return this structure:

```json
{
  "breadth": {
    "advancing": 2036,          // Number of stocks UP today (change_percent > 0)
    "declining": 3110,          // Number of stocks DOWN today (change_percent < 0)
    "unchanged": 139,           // Number of stocks with no change
    "total": 5285,              // Total stocks analyzed
    "advance_decline_ratio": 0.65,  // advancing / declining
    "advance_percent": 38.5,    // (advancing / total) * 100
    "decline_percent": 58.8,    // (declining / total) * 100
    "new_highs": 45,            // Stocks at new 52-week high
    "new_lows": 23              // Stocks at new 52-week low
  },
  "sma_analysis": {
    "sma50": {
      "above": 2880,            // Number of stocks trading ABOVE their 50-day SMA
      "below": 2405,            // Number of stocks trading BELOW their 50-day SMA
      "above_percent": 54.5     // (above / total) * 100
    },
    "sma200": {
      "above": 1623,            // Number of stocks trading ABOVE their 200-day SMA
      "below": 3662,            // Number of stocks trading BELOW their 200-day SMA
      "above_percent": 30.7     // (above / total) * 100
    }
  },
  "stats": {
    "total_stocks": 5285,       // CRITICAL: Total number of stocks in the dataset
    "unusual_volume_count": 127,
    "near_52w_high_count": 89,
    "big_gainers_count": 156,   // Stocks up > 5%
    "big_losers_count": 203,    // Stocks down > 5%
    "last_scan": "2024-01-24T18:00:00Z"
  },
  "updated_at": "2024-01-24T18:05:00Z"
}
```

---

## Python Implementation Guide

### 1. Calculating Market Breadth

```python
def calculate_market_breadth(all_stocks: list) -> dict:
    """
    Calculate market breadth from ALL stocks in the dataset.
    
    Args:
        all_stocks: List of stock dicts, each with 'change_percent', 
                   'price', 'week_52_high', 'week_52_low'
    
    Returns:
        dict with breadth metrics
    """
    total = len(all_stocks)
    
    advancing = sum(1 for s in all_stocks if s.get('change_percent', 0) > 0)
    declining = sum(1 for s in all_stocks if s.get('change_percent', 0) < 0)
    unchanged = total - advancing - declining
    
    # New 52-week highs/lows (stocks within 1% of their 52W high/low)
    new_highs = sum(1 for s in all_stocks 
                   if s.get('price', 0) >= s.get('week_52_high', float('inf')) * 0.99)
    new_lows = sum(1 for s in all_stocks 
                  if s.get('price', float('inf')) <= s.get('week_52_low', 0) * 1.01)
    
    return {
        "advancing": advancing,
        "declining": declining,
        "unchanged": unchanged,
        "total": total,
        "advance_decline_ratio": round(advancing / max(declining, 1), 2),
        "advance_percent": round((advancing / total) * 100, 1) if total > 0 else 0,
        "decline_percent": round((declining / total) * 100, 1) if total > 0 else 0,
        "new_highs": new_highs,
        "new_lows": new_lows
    }
```

### 2. Calculating SMA Analysis

```python
def calculate_sma_analysis(all_stocks: list) -> dict:
    """
    Calculate how many stocks are above/below their moving averages.
    
    Args:
        all_stocks: List of stock dicts, each with 'price', 'sma_50', 'sma_200'
                   (You need to fetch or calculate these SMAs)
    
    Returns:
        dict with SMA analysis
    """
    # Filter to stocks that have SMA data
    stocks_with_sma50 = [s for s in all_stocks if s.get('sma_50') is not None]
    stocks_with_sma200 = [s for s in all_stocks if s.get('sma_200') is not None]
    
    # SMA 50 analysis
    above_sma50 = sum(1 for s in stocks_with_sma50 if s['price'] > s['sma_50'])
    total_sma50 = len(stocks_with_sma50)
    
    # SMA 200 analysis
    above_sma200 = sum(1 for s in stocks_with_sma200 if s['price'] > s['sma_200'])
    total_sma200 = len(stocks_with_sma200)
    
    return {
        "sma50": {
            "above": above_sma50,
            "below": total_sma50 - above_sma50,
            "above_percent": round((above_sma50 / total_sma50) * 100, 1) if total_sma50 > 0 else 50
        },
        "sma200": {
            "above": above_sma200,
            "below": total_sma200 - above_sma200,
            "above_percent": round((above_sma200 / total_sma200) * 100, 1) if total_sma200 > 0 else 50
        }
    }
```

### 3. Getting SMA Data

If your data source (Finviz, etc.) doesn't provide SMA values directly, you have options:

#### Option A: Use Finviz Screener Filters
Finviz allows filtering by "Price above SMA50" and "Price above SMA200". You can run two separate scans:
- Scan 1: All stocks with `ta_sma50_pa` (price above SMA50) → count results
- Scan 2: All stocks with `ta_sma200_pa` (price above SMA200) → count results

```python
# Finviz filter examples
filters_above_sma50 = ['ta_sma50_pa']  # Price above SMA50
filters_above_sma200 = ['ta_sma200_pa']  # Price above SMA200
```

#### Option B: Calculate from Historical Data
If you have access to historical price data (e.g., via yfinance):

```python
import yfinance as yf
import pandas as pd

def get_sma_data(symbol: str) -> dict:
    """Get current price vs SMAs for a single stock."""
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
            "sma_200": sma_200
        }
    except:
        return None
```

#### Option C: Use a Pre-built Market Breadth API
Services like:
- **Barchart.com** - Has market breadth data
- **StockCharts.com** - Provides breadth indicators
- **CBOE** - For VIX and put/call ratios
- **FinViz** - Can filter by technical indicators

---

## Fear & Greed Index (Optional Server-Side Calculation)

You can optionally calculate the Fear & Greed index on the backend:

```python
def calculate_fear_greed(breadth: dict, sma_analysis: dict) -> dict:
    """
    Calculate Fear & Greed index (0-100 scale).
    
    Components (each 0-25 points):
    1. Advance/Decline % (50% = 12.5 pts, 70%+ = 25 pts, 30%- = 0 pts)
    2. % Above SMA 50 (same scale)
    3. % Above SMA 200 (same scale)
    4. New Highs/Lows ratio (1:1 = 12.5 pts, 3:1+ = 25 pts, 1:3- = 0 pts)
    """
    score = 0
    
    # Factor 1: Advance/Decline (0-25 points)
    adv_pct = breadth.get('advance_percent', 50)
    score += min(25, max(0, (adv_pct - 30) * 0.625))
    
    # Factor 2: Above SMA 50 (0-25 points)
    sma50_pct = sma_analysis.get('sma50', {}).get('above_percent', 50)
    score += min(25, max(0, (sma50_pct - 30) * 0.625))
    
    # Factor 3: Above SMA 200 (0-25 points)
    sma200_pct = sma_analysis.get('sma200', {}).get('above_percent', 50)
    score += min(25, max(0, (sma200_pct - 30) * 0.625))
    
    # Factor 4: New Highs/Lows ratio (0-25 points)
    highs = breadth.get('new_highs', 0)
    lows = breadth.get('new_lows', 1) or 1
    hl_ratio = highs / lows
    score += min(25, max(0, (hl_ratio - 0.33) * 9.375))
    
    final_score = round(score)
    
    # Determine label
    if final_score >= 75:
        label = "Extreme Greed"
    elif final_score >= 55:
        label = "Greed"
    elif final_score >= 45:
        label = "Neutral"
    elif final_score >= 25:
        label = "Fear"
    else:
        label = "Extreme Fear"
    
    return {
        "score": final_score,
        "label": label,
        "components": {
            "advance_decline": adv_pct,
            "sma50": sma50_pct,
            "sma200": sma200_pct,
            "high_low_ratio": round(hl_ratio, 2)
        }
    }
```

---

## Complete Example: Flask Endpoint

```python
from flask import Flask, jsonify
from finvizfinance.screener.overview import Overview

app = Flask(__name__)

@app.route('/api/market/overview')
def market_overview():
    # 1. Fetch ALL stocks from Finviz (or your data source)
    screener = Overview()
    screener.set_filter(filters_dict={})  # No filters = all stocks
    all_stocks = screener.screener_view()  # Returns DataFrame
    
    # Convert to list of dicts
    stocks_list = all_stocks.to_dict('records')
    
    # 2. Calculate breadth metrics
    breadth = calculate_market_breadth(stocks_list)
    
    # 3. Calculate SMA analysis
    # (This requires SMA data - see Options A/B/C above)
    sma_analysis = calculate_sma_analysis(stocks_list)
    
    # 4. Calculate Fear & Greed
    fear_greed = calculate_fear_greed(breadth, sma_analysis)
    
    # 5. Build response
    response = {
        "breadth": breadth,
        "sma_analysis": sma_analysis,
        "stats": {
            "total_stocks": len(stocks_list),
            "last_scan": datetime.now().isoformat()
        },
        "fear_greed": fear_greed,
        "updated_at": datetime.now().isoformat()
    }
    
    return jsonify(response)
```

---

## Data Sources for Market-Wide Stats

| Data Point | Possible Sources |
|------------|------------------|
| All stock prices & changes | Finviz, Yahoo Finance, Polygon.io, Alpha Vantage |
| SMA 50/200 indicators | Finviz filters, Yahoo Finance, TradingView |
| New 52W Highs/Lows | Finviz (`ta_highlow52w_nh`, `ta_highlow52w_nl`) |
| Put/Call Ratio | CBOE, Barchart |
| VIX (Volatility Index) | Yahoo Finance (`^VIX`), CBOE |
| Market breadth (A/D Line) | Barchart, StockCharts |

---

## Summary Checklist

To make the Market Dashboard show accurate market-wide stats, your backend needs to:

- [ ] Fetch data for **ALL stocks** (not just top gainers/losers)
- [ ] Calculate `breadth.advancing` and `breadth.declining` from all stocks
- [ ] Calculate `breadth.new_highs` and `breadth.new_lows` from all stocks
- [ ] Calculate `sma_analysis.sma50.above_percent` for all stocks
- [ ] Calculate `sma_analysis.sma200.above_percent` for all stocks
- [ ] Include `stats.total_stocks` with the actual count
- [ ] Optionally: Calculate `fear_greed` server-side for consistency

---

## Questions?

If you need help implementing any of these calculations in your Python script, let me know and I can provide more detailed code examples!
