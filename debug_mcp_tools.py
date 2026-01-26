
import asyncio
import logging
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp_debug")

async def list_tools():
    print("--- STARTING DEBUG ---")
    try:
        config = StdioServerParameters(command="uvx", args=["finance-tools-mcp"])
        async with stdio_client(config) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                print("--- INITIALIZED ---")
                tools = await session.list_tools()
                print(f"AVAILABLE TOOLS: {tools}")
    except Exception as e:
        print(f"ERROR: {e}")
    print("--- FINISHED DEBUG ---")

if __name__ == "__main__":
    asyncio.run(list_tools())
