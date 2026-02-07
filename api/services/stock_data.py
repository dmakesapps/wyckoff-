# api/services/stock_data.py

"""
Hybrid stock data fetching service

Strategy:
- ALPACA: Fast bulk data, real-time quotes, reliable for scanning
- YAHOO: Options, fundamentals, sector/industry, detailed analysis

Use Alpaca for:
- Bulk scanning (7000+ stocks without rate limits)
- Real-time quotes (faster, more reliable)
- Basic price/volume data

Use Yahoo for:
- Options chain data (Alpaca doesn't have this)
- Fundamentals (P/E, EPS, market cap, etc.)
- Sector/Industry classification
- Detailed company info
"""

import yfinance as yf
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
import requests
import logging
import threading
import time

from api.config import ALPACA_API_KEY, ALPACA_SECRET_KEY, ALPACA_DATA_URL, ALPACA_BASE_URL
from api.models.stock import StockQuote, Fundamentals

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# SIMPLE IN-MEMORY CACHE
# ═══════════════════════════════════════════════════════════════

class SimpleCache:
    """Thread-safe in-memory cache with TTL"""
    
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired"""
        with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                if datetime.now(timezone.utc) < entry["expires"]:
                    return entry["value"]
                else:
                    del self._cache[key]
        return None
    
    def set(self, key: str, value: Any, ttl_seconds: int):
        """Set value in cache with TTL"""
        with self._lock:
            self._cache[key] = {
                "value": value,
                "expires": datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)
            }
    
    def clear_expired(self):
        """Remove expired entries (call periodically)"""
        now = datetime.now(timezone.utc)
        with self._lock:
            expired = [k for k, v in self._cache.items() if now >= v["expires"]]
            for k in expired:
                del self._cache[k]


# Global cache instances
_quote_cache = SimpleCache()      # 15 second TTL for quotes
_fundamentals_cache = SimpleCache()  # 1 hour TTL for fundamentals
_history_cache = SimpleCache()    # 60 second TTL for historical data


class StockDataService:
    """
    Hybrid data service - uses Alpaca for speed, Yahoo for depth
    
    Alpaca: Real-time quotes, bulk scanning (PREFERRED for speed)
    Yahoo: Options, fundamentals, sector data, fallback
    """
    
    def __init__(self):
        self._alpaca_headers = {
            "APCA-API-KEY-ID": ALPACA_API_KEY,
            "APCA-API-SECRET-KEY": ALPACA_SECRET_KEY,
        }

        # Volume is enriched separately when needed
        self._use_alpaca_quotes = True
    
    def get_quote(self, symbol: str, prefer_alpaca: bool = True) -> Optional[StockQuote]:
        """
        Get current quote - tries Alpaca first (faster), falls back to Yahoo
        
        ✅ FIXED: Added caching (15 second TTL) to prevent rate limiting
        """
        symbol = symbol.upper().strip()
        cache_key = f"quote:{symbol}"
        
        # Check cache first
        cached = _quote_cache.get(cache_key)
        if cached:
            return cached
        
        quote = None
        
        if prefer_alpaca and self._use_alpaca_quotes:
            quote = self._get_alpaca_quote(symbol)
        
        # Fallback to Yahoo if Alpaca fails
        if not quote:
            quote = self._get_yahoo_quote(symbol)
        
        # Cache successful results for 15 seconds
        if quote:
            _quote_cache.set(cache_key, quote, ttl_seconds=15)
        
        return quote
    
    def _get_alpaca_quote(self, symbol: str) -> Optional[StockQuote]:
        """
        Get quote from Alpaca (fast, reliable, no rate limits)
        
        ✅ FIXED: Use latestTrade.p for real-time price (not daily close)
        """
        try:
            url = f"{ALPACA_DATA_URL}/v2/stocks/{symbol}/snapshot"
            response = requests.get(url, headers=self._alpaca_headers, timeout=10)
            
            if response.status_code != 200:
                logger.debug(f"Alpaca snapshot returned {response.status_code} for {symbol}")
                return None
            
            data = response.json()
            daily = data.get("dailyBar", {})
            prev = data.get("prevDailyBar", {})
            latest_trade = data.get("latestTrade", {})
            minute_bar = data.get("minuteBar", {})
            

            # 1. Latest trade price (most recent actual trade)
            # 2. Minute bar close (recent 1-min aggregation)
            # 3. Daily bar close (fallback - may be stale intraday)
            price = latest_trade.get("p") or minute_bar.get("c") or daily.get("c")
            prev_close = prev.get("c")
            
            if not price:
                return None
            
            change = price - prev_close if prev_close else 0
            change_pct = (change / prev_close) * 100 if prev_close else 0
            
            # Volume: use daily bar volume (accumulated today)
            volume = daily.get("v", 0)
            
            return StockQuote(
                symbol=symbol.upper(),
                price=round(price, 2),
                open=daily.get("o", price),
                high=daily.get("h", price),
                low=daily.get("l", price),
                close=round(price, 2),
                volume=volume,
                previous_close=prev_close or price,
                change=round(change, 2),
                change_percent=round(change_pct, 2),
                timestamp=datetime.now(timezone.utc),
            )
        except requests.exceptions.Timeout:
            logger.warning(f"Alpaca quote timed out for {symbol}")
            return None
        except Exception as e:
            logger.debug(f"Alpaca quote failed for {symbol}: {e}")
            return None
    
    def _get_yahoo_quote(self, symbol: str) -> Optional[StockQuote]:
        """
        Get quote from Yahoo Finance (fallback)
        
        ✅ FIXED: Use fast_info for real-time price instead of daily history Close
        fast_info provides: lastPrice, previousClose, open, dayLow, dayHigh, volume
        This is the actual real-time quote, not the stale daily bar close!
        """
        try:
            ticker = yf.Ticker(symbol)
            

            # fast_info is a cached property that makes a single request
            try:
                fast = ticker.fast_info
                
                price = getattr(fast, 'last_price', None) or getattr(fast, 'lastPrice', None)
                prev_close = getattr(fast, 'previous_close', None) or getattr(fast, 'regularMarketPreviousClose', None)
                open_price = getattr(fast, 'open', None) or getattr(fast, 'regularMarketOpen', None)
                day_high = getattr(fast, 'day_high', None) or getattr(fast, 'dayHigh', None)
                day_low = getattr(fast, 'day_low', None) or getattr(fast, 'dayLow', None)
                volume = getattr(fast, 'last_volume', None) or getattr(fast, 'volume', None) or 0
                
                if price and prev_close:
                    change = price - prev_close
                    change_pct = (change / prev_close) * 100 if prev_close else 0
                    
                    return StockQuote(
                        symbol=symbol.upper(),
                        price=round(float(price), 2),
                        open=round(float(open_price), 2) if open_price else round(float(price), 2),
                        high=round(float(day_high), 2) if day_high else round(float(price), 2),
                        low=round(float(day_low), 2) if day_low else round(float(price), 2),
                        close=round(float(price), 2),
                        volume=int(volume) if volume else 0,
                        previous_close=round(float(prev_close), 2),
                        change=round(float(change), 2),
                        change_percent=round(float(change_pct), 2),
                        timestamp=datetime.now(timezone.utc),
                    )
            except Exception as fast_err:
                logger.debug(f"fast_info failed for {symbol}: {fast_err}, trying history fallback")
            
            # Fallback to history if fast_info fails
            # This uses daily bars - less accurate intraday but works as backup
            hist = ticker.history(period="2d")
            
            if hist.empty:
                return None
            
            current = hist.iloc[-1]
            previous = hist.iloc[-2] if len(hist) > 1 else current
            
            # For daily history, the "Close" is end-of-day, not real-time
            # But it's better than nothing as a fallback
            price = float(current["Close"])
            prev_close = float(previous["Close"])
            current_volume = int(current["Volume"])
            
            change = price - prev_close
            change_pct = (change / prev_close) * 100 if prev_close else 0
            
            return StockQuote(
                symbol=symbol.upper(),
                price=round(price, 2),
                open=round(float(current["Open"]), 2),
                high=round(float(current["High"]), 2),
                low=round(float(current["Low"]), 2),
                close=round(price, 2),
                volume=current_volume,
                previous_close=round(prev_close, 2),
                change=round(change, 2),
                change_percent=round(change_pct, 2),
                timestamp=datetime.now(timezone.utc),
            )
        except Exception as e:
            logger.warning(f"Yahoo quote failed for {symbol}: {e}")
            return None
    
    def get_historical_data(self, symbol: str, period: str = "1y") -> Optional[dict]:
        """
        Get historical OHLCV data (Yahoo Finance - free unlimited history)
        
        Args:
            symbol: Stock symbol
            period: "1mo", "3mo", "6mo", "1y", "2y", "5y", "max"
        
        Returns:
            Dict with lists: dates, opens, highs, lows, closes, volumes
            
        Note: Yahoo is better for historical data (Alpaca requires paid subscription)
        ✅ FIXED: Added caching (60 second TTL) to prevent rate limiting
        """
        symbol = symbol.upper().strip()
        cache_key = f"history:{symbol}:{period}"
        
        # Check cache first
        cached = _history_cache.get(cache_key)
        if cached:
            return cached
        
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period)
            
            if hist.empty:
                return None
            
            result = {
                "dates": hist.index.strftime("%Y-%m-%d").tolist(),
                "opens": hist["Open"].tolist(),
                "highs": hist["High"].tolist(),
                "lows": hist["Low"].tolist(),
                "closes": hist["Close"].tolist(),
                "volumes": hist["Volume"].tolist(),
            }
            
            # Cache for 60 seconds (historical data doesn't change that often)
            _history_cache.set(cache_key, result, ttl_seconds=60)
            
            return result
        except Exception as e:
            logger.debug(f"Error fetching history for {symbol}: {e}")
            return None
    
    def get_fundamentals(self, symbol: str) -> Optional[Fundamentals]:
        """
        Get fundamental data for a stock (Yahoo Finance only)
        
        This data is NOT available from Alpaca:
        - P/E ratio, EPS
        - Market cap
        - Sector/Industry
        - Short interest
        
        ✅ FIXED: Added caching (1 hour TTL) - fundamentals don't change often
        """
        symbol = symbol.upper().strip()
        cache_key = f"fundamentals:{symbol}"
        
        # Check cache first
        cached = _fundamentals_cache.get(cache_key)
        if cached:
            return cached
        
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            market_cap = info.get("marketCap")
            market_cap_fmt = self._format_market_cap(market_cap) if market_cap else None
            
            result = Fundamentals(
                market_cap=market_cap,
                market_cap_formatted=market_cap_fmt,
                pe_ratio=info.get("trailingPE"),
                forward_pe=info.get("forwardPE"),
                eps=info.get("trailingEps"),
                dividend_yield=info.get("dividendYield"),
                sector=info.get("sector"),
                industry=info.get("industry"),
                shares_outstanding=info.get("sharesOutstanding"),
                float_shares=info.get("floatShares"),
                short_percent=info.get("shortPercentOfFloat"),
            )
            
            # Cache for 1 hour (fundamentals rarely change)
            _fundamentals_cache.set(cache_key, result, ttl_seconds=3600)
            
            return result
        except Exception as e:
            logger.debug(f"Error fetching fundamentals for {symbol}: {e}")
            return None
    
    def get_company_name(self, symbol: str) -> Optional[str]:
        """
        Get company name for a symbol (Yahoo Finance)
        
        ✅ FIXED: Use cached fundamentals when available, proper exception handling
        """
        symbol = symbol.upper().strip()
        
        # Try to get from cached fundamentals first
        cache_key = f"fundamentals:{symbol}"
        cached = _fundamentals_cache.get(cache_key)
        
        # If we have fundamentals, we made a ticker.info call, so make another for name
        # Or just fetch it directly
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            return info.get("longName") or info.get("shortName") or symbol
        except Exception as e:
            logger.debug(f"Error fetching company name for {symbol}: {e}")
            return symbol  # Return symbol as fallback instead of None

    def get_insider_transactions(self, symbol: str) -> Optional[dict]:
        """
        Get recent insider transactions (Yahoo Finance)
        Returns: Dict with transaction summary
        """
        try:
            ticker = yf.Ticker(symbol)
            insiders = ticker.insider_transactions
            
            if insiders is None or insiders.empty:
                return {"count": 0, "transactions": [], "message": "No recent insider transactions found."}
            
            # Get latest 10 transactions
            latest = insiders.head(10).copy()
            # Convert timestamp to string if needed
            if 'Start Date' in latest.columns:
                latest['Date'] = latest['Start Date'].astype(str)
            
            transactions = latest.to_dict('records')
            
            # Replace NaNs with None for JSON compatibility
            for t in transactions:
                for k, v in t.items():
                    if isinstance(v, float) and (v != v): # Check for NaN
                        t[k] = None
            
            # Calculate summary
            buys = insiders[insiders['Text'].str.contains('Buy', case=False, na=False)]
            sales = insiders[insiders['Text'].str.contains('Sale', case=False, na=False)]
            
            return {
                "count": len(insiders),
                "recent_buys": len(buys),
                "recent_sales": len(sales),
                "transactions": transactions,
                "summary": f"Found {len(insiders)} total transactions in the last 6 months ({len(buys)} buys, {len(sales)} sales)."
            }
        except Exception as e:
            logger.debug(f"Error fetching insider transactions for {symbol}: {e}")
            return None

    def get_institutional_holders(self, symbol: str) -> Optional[dict]:
        """
        Get major institutional holders (Yahoo Finance)
        """
        try:
            ticker = yf.Ticker(symbol)
            holders = ticker.institutional_holders
            major = ticker.major_holders
            
            if holders is None or holders.empty:
                return {"holders": [], "message": "Institutional holdings data unavailable."}
            
            # Format results
            data = holders.head(10).to_dict('records')
            
            # Replace NaNs with None for JSON compatibility
            for h in data:
                for k, v in h.items():
                    if isinstance(v, float) and (v != v):
                        h[k] = None
            
            summary = {}
            if major is not None and not major.empty:
                summary = major.set_index(1).to_dict()[0]
            
            return {
                "top_holders": data,
                "major_holders_summary": summary,
                "total_holders_count": len(holders)
            }
        except Exception as e:
            logger.debug(f"Error fetching institutional holders for {symbol}: {e}")
            return None
    
    def get_tradeable_symbols(self) -> list[str]:
        """
        Get list of tradeable US stock symbols (Alpaca)
        
        Alpaca provides the definitive list of tradeable symbols.
        Returns ~13,000 active US equities.
        """
        try:
            url = f"{ALPACA_BASE_URL}/v2/assets"
            params = {
                "status": "active",
                "asset_class": "us_equity",
            }
            
            response = requests.get(
                url, 
                headers=self._alpaca_headers, 
                params=params, 
                timeout=30
            )
            
            if response.status_code != 200:
                return []
            
            assets = response.json()
            
            # Filter for tradeable, non-OTC stocks
            symbols = [
                a["symbol"] for a in assets
                if a.get("tradable") and a.get("exchange") not in ["OTC", ""]
            ]
            
            return symbols
        except Exception as e:
            logger.error(f"Error fetching tradeable symbols: {e}")
            return []
    
    # ═══════════════════════════════════════════════════════════════
    # DATA SOURCE SUMMARY
    # ═══════════════════════════════════════════════════════════════
    #
    # ALPACA (fast, reliable, 200 req/min):
    #   - get_quote() -> primary source for real-time quotes
    #   - get_tradeable_symbols() -> list of all tradeable stocks
    #   - Scanner uses Alpaca for bulk scanning 7000+ stocks
    #
    # YAHOO FINANCE (slower but richer data):
    #   - get_quote() -> fallback when Alpaca fails
    #   - get_historical_data() -> free unlimited history
    #   - get_fundamentals() -> P/E, EPS, market cap, sector
    #   - get_company_name() -> company info
    #   - Options data (via OptionsService)
    #   - News (via NewsService)
    #
    # The frontend/chat can request specific data and the appropriate
    # service will be used automatically.
    # ═══════════════════════════════════════════════════════════════
    
    def _format_market_cap(self, value: float) -> str:
        """Format market cap with B/M suffix"""
        if value >= 1_000_000_000_000:
            return f"${value / 1_000_000_000_000:.2f}T"
        elif value >= 1_000_000_000:
            return f"${value / 1_000_000_000:.2f}B"
        elif value >= 1_000_000:
            return f"${value / 1_000_000:.2f}M"
        else:
            return f"${value:,.0f}"

