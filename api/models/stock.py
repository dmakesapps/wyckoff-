# api/models/stock.py

"""
Pydantic models for stock data
"""

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# ═══════════════════════════════════════════════════════════════
# QUOTE & PRICE MODELS
# ═══════════════════════════════════════════════════════════════

class StockQuote(BaseModel):
    """Real-time stock quote"""
    symbol: str
    price: float
    open: float
    high: float
    low: float
    close: float
    volume: int
    previous_close: float
    change: float
    change_percent: float
    timestamp: datetime


class Fundamentals(BaseModel):
    """Company fundamentals"""
    market_cap: Optional[float] = None
    market_cap_formatted: Optional[str] = None
    pe_ratio: Optional[float] = None
    eps: Optional[float] = None
    dividend_yield: Optional[float] = None
    beta: Optional[float] = None
    week_52_high: Optional[float] = None
    week_52_low: Optional[float] = None
    avg_volume: Optional[int] = None
    shares_outstanding: Optional[int] = None
    sector: Optional[str] = None
    industry: Optional[str] = None


# ═══════════════════════════════════════════════════════════════
# TECHNICAL INDICATOR MODELS
# ═══════════════════════════════════════════════════════════════

class MovingAverages(BaseModel):
    """Moving average indicators"""
    sma_20: Optional[float] = None
    sma_50: Optional[float] = None
    sma_200: Optional[float] = None
    ema_20: Optional[float] = None
    price_vs_sma_20: Optional[str] = None  # "above" or "below"
    price_vs_sma_50: Optional[str] = None
    price_vs_sma_200: Optional[str] = None
    golden_cross: Optional[bool] = None  # SMA 50 > SMA 200
    death_cross: Optional[bool] = None   # SMA 50 < SMA 200


class MomentumIndicators(BaseModel):
    """Momentum indicators"""
    rsi: Optional[float] = None
    rsi_signal: Optional[str] = None  # "overbought", "oversold", "neutral"
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_histogram: Optional[float] = None
    macd_trend: Optional[str] = None  # "bullish", "bearish", "neutral"
    stoch_k: Optional[float] = None
    stoch_d: Optional[float] = None
    stoch_signal: Optional[str] = None


class VolatilityIndicators(BaseModel):
    """Volatility indicators"""
    atr: Optional[float] = None
    atr_percent: Optional[float] = None
    bollinger_upper: Optional[float] = None
    bollinger_middle: Optional[float] = None
    bollinger_lower: Optional[float] = None
    bollinger_width: Optional[float] = None
    price_position: Optional[str] = None  # "above_upper", "below_lower", "within"


class VolumeAnalysis(BaseModel):
    """Volume analysis"""
    current_volume: Optional[int] = None
    avg_volume_20d: Optional[int] = None
    volume_ratio: Optional[float] = None
    is_unusual: Optional[bool] = None
    volume_trend: Optional[str] = None  # "increasing", "decreasing", "stable"
    # Advanced volume metrics
    vwap: Optional[float] = None
    price_vs_vwap: Optional[str] = None  # "above" or "below"
    obv: Optional[float] = None
    obv_trend: Optional[str] = None
    mfi: Optional[float] = None
    mfi_signal: Optional[str] = None
    volume_roc: Optional[float] = None
    cmf: Optional[float] = None
    cmf_signal: Optional[str] = None


class PriceLevels(BaseModel):
    """Key price levels"""
    support_1: Optional[float] = None
    support_2: Optional[float] = None
    resistance_1: Optional[float] = None
    resistance_2: Optional[float] = None
    pivot_point: Optional[float] = None
    ath: Optional[float] = None
    atl: Optional[float] = None
    week_52_high: Optional[float] = None
    week_52_low: Optional[float] = None
    distance_from_ath: Optional[float] = None  # percentage
    distance_from_atl: Optional[float] = None  # percentage
    distance_from_52w_high: Optional[float] = None
    distance_from_52w_low: Optional[float] = None


class TechnicalIndicators(BaseModel):
    """Complete technical analysis"""
    moving_averages: MovingAverages
    momentum: MomentumIndicators
    volatility: VolatilityIndicators
    volume: VolumeAnalysis
    price_levels: PriceLevels
    overall_trend: Optional[str] = None  # "bullish", "bearish", "neutral"


# ═══════════════════════════════════════════════════════════════
# OPTIONS MODELS
# ═══════════════════════════════════════════════════════════════

class OptionContract(BaseModel):
    """Single option contract"""
    strike: float
    expiration: str
    type: str  # "call" or "put"
    bid: Optional[float] = None
    ask: Optional[float] = None
    last_price: Optional[float] = None
    volume: Optional[int] = None
    open_interest: Optional[int] = None
    implied_volatility: Optional[float] = None


class OptionsData(BaseModel):
    """Options chain summary"""
    symbol: str
    expirations: List[str]
    put_call_ratio: Optional[float] = None
    total_call_volume: int = 0
    total_put_volume: int = 0
    total_call_oi: int = 0
    total_put_oi: int = 0
    max_pain: Optional[float] = None
    nearest_calls: List[OptionContract] = []
    nearest_puts: List[OptionContract] = []
    unusual_activity: List[dict] = []
    # Additional volume metrics
    total_options_volume: Optional[int] = None
    volume_vs_oi_ratio: Optional[float] = None
    volume_signal: Optional[str] = None  # "unusually_high", "high", "normal", "low"
    call_volume_vs_put_volume: Optional[float] = None


# ═══════════════════════════════════════════════════════════════
# NEWS MODELS
# ═══════════════════════════════════════════════════════════════

class NewsItem(BaseModel):
    """Single news article with source"""
    title: str
    source: str
    url: Optional[str] = None
    published_at: datetime
    sentiment: Optional[str] = None  # "positive", "negative", "neutral"
    summary: Optional[str] = None


class NewsSummary(BaseModel):
    """News summary with sentiment analysis"""
    symbol: str
    articles: List[NewsItem]
    overall_sentiment: str  # "positive", "negative", "neutral"
    key_catalysts: List[str] = []
    earnings_date: Optional[str] = None


# ═══════════════════════════════════════════════════════════════
# ANALYSIS MODELS
# ═══════════════════════════════════════════════════════════════

class AIAnalysis(BaseModel):
    """AI-generated analysis"""
    summary: str
    sentiment: str  # "bullish", "bearish", "neutral"
    confidence: float  # 0.0 to 1.0
    key_points: List[str] = []
    catalysts: List[str] = []
    risks: List[str] = []
    price_targets: Optional[dict] = None
    recommendation: Optional[str] = None
    generated_at: datetime


class StockAnalysis(BaseModel):
    """Complete stock analysis"""
    symbol: str
    company_name: Optional[str] = None
    quote: StockQuote
    technicals: TechnicalIndicators
    options: Optional[OptionsData] = None
    news: Optional[NewsSummary] = None
    fundamentals: Optional[Fundamentals] = None
    alpha_score: Optional[dict] = None
    ai_analysis: Optional[AIAnalysis] = None
    analyzed_at: datetime


# ═══════════════════════════════════════════════════════════════
# REQUEST/RESPONSE MODELS
# ═══════════════════════════════════════════════════════════════

class AnalysisRequest(BaseModel):
    """Request for stock analysis"""
    symbol: str
    include_options: bool = True
    include_news: bool = True
    include_ai: bool = True


class ScanRequest(BaseModel):
    """Market scan request"""
    symbols: Optional[List[str]] = None
    strategies: List[str] = ["breakout", "momentum", "unusual_volume"]
    min_price: float = 5.0
    max_price: float = 500.0
    min_volume: int = 100000


class ScanResult(BaseModel):
    """Single scan result"""
    symbol: str
    company_name: Optional[str] = None
    price: float
    change_percent: float
    volume: int
    signals: List[str]
    score: int
    sentiment: str
    brief: str

