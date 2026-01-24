# api/services/indicators.py

"""
Technical indicator calculations
"""

from typing import Optional
from api.config import (
    SMA_PERIODS, EMA_PERIOD, RSI_PERIOD, RSI_OVERBOUGHT, RSI_OVERSOLD,
    MACD_FAST, MACD_SLOW, MACD_SIGNAL,
    BB_PERIOD, BB_STD, ATR_PERIOD,
    STOCH_K_PERIOD, STOCH_D_PERIOD,
    VOLUME_AVG_PERIOD, UNUSUAL_VOLUME_MULTIPLIER,
)
from api.models.stock import (
    TechnicalIndicators, MovingAverages, MomentumIndicators,
    VolatilityIndicators, VolumeAnalysis, PriceLevels,
)


class IndicatorService:
    """Service for calculating technical indicators"""
    
    def calculate_all(
        self, 
        closes: list[float], 
        highs: list[float], 
        lows: list[float], 
        volumes: list[int],
        current_price: float,
    ) -> TechnicalIndicators:
        """Calculate all technical indicators"""
        
        ma = self._calculate_moving_averages(closes, current_price)
        momentum = self._calculate_momentum(closes)
        volatility = self._calculate_volatility(closes, highs, lows, current_price)
        volume = self._calculate_volume_analysis(volumes)
        price_levels = self._calculate_price_levels(closes, highs, lows, current_price)
        
        # Determine overall trend
        overall_trend = self._determine_overall_trend(ma, momentum, current_price)
        
        return TechnicalIndicators(
            moving_averages=ma,
            momentum=momentum,
            volatility=volatility,
            volume=volume,
            price_levels=price_levels,
            overall_trend=overall_trend,
        )
    
    def _calculate_moving_averages(
        self, 
        closes: list[float], 
        current_price: float
    ) -> MovingAverages:
        """Calculate all moving averages"""
        
        sma_20 = self._sma(closes, 20)
        sma_50 = self._sma(closes, 50)
        sma_200 = self._sma(closes, 200)
        ema_20 = self._ema(closes, 20)
        
        return MovingAverages(
            sma_20=sma_20,
            sma_50=sma_50,
            sma_200=sma_200,
            ema_20=ema_20,
            price_vs_sma_20="above" if sma_20 and current_price > sma_20 else "below" if sma_20 else None,
            price_vs_sma_50="above" if sma_50 and current_price > sma_50 else "below" if sma_50 else None,
            price_vs_sma_200="above" if sma_200 and current_price > sma_200 else "below" if sma_200 else None,
            golden_cross=sma_50 > sma_200 if sma_50 and sma_200 else None,
            death_cross=sma_50 < sma_200 if sma_50 and sma_200 else None,
        )
    
    def _calculate_momentum(self, closes: list[float]) -> MomentumIndicators:
        """Calculate momentum indicators"""
        
        rsi = self._rsi(closes)
        rsi_signal = None
        if rsi is not None:
            if rsi >= RSI_OVERBOUGHT:
                rsi_signal = "overbought"
            elif rsi <= RSI_OVERSOLD:
                rsi_signal = "oversold"
            else:
                rsi_signal = "neutral"
        
        macd, macd_signal_line, macd_hist = self._macd(closes)
        macd_trend = None
        if macd is not None and macd_signal_line is not None:
            if macd > macd_signal_line:
                macd_trend = "bullish"
            elif macd < macd_signal_line:
                macd_trend = "bearish"
            else:
                macd_trend = "neutral"
        
        stoch_k, stoch_d = self._stochastic(closes)
        stoch_signal = None
        if stoch_k is not None:
            if stoch_k >= 80:
                stoch_signal = "overbought"
            elif stoch_k <= 20:
                stoch_signal = "oversold"
            else:
                stoch_signal = "neutral"
        
        return MomentumIndicators(
            rsi=rsi,
            rsi_signal=rsi_signal,
            macd=macd,
            macd_signal=macd_signal_line,
            macd_histogram=macd_hist,
            macd_trend=macd_trend,
            stochastic_k=stoch_k,
            stochastic_d=stoch_d,
            stochastic_signal=stoch_signal,
        )
    
    def _calculate_volatility(
        self, 
        closes: list[float], 
        highs: list[float], 
        lows: list[float],
        current_price: float,
    ) -> VolatilityIndicators:
        """Calculate volatility indicators"""
        
        bb_upper, bb_middle, bb_lower = self._bollinger_bands(closes)
        
        bb_position = None
        if bb_upper and bb_lower:
            if current_price > bb_upper:
                bb_position = "above_upper"
            elif current_price < bb_lower:
                bb_position = "below_lower"
            else:
                bb_position = "within"
        
        atr = self._atr(closes, highs, lows)
        atr_percent = (atr / current_price * 100) if atr and current_price else None
        
        return VolatilityIndicators(
            bb_upper=bb_upper,
            bb_middle=bb_middle,
            bb_lower=bb_lower,
            bb_position=bb_position,
            atr=atr,
            atr_percent=atr_percent,
        )
    
    def _calculate_volume_analysis(self, volumes: list[int]) -> VolumeAnalysis:
        """Analyze volume patterns"""
        
        if not volumes:
            return VolumeAnalysis(current_volume=0)
        
        current = volumes[-1]
        avg = sum(volumes[-VOLUME_AVG_PERIOD:]) / min(len(volumes), VOLUME_AVG_PERIOD)
        
        ratio = current / avg if avg > 0 else 0
        is_unusual = ratio >= UNUSUAL_VOLUME_MULTIPLIER
        
        # Determine volume trend (compare recent vs older average)
        if len(volumes) >= 10:
            recent_avg = sum(volumes[-5:]) / 5
            older_avg = sum(volumes[-10:-5]) / 5
            if recent_avg > older_avg * 1.2:
                trend = "increasing"
            elif recent_avg < older_avg * 0.8:
                trend = "decreasing"
            else:
                trend = "stable"
        else:
            trend = None
        
        return VolumeAnalysis(
            current_volume=current,
            avg_volume_20d=avg,
            volume_ratio=ratio,
            is_unusual=is_unusual,
            volume_trend=trend,
        )
    
    def _calculate_price_levels(
        self, 
        closes: list[float], 
        highs: list[float], 
        lows: list[float],
        current_price: float,
    ) -> PriceLevels:
        """Calculate key price levels"""
        
        if not closes:
            return PriceLevels()
        
        ath = max(highs) if highs else None
        atl = min(lows) if lows else None
        
        # 52-week high/low (approximately 252 trading days)
        week_52_highs = highs[-252:] if len(highs) >= 252 else highs
        week_52_lows = lows[-252:] if len(lows) >= 252 else lows
        week_52_high = max(week_52_highs) if week_52_highs else None
        week_52_low = min(week_52_lows) if week_52_lows else None
        
        return PriceLevels(
            ath=ath,
            atl=atl,
            week_52_high=week_52_high,
            week_52_low=week_52_low,
            distance_from_ath=((current_price - ath) / ath * 100) if ath else None,
            distance_from_atl=((current_price - atl) / atl * 100) if atl else None,
            distance_from_52w_high=((current_price - week_52_high) / week_52_high * 100) if week_52_high else None,
            distance_from_52w_low=((current_price - week_52_low) / week_52_low * 100) if week_52_low else None,
        )
    
    def _determine_overall_trend(
        self, 
        ma: MovingAverages, 
        momentum: MomentumIndicators,
        current_price: float,
    ) -> str:
        """Determine overall trend based on indicators"""
        
        bullish_signals = 0
        bearish_signals = 0
        
        # Moving average signals
        if ma.price_vs_sma_20 == "above":
            bullish_signals += 1
        elif ma.price_vs_sma_20 == "below":
            bearish_signals += 1
            
        if ma.price_vs_sma_50 == "above":
            bullish_signals += 1
        elif ma.price_vs_sma_50 == "below":
            bearish_signals += 1
            
        if ma.price_vs_sma_200 == "above":
            bullish_signals += 1
        elif ma.price_vs_sma_200 == "below":
            bearish_signals += 1
        
        if ma.golden_cross:
            bullish_signals += 2
        elif ma.death_cross:
            bearish_signals += 2
        
        # Momentum signals
        if momentum.macd_trend == "bullish":
            bullish_signals += 1
        elif momentum.macd_trend == "bearish":
            bearish_signals += 1
        
        if momentum.rsi_signal == "oversold":
            bullish_signals += 1
        elif momentum.rsi_signal == "overbought":
            bearish_signals += 1
        
        # Determine trend
        if bullish_signals > bearish_signals + 2:
            return "bullish"
        elif bearish_signals > bullish_signals + 2:
            return "bearish"
        else:
            return "neutral"
    
    # ═══════════════════════════════════════════════════════════════
    # INDICATOR CALCULATIONS
    # ═══════════════════════════════════════════════════════════════
    
    def _sma(self, data: list[float], period: int) -> Optional[float]:
        """Calculate Simple Moving Average"""
        if len(data) < period:
            return None
        return sum(data[-period:]) / period
    
    def _ema(self, data: list[float], period: int) -> Optional[float]:
        """Calculate Exponential Moving Average"""
        if len(data) < period:
            return None
        
        multiplier = 2 / (period + 1)
        ema = data[0]
        
        for price in data[1:]:
            ema = (price - ema) * multiplier + ema
        
        return ema
    
    def _rsi(self, closes: list[float], period: int = RSI_PERIOD) -> Optional[float]:
        """Calculate Relative Strength Index"""
        if len(closes) < period + 1:
            return None
        
        deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
        recent = deltas[-period:]
        
        gains = [d if d > 0 else 0 for d in recent]
        losses = [-d if d < 0 else 0 for d in recent]
        
        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period
        
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))
    
    def _macd(self, closes: list[float]) -> tuple[Optional[float], Optional[float], Optional[float]]:
        """Calculate MACD, Signal, and Histogram"""
        if len(closes) < MACD_SLOW + MACD_SIGNAL:
            return None, None, None
        
        ema_fast = self._ema(closes, MACD_FAST)
        ema_slow = self._ema(closes, MACD_SLOW)
        
        if ema_fast is None or ema_slow is None:
            return None, None, None
        
        macd_line = ema_fast - ema_slow
        
        # Calculate MACD values for signal line
        macd_values = []
        for i in range(MACD_SLOW - 1, len(closes)):
            fast = self._ema(closes[:i+1], MACD_FAST)
            slow = self._ema(closes[:i+1], MACD_SLOW)
            if fast and slow:
                macd_values.append(fast - slow)
        
        if len(macd_values) < MACD_SIGNAL:
            return macd_line, None, None
        
        signal_line = self._ema(macd_values, MACD_SIGNAL)
        histogram = macd_line - signal_line if signal_line else None
        
        return macd_line, signal_line, histogram
    
    def _stochastic(self, closes: list[float]) -> tuple[Optional[float], Optional[float]]:
        """Calculate Stochastic %K and %D"""
        if len(closes) < STOCH_K_PERIOD:
            return None, None
        
        # %K = (Current Close - Lowest Low) / (Highest High - Lowest Low) * 100
        period_closes = closes[-STOCH_K_PERIOD:]
        highest = max(period_closes)
        lowest = min(period_closes)
        
        if highest == lowest:
            return 50, 50  # Avoid division by zero
        
        k = ((closes[-1] - lowest) / (highest - lowest)) * 100
        
        # %D = SMA of %K (typically 3 periods)
        # Simplified: just return %K for now
        d = k  # Would need to track %K values over time for proper %D
        
        return k, d
    
    def _bollinger_bands(self, closes: list[float]) -> tuple[Optional[float], Optional[float], Optional[float]]:
        """Calculate Bollinger Bands"""
        if len(closes) < BB_PERIOD:
            return None, None, None
        
        sma = self._sma(closes, BB_PERIOD)
        if sma is None:
            return None, None, None
        
        # Calculate standard deviation
        recent = closes[-BB_PERIOD:]
        variance = sum((x - sma) ** 2 for x in recent) / BB_PERIOD
        std = variance ** 0.5
        
        upper = sma + (BB_STD * std)
        lower = sma - (BB_STD * std)
        
        return upper, sma, lower
    
    def _atr(self, closes: list[float], highs: list[float], lows: list[float]) -> Optional[float]:
        """Calculate Average True Range"""
        if len(closes) < ATR_PERIOD + 1:
            return None
        
        true_ranges = []
        for i in range(1, len(closes)):
            tr = max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i-1]),
                abs(lows[i] - closes[i-1])
            )
            true_ranges.append(tr)
        
        if len(true_ranges) < ATR_PERIOD:
            return None
        
        return sum(true_ranges[-ATR_PERIOD:]) / ATR_PERIOD

