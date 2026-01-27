# api/services/chat.py

"""
Chat service with streaming and tool calling
Enables Kimi to call Python analysis tools during conversation
"""

import os
import re
import json
import time
import requests
import logging
from typing import Generator, Optional, Any, List
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

from api.config import (
    OPENROUTER_API_KEY,
    OPENROUTER_BASE_URL,
    KIMI_MODEL,
    SCOUT_MODEL,
    OPENROUTER_APP_NAME,
    OPENROUTER_APP_URL,
)


# ═══════════════════════════════════════════════════════════════
# TOOL DEFINITIONS
# ═══════════════════════════════════════════════════════════════

AVAILABLE_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_stock_analysis",
            "description": "Get comprehensive stock analysis including price, technicals, options flow, news, and AI insights. Use this when user asks about a specific stock.",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Stock ticker symbol (e.g., AAPL, TSLA, NVDA)"
                    },
                    "include_options": {
                        "type": "boolean",
                        "description": "Include options chain analysis",
                        "default": True
                    },
                    "include_news": {
                        "type": "boolean",
                        "description": "Include recent news",
                        "default": True
                    }
                },
                "required": ["symbol"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_stock_quote",
            "description": "Get real-time price and daily change for a stock. ALWAYS use this for price checks, even for popular stocks. NEVER guess a price.",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Stock ticker symbol"
                    }
                },
                "required": ["symbol"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_stock_news",
            "description": "Get recent news for a stock with sentiment analysis and sources.",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Stock ticker symbol"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of articles to fetch",
                        "default": 10
                    }
                },
                "required": ["symbol"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_price_history",
            "description": "Get historical price and volume data for a stock. Use this when user asks for 'volume last week', 'price history', 'past month', or 'how did it trade recently'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Stock ticker symbol"
                    },
                    "period": {
                        "type": "string",
                        "description": "Time period: '1w' (1 week), '1mo' (1 month), '3mo', '6mo', '1y'",
                        "default": "1mo"
                    }
                },
                "required": ["symbol"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_options_flow",
            "description": "Get options chain data and unusual activity for a stock.",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Stock ticker symbol"
                    }
                },
                "required": ["symbol"]
            }
        }
    },
    {
        "type": "function", 
        "function": {
            "name": "get_market_news",
            "description": "Get general market news and breaking financial headlines.",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "News category: 'market', 'tech', 'earnings'",
                        "default": "market"
                    }
                },
                "required": []
            }
        }
    },
    # ═══════════════════════════════════════════════════════════════
    # MARKET SCANNER TOOLS (query pre-scanned data)
    # ═══════════════════════════════════════════════════════════════
    {
        "type": "function",
        "function": {
            "name": "scan_unusual_volume",
            "description": "Find stocks with unusual trading volume (2x+ normal). Use this to find stocks with volume spikes, potential breakouts, or unusual activity. Can filter by market cap (micro, small, mid, large, mega).",
            "parameters": {
                "type": "object",
                "properties": {
                    "min_rvol": {
                        "type": "number",
                        "description": "Minimum relative volume (e.g., 2.0 = 2x average volume)",
                        "default": 2.0
                    },
                    "market_cap_category": {
                        "type": "string",
                        "description": "Filter by market cap: 'micro', 'small', 'mid', 'large', 'mega'",
                        "enum": ["micro", "small", "mid", "large", "mega"]
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of results to return",
                        "default": 20
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "scan_top_movers",
            "description": "Find top gaining or losing stocks today. Use this to find the biggest movers in the market.",
            "parameters": {
                "type": "object",
                "properties": {
                    "direction": {
                        "type": "string",
                        "description": "'gainers' or 'losers'",
                        "enum": ["gainers", "losers"],
                        "default": "gainers"
                    },
                    "market_cap_category": {
                        "type": "string",
                        "description": "Filter by market cap: 'micro', 'small', 'mid', 'large', 'mega'",
                        "enum": ["micro", "small", "mid", "large", "mega"]
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of results to return",
                        "default": 20
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "scan_breakout_candidates",
            "description": "Find stocks near their 52-week high (potential breakouts) or 52-week low (potential value plays or falling knives).",
            "parameters": {
                "type": "object",
                "properties": {
                    "type": {
                        "type": "string",
                        "description": "'near_high' (within 5% of 52w high) or 'near_low' (within 10% of 52w low)",
                        "enum": ["near_high", "near_low"],
                        "default": "near_high"
                    },
                    "market_cap_category": {
                        "type": "string",
                        "description": "Filter by market cap: 'micro', 'small', 'mid', 'large', 'mega'",
                        "enum": ["micro", "small", "mid", "large", "mega"]
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of results to return",
                        "default": 20
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "scan_by_sector",
            "description": "Find stocks in a specific sector. Useful for sector analysis or rotation strategies.",
            "parameters": {
                "type": "object",
                "properties": {
                    "sector": {
                        "type": "string",
                        "description": "Sector name (e.g., 'Technology', 'Healthcare', 'Financial Services', 'Energy', 'Consumer Cyclical')"
                    },
                    "sort_by": {
                        "type": "string",
                        "description": "Sort by: 'change_percent', 'relative_volume', 'volume', 'market_cap'",
                        "enum": ["change_percent", "relative_volume", "volume", "market_cap"],
                        "default": "change_percent"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of results to return",
                        "default": 20
                    }
                },
                "required": ["sector"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_market",
            "description": "Search stocks by sector, price change, or market cap. Keep filters minimal for best results.",
            "parameters": {
                "type": "object",
                "properties": {
                    "sector": {
                        "type": "string",
                        "description": "Sector: 'Healthcare', 'Technology', 'Financial Services', 'Energy', 'Consumer Cyclical', 'Industrials', 'Communication Services', 'Consumer Defensive', 'Basic Materials', 'Real Estate', 'Utilities'"
                    },
                    "min_change": {
                        "type": "number",
                        "description": "Minimum price change % (use 0.5 for 'up today', -0.5 for 'down today')"
                    },
                    "market_cap_category": {
                        "type": "string",
                        "description": "Market cap: 'micro', 'small', 'mid', 'large', 'mega'",
                        "enum": ["micro", "small", "mid", "large", "mega"]
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of results (default 20)",
                        "default": 20
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_insider_transactions",
            "description": "Get recent insider trades and institutional ownership for a stock. Use this for questions about insider buying, selling, or who owns the stock.",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Stock ticker symbol"
                    }
                },
                "required": ["symbol"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_market_overview",
            "description": "Get a summary of current market conditions including counts of unusual volume stocks, big movers, breakout candidates, etc.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }
]


# ═══════════════════════════════════════════════════════════════
# SYSTEM PROMPT
# ═══════════════════════════════════════════════════════════════

SYSTEM_PROMPT = """You are **AlphaBot**, a financial AI that provides real-time market data.

## ABSOLUTE RULES (VIOLATION = FAILURE)

### RULE 1: NO PLANNING OUT LOUD
- **FORBIDDEN PHRASES** (NEVER say these):
  - "Let me search..."
  - "I'll find..."
  - "Let me look..."
  - "I need to scan..."
  - "I'll check..."
- **JUST CALL THE TOOL DIRECTLY**. No preamble. No explanation.

### RULE 2: TOOL-FIRST (NO EXCEPTIONS)
- User asks about stocks? → Call `search_market` or `scan_top_movers` IMMEDIATELY
- User asks about a price? → Call `get_stock_quote` IMMEDIATELY  
- User asks about news? → Call `get_stock_news` or `get_market_news` IMMEDIATELY
- **DO NOT** output any text before calling a tool

### RULE 3: COMPLETE RESPONSES
After receiving tool data, you MUST provide:
1. **Data Table**: Markdown format with Symbol | Price | Change | Volume
2. **1-2 sentences of insight**
3. **Follow-up question** (MANDATORY - end every response with a question)

### RULE 4: NO HALLUCINATIONS
- NEVER guess prices, volumes, or technical levels
- ALWAYS use tool data for any numbers you quote
- If `sma_20` = $25.37 in tool data, you say $25.37 (not $1.45)

### RULE 5: CHARTS
To show a chart: `[CHART:SYMBOL:1d:3mo:sma_20,volume]`
You CAN display charts. Never say you can't.

## EXAMPLES

**WRONG** (announces plan):
User: "Find biotech stocks with catalysts"
Bot: "I'll find biotech stocks with recent catalysts. Let me scan for biotech companies..."
[FAILS - announced plan instead of calling tool]

**CORRECT** (calls tool immediately):
User: "Find biotech stocks with catalysts"
Bot: [CALLS search_market with sector="Healthcare"]
[After receiving data]
"Here are biotech stocks showing momentum today:

| Ticker | Price | Change | Volume | Sector |
|--------|-------|--------|--------|--------|
| **MRNA** | $45.23 | +8.2% | 12.5M | Healthcare |
| **BNTX** | $112.45 | +5.1% | 3.2M | Healthcare |

**MRNA** is leading the sector on positive clinical trial news.

Would you like me to show the chart for any of these, or check the recent headlines?"

## AVAILABLE TOOLS
- `search_market`: Find stocks by filters (sector, price, volume, market_cap)
- `scan_top_movers`: Get gainers/losers
- `scan_unusual_volume`: Find volume spikes  
- `scan_by_sector`: Stocks in a sector
- `get_stock_quote`: Real-time price
- `get_stock_analysis`: Full analysis with technicals
- `get_stock_news`: Recent headlines
- `get_market_news`: General market news
- `get_insider_transactions`: Insider trades

## CRITICAL: FILTER USAGE
- **START BROAD**: Use minimal filters. 
- **NEVER use min_rvol** - we don't have reliable relative volume data.
- **If user says "volume"**: Sort by volume, don't filter by it.
- **If sector requested**: Just filter by sector + min_change: 0.5. That's it.
- **If "unusual volume" requested**: Use scan_unusual_volume tool OR just get top movers.
- **If 0 results**: Broaden search immediately.
"""


class ChatService:
    """Service for streaming chat with tool calling"""
    
    def __init__(self, tool_executor=None):
        self.api_key = OPENROUTER_API_KEY or os.getenv("OPENROUTER_API_KEY")
        self.api_base = OPENROUTER_BASE_URL
        self.model = SCOUT_MODEL
        self.tool_executor = tool_executor
    
    def _format_stocks_table(self, data: dict) -> str:
        """Fallback method to format stock data into a markdown table"""
        stocks = data.get("stocks", [])
        if not stocks:
            return "No stocks found matching your criteria.\n\nWould you like to try different filters?"
        
        # Build markdown table
        lines = [
            "| Ticker | Price | Change | Rel Vol | Sector |",
            "|--------|-------|--------|---------|--------|"
        ]
        
        for stock in stocks[:15]:  # Limit to 15 rows
            symbol = stock.get("symbol", "N/A")
            price = stock.get("price", 0)
            change = stock.get("change_percent", 0)
            rvol = stock.get("relative_volume", 0)
            sector = stock.get("sector", "N/A") or "N/A"
            
            change_str = f"+{change:.1f}%" if change > 0 else f"{change:.1f}%"
            rvol_str = f"{rvol:.1f}x" if rvol else "N/A"
            
            lines.append(f"| **{symbol}** | ${price:.2f} | {change_str} | {rvol_str} | {sector} |")
        
        table = "\n".join(lines)
        
        # Add summary
        count = data.get("count", len(stocks))
        table += f"\n\nFound {count} stocks matching your criteria."
        table += "\n\nWould you like more details on any of these tickers?"
        
        return table
    
    def _prune_history(self, messages: List[dict], max_messages: int = 10) -> List[dict]:
        """Prune history to avoid token bloat from large tables and news lists"""
        # Keep only the last N messages
        pruned = messages[-max_messages:] if len(messages) > max_messages else messages
        
        new_messages = []
        for msg in pruned:
            content = msg.get("content", "")
            if not isinstance(content, str):
                new_messages.append(msg)
                continue
                
            # If message contains a large markdown table, condense it
            if "| Ticker |" in content and len(content) > 500:
                # Keep first sentence/lines, replace table
                lines = content.split("\n")
                new_content = ""
                table_started = False
                for line in lines:
                    if "|" in line and "Ticker" in line:
                        if not table_started:
                            new_content += "\n[... Previous results table summarized to save memory ...]\n"
                            table_started = True
                        continue
                    if table_started and "|" in line:
                        continue
                    new_content += line + "\n"
                
                new_messages.append({**msg, "content": new_content.strip()})
            else:
                new_messages.append(msg)
        
        return new_messages

    # Regex pattern to detect XML-style tool calls in text
    # Matches: <tool_name> {...json...} </tool_name>
    TOOL_TAG_PATTERN = re.compile(
        r'<(get_stock_analysis|get_stock_quote|get_stock_news|get_options_flow|get_market_news|'
        r'scan_unusual_volume|scan_top_movers|scan_breakout_candidates|scan_by_sector|search_market|get_market_overview)>'
        r'\s*(\{.*?\})\s*'
        r'</\1>',
        re.DOTALL
    )
    
    # Pattern for Kimi's special token format:
    # <|tool_calls_section_begin|><|tool_call_begin|>tool {"count": 15, "stocks": [...]}
    KIMI_TOOL_TOKEN_PATTERN = re.compile(
        r'<\|tool_calls_section_begin\|>.*?<\|tool_call_begin\|>\s*tool\s*(\{.*)',
        re.DOTALL
    )
    
    def _extract_xml_tool_calls(self, text: str) -> tuple[str, list[dict], dict]:
        """
        Extract tool calls from text (both XML-style and Kimi token format)
        
        Returns:
            (cleaned_text, tool_calls_to_execute, embedded_data)
            
        embedded_data: If the model already included results (Kimi token format), 
                       this will contain the parsed data so we can skip execution.
        """
        tool_calls = []
        embedded_data = None
        cleaned_text = text
        
        # Check for Kimi's special token format first:
        # <|tool_calls_section_begin|><|tool_call_begin|>tool {"count": 15, "filters": {...}, "stocks": [...]}
        kimi_match = self.KIMI_TOOL_TOKEN_PATTERN.search(text)
        if kimi_match:
            json_str = kimi_match.group(1)
            logger.info(f"[CHAT] Detected Kimi token format tool output ({len(json_str)} chars)")
            
            # Try to parse the JSON - it might be incomplete or malformed
            try:
                # The JSON might not have a closing brace, try to fix it
                json_str = json_str.strip()
                if not json_str.endswith('}'):
                    # Count braces to find where to close
                    open_braces = json_str.count('{')
                    close_braces = json_str.count('}')
                    json_str += '}' * (open_braces - close_braces)
                
                parsed_data = json.loads(json_str)
                
                # Check if this contains actual data (stocks, etc) or just parameters
                if 'stocks' in parsed_data:
                    # The model already "executed" the tool and included results
                    logger.info(f"[CHAT] Found embedded results with {len(parsed_data.get('stocks', []))} stocks")
                    embedded_data = parsed_data
                else:
                    # Just parameters - need to execute
                    tool_calls.append({
                        "id": "kimi_token_call_0",
                        "name": "search_market",  # Default to search_market
                        "arguments": parsed_data.get("filters", parsed_data)
                    })
                    
            except json.JSONDecodeError as e:
                logger.warning(f"[CHAT] Failed to parse Kimi token JSON: {e}")
                # Try to extract just the stocks array if present
                stocks_match = re.search(r'"stocks"\s*:\s*(\[.*\])', json_str, re.DOTALL)
                if stocks_match:
                    try:
                        stocks = json.loads(stocks_match.group(1))
                        embedded_data = {"stocks": stocks}
                        logger.info(f"[CHAT] Extracted {len(stocks)} stocks from partial JSON")
                    except:
                        pass
            
            # Remove the Kimi token format from text
            # Find where the token section starts
            token_start = text.find('<|tool_calls_section_begin|>')
            if token_start != -1:
                cleaned_text = text[:token_start].strip()
            
            return cleaned_text, tool_calls, embedded_data
        
        # Fall back to XML-style pattern
        for match in self.TOOL_TAG_PATTERN.finditer(text):
            tool_name = match.group(1)
            json_str = match.group(2)
            
            try:
                arguments = json.loads(json_str)
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse tool arguments: {json_str[:100]}")
                arguments = {}
            
            tool_calls.append({
                "id": f"xml_call_{tool_name}_{len(tool_calls)}",
                "name": tool_name,
                "arguments": arguments
            })
        
        # Remove the tool tags from text
        cleaned_text = self.TOOL_TAG_PATTERN.sub('', cleaned_text)
        # Clean up extra whitespace
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
        
        return cleaned_text, tool_calls, embedded_data
    
    def chat_stream(
        self,
        messages: list[dict],
        use_tools: bool = True,
    ) -> Generator[dict, None, None]:
        """
        Stream chat response with tool calling support
        
        Handles both:
        1. OpenAI-style tool_calls in the API response
        2. XML-style tool tags in text content (legacy Kimi behavior)
        
        Yields chunks in format:
        {"type": "text", "content": "..."}
        {"type": "tool_call", "name": "...", "arguments": {...}}
        {"type": "tool_result", "name": "...", "result": {...}}
        {"type": "thinking", "content": "..."} - When model is processing
        {"type": "done", "content": "full response"}
        {"type": "error", "content": "error message"}
        """
        
        if not self.api_key:
            yield {"type": "error", "content": "API key not configured"}
            return
        
        # COST OPTIMIZATION: Prune history to skip old large tables
        messages = self._prune_history(messages)
        
        # Add system prompt
        full_messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            *messages
        ]
        
        try:
            # Initial request with tools
            response = self._call_api(full_messages, stream=True, tools=AVAILABLE_TOOLS if use_tools else None)
            
            full_response = ""
            tool_calls = []
            text_buffer = ""  # Buffer to accumulate text for XML tool detection
            xml_tool_calls = []  # Track XML-style tool calls separately
            has_streamed = False
            
            for chunk in self._parse_stream(response):
                if chunk.get("type") == "content":
                    content = chunk["content"]
                    text_buffer += content
                    
                    # Stream immediately if no tool tag start detected
                    if "<" not in text_buffer:
                        yield {"type": "text", "content": content}
                        has_streamed = True
                    
                elif chunk.get("type") == "tool_call":
                    tool_name = chunk.get("name")
                    tool_args = chunk.get("arguments", {})
                    
                    if not tool_name or not isinstance(tool_name, str):
                        continue
                    if not isinstance(tool_args, dict):
                        tool_args = {}
                    
                    tool_calls.append({
                        "id": chunk.get("id", f"call_{tool_name}"),
                        "name": tool_name,
                        "arguments": tool_args
                    })
            
            # Check for XML-style tool calls in accumulated text
            if text_buffer:
                logger.info(f"[CHAT] Checking text buffer ({len(text_buffer)} chars) for tool calls...")
                
                cleaned_text, extracted_xml_tools, embedded_data = self._extract_xml_tool_calls(text_buffer)
                xml_tool_calls = extracted_xml_tools  # Update the outer variable
                
                # FALLBACK: If model said "Let me search" but didn't call a tool, force it
                planning_phrases = [
                    "let me search", "let me scan", "let me find", "let me look", "let me check",
                    "i'll find", "i'll search", "i'll scan", "i'll look", "i'll check",
                    "i need to", "i will search", "i will find", "i will look"
                ]
                text_lower = text_buffer.lower()
                
                # Don't fallback for simple greetings
                is_greeting = any(g in text_lower for g in ["hello", "hi ", "hey "])
                
                logger.info(f"[CHAT] Checking for planning phrases in: '{text_lower[:100]}...'")
                
                detected_phrase = None if is_greeting else next((p for p in planning_phrases if p in text_lower), None)
                if detected_phrase and not xml_tool_calls and not embedded_data:
                    logger.warning(f"[CHAT] ⚠️ Model announced plan ('{detected_phrase}') but didn't call tool - FORCING FALLBACK")
                    
                    # Get user's original question to determine what tool to call
                    user_question = ""
                    for msg in reversed(messages):
                        if msg.get("role") == "user":
                            user_question = msg.get("content", "").lower()
                            break
                    
                    # Determine the right tool based on user question
                    forced_tool = None
                    forced_args = {}
                    
                    # Less restrictive searches - just get data, let Kimi analyze
                    if any(kw in user_question for kw in ["biotech", "healthcare", "pharma", "drug"]):
                        forced_tool = "scan_by_sector"
                        forced_args = {"sector": "Healthcare", "sort_by": "change_percent", "limit": 20}
                    elif any(kw in user_question for kw in ["tech", "software", "ai", "semiconductor"]):
                        forced_tool = "scan_by_sector"
                        forced_args = {"sector": "Technology", "sort_by": "change_percent", "limit": 20}
                    elif any(kw in user_question for kw in ["energy", "oil", "gas"]):
                        forced_tool = "scan_by_sector"
                        forced_args = {"sector": "Energy", "sort_by": "change_percent", "limit": 20}
                    elif any(kw in user_question for kw in ["finance", "bank", "financial"]):
                        forced_tool = "scan_by_sector"
                        forced_args = {"sector": "Financial Services", "sort_by": "change_percent", "limit": 20}
                    elif any(kw in user_question for kw in ["gainer", "winner", "top", "best", "hot", "return"]):
                        forced_tool = "scan_top_movers"
                        forced_args = {"direction": "gainers", "limit": 20}
                    elif any(kw in user_question for kw in ["loser", "worst", "down", "falling"]):
                        forced_tool = "scan_top_movers"
                        forced_args = {"direction": "losers", "limit": 20}
                    elif any(kw in user_question for kw in ["volume", "unusual", "spike", "active"]):
                        forced_tool = "scan_unusual_volume"
                        forced_args = {"min_rvol": 1.5, "limit": 20}
                    elif any(kw in user_question for kw in ["breakout", "high", "52"]):
                        forced_tool = "scan_breakout_candidates"
                        forced_args = {"type": "near_high", "limit": 20}
                    else:
                        # Default: top movers
                        forced_tool = "scan_top_movers"
                        forced_args = {"direction": "gainers", "limit": 20}
                    
                    if forced_tool:
                        xml_tool_calls = [{
                            "id": f"forced_{forced_tool}",
                            "name": forced_tool,
                            "arguments": forced_args
                        }]
                        logger.info(f"[CHAT] 🔧 FORCING TOOL: {forced_tool} with args: {forced_args}")
                        # Clear the text buffer so we don't show "Let me search..."
                        cleaned_text = ""
                        # Don't yield the planning text - it's useless
                        text_buffer = ""
                
                # Case 1: Model already included the data (Kimi token format with embedded results)
                if embedded_data:
                    logger.info(f"[CHAT] Found embedded data - formatting directly")
                    
                    # Yield any text before the tool output
                    if cleaned_text and not has_streamed and not cleaned_text.lower().startswith("let me"):
                        yield {"type": "text", "content": cleaned_text + "\n\n"}
                    
                    # yield {"type": "thinking", "content": "Formatting results..."}
                    
                    # LOCAL FORMATTING: Use Python to build the table instead of an expensive LLM call
                    formatted_table = self._format_stocks_table(embedded_data)
                    yield {"type": "text", "content": formatted_table}
                    yield {"type": "done", "content": ""}
                    return
                
                # Case 2: Need to execute tool calls
                if xml_tool_calls:
                    # Found XML tool calls - execute them and get results
                    logger.info(f"[CHAT] ✓ Detected {len(xml_tool_calls)} XML-style tool calls")
                    
                    # Tell frontend we're thinking
                    yield {"type": "thinking", "content": "Searching market data..."}
                    
                    # Execute all tools and collect results
                    tool_results = []
                    skip_follow_up = False
                    
                    for tc in xml_tool_calls:
                        tool_name = tc["name"]
                        tool_args = tc["arguments"]
                        logger.info(f"[CHAT] Executing tool: {tool_name}")
                        yield {"type": "tool_call", "name": tool_name, "arguments": tool_args}
                        
                        # Use existing tool execution logic (with heartbeat)
                        import queue
                        import threading
                        result_queue = queue.Queue()
                        def _run_tool():
                            try:
                                res = self.tool_executor(tool_name, tool_args)
                                result_queue.put(("success", res))
                            except Exception as e:
                                result_queue.put(("error", str(e)))
                        tool_thread = threading.Thread(target=_run_tool)
                        tool_thread.start()
                        
                        tool_result = None
                        start_wait = time.time()
                        while tool_thread.is_alive():
                            try:
                                status, val = result_queue.get(timeout=2.0)
                                if status == "success": tool_result = val
                                else: tool_result = {"error": val}
                            except queue.Empty:
                                yield {"type": "thinking", "content": f"Running {tool_name}..."}
                                if time.time() - start_wait > 30: break
                        
                        if tool_result is None and not tool_thread.is_alive():
                            try:
                                status, val = result_queue.get(block=False)
                                tool_result = val if status == "success" else {"error": val}
                            except: tool_result = {"error": "Unknown tool failure"}

                        # COST OPTIMIZATION: If the tool result already has formatted markdown, 
                        # display it immediately and skip the follow-up LLM summary.
                        if isinstance(tool_result, dict) and "formatted_markdown" in tool_result:
                            yield {"type": "text", "content": "\n\n" + tool_result["formatted_markdown"]}
                            skip_follow_up = True

                        tool_results.append({
                            "tool": tool_name,
                            "args": tool_args,
                            "result": tool_result
                        })
                        yield {"type": "tool_result", "name": tool_name, "result": tool_result}
                    
                    if skip_follow_up:
                        logger.info(f"[CHAT] 💰 Cost saved: Skipping follow-up LLM call (used local formatting)")
                        yield {"type": "done", "content": ""}
                        return
                    
                    # Now make a follow-up call with the results (only if NOT skipped)
                    # Use a SIMPLE system prompt that just asks for a summary (no tools)
                    results_summary = json.dumps(tool_results, indent=2, default=str)
                    
                    # Get the original user question
                    user_question = ""
                    for msg in reversed(messages):
                        if msg.get("role") == "user":
                            user_question = msg.get("content", "")
                            break
                    
                    # Simple follow-up prompt that won't trigger more tool calls
                    summary_system = """You are a financial analyst. Present the tool results to the user.

RULES:
1. If stocks were found: Create a Markdown table (Ticker | Price | Change | Volume | Sector)
2. If NO stocks found: Say "No exact matches found" and suggest broadening criteria
3. Add 1-2 sentences of market insight
4. End with a follow-up question

FORBIDDEN:
- Do NOT say "Let me search/check/find"
- Do NOT mention tool names like scan_unusual_volume
- Do NOT call any tools
- Do NOT use XML tags
- Just present the data you have"""
                    
                    follow_up_messages = [
                        {"role": "system", "content": summary_system},
                        {"role": "user", "content": f"User's question: {user_question}\n\nTool results (format this nicely):\n```json\n{results_summary}\n```\n\nPresent this data in a helpful, formatted response with a table if applicable."}
                    ]
                    
                    logger.info(f"[CHAT] Making follow-up API call to summarize {len(results_summary)} chars of tool results...")
                    
                    try:
                        yield {"type": "thinking", "content": "Analyzing and formatting results..."}
                        response = self._call_api(follow_up_messages, stream=True, tools=None)
                        
                        full_response = ""
                        for chunk in self._parse_stream(response):
                            if chunk.get("type") == "content":
                                content = chunk["content"]
                                # Clean any stray XML tags (shouldn't happen but be safe)
                                if '<' in content and '>' in content:
                                    content, _ = self._extract_xml_tool_calls(content)
                                full_response += content
                                yield {"type": "text", "content": content}
                        
                        logger.info(f"[CHAT] Follow-up response complete: {len(full_response)} chars")
                        
                        # If we got no response, yield an error
                        if not full_response.strip():
                            logger.error("[CHAT] Follow-up returned empty response!")
                            yield {"type": "text", "content": "\n\nI found the data but had trouble formatting it. Here's the raw result:\n\n"}
                            yield {"type": "text", "content": f"```json\n{results_summary[:2000]}\n```"}
                            
                    except Exception as e:
                        logger.error(f"[CHAT] Follow-up API call failed: {e}")
                        yield {"type": "text", "content": f"\n\nI executed the search but encountered an error formatting results: {str(e)[:100]}"}
                        yield {"type": "text", "content": f"\n\nRaw data:\n```json\n{results_summary[:1500]}\n```"}
                    
                else:
                    # No XML tool calls - stream the text normally
                    full_response = text_buffer
                    if not has_streamed:
                        yield {"type": "text", "content": text_buffer}
            
            # Handle API-style tool calls (from tool_calls in response)
            if tool_calls and self.tool_executor and not xml_tool_calls:
                logger.info(f"[CHAT] Processing {len(tool_calls)} API-style tool calls")
                
                # Execute all tools and collect results
                tool_results = []
                for tool_call in tool_calls:
                    tool_name = tool_call["name"]
                    tool_args = tool_call["arguments"]
                    
                    yield {"type": "tool_call", "name": tool_name, "arguments": tool_args}
                    
                    try:
                        result = self.tool_executor(tool_name, tool_args)
                        yield {"type": "tool_result", "name": tool_name, "result": result}
                        tool_results.append({
                            "tool": tool_name,
                            "args": tool_args,
                            "result": result
                        })
                    except Exception as e:
                        logger.error(f"Tool execution error: {e}")
                        yield {"type": "error", "content": f"Tool error: {str(e)}"}
                        tool_results.append({
                            "tool": tool_name,
                            "args": tool_args,
                            "result": {"error": str(e)}
                        })
                
                # Use summary system prompt for follow-up (prevents "Let me scan..." responses)
                results_summary = json.dumps(tool_results, indent=2, default=str)
                
                user_question = ""
                for msg in reversed(messages):
                    if msg.get("role") == "user":
                        user_question = msg.get("content", "")
                        break
                
                summary_system = """You are a financial analyst. Present the tool results to the user.

RULES:
1. If stocks were found: Create a Markdown table (Ticker | Price | Change | Volume | Sector)
2. If NO stocks found: Say "No exact matches found" and suggest broadening criteria
3. Add 1-2 sentences of market insight
4. End with a follow-up question

FORBIDDEN:
- Do NOT say "Let me search/check/find/scan"
- Do NOT mention tool names
- Do NOT call any tools
- Do NOT use XML tags
- Just present the data you have"""
                
                follow_up_messages = [
                    {"role": "system", "content": summary_system},
                    {"role": "user", "content": f"User's question: {user_question}\n\nTool results:\n```json\n{results_summary}\n```\n\nPresent this data helpfully."}
                ]
                
                logger.info(f"[CHAT] Making follow-up call with summary system prompt")
                yield {"type": "thinking", "content": "Analyzing and formatting results..."}
                response = self._call_api(follow_up_messages, stream=True, tools=None)
                
                full_response = ""
                for chunk in self._parse_stream(response):
                    if chunk.get("type") == "content":
                        content = chunk["content"]
                        full_response += content
                        yield {"type": "text", "content": content}
            
            yield {"type": "done", "content": full_response}
            
        except Exception as e:
            logger.error(f"Chat stream error: {e}")
            yield {"type": "error", "content": str(e)}
    
    def chat_sync(
        self,
        messages: list[dict],
        use_tools: bool = True,
    ) -> dict:
        """
        Non-streaming chat (for simpler integrations)
        
        Returns:
        {
            "response": "full text response",
            "tools_used": ["tool1", "tool2"],
            "sources": [...],
        }
        """
        full_response = ""
        tools_used = []
        
        for chunk in self.chat_stream(messages, use_tools):
            if chunk["type"] == "text":
                full_response += chunk["content"]
            elif chunk["type"] == "tool_call":
                tools_used.append(chunk["name"])
            elif chunk["type"] == "error":
                return {"error": chunk["content"]}
        
        return {
            "response": full_response,
            "tools_used": tools_used,
        }
    
    def _call_api(
        self, 
        messages: list[dict], 
        stream: bool = True,
        tools: Optional[list] = None,
    ) -> requests.Response:
        """Make API call to OpenRouter"""
        
        url = f"{self.api_base}/chat/completions"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": OPENROUTER_APP_URL,
            "X-Title": OPENROUTER_APP_NAME,
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": stream,
            "temperature": 0.7,
        }
        
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"
        
        response = requests.post(
            url, 
            headers=headers, 
            json=payload, 
            stream=stream,
            timeout=120
        )
        
        if response.status_code != 200:
            raise Exception(f"API error: {response.status_code} - {response.text}")
        
        return response
    
    def _parse_stream(self, response: requests.Response) -> Generator[dict, None, None]:
        """Parse SSE stream from OpenRouter
        
        Tool calls come in multiple chunks:
        - First chunk: has id and name
        - Subsequent chunks: have arguments (as partial JSON strings)
        - We accumulate and only yield when complete
        """
        
        # Accumulator for tool calls (keyed by index)
        pending_tool_calls: dict[int, dict] = {}
        
        for line in response.iter_lines():
            if not line:
                continue
                
            line = line.decode("utf-8")
            
            if line.startswith("data: "):
                data = line[6:]
                
                if data == "[DONE]":
                    # Stream ended - yield any pending complete tool calls
                    for idx in sorted(pending_tool_calls.keys()):
                        tc = pending_tool_calls[idx]
                        if tc.get("name"):  # Only yield if we have a name
                            # Try to parse accumulated arguments
                            args_str = tc.get("arguments_str", "")
                            try:
                                args = json.loads(args_str) if args_str else {}
                            except json.JSONDecodeError:
                                args = {"raw": args_str}  # Fallback
                            
                            yield {
                                "type": "tool_call",
                                "id": tc.get("id", f"call_{tc['name']}"),
                                "name": tc["name"],
                                "arguments": args
                            }
                    break
                
                try:
                    chunk = json.loads(data)
                    choices = chunk.get("choices", [])
                    if not choices:
                        continue
                        
                    delta = choices[0].get("delta", {})
                    finish_reason = choices[0].get("finish_reason")
                    
                    # Text content
                    if delta.get("content"):
                        yield {"type": "content", "content": delta["content"]}
                    
                    # Tool calls - accumulate across chunks
                    if delta.get("tool_calls"):
                        for tool_call in delta["tool_calls"]:
                            idx = tool_call.get("index", 0)
                            
                            # Initialize if new
                            if idx not in pending_tool_calls:
                                pending_tool_calls[idx] = {
                                    "id": None,
                                    "name": None,
                                    "arguments_str": ""
                                }
                            
                            # Accumulate data
                            if tool_call.get("id"):
                                pending_tool_calls[idx]["id"] = tool_call["id"]
                            
                            if tool_call.get("function"):
                                func = tool_call["function"]
                                if func.get("name"):
                                    pending_tool_calls[idx]["name"] = func["name"]
                                if func.get("arguments"):
                                    pending_tool_calls[idx]["arguments_str"] += func["arguments"]
                    
                    # If finish_reason is "tool_calls", yield the accumulated tool calls
                    if finish_reason == "tool_calls":
                        for idx in sorted(pending_tool_calls.keys()):
                            tc = pending_tool_calls[idx]
                            if tc.get("name"):
                                args_str = tc.get("arguments_str", "")
                                try:
                                    args = json.loads(args_str) if args_str else {}
                                except json.JSONDecodeError:
                                    args = {"raw": args_str}
                                
                                yield {
                                    "type": "tool_call",
                                    "id": tc.get("id", f"call_{tc['name']}"),
                                    "name": tc["name"],
                                    "arguments": args
                                }
                        # Clear after yielding
                        pending_tool_calls.clear()
                                
                except json.JSONDecodeError:
                    continue

