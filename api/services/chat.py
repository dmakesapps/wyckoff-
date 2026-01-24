# api/services/chat.py

"""
Chat service with streaming and tool calling
Enables Kimi to call Python analysis tools during conversation
"""

import os
import json
import requests
from typing import Generator, Optional, Any
from datetime import datetime, timezone

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
You have access to real-time tools to fetch:
- Stock prices and quotes
- Technical analysis (SMA, RSI, MACD, Bollinger Bands)
- Options flow and unusual activity
- News with sentiment analysis
- Volume metrics and alpha signals

## How to Respond
1. **Use your tools** - When users ask about stocks, ALWAYS fetch real data first
2. **Cite sources** - Reference news articles with [1], [2] when discussing catalysts
3. **Be specific** - Use actual numbers, prices, and percentages
4. **First principles** - Explain the WHY, not just the WHAT
5. **Risk aware** - Always mention risks and what could go wrong

## Response Format
- Start with the key insight/answer
- Support with data from your tools
- End with actionable recommendation or key levels to watch
- Keep responses concise but informative

## Example
User: "Why is NVDA up today?"
You: [Call get_stock_analysis("NVDA") and get_stock_news("NVDA")]
Then synthesize: "NVDA is up 3.2% to $485 on strong volume (1.5x average)..."

Remember: You're talking to traders who want actionable insights, not generic advice."""


class ChatService:
    """Service for streaming chat with tool calling"""
    
    def __init__(self, tool_executor=None):
        self.api_key = OPENROUTER_API_KEY or os.getenv("OPENROUTER_API_KEY")
        self.api_base = OPENROUTER_BASE_URL
        self.model = KIMI_MODEL
        self.tool_executor = tool_executor
    
    def chat_stream(
        self,
        messages: list[dict],
        use_tools: bool = True,
    ) -> Generator[dict, None, None]:
        """
        Stream chat response with tool calling support
        
        Yields chunks in format:
        {"type": "text", "content": "..."}
        {"type": "tool_call", "name": "...", "arguments": {...}}
        {"type": "tool_result", "name": "...", "result": {...}}
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
            
            for chunk in self._parse_stream(response):
                if chunk.get("type") == "content":
                    full_response += chunk["content"]
                    yield {"type": "text", "content": chunk["content"]}
                    
                elif chunk.get("type") == "tool_call":
                    tool_calls.append(chunk)
                    yield {"type": "tool_call", "name": chunk["name"], "arguments": chunk["arguments"]}
            
            # Execute tool calls if any
            if tool_calls and self.tool_executor:
                for tool_call in tool_calls:
                    tool_name = tool_call["name"]
                    tool_args = tool_call["arguments"]
                    
                    # Execute the tool
                    try:
                        result = self.tool_executor(tool_name, tool_args)
                        yield {"type": "tool_result", "name": tool_name, "result": result}
                        
                        # Add tool result to messages and continue conversation
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
                        yield {"type": "error", "content": f"Tool error: {str(e)}"}
                
                # Continue conversation with tool results
                response = self._call_api(full_messages, stream=True, tools=None)
                
                for chunk in self._parse_stream(response):
                    if chunk.get("type") == "content":
                        full_response += chunk["content"]
                        yield {"type": "text", "content": chunk["content"]}
            
            yield {"type": "done", "content": full_response}
            
        except Exception as e:
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
        """Parse SSE stream from OpenRouter"""
        
        for line in response.iter_lines():
            if not line:
                continue
                
            line = line.decode("utf-8")
            
            if line.startswith("data: "):
                data = line[6:]
                
                if data == "[DONE]":
                    break
                
                try:
                    chunk = json.loads(data)
                    delta = chunk.get("choices", [{}])[0].get("delta", {})
                    
                    # Text content
                    if delta.get("content"):
                        yield {"type": "content", "content": delta["content"]}
                    
                    # Tool calls
                    if delta.get("tool_calls"):
                        for tool_call in delta["tool_calls"]:
                            if tool_call.get("function"):
                                yield {
                                    "type": "tool_call",
                                    "id": tool_call.get("id"),
                                    "name": tool_call["function"].get("name"),
                                    "arguments": json.loads(tool_call["function"].get("arguments", "{}"))
                                }
                                
                except json.JSONDecodeError:
                    continue

