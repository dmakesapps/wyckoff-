# api/services/news.py

"""
News fetching service with source tracking
Uses yfinance for news (free)
"""

import yfinance as yf
import logging
from typing import Optional
from datetime import datetime, timezone, timedelta

from api.models.stock import NewsItem, NewsSummary

logger = logging.getLogger(__name__)


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

                    # yfinance changes their structure occasionally, so we need to be flexible
                    content = item.get("content", item)  # Try nested "content" key first
                    
                    # If content is a string (old format), use the item directly
                    if isinstance(content, str):
                        content = item
                    
                    # Get title - required field
                    title = content.get("title", "") or item.get("title", "")
                    if not title:
                        continue
                    
                    # Get source/publisher (handle multiple formats)
                    source = "Unknown"
                    provider = content.get("provider", {}) or item.get("publisher", "")
                    if isinstance(provider, dict):
                        source = provider.get("displayName") or provider.get("name", "Unknown")
                    elif isinstance(provider, str):
                        source = provider
                    
                    # Get URL (handle multiple formats)
                    url = ""
                    canonical = content.get("canonicalUrl", {})
                    if isinstance(canonical, dict):
                        url = canonical.get("url", "")
                    elif isinstance(canonical, str):
                        url = canonical
                    # Fallback to direct link fields
                    if not url:
                        url = content.get("link", "") or item.get("link", "")
                    
                    # Get summary
                    summary = content.get("summary") or content.get("description") or item.get("summary", "")
                    

                    pub_time = self._parse_timestamp(content, item)
                    
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

                    logger.warning(f"Error parsing news item for {symbol}: {e}")
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
    
    def _parse_timestamp(self, content: dict, item: dict) -> datetime:
        """
        ✅ FIXED: Robust timestamp parsing with multiple format support
        
        Tries multiple timestamp fields and formats to extract the published date.
        Falls back to a "stale" date (1 week ago) rather than "now" to prevent
        old news from appearing as fresh.
        """
        # List of possible timestamp fields (in order of priority)
        timestamp_fields = [
            ("pubDate", content),
            ("displayTime", content),
            ("providerPublishTime", content),  # Unix timestamp in some versions
            ("providerPublishTime", item),
            ("pubTime", item),
            ("published", item),
        ]
        
        for field_name, source in timestamp_fields:
            timestamp_val = source.get(field_name)
            if timestamp_val:
                parsed = self._try_parse_timestamp(timestamp_val)
                if parsed:
                    return parsed
        

        # This prevents old news from appearing as brand new
        logger.debug(f"Could not parse timestamp from news item, using fallback")
        return datetime.now(timezone.utc) - timedelta(days=7)
    
    def _try_parse_timestamp(self, value) -> Optional[datetime]:
        """Try to parse a timestamp value in various formats"""
        
        # Handle Unix timestamp (integer seconds)
        if isinstance(value, (int, float)):
            try:
                return datetime.fromtimestamp(value, tz=timezone.utc)
            except (ValueError, OSError):
                pass
        
        # Handle string formats
        if isinstance(value, str):
            # Try ISO format first (most common)
            try:
                # Handle "Z" suffix
                clean_val = value.replace("Z", "+00:00")
                return datetime.fromisoformat(clean_val)
            except ValueError:
                pass
            
            # Try common date formats
            formats_to_try = [
                "%Y-%m-%dT%H:%M:%S.%f%z",
                "%Y-%m-%dT%H:%M:%S%z",
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d",
                "%a, %d %b %Y %H:%M:%S %Z",  # RFC 822
                "%a, %d %b %Y %H:%M:%S %z",
            ]
            
            for fmt in formats_to_try:
                try:
                    parsed = datetime.strptime(value, fmt)
                    # Add UTC timezone if naive
                    if parsed.tzinfo is None:
                        parsed = parsed.replace(tzinfo=timezone.utc)
                    return parsed
                except ValueError:
                    continue
        
        return None
    
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

