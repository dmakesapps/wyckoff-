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
from datetime import datetime, timezone
from typing import Optional
import requests
import logging

from api.config import ALPACA_API_KEY, ALPACA_SECRET_KEY, ALPACA_DATA_URL, ALPACA_BASE_URL
from api.models.stock import StockQuote, Fundamentals

logger = logging.getLogger(__name__)


class StockDataService:
    """
    Hybrid data service - uses Alpaca for speed, Yahoo for depth
    
    Alpaca: Real-time quotes, bulk scanning
    Yahoo: Options, fundamentals, sector data
    """
    
    def __init__(self):
        self._alpaca_headers = {
            "APCA-API-KEY-ID": ALPACA_API_KEY,
            "APCA-API-SECRET-KEY": ALPACA_SECRET_KEY,
        }
        self._use_alpaca_quotes = True  # Try Alpaca first for quotes
    
    def get_quote(self, symbol: str, prefer_alpaca: bool = True) -> Optional[StockQuote]:
        """
        Get current quote - tries Alpaca first (faster), falls back to Yahoo
        """
        if prefer_alpaca and self._use_alpaca_quotes:
            quote = self._get_alpaca_quote(symbol)
            if quote:
                return quote
        
        # Fallback to Yahoo
        return self._get_yahoo_quote(symbol)
    
    def _get_alpaca_quote(self, symbol: str) -> Optional[StockQuote]:
        """Get quote from Alpaca (fast, reliable, no rate limits)"""
        try:
            url = f"{ALPACA_DATA_URL}/v2/stocks/{symbol}/snapshot"
            response = requests.get(url, headers=self._alpaca_headers, timeout=10)
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            daily = data.get("dailyBar", {})
            prev = data.get("prevDailyBar", {})
            latest = data.get("latestTrade", {})
            
            price = daily.get("c") or latest.get("p")
            prev_close = prev.get("c")
            
            if not price:
                return None
            
            change = price - prev_close if prev_close else 0
            change_pct = (change / prev_close) * 100 if prev_close else 0
            
            return StockQuote(
                symbol=symbol.upper(),
                price=price,
                open=daily.get("o", price),
                high=daily.get("h", price),
                low=daily.get("l", price),
                close=price,
                volume=daily.get("v", 0),
                previous_close=prev_close or price,
                change=change,
                change_percent=change_pct,
                timestamp=datetime.now(timezone.utc),
            )
        except Exception as e:
            logger.debug(f"Alpaca quote failed for {symbol}: {e}")
            return None
    
    def _get_yahoo_quote(self, symbol: str) -> Optional[StockQuote]:
        """Get quote from Yahoo Finance (fallback, has more detail)"""
        try:
            ticker = yf.Ticker(symbol)
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
            logger.debug(f"Yahoo quote failed for {symbol}: {e}")
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
        """
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
            logger.debug(f"Error fetching fundamentals for {symbol}: {e}")
            return None
    
    def get_company_name(self, symbol: str) -> Optional[str]:
        """Get company name for a symbol (Yahoo Finance)"""
        try:
            ticker = yf.Ticker(symbol)
            return ticker.info.get("longName") or ticker.info.get("shortName")
        except:
            return None

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

