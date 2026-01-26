# api/services/chat.py

"""
Chat service with streaming and tool calling
Enables Kimi to call Python analysis tools during conversation
"""

import os
import re
import json
import requests
import logging
from typing import Generator, Optional, Any
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

from api.config import (
    OPENROUTER_API_KEY,
    OPENROUTER_BASE_URL,
    KIMI_MODEL,
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
            "description": "Get quick price quote for a stock. Use for simple price checks.",
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
            "description": "Advanced market search with multiple filters. Find stocks matching specific criteria.",
            "parameters": {
                "type": "object",
                "properties": {
                    "min_price": {
                        "type": "number",
                        "description": "Minimum stock price"
                    },
                    "max_price": {
                        "type": "number",
                        "description": "Maximum stock price"
                    },
                    "min_volume": {
                        "type": "integer",
                        "description": "Minimum trading volume"
                    },
                    "min_rvol": {
                        "type": "number",
                        "description": "Minimum relative volume"
                    },
                    "min_change": {
                        "type": "number",
                        "description": "Minimum price change %"
                    },
                    "max_change": {
                        "type": "number",
                        "description": "Maximum price change %"
                    },
                    "market_cap_category": {
                        "type": "string",
                        "description": "Market cap: 'micro', 'small', 'mid', 'large', 'mega'",
                        "enum": ["micro", "small", "mid", "large", "mega"]
                    },
                    "sector": {
                        "type": "string",
                        "description": "Sector name"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of results",
                        "default": 50
                    }
                },
                "required": []
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

SYSTEM_PROMPT = """You are Alpha, an elite AI investment analyst assistant. You combine:
- Warren Buffett's value investing principles
- Ray Dalio's systematic macro analysis  
- Quantitative technical analysis
- Real-time market data access

## Your Capabilities

### MARKET SCANNER (use for finding stocks)
You have access to a pre-scanned database of 1000+ stocks updated every 30 minutes:
- `scan_unusual_volume` - Find stocks with volume spikes (2x+ normal)
- `scan_top_movers` - Find biggest gainers/losers today
- `scan_breakout_candidates` - Find stocks near 52-week highs/lows
- `scan_by_sector` - Find stocks in specific sectors
- `search_market` - Advanced search with multiple filters
- `get_market_overview` - Get summary of market conditions

### DEEP ANALYSIS (use for specific stocks)
For detailed analysis of individual stocks:
- `get_stock_analysis` - Full technicals, options, news, AI insights
- `get_stock_quote` - Quick price check
- `get_stock_news` - Recent news with sentiment
- `get_options_flow` - Options chain and unusual activity

## How to Respond
1. **For market-wide questions** ("find unusual volume", "what's moving today") - Use SCANNER tools first
2. **For specific stocks** ("analyze AAPL", "why is TSLA up") - Use ANALYSIS tools
3. **Cite sources** - Reference news articles with [1], [2] when discussing catalysts
4. **Be specific** - Use actual numbers, prices, and percentages
5. **First principles** - Explain the WHY, not just the WHAT
6. **Risk aware** - Always mention risks and what could go wrong

## Interactive Charts

You can include interactive charts in your responses when they would help illustrate your analysis.
To include a chart, add a special chart block in your response using this exact format:

[CHART:SYMBOL:INTERVAL:PERIOD:INDICATORS]

Examples:
- [CHART:AAPL:1d:3mo:sma_20,sma_50,volume]
- [CHART:TSLA:1d:6mo:sma_20,rsi,volume]
- [CHART:NVDA:1d:1y:sma_20,sma_50,sma_200,volume]

**When to include charts:**
- When analyzing price action, trends, or technical patterns
- When discussing support/resistance levels
- When the user asks to "show", "see", or "chart" something
- When technical analysis helps explain your point

**When NOT to include charts:**
- Quick factual questions ("What's the price of AAPL?")
- Pure fundamental/news discussions without price relevance
- Market-wide overviews (unless a specific stock is the focal point)

**Available indicators:** sma_20, sma_50, sma_200, rsi, volume

## Response Format
- Start with the key insight/answer
- Include a chart when technical analysis is relevant (use [CHART:...] format)
- Support with data from your tools
- End with actionable recommendation or key levels to watch
- Keep responses concise but informative

## Examples

User: "Find microcap stocks with unusual volume"
You: [Call scan_unusual_volume(market_cap_category="micro")]
Then: "Found 15 microcaps with 2x+ volume today. Top picks: ABC (+12%, 4.5x vol), XYZ..."

User: "Analyze NVDA"
You: [Call get_stock_analysis("NVDA")]
Then: "NVDA is trading at $485, up 3.2% on strong volume...

[CHART:NVDA:1d:3mo:sma_20,sma_50,volume]

The chart shows a clear uptrend with price holding above both key moving averages..."

User: "Show me TSLA's chart with RSI"
You: "Here's TSLA with RSI indicator:

[CHART:TSLA:1d:6mo:sma_20,rsi,volume]

RSI is currently at 62, indicating moderate bullish momentum without being overbought..."

Remember: You're talking to traders who want actionable insights, not generic advice.

IMPORTANT: Use the tool_calls API to call functions. Do NOT output XML tags like <search_market> in your text response."""


class ChatService:
    """Service for streaming chat with tool calling"""
    
    def __init__(self, tool_executor=None):
        self.api_key = OPENROUTER_API_KEY or os.getenv("OPENROUTER_API_KEY")
        self.api_base = OPENROUTER_BASE_URL
        self.model = KIMI_MODEL
        self.tool_executor = tool_executor
    
    # Regex pattern to detect XML-style tool calls in text
    # Matches: <tool_name> {...json...} </tool_name>
    TOOL_TAG_PATTERN = re.compile(
        r'<(get_stock_analysis|get_stock_quote|get_stock_news|get_options_flow|get_market_news|'
        r'scan_unusual_volume|scan_top_movers|scan_breakout_candidates|scan_by_sector|search_market|get_market_overview)>'
        r'\s*(\{.*?\})\s*'
        r'</\1>',
        re.DOTALL
    )
    
    def _extract_xml_tool_calls(self, text: str) -> tuple[str, list[dict]]:
        """
        Extract XML-style tool calls from text and return cleaned text + tool calls
        
        Input: "I'll search... <search_market> {"min_price": 5} </search_market> here are results"
        Output: ("I'll search... here are results", [{"name": "search_market", "arguments": {"min_price": 5}}])
        """
        tool_calls = []
        
        # Find all matches
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
        cleaned_text = self.TOOL_TAG_PATTERN.sub('', text)
        # Clean up extra whitespace
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
        
        return cleaned_text, tool_calls
    
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
            
            for chunk in self._parse_stream(response):
                if chunk.get("type") == "content":
                    text_buffer += chunk["content"]
                    
                elif chunk.get("type") == "tool_call":
                    # Validate tool call before adding
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
                logger.info(f"[CHAT] Checking text buffer ({len(text_buffer)} chars) for XML tool calls...")
                logger.info(f"[CHAT] Buffer preview: {text_buffer[:200]}...")
                
                cleaned_text, xml_tool_calls = self._extract_xml_tool_calls(text_buffer)
                
                if xml_tool_calls:
                    # Found XML tool calls - don't stream the raw text yet
                    logger.info(f"[CHAT] ✓ Detected {len(xml_tool_calls)} XML-style tool calls - NOT streaming raw tags")
                    for tc in xml_tool_calls:
                        logger.info(f"[CHAT]   Tool: {tc['name']}, Args: {tc['arguments']}")
                    tool_calls.extend(xml_tool_calls)
                    
                    # Only keep the clean text (before tool tags) for later
                    text_before_tools = cleaned_text.split('.')[0] + '...' if cleaned_text else ""
                    if text_before_tools:
                        yield {"type": "thinking", "content": text_before_tools}
                else:
                    # No XML tool calls - stream the text normally
                    logger.info(f"[CHAT] No XML tool calls found, streaming text normally")
                    full_response = text_buffer
                    yield {"type": "text", "content": text_buffer}
            
            # Execute tool calls if any (either from API or XML)
            if tool_calls and self.tool_executor:
                # Notify frontend that we're executing tools
                for tool_call in tool_calls:
                    yield {"type": "tool_call", "name": tool_call["name"], "arguments": tool_call["arguments"]}
                
                for tool_call in tool_calls:
                    tool_name = tool_call["name"]
                    tool_args = tool_call["arguments"]
                    
                    try:
                        result = self.tool_executor(tool_name, tool_args)
                        yield {"type": "tool_result", "name": tool_name, "result": result}
                        
                        # Add tool result to messages
                        full_messages.append({
                            "role": "assistant",
                            "content": None,
                            "tool_calls": [{
                                "id": tool_call.get("id", f"call_{tool_name}"),
                                "type": "function",
                                "function": {
                                    "name": tool_name,
                                    "arguments": json.dumps(tool_args)
                                }
                            }]
                        })
                        full_messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.get("id", f"call_{tool_name}"),
                            "content": json.dumps(result, default=str)
                        })
                        
                    except Exception as e:
                        logger.error(f"Tool execution error: {e}")
                        yield {"type": "error", "content": f"Tool error: {str(e)}"}
                
                # Continue conversation with tool results - get the actual response
                response = self._call_api(full_messages, stream=True, tools=None)
                
                full_response = ""  # Reset for final response
                for chunk in self._parse_stream(response):
                    if chunk.get("type") == "content":
                        content = chunk["content"]
                        # Double-check the response for any XML tags (shouldn't happen but be safe)
                        if '<' in content and '>' in content:
                            cleaned, _ = self._extract_xml_tool_calls(content)
                            if cleaned != content:
                                content = cleaned
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

