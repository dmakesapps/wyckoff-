# api/services/news.py

"""
News fetching service with source tracking
Uses yfinance for news (free)
"""

import yfinance as yf
from typing import Optional
from datetime import datetime, timezone, timedelta

from api.models.stock import NewsItem, NewsSummary


class NewsService:
    """Service for fetching stock news with sources"""
    
    def get_news(self, symbol: str, limit: int = 15) -> Optional[NewsSummary]:
        """
        Get recent news for a stock with full source information
        
        Args:
            symbol: Stock symbol
            limit: Maximum number of articles to return
        
        Returns:
            NewsSummary with articles, sources, and sentiment
        """
        try:
            ticker = yf.Ticker(symbol)
            
            # Get news from yfinance
            news_data = ticker.news
            
            if not news_data:
                return NewsSummary(
                    symbol=symbol.upper(),
                    articles=[],
                    overall_sentiment="neutral",
                    key_catalysts=[],
                )
            
            articles = []
            sources_seen = set()
            
            for item in news_data[:limit]:
                try:
                    # Handle new yfinance news structure (nested under 'content')
                    content = item.get("content", item)  # Fallback to item if no content key
                    
                    # Get title
                    title = content.get("title", "")
                    if not title:
                        continue
                    
                    # Get source/publisher
                    provider = content.get("provider", {})
                    source = provider.get("displayName", "Unknown") if isinstance(provider, dict) else "Unknown"
                    
                    # Get URL
                    canonical = content.get("canonicalUrl", {})
                    url = canonical.get("url", "") if isinstance(canonical, dict) else ""
                    
                    # Get summary
                    summary = content.get("summary") or content.get("description")
                    
                    # Parse timestamp
                    pub_date_str = content.get("pubDate") or content.get("displayTime")
                    if pub_date_str:
                        try:
                            pub_time = datetime.fromisoformat(pub_date_str.replace("Z", "+00:00"))
                        except:
                            pub_time = datetime.now(timezone.utc)
                    else:
                        pub_time = datetime.now(timezone.utc)
                    
                    sources_seen.add(source)
                    
                    articles.append(NewsItem(
                        title=title,
                        summary=summary,
                        source=source,
                        url=url,
                        published_at=pub_time,
                        sentiment=self._analyze_sentiment(title),
                    ))
                except Exception as e:
                    print(f"Error parsing news item: {e}")
                    continue
            
            # Determine overall sentiment with weighting (recent news weighted more)
            overall = self._calculate_overall_sentiment(articles)
            
            # Extract potential catalysts from titles
            catalysts = self._extract_catalysts(articles)
            
            # Get earnings and other key dates
            earnings_date = self._get_earnings_date(ticker)
            
            # Get additional company events if available
            key_events = self._get_key_events(ticker)
            
            return NewsSummary(
                symbol=symbol.upper(),
                articles=articles,
                overall_sentiment=overall,
                key_catalysts=catalysts + key_events,
                earnings_date=earnings_date,
            )
            
        except Exception as e:
            print(f"Error fetching news for {symbol}: {e}")
            return None
    
    def get_news_for_ai(self, symbol: str) -> dict:
        """
        Get news formatted for AI analysis with source citations
        
        Returns structured data that Kimi can use to provide sourced analysis
        """
        news = self.get_news(symbol, limit=15)
        
        if not news or not news.articles:
            return {
                "has_news": False,
                "articles": [],
                "sources": [],
                "summary": "No recent news available",
            }
        
        # Format articles with citation numbers
        formatted_articles = []
        sources = []
        
        for i, article in enumerate(news.articles):
            citation_num = i + 1
            
            # Calculate time ago
            time_ago = self._format_time_ago(article.published_at)
            
            formatted_articles.append({
                "citation": citation_num,
                "title": article.title,
                "source": article.source,
                "url": article.url,
                "time_ago": time_ago,
                "sentiment": article.sentiment,
            })
            
            sources.append({
                "num": citation_num,
                "source": article.source,
                "url": article.url,
                "title": article.title[:80] + "..." if len(article.title) > 80 else article.title,
            })
        
        return {
            "has_news": True,
            "articles": formatted_articles,
            "sources": sources,
            "overall_sentiment": news.overall_sentiment,
            "catalysts": news.key_catalysts,
            "earnings_date": news.earnings_date,
            "summary": f"{len(formatted_articles)} articles from {len(set(a['source'] for a in formatted_articles))} sources",
        }
    
    def _format_time_ago(self, dt: datetime) -> str:
        """Format datetime as 'X hours ago' or 'X days ago'"""
        now = datetime.now(timezone.utc)
        diff = now - dt
        
        hours = diff.total_seconds() / 3600
        if hours < 1:
            return "just now"
        elif hours < 24:
            return f"{int(hours)} hours ago"
        elif hours < 48:
            return "yesterday"
        else:
            days = int(hours / 24)
            return f"{days} days ago"
    
    def _analyze_sentiment(self, text: str) -> str:
        """
        Analyze sentiment of news headline
        Returns: "positive", "negative", or "neutral"
        """
        text_lower = text.lower()
        
        # Strong positive indicators
        strong_positive = [
            "surge", "soar", "jump", "rally", "record high", "all-time high",
            "beat", "exceeds", "outperform", "upgrade", "breakthrough",
            "approval", "win", "success", "growth", "profit"
        ]
        
        # Strong negative indicators
        strong_negative = [
            "crash", "plunge", "tumble", "collapse", "lawsuit", "fraud",
            "investigation", "recall", "miss", "downgrade", "warning",
            "loss", "decline", "fail", "concern", "risk", "cut"
        ]
        
        # Moderate positive
        moderate_positive = [
            "gain", "rise", "up", "higher", "improve", "positive",
            "buy", "bullish", "opportunity"
        ]
        
        # Moderate negative
        moderate_negative = [
            "drop", "fall", "down", "lower", "weak", "negative",
            "sell", "bearish", "concern"
        ]
        
        score = 0
        
        for word in strong_positive:
            if word in text_lower:
                score += 2
        for word in moderate_positive:
            if word in text_lower:
                score += 1
        for word in strong_negative:
            if word in text_lower:
                score -= 2
        for word in moderate_negative:
            if word in text_lower:
                score -= 1
        
        if score >= 2:
            return "positive"
        elif score <= -2:
            return "negative"
        return "neutral"
    
    def _calculate_overall_sentiment(self, articles: list[NewsItem]) -> str:
        """Calculate weighted sentiment (recent articles weighted more)"""
        if not articles:
            return "neutral"
        
        now = datetime.now(timezone.utc)
        weighted_score = 0
        total_weight = 0
        
        for article in articles:
            # Weight by recency (last 24h = weight 3, 24-48h = weight 2, older = weight 1)
            hours_ago = (now - article.published_at).total_seconds() / 3600
            if hours_ago < 24:
                weight = 3
            elif hours_ago < 48:
                weight = 2
            else:
                weight = 1
            
            # Score sentiment
            if article.sentiment == "positive":
                weighted_score += weight
            elif article.sentiment == "negative":
                weighted_score -= weight
            
            total_weight += weight
        
        if total_weight == 0:
            return "neutral"
        
        avg_score = weighted_score / total_weight
        
        if avg_score > 0.3:
            return "positive"
        elif avg_score < -0.3:
            return "negative"
        return "neutral"
    
    def _simple_sentiment(self, text: str) -> str:
        """
        Simple keyword-based sentiment analysis
        (This will be enhanced by Kimi AI for nuanced analysis)
        """
        text_lower = text.lower()
        
        positive_words = [
            "surge", "jump", "soar", "rally", "gain", "beat", "record", "high",
            "upgrade", "buy", "bullish", "growth", "profit", "success", "win",
            "breakthrough", "positive", "strong", "outperform", "exceed"
        ]
        
        negative_words = [
            "drop", "fall", "plunge", "crash", "loss", "miss", "low", "cut",
            "downgrade", "sell", "bearish", "decline", "warning", "concern",
            "lawsuit", "investigation", "negative", "weak", "underperform", "fail"
        ]
        
        pos_count = sum(1 for word in positive_words if word in text_lower)
        neg_count = sum(1 for word in negative_words if word in text_lower)
        
        if pos_count > neg_count:
            return "positive"
        elif neg_count > pos_count:
            return "negative"
        return "neutral"
    
    def _extract_catalysts(self, articles: list[NewsItem]) -> list[str]:
        """Extract potential catalysts from news titles"""
        catalysts = []
        
        catalyst_keywords = {
            "earnings": "Earnings report",
            "fda": "FDA news",
            "approval": "Regulatory approval",
            "merger": "M&A activity",
            "acquisition": "M&A activity",
            "buyout": "M&A activity",
            "partnership": "Partnership announcement",
            "contract": "Contract news",
            "guidance": "Guidance update",
            "upgrade": "Analyst upgrade",
            "downgrade": "Analyst downgrade",
            "lawsuit": "Legal issues",
            "ceo": "Management change",
            "dividend": "Dividend news",
            "buyback": "Share buyback",
            "split": "Stock split",
            "ipo": "IPO related",
            "sec": "SEC filing/investigation",
        }
        
        for article in articles:
            title_lower = article.title.lower()
            for keyword, catalyst in catalyst_keywords.items():
                if keyword in title_lower and catalyst not in catalysts:
                    catalysts.append(catalyst)
        
        return catalysts[:5]  # Top 5 catalysts
    
    def _get_earnings_date(self, ticker) -> Optional[str]:
        """Get next earnings date if available"""
        try:
            calendar = ticker.calendar
            if calendar is not None and "Earnings Date" in calendar:
                earnings = calendar["Earnings Date"]
                if earnings:
                    return str(earnings[0].date()) if hasattr(earnings[0], "date") else str(earnings[0])
        except Exception:
            pass
        return None
    
    def _get_key_events(self, ticker) -> list[str]:
        """Get key upcoming events from ticker calendar"""
        events = []
        try:
            calendar = ticker.calendar
            if calendar is not None:
                # Earnings
                if "Earnings Date" in calendar and calendar["Earnings Date"]:
                    events.append(f"Earnings: {calendar['Earnings Date'][0]}")
                
                # Ex-Dividend
                if "Ex-Dividend Date" in calendar and calendar["Ex-Dividend Date"]:
                    events.append(f"Ex-Dividend: {calendar['Ex-Dividend Date']}")
        except Exception:
            pass
        return events

