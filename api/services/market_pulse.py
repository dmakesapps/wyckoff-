# api/services/market_pulse.py

"""
Market Pulse Service - AI-generated bite-sized market updates
Powers the "What's happening today" section
"""

import yfinance as yf
import requests
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List
import threading

from api.config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL, PULSE_MODEL

logger = logging.getLogger(__name__)


class MarketPulseService:
    """
    Generates bite-sized AI market updates across multiple categories.
    Caches results for 15 minutes to avoid excessive API calls.
    """
    
    # Market data symbols
    INDICES = {
        "SPY": "S&P 500",
        "QQQ": "NASDAQ",
        "DIA": "Dow Jones",
    }
    
    CRYPTO = {
        "BTC-USD": "Bitcoin",
        "ETH-USD": "Ethereum",
    }
    
    COMMODITIES = {
        "GC=F": "Gold",
        "CL=F": "Oil (WTI)",
    }
    
    TREASURY = {
        "^TNX": "10Y Treasury",
    }
    
    CURRENCIES = {
        "DX-Y.NYB": "US Dollar Index",
    }
    
    # Tech leaders for tech category
    TECH_LEADERS = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA"]
    
    def __init__(self, cache_minutes: int = 15):
        self.cache_minutes = cache_minutes
        self._cache: Optional[Dict] = None
        self._cache_time: Optional[datetime] = None
        self._lock = threading.Lock()
    
    def get_pulse(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Get market pulse updates. Returns cached data if fresh.
        
        Args:
            force_refresh: Force regeneration even if cache is valid
            
        Returns:
            Dict with updates array and metadata
        """
        with self._lock:
            # Check cache - but only if it has actual updates
            if not force_refresh and self._is_cache_valid():
                if self._cache and self._cache.get("updates"):
                    return self._cache
            
            # Generate new pulse
            pulse = self._generate_pulse()
            
            # Only cache if we got valid updates
            if pulse.get("updates"):
                self._cache = pulse
                self._cache_time = datetime.now(timezone.utc)
                logger.info(f"Cached market pulse with {len(pulse['updates'])} updates")
            else:
                logger.warning("Generated pulse has no updates, not caching")
            
            return pulse
    
    def _is_cache_valid(self) -> bool:
        """Check if cache is still fresh"""
        if self._cache is None or self._cache_time is None:
            return False
        
        age = datetime.now(timezone.utc) - self._cache_time
        return age.total_seconds() < (self.cache_minutes * 60)
    
    def _generate_pulse(self) -> Dict[str, Any]:
        """Generate fresh market pulse data"""
        logger.info("Generating fresh market pulse...")
        
        # Step 1: Gather all market data
        market_data = self._fetch_all_market_data()
        
        # Step 2: Generate headlines (Non-AI Fallback)
        updates = self._generate_fallback_headlines(market_data)
        
        # Step 3: Build response
        now = datetime.now(timezone.utc)
        expires = now + timedelta(minutes=self.cache_minutes)
        
        return {
            "generated_at": now.isoformat(),
            "updates": updates,
            "cache_expires_at": expires.isoformat(),
            "raw_data": market_data,  # Include raw data for debugging/advanced use
        }
    
    def _fetch_all_market_data(self) -> Dict[str, Any]:
        """Fetch all market data from various sources"""
        data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "markets": {},
            "crypto": {},
            "commodities": {},
            "treasury": {},
            "currencies": {},
            "tech": {},
            "top_movers": [],
        }
        
        # Fetch indices
        for symbol, name in self.INDICES.items():
            quote = self._get_quote(symbol)
            if quote:
                data["markets"][name] = quote
        
        # Fetch crypto
        for symbol, name in self.CRYPTO.items():
            quote = self._get_quote(symbol)
            if quote:
                data["crypto"][name] = quote
        
        # Fetch commodities
        for symbol, name in self.COMMODITIES.items():
            quote = self._get_quote(symbol)
            if quote:
                data["commodities"][name] = quote
        
        # Fetch treasury
        for symbol, name in self.TREASURY.items():
            quote = self._get_quote(symbol)
            if quote:
                data["treasury"][name] = quote
        
        # Fetch USD index
        for symbol, name in self.CURRENCIES.items():
            quote = self._get_quote(symbol)
            if quote:
                data["currencies"][name] = quote
        
        # Fetch tech leaders
        tech_quotes = []
        for symbol in self.TECH_LEADERS:
            quote = self._get_quote(symbol)
            if quote:
                quote["symbol"] = symbol
                tech_quotes.append(quote)
        
        # Sort by change to find biggest mover
        tech_quotes.sort(key=lambda x: abs(x.get("change_percent", 0)), reverse=True)
        data["tech"]["leaders"] = tech_quotes[:5]
        
        # Find top mover
        if tech_quotes:
            top = tech_quotes[0]
            data["tech"]["top_mover"] = {
                "symbol": top["symbol"],
                "change": top.get("change_percent", 0),
                "price": top.get("price", 0),
            }
        
        return data
    
    def _get_quote(self, symbol: str) -> Optional[Dict]:
        """Get current quote for a symbol"""
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="2d")
            
            if hist.empty:
                return None
            
            current = hist.iloc[-1]
            prev_close = hist.iloc[-2]["Close"] if len(hist) > 1 else current["Open"]
            
            price = float(current["Close"])
            change = price - prev_close
            change_pct = (change / prev_close) * 100 if prev_close else 0
            
            return {
                "price": round(price, 2),
                "change": round(change, 2),
                "change_percent": round(change_pct, 2),
                "direction": "up" if change >= 0 else "down",
            }
        except Exception as e:
            logger.warning(f"Failed to get quote for {symbol}: {e}")
            return None
    
    # Removed AI methods to strip AI dependency. Using fallback headlines only.
    
    def _generate_fallback_headlines(self, data: Dict) -> List[Dict]:
        """Generate basic headlines from raw data (no AI) - ALWAYS returns 6 categories"""
        logger.info("Generating fallback headlines from raw data")
        updates = []
        
        # Markets - always include
        sp500 = data.get("markets", {}).get("S&P 500", {})
        nasdaq = data.get("markets", {}).get("NASDAQ", {})
        if sp500:
            direction = "rises" if sp500.get("change_percent", 0) >= 0 else "falls"
            pct = abs(sp500.get("change_percent", 0))
            updates.append({
                "category": "Markets",
                "headline": f"S&P 500 {direction} {pct:.1f}% in trading",
                "sentiment": "positive" if sp500.get("change_percent", 0) >= 0 else "negative",
            })
        elif nasdaq:
            direction = "rises" if nasdaq.get("change_percent", 0) >= 0 else "falls"
            pct = abs(nasdaq.get("change_percent", 0))
            updates.append({
                "category": "Markets",
                "headline": f"NASDAQ {direction} {pct:.1f}% in trading",
                "sentiment": "positive" if nasdaq.get("change_percent", 0) >= 0 else "negative",
            })
        else:
            updates.append({
                "category": "Markets",
                "headline": "Markets trading in mixed territory",
                "sentiment": "neutral",
            })
        
        # Crypto - always include
        btc = data.get("crypto", {}).get("Bitcoin", {})
        if btc and btc.get("price"):
            price_k = btc["price"] / 1000
            direction = "up" if btc.get("change_percent", 0) >= 0 else "down"
            pct = abs(btc.get("change_percent", 0))
            updates.append({
                "category": "Crypto",
                "headline": f"Bitcoin {direction} {pct:.1f}% near ${price_k:.0f}K",
                "sentiment": "positive" if btc.get("change_percent", 0) >= 0 else "negative",
            })
        else:
            updates.append({
                "category": "Crypto",
                "headline": "Crypto markets showing mixed signals",
                "sentiment": "neutral",
            })
        
        # Economy - always include
        treasury = data.get("treasury", {}).get("10Y Treasury", {})
        if treasury and treasury.get("price"):
            updates.append({
                "category": "Economy",
                "headline": f"10-year Treasury yield at {treasury['price']:.2f}%",
                "sentiment": "neutral",
            })
        else:
            updates.append({
                "category": "Economy",
                "headline": "Economic indicators remain stable",
                "sentiment": "neutral",
            })
        
        # Earnings - always include (generic)
        updates.append({
            "category": "Earnings",
            "headline": "Earnings season continues with mixed results",
            "sentiment": "neutral",
        })
        
        # Tech - always include
        tech_top = data.get("tech", {}).get("top_mover", {})
        if tech_top and tech_top.get("symbol"):
            direction = "leads gains" if tech_top.get("change", 0) >= 0 else "leads decline"
            pct = abs(tech_top.get("change", 0))
            updates.append({
                "category": "Tech",
                "headline": f"{tech_top['symbol']} {direction} with {pct:.1f}% move",
                "sentiment": "positive" if tech_top.get("change", 0) >= 0 else "negative",
            })
        else:
            updates.append({
                "category": "Tech",
                "headline": "Tech stocks trading in mixed territory",
                "sentiment": "neutral",
            })
        
        # Commodities - always include
        gold = data.get("commodities", {}).get("Gold", {})
        oil = data.get("commodities", {}).get("Oil (WTI)", {})
        if gold and gold.get("price"):
            direction = "rises" if gold.get("change_percent", 0) >= 0 else "falls"
            updates.append({
                "category": "Commodities",
                "headline": f"Gold {direction} to ${gold['price']:,.0f} per ounce",
                "sentiment": "positive" if gold.get("change_percent", 0) >= 0 else "negative",
            })
        elif oil and oil.get("price"):
            direction = "rises" if oil.get("change_percent", 0) >= 0 else "falls"
            updates.append({
                "category": "Commodities",
                "headline": f"Oil {direction} to ${oil['price']:.2f} per barrel",
                "sentiment": "positive" if oil.get("change_percent", 0) >= 0 else "negative",
            })
        else:
            updates.append({
                "category": "Commodities",
                "headline": "Commodities trading in narrow range",
                "sentiment": "neutral",
            })
        
        logger.info(f"Generated {len(updates)} fallback headlines")
        return updates
    
    def get_cache_status(self) -> Dict:
        """Get current cache status"""
        if self._cache_time:
            age = (datetime.now(timezone.utc) - self._cache_time).total_seconds()
            expires_in = max(0, (self.cache_minutes * 60) - age)
        else:
            age = None
            expires_in = 0
        
        return {
            "cached": self._cache is not None,
            "cache_age_seconds": age,
            "expires_in_seconds": expires_in,
            "cache_minutes": self.cache_minutes,
        }


# Singleton instance - cache for 1 hour to minimize API costs
market_pulse_service = MarketPulseService(cache_minutes=60)

