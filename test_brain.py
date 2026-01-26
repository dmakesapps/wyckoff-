
import asyncio
import logging
from api.services.bot_brain import bot_brain

# Setup logging to see output
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp_debug")

async def test_brain():
    print("--- TESTING BOT BRAIN ---")
    try:
        data = await bot_brain.get_alpha_data("AAPL")
        print("\n--- FINAL RESULT ---")
        import json
        print(json.dumps(data, indent=2))
        
        if not data.get("price_data", {}).get("current"):
            print("\n❌ FAILURE: No price data found.")
        else:
            print("\n✅ SUCCESS: Got price data!")
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(test_brain())
