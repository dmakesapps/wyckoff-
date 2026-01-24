# api/models/stock.py

"""
Pydantic models for API requests and responses
"""

from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime


# ═══════════════════════════════════════════════════════════════
# STOCK DATA MODELS
# ═══════════════════════════════════════════════════════════════

class StockQuote(BaseModel):
    """Current stock price data"""
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


class MovingAverages(BaseModel):
    """Moving average values"""
    sma_20: Optional[float] = None
    sma_50: Optional[float] = None
    sma_200: Optional[float] = None
    ema_20: Optional[float] = None
    price_vs_sma_20: Optional[str] = None  # "above" or "below"
    price_vs_sma_50: Optional[str] = None
    price_vs_sma_200: Optional[str] = None
    golden_cross: Optional[bool] = None  # 50 SMA > 200 SMA
    death_cross: Optional[bool] = None   # 50 SMA < 200 SMA


class MomentumIndicators(BaseModel):
    """Momentum indicator values"""
    rsi: Optional[float] = None
    rsi_signal: Optional[str] = None  # "overbought", "oversold", "neutral"
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_histogram: Optional[float] = None
    macd_trend: Optional[str] = None  # "bullish", "bearish", "neutral"
    stochastic_k: Optional[float] = None
    stochastic_d: Optional[float] = None
    stochastic_signal: Optional[str] = None


class VolatilityIndicators(BaseModel):
    """Volatility indicator values"""
    bb_upper: Optional[float] = None
    bb_middle: Optional[float] = None
    bb_lower: Optional[float] = None
    bb_position: Optional[str] = None  # "above_upper", "below_lower", "within"
    atr: Optional[float] = None
    atr_percent: Optional[float] = None  # ATR as % of price


class VolumeAnalysis(BaseModel):
    """Volume analysis"""
    current_volume: int
    avg_volume_20d: Optional[float] = None
    volume_ratio: Optional[float] = None  # current / average
    is_unusual: bool = False
    volume_trend: Optional[str] = None  # "increasing", "decreasing", "stable"


class PriceLevels(BaseModel):
    """Key price levels"""
    ath: Optional[float] = None
    ath_date: Optional[str] = None
    atl: Optional[float] = None
    atl_date: Optional[str] = None
    week_52_high: Optional[float] = None
    week_52_low: Optional[float] = None
    distance_from_ath: Optional[float] = None  # percentage
    distance_from_atl: Optional[float] = None
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
# OPTIONS DATA MODELS
# ═══════════════════════════════════════════════════════════════

class OptionContract(BaseModel):
    """Single option contract"""
    strike: float
    expiration: str
    contract_type: Literal["call", "put"]
    bid: float
    ask: float
    last_price: float
    volume: int
    open_interest: int
    implied_volatility: Optional[float] = None


class OptionsData(BaseModel):
    """Options chain summary"""
    symbol: str
    expirations: list[str]
    put_call_ratio: Optional[float] = None
    total_call_volume: int = 0
    total_put_volume: int = 0
    total_call_oi: int = 0
    total_put_oi: int = 0
    iv_percentile: Optional[float] = None
    max_pain: Optional[float] = None
    unusual_activity: list[dict] = []
    nearest_expiry_calls: list[OptionContract] = []
    nearest_expiry_puts: list[OptionContract] = []


# ═══════════════════════════════════════════════════════════════
# NEWS DATA MODELS
# ═══════════════════════════════════════════════════════════════

class NewsItem(BaseModel):
    """Single news article"""
    title: str
    summary: Optional[str] = None
    source: str
    url: str
    published_at: datetime
    sentiment: Optional[str] = None  # "positive", "negative", "neutral"


class NewsSummary(BaseModel):
    """News summary for a stock"""
    symbol: str
    articles: list[NewsItem]
    overall_sentiment: Optional[str] = None
    key_catalysts: list[str] = []
    earnings_date: Optional[str] = None


# ═══════════════════════════════════════════════════════════════
# FUNDAMENTALS
# ═══════════════════════════════════════════════════════════════

class Fundamentals(BaseModel):
    """Basic fundamental data"""
    market_cap: Optional[float] = None
    market_cap_formatted: Optional[str] = None
    pe_ratio: Optional[float] = None
    forward_pe: Optional[float] = None
    eps: Optional[float] = None
    dividend_yield: Optional[float] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    shares_outstanding: Optional[int] = None
    float_shares: Optional[int] = None
    short_percent: Optional[float] = None


# ═══════════════════════════════════════════════════════════════
# AI ANALYSIS
# ═══════════════════════════════════════════════════════════════

class AIAnalysis(BaseModel):
    """AI-generated analysis"""
    summary: str
    sentiment: Literal["bullish", "bearish", "neutral"]
    confidence: float = Field(ge=0, le=100)  # 0-100
    key_points: list[str]
    catalysts: list[str]
    risks: list[str]
    price_targets: Optional[dict] = None  # {"support": x, "resistance": y}
    recommendation: Optional[str] = None
    generated_at: datetime


# ═══════════════════════════════════════════════════════════════
# COMPLETE ANALYSIS RESPONSE
# ═══════════════════════════════════════════════════════════════

class StockAnalysis(BaseModel):
    """Complete stock analysis response"""
    symbol: str
    company_name: Optional[str] = None
    quote: StockQuote
    technicals: TechnicalIndicators
    options: Optional[OptionsData] = None
    news: Optional[NewsSummary] = None
    fundamentals: Optional[Fundamentals] = None
    ai_analysis: Optional[AIAnalysis] = None
    analyzed_at: datetime


# ═══════════════════════════════════════════════════════════════
# REQUEST MODELS
# ═══════════════════════════════════════════════════════════════

class AnalysisRequest(BaseModel):
    """Request for single stock analysis"""
    symbol: str
    include_options: bool = True
    include_news: bool = True
    include_ai: bool = True


class ScanRequest(BaseModel):
    """Request for market scan"""
    symbols: Optional[list[str]] = None  # If None, scan all tradeable
    min_price: float = 1.0
    max_price: float = 10000.0
    min_volume: int = 100000
    strategies: list[str] = ["breakout", "momentum", "unusual_volume"]


class ScanResult(BaseModel):
    """Single result from market scan"""
    symbol: str
    company_name: Optional[str] = None
    price: float
    change_percent: float
    volume: int
    signals: list[str]  # Which strategies flagged this
    score: float  # Overall alpha score
    sentiment: Literal["bullish", "bearish", "neutral"]
    brief: str  # One-line summary

