# api/main.py

"""
Alpha Discovery API — FastAPI Application
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timezone
from typing import Optional

from api.config import API_TITLE, API_VERSION, API_DESCRIPTION, CORS_ORIGINS
from api.models.stock import (
    StockAnalysis, AnalysisRequest, ScanRequest, ScanResult
)
from api.services.stock_data import StockDataService
from api.services.indicators import IndicatorService
from api.services.options import OptionsService
from api.services.news import NewsService
from api.services.kimi import KimiService
from api.services.alpha import AlphaService


# ═══════════════════════════════════════════════════════════════
# APP SETUP
# ═══════════════════════════════════════════════════════════════

app = FastAPI(
    title=API_TITLE,
    version=API_VERSION,
    description=API_DESCRIPTION,
)

# CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
stock_service = StockDataService()
indicator_service = IndicatorService()
options_service = OptionsService()
news_service = NewsService()
kimi_service = KimiService()
alpha_service = AlphaService()


# ═══════════════════════════════════════════════════════════════
# HEALTH CHECK
# ═══════════════════════════════════════════════════════════════

@app.get("/api/health")
async def health_check():
    """API health check endpoint"""
    return {
        "status": "healthy",
        "version": API_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ═══════════════════════════════════════════════════════════════
# STOCK ANALYSIS
# ═══════════════════════════════════════════════════════════════

@app.get("/api/analyze/{symbol}")
async def analyze_stock(
    symbol: str,
    include_options: bool = Query(True, description="Include options data"),
    include_news: bool = Query(True, description="Include news data"),
    include_ai: bool = Query(True, description="Include AI analysis"),
):
    """
    Get comprehensive analysis for a single stock
    
    Returns:
    - Current quote and price data
    - Technical indicators (SMA, RSI, MACD, Bollinger Bands, etc.)
    - Volume metrics and alpha signals
    - Options chain summary and unusual activity
    - Recent news and sentiment
    - AI-powered analysis with sentiment and recommendations
    """
    symbol = symbol.upper().strip()
    
    # Get quote
    quote = stock_service.get_quote(symbol)
    if not quote:
        raise HTTPException(status_code=404, detail=f"Symbol {symbol} not found")
    
    # Get historical data for indicators
    history = stock_service.get_historical_data(symbol, period="1y")
    if not history:
        raise HTTPException(status_code=404, detail=f"No historical data for {symbol}")
    
    # Calculate technical indicators
    technicals = indicator_service.calculate_all(
        closes=history["closes"],
        highs=history["highs"],
        lows=history["lows"],
        volumes=[int(v) for v in history["volumes"]],
        current_price=quote.price,
    )
    
    # Calculate volume metrics
    volume_metrics = alpha_service.calculate_volume_metrics(
        volumes=[int(v) for v in history["volumes"]],
        closes=history["closes"],
        current_price=quote.price,
        current_volume=quote.volume,
    )
    
    # Get options data
    options = None
    if include_options:
        options = options_service.get_options_data(symbol)
    
    # Get news
    news = None
    if include_news:
        news = news_service.get_news(symbol)
    
    # Get fundamentals
    fundamentals = stock_service.get_fundamentals(symbol)
    
    # Get company name
    company_name = stock_service.get_company_name(symbol)
    
    # Calculate alpha score
    alpha_score = alpha_service.calculate_alpha_score(
        quote=quote,
        technicals=technicals,
        volume_metrics=volume_metrics,
        options=options,
        news=news,
        fundamentals=fundamentals,
    )
    
    # Generate AI analysis
    ai_analysis = None
    if include_ai:
        ai_analysis = kimi_service.analyze(
            symbol=symbol,
            quote=quote,
            technicals=technicals,
            options=options,
            news=news,
            fundamentals=fundamentals,
        )
    
    return {
        "symbol": symbol,
        "company_name": company_name,
        "quote": quote,
        "technicals": technicals,
        "volume_metrics": volume_metrics,
        "alpha_score": alpha_score,
        "options": options,
        "news": news,
        "fundamentals": fundamentals,
        "ai_analysis": ai_analysis,
        "analyzed_at": datetime.now(timezone.utc),
    }


# ═══════════════════════════════════════════════════════════════
# QUICK ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@app.get("/api/quote/{symbol}")
async def get_quote(symbol: str):
    """Get current quote for a symbol"""
    symbol = symbol.upper().strip()
    quote = stock_service.get_quote(symbol)
    
    if not quote:
        raise HTTPException(status_code=404, detail=f"Symbol {symbol} not found")
    
    return quote


@app.get("/api/technicals/{symbol}")
async def get_technicals(symbol: str):
    """Get technical indicators for a symbol"""
    symbol = symbol.upper().strip()
    
    quote = stock_service.get_quote(symbol)
    if not quote:
        raise HTTPException(status_code=404, detail=f"Symbol {symbol} not found")
    
    history = stock_service.get_historical_data(symbol, period="1y")
    if not history:
        raise HTTPException(status_code=404, detail=f"No historical data for {symbol}")
    
    technicals = indicator_service.calculate_all(
        closes=history["closes"],
        highs=history["highs"],
        lows=history["lows"],
        volumes=[int(v) for v in history["volumes"]],
        current_price=quote.price,
    )
    
    return {
        "symbol": symbol,
        "price": quote.price,
        "technicals": technicals,
    }


@app.get("/api/options/{symbol}")
async def get_options(symbol: str):
    """Get options chain data for a symbol"""
    symbol = symbol.upper().strip()
    
    options = options_service.get_options_data(symbol)
    if not options:
        raise HTTPException(status_code=404, detail=f"No options data for {symbol}")
    
    # Include sentiment analysis
    sentiment = options_service.analyze_sentiment(options)
    
    return {
        "symbol": symbol,
        "options": options,
        "sentiment": sentiment,
    }


@app.get("/api/news/{symbol}")
async def get_news(symbol: str, limit: int = Query(15, ge=1, le=50)):
    """
    Get recent news for a symbol with source information
    
    Returns:
    - Articles with source, URL, timestamp, sentiment
    - Overall sentiment analysis
    - Key catalysts extracted from headlines
    - Earnings date if available
    """
    symbol = symbol.upper().strip()
    
    news = news_service.get_news(symbol, limit=limit)
    if not news:
        raise HTTPException(status_code=404, detail=f"No news found for {symbol}")
    
    # Format for frontend display
    return {
        "symbol": symbol,
        "overall_sentiment": news.overall_sentiment,
        "earnings_date": news.earnings_date,
        "catalysts": news.key_catalysts,
        "article_count": len(news.articles),
        "articles": [
            {
                "id": i + 1,
                "title": article.title,
                "source": article.source,
                "url": article.url,
                "published_at": article.published_at.isoformat(),
                "sentiment": article.sentiment,
                "summary": article.summary,
            }
            for i, article in enumerate(news.articles)
        ],
    }


@app.get("/api/news/{symbol}/for-ai")
async def get_news_for_ai(symbol: str):
    """
    Get news formatted for AI analysis with citation numbers
    
    This endpoint returns news in a format optimized for LLM consumption
    with citation numbers that can be referenced in AI responses.
    """
    symbol = symbol.upper().strip()
    
    news_data = news_service.get_news_for_ai(symbol)
    return {
        "symbol": symbol,
        **news_data,
    }


# ═══════════════════════════════════════════════════════════════
# MARKET SCAN
# ═══════════════════════════════════════════════════════════════

@app.post("/api/scan", response_model=list[ScanResult])
async def scan_market(request: ScanRequest):
    """
    Scan market for alpha opportunities
    
    Runs multiple strategies and returns ranked results:
    - Breakout: Stocks near ATH/ATL
    - Momentum: Strong trend with volume
    - Unusual Volume: Volume spikes
    """
    # Get symbols to scan
    if request.symbols:
        symbols = request.symbols
    else:
        # Get all tradeable symbols (limited for speed)
        all_symbols = stock_service.get_tradeable_symbols()
        symbols = all_symbols[:100]  # Limit for API response time
    
    results = []
    
    for symbol in symbols:
        try:
            # Quick data fetch
            quote = stock_service.get_quote(symbol)
            if not quote:
                continue
            
            # Apply price filter
            if quote.price < request.min_price or quote.price > request.max_price:
                continue
            
            # Apply volume filter
            if quote.volume < request.min_volume:
                continue
            
            # Get quick technicals
            history = stock_service.get_historical_data(symbol, period="3mo")
            if not history:
                continue
            
            technicals = indicator_service.calculate_all(
                closes=history["closes"],
                highs=history["highs"],
                lows=history["lows"],
                volumes=[int(v) for v in history["volumes"]],
                current_price=quote.price,
            )
            
            # Check strategies
            signals = []
            score = 0
            
            # Breakout strategy
            if "breakout" in request.strategies:
                if technicals.price_levels.distance_from_ath:
                    if technicals.price_levels.distance_from_ath > -5:
                        signals.append("near_ath")
                        score += 3
                if technicals.price_levels.distance_from_atl:
                    if technicals.price_levels.distance_from_atl < 10:
                        signals.append("near_atl")
                        score += 2
            
            # Momentum strategy
            if "momentum" in request.strategies:
                if technicals.overall_trend == "bullish":
                    signals.append("bullish_trend")
                    score += 2
                if technicals.momentum.macd_trend == "bullish":
                    signals.append("macd_bullish")
                    score += 1
            
            # Unusual volume strategy
            if "unusual_volume" in request.strategies:
                if technicals.volume.is_unusual:
                    signals.append("unusual_volume")
                    score += 2
            
            # Only include if has signals
            if signals:
                sentiment = "bullish" if technicals.overall_trend == "bullish" else \
                           "bearish" if technicals.overall_trend == "bearish" else "neutral"
                
                results.append(ScanResult(
                    symbol=symbol,
                    company_name=stock_service.get_company_name(symbol),
                    price=quote.price,
                    change_percent=quote.change_percent,
                    volume=quote.volume,
                    signals=signals,
                    score=score,
                    sentiment=sentiment,
                    brief=f"{technicals.overall_trend.title() if technicals.overall_trend else 'Mixed'} setup, {', '.join(signals)}",
                ))
                
        except Exception as e:
            continue
    
    # Sort by score
    results.sort(key=lambda x: x.score, reverse=True)
    
    return results[:50]  # Top 50


# ═══════════════════════════════════════════════════════════════
# RUN SERVER
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

