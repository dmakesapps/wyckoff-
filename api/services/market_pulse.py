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

from api.config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL, KIMI_MODEL

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
            # Check cache
            if not force_refresh and self._is_cache_valid():
                return self._cache
            
            # Generate new pulse
            pulse = self._generate_pulse()
            
            # Cache it
            self._cache = pulse
            self._cache_time = datetime.now(timezone.utc)
            
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
        
        # Step 2: Generate headlines with Kimi
        updates = self._generate_headlines(market_data)
        
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
    
    def _generate_headlines(self, market_data: Dict) -> List[Dict]:
        """Use Kimi to generate headlines from market data"""
        
        # Build prompt with market data
        prompt = self._build_prompt(market_data)
        
        try:
            # Call Kimi API
            response = requests.post(
                f"{OPENROUTER_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": KIMI_MODEL,
                    "messages": [
                        {"role": "system", "content": self._get_system_prompt()},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 1000,
                },
                timeout=30
            )
            
            response.raise_for_status()
            result = response.json()
            
            content = result["choices"][0]["message"]["content"]
            
            # Parse JSON from response
            updates = self._parse_headlines(content)
            
            return updates
            
        except Exception as e:
            logger.error(f"Kimi headline generation failed: {e}")
            # Return fallback headlines based on raw data
            return self._generate_fallback_headlines(market_data)
    
    def _get_system_prompt(self) -> str:
        return """You are a financial news editor for a trading platform. Your job is to write ONE concise headline (max 60 characters) for each market category.

Rules:
- No periods at the end
- Use specific numbers (e.g., "up 1.2%", "$105K", "near $2,100")
- Be informative, not clickbait
- Capture the key theme or movement
- If data shows gains, headline should reflect positive momentum
- If data shows losses, headline should reflect caution/decline
- Keep it professional like Bloomberg or CNBC

Output ONLY valid JSON array, no markdown, no explanation:
[
  {"category": "Markets", "headline": "...", "sentiment": "positive|negative|neutral"},
  {"category": "Crypto", "headline": "...", "sentiment": "positive|negative|neutral"},
  {"category": "Economy", "headline": "...", "sentiment": "positive|negative|neutral"},
  {"category": "Earnings", "headline": "...", "sentiment": "positive|negative|neutral"},
  {"category": "Tech", "headline": "...", "sentiment": "positive|negative|neutral"},
  {"category": "Commodities", "headline": "...", "sentiment": "positive|negative|neutral"}
]"""
    
    def _build_prompt(self, data: Dict) -> str:
        """Build prompt with market data for Kimi"""
        
        lines = ["Here's today's market data:\n"]
        
        # Markets
        lines.append("## MARKETS (Major Indices)")
        for name, quote in data.get("markets", {}).items():
            if quote:
                direction = "↑" if quote["change_percent"] >= 0 else "↓"
                lines.append(f"- {name}: ${quote['price']:,.2f} ({direction}{abs(quote['change_percent']):.2f}%)")
        
        # Crypto
        lines.append("\n## CRYPTO")
        for name, quote in data.get("crypto", {}).items():
            if quote:
                direction = "↑" if quote["change_percent"] >= 0 else "↓"
                price_str = f"${quote['price']:,.0f}" if quote['price'] > 1000 else f"${quote['price']:,.2f}"
                lines.append(f"- {name}: {price_str} ({direction}{abs(quote['change_percent']):.2f}%)")
        
        # Treasury/Economy
        lines.append("\n## ECONOMY")
        for name, quote in data.get("treasury", {}).items():
            if quote:
                lines.append(f"- {name} Yield: {quote['price']:.2f}%")
        for name, quote in data.get("currencies", {}).items():
            if quote:
                direction = "↑" if quote["change_percent"] >= 0 else "↓"
                lines.append(f"- {name}: {quote['price']:.2f} ({direction}{abs(quote['change_percent']):.2f}%)")
        
        # Tech
        lines.append("\n## TECH (Big Tech Movers)")
        tech_leaders = data.get("tech", {}).get("leaders", [])
        for stock in tech_leaders[:3]:
            direction = "↑" if stock["change_percent"] >= 0 else "↓"
            lines.append(f"- {stock['symbol']}: ${stock['price']:.2f} ({direction}{abs(stock['change_percent']):.2f}%)")
        
        # Commodities
        lines.append("\n## COMMODITIES")
        for name, quote in data.get("commodities", {}).items():
            if quote:
                direction = "↑" if quote["change_percent"] >= 0 else "↓"
                price_str = f"${quote['price']:,.2f}"
                lines.append(f"- {name}: {price_str} ({direction}{abs(quote['change_percent']):.2f}%)")
        
        lines.append("\n\nGenerate headlines for: Markets, Crypto, Economy, Earnings, Tech, Commodities")
        lines.append("For Earnings, focus on any notable tech earnings or general earnings sentiment.")
        
        return "\n".join(lines)
    
    def _parse_headlines(self, content: str) -> List[Dict]:
        """Parse JSON headlines from Kimi response"""
        try:
            # Try to extract JSON from response
            content = content.strip()
            
            # Remove markdown code blocks if present
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            
            updates = json.loads(content)
            
            # Validate structure
            valid_updates = []
            for update in updates:
                if isinstance(update, dict) and "category" in update and "headline" in update:
                    valid_updates.append({
                        "category": update["category"],
                        "headline": update["headline"][:80],  # Enforce max length
                        "sentiment": update.get("sentiment", "neutral"),
                    })
            
            return valid_updates
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Kimi JSON: {e}")
            return []
    
    def _generate_fallback_headlines(self, data: Dict) -> List[Dict]:
        """Generate basic headlines from raw data (no AI)"""
        updates = []
        
        # Markets
        sp500 = data.get("markets", {}).get("S&P 500", {})
        if sp500:
            direction = "rises" if sp500["change_percent"] >= 0 else "falls"
            updates.append({
                "category": "Markets",
                "headline": f"S&P 500 {direction} {abs(sp500['change_percent']):.1f}% in trading",
                "sentiment": "positive" if sp500["change_percent"] >= 0 else "negative",
            })
        
        # Crypto
        btc = data.get("crypto", {}).get("Bitcoin", {})
        if btc:
            price_k = btc["price"] / 1000
            direction = "up" if btc["change_percent"] >= 0 else "down"
            updates.append({
                "category": "Crypto",
                "headline": f"Bitcoin {direction} {abs(btc['change_percent']):.1f}% near ${price_k:.0f}K",
                "sentiment": "positive" if btc["change_percent"] >= 0 else "negative",
            })
        
        # Economy
        treasury = data.get("treasury", {}).get("10Y Treasury", {})
        if treasury:
            updates.append({
                "category": "Economy",
                "headline": f"10-year Treasury yield at {treasury['price']:.2f}%",
                "sentiment": "neutral",
            })
        
        # Tech
        tech_top = data.get("tech", {}).get("top_mover", {})
        if tech_top:
            direction = "leads gains" if tech_top["change"] >= 0 else "leads decline"
            updates.append({
                "category": "Tech",
                "headline": f"{tech_top['symbol']} {direction} with {abs(tech_top['change']):.1f}% move",
                "sentiment": "positive" if tech_top["change"] >= 0 else "negative",
            })
        
        # Commodities
        gold = data.get("commodities", {}).get("Gold", {})
        if gold:
            direction = "rises" if gold["change_percent"] >= 0 else "falls"
            updates.append({
                "category": "Commodities",
                "headline": f"Gold {direction} to ${gold['price']:,.0f} per ounce",
                "sentiment": "positive" if gold["change_percent"] >= 0 else "negative",
            })
        
        # Earnings (generic since we don't have specific data)
        updates.append({
            "category": "Earnings",
            "headline": "Earnings season continues with mixed results",
            "sentiment": "neutral",
        })
        
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


# Singleton instance
market_pulse_service = MarketPulseService(cache_minutes=15)

