# api/services/options.py

"""
Options chain data service using Yahoo Finance (yfinance)

NOTE: Alpaca does NOT provide options data - this is Yahoo Finance only.
Options data includes:
- Put/Call ratio
- Open interest
- Implied volatility
- Max pain calculation
- Unusual activity detection
"""

import yfinance as yf
from typing import Optional
from datetime import datetime

from api.config import (
    UNUSUAL_OPTIONS_VOLUME,
    PUT_CALL_RATIO_BULLISH,
    PUT_CALL_RATIO_BEARISH,
)
from api.models.stock import OptionsData, OptionContract


class OptionsService:
    """Service for fetching and analyzing options data"""
    
    def get_options_data(self, symbol: str) -> Optional[OptionsData]:
        """
        Get options chain data for a symbol
        
        Returns summary of options activity including:
        - Put/Call ratio
        - Total volume and open interest
        - Unusual activity
        - Nearest expiration chain
        """
        try:
            ticker = yf.Ticker(symbol)
            
            # Get available expiration dates
            expirations = ticker.options
            if not expirations:
                return None
            
            # Get nearest expiration chain
            nearest_exp = expirations[0]
            chain = ticker.option_chain(nearest_exp)
            
            calls_df = chain.calls
            puts_df = chain.puts
            
            # Calculate totals
            total_call_volume = int(calls_df["volume"].sum()) if "volume" in calls_df else 0
            total_put_volume = int(puts_df["volume"].sum()) if "volume" in puts_df else 0
            total_call_oi = int(calls_df["openInterest"].sum()) if "openInterest" in calls_df else 0
            total_put_oi = int(puts_df["openInterest"].sum()) if "openInterest" in puts_df else 0
            
            # Put/Call ratio
            pc_ratio = total_put_volume / total_call_volume if total_call_volume > 0 else None
            
            # Find unusual activity (high volume relative to open interest)
            unusual = self._find_unusual_activity(calls_df, puts_df, nearest_exp)
            
            # Calculate max pain (strike with most OI)
            max_pain = self._calculate_max_pain(calls_df, puts_df)
            
            # Get nearest expiry contracts
            nearest_calls = self._df_to_contracts(calls_df, nearest_exp, "call")
            nearest_puts = self._df_to_contracts(puts_df, nearest_exp, "put")
            
            # Calculate additional volume metrics
            total_options_volume = total_call_volume + total_put_volume
            total_oi = total_call_oi + total_put_oi
            
            # Volume vs OI ratio (indicates how active vs positions held)
            vol_oi_ratio = total_options_volume / total_oi if total_oi > 0 else None
            
            # Volume signal based on vol/OI ratio
            volume_signal = None
            if vol_oi_ratio:
                if vol_oi_ratio > 0.5:
                    volume_signal = "unusually_high"  # Very active day
                elif vol_oi_ratio > 0.3:
                    volume_signal = "high"
                elif vol_oi_ratio > 0.1:
                    volume_signal = "normal"
                else:
                    volume_signal = "low"
            
            # Call vs Put volume ratio
            call_vs_put = total_call_volume / total_put_volume if total_put_volume > 0 else None
            
            return OptionsData(
                symbol=symbol.upper(),
                expirations=list(expirations),
                put_call_ratio=pc_ratio,
                total_call_volume=total_call_volume,
                total_put_volume=total_put_volume,
                total_call_oi=total_call_oi,
                total_put_oi=total_put_oi,
                max_pain=max_pain,
                unusual_activity=unusual,
                nearest_expiry_calls=nearest_calls[:10],  # Top 10 by volume
                nearest_expiry_puts=nearest_puts[:10],
                total_options_volume=total_options_volume,
                volume_vs_oi_ratio=round(vol_oi_ratio, 3) if vol_oi_ratio else None,
                volume_signal=volume_signal,
                call_volume_vs_put_volume=round(call_vs_put, 2) if call_vs_put else None,
            )
            
        except Exception as e:
            print(f"Error fetching options for {symbol}: {e}")
            return None
    
    def _find_unusual_activity(self, calls_df, puts_df, expiration: str) -> list[dict]:
        """Find options with unusual volume"""
        unusual = []
        
        for df, contract_type in [(calls_df, "call"), (puts_df, "put")]:
            if df.empty:
                continue
                
            for _, row in df.iterrows():
                volume = row.get("volume", 0)
                oi = row.get("openInterest", 1)
                
                # Flag if volume > threshold and volume > open interest
                if volume and volume >= UNUSUAL_OPTIONS_VOLUME and volume > oi:
                    unusual.append({
                        "type": contract_type,
                        "strike": row["strike"],
                        "expiration": expiration,
                        "volume": int(volume),
                        "open_interest": int(oi) if oi else 0,
                        "volume_oi_ratio": round(volume / oi, 2) if oi else 0,
                        "implied_volatility": round(row.get("impliedVolatility", 0) * 100, 2),
                    })
        
        # Sort by volume
        unusual.sort(key=lambda x: x["volume"], reverse=True)
        return unusual[:20]  # Top 20
    
    def _calculate_max_pain(self, calls_df, puts_df) -> Optional[float]:
        """
        Calculate max pain - the strike price where option holders 
        lose the most money (and market makers profit most)
        """
        try:
            if calls_df.empty or puts_df.empty:
                return None
            
            # Get unique strikes
            strikes = sorted(set(calls_df["strike"].tolist() + puts_df["strike"].tolist()))
            
            if not strikes:
                return None
            
            min_pain = float("inf")
            max_pain_strike = strikes[0]
            
            for strike in strikes:
                total_pain = 0
                
                # Pain for call holders (ITM calls)
                for _, call in calls_df.iterrows():
                    if call["strike"] < strike:
                        pain = (strike - call["strike"]) * call.get("openInterest", 0)
                        total_pain += pain
                
                # Pain for put holders (ITM puts)
                for _, put in puts_df.iterrows():
                    if put["strike"] > strike:
                        pain = (put["strike"] - strike) * put.get("openInterest", 0)
                        total_pain += pain
                
                if total_pain < min_pain:
                    min_pain = total_pain
                    max_pain_strike = strike
            
            return max_pain_strike
            
        except Exception:
            return None
    
    def _df_to_contracts(self, df, expiration: str, contract_type: str) -> list[OptionContract]:
        """Convert DataFrame rows to OptionContract models"""
        contracts = []
        
        if df.empty:
            return contracts
        
        # Sort by volume
        df_sorted = df.sort_values("volume", ascending=False)
        
        for _, row in df_sorted.iterrows():
            try:
                contracts.append(OptionContract(
                    strike=row["strike"],
                    expiration=expiration,
                    contract_type=contract_type,
                    bid=row.get("bid", 0),
                    ask=row.get("ask", 0),
                    last_price=row.get("lastPrice", 0),
                    volume=int(row.get("volume", 0)) if row.get("volume") else 0,
                    open_interest=int(row.get("openInterest", 0)) if row.get("openInterest") else 0,
                    implied_volatility=row.get("impliedVolatility"),
                ))
            except Exception:
                continue
        
        return contracts
    
    def analyze_sentiment(self, options_data: OptionsData) -> dict:
        """
        Analyze options data for bullish/bearish sentiment
        
        Returns dict with sentiment analysis
        """
        if not options_data:
            return {"sentiment": "neutral", "confidence": 0, "signals": []}
        
        signals = []
        bullish_score = 0
        bearish_score = 0
        
        # Put/Call ratio
        if options_data.put_call_ratio:
            if options_data.put_call_ratio < PUT_CALL_RATIO_BULLISH:
                signals.append(f"Low P/C ratio ({options_data.put_call_ratio:.2f}) - Bullish")
                bullish_score += 2
            elif options_data.put_call_ratio > PUT_CALL_RATIO_BEARISH:
                signals.append(f"High P/C ratio ({options_data.put_call_ratio:.2f}) - Bearish")
                bearish_score += 2
        
        # Unusual call vs put activity
        if options_data.unusual_activity:
            call_unusual = sum(1 for u in options_data.unusual_activity if u["type"] == "call")
            put_unusual = sum(1 for u in options_data.unusual_activity if u["type"] == "put")
            
            if call_unusual > put_unusual * 1.5:
                signals.append(f"Unusual call activity ({call_unusual} vs {put_unusual} puts)")
                bullish_score += 1
            elif put_unusual > call_unusual * 1.5:
                signals.append(f"Unusual put activity ({put_unusual} vs {call_unusual} calls)")
                bearish_score += 1
        
        # Volume comparison
        if options_data.total_call_volume > options_data.total_put_volume * 1.5:
            signals.append("Heavy call volume")
            bullish_score += 1
        elif options_data.total_put_volume > options_data.total_call_volume * 1.5:
            signals.append("Heavy put volume")
            bearish_score += 1
        
        # Determine sentiment
        if bullish_score > bearish_score + 1:
            sentiment = "bullish"
            confidence = min(100, (bullish_score - bearish_score) * 25)
        elif bearish_score > bullish_score + 1:
            sentiment = "bearish"
            confidence = min(100, (bearish_score - bullish_score) * 25)
        else:
            sentiment = "neutral"
            confidence = 50
        
        return {
            "sentiment": sentiment,
            "confidence": confidence,
            "signals": signals,
            "bullish_score": bullish_score,
            "bearish_score": bearish_score,
        }

