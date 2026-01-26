# AlphaBot System Roadmap
## World-Class Financial Intelligence Platform

**Version:** 1.0  
**Created:** January 2026  
**Goal:** Build a self-improving AI trading assistant that learns from investor wisdom, provides real-time market intelligence, and can be programmed through natural conversation.

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Architecture Overview](#architecture-overview)
3. [Phase 1: Polygon Integration](#phase-1-polygon-integration)
4. [Phase 2: RAG Knowledge System](#phase-2-rag-knowledge-system)
5. [Phase 3: Clawdbot Mobile Interface](#phase-3-clawdbot-mobile-interface)
6. [Phase 4: Self-Improving Algorithm](#phase-4-self-improving-algorithm)
7. [Technical Specifications](#technical-specifications)
8. [Cost Analysis](#cost-analysis)
9. [Success Metrics](#success-metrics)

---

## Executive Summary

### The Vision

Build a **personal Bloomberg Terminal** powered by AI that:
- Scans the entire market in real-time
- Thinks like legendary investors (Livermore, Buffett, Dalio)
- Learns from your trades and feedback
- Can be programmed by talking to it
- Accessible from your phone via text messages

### Current State vs. Future State

| Aspect | Current (Messy) | Future (Clean) |
|--------|-----------------|----------------|
| **Data Sources** | 3 APIs with fallbacks (Alpaca, Yahoo, IEX) | 1 API (Polygon) |
| **Codebase** | ~20,000 lines with workarounds | ~5,000 lines, clean |
| **AI Accuracy** | Inconsistent (data gaps → hallucinations) | Reliable (complete data) |
| **Knowledge** | None (just raw data) | RAG with investor wisdom |
| **Access** | Web UI only | Web + Mobile + Voice |
| **Improvement** | Manual code changes | Chat-based programming |

### Timeline

```
Week 1-2:   Phase 1 - Polygon Integration (Foundation)
Week 3-5:   Phase 2 - RAG Knowledge System (Intelligence)
Week 6-7:   Phase 3 - Clawdbot Mobile Interface (Access)
Week 8+:    Phase 4 - Self-Improving Algorithm (Evolution)
```

### Monthly Cost

| Service | Cost |
|---------|------|
| Polygon.io (Stocks Starter) | $79/mo |
| Pinecone (Vector DB) | $0-25/mo |
| OpenRouter (Kimi) | ~$10-20/mo |
| Server (Railway/Render) | $0-20/mo |
| **Total** | **~$100-150/mo** |

---

## Architecture Overview

### System Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           USER INTERFACES                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                │
│   │   Web UI    │    │  Mobile     │    │   Voice     │                │
│   │  (React)    │    │ (iMessage/  │    │  (Future)   │                │
│   │             │    │  Telegram)  │    │             │                │
│   └──────┬──────┘    └──────┬──────┘    └──────┬──────┘                │
│          │                  │                  │                        │
│          └──────────────────┼──────────────────┘                        │
│                             ↓                                           │
├─────────────────────────────────────────────────────────────────────────┤
│                         AGENT LAYER                                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   ┌─────────────────────────────────────────────────────────────┐      │
│   │                      CLAWDBOT AGENT                          │      │
│   │                                                              │      │
│   │  • Receives messages from any interface                      │      │
│   │  • Routes to appropriate tools                               │      │
│   │  • Can modify code via GitHub                                │      │
│   │  • Sends responses back to user                              │      │
│   └─────────────────────────────────────────────────────────────┘      │
│                             ↓                                           │
├─────────────────────────────────────────────────────────────────────────┤
│                      INTELLIGENCE LAYER                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   ┌──────────────────┐    ┌──────────────────┐                         │
│   │   KIMI LLM       │    │   RAG SYSTEM     │                         │
│   │                  │    │                  │                         │
│   │  • Analysis      │←──→│  • Vector DB     │                         │
│   │  • Reasoning     │    │  • Books/PDFs    │                         │
│   │  • Tool calling  │    │  • Trade history │                         │
│   │  • Responses     │    │  • Strategies    │                         │
│   └────────┬─────────┘    └──────────────────┘                         │
│            ↓                                                            │
├─────────────────────────────────────────────────────────────────────────┤
│                         DATA LAYER                                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   ┌─────────────────────────────────────────────────────────────┐      │
│   │                      POLYGON.IO                              │      │
│   │                                                              │      │
│   │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐           │      │
│   │  │ Quotes  │ │ Bars    │ │ Options │ │ News    │           │      │
│   │  │ (Real-  │ │ (OHLCV  │ │ (Chains │ │ (With   │           │      │
│   │  │  time)  │ │  Any TF)│ │  Greeks)│ │  Sent.) │           │      │
│   │  └─────────┘ └─────────┘ └─────────┘ └─────────┘           │      │
│   │                                                              │      │
│   │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐           │      │
│   │  │Financ-  │ │ Insider │ │ Divid-  │ │ Ticker  │           │      │
│   │  │  ials   │ │  Trans  │ │  ends   │ │ Details │           │      │
│   │  └─────────┘ └─────────┘ └─────────┘ └─────────┘           │      │
│   │                                                              │      │
│   └─────────────────────────────────────────────────────────────┘      │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                       STORAGE LAYER                                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   ┌──────────────────┐    ┌──────────────────┐                         │
│   │   SQLite/Postgres│    │   Pinecone       │                         │
│   │                  │    │   (Vector DB)    │                         │
│   │  • Scan cache    │    │  • Embeddings    │                         │
│   │  • User prefs    │    │  • Knowledge     │                         │
│   │  • Trade log     │    │  • Strategies    │                         │
│   └──────────────────┘    └──────────────────┘                         │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Polygon Integration

### Objective

Replace the fragmented data layer (Alpaca + Yahoo + IEX) with a single, reliable source (Polygon.io).

### Duration: 1-2 Weeks

### Prerequisites

- [ ] Polygon.io account (Stocks Starter plan - $79/mo)
- [ ] API key from Polygon dashboard

### What Gets Deleted

| File | Lines | Reason |
|------|-------|--------|
| `api/scanner/alpaca_scan.py` | ~400 | Replaced by Polygon |
| `api/services/stock_data.py` | ~350 | Replaced by Polygon |
| Yahoo Finance fallbacks | ~500 | No longer needed |
| IEX workarounds | ~200 | No longer needed |
| Rate limit handling | ~300 | Polygon is generous |
| **Total Deleted** | **~1,750** | |

### What Gets Created

| File | Purpose |
|------|---------|
| `api/services/polygon.py` | Single data service (~400 lines) |
| `api/scanner/polygon_scanner.py` | Fast market scanner (~200 lines) |

### New File Structure

```
api/
├── config.py                    # Polygon API key
├── main.py                      # FastAPI endpoints
├── models/
│   └── stock.py                 # Pydantic models (simplified)
├── services/
│   ├── polygon.py               # 🆕 ALL data fetching
│   ├── kimi.py                  # AI service (unchanged)
│   ├── chat.py                  # Chat streaming (unchanged)
│   ├── alpha.py                 # Alpha scoring (simplified)
│   └── chart.py                 # Chart data (uses Polygon)
└── scanner/
    ├── polygon_scanner.py       # 🆕 Market scanner
    ├── scheduler.py             # Background jobs (simplified)
    └── database.py              # SQLite cache (unchanged)
```

### Polygon Service Implementation

```python
# api/services/polygon.py

import httpx
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from api.config import POLYGON_API_KEY

BASE_URL = "https://api.polygon.io"

class PolygonService:
    """
    Single source of truth for all market data.
    Replaces: Alpaca, Yahoo Finance, IEX
    """
    
    def __init__(self):
        self.api_key = POLYGON_API_KEY
        self.client = httpx.AsyncClient(timeout=30.0)
    
    # ═══════════════════════════════════════════════════════════
    # REAL-TIME QUOTES
    # ═══════════════════════════════════════════════════════════
    
    async def get_quote(self, symbol: str) -> Dict[str, Any]:
        """Get real-time quote for a symbol."""
        url = f"{BASE_URL}/v2/last/trade/{symbol}"
        response = await self._request(url)
        
        # Also get previous close for change calculation
        prev = await self.get_previous_close(symbol)
        
        price = response["results"]["p"]
        prev_close = prev["results"][0]["c"]
        change = price - prev_close
        change_pct = (change / prev_close) * 100
        
        return {
            "symbol": symbol,
            "price": price,
            "change": change,
            "change_percent": change_pct,
            "volume": response["results"].get("s", 0),
            "timestamp": response["results"]["t"]
        }
    
    async def get_snapshot(self, symbol: str) -> Dict[str, Any]:
        """Get full snapshot including quote, day stats, prev day."""
        url = f"{BASE_URL}/v2/snapshot/locale/us/markets/stocks/tickers/{symbol}"
        return await self._request(url)
    
    async def get_all_snapshots(self) -> List[Dict[str, Any]]:
        """Get snapshots for ALL tickers (for scanning)."""
        url = f"{BASE_URL}/v2/snapshot/locale/us/markets/stocks/tickers"
        response = await self._request(url)
        return response.get("tickers", [])
    
    # ═══════════════════════════════════════════════════════════
    # HISTORICAL BARS (OHLCV)
    # ═══════════════════════════════════════════════════════════
    
    async def get_bars(
        self,
        symbol: str,
        timeframe: str = "1",        # 1, 5, 15, 30, 60, D, W, M
        timeframe_unit: str = "day", # minute, hour, day, week, month
        from_date: str = None,
        to_date: str = None,
        limit: int = 500
    ) -> List[Dict[str, Any]]:
        """Get historical OHLCV bars."""
        if not from_date:
            from_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        if not to_date:
            to_date = datetime.now().strftime("%Y-%m-%d")
        
        url = f"{BASE_URL}/v2/aggs/ticker/{symbol}/range/{timeframe}/{timeframe_unit}/{from_date}/{to_date}"
        params = {"limit": limit, "sort": "asc"}
        response = await self._request(url, params)
        
        return [
            {
                "time": bar["t"] // 1000,  # Convert to seconds for charts
                "open": bar["o"],
                "high": bar["h"],
                "low": bar["l"],
                "close": bar["c"],
                "volume": bar["v"]
            }
            for bar in response.get("results", [])
        ]
    
    async def get_previous_close(self, symbol: str) -> Dict[str, Any]:
        """Get previous day's OHLCV."""
        url = f"{BASE_URL}/v2/aggs/ticker/{symbol}/prev"
        return await self._request(url)
    
    # ═══════════════════════════════════════════════════════════
    # TICKER DETAILS (Company Info, Market Cap, Sector)
    # ═══════════════════════════════════════════════════════════
    
    async def get_ticker_details(self, symbol: str) -> Dict[str, Any]:
        """Get company details including sector, market cap, etc."""
        url = f"{BASE_URL}/v3/reference/tickers/{symbol}"
        response = await self._request(url)
        results = response.get("results", {})
        
        return {
            "symbol": symbol,
            "name": results.get("name"),
            "market_cap": results.get("market_cap"),
            "sector": results.get("sic_description"),
            "industry": results.get("sic_description"),
            "shares_outstanding": results.get("share_class_shares_outstanding"),
            "float": results.get("weighted_shares_outstanding"),
            "description": results.get("description"),
            "homepage": results.get("homepage_url"),
            "list_date": results.get("list_date"),
            "locale": results.get("locale"),
            "primary_exchange": results.get("primary_exchange")
        }
    
    async def get_all_tickers(self, market: str = "stocks", active: bool = True) -> List[str]:
        """Get all active ticker symbols."""
        url = f"{BASE_URL}/v3/reference/tickers"
        params = {"market": market, "active": active, "limit": 1000}
        
        all_tickers = []
        while True:
            response = await self._request(url, params)
            tickers = response.get("results", [])
            all_tickers.extend([t["ticker"] for t in tickers])
            
            # Handle pagination
            next_url = response.get("next_url")
            if not next_url:
                break
            url = next_url
            params = {}
        
        return all_tickers
    
    # ═══════════════════════════════════════════════════════════
    # FINANCIALS (Income Statement, Balance Sheet, Cash Flow)
    # ═══════════════════════════════════════════════════════════
    
    async def get_financials(
        self,
        symbol: str,
        timeframe: str = "quarterly",  # quarterly, annual
        limit: int = 4
    ) -> List[Dict[str, Any]]:
        """Get financial statements."""
        url = f"{BASE_URL}/vX/reference/financials"
        params = {
            "ticker": symbol,
            "timeframe": timeframe,
            "limit": limit,
            "sort": "filing_date",
            "order": "desc"
        }
        response = await self._request(url, params)
        return response.get("results", [])
    
    # ═══════════════════════════════════════════════════════════
    # OPTIONS
    # ═══════════════════════════════════════════════════════════
    
    async def get_options_chain(
        self,
        symbol: str,
        expiration_date: str = None,
        contract_type: str = None,  # "call" or "put"
        limit: int = 250
    ) -> List[Dict[str, Any]]:
        """Get options chain for a symbol."""
        url = f"{BASE_URL}/v3/reference/options/contracts"
        params = {
            "underlying_ticker": symbol,
            "limit": limit
        }
        if expiration_date:
            params["expiration_date"] = expiration_date
        if contract_type:
            params["contract_type"] = contract_type
        
        response = await self._request(url, params)
        return response.get("results", [])
    
    async def get_option_quote(self, option_ticker: str) -> Dict[str, Any]:
        """Get quote for specific option contract."""
        url = f"{BASE_URL}/v2/last/trade/{option_ticker}"
        return await self._request(url)
    
    # ═══════════════════════════════════════════════════════════
    # NEWS
    # ═══════════════════════════════════════════════════════════
    
    async def get_news(
        self,
        symbol: str = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get news articles, optionally filtered by ticker."""
        url = f"{BASE_URL}/v2/reference/news"
        params = {"limit": limit, "sort": "published_utc", "order": "desc"}
        if symbol:
            params["ticker"] = symbol
        
        response = await self._request(url, params)
        return [
            {
                "title": article["title"],
                "url": article["article_url"],
                "source": article["publisher"]["name"],
                "published": article["published_utc"],
                "tickers": article.get("tickers", []),
                "description": article.get("description", ""),
                "image": article.get("image_url"),
                "keywords": article.get("keywords", [])
            }
            for article in response.get("results", [])
        ]
    
    # ═══════════════════════════════════════════════════════════
    # INSIDER TRANSACTIONS
    # ═══════════════════════════════════════════════════════════
    
    async def get_insider_transactions(
        self,
        symbol: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get insider (Form 4) transactions."""
        url = f"{BASE_URL}/vX/reference/insider-transactions"
        params = {"ticker": symbol, "limit": limit}
        response = await self._request(url, params)
        return response.get("results", [])
    
    # ═══════════════════════════════════════════════════════════
    # DIVIDENDS
    # ═══════════════════════════════════════════════════════════
    
    async def get_dividends(
        self,
        symbol: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get dividend history."""
        url = f"{BASE_URL}/v3/reference/dividends"
        params = {"ticker": symbol, "limit": limit}
        response = await self._request(url, params)
        return response.get("results", [])
    
    # ═══════════════════════════════════════════════════════════
    # HELPER METHODS
    # ═══════════════════════════════════════════════════════════
    
    async def _request(
        self,
        url: str,
        params: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Make authenticated request to Polygon API."""
        if params is None:
            params = {}
        params["apiKey"] = self.api_key
        
        response = await self.client.get(url, params=params)
        response.raise_for_status()
        return response.json()
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


# Singleton instance
polygon_service = PolygonService()
```

### Scanner Implementation

```python
# api/scanner/polygon_scanner.py

from typing import List, Dict, Any
from api.services.polygon import polygon_service
from api.scanner.database import ScannerDB

class PolygonScanner:
    """
    Fast market scanner using Polygon snapshots.
    Scans entire market in ONE API call.
    """
    
    def __init__(self):
        self.db = ScannerDB()
    
    async def scan(self) -> Dict[str, Any]:
        """
        Scan entire market using Polygon's snapshot endpoint.
        Returns: Dict with scan results and statistics.
        """
        # ONE API call gets ALL stocks
        snapshots = await polygon_service.get_all_snapshots()
        
        results = []
        stats = {
            "total_scanned": 0,
            "gainers": 0,
            "losers": 0,
            "unusual_volume": 0,
            "new_highs": 0,
            "new_lows": 0
        }
        
        for snap in snapshots:
            try:
                ticker = snap.get("ticker")
                day = snap.get("day", {})
                prev = snap.get("prevDay", {})
                
                if not day or not prev:
                    continue
                
                price = day.get("c", 0)
                prev_close = prev.get("c", 0)
                volume = day.get("v", 0)
                avg_volume = prev.get("v", 1)  # Use prev day as baseline
                
                if prev_close == 0:
                    continue
                
                change_pct = ((price - prev_close) / prev_close) * 100
                relative_volume = volume / avg_volume if avg_volume > 0 else 1.0
                
                # Calculate 52-week high/low from snapshot
                min_data = snap.get("min", {})
                
                stock_data = {
                    "symbol": ticker,
                    "price": price,
                    "change_percent": round(change_pct, 2),
                    "volume": volume,
                    "relative_volume": round(relative_volume, 2),
                    "day_high": day.get("h", price),
                    "day_low": day.get("l", price),
                    "vwap": day.get("vw", price),
                    "prev_close": prev_close,
                    "updated": snap.get("updated", 0)
                }
                
                results.append(stock_data)
                
                # Update stats
                stats["total_scanned"] += 1
                if change_pct > 0:
                    stats["gainers"] += 1
                elif change_pct < 0:
                    stats["losers"] += 1
                if relative_volume > 2.0:
                    stats["unusual_volume"] += 1
                    
            except Exception as e:
                continue
        
        # Sort by absolute change
        results.sort(key=lambda x: abs(x["change_percent"]), reverse=True)
        
        # Save to cache
        self.db.save_scan_results(results)
        
        return {
            "stocks": results,
            "stats": stats,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_top_gainers(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get top gaining stocks from cache."""
        return self.db.query(
            order_by="change_percent DESC",
            where="change_percent > 0",
            limit=limit
        )
    
    def get_top_losers(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get top losing stocks from cache."""
        return self.db.query(
            order_by="change_percent ASC",
            where="change_percent < 0",
            limit=limit
        )
    
    def get_unusual_volume(self, min_rvol: float = 2.0, limit: int = 20) -> List[Dict[str, Any]]:
        """Get stocks with unusual volume."""
        return self.db.query(
            order_by="relative_volume DESC",
            where=f"relative_volume >= {min_rvol}",
            limit=limit
        )
    
    def search(
        self,
        sector: str = None,
        min_price: float = None,
        max_price: float = None,
        min_volume: int = None,
        min_change: float = None,
        max_change: float = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Search stocks with filters."""
        conditions = []
        
        if sector:
            conditions.append(f"sector = '{sector}'")
        if min_price:
            conditions.append(f"price >= {min_price}")
        if max_price:
            conditions.append(f"price <= {max_price}")
        if min_volume:
            conditions.append(f"volume >= {min_volume}")
        if min_change:
            conditions.append(f"change_percent >= {min_change}")
        if max_change:
            conditions.append(f"change_percent <= {max_change}")
        
        where = " AND ".join(conditions) if conditions else None
        
        return self.db.query(
            order_by="volume DESC",
            where=where,
            limit=limit
        )
```

### API Endpoints Update

```python
# api/main.py (relevant sections)

from api.services.polygon import polygon_service
from api.scanner.polygon_scanner import PolygonScanner

scanner = PolygonScanner()

# ═══════════════════════════════════════════════════════════
# QUOTES
# ═══════════════════════════════════════════════════════════

@app.get("/api/quote/{symbol}")
async def get_quote(symbol: str):
    """Get real-time quote."""
    return await polygon_service.get_quote(symbol.upper())

@app.get("/api/snapshot/{symbol}")
async def get_snapshot(symbol: str):
    """Get full snapshot for a symbol."""
    return await polygon_service.get_snapshot(symbol.upper())

# ═══════════════════════════════════════════════════════════
# HISTORICAL DATA
# ═══════════════════════════════════════════════════════════

@app.get("/api/bars/{symbol}")
async def get_bars(
    symbol: str,
    timeframe: str = "1",
    timeframe_unit: str = "day",
    from_date: str = None,
    to_date: str = None,
    limit: int = 500
):
    """Get historical OHLCV bars."""
    return await polygon_service.get_bars(
        symbol.upper(),
        timeframe,
        timeframe_unit,
        from_date,
        to_date,
        limit
    )

# ═══════════════════════════════════════════════════════════
# COMPANY INFO
# ═══════════════════════════════════════════════════════════

@app.get("/api/ticker/{symbol}")
async def get_ticker_details(symbol: str):
    """Get company details."""
    return await polygon_service.get_ticker_details(symbol.upper())

# ═══════════════════════════════════════════════════════════
# FINANCIALS
# ═══════════════════════════════════════════════════════════

@app.get("/api/financials/{symbol}")
async def get_financials(symbol: str, timeframe: str = "quarterly"):
    """Get financial statements."""
    return await polygon_service.get_financials(symbol.upper(), timeframe)

# ═══════════════════════════════════════════════════════════
# OPTIONS
# ═══════════════════════════════════════════════════════════

@app.get("/api/options/{symbol}")
async def get_options_chain(symbol: str, expiration: str = None):
    """Get options chain."""
    return await polygon_service.get_options_chain(symbol.upper(), expiration)

# ═══════════════════════════════════════════════════════════
# NEWS
# ═══════════════════════════════════════════════════════════

@app.get("/api/news")
async def get_news(symbol: str = None, limit: int = 10):
    """Get news articles."""
    return await polygon_service.get_news(symbol, limit)

# ═══════════════════════════════════════════════════════════
# SCANNER
# ═══════════════════════════════════════════════════════════

@app.post("/api/scanner/scan")
async def trigger_scan():
    """Trigger a full market scan."""
    return await scanner.scan()

@app.get("/api/scanner/gainers")
async def get_gainers(limit: int = 20):
    """Get top gainers."""
    return scanner.get_top_gainers(limit)

@app.get("/api/scanner/losers")
async def get_losers(limit: int = 20):
    """Get top losers."""
    return scanner.get_top_losers(limit)

@app.get("/api/scanner/volume")
async def get_unusual_volume(min_rvol: float = 2.0, limit: int = 20):
    """Get unusual volume stocks."""
    return scanner.get_unusual_volume(min_rvol, limit)

@app.get("/api/scanner/search")
async def search_stocks(
    sector: str = None,
    min_price: float = None,
    max_price: float = None,
    min_volume: int = None,
    min_change: float = None,
    max_change: float = None,
    limit: int = 50
):
    """Search stocks with filters."""
    return scanner.search(
        sector=sector,
        min_price=min_price,
        max_price=max_price,
        min_volume=min_volume,
        min_change=min_change,
        max_change=max_change,
        limit=limit
    )
```

### Environment Configuration

```python
# api/config.py

import os
from dotenv import load_dotenv

load_dotenv()

# Polygon.io
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")

# OpenRouter (for Kimi)
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Optional: Pinecone (for RAG - Phase 2)
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT")
```

```bash
# .env

POLYGON_API_KEY=your_polygon_api_key_here
OPENROUTER_API_KEY=your_openrouter_api_key_here

# Phase 2 (add later)
# PINECONE_API_KEY=your_pinecone_key
# PINECONE_ENVIRONMENT=us-east-1
```

### Testing Checklist

- [ ] Quote endpoint returns real-time data
- [ ] Historical bars return correct OHLCV
- [ ] Scanner completes in < 30 seconds
- [ ] Top gainers/losers sorted correctly
- [ ] Unusual volume filter works
- [ ] Options chain returns data
- [ ] News endpoint returns articles
- [ ] Kimi receives clean data (no hallucinations)

---

## Phase 2: RAG Knowledge System

### Objective

Give the AI access to investor wisdom, trading strategies, and historical patterns through a Retrieval-Augmented Generation (RAG) system.

### Duration: 2-3 Weeks

### Prerequisites

- [ ] Phase 1 complete (clean data layer)
- [ ] Pinecone account (free tier to start)
- [ ] Collection of knowledge sources (PDFs, notes, etc.)

### Knowledge Sources to Ingest

| Source Type | Examples | Purpose |
|-------------|----------|---------|
| **Trading Books** | Market Wizards, Reminiscences of a Stock Operator, Technical Analysis of Financial Markets | Investment philosophy |
| **Strategy Docs** | Your personal playbook, winning trade patterns | Your edge |
| **Historical Trades** | Your trade log with outcomes | Learn from experience |
| **News Archive** | Major market events + reactions | Pattern recognition |
| **SEC Filings** | 10-Ks, 8-Ks for key stocks | Deep company knowledge |

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     INGESTION PIPELINE                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  PDF/Text → Chunker → Embedder → Vector DB                     │
│                         │                                       │
│                         ↓                                       │
│              OpenAI text-embedding-3-small                      │
│              (or local: sentence-transformers)                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                     RETRIEVAL PIPELINE                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  User Query → Embed → Vector Search → Top K Chunks              │
│                                           │                     │
│                                           ↓                     │
│                                    Inject into Kimi prompt      │
│                                           │                     │
│                                           ↓                     │
│                                    Kimi generates response      │
│                                    with cited knowledge         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Implementation

```python
# api/services/rag.py

from pinecone import Pinecone
import openai
from typing import List, Dict, Any

class RAGService:
    """
    Retrieval-Augmented Generation for investor knowledge.
    """
    
    def __init__(self):
        self.pc = Pinecone(api_key=PINECONE_API_KEY)
        self.index = self.pc.Index("alphabot-knowledge")
        self.embed_model = "text-embedding-3-small"
    
    async def ingest_document(
        self,
        content: str,
        metadata: Dict[str, Any],
        chunk_size: int = 500
    ):
        """
        Ingest a document into the knowledge base.
        
        Args:
            content: Full text of document
            metadata: {"source": "Market Wizards", "author": "Jack Schwager", "type": "book"}
            chunk_size: Characters per chunk
        """
        # Chunk the document
        chunks = self._chunk_text(content, chunk_size)
        
        # Embed and upsert
        for i, chunk in enumerate(chunks):
            embedding = await self._embed(chunk)
            self.index.upsert(
                vectors=[{
                    "id": f"{metadata['source']}_{i}",
                    "values": embedding,
                    "metadata": {
                        **metadata,
                        "chunk_index": i,
                        "text": chunk
                    }
                }]
            )
    
    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
        filter: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant knowledge chunks for a query.
        
        Args:
            query: User's question
            top_k: Number of chunks to return
            filter: Optional metadata filter (e.g., {"type": "book"})
        
        Returns:
            List of relevant chunks with metadata
        """
        query_embedding = await self._embed(query)
        
        results = self.index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True,
            filter=filter
        )
        
        return [
            {
                "text": match["metadata"]["text"],
                "source": match["metadata"]["source"],
                "author": match["metadata"].get("author"),
                "score": match["score"]
            }
            for match in results["matches"]
        ]
    
    async def augment_prompt(
        self,
        user_query: str,
        system_prompt: str
    ) -> str:
        """
        Augment system prompt with relevant knowledge.
        """
        # Retrieve relevant chunks
        chunks = await self.retrieve(user_query, top_k=3)
        
        if not chunks:
            return system_prompt
        
        # Format knowledge section
        knowledge_section = "\n\n## Relevant Knowledge\n\n"
        for chunk in chunks:
            knowledge_section += f"**From {chunk['source']}** (relevance: {chunk['score']:.2f}):\n"
            knowledge_section += f"> {chunk['text']}\n\n"
        
        # Inject into system prompt
        augmented = system_prompt + knowledge_section
        augmented += "\n**Use the above knowledge to inform your analysis when relevant.**"
        
        return augmented
    
    def _chunk_text(self, text: str, chunk_size: int) -> List[str]:
        """Split text into overlapping chunks."""
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start = end - 100  # 100 char overlap
        return chunks
    
    async def _embed(self, text: str) -> List[float]:
        """Generate embedding for text."""
        response = await openai.Embedding.create(
            input=text,
            model=self.embed_model
        )
        return response["data"][0]["embedding"]


rag_service = RAGService()
```

### Integration with Kimi

```python
# api/services/chat.py (modified)

from api.services.rag import rag_service

async def chat_stream(messages: List[Dict], model: str = "kimi-k2"):
    """
    Stream chat with RAG-augmented knowledge.
    """
    user_query = messages[-1]["content"]
    
    # Augment system prompt with relevant knowledge
    base_system = SYSTEM_PROMPT
    augmented_system = await rag_service.augment_prompt(user_query, base_system)
    
    # Make API call with augmented context
    async for chunk in _call_openrouter(
        messages=messages,
        system=augmented_system,
        model=model
    ):
        yield chunk
```

### Knowledge Ingestion CLI

```python
# scripts/ingest_knowledge.py

import asyncio
import PyPDF2
from api.services.rag import rag_service

async def ingest_pdf(filepath: str, metadata: Dict):
    """Ingest a PDF into the knowledge base."""
    with open(filepath, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
    
    await rag_service.ingest_document(text, metadata)
    print(f"Ingested: {metadata['source']}")

async def main():
    # Example: Ingest trading books
    books = [
        {
            "path": "books/market_wizards.pdf",
            "metadata": {
                "source": "Market Wizards",
                "author": "Jack Schwager",
                "type": "book",
                "topic": "trading psychology"
            }
        },
        {
            "path": "books/reminiscences.pdf",
            "metadata": {
                "source": "Reminiscences of a Stock Operator",
                "author": "Edwin Lefèvre",
                "type": "book",
                "topic": "speculation"
            }
        }
    ]
    
    for book in books:
        await ingest_pdf(book["path"], book["metadata"])

if __name__ == "__main__":
    asyncio.run(main())
```

### Example RAG-Enhanced Response

**User:** "Should I buy NVDA on this pullback?"

**Kimi (with RAG):**

> Based on the current data and relevant wisdom from the knowledge base:
> 
> **Current Situation:**
> - NVDA is down 5% from its high, trading at $890
> - Volume is 1.2x average (moderate)
> - RSI is at 45 (neutral)
> 
> **Relevant Wisdom:**
> 
> From *Reminiscences of a Stock Operator*:
> > "The big money is not in the buying or selling, but in the waiting. I never try to catch the top or bottom."
> 
> From *Market Wizards* (Paul Tudor Jones):
> > "I'm always thinking about losing money as opposed to making money. Don't focus on making money; focus on protecting what you have."
> 
> **Analysis:**
> This pullback is shallow (5%) compared to NVDA's typical swings (10-15%). The greats would say:
> 1. **Wait for confirmation** - Jones would want to see support hold before adding
> 2. **Risk management first** - Where's your stop? Define the risk before entry
> 
> **Would you like me to identify the key support levels on the chart?**

---

## Phase 3: Clawdbot Mobile Interface

### Objective

Enable conversation with your AlphaBot system from anywhere via text messages.

### Duration: 1-2 Weeks

### Prerequisites

- [ ] Phase 1 & 2 complete
- [ ] Clawdbot installed and configured
- [ ] Messaging integration (Telegram, Discord, or SMS via Twilio)

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     MESSAGE FLOW                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Your Phone ──→ Telegram/Discord ──→ Clawdbot ──→ AlphaBot API │
│       ↑                                              │          │
│       │                                              ↓          │
│       └─────────────── Response ←──────────────────────         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Clawdbot Configuration

```yaml
# clawdbot/config.yaml

name: "AlphaBot"
description: "Your AI trading assistant"

# LLM Provider
provider: openrouter
model: moonshotai/kimi-k2

# Tools available to the agent
tools:
  - name: get_quote
    description: "Get real-time stock quote"
    endpoint: "http://localhost:8000/api/quote/{symbol}"
    method: GET
    
  - name: search_market
    description: "Search for stocks with filters"
    endpoint: "http://localhost:8000/api/scanner/search"
    method: GET
    params:
      - sector
      - min_price
      - max_price
      - min_volume
      
  - name: get_news
    description: "Get latest news for a stock"
    endpoint: "http://localhost:8000/api/news"
    method: GET
    params:
      - symbol
      
  - name: get_chart
    description: "Get chart data for a stock"
    endpoint: "http://localhost:8000/api/chart/{symbol}"
    method: GET
    
  - name: analyze_stock
    description: "Get full AI analysis of a stock"
    endpoint: "http://localhost:8000/api/analyze/{symbol}"
    method: GET

# Messaging integration
messaging:
  telegram:
    token: ${TELEGRAM_BOT_TOKEN}
    allowed_users:
      - your_telegram_id
  
  # Optional: Discord
  # discord:
  #   token: ${DISCORD_BOT_TOKEN}
  #   allowed_servers:
  #     - your_server_id
```

### Telegram Bot Setup

```python
# clawdbot/integrations/telegram.py

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from clawdbot import Agent

agent = Agent.from_config("config.yaml")

async def handle_message(update: Update, context):
    """Handle incoming Telegram messages."""
    user_message = update.message.text
    user_id = update.effective_user.id
    
    # Check if user is allowed
    if user_id not in ALLOWED_USERS:
        await update.message.reply_text("Unauthorized.")
        return
    
    # Get response from agent
    response = await agent.chat(user_message)
    
    # Send response (handle long messages)
    if len(response) > 4096:
        # Split into chunks
        for i in range(0, len(response), 4096):
            await update.message.reply_text(
                response[i:i+4096],
                parse_mode="Markdown"
            )
    else:
        await update.message.reply_text(response, parse_mode="Markdown")

async def start(update: Update, context):
    """Handle /start command."""
    await update.message.reply_text(
        "👋 Hey! I'm AlphaBot, your AI trading assistant.\n\n"
        "Ask me anything about the markets:\n"
        "• 'What's moving in tech today?'\n"
        "• 'Analyze NVDA'\n"
        "• 'Show me biotech breakouts'\n"
        "• 'What's the news on AAPL?'"
    )

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    app.run_polling()

if __name__ == "__main__":
    main()
```

### Example Mobile Conversations

**You:** "What's hot in biotech?"

**AlphaBot:**
```
📊 Biotech Movers Today

| Ticker | Price | Change | Volume |
|--------|-------|--------|--------|
| MRNA   | $125  | +8.2%  | 3.2x   |
| NVAX   | $18   | +5.1%  | 2.1x   |
| VXRT   | $2.45 | +12%   | 4.5x   |

MRNA is leading on FDA approval news.
Want details on any of these?
```

---

**You:** "Set an alert if NVDA drops below 850"

**AlphaBot:**
```
✅ Alert set: NVDA < $850

Current price: $892
Distance to alert: -4.7%

I'll message you when triggered.
```

---

**You:** "The RSI filter is too strict, change it to 60"

**AlphaBot:**
```
📝 Proposed change to alpha scoring:

File: api/services/alpha.py
Line 45: RSI_OVERSOLD_THRESHOLD = 30 → 60

This will flag more stocks as "oversold".
Should I apply this change? (yes/no)
```

**You:** "yes"

**AlphaBot:**
```
✅ Change applied and deployed.

New RSI threshold: 60
This will affect future scans.
```

---

## Phase 4: Self-Improving Algorithm

### Objective

Create a feedback loop where the system learns from outcomes and your guidance.

### Duration: Ongoing

### Components

1. **Trade Logging** - Record all alerts and their outcomes
2. **Performance Tracking** - Which signals worked, which didn't
3. **Feedback Integration** - Learn from your corrections
4. **Automatic Tuning** - Adjust weights based on results

### Trade Logger

```python
# api/services/trade_logger.py

from datetime import datetime
from typing import Dict, Any, Optional
import sqlite3

class TradeLogger:
    """
    Log signals, alerts, and outcomes for learning.
    """
    
    def __init__(self, db_path: str = "trades.db"):
        self.conn = sqlite3.connect(db_path)
        self._init_db()
    
    def _init_db(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS signals (
                id INTEGER PRIMARY KEY,
                timestamp TEXT,
                symbol TEXT,
                signal_type TEXT,
                entry_price REAL,
                target_price REAL,
                stop_price REAL,
                confidence REAL,
                reasoning TEXT,
                outcome TEXT,
                exit_price REAL,
                return_pct REAL,
                feedback TEXT
            )
        """)
        self.conn.commit()
    
    def log_signal(
        self,
        symbol: str,
        signal_type: str,  # "breakout", "volume_spike", "momentum", etc.
        entry_price: float,
        target_price: float = None,
        stop_price: float = None,
        confidence: float = None,
        reasoning: str = None
    ) -> int:
        """Log a new signal/alert."""
        cursor = self.conn.execute("""
            INSERT INTO signals 
            (timestamp, symbol, signal_type, entry_price, target_price, stop_price, confidence, reasoning)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            symbol,
            signal_type,
            entry_price,
            target_price,
            stop_price,
            confidence,
            reasoning
        ))
        self.conn.commit()
        return cursor.lastrowid
    
    def record_outcome(
        self,
        signal_id: int,
        outcome: str,  # "win", "loss", "breakeven", "missed"
        exit_price: float = None,
        feedback: str = None
    ):
        """Record the outcome of a signal."""
        return_pct = None
        if exit_price:
            entry = self.conn.execute(
                "SELECT entry_price FROM signals WHERE id = ?", (signal_id,)
            ).fetchone()[0]
            return_pct = ((exit_price - entry) / entry) * 100
        
        self.conn.execute("""
            UPDATE signals 
            SET outcome = ?, exit_price = ?, return_pct = ?, feedback = ?
            WHERE id = ?
        """, (outcome, exit_price, return_pct, feedback, signal_id))
        self.conn.commit()
    
    def get_performance_stats(self, signal_type: str = None) -> Dict[str, Any]:
        """Get performance statistics."""
        where = f"WHERE signal_type = '{signal_type}'" if signal_type else ""
        
        stats = self.conn.execute(f"""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN outcome = 'win' THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN outcome = 'loss' THEN 1 ELSE 0 END) as losses,
                AVG(return_pct) as avg_return,
                AVG(CASE WHEN outcome = 'win' THEN return_pct END) as avg_win,
                AVG(CASE WHEN outcome = 'loss' THEN return_pct END) as avg_loss
            FROM signals
            {where}
            AND outcome IS NOT NULL
        """).fetchone()
        
        return {
            "total_signals": stats[0],
            "wins": stats[1],
            "losses": stats[2],
            "win_rate": stats[1] / stats[0] if stats[0] > 0 else 0,
            "avg_return": stats[3],
            "avg_win": stats[4],
            "avg_loss": stats[5],
            "profit_factor": abs(stats[4] / stats[5]) if stats[5] else None
        }
    
    def get_best_patterns(self, min_trades: int = 10) -> List[Dict[str, Any]]:
        """Find the most profitable signal types."""
        patterns = self.conn.execute("""
            SELECT 
                signal_type,
                COUNT(*) as trades,
                AVG(return_pct) as avg_return,
                SUM(CASE WHEN outcome = 'win' THEN 1 ELSE 0 END) * 1.0 / COUNT(*) as win_rate
            FROM signals
            WHERE outcome IS NOT NULL
            GROUP BY signal_type
            HAVING COUNT(*) >= ?
            ORDER BY avg_return DESC
        """, (min_trades,)).fetchall()
        
        return [
            {
                "signal_type": p[0],
                "trades": p[1],
                "avg_return": p[2],
                "win_rate": p[3]
            }
            for p in patterns
        ]


trade_logger = TradeLogger()
```

### Feedback Integration

```python
# api/services/feedback.py

from api.services.trade_logger import trade_logger
from api.services.rag import rag_service

class FeedbackProcessor:
    """
    Process user feedback to improve the algorithm.
    """
    
    async def process_feedback(self, feedback: str, context: Dict[str, Any]):
        """
        Process natural language feedback and apply learnings.
        
        Examples:
        - "That NVDA call was perfect"
        - "Stop alerting on penny stocks"
        - "The volume filter is too loose"
        """
        # Store feedback in RAG for future reference
        await rag_service.ingest_document(
            content=f"User feedback on {context.get('symbol', 'general')}: {feedback}",
            metadata={
                "source": "user_feedback",
                "type": "feedback",
                "timestamp": datetime.now().isoformat(),
                "context": context
            }
        )
        
        # Parse actionable items
        actions = self._parse_feedback(feedback)
        
        return actions
    
    def _parse_feedback(self, feedback: str) -> List[Dict[str, Any]]:
        """Parse feedback into actionable items."""
        actions = []
        
        feedback_lower = feedback.lower()
        
        # Pattern: Price filter
        if "penny stock" in feedback_lower or "under $" in feedback_lower:
            actions.append({
                "type": "filter",
                "parameter": "min_price",
                "suggested_value": 5.0,
                "reason": "User wants to avoid penny stocks"
            })
        
        # Pattern: Volume filter
        if "volume" in feedback_lower and ("loose" in feedback_lower or "strict" in feedback_lower):
            direction = "increase" if "loose" in feedback_lower else "decrease"
            actions.append({
                "type": "adjust",
                "parameter": "min_relative_volume",
                "direction": direction,
                "reason": f"User feedback: volume filter too {direction}"
            })
        
        # Pattern: Positive reinforcement
        if any(word in feedback_lower for word in ["perfect", "great", "good call", "worked"]):
            actions.append({
                "type": "reinforce",
                "reason": "Positive feedback - reinforce this pattern"
            })
        
        return actions


feedback_processor = FeedbackProcessor()
```

### Automatic Tuning

```python
# api/services/tuner.py

from api.services.trade_logger import trade_logger

class AlgorithmTuner:
    """
    Automatically tune algorithm parameters based on performance.
    """
    
    def __init__(self):
        self.config_path = "api/config/alpha_weights.json"
        self.weights = self._load_weights()
    
    def _load_weights(self) -> Dict[str, float]:
        """Load current weight configuration."""
        with open(self.config_path) as f:
            return json.load(f)
    
    def _save_weights(self):
        """Save updated weights."""
        with open(self.config_path, "w") as f:
            json.dump(self.weights, f, indent=2)
    
    def tune(self, min_trades: int = 20):
        """
        Tune weights based on historical performance.
        """
        # Get performance by signal type
        best_patterns = trade_logger.get_best_patterns(min_trades)
        
        if not best_patterns:
            return {"status": "not_enough_data"}
        
        # Calculate new weights
        # Higher weight = better historical performance
        total_return = sum(p["avg_return"] for p in best_patterns if p["avg_return"] > 0)
        
        for pattern in best_patterns:
            signal_type = pattern["signal_type"]
            if pattern["avg_return"] > 0:
                new_weight = pattern["avg_return"] / total_return
                self.weights[signal_type] = round(new_weight, 3)
            else:
                # Reduce weight for losing patterns
                self.weights[signal_type] = max(0.01, self.weights.get(signal_type, 0.1) * 0.8)
        
        self._save_weights()
        
        return {
            "status": "tuned",
            "new_weights": self.weights,
            "based_on_patterns": best_patterns
        }
    
    def get_recommendation(self) -> str:
        """Get tuning recommendations in natural language."""
        stats = trade_logger.get_performance_stats()
        best = trade_logger.get_best_patterns(5)
        
        if not best:
            return "Not enough trade data yet. Keep logging outcomes!"
        
        top_pattern = best[0]
        worst_pattern = best[-1] if len(best) > 1 else None
        
        rec = f"Based on {stats['total_signals']} logged signals:\n\n"
        rec += f"**Best performer:** {top_pattern['signal_type']}\n"
        rec += f"- Win rate: {top_pattern['win_rate']:.1%}\n"
        rec += f"- Avg return: {top_pattern['avg_return']:.1f}%\n\n"
        
        if worst_pattern and worst_pattern['avg_return'] < 0:
            rec += f"**Consider reducing:** {worst_pattern['signal_type']}\n"
            rec += f"- Win rate: {worst_pattern['win_rate']:.1%}\n"
            rec += f"- Avg return: {worst_pattern['avg_return']:.1f}%\n"
        
        return rec


tuner = AlgorithmTuner()
```

---

## Technical Specifications

### System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **Server** | 1 vCPU, 1GB RAM | 2 vCPU, 4GB RAM |
| **Storage** | 5GB | 20GB (for knowledge base) |
| **Python** | 3.10+ | 3.11+ |
| **Database** | SQLite | PostgreSQL |

### Dependencies

```txt
# requirements.txt

# Web Framework
fastapi==0.109.0
uvicorn==0.27.0
httpx==0.26.0

# Data
polygon-api-client==1.12.0
pandas==2.1.4
numpy==1.26.3

# AI/ML
openai==1.12.0
pinecone-client==3.0.0
sentence-transformers==2.2.2

# Utilities
python-dotenv==1.0.0
pydantic==2.5.3
apscheduler==3.10.4

# PDF Processing (for RAG ingestion)
PyPDF2==3.0.1
pypdf==3.17.4

# Telegram Bot (optional)
python-telegram-bot==20.7
```

### API Rate Limits

| Service | Limit | Our Usage |
|---------|-------|-----------|
| **Polygon** | 5 req/min (free) → Unlimited (paid) | ~100/min scanning |
| **OpenRouter** | Varies by model | ~50 req/hour |
| **Pinecone** | 100 req/sec | ~10 req/min |

### Security Considerations

- [ ] All API keys in `.env` (never committed)
- [ ] `.env` in `.gitignore`
- [ ] Rate limiting on public endpoints
- [ ] User authentication for mobile access
- [ ] Telegram/Discord user allowlist

---

## Cost Analysis

### Monthly Costs

| Service | Tier | Cost |
|---------|------|------|
| **Polygon.io** | Stocks Starter | $79/mo |
| **OpenRouter** | Pay-as-you-go | ~$10-20/mo |
| **Pinecone** | Starter (free) → Standard | $0-25/mo |
| **Server** | Railway/Render | $0-20/mo |
| **Domain** (optional) | | ~$12/year |
| **Total** | | **$89-144/mo** |

### Cost Optimization

1. **Cache aggressively** - Reduce Polygon calls
2. **Batch requests** - Use snapshot endpoint for scans
3. **Free tier Pinecone** - 100K vectors free
4. **Railway free tier** - 500 hours/month

### Comparison to Alternatives

| Solution | Monthly Cost |
|----------|--------------|
| **Bloomberg Terminal** | $2,000+ |
| **Finviz Elite + API** | $339 |
| **TradingView + API** | $150+ |
| **Your AlphaBot** | **$100-150** |

---

## Success Metrics

### Phase 1 (Data Foundation)

- [ ] Single API source (Polygon)
- [ ] Market scan < 30 seconds
- [ ] Zero data-related hallucinations from Kimi
- [ ] Codebase < 5,000 lines

### Phase 2 (Knowledge)

- [ ] 5+ books ingested
- [ ] 100+ strategy notes indexed
- [ ] Kimi cites relevant knowledge in responses
- [ ] Trade history logging active

### Phase 3 (Access)

- [ ] Mobile bot responds in < 5 seconds
- [ ] Can execute searches from phone
- [ ] Alerts delivered instantly
- [ ] Can request code changes via chat

### Phase 4 (Evolution)

- [ ] 100+ signals logged with outcomes
- [ ] Win rate tracked per signal type
- [ ] Automatic weight tuning active
- [ ] Feedback loop integrated

---

## Getting Started

### Immediate Next Steps

1. **Sign up for Polygon.io** ($79/mo Stocks Starter)
   - https://polygon.io/pricing
   
2. **Get your API key** from Polygon dashboard

3. **Tell me "Go"** and I'll:
   - Delete ~6,000 lines of messy code
   - Implement clean Polygon integration
   - Test everything works
   - Push to GitHub

### Week 1 Deliverables

- [ ] Polygon service implemented
- [ ] Scanner using Polygon snapshots
- [ ] All endpoints updated
- [ ] Kimi receiving clean data
- [ ] Old code deleted

---

## Appendix

### A. Polygon API Quick Reference

```python
# Quotes
GET /v2/last/trade/{symbol}
GET /v2/snapshot/locale/us/markets/stocks/tickers/{symbol}
GET /v2/snapshot/locale/us/markets/stocks/tickers  # ALL stocks

# Historical
GET /v2/aggs/ticker/{symbol}/range/{multiplier}/{timespan}/{from}/{to}
GET /v2/aggs/ticker/{symbol}/prev

# Reference
GET /v3/reference/tickers/{symbol}
GET /v3/reference/tickers
GET /vX/reference/financials

# Options
GET /v3/reference/options/contracts
GET /v2/last/trade/{option_ticker}

# News
GET /v2/reference/news

# Insider
GET /vX/reference/insider-transactions
```

### B. Kimi Tool Definitions (Updated)

```json
{
  "tools": [
    {
      "name": "get_quote",
      "description": "Get real-time stock quote from Polygon",
      "parameters": {
        "symbol": {"type": "string", "required": true}
      }
    },
    {
      "name": "search_market",
      "description": "Search stocks with filters",
      "parameters": {
        "sector": {"type": "string"},
        "min_price": {"type": "number"},
        "max_price": {"type": "number"},
        "min_change": {"type": "number"},
        "min_volume": {"type": "number"}
      }
    },
    {
      "name": "get_chart_data",
      "description": "Get OHLCV data for charts",
      "parameters": {
        "symbol": {"type": "string", "required": true},
        "timeframe": {"type": "string", "default": "1d"},
        "period": {"type": "string", "default": "3mo"}
      }
    },
    {
      "name": "get_financials",
      "description": "Get company financial statements",
      "parameters": {
        "symbol": {"type": "string", "required": true}
      }
    },
    {
      "name": "get_news",
      "description": "Get latest news for a stock",
      "parameters": {
        "symbol": {"type": "string"}
      }
    },
    {
      "name": "get_options_chain",
      "description": "Get options chain data",
      "parameters": {
        "symbol": {"type": "string", "required": true},
        "expiration": {"type": "string"}
      }
    }
  ]
}
```

### C. Environment Variables

```bash
# .env

# Required
POLYGON_API_KEY=your_polygon_key
OPENROUTER_API_KEY=your_openrouter_key

# Phase 2 (RAG)
PINECONE_API_KEY=your_pinecone_key
PINECONE_ENVIRONMENT=us-east-1
OPENAI_API_KEY=your_openai_key  # For embeddings

# Phase 3 (Mobile)
TELEGRAM_BOT_TOKEN=your_telegram_token
ALLOWED_TELEGRAM_USERS=123456789,987654321

# Optional
DATABASE_URL=postgresql://user:pass@host:5432/alphabot
REDIS_URL=redis://localhost:6379
```

---

**Document Version:** 1.0  
**Last Updated:** January 2026  
**Author:** AlphaBot Development Team

---

*Ready to build something amazing. Just say "Go."*

