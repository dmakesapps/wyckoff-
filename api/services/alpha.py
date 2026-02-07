# api/services/alpha.py

"""
Alpha scoring and advanced metrics service
Identifies high-probability trading opportunities
"""

from typing import Optional
from dataclasses import dataclass

from api.models.stock import (
    StockQuote, TechnicalIndicators, OptionsData, NewsSummary, Fundamentals
)


@dataclass
class VolumeMetrics:
    """Detailed volume analysis"""
    current_volume: int
    avg_volume_10d: float
    avg_volume_20d: float
    avg_volume_50d: float
    relative_volume: float  # Current vs 20d avg (RVOL)
    volume_trend_5d: str    # "increasing", "decreasing", "stable"
    volume_spike: bool      # > 2x average
    volume_dry_up: bool     # < 0.5x average
    dollar_volume: float    # Price * Volume
    accumulation_distribution: str  # "accumulation", "distribution", "neutral"


@dataclass  
class AlphaSignal:
    """Individual alpha signal"""
    name: str
    signal_type: str  # "bullish", "bearish", "neutral"
    strength: int     # 1-5
    description: str


@dataclass
class AlphaScore:
    """Comprehensive alpha scoring"""
    total_score: int          # -100 to +100
    bullish_signals: int
    bearish_signals: int
    signal_strength: str      # "strong", "moderate", "weak"
    signals: list[dict]
    volume_metrics: dict
    momentum_grade: str       # A, B, C, D, F
    trend_grade: str
    risk_reward_grade: str
    overall_grade: str
    summary: str


class AlphaService:
    """Service for calculating alpha scores and advanced metrics"""
    
    def calculate_volume_metrics(
        self,
        volumes: list[int],
        closes: list[float],
        current_price: float,
        current_volume: int,
    ) -> dict:
        """Calculate detailed volume metrics"""
        
        if not volumes or len(volumes) < 10:
            return {}
        
        # Average volumes (from historical data)
        avg_10d = sum(volumes[-10:]) / 10
        avg_20d = sum(volumes[-20:]) / min(20, len(volumes))
        avg_50d = sum(volumes[-50:]) / min(50, len(volumes))
        
        # Last complete day's volume
        last_complete_volume = volumes[-1] if volumes else 0
        
        # Smart volume selection:
        # If current_volume is less than 10% of average, we're likely outside market hours
        # or very early in the day - use last complete day's volume instead
        is_partial_day = current_volume < (avg_20d * 0.1)
        
        if is_partial_day and last_complete_volume > 0:
            # Use last complete trading day's volume
            effective_volume = last_complete_volume
            volume_note = "last_complete_day"
        else:
            # Use real-time volume (market is open and accumulating)
            effective_volume = current_volume
            volume_note = "intraday" if current_volume < avg_20d * 0.5 else "current"
        
        # Relative volume (RVOL) - using effective volume
        rvol = effective_volume / avg_20d if avg_20d > 0 else 1.0
        
        # Volume trend (compare last 5 days vs previous 5 days)
        if len(volumes) >= 10:
            recent_avg = sum(volumes[-5:]) / 5
            prior_avg = sum(volumes[-10:-5]) / 5
            if recent_avg > prior_avg * 1.2:
                volume_trend = "increasing"
            elif recent_avg < prior_avg * 0.8:
                volume_trend = "decreasing"
            else:
                volume_trend = "stable"
        else:
            volume_trend = "unknown"
        
        # Volume spike / dry up - based on effective volume
        volume_spike = rvol >= 2.0
        volume_dry_up = rvol <= 0.5
        
        # Dollar volume
        dollar_volume = current_price * effective_volume
        
        # Accumulation/Distribution (simplified)
        # Compare volume on up days vs down days
        if len(closes) >= 10 and len(volumes) >= 10:
            up_volume = 0
            down_volume = 0
            for i in range(-10, 0):
                if closes[i] > closes[i-1]:
                    up_volume += volumes[i]
                else:
                    down_volume += volumes[i]
            
            if up_volume > down_volume * 1.3:
                acc_dist = "accumulation"
            elif down_volume > up_volume * 1.3:
                acc_dist = "distribution"
            else:
                acc_dist = "neutral"
        else:
            acc_dist = "unknown"
        
        return {
            "current_volume": effective_volume,
            "raw_intraday_volume": current_volume,
            "last_day_volume": last_complete_volume,
            "volume_note": volume_note,
            "avg_volume_10d": round(avg_10d),
            "avg_volume_20d": round(avg_20d),
            "avg_volume_50d": round(avg_50d),
            "relative_volume": round(rvol, 2),
            "relative_volume_label": self._rvol_label(rvol),
            "volume_trend_5d": volume_trend,
            "volume_spike": volume_spike,
            "volume_dry_up": volume_dry_up,
            "dollar_volume": round(dollar_volume),
            "dollar_volume_formatted": self._format_dollar_volume(dollar_volume),
            "accumulation_distribution": acc_dist,
        }
    
    def _rvol_label(self, rvol: float) -> str:
        """Convert RVOL to human label"""
        if rvol >= 3.0:
            return "extremely high"
        elif rvol >= 2.0:
            return "very high"
        elif rvol >= 1.5:
            return "high"
        elif rvol >= 0.8:
            return "normal"
        elif rvol >= 0.5:
            return "low"
        else:
            return "very low"
    
    def _format_dollar_volume(self, value: float) -> str:
        """Format dollar volume"""
        if value >= 1_000_000_000:
            return f"${value / 1_000_000_000:.2f}B"
        elif value >= 1_000_000:
            return f"${value / 1_000_000:.2f}M"
        elif value >= 1_000:
            return f"${value / 1_000:.1f}K"
        return f"${value:.0f}"
    
    def calculate_alpha_score(
        self,
        quote: StockQuote,
        technicals: TechnicalIndicators,
        volume_metrics: dict,
        options: Optional[OptionsData] = None,
        news: Optional[NewsSummary] = None,
        fundamentals: Optional[Fundamentals] = None,
    ) -> dict:
        """
        Calculate comprehensive alpha score
        
        Returns score from -100 (very bearish) to +100 (very bullish)
        with detailed breakdown
        """
        
        signals = []
        bullish_points = 0
        bearish_points = 0
        
        # ═══════════════════════════════════════════════════════════════
        # TREND SIGNALS
        # ═══════════════════════════════════════════════════════════════
        
        ma = technicals.moving_averages
        
        # Golden/Death Cross (strong signal)
        if ma.golden_cross:
            signals.append({
                "name": "Golden Cross",
                "type": "bullish",
                "strength": 4,
                "description": "50 SMA above 200 SMA - long-term bullish"
            })
            bullish_points += 15
        elif ma.death_cross:
            signals.append({
                "name": "Death Cross", 
                "type": "bearish",
                "strength": 4,
                "description": "50 SMA below 200 SMA - long-term bearish"
            })
            bearish_points += 15
        
        # Price vs Major MAs
        above_all_mas = (
            ma.price_vs_sma_20 == "above" and 
            ma.price_vs_sma_50 == "above" and 
            ma.price_vs_sma_200 == "above"
        )
        below_all_mas = (
            ma.price_vs_sma_20 == "below" and 
            ma.price_vs_sma_50 == "below" and 
            ma.price_vs_sma_200 == "below"
        )
        
        if above_all_mas:
            signals.append({
                "name": "Above All MAs",
                "type": "bullish", 
                "strength": 3,
                "description": "Price above 20/50/200 SMA - strong uptrend"
            })
            bullish_points += 10
        elif below_all_mas:
            signals.append({
                "name": "Below All MAs",
                "type": "bearish",
                "strength": 3, 
                "description": "Price below 20/50/200 SMA - strong downtrend"
            })
            bearish_points += 10
        
        # ═══════════════════════════════════════════════════════════════
        # MOMENTUM SIGNALS
        # ═══════════════════════════════════════════════════════════════
        
        mom = technicals.momentum
        
        # RSI
        if mom.rsi:
            if mom.rsi <= 30:
                signals.append({
                    "name": "RSI Oversold",
                    "type": "bullish",
                    "strength": 3,
                    "description": f"RSI at {mom.rsi:.0f} - potential bounce"
                })
                bullish_points += 8
            elif mom.rsi >= 70:
                signals.append({
                    "name": "RSI Overbought",
                    "type": "bearish",
                    "strength": 3,
                    "description": f"RSI at {mom.rsi:.0f} - potential pullback"
                })
                bearish_points += 8
            elif 50 <= mom.rsi <= 60:
                signals.append({
                    "name": "RSI Bullish Zone",
                    "type": "bullish",
                    "strength": 2,
                    "description": f"RSI at {mom.rsi:.0f} - healthy momentum"
                })
                bullish_points += 5
        
        # MACD
        if mom.macd_trend == "bullish":
            signals.append({
                "name": "MACD Bullish",
                "type": "bullish",
                "strength": 3,
                "description": "MACD above signal line"
            })
            bullish_points += 8
        elif mom.macd_trend == "bearish":
            signals.append({
                "name": "MACD Bearish",
                "type": "bearish",
                "strength": 3,
                "description": "MACD below signal line"
            })
            bearish_points += 8
        
        # ═══════════════════════════════════════════════════════════════
        # VOLUME SIGNALS
        # ═══════════════════════════════════════════════════════════════
        
        if volume_metrics:
            rvol = volume_metrics.get("relative_volume", 1.0)
            acc_dist = volume_metrics.get("accumulation_distribution")
            vol_trend = volume_metrics.get("volume_trend_5d")
            
            # High volume breakout
            if rvol >= 2.0 and quote.change_percent > 2:
                signals.append({
                    "name": "Volume Breakout",
                    "type": "bullish",
                    "strength": 5,
                    "description": f"Price up {quote.change_percent:.1f}% on {rvol:.1f}x volume"
                })
                bullish_points += 15
            elif rvol >= 2.0 and quote.change_percent < -2:
                signals.append({
                    "name": "Volume Breakdown",
                    "type": "bearish",
                    "strength": 5,
                    "description": f"Price down {abs(quote.change_percent):.1f}% on {rvol:.1f}x volume"
                })
                bearish_points += 15
            elif rvol >= 1.5:
                signals.append({
                    "name": "Elevated Volume",
                    "type": "neutral",
                    "strength": 2,
                    "description": f"Volume {rvol:.1f}x average - increased interest"
                })
            
            # Accumulation/Distribution
            if acc_dist == "accumulation":
                signals.append({
                    "name": "Accumulation Pattern",
                    "type": "bullish",
                    "strength": 3,
                    "description": "Higher volume on up days - institutional buying"
                })
                bullish_points += 8
            elif acc_dist == "distribution":
                signals.append({
                    "name": "Distribution Pattern",
                    "type": "bearish",
                    "strength": 3,
                    "description": "Higher volume on down days - institutional selling"
                })
                bearish_points += 8
            
            # Volume trend
            if vol_trend == "increasing" and quote.change_percent > 0:
                signals.append({
                    "name": "Rising Volume Trend",
                    "type": "bullish",
                    "strength": 2,
                    "description": "5-day volume trend increasing with price"
                })
                bullish_points += 5
        
        # ═══════════════════════════════════════════════════════════════
        # ADVANCED VOLUME SIGNALS (from technicals.volume)
        # ═══════════════════════════════════════════════════════════════
        
        tech_vol = technicals.volume
        
        # VWAP Signal
        if tech_vol.vwap and tech_vol.price_vs_vwap:
            if tech_vol.price_vs_vwap == "above" and quote.change_percent > 0:
                signals.append({
                    "name": "Above VWAP",
                    "type": "bullish",
                    "strength": 3,
                    "description": f"Trading above VWAP (${tech_vol.vwap:.2f}) - institutional support"
                })
                bullish_points += 7
            elif tech_vol.price_vs_vwap == "below" and quote.change_percent < 0:
                signals.append({
                    "name": "Below VWAP",
                    "type": "bearish",
                    "strength": 3,
                    "description": f"Trading below VWAP (${tech_vol.vwap:.2f}) - institutional resistance"
                })
                bearish_points += 7
        
        # OBV Trend Signal
        if tech_vol.obv_trend:
            if tech_vol.obv_trend == "accumulating":
                signals.append({
                    "name": "OBV Accumulating",
                    "type": "bullish",
                    "strength": 4,
                    "description": "On-Balance Volume rising - smart money buying"
                })
                bullish_points += 10
            elif tech_vol.obv_trend == "distributing":
                signals.append({
                    "name": "OBV Distributing",
                    "type": "bearish",
                    "strength": 4,
                    "description": "On-Balance Volume falling - smart money selling"
                })
                bearish_points += 10
        
        # MFI Signal (volume-weighted RSI)
        if tech_vol.mfi is not None:
            if tech_vol.mfi <= 20:
                signals.append({
                    "name": "MFI Oversold",
                    "type": "bullish",
                    "strength": 4,
                    "description": f"Money Flow Index at {tech_vol.mfi:.0f} - volume confirms oversold"
                })
                bullish_points += 10
            elif tech_vol.mfi >= 80:
                signals.append({
                    "name": "MFI Overbought",
                    "type": "bearish",
                    "strength": 4,
                    "description": f"Money Flow Index at {tech_vol.mfi:.0f} - volume confirms overbought"
                })
                bearish_points += 10
            elif 50 <= tech_vol.mfi <= 70:
                signals.append({
                    "name": "MFI Bullish Zone",
                    "type": "bullish",
                    "strength": 2,
                    "description": f"Money Flow Index at {tech_vol.mfi:.0f} - healthy buying pressure"
                })
                bullish_points += 5
        
        # Volume ROC Signal
        if tech_vol.volume_roc is not None:
            if tech_vol.volume_roc > 100 and quote.change_percent > 2:
                signals.append({
                    "name": "Volume Acceleration",
                    "type": "bullish",
                    "strength": 5,
                    "description": f"Volume up {tech_vol.volume_roc:.0f}% - explosive move"
                })
                bullish_points += 12
            elif tech_vol.volume_roc > 100 and quote.change_percent < -2:
                signals.append({
                    "name": "Panic Selling",
                    "type": "bearish",
                    "strength": 5,
                    "description": f"Volume up {tech_vol.volume_roc:.0f}% on selloff - capitulation?"
                })
                bearish_points += 12
            elif tech_vol.volume_roc < -50:
                signals.append({
                    "name": "Volume Dry Up",
                    "type": "neutral",
                    "strength": 2,
                    "description": f"Volume down {abs(tech_vol.volume_roc):.0f}% - low interest"
                })
        
        # CMF Signal (Chaikin Money Flow)
        if tech_vol.cmf is not None:
            if tech_vol.cmf > 0.25:
                signals.append({
                    "name": "Strong Accumulation (CMF)",
                    "type": "bullish",
                    "strength": 4,
                    "description": f"Chaikin MF at {tech_vol.cmf:.2f} - heavy buying pressure"
                })
                bullish_points += 10
            elif tech_vol.cmf < -0.25:
                signals.append({
                    "name": "Strong Distribution (CMF)",
                    "type": "bearish",
                    "strength": 4,
                    "description": f"Chaikin MF at {tech_vol.cmf:.2f} - heavy selling pressure"
                })
                bearish_points += 10
            elif tech_vol.cmf > 0.1:
                signals.append({
                    "name": "CMF Accumulation",
                    "type": "bullish",
                    "strength": 2,
                    "description": f"Chaikin MF at {tech_vol.cmf:.2f} - modest buying"
                })
                bullish_points += 5
            elif tech_vol.cmf < -0.1:
                signals.append({
                    "name": "CMF Distribution",
                    "type": "bearish",
                    "strength": 2,
                    "description": f"Chaikin MF at {tech_vol.cmf:.2f} - modest selling"
                })
                bearish_points += 5
        
        # Volume Divergence Detection (price up but volume indicators negative)
        if tech_vol.obv_trend == "distributing" and quote.change_percent > 1:
            signals.append({
                "name": "Bearish Volume Divergence",
                "type": "bearish",
                "strength": 4,
                "description": "Price rising but OBV falling - weak rally"
            })
            bearish_points += 10
        elif tech_vol.obv_trend == "accumulating" and quote.change_percent < -1:
            signals.append({
                "name": "Bullish Volume Divergence",
                "type": "bullish",
                "strength": 4,
                "description": "Price falling but OBV rising - accumulation on dip"
            })
            bullish_points += 10
        
        # ═══════════════════════════════════════════════════════════════
        # VOLATILITY SIGNALS  
        # ═══════════════════════════════════════════════════════════════
        
        vol = technicals.volatility
        
        # Bollinger Band squeeze (low volatility = potential breakout)

        if vol.bollinger_upper and vol.bollinger_lower and vol.bollinger_middle:
            bb_width = (vol.bollinger_upper - vol.bollinger_lower) / vol.bollinger_middle
            if bb_width < 0.1:  # Tight bands
                signals.append({
                    "name": "Bollinger Squeeze",
                    "type": "neutral",
                    "strength": 4,
                    "description": "Low volatility - breakout imminent"
                })
                # Could go either way, slight bullish bias
                bullish_points += 3
        
        # Price at Bollinger extremes

        if vol.price_position == "below_lower":
            signals.append({
                "name": "Below Lower BB",
                "type": "bullish",
                "strength": 3,
                "description": "Price below lower Bollinger Band - oversold"
            })
            bullish_points += 8
        elif vol.price_position == "above_upper":
            signals.append({
                "name": "Above Upper BB",
                "type": "bearish",
                "strength": 2,
                "description": "Price above upper Bollinger Band - extended"
            })
            bearish_points += 5
        
        # ═══════════════════════════════════════════════════════════════
        # PRICE LEVEL SIGNALS
        # ═══════════════════════════════════════════════════════════════
        
        levels = technicals.price_levels
        
        # Near ATH
        if levels.distance_from_ath and levels.distance_from_ath > -5:
            signals.append({
                "name": "Near All-Time High",
                "type": "bullish",
                "strength": 4,
                "description": f"Only {abs(levels.distance_from_ath):.1f}% from ATH"
            })
            bullish_points += 12
        
        # Breaking ATH
        if levels.distance_from_ath and levels.distance_from_ath > 0:
            signals.append({
                "name": "New All-Time High",
                "type": "bullish",
                "strength": 5,
                "description": f"Trading {levels.distance_from_ath:.1f}% above previous ATH"
            })
            bullish_points += 15
        
        # Near 52-week high
        if levels.distance_from_52w_high and -10 < levels.distance_from_52w_high < 0:
            signals.append({
                "name": "Near 52-Week High",
                "type": "bullish",
                "strength": 3,
                "description": f"{abs(levels.distance_from_52w_high):.1f}% from 52-week high"
            })
            bullish_points += 7
        
        # Near 52-week low (potential value or falling knife)
        if levels.distance_from_52w_low and levels.distance_from_52w_low < 10:
            signals.append({
                "name": "Near 52-Week Low",
                "type": "bearish",
                "strength": 3,
                "description": f"Only {levels.distance_from_52w_low:.1f}% above 52-week low"
            })
            bearish_points += 7
        
        # ═══════════════════════════════════════════════════════════════
        # OPTIONS FLOW SIGNALS
        # ═══════════════════════════════════════════════════════════════
        
        if options:
            # Put/Call ratio
            if options.put_call_ratio:
                if options.put_call_ratio < 0.5:
                    signals.append({
                        "name": "Very Low Put/Call",
                        "type": "bullish",
                        "strength": 3,
                        "description": f"P/C ratio {options.put_call_ratio:.2f} - strong call buying"
                    })
                    bullish_points += 10
                elif options.put_call_ratio < 0.7:
                    signals.append({
                        "name": "Low Put/Call",
                        "type": "bullish",
                        "strength": 2,
                        "description": f"P/C ratio {options.put_call_ratio:.2f} - bullish options flow"
                    })
                    bullish_points += 5
                elif options.put_call_ratio > 1.5:
                    signals.append({
                        "name": "Very High Put/Call",
                        "type": "bearish",
                        "strength": 3,
                        "description": f"P/C ratio {options.put_call_ratio:.2f} - heavy put buying"
                    })
                    bearish_points += 10
                elif options.put_call_ratio > 1.2:
                    signals.append({
                        "name": "High Put/Call",
                        "type": "bearish",
                        "strength": 2,
                        "description": f"P/C ratio {options.put_call_ratio:.2f} - bearish options flow"
                    })
                    bearish_points += 5
            
            # Unusual options activity
            if options.unusual_activity:
                call_unusual = sum(1 for u in options.unusual_activity if u["type"] == "call")
                put_unusual = sum(1 for u in options.unusual_activity if u["type"] == "put")
                
                if call_unusual > put_unusual * 2:
                    signals.append({
                        "name": "Unusual Call Activity",
                        "type": "bullish",
                        "strength": 4,
                        "description": f"{call_unusual} unusual call sweeps detected"
                    })
                    bullish_points += 12
                elif put_unusual > call_unusual * 2:
                    signals.append({
                        "name": "Unusual Put Activity",
                        "type": "bearish",
                        "strength": 4,
                        "description": f"{put_unusual} unusual put sweeps detected"
                    })
                    bearish_points += 12
            
            # Options volume intensity signal
            if options.volume_signal:
                if options.volume_signal == "unusually_high":
                    signals.append({
                        "name": "Extreme Options Activity",
                        "type": "neutral",
                        "strength": 5,
                        "description": f"Options volume {options.volume_vs_oi_ratio:.1%} of OI - big move expected"
                    })
                    # Could go either way - check put/call for direction
                    if options.put_call_ratio and options.put_call_ratio < 0.8:
                        bullish_points += 8
                    elif options.put_call_ratio and options.put_call_ratio > 1.2:
                        bearish_points += 8
                elif options.volume_signal == "high":
                    signals.append({
                        "name": "High Options Activity",
                        "type": "neutral",
                        "strength": 3,
                        "description": f"Options volume elevated - increased interest"
                    })
            
            # Call vs Put volume directional signal
            if options.call_volume_vs_put_volume:
                if options.call_volume_vs_put_volume > 3:
                    signals.append({
                        "name": "Heavy Call Volume",
                        "type": "bullish",
                        "strength": 4,
                        "description": f"Call volume {options.call_volume_vs_put_volume:.1f}x put volume"
                    })
                    bullish_points += 10
                elif options.call_volume_vs_put_volume < 0.33:
                    signals.append({
                        "name": "Heavy Put Volume",
                        "type": "bearish",
                        "strength": 4,
                        "description": f"Put volume {1/options.call_volume_vs_put_volume:.1f}x call volume"
                    })
                    bearish_points += 10
        
        # ═══════════════════════════════════════════════════════════════
        # NEWS/CATALYST SIGNALS
        # ═══════════════════════════════════════════════════════════════
        
        if news:
            if news.overall_sentiment == "positive":
                signals.append({
                    "name": "Positive News Sentiment",
                    "type": "bullish",
                    "strength": 2,
                    "description": "Recent news is positive"
                })
                bullish_points += 5
            elif news.overall_sentiment == "negative":
                signals.append({
                    "name": "Negative News Sentiment",
                    "type": "bearish",
                    "strength": 2,
                    "description": "Recent news is negative"
                })
                bearish_points += 5
            
            # Upcoming earnings
            if news.earnings_date:
                signals.append({
                    "name": "Upcoming Earnings",
                    "type": "neutral",
                    "strength": 3,
                    "description": f"Earnings on {news.earnings_date}"
                })
        
        # ═══════════════════════════════════════════════════════════════
        # FUNDAMENTAL SIGNALS
        # ═══════════════════════════════════════════════════════════════
        
        if fundamentals:
            # Short interest
            if fundamentals.short_percent:
                if fundamentals.short_percent > 0.20:
                    signals.append({
                        "name": "High Short Interest",
                        "type": "bullish",  # Squeeze potential
                        "strength": 3,
                        "description": f"{fundamentals.short_percent*100:.1f}% short - squeeze potential"
                    })
                    bullish_points += 8
                elif fundamentals.short_percent > 0.10:
                    signals.append({
                        "name": "Elevated Short Interest",
                        "type": "neutral",
                        "strength": 2,
                        "description": f"{fundamentals.short_percent*100:.1f}% of float short"
                    })
        
        # ═══════════════════════════════════════════════════════════════
        # CALCULATE FINAL SCORES
        # ═══════════════════════════════════════════════════════════════
        
        # Net score (-100 to +100)
        max_possible = max(bullish_points, bearish_points, 1)
        raw_score = bullish_points - bearish_points
        total_score = max(-100, min(100, int(raw_score * 100 / 50)))  # Normalize
        
        # Determine grades
        momentum_grade = self._grade_momentum(technicals)
        trend_grade = self._grade_trend(technicals)
        risk_reward_grade = self._grade_risk_reward(technicals, quote)
        
        # Overall grade
        grades = [momentum_grade, trend_grade, risk_reward_grade]
        grade_values = {"A": 4, "B": 3, "C": 2, "D": 1, "F": 0}
        avg_grade = sum(grade_values.get(g, 2) for g in grades) / len(grades)
        
        if avg_grade >= 3.5:
            overall_grade = "A"
        elif avg_grade >= 2.5:
            overall_grade = "B"
        elif avg_grade >= 1.5:
            overall_grade = "C"
        elif avg_grade >= 0.5:
            overall_grade = "D"
        else:
            overall_grade = "F"
        
        # Signal strength
        if abs(total_score) >= 50:
            signal_strength = "strong"
        elif abs(total_score) >= 25:
            signal_strength = "moderate"
        else:
            signal_strength = "weak"
        
        # Summary
        direction = "bullish" if total_score > 10 else "bearish" if total_score < -10 else "neutral"
        bullish_count = len([s for s in signals if s["type"] == "bullish"])
        bearish_count = len([s for s in signals if s["type"] == "bearish"])
        
        summary = f"{signal_strength.title()} {direction} setup with {bullish_count} bullish and {bearish_count} bearish signals. "
        
        if signals:
            top_signal = max(signals, key=lambda x: x["strength"])
            summary += f"Key signal: {top_signal['name']}."
        
        return {
            "total_score": total_score,
            "bullish_signals": bullish_count,
            "bearish_signals": bearish_count,
            "signal_strength": signal_strength,
            "signals": signals,
            "momentum_grade": momentum_grade,
            "trend_grade": trend_grade,
            "risk_reward_grade": risk_reward_grade,
            "overall_grade": overall_grade,
            "summary": summary,
        }
    
    def _grade_momentum(self, technicals: TechnicalIndicators) -> str:
        """Grade momentum A-F"""
        score = 0
        
        mom = technicals.momentum
        if mom.macd_trend == "bullish":
            score += 2
        if mom.rsi and 40 <= mom.rsi <= 60:
            score += 1
        elif mom.rsi and 50 <= mom.rsi <= 70:
            score += 2

        if mom.stoch_signal == "neutral":
            score += 1
        
        if score >= 4:
            return "A"
        elif score >= 3:
            return "B"
        elif score >= 2:
            return "C"
        elif score >= 1:
            return "D"
        return "F"
    
    def _grade_trend(self, technicals: TechnicalIndicators) -> str:
        """Grade trend strength A-F"""
        score = 0
        
        ma = technicals.moving_averages
        if ma.golden_cross:
            score += 2
        if ma.price_vs_sma_20 == "above":
            score += 1
        if ma.price_vs_sma_50 == "above":
            score += 1
        if ma.price_vs_sma_200 == "above":
            score += 1
        
        if score >= 4:
            return "A"
        elif score >= 3:
            return "B"
        elif score >= 2:
            return "C"
        elif score >= 1:
            return "D"
        return "F"
    
    def _grade_risk_reward(self, technicals: TechnicalIndicators, quote: StockQuote) -> str:
        """Grade risk/reward setup A-F"""
        score = 0
        
        vol = technicals.volatility
        levels = technicals.price_levels
        
        # Good entry near support

        if vol.price_position == "below_lower":
            score += 2
        elif vol.price_position == "within":
            score += 1
        
        # Not extended
        if levels.distance_from_ath and levels.distance_from_ath < -20:
            score += 1  # Room to run
        
        # Reasonable volatility
        if vol.atr_percent and vol.atr_percent < 5:
            score += 1
        
        if score >= 3:
            return "A"
        elif score >= 2:
            return "B"
        elif score >= 1:
            return "C"
        return "D"

