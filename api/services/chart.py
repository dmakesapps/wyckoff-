# api/services/chart.py

"""
Chart data service for Lightweight Charts integration
Fetches OHLCV data from Yahoo Finance and calculates indicators
"""

import yfinance as yf
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


class ChartService:
    """
    Provides chart data formatted for Lightweight Charts library.
    
    Data format (flat structure for direct Lightweight Charts consumption):
    - candlestick: [{ time, open, high, low, close }]
    - volume: [{ time, value, color }]
    - sma_20/50/200: [{ time, value }]
    - rsi: [{ time, value }]
    """
    
    # Valid intervals and their Yahoo Finance equivalents
    INTERVALS = {
        "1m": "1m",      # Last 7 days only
        "5m": "5m",      # Last 60 days
        "15m": "15m",    # Last 60 days
        "30m": "30m",    # Last 60 days
        "1h": "1h",      # Last 730 days
        "1d": "1d",      # Years of data
        "1wk": "1wk",    # Years of data
        "1mo": "1mo",    # Years of data
    }
    
    # Valid periods
    PERIODS = {
        "5d": "5d",
        "7d": "7d",
        "1mo": "1mo",
        "3mo": "3mo",
        "6mo": "6mo",
        "1y": "1y",
        "2y": "2y",
        "5y": "5y",
        "10y": "10y",
        "max": "max",
    }
    
    # Map periods to extended periods (to get previous close)
    EXTENDED_PERIODS = {
        "5d": "1mo",      # Need extra days for 5d
        "7d": "1mo",      # Need extra days for 7d
        "1mo": "3mo",     # Need extra month for 1mo
        "3mo": "6mo",     # etc.
        "6mo": "1y",
        "1y": "2y",
        "2y": "5y",
        "5y": "10y",
        "10y": "max",
        "max": "max",
    }
    
    def get_chart_data(
        self,
        symbol: str,
        interval: str = "1d",
        period: str = "1y",
        indicators: List[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get chart data for a symbol with optional indicators.
        
        Args:
            symbol: Stock ticker (e.g., "AAPL")
            interval: Candle interval (1m, 5m, 15m, 30m, 1h, 1d, 1wk, 1mo)
            period: How far back (5d, 7d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, max)
            indicators: List of indicators ["sma_20", "sma_50", "sma_200", "rsi", "volume"]
        
        Returns:
            Dict with candlestick, volume, and indicator data formatted for Lightweight Charts
            Includes periodPreviousClose in meta for accurate period return calculations
        """
        # Validate inputs
        if interval not in self.INTERVALS:
            interval = "1d"
        if period not in self.PERIODS:
            period = "1y"
        
        # Default indicators
        if indicators is None:
            indicators = ["sma_20", "sma_50", "sma_200", "rsi", "volume"]
        
        try:
            ticker = yf.Ticker(symbol)
            
            # Fetch extended historical data to get previous close
            extended_period = self.EXTENDED_PERIODS.get(period, period)
            hist = ticker.history(period=extended_period, interval=interval)
            
            if hist.empty:
                logger.warning(f"No data found for {symbol}")
                return None
            
            # Determine how many candles to return based on requested period
            requested_candles = self._period_to_candles(period, interval, len(hist))
            
            # Extract previous close (the close BEFORE the requested period starts)
            period_previous_close = None
            if len(hist) > requested_candles:
                # Get the close of the day before our period starts
                extra_data = hist.iloc[:len(hist) - requested_candles]
                if not extra_data.empty:
                    period_previous_close = round(float(extra_data.iloc[-1]["Close"]), 2)
            
            # Trim to requested period (most recent candles)
            if len(hist) > requested_candles:
                hist = hist.tail(requested_candles)
            
            # Convert to Lightweight Charts format
            result = self._format_chart_data(
                symbol, hist, indicators, interval, 
                period_previous_close=period_previous_close
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error fetching chart data for {symbol}: {e}")
            return None
    
    def _period_to_candles(self, period: str, interval: str, max_available: int) -> int:
        """Convert period string to approximate number of candles"""
        # Approximate trading days per period
        period_days = {
            "5d": 5,
            "7d": 7,
            "1mo": 22,
            "3mo": 65,
            "6mo": 130,
            "1y": 252,
            "2y": 504,
            "5y": 1260,
            "10y": 2520,
            "max": max_available,
        }
        
        days = period_days.get(period, 252)
        
        # Adjust for interval (intraday has more candles per day)
        if interval == "1m":
            return min(days * 390, max_available)  # ~390 minutes per trading day
        elif interval == "5m":
            return min(days * 78, max_available)
        elif interval == "15m":
            return min(days * 26, max_available)
        elif interval == "30m":
            return min(days * 13, max_available)
        elif interval == "1h":
            return min(days * 7, max_available)
        elif interval == "1wk":
            return min(days // 5, max_available)
        elif interval == "1mo":
            return min(days // 22, max_available)
        else:  # 1d
            return min(days, max_available)
    
    def get_mini_chart(
        self,
        symbol: str,
        period: str = "3mo",
        candles: int = 50
    ) -> Optional[Dict[str, Any]]:
        """
        Get mini chart data for Kimi chat responses.
        Lighter weight - fewer candles, basic indicators only.
        
        Args:
            symbol: Stock ticker
            period: How far back (default 3mo)
            candles: Max number of candles to return (default 50)
        
        Returns:
            Compact chart data for inline display with periodPreviousClose
        """
        try:
            ticker = yf.Ticker(symbol)
            
            # Fetch extra data to get previous close
            extended_period = self.EXTENDED_PERIODS.get(period, "6mo")
            hist = ticker.history(period=extended_period, interval="1d")
            
            if hist.empty:
                return None
            
            # Get previous close before limiting to requested candles
            period_previous_close = None
            if len(hist) > candles:
                extra_data = hist.iloc[:len(hist) - candles]
                if not extra_data.empty:
                    period_previous_close = round(float(extra_data.iloc[-1]["Close"]), 2)
            
            # Limit to requested candles (most recent)
            if len(hist) > candles:
                hist = hist.tail(candles)
            
            # Mini chart only includes basic indicators
            result = self._format_chart_data(
                symbol, 
                hist, 
                indicators=["sma_20", "volume"],
                interval="1d",
                is_mini=True,
                period_previous_close=period_previous_close
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error fetching mini chart for {symbol}: {e}")
            return None
    
    def _format_chart_data(
        self,
        symbol: str,
        hist,
        indicators: List[str],
        interval: str,
        is_mini: bool = False,
        period_previous_close: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Format pandas DataFrame to Lightweight Charts format.
        
        Lightweight Charts expects:
        - time: Unix timestamp (seconds) or 'YYYY-MM-DD' string
        - For candlestick: open, high, low, close
        - For line/histogram: value
        
        Args:
            period_previous_close: The closing price of the day BEFORE the period started.
                                   Used for accurate period return calculations.
        """
        
        # Convert index to timestamps
        # Use date string for daily+ intervals, unix timestamp for intraday
        use_date_string = interval in ["1d", "1wk", "1mo"]
        
        def format_time(dt):
            if use_date_string:
                return dt.strftime("%Y-%m-%d")
            else:
                return int(dt.timestamp())
        
        # Build candlestick data
        candlestick = []
        volume_data = []
        closes = []
        
        for idx, row in hist.iterrows():
            time_val = format_time(idx)
            
            candlestick.append({
                "time": time_val,
                "open": round(row["Open"], 2),
                "high": round(row["High"], 2),
                "low": round(row["Low"], 2),
                "close": round(row["Close"], 2),
            })
            
            closes.append(row["Close"])
            
            # Volume with color (green if close > open, red otherwise)
            if "volume" in indicators:
                color = "#26a69a" if row["Close"] >= row["Open"] else "#ef5350"
                volume_data.append({
                    "time": time_val,
                    "value": int(row["Volume"]),
                    "color": color,
                })
        
        # Build result
        result = {
            "symbol": symbol.upper(),
            "interval": interval,
            "dataPoints": len(candlestick),
            "candlestick": candlestick,
        }
        
        if volume_data:
            result["volume"] = volume_data
        
        # Calculate and add indicators
        times = [c["time"] for c in candlestick]
        
        if "sma_20" in indicators:
            sma_20 = self._calculate_sma(closes, 20)
            result["sma_20"] = self._format_indicator(times, sma_20)
        
        if "sma_50" in indicators:
            sma_50 = self._calculate_sma(closes, 50)
            result["sma_50"] = self._format_indicator(times, sma_50)
        
        if "sma_200" in indicators:
            sma_200 = self._calculate_sma(closes, 200)
            result["sma_200"] = self._format_indicator(times, sma_200)
        
        if "rsi" in indicators and not is_mini:
            rsi = self._calculate_rsi(closes, 14)
            result["rsi"] = self._format_indicator(times, rsi)
        
        # Add metadata
        if candlestick:
            last_price = candlestick[-1]["close"]
            first_open = candlestick[0]["open"]
            
            # Calculate period change using proper previous close
            if period_previous_close is not None:
                period_change = round(((last_price - period_previous_close) / period_previous_close) * 100, 2)
            else:
                # Fallback: use first candle's open (less accurate)
                period_change = round(((last_price - first_open) / first_open) * 100, 2)
            
            result["meta"] = {
                "firstDate": candlestick[0]["time"],
                "lastDate": candlestick[-1]["time"],
                "firstOpen": first_open,
                "lastPrice": last_price,
                "lastVolume": volume_data[-1]["value"] if volume_data else None,
                "periodPreviousClose": period_previous_close,  # Key field for accurate returns
                "periodChange": period_change,  # Pre-calculated for convenience
            }
        
        return result
    
    def _calculate_sma(self, closes: List[float], period: int) -> List[Optional[float]]:
        """Calculate Simple Moving Average"""
        sma = []
        for i in range(len(closes)):
            if i < period - 1:
                sma.append(None)
            else:
                window = closes[i - period + 1:i + 1]
                sma.append(round(sum(window) / period, 2))
        return sma
    
    def _calculate_rsi(self, closes: List[float], period: int = 14) -> List[Optional[float]]:
        """Calculate Relative Strength Index"""
        if len(closes) < period + 1:
            return [None] * len(closes)
        
        rsi = [None] * len(closes)
        
        # Calculate price changes
        deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
        
        # Initialize with first period
        gains = []
        losses = []
        
        for i, delta in enumerate(deltas):
            if i < period:
                if delta > 0:
                    gains.append(delta)
                    losses.append(0)
                else:
                    gains.append(0)
                    losses.append(abs(delta))
                
                if i == period - 1:
                    avg_gain = sum(gains) / period
                    avg_loss = sum(losses) / period
                    
                    if avg_loss == 0:
                        rsi[i + 1] = 100
                    else:
                        rs = avg_gain / avg_loss
                        rsi[i + 1] = round(100 - (100 / (1 + rs)), 2)
            else:
                # Smoothed RSI calculation
                if delta > 0:
                    current_gain = delta
                    current_loss = 0
                else:
                    current_gain = 0
                    current_loss = abs(delta)
                
                avg_gain = (avg_gain * (period - 1) + current_gain) / period
                avg_loss = (avg_loss * (period - 1) + current_loss) / period
                
                if avg_loss == 0:
                    rsi[i + 1] = 100
                else:
                    rs = avg_gain / avg_loss
                    rsi[i + 1] = round(100 - (100 / (1 + rs)), 2)
        
        return rsi
    
    def _format_indicator(
        self, 
        times: List[str], 
        values: List[Optional[float]]
    ) -> List[Dict[str, Any]]:
        """Format indicator values for Lightweight Charts line series"""
        result = []
        for time, value in zip(times, values):
            if value is not None:
                result.append({"time": time, "value": value})
        return result
    
    def get_available_indicators(self) -> List[Dict[str, str]]:
        """Return list of available indicators"""
        return [
            {"id": "sma_20", "name": "SMA 20", "type": "overlay", "color": "#2196F3"},
            {"id": "sma_50", "name": "SMA 50", "type": "overlay", "color": "#FF9800"},
            {"id": "sma_200", "name": "SMA 200", "type": "overlay", "color": "#9C27B0"},
            {"id": "rsi", "name": "RSI 14", "type": "separate", "color": "#4CAF50"},
            {"id": "volume", "name": "Volume", "type": "separate", "color": "#607D8B"},
        ]


# Singleton instance
chart_service = ChartService()

