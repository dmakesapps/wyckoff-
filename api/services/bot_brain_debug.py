"""
AlphaBot Brain - MCP Orchestrator
Connects to local MCP servers to fetch real-time financial data.
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Configure logging
logger = logging.getLogger(__name__)

class BotBrain:
    """
    Orchestrator for fetching and merging data from MCP servers.
    """
    
    def __init__(self):
        self.market_data_config = StdioServerParameters(
            command="uvx",
            args=["finance-tools-mcp"]
        )
        self.technical_engine_config = StdioServerParameters(
            command="uvx",
            args=["maverick-mcp"]
        )

    async def get_alpha_data(self, ticker: str) -> Dict[str, Any]:
        """
        Fetches real-time price, volume, and standard indicators 
        from the configured MCP servers.
        
        Args:
            ticker: Stock symbol (e.g., "AAPL")
            
        Returns:
            Merged dictionary containing price, technicals, and fundamental data.
        """
        result = {
            "ticker": ticker.upper(),
            "price_data": {},
            "technicals": {},
            "fundamental_summary": {}
        }

        try:
            # We use AsyncExitStack to manage multiple context managers (client connections)
            async with AsyncExitStack() as stack:
                # 1. Connect to Market Data Server
                market_transport = await stack.enter_async_context(stdio_client(self.market_data_config))
                market_read, market_write = market_transport
                market_session = await stack.enter_async_context(ClientSession(market_read, market_write))
                await market_session.initialize()

                # 2. Connect to Technical Engine Server
                tech_transport = await stack.enter_async_context(stdio_client(self.technical_engine_config))
                tech_read, tech_write = tech_transport
                tech_session = await stack.enter_async_context(ClientSession(tech_read, tech_write))
                await tech_session.initialize()

                # 3. Parallel Data Fetching
                # We need to know the specific tool names exposed by these servers.
                # Assuming standard tool names or we list tools to find them.
                # For this implementation, we'll assume specific tool calls based on the plan.
                
                # Fetch Price & Volume (Market Data)
                price_task = market_session.call_tool("get_quote", arguments={"ticker": ticker})
                fundamentals_task = market_session.call_tool("get_fundamentals", arguments={"ticker": ticker})
                
                # Fetch Technicals (Technical Engine)
                technicals_task = tech_session.call_tool("get_moving_averages", arguments={"ticker": ticker, "periods": [20, 50, 200]})
                
                # Await all tasks
                price_result, fund_result, tech_result = await asyncio.gather(
                    price_task, 
                    fundamentals_task, 
                    technicals_task, 
                    return_exceptions=True
                )

                # 4. Process & Merge Results
                
                # Process Price Data
                if isinstance(price_result, Exception):
                    logger.error(f"Error fetching price: {price_result}")
                else:
                    # Parse tool output (structure depends on the specific MCP server implementation)
                    # Assuming it returns a dict content
                    data = self._parse_mcp_result(price_result)
                    result["price_data"] = {
                        "current": data.get("price", 0.0),
                        "volume": data.get("volume", 0),
                        "rel_volume": data.get("relative_volume", 0.0)
                    }

                # Process Fundamentals
                if isinstance(fund_result, Exception):
                    logger.error(f"Error fetching fundamentals: {fund_result}")
                else:
                    data = self._parse_mcp_result(fund_result)
                    result["fundamental_summary"] = {
                        "mkt_cap": data.get("market_cap", "N/A"),
                        "sector": data.get("sector", "N/A"),
                        "short_interest": data.get("short_interest", "N/A")
                    }

                # Process Technicals
                if isinstance(tech_result, Exception):
                    logger.error(f"Error fetching technicals: {tech_result}")
                else:
                    data = self._parse_mcp_result(tech_result)
                    result["technicals"] = {
                        "sma_50": data.get("sma_50", 0.0),
                        "sma_200": data.get("sma_200", 0.0),
                        "trend_status": data.get("trend", "Unknown")
                    }

        except Exception as e:
            logger.error(f"Global error in orchestration: {e}")
            result["error"] = str(e)

        return result

    def _parse_mcp_result(self, tool_result) -> Dict[str, Any]:
        """Helper to extract data from MCP tool result objects."""
        # Log the raw result for debugging
        logger.info(f"Raw MCP Result Type: {type(tool_result)}")
        logger.info(f"Raw MCP Result: {tool_result}")
        
        try:
            if hasattr(tool_result, 'content') and tool_result.content:
                text_content = tool_result.content[0].text
                import json
                parsed = json.loads(text_content)
                logger.info(f"Parsed JSON: {parsed}")
                return parsed
        except Exception as e:
            logger.error(f"Failed to parse result: {e}")
        return {}

# Singleton instance
bot_brain = BotBrain()
