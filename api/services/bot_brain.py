"""
AlphaBot Brain - Market Data Orchestrator
Fetches real-time price from Alpaca and deep stats from yfinance.
"""

import asyncio
import logging
import time
import json
import os
from typing import Dict, Any, Optional
import yfinance as yf
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Try importing Alpaca, make it optional to avoid crash if not installed
try:
    import alpaca_trade_api as tradeapi
    ALPACA_AVAILABLE: bool = True
except ImportError:
    ALPACA_AVAILABLE: bool = False

# Configure logging
logger = logging.getLogger(__name__)

class BotBrain:
    """
    Orchestrator for fetching market data.
    Hybrid Logic:
    - Current Price: Alpaca (Real-time)
    - Fundamentals/Technicals: Yahoo Finance (Deep Data)
    """
    
    def __init__(self) -> None:
        # In-memory cache
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_ttl: int = 60  # 60 seconds

        # Initialize Alpaca
        self.alpaca: Optional[tradeapi.REST] = None
        if ALPACA_AVAILABLE:
            api_key = os.getenv("ALPACA_API_KEY")
            secret_key = os.getenv("ALPACA_SECRET_KEY")
            endpoint = os.getenv("ALPACA_ENDPOINT", "https://paper-api.alpaca.markets")
            
            if api_key and secret_key:
                try:
                    self.alpaca = tradeapi.REST(api_key, secret_key, endpoint, api_version='v2')
                    logger.info("Alpaca API connection initialized.")
                except Exception as e:
                    logger.error(f"Failed to connect to Alpaca: {e}")
            else:
                logger.warning("Alpaca keys not found in environment.")
        else:
            logger.warning("alpaca-trade-api not installed.")

    def _get_from_cache(self, key: str) -> Any:
        if key in self._cache:
            cached_data = self._cache[key]
            if time.time() - cached_data["timestamp"] < self._cache_ttl:
                return cached_data["data"]
        return None

    def _set_cache(self, key: str, data: Any) -> None:
        self._cache[key] = {
            "data": data,
            "timestamp": time.time()
        }

    async def get_alpha_data(self, ticker: str) -> Dict[str, Any]:
        """Fetch alpha data using Hybrid approach."""
        ticker = ticker.upper()
        cache_key = f"alpha_{ticker}"
        
        # Check cache
        cached_data = self._get_from_cache(cache_key)
        if cached_data is not None:
            return cached_data
        
        logger.info(f"Fetching hybrid data for {ticker}..")
        
        # 1. Fetch YFinance Data (Base)
        # We run this in a thread because yfinance is blocking
        try:
            yf_data = await asyncio.to_thread(self._fetch_yfinance_data, ticker)
        except Exception as e:
            logger.error(f"YFinance failed: {e}")
            yf_data = {"error": str(e), "price_data": {}, "technicals": {}, "fundamental_summary": {}}

        # 2. Fetch Alpaca Price (Real-time Override)
        alpaca_price = None
        if self.alpaca:
            try:
                alpaca_price = await asyncio.to_thread(self._fetch_alpaca_price, ticker)
            except Exception as e:
                logger.error(f"Alpaca failed: {e}")

        # 3. Merge Data
        if alpaca_price:
            logger.info(f"Overwriting YFinance price {yf_data.get('price_data', {}).get('current')} with Alpaca price {alpaca_price}")
            if "price_data" not in yf_data:
                yf_data["price_data"] = {}
            yf_data["price_data"]["current"] = alpaca_price
            yf_data["source"] = "Hybrid (Alpaca + YFinance)"
        else:
            yf_data["source"] = "YFinance Only"

        # Cache result
        self._set_cache(cache_key, yf_data)
        return yf_data

    def _fetch_alpaca_price(self, ticker: str) -> float:
        """Get latest trade price from Alpaca."""
        # Get latest trade
        trade = self.alpaca.get_latest_trade(ticker)
        return float(trade.price)

    def _fetch_yfinance_data(self, ticker: str) -> Dict[str, Any]:
        """Fetch deep stats from yfinance."""
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # Extract price (backup)
            current = info.get("currentPrice") or info.get("regularMarketPrice") or 0.0
            volume = info.get("volume") or info.get("regularMarketVolume") or 0
            
            result = {
                "ticker": ticker,
                "price_data": {
                    "current": current,
                    "volume": volume,
                    "rel_volume": 1.0 
                },
                "fundamental_summary": {
                    "market_cap": info.get("marketCap"),
                    "sector": info.get("sector"),
                    "industry": info.get("industry")
                },
                "technicals": {},
                "timestamp": time.time()
            }
            
            # Simple technicals
            hist = stock.history(period="1y")
            if not hist.empty:
                sma_50 = hist["Close"].rolling(window=50).mean().iloc[-1]
                sma_200 = hist["Close"].rolling(window=200).mean().iloc[-1]
                
                result["technicals"] = {
                    "sma_50": sma_50,
                    "sma_200": sma_200,
                    "trend": "Bullish" if sma_50 > sma_200 else "Bearish"
                }
                
            return result
        except Exception as e:
            logger.error(f"yfinance internal error: {e}")
            raise e

# Singleton instance
bot_brain: BotBrain = BotBrain()