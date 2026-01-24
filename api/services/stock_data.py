# api/services/stock_data.py

"""
Stock data fetching service using yfinance and Alpaca
"""

import yfinance as yf
from datetime import datetime, timezone
from typing import Optional
import requests

from api.config import ALPACA_API_KEY, ALPACA_SECRET_KEY, ALPACA_DATA_URL, ALPACA_BASE_URL
from api.models.stock import StockQuote, Fundamentals


class StockDataService:
    """Service for fetching stock data"""
    
    def __init__(self):
        self._alpaca_headers = {
            "APCA-API-KEY-ID": ALPACA_API_KEY,
            "APCA-API-SECRET-KEY": ALPACA_SECRET_KEY,
        }
    
    def get_quote(self, symbol: str) -> Optional[StockQuote]:
        """Get current quote for a stock"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            hist = ticker.history(period="2d")
            
            if hist.empty:
                return None
            
            current = hist.iloc[-1]
            previous = hist.iloc[-2] if len(hist) > 1 else current
            
            price = float(current["Close"])
            prev_close = float(previous["Close"])
            change = price - prev_close
            change_pct = (change / prev_close) * 100 if prev_close else 0
            
            return StockQuote(
                symbol=symbol.upper(),
                price=price,
                open=float(current["Open"]),
                high=float(current["High"]),
                low=float(current["Low"]),
                close=price,
                volume=int(current["Volume"]),
                previous_close=prev_close,
                change=change,
                change_percent=change_pct,
                timestamp=datetime.now(timezone.utc),
            )
        except Exception as e:
            print(f"Error fetching quote for {symbol}: {e}")
            return None
    
    def get_historical_data(self, symbol: str, period: str = "1y") -> Optional[dict]:
        """
        Get historical OHLCV data
        
        Args:
            symbol: Stock symbol
            period: "1mo", "3mo", "6mo", "1y", "2y", "5y", "max"
        
        Returns:
            Dict with lists: dates, opens, highs, lows, closes, volumes
        """
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period)
            
            if hist.empty:
                return None
            
            return {
                "dates": hist.index.strftime("%Y-%m-%d").tolist(),
                "opens": hist["Open"].tolist(),
                "highs": hist["High"].tolist(),
                "lows": hist["Low"].tolist(),
                "closes": hist["Close"].tolist(),
                "volumes": hist["Volume"].tolist(),
            }
        except Exception as e:
            print(f"Error fetching history for {symbol}: {e}")
            return None
    
    def get_fundamentals(self, symbol: str) -> Optional[Fundamentals]:
        """Get fundamental data for a stock"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            market_cap = info.get("marketCap")
            market_cap_fmt = self._format_market_cap(market_cap) if market_cap else None
            
            return Fundamentals(
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
        except Exception as e:
            print(f"Error fetching fundamentals for {symbol}: {e}")
            return None
    
    def get_company_name(self, symbol: str) -> Optional[str]:
        """Get company name for a symbol"""
        try:
            ticker = yf.Ticker(symbol)
            return ticker.info.get("longName") or ticker.info.get("shortName")
        except:
            return None
    
    def get_tradeable_symbols(self) -> list[str]:
        """Get list of tradeable US stock symbols from Alpaca"""
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
            print(f"Error fetching tradeable symbols: {e}")
            return []
    
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

