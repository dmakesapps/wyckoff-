# api/main.py

"""
Alpha Discovery API — FastAPI Application
"""

import json
import threading
from fastapi import FastAPI, HTTPException, Query, Request, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from datetime import datetime, timezone, timedelta
from typing import Optional, List
import os
import json

from api.config import API_TITLE, API_VERSION, API_DESCRIPTION, CORS_ORIGINS
from api.models.stock import (
    StockAnalysis, AnalysisRequest, ScanRequest, ScanResult
)
from api.services.stock_data import StockDataService
from api.services.indicators import IndicatorService
from api.services.options import OptionsService
from api.services.news import NewsService
from api.services.alpha import AlphaService
from api.services.chart import ChartService
from api.services.market_pulse import market_pulse_service

# Scanner imports
from api.scanner.database import ScannerDB
from api.scanner.scheduler import start_scheduler, get_scheduler


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
    allow_origins=["*"],  # Allow all for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
stock_service = StockDataService()
indicator_service = IndicatorService()
options_service = OptionsService()
news_service = NewsService()
alpha_service = AlphaService()
chart_service = ChartService()

# Initialize scanner database
scanner_db = ScannerDB()

# ═══════════════════════════════════════════════════════════════
# HEADLINES CACHE (1 hour)
# ═══════════════════════════════════════════════════════════════
_headlines_cache = {
    "data": None,
    "timestamp": None,
    "lock": threading.Lock(),
    "cache_minutes": 60,  # 1 hour cache
}


# AI Tool Execution logic removed (was for Kimi)
# AI Tool Execution and Chat Logic removed.


# ═══════════════════════════════════════════════════════════════
# STARTUP/SHUTDOWN EVENTS
# ═══════════════════════════════════════════════════════════════

@app.on_event("startup")
async def startup_event():
    """Start background scanner on server startup"""
    print("🚀 Starting Alpha Discovery API...")
    print("   Docs: http://localhost:8000/docs")
    print("   Health: http://localhost:8000/api/health")
    print("")
    
    # Start the scanner scheduler
    try:
        scheduler = start_scheduler()
        print(f"🔄 Scanner scheduler started (every {scheduler.interval_minutes} mins)")
        print("   First scan will begin shortly...")
    except Exception as e:
        print(f"⚠️  Scanner failed to start: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Stop scanner on shutdown"""
    from api.scanner.scheduler import stop_scheduler
    stop_scheduler()
    print("Scanner stopped")


# ═══════════════════════════════════════════════════════════════
# HEALTH CHECK
# ═══════════════════════════════════════════════════════════════

@app.get("/api/health")
async def health_check():
    """API health check endpoint"""
    scheduler = get_scheduler()
    scanner_status = scheduler.get_status() if scheduler else {}
    
    return {
        "status": "healthy",
        "version": API_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "scanner": {
            "running": scanner_status.get("running", False),
            "last_scan": scanner_status.get("last_scan"),
            "stocks_in_db": scanner_status.get("db_stats", {}).get("total_stocks", 0),
        }
    }

IDEAS_FILE = os.path.join(os.path.dirname(__file__), "../agentic_layer/knowledge_base/ideas.json")

# AI Ideas endpoint removed

# Removed intelligence system as it depends on LLM agent logic

# Removed intelligence endpoints

# Removed bot status endpoint


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


# Removed news for ai endpoint


# ═══════════════════════════════════════════════════════════════
# MARKET SCAN
# ═══════════════════════════════════════════════════════════════

@app.api_route("/api/scan", methods=["GET", "POST"], response_model=list[ScanResult])
async def scan_market(
    request: Optional[ScanRequest] = None,
    symbols: Optional[str] = Query(None, description="Comma-separated symbols to scan"),
    min_price: float = Query(5.0, description="Minimum price"),
    max_price: float = Query(500.0, description="Maximum price"),
    min_volume: int = Query(100000, description="Minimum volume"),
):
    """
    Scan market for alpha opportunities
    
    Supports both POST (with JSON body) and GET (with query parameters).
    
    If no symbols provided, scans a subset of tradeable symbols.
    """
    # If it's a POST request, 'request' will be populated by FastAPI from the body.
    # If it's a GET request, we build the request object from query parameters.
    if request is None:
        symbol_list = [s.strip().upper() for s in symbols.split(",")] if symbols else None
        request = ScanRequest(
            symbols=symbol_list,
            min_price=min_price,
            max_price=max_price,
            min_volume=min_volume
        )
    
    # If no specific symbols provided, use the faster database-backed scanner
    if not request.symbols:
        db_results = scanner_db.search_stocks(
            min_price=request.min_price,
            max_price=request.max_price,
            min_volume=request.min_volume,
            limit=50
        )
        
        # If DB has results, return them immediately
        if db_results:
            results = []
            for r in db_results:
                signals = []
                score = 0
                if r.get("is_unusual_volume"):
                    signals.append("unusual_volume")
                    score += 2
                if r.get("is_near_high"):
                    signals.append("near_ath")
                    score += 3
                    
                change = r.get("change_percent", 0)
                sentiment = "bullish" if change > 2 else "bearish" if change < -2 else "neutral"
                
                results.append(ScanResult(
                    symbol=r["symbol"],
                    company_name=r.get("company_name"),
                    price=r["price"],
                    change_percent=change,
                    volume=r["volume"],
                    signals=signals,
                    score=score,
                    sentiment=sentiment,
                    brief=f"{sentiment.title()} move with {r.get('relative_volume', 1):.1f}x relative volume",
                ))
            return results

    # Fallback to live scan for specific symbols (limit to 15 to avoid timeout)
    symbols = request.symbols or []
    if len(symbols) > 15:
        symbols = symbols[:15]
    
    results = []
    for symbol in symbols:
        try:
            # Live scan logic...
            quote = stock_service.get_quote(symbol)
            if not quote: continue
            if quote.price < request.min_price or quote.price > request.max_price: continue
            if quote.volume < request.min_volume: continue
            
            history = stock_service.get_historical_data(symbol, period="3mo")
            if not history: continue
            
            technicals = indicator_service.calculate_all(
                closes=history["closes"],
                highs=history["highs"],
                lows=history["lows"],
                volumes=[int(v) for v in history["volumes"]],
                current_price=quote.price,
            )
            
            signals = []
            score = 0
            if "breakout" in request.strategies:
                if technicals.price_levels.distance_from_ath and technicals.price_levels.distance_from_ath > -5:
                    signals.append("near_ath"); score += 3
            if "momentum" in request.strategies and technicals.overall_trend == "bullish":
                signals.append("bullish_trend"); score += 2
            if "unusual_volume" in request.strategies and technicals.volume.is_unusual:
                signals.append("unusual_volume"); score += 2
            
            if signals:
                results.append(ScanResult(
                    symbol=symbol,
                    company_name=stock_service.get_company_name(symbol),
                    price=quote.price,
                    change_percent=quote.change_percent,
                    volume=quote.volume,
                    signals=signals,
                    score=score,
                    sentiment="bullish" if technicals.overall_trend == "bullish" else "neutral",
                    brief=f"{technicals.overall_trend.title()} setup, {', '.join(signals)}",
                ))
        except: continue

    results.sort(key=lambda x: x.score, reverse=True)
    return results[:50]


# ═══════════════════════════════════════════════════════════════
# CHAT ENDPOINT (Streaming)
# ═══════════════════════════════════════════════════════════════

# Removed chat endpoint


# ═══════════════════════════════════════════════════════════════
# POSITIONS ENDPOINT
# ═══════════════════════════════════════════════════════════════

@app.get("/api/positions")
async def get_positions():
    """
    Get user's portfolio positions with live prices
    
    Note: This is currently using sample data.
    In production, integrate with a broker API or database.
    """
    # Sample positions - replace with real data source
    sample_positions = [
        {"symbol": "AAPL", "shares": 100, "avg_cost": 150.00},
        {"symbol": "NVDA", "shares": 50, "avg_cost": 450.00},
        {"symbol": "TSLA", "shares": 25, "avg_cost": 200.00},
        {"symbol": "MSFT", "shares": 75, "avg_cost": 350.00},
    ]
    
    positions = []
    total_value = 0
    total_cost = 0
    total_gain_loss = 0
    
    for pos in sample_positions:
        quote = stock_service.get_quote(pos["symbol"])
        if quote:
            current_value = quote.price * pos["shares"]
            cost_basis = pos["avg_cost"] * pos["shares"]
            gain_loss = current_value - cost_basis
            gain_loss_pct = (gain_loss / cost_basis) * 100
            
            positions.append({
                "symbol": pos["symbol"],
                "company_name": stock_service.get_company_name(pos["symbol"]),
                "shares": pos["shares"],
                "avg_cost": pos["avg_cost"],
                "current_price": quote.price,
                "current_value": round(current_value, 2),
                "cost_basis": round(cost_basis, 2),
                "gain_loss": round(gain_loss, 2),
                "gain_loss_percent": round(gain_loss_pct, 2),
                "day_change": quote.change,
                "day_change_percent": quote.change_percent,
            })
            
            total_value += current_value
            total_cost += cost_basis
            total_gain_loss += gain_loss
    
    return {
        "positions": positions,
        "summary": {
            "total_value": round(total_value, 2),
            "total_cost": round(total_cost, 2),
            "total_gain_loss": round(total_gain_loss, 2),
            "total_gain_loss_percent": round((total_gain_loss / total_cost) * 100, 2) if total_cost > 0 else 0,
        },
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


# ═══════════════════════════════════════════════════════════════
# MARKET NEWS ENDPOINT
# ═══════════════════════════════════════════════════════════════

@app.get("/api/market/news")
async def get_market_news(limit: int = Query(15, ge=1, le=50)):
    """
    Get general market news with sentiment analysis
    
    Uses major indices/ETFs to get broad market news:
    - SPY (S&P 500)
    - QQQ (Nasdaq)
    """
    # Fetch news from major market proxies
    spy_news = news_service.get_news("SPY", limit=limit // 2)
    qqq_news = news_service.get_news("QQQ", limit=limit // 2)
    
    all_articles = []
    
    if spy_news:
        all_articles.extend(spy_news.articles)
    if qqq_news:
        all_articles.extend(qqq_news.articles)
    
    # Sort by date and deduplicate
    seen_titles = set()
    unique_articles = []
    for article in sorted(all_articles, key=lambda x: x.published_at, reverse=True):
        if article.title not in seen_titles:
            seen_titles.add(article.title)
            unique_articles.append(article)
    
    # Calculate overall sentiment
    sentiments = [a.sentiment for a in unique_articles]
    pos = sentiments.count("positive")
    neg = sentiments.count("negative")
    overall = "positive" if pos > neg else "negative" if neg > pos else "neutral"
    
    return {
        "overall_sentiment": overall,
        "article_count": len(unique_articles),
        "articles": [
            {
                "id": i + 1,
                "title": article.title,
                "source": article.source,
                "url": article.url,
                "published_at": article.published_at.isoformat(),
                "sentiment": article.sentiment,
            }
            for i, article in enumerate(unique_articles[:limit])
        ],
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }


# ═══════════════════════════════════════════════════════════════
# SCANNER ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@app.get("/api/scanner/status")
async def get_scanner_status():
    """Get current scanner status and statistics"""
    scheduler = get_scheduler()
    return scheduler.get_status()


@app.post("/api/scanner/trigger")
async def trigger_scan():
    """Manually trigger a market scan"""
    scheduler = get_scheduler()
    return scheduler.trigger_scan_now()


@app.get("/api/scanner/validate/{symbol}")
async def validate_symbol(symbol: str):
    """
    Check if a stock symbol is valid and tradeable
    
    Returns:
        valid: bool - True if symbol is active and tradeable
        message: str - Reason if invalid
    """
    scheduler = get_scheduler()
    
    # Only works with Alpaca scanner
    if not scheduler.use_alpaca:
        raise HTTPException(status_code=501, detail="Validation requires Alpaca scanner")
    
    is_valid = scheduler.scanner.is_valid_symbol(symbol.upper())
    
    return {
        "symbol": symbol.upper(),
        "valid": is_valid,
        "message": "Active and tradeable" if is_valid else "Symbol may be delisted, halted, or invalid"
    }


@app.post("/api/scanner/validate")
async def validate_symbols(symbols: list[str] = Body(..., embed=True)):
    """
    Validate multiple symbols at once
    
    Request body: {"symbols": ["AAPL", "MSFT", "INVALID123"]}
    
    Returns:
        valid: list of valid symbols
        invalid: list of invalid/delisted symbols
    """
    scheduler = get_scheduler()
    
    if not scheduler.use_alpaca:
        raise HTTPException(status_code=501, detail="Validation requires Alpaca scanner")
    
    valid, invalid = scheduler.scanner.validate_symbols(symbols)
    
    return {
        "valid": valid,
        "invalid": invalid,
        "valid_count": len(valid),
        "invalid_count": len(invalid)
    }


@app.post("/api/scanner/cleanup")
async def cleanup_invalid_symbols():
    """
    Manually trigger cleanup of invalid/delisted symbols from database
    """
    scheduler = get_scheduler()
    scheduler._cleanup_invalid_symbols()
    
    return {
        "status": "completed",
        "message": "Invalid symbols removed from database"
    }


@app.get("/api/scanner/unusual-volume")
async def get_unusual_volume_stocks(
    min_rvol: float = Query(2.0, description="Minimum relative volume"),
    market_cap: str = Query(None, description="Market cap category"),
    limit: int = Query(50, ge=1, le=200)
):
    """Get stocks with unusual trading volume"""
    results = scanner_db.get_unusual_volume(
        min_rvol=min_rvol,
        limit=limit,
        market_cap_category=market_cap
    )
    return {"count": len(results), "stocks": results}


@app.get("/api/scanner/top-movers")
async def get_top_movers(
    direction: str = Query("gainers", description="'gainers' or 'losers'"),
    market_cap: str = Query(None, description="Market cap category"),
    limit: int = Query(50, ge=1, le=200)
):
    """Get top gaining or losing stocks"""
    if direction == "gainers":
        results = scanner_db.get_top_gainers(limit=limit, market_cap_category=market_cap)
    else:
        results = scanner_db.get_top_losers(limit=limit, market_cap_category=market_cap)
    return {"direction": direction, "count": len(results), "stocks": results}


@app.get("/api/scanner/breakouts")
async def get_breakout_candidates(
    type: str = Query("near_high", description="'near_high' or 'near_low'"),
    market_cap: str = Query(None, description="Market cap category"),
    limit: int = Query(50, ge=1, le=200)
):
    """Get stocks near 52-week high or low"""
    if type == "near_high":
        results = scanner_db.get_near_52w_high(limit=limit, market_cap_category=market_cap)
    else:
        results = scanner_db.get_near_52w_low(limit=limit, market_cap_category=market_cap)
    return {"type": type, "count": len(results), "stocks": results}


@app.get("/api/scanner/sector/{sector}")
async def get_sector_stocks(
    sector: str,
    sort_by: str = Query("change_percent", description="Sort field"),
    limit: int = Query(50, ge=1, le=200)
):
    """Get stocks in a specific sector"""
    results = scanner_db.get_by_sector(sector=sector, sort_by=sort_by, limit=limit)
    return {"sector": sector, "count": len(results), "stocks": results}


# ═══════════════════════════════════════════════════════════════
# CHART ENDPOINTS (Lightweight Charts Integration)
# ═══════════════════════════════════════════════════════════════

@app.get("/api/chart/config")
async def get_chart_config():
    """
    📋 Get chart configuration (available indicators, intervals, periods)
    
    Returns metadata about each indicator including:
    - ID for API requests
    - Display name
    - Type (overlay on price or separate pane)
    - Default color
    """
    return {
        "indicators": chart_service.get_available_indicators(),
        "intervals": list(chart_service.INTERVALS.keys()),
        "periods": list(chart_service.PERIODS.keys()),
    }


@app.get("/api/chart/{symbol}/mini")
async def get_mini_chart(
    symbol: str,
    period: str = Query("3mo", description="Time period: 1mo, 3mo, 6mo"),
    candles: int = Query(50, ge=20, le=100, description="Number of candles")
):
    """
    📊 Get mini chart data for Kimi chat responses
    
    Lightweight chart data optimized for inline display in chat.
    Includes only essential data: candlesticks, SMA 20, and volume.
    
    **Use case:** When Kimi includes a chart reference in its response,
    the frontend fetches this endpoint to render an inline chart.
    
    **Example:**
    ```
    GET /api/chart/TSLA/mini?period=3mo&candles=50
    ```
    """
    data = chart_service.get_mini_chart(
        symbol=symbol.upper(),
        period=period,
        candles=candles
    )
    
    if not data:
        raise HTTPException(status_code=404, detail=f"No chart data found for {symbol}")
    
    return data


@app.get("/api/chart/{symbol}")
async def get_chart_data(
    symbol: str,
    interval: str = Query("1d", description="Candle interval: 1m, 5m, 15m, 30m, 1h, 1d, 1wk, 1mo"),
    period: str = Query("1y", description="Time period: 7d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, max"),
    indicators: str = Query("sma_20,sma_50,sma_200,rsi,volume", description="Comma-separated indicators")
):
    """
    📈 Get chart data for Lightweight Charts
    
    Returns OHLCV candlestick data with optional indicators.
    Data is formatted for direct use with Lightweight Charts library.
    
    **Intervals:**
    - 1m, 5m, 15m, 30m: Intraday (limited history)
    - 1h: Hourly (up to 730 days)
    - 1d: Daily (years of data) ⭐ Recommended
    - 1wk, 1mo: Weekly/Monthly
    
    **Indicators:**
    - sma_20, sma_50, sma_200: Simple Moving Averages
    - rsi: Relative Strength Index (14-period)
    - volume: Volume bars with color coding
    
    **Example:**
    ```
    GET /api/chart/AAPL?interval=1d&period=1y&indicators=sma_20,sma_50,volume
    ```
    """
    indicator_list = [i.strip() for i in indicators.split(",") if i.strip()]
    
    data = chart_service.get_chart_data(
        symbol=symbol.upper(),
        interval=interval,
        period=period,
        indicators=indicator_list
    )
    
    if not data:
        raise HTTPException(status_code=404, detail=f"No chart data found for {symbol}")
    
    return data


# ═══════════════════════════════════════════════════════════════
# MARKET INDICATORS (7 CATEGORIES)
# ═══════════════════════════════════════════════════════════════

@app.get("/api/market/indicators")
async def get_market_indicators():
    """
    📊 Complete market indicators - 7 categories updated every scan
    
    Returns:
    1. Market Breadth - Advancing/declining stocks, A/D ratio
    2. Volume Analysis - Up/down volume, unusual volume counts
    3. Momentum - Gainers/losers at various thresholds
    4. Sector Performance - Rankings by avg change
    5. Volatility - Big movers count, volatility level
    6. Fear & Greed Index - Composite score 0-100
    7. (SMA Analysis - Coming soon with historical cache)
    """
    scheduler = get_scheduler()
    indicators = scheduler.get_indicators()
    
    # If no indicators yet, calculate from existing DB data
    if "error" in indicators:
        indicators = scanner_db.calculate_and_store_indicators()
    
    return indicators


@app.get("/api/market/fear-greed")
async def get_fear_greed():
    """
    😱🤑 Fear & Greed Index
    
    A composite score from 0 (Extreme Fear) to 100 (Extreme Greed)
    
    Components:
    - Market Breadth (25%) - Advancing vs declining stocks
    - Volume (25%) - Up volume vs down volume
    - Momentum (25%) - Big gainers vs big losers
    - Market Strength (25%) - New highs vs new lows
    """
    scheduler = get_scheduler()
    indicators = scheduler.get_indicators()
    fg = indicators.get("fear_greed", {})
    
    return {
        "score": fg.get("score", 50),
        "label": fg.get("label", "Neutral"),
        "components": fg.get("components", {}),
        "interpretation": fg.get("interpretation", ""),
        "timestamp": indicators.get("timestamp"),
    }


@app.get("/api/market/indicators/history")
async def get_indicator_history(
    limit: int = Query(48, ge=1, le=500, description="Number of historical records")
):
    """
    📈 Historical market indicators for charting
    
    Returns the last N indicator snapshots (one per scan)
    Default: 48 records (about 24 hours if scanning every 30 min)
    """
    scheduler = get_scheduler()
    return {
        "history": scheduler.get_indicator_history(limit),
        "count": limit,
    }


# ═══════════════════════════════════════════════════════════════
# FINVIZ-STYLE ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@app.get("/api/market/overview")
async def get_market_overview():
    """
    Complete market overview like Finviz homepage
    
    Returns:
    - Market breadth (advancing/declining/unchanged)
    - New highs and lows
    - Sector performance summary
    - Top gainers/losers preview
    - Unusual volume preview
    """
    overview = scanner_db.get_finviz_style_overview()
    
    # Add top movers preview
    overview["top_gainers"] = scanner_db.get_top_gainers(limit=10)
    overview["top_losers"] = scanner_db.get_top_losers(limit=10)
    overview["most_active"] = scanner_db.get_most_active(limit=10)
    overview["unusual_volume"] = scanner_db.get_unusual_volume(limit=10)
    
    overview["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    return overview


@app.get("/api/market/gainers")
async def get_market_gainers(
    limit: int = Query(50, ge=1, le=200),
    min_volume: int = Query(100000, description="Minimum volume filter"),
    market_cap: str = Query(None, description="Market cap category filter")
):
    """
    Top gaining stocks - like Finviz Top Gainers
    
    Returns stocks sorted by % change (descending)
    """
    results = scanner_db.get_top_gainers(
        limit=limit, 
        min_volume=min_volume,
        market_cap_category=market_cap
    )
    
    # Format for frontend
    stocks = [{
        "rank": i + 1,
        "ticker": r["symbol"],
        "company": r["company_name"],
        "last": r["price"],
        "change": r["change_percent"],
        "volume": r["volume"],
        "relativeVolume": r["relative_volume"],
        "marketCap": r["market_cap"],
        "sector": r["sector"],
        "signal": "Top Gainers" if r["change_percent"] >= 10 else "Gainers"
    } for i, r in enumerate(results)]
    
    return {
        "count": len(stocks),
        "stocks": stocks,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }


@app.get("/api/market/losers")
async def get_market_losers(
    limit: int = Query(50, ge=1, le=200),
    min_volume: int = Query(100000, description="Minimum volume filter"),
    market_cap: str = Query(None, description="Market cap category filter")
):
    """
    Top losing stocks - like Finviz Top Losers
    
    Returns stocks sorted by % change (ascending, most negative first)
    """
    results = scanner_db.get_top_losers(
        limit=limit,
        min_volume=min_volume,
        market_cap_category=market_cap
    )
    
    # Format for frontend
    stocks = [{
        "rank": i + 1,
        "ticker": r["symbol"],
        "company": r["company_name"],
        "last": r["price"],
        "change": r["change_percent"],
        "volume": r["volume"],
        "relativeVolume": r["relative_volume"],
        "marketCap": r["market_cap"],
        "sector": r["sector"],
        "signal": "Top Losers" if r["change_percent"] <= -10 else "Losers"
    } for i, r in enumerate(results)]
    
    return {
        "count": len(stocks),
        "stocks": stocks,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }


@app.get("/api/market/most-active")
async def get_most_active(
    limit: int = Query(50, ge=1, le=200)
):
    """
    Most active stocks by volume - like Finviz Most Active
    """
    results = scanner_db.get_most_active(limit=limit)
    
    stocks = [{
        "rank": i + 1,
        "ticker": r["symbol"],
        "company": r["company_name"],
        "last": r["price"],
        "change": r["change_percent"],
        "volume": r["volume"],
        "relativeVolume": r["relative_volume"],
        "marketCap": r["market_cap"],
        "sector": r["sector"],
        "signal": "Most Active"
    } for i, r in enumerate(results)]
    
    return {
        "count": len(stocks),
        "stocks": stocks,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }


@app.get("/api/market/most-volatile")
async def get_most_volatile(
    limit: int = Query(50, ge=1, le=200)
):
    """
    Most volatile stocks (biggest % moves in either direction)
    """
    results = scanner_db.get_most_volatile(limit=limit)
    
    stocks = [{
        "rank": i + 1,
        "ticker": r["symbol"],
        "company": r["company_name"],
        "last": r["price"],
        "change": r["change_percent"],
        "absChange": abs(r["change_percent"]) if r["change_percent"] else 0,
        "volume": r["volume"],
        "relativeVolume": r["relative_volume"],
        "marketCap": r["market_cap"],
        "sector": r["sector"],
        "signal": "Most Volatile"
    } for i, r in enumerate(results)]
    
    return {
        "count": len(stocks),
        "stocks": stocks,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }


@app.get("/api/market/heatmap")
async def get_heatmap():
    """
    Sector heatmap data - like Finviz S&P 500 Map
    
    Returns stocks organized by sector with performance data
    for building a treemap/heatmap visualization
    """
    sectors = scanner_db.get_heatmap_data(limit_per_sector=30)
    sector_performance = scanner_db.get_sector_performance()
    
    return {
        "sectors": sectors,
        "sectorSummary": sector_performance,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }


@app.get("/api/market/sectors")
async def get_sectors_performance():
    """
    Sector performance summary
    
    Returns average change, stock count, and volume for each sector
    """
    sectors = scanner_db.get_sector_performance()
    
    return {
        "sectors": sectors,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }


@app.get("/api/market/breadth")
async def get_market_breadth():
    """
    Market breadth indicators
    
    Returns:
    - Advancing vs declining stocks
    - New highs vs new lows
    - Advance/decline ratio
    """
    breadth = scanner_db.get_market_breadth()
    sma = scanner_db.get_above_below_sma()
    
    return {
        **breadth,
        "sma_analysis": sma,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }


@app.get("/api/market/headlines")
async def get_top_headlines(
    limit: int = Query(20, ge=1, le=50),
    force_refresh: bool = Query(False, description="Force refresh cache")
):
    """
    Top market headlines - aggregated from major indices
    
    Returns the most important/recent market news headlines.
    Cached for 1 hour to reduce API calls.
    """
    with _headlines_cache["lock"]:
        # Check cache
        cache_valid = (
            not force_refresh and
            _headlines_cache["data"] is not None and
            _headlines_cache["timestamp"] is not None and
            (datetime.now(timezone.utc) - _headlines_cache["timestamp"]).total_seconds() < (_headlines_cache["cache_minutes"] * 60)
        )
        
        if cache_valid:
            # Return cached data with updated "age" times
            cached = _headlines_cache["data"].copy()
            # Update age strings for freshness
            for headline in cached.get("headlines", []):
                if "published" in headline:
                    try:
                        pub_time = datetime.fromisoformat(headline["published"].replace("Z", "+00:00"))
                        headline["age"] = _get_time_ago(pub_time)
                    except:
                        pass
            cached["from_cache"] = True
            cached["cache_expires_at"] = (_headlines_cache["timestamp"] + timedelta(minutes=_headlines_cache["cache_minutes"])).isoformat()
            return cached
    
    # Fetch fresh data
    spy_news = news_service.get_news("SPY", limit=limit)
    qqq_news = news_service.get_news("QQQ", limit=limit // 2)
    dia_news = news_service.get_news("DIA", limit=limit // 2)
    
    all_articles = []
    
    if spy_news:
        all_articles.extend(spy_news.articles)
    if qqq_news:
        all_articles.extend(qqq_news.articles)
    if dia_news:
        all_articles.extend(dia_news.articles)
    
    # Deduplicate and sort by date
    seen_titles = set()
    unique_articles = []
    for article in sorted(all_articles, key=lambda x: x.published_at, reverse=True):
        # Simple dedup by checking if title is similar
        title_key = article.title.lower()[:50]
        if title_key not in seen_titles:
            seen_titles.add(title_key)
            unique_articles.append(article)
    
    # Format headlines
    headlines = [{
        "id": i + 1,
        "title": article.title,
        "source": article.source,
        "url": article.url,
        "published": article.published_at.isoformat(),
        "sentiment": article.sentiment,
        "age": _get_time_ago(article.published_at),
    } for i, article in enumerate(unique_articles[:limit])]
    
    # Overall market sentiment
    sentiments = [a.sentiment for a in unique_articles[:limit]]
    pos = sentiments.count("positive")
    neg = sentiments.count("negative")
    overall = "bullish" if pos > neg * 1.5 else "bearish" if neg > pos * 1.5 else "neutral"
    
    now = datetime.now(timezone.utc)
    result = {
        "headlines": headlines,
        "count": len(headlines),
        "marketSentiment": overall,
        "sentimentBreakdown": {
            "positive": pos,
            "negative": neg,
            "neutral": len(sentiments) - pos - neg
        },
        "updated_at": now.isoformat(),
        "from_cache": False,
        "cache_expires_at": (now + timedelta(minutes=_headlines_cache["cache_minutes"])).isoformat()
    }
    
    # Cache if we got results
    if headlines:
        with _headlines_cache["lock"]:
            _headlines_cache["data"] = result
            _headlines_cache["timestamp"] = now
    
    return result


def _get_time_ago(dt: datetime) -> str:
    """Convert datetime to human-readable 'time ago' string"""
    now = datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    diff = now - dt
    seconds = diff.total_seconds()
    
    if seconds < 60:
        return "just now"
    elif seconds < 3600:
        mins = int(seconds // 60)
        return f"{mins}m ago"
    elif seconds < 86400:
        hours = int(seconds // 3600)
        return f"{hours}h ago"
    else:
        days = int(seconds // 86400)
        return f"{days}d ago"


@app.get("/api/market/new-highs")
async def get_new_highs(
    limit: int = Query(50, ge=1, le=200),
    market_cap: str = Query(None, description="Market cap category filter")
):
    """Stocks at or near 52-week highs"""
    results = scanner_db.get_near_52w_high(max_distance=2.0, limit=limit, market_cap_category=market_cap)
    
    stocks = [{
        "rank": i + 1,
        "ticker": r["symbol"],
        "company": r["company_name"],
        "last": r["price"],
        "change": r["change_percent"],
        "high52w": r["week_52_high"],
        "distanceFromHigh": r["distance_from_52w_high"],
        "volume": r["volume"],
        "sector": r["sector"],
        "signal": "New High" if r["distance_from_52w_high"] and r["distance_from_52w_high"] >= -1 else "Near High"
    } for i, r in enumerate(results)]
    
    return {
        "count": len(stocks),
        "stocks": stocks,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }


@app.get("/api/market/new-lows")
async def get_new_lows(
    limit: int = Query(50, ge=1, le=200),
    market_cap: str = Query(None, description="Market cap category filter")
):
    """Stocks at or near 52-week lows"""
    results = scanner_db.get_near_52w_low(max_distance=5.0, limit=limit, market_cap_category=market_cap)
    
    stocks = [{
        "rank": i + 1,
        "ticker": r["symbol"],
        "company": r["company_name"],
        "last": r["price"],
        "change": r["change_percent"],
        "low52w": r["week_52_low"],
        "distanceFromLow": r["distance_from_52w_low"],
        "volume": r["volume"],
        "sector": r["sector"],
        "signal": "New Low" if r["distance_from_52w_low"] and r["distance_from_52w_low"] <= 1 else "Near Low"
    } for i, r in enumerate(results)]
    
    return {
        "count": len(stocks),
        "stocks": stocks,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }


@app.get("/api/market/unusual-volume")
async def get_unusual_volume(
    limit: int = Query(50, ge=1, le=200),
    min_rvol: float = Query(2.0, description="Minimum relative volume multiplier"),
    market_cap: str = Query(None, description="Market cap category filter")
):
    """Stocks with unusual trading volume"""
    results = scanner_db.get_unusual_volume(
        min_rvol=min_rvol,
        limit=limit,
        market_cap_category=market_cap
    )
    
    stocks = [{
        "rank": i + 1,
        "ticker": r["symbol"],
        "company": r["company_name"],
        "last": r["price"],
        "change": r["change_percent"],
        "volume": r["volume"],
        "avgVolume": r["avg_volume_20d"],
        "relativeVolume": r["relative_volume"],
        "sector": r["sector"],
        "signal": "Unusual Volume"
    } for i, r in enumerate(results)]
    
    return {
        "count": len(stocks),
        "stocks": stocks,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }


# ═══════════════════════════════════════════════════════════════
# MARKET PULSE (AI-Generated Headlines)
# ═══════════════════════════════════════════════════════════════

@app.get("/api/market/pulse")
async def get_market_pulse(
    force_refresh: bool = Query(False, description="Force regenerate even if cached")
):
    """
    🎯 AI-Generated Market Pulse - "What's happening today"
    
    Returns bite-sized, Kimi-generated financial updates across 6 categories:
    - **Markets** - Major indices (S&P, NASDAQ, Dow)
    - **Crypto** - Bitcoin, Ethereum
    - **Economy** - Fed, rates, treasury yields
    - **Earnings** - Notable earnings reports
    - **Tech** - Big tech moves
    - **Commodities** - Gold, Oil
    
    Headlines are AI-generated using real-time market data and cached for 15 minutes.
    
    **Example Response:**
    ```json
    {
      "updates": [
        {"category": "Markets", "headline": "S&P 500 rallies 1.2% on tech strength", "sentiment": "positive"},
        {"category": "Crypto", "headline": "Bitcoin holds above $105K amid ETF inflows", "sentiment": "positive"}
      ]
    }
    ```
    """
    pulse = market_pulse_service.get_pulse(force_refresh=force_refresh)
    
    # Remove raw_data from response (keep it internal)
    response = {
        "generated_at": pulse["generated_at"],
        "updates": pulse["updates"],
        "cache_expires_at": pulse["cache_expires_at"],
    }
    
    return response


@app.get("/api/market/pulse/status")
async def get_pulse_cache_status():
    """
    Get cache status for market pulse
    
    Useful for frontend to know when to expect fresh data
    """
    return market_pulse_service.get_cache_status()


@app.get("/api/market/pulse/raw")
async def get_market_pulse_raw():
    """
    Get market pulse with raw underlying data
    
    Includes the raw market data used to generate headlines.
    Useful for debugging or advanced displays.
    """
    return market_pulse_service.get_pulse()


# ═══════════════════════════════════════════════════════════════
# RUN SERVER
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

