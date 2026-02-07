# api/services/kimi.py

"""
Kimi AI integration for intelligent stock analysis
Uses OpenRouter API to access Kimi model
"""

import os
import json
import requests
from typing import Optional
from datetime import datetime, timezone

from api.config import (
    OPENROUTER_API_KEY, 
    OPENROUTER_BASE_URL, 
    KIMI_MODEL,
    OPENROUTER_APP_NAME,
    OPENROUTER_APP_URL,
)
from api.models.stock import (
    AIAnalysis, StockQuote, TechnicalIndicators, 
    OptionsData, NewsSummary, Fundamentals
)


class KimiService:
    """Service for AI-powered analysis using Kimi via OpenRouter"""
    
    def __init__(self):
        self.api_key = OPENROUTER_API_KEY or os.getenv("OPENROUTER_API_KEY")
        self.api_base = OPENROUTER_BASE_URL
        self.model = KIMI_MODEL
    
    def analyze(
        self,
        symbol: str,
        quote: StockQuote,
        technicals: TechnicalIndicators,
        options: Optional[OptionsData] = None,
        news: Optional[NewsSummary] = None,
        fundamentals: Optional[Fundamentals] = None,
    ) -> Optional[dict]:
        """
        Generate AI analysis using first-principles thinking
        
        Returns comprehensive analysis with:
        - Summary and investment thesis
        - First principles breakdown
        - Bullish/Bearish/Neutral sentiment with confidence
        - Key points with source citations [1], [2], etc.
        - News analysis with sources
        - Catalysts with timeframes
        - Risks with probability and mitigation
        - Price projections (bull/base/bear case)
        - Support/resistance levels
        - Actionable recommendation
        """
        if not self.api_key:
            return self._generate_fallback_analysis(
                symbol, quote, technicals, options, news, fundamentals
            )
        
        # Build context for Kimi
        context = self._build_context(
            symbol, quote, technicals, options, news, fundamentals
        )
        
        # Build prompt
        prompt = self._build_prompt(symbol, context)
        
        try:
            # Call Kimi API
            response = self._call_kimi(prompt)
            
            if response:
                parsed = self._parse_response(response)
                if parsed:
                    # Add source reference list from news
                    if news and news.articles:
                        parsed["source_references"] = [
                            {
                                "num": i + 1,
                                "source": article.source,
                                "title": article.title,
                                "url": article.url,
                                "date": article.published_at.strftime("%Y-%m-%d"),
                            }
                            for i, article in enumerate(news.articles[:10])
                        ]
                    return parsed
            
            return self._generate_fallback_analysis(
                symbol, quote, technicals, options, news, fundamentals
            )
                
        except Exception as e:
            print(f"Error calling Kimi API: {e}")
            return self._generate_fallback_analysis(
                symbol, quote, technicals, options, news, fundamentals
            )
    
    def _build_context(
        self,
        symbol: str,
        quote: StockQuote,
        technicals: TechnicalIndicators,
        options: Optional[OptionsData],
        news: Optional[NewsSummary],
        fundamentals: Optional[Fundamentals],
    ) -> dict:
        """Build structured context for AI analysis with cited sources"""
        
        context = {
            "symbol": symbol,
            "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
            "price_data": {
                "current": quote.price,
                "change_today": quote.change,
                "change_percent": f"{quote.change_percent:+.2f}%",
                "volume": f"{quote.volume:,}",
                "open": quote.open,
                "high": quote.high,
                "low": quote.low,
            },
            "technical_analysis": {
                "overall_trend": technicals.overall_trend,
                "momentum": {
                    "rsi": round(technicals.momentum.rsi, 1) if technicals.momentum.rsi else None,
                    "rsi_interpretation": technicals.momentum.rsi_signal,
                    "macd_trend": technicals.momentum.macd_trend,
                    "macd_value": round(technicals.momentum.macd, 4) if technicals.momentum.macd else None,
                },
                "moving_averages": {
                    "sma_20": round(technicals.moving_averages.sma_20, 2) if technicals.moving_averages.sma_20 else None,
                    "sma_50": round(technicals.moving_averages.sma_50, 2) if technicals.moving_averages.sma_50 else None,
                    "sma_200": round(technicals.moving_averages.sma_200, 2) if technicals.moving_averages.sma_200 else None,
                    "price_vs_sma20": technicals.moving_averages.price_vs_sma_20,
                    "price_vs_sma50": technicals.moving_averages.price_vs_sma_50,
                    "price_vs_sma200": technicals.moving_averages.price_vs_sma_200,
                    "golden_cross": technicals.moving_averages.golden_cross,
                    "death_cross": technicals.moving_averages.death_cross,
                },
                "volatility": {

                    "bollinger_position": technicals.volatility.price_position,
                    "bollinger_upper": round(technicals.volatility.bollinger_upper, 2) if technicals.volatility.bollinger_upper else None,
                    "bollinger_lower": round(technicals.volatility.bollinger_lower, 2) if technicals.volatility.bollinger_lower else None,
                    "bollinger_width": technicals.volatility.bollinger_width,
                    "atr_percent": f"{technicals.volatility.atr_percent:.1f}%" if technicals.volatility.atr_percent else None,
                },
                "volume_analysis": {
                    "is_unusual": technicals.volume.is_unusual,
                    "volume_ratio": round(technicals.volume.volume_ratio, 2) if technicals.volume.volume_ratio else None,
                    "trend": technicals.volume.volume_trend,
                },
                "key_levels": {
                    "all_time_high": technicals.price_levels.ath,
                    "all_time_low": technicals.price_levels.atl,
                    "52_week_high": technicals.price_levels.week_52_high,
                    "52_week_low": technicals.price_levels.week_52_low,
                    "distance_from_ath": f"{technicals.price_levels.distance_from_ath:.1f}%" if technicals.price_levels.distance_from_ath else None,
                    "distance_from_52w_high": f"{technicals.price_levels.distance_from_52w_high:.1f}%" if technicals.price_levels.distance_from_52w_high else None,
                },
            },
        }
        
        if options:
            context["options_flow"] = {
                "put_call_ratio": round(options.put_call_ratio, 2) if options.put_call_ratio else None,
                "interpretation": "bullish" if options.put_call_ratio and options.put_call_ratio < 0.7 else "bearish" if options.put_call_ratio and options.put_call_ratio > 1.3 else "neutral",
                "total_call_volume": f"{options.total_call_volume:,}",
                "total_put_volume": f"{options.total_put_volume:,}",
                "max_pain_strike": options.max_pain,
                "unusual_activity": [
                    {
                        "type": u["type"],
                        "strike": u["strike"],
                        "expiration": u["expiration"],
                        "volume": f"{u['volume']:,}",
                        "volume_oi_ratio": u["volume_oi_ratio"],
                    }
                    for u in options.unusual_activity[:5]
                ],
            }
        
        # News with citation numbers for sourcing
        if news and news.articles:
            context["news_with_sources"] = {
                "overall_sentiment": news.overall_sentiment,
                "key_catalysts": news.key_catalysts,
                "earnings_date": news.earnings_date,
                "articles": [
                    {
                        "citation_number": i + 1,
                        "headline": article.title,
                        "source": article.source,
                        "url": article.url,
                        "published": article.published_at.strftime("%Y-%m-%d %H:%M UTC"),
                        "sentiment": article.sentiment,
                    }
                    for i, article in enumerate(news.articles[:10])
                ],
                "source_list": [
                    f"[{i+1}] {article.source}: {article.title[:60]}..."
                    for i, article in enumerate(news.articles[:10])
                ],
            }
        
        if fundamentals:
            context["fundamentals"] = {
                "market_cap": fundamentals.market_cap_formatted,
                "pe_ratio": round(fundamentals.pe_ratio, 1) if fundamentals.pe_ratio else None,
                "forward_pe": round(fundamentals.forward_pe, 1) if fundamentals.forward_pe else None,
                "eps": fundamentals.eps,
                "sector": fundamentals.sector,
                "industry": fundamentals.industry,
                "dividend_yield": f"{fundamentals.dividend_yield*100:.2f}%" if fundamentals.dividend_yield else None,
                "short_percent_of_float": f"{fundamentals.short_percent*100:.1f}%" if fundamentals.short_percent else None,
            }
        
        return context
    
    def _build_prompt(self, symbol: str, context: dict) -> str:
        """Build prompt for Kimi analysis with first-principles thinking"""
        
        return f"""You are an elite investment analyst combining Warren Buffett's value principles, Ray Dalio's systematic approach, and quantitative analysis. Analyze {symbol} using FIRST PRINCIPLES THINKING.

## YOUR ANALYSIS FRAMEWORK

### 1. FIRST PRINCIPLES (Break down to fundamentals)
- What is this company's core value proposition?
- What are the unit economics?
- Is this a durable competitive advantage (moat)?
- What would have to be true for this investment to succeed?

### 2. INTELLIGENT INVESTING PRINCIPLES
- Margin of Safety: Is there a buffer if things go wrong?
- Circle of Competence: What do we know vs. assume?
- Mr. Market: Is the market being rational or emotional?
- Long-term Value: What's the intrinsic value trajectory?

### 3. QUANTITATIVE EVIDENCE
Use the data provided to support your thesis with SPECIFIC NUMBERS.

## DATA PROVIDED:
{json.dumps(context, indent=2, default=str)}

## REQUIRED OUTPUT FORMAT (JSON):
{{
    "summary": "2-3 sentence thesis statement synthesizing the data",
    "sentiment": "bullish" or "bearish" or "neutral",
    "confidence": 0-100,
    "thesis": "One clear sentence: The core investment thesis",
    "first_principles_analysis": {{
        "core_question": "The fundamental question this trade answers",
        "key_assumptions": ["assumption 1", "assumption 2"],
        "what_must_be_true": ["condition 1 for success", "condition 2"]
    }},
    "key_points": [
        "[1] Point with citation if from news",
        "[2] Point referencing specific data",
        "Point 3"
    ],
    "news_analysis": {{
        "summary": "What the news tells us",
        "cited_sources": [1, 2, 3],
        "sentiment_driver": "What's driving news sentiment"
    }},
    "catalysts": [
        {{"event": "catalyst name", "timeframe": "when", "impact": "high/medium/low"}},
    ],
    "risks": [
        {{"risk": "risk description", "probability": "high/medium/low", "mitigation": "how to manage"}}
    ],
    "projections": {{
        "bull_case": {{"price": number, "thesis": "why"}},
        "base_case": {{"price": number, "thesis": "why"}},
        "bear_case": {{"price": number, "thesis": "why"}},
        "timeframe": "3-6 months"
    }},
    "support_level": price number,
    "resistance_level": price number,
    "recommendation": "Specific actionable advice with position sizing suggestion",
    "sources_used": [1, 2, 3]
}}

## CRITICAL RULES:
1. CITE NEWS SOURCES using [1], [2], etc. when referencing news
2. Use SPECIFIC NUMBERS from the data (prices, percentages, volumes)
3. Apply FIRST PRINCIPLES - don't just describe, EXPLAIN WHY
4. Consider BOTH SIDES - what could go wrong?
5. Make PROJECTIONS based on historical patterns and current data
6. Be INTELLECTUALLY HONEST about uncertainty

Respond ONLY with valid JSON."""
    
    def _call_kimi(self, prompt: str) -> Optional[str]:
        """Call Kimi via OpenRouter API"""
        
        url = f"{self.api_base}/chat/completions"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": OPENROUTER_APP_URL,  # Required by OpenRouter
            "X-Title": OPENROUTER_APP_NAME,       # Shows in OpenRouter dashboard
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert financial analyst. Provide analysis in valid JSON format only."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.3,
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        
        if response.status_code != 200:
            print(f"OpenRouter API error: {response.status_code} - {response.text}")
            return None
        
        data = response.json()
        return data.get("choices", [{}])[0].get("message", {}).get("content")
    
    def _parse_response(self, response: str) -> Optional[dict]:
        """Parse Kimi response into enhanced analysis dict"""
        
        try:
            # Clean response (remove markdown code blocks if present)
            response = response.strip()
            if response.startswith("```"):
                response = response.split("```")[1]
                if response.startswith("json"):
                    response = response[4:]
            response = response.strip()
            
            data = json.loads(response)
            
            # Build enhanced response
            price_targets = None
            if data.get("support_level") or data.get("resistance_level"):
                price_targets = {
                    "support": data.get("support_level"),
                    "resistance": data.get("resistance_level"),
                }
            
            # Extract projections if available
            projections = data.get("projections")
            
            # Extract first principles analysis
            first_principles = data.get("first_principles_analysis")
            
            # Extract news analysis with sources
            news_analysis = data.get("news_analysis")
            
            # Format catalysts (handle both old and new format)
            catalysts = data.get("catalysts", [])
            if catalysts and isinstance(catalysts[0], dict):
                formatted_catalysts = [
                    f"{c.get('event', c)} ({c.get('timeframe', 'TBD')}) - {c.get('impact', 'medium')} impact"
                    for c in catalysts
                ]
            else:
                formatted_catalysts = catalysts
            
            # Format risks (handle both old and new format)
            risks = data.get("risks", [])
            if risks and isinstance(risks[0], dict):
                formatted_risks = [
                    f"{r.get('risk', r)} (prob: {r.get('probability', 'medium')})"
                    for r in risks
                ]
            else:
                formatted_risks = risks
            
            return {
                "summary": data.get("summary", "Analysis unavailable"),
                "sentiment": data.get("sentiment", "neutral"),
                "confidence": data.get("confidence", 50),
                "thesis": data.get("thesis"),
                "first_principles": first_principles,
                "key_points": data.get("key_points", []),
                "news_analysis": news_analysis,
                "catalysts": formatted_catalysts,
                "risks": formatted_risks,
                "projections": projections,
                "price_targets": price_targets,
                "recommendation": data.get("recommendation"),
                "sources_cited": data.get("sources_used", []),
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }
            
        except json.JSONDecodeError as e:
            print(f"Error parsing Kimi response: {e}")
            print(f"Raw response: {response[:500]}")
            return None
    
    def _generate_fallback_analysis(
        self,
        symbol: str,
        quote: StockQuote,
        technicals: TechnicalIndicators,
        options: Optional[OptionsData],
        news: Optional[NewsSummary],
        fundamentals: Optional[Fundamentals],
    ) -> AIAnalysis:
        """
        Generate rule-based analysis when Kimi API is unavailable
        """
        
        # Score the setup
        bullish_points = 0
        bearish_points = 0
        key_points = []
        catalysts = []
        risks = []
        
        # Technical signals
        if technicals.overall_trend == "bullish":
            bullish_points += 2
            key_points.append(f"Overall technical trend is bullish")
        elif technicals.overall_trend == "bearish":
            bearish_points += 2
            key_points.append(f"Overall technical trend is bearish")
        
        if technicals.momentum.rsi:
            if technicals.momentum.rsi_signal == "oversold":
                bullish_points += 1
                key_points.append(f"RSI oversold ({technicals.momentum.rsi:.0f})")
            elif technicals.momentum.rsi_signal == "overbought":
                bearish_points += 1
                risks.append(f"RSI overbought ({technicals.momentum.rsi:.0f})")
        
        if technicals.momentum.macd_trend == "bullish":
            bullish_points += 1
            key_points.append("MACD bullish crossover")
        elif technicals.momentum.macd_trend == "bearish":
            bearish_points += 1
            key_points.append("MACD bearish crossover")
        
        if technicals.moving_averages.golden_cross:
            bullish_points += 2
            catalysts.append("Golden cross formation")
        elif technicals.moving_averages.death_cross:
            bearish_points += 2
            risks.append("Death cross formation")
        
        if technicals.volume.is_unusual:
            key_points.append(f"Unusual volume ({technicals.volume.volume_ratio:.1f}x average)")
        
        # ATH/ATL proximity
        if technicals.price_levels.distance_from_ath:
            if technicals.price_levels.distance_from_ath > -5:
                catalysts.append(f"Near all-time high ({technicals.price_levels.distance_from_ath:.1f}%)")
        if technicals.price_levels.distance_from_atl:
            if technicals.price_levels.distance_from_atl < 10:
                risks.append(f"Near all-time low ({technicals.price_levels.distance_from_atl:.1f}% above)")
        
        # Options signals
        if options:
            if options.put_call_ratio:
                if options.put_call_ratio < 0.7:
                    bullish_points += 1
                    key_points.append(f"Low put/call ratio ({options.put_call_ratio:.2f})")
                elif options.put_call_ratio > 1.3:
                    bearish_points += 1
                    key_points.append(f"High put/call ratio ({options.put_call_ratio:.2f})")
            
            if options.unusual_activity:
                call_unusual = sum(1 for u in options.unusual_activity if u["type"] == "call")
                put_unusual = sum(1 for u in options.unusual_activity if u["type"] == "put")
                if call_unusual > put_unusual:
                    catalysts.append(f"Unusual call activity detected")
                elif put_unusual > call_unusual:
                    risks.append(f"Unusual put activity detected")
        
        # News signals
        if news:
            if news.overall_sentiment == "positive":
                bullish_points += 1
                key_points.append("Positive news sentiment")
            elif news.overall_sentiment == "negative":
                bearish_points += 1
                key_points.append("Negative news sentiment")
            
            if news.key_catalysts:
                catalysts.extend(news.key_catalysts[:3])
            
            if news.earnings_date:
                catalysts.append(f"Earnings on {news.earnings_date}")
        
        # Determine sentiment
        if bullish_points > bearish_points + 2:
            sentiment = "bullish"
            confidence = min(85, 50 + (bullish_points - bearish_points) * 10)
        elif bearish_points > bullish_points + 2:
            sentiment = "bearish"
            confidence = min(85, 50 + (bearish_points - bullish_points) * 10)
        else:
            sentiment = "neutral"
            confidence = 50
        
        # Generate summary
        price_move = "up" if quote.change_percent > 0 else "down"
        summary = f"{symbol} is trading at ${quote.price:.2f}, {price_move} {abs(quote.change_percent):.1f}% today. "
        summary += f"Technical indicators show a {technicals.overall_trend or 'mixed'} setup. "
        if options and options.put_call_ratio:
            summary += f"Options flow shows P/C ratio of {options.put_call_ratio:.2f}."
        
        # Calculate support/resistance from Bollinger Bands

        price_targets = None
        if technicals.volatility.bollinger_lower and technicals.volatility.bollinger_upper:
            price_targets = {
                "support": round(technicals.volatility.bollinger_lower, 2),
                "resistance": round(technicals.volatility.bollinger_upper, 2),
            }
        
        return AIAnalysis(
            summary=summary,
            sentiment=sentiment,
            confidence=confidence,
            key_points=key_points[:5],
            catalysts=catalysts[:3],
            risks=risks[:3],
            price_targets=price_targets,
            recommendation=f"{'Consider long positions' if sentiment == 'bullish' else 'Consider short positions' if sentiment == 'bearish' else 'Wait for clearer signals'}",
            generated_at=datetime.now(timezone.utc),
        )

