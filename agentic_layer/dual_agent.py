import os
import time
import json
import logging
import asyncio
import requests
from dotenv import load_dotenv
from api.services.bot_brain import bot_brain
from api.config import SCOUT_MODEL, STRATEGIST_MODEL, OPENROUTER_API_KEY as API_KEY

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("DualAgent")

# Configuration
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
# Models now imported from config

IDEAS_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "knowledge_base/ideas.json"))

class DualAgentSystem:
    def __init__(self):
        self.headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/dmakesapps/wyckoff-", # Optional
            "X-Title": "AlphaBot Dual-Agent"
        }
        os.makedirs(os.path.dirname(IDEAS_FILE), exist_ok=True)

    def save_idea(self, ticker, report):
        """Saves Kimi's report as an idea for the UI."""
        ideas = []
        if os.path.exists(IDEAS_FILE):
            try:
                with open(IDEAS_FILE, 'r') as f:
                    ideas = json.load(f)
            except:
                ideas = []
        
        # Format for UI
        new_idea = {
            "id": f"kimi_{int(time.time())}",
            "ticker": ticker,
            "title": f"The Strategist: {ticker} Deep Dive",
            "notes": report,
            "createdAt": time.strftime("%Y-%m-%d"),
            "updatedAt": time.strftime("%Y-%m-%d")
        }
        
        # Insert at top
        ideas.insert(0, new_idea)
        
        # Keep last 20
        ideas = ideas[:20]
        
        with open(IDEAS_FILE, 'w') as f:
            json.dump(ideas, f, indent=2)
        logger.info(f"Report saved to {IDEAS_FILE}")

    async def query_openrouter(self, model: str, prompt: str, system_prompt: str = ""):
        """Helper to query OpenRouter cloud models."""
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
        }
        
        try:
            logger.info(f"Querying Cloud Model: {model}...")
            response = requests.post(OPENROUTER_URL, headers=self.headers, data=json.dumps(payload), timeout=120)
            response.raise_for_status()
            data = response.json()
            return data['choices'][0]['message']['content']
        except Exception as e:
            logger.error(f"Error querying {model}: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Details: {e.response.text}")
            return None

    async def run_scout(self, ticker: str):
        """The Scout: Scans data for signals."""
        logger.info(f"--- SCOUT STARTED for {ticker} ---")
        
        # 1. Fetch real market data
        data = await bot_brain.get_alpha_data(ticker)
        
        # 2. Prepare prompt for Scout
        market_summary = json.dumps(data, indent=2)
        system_prompt = "You are 'The Scout'. Continuously scan market data. Only output 'SIGNAL: [TICKER]' if you detect high-confidence bullish divergence or oversold RSI based on the numbers. Otherwise, output 'NO_SIGNAL'. Be extremely brief."
        
        prompt = f"Analyze this data for {ticker}:\n{market_summary}"
        
        response = await self.query_openrouter(SCOUT_MODEL, prompt, system_prompt)
        return response

    async def run_strategist(self, ticker: str, scout_insight: str):
        """The Strategist: Deep dive research."""
        logger.info(f"--- STRATEGIST TRIGGERED for {ticker} ---")
        
        data = await bot_brain.get_alpha_data(ticker)
        
        # COST OPTIMIZATION: Prune data before sending to expensive Thinking model
        # Remove raw objects that the model doesn't need to 'calculate' itself (Python already did)
        pruned_data = {
            "ticker": data.get("ticker"),
            "price": data.get("price_data", {}).get("current"),
            "volume": data.get("price_data", {}).get("volume"),
            "technicals": data.get("technicals"),
            "fundamentals": data.get("fundamental_summary"),
        }
        
        market_summary = json.dumps(pruned_data, indent=2)
        
        system_prompt = "You are 'The Strategist'. You have been triggered by a Scout signal. Conduct a deep mathematical risk analysis and catalyst research. Provide a deep dive report. Format with clean bullet points and clear sections."
        
        prompt = f"Ticker: {ticker}\nScout Insight: {scout_insight}\nMarket Data: {market_summary}\n\nPlease provide a comprehensive research report and trading plan."
        
        response = await self.query_openrouter(STRATEGIST_MODEL, prompt, system_prompt)
        return response

    async def monitor(self, tickers: list):
        """Main Loop."""
        logger.info("AlphaBot Dual-Agent System Online.")
        while True:
            for ticker in tickers:
                await self.run_scan(ticker)
            logger.info("Cycle complete. Waiting 60s...")
            await asyncio.sleep(60)

    async def run_scan(self, ticker: str) -> dict:
        """Run a one-off intelligence scan for a ticker."""
        logger.info(f"🔍 Starting Intelligence Scan for {ticker}")
        scout_result = await self.run_scout(ticker)
        
        if scout_result and "SIGNAL:" in scout_result.upper():
            logger.info(f"🚀 SIGNAL DETECTED for {ticker}: {scout_result}")
            report = await self.run_strategist(ticker, scout_result)
            self.save_idea(ticker, report)
            return {
                "symbol": ticker,
                "status": "signal",
                "scout_insight": scout_result,
                "report": report
            }
        
        return {
            "symbol": ticker,
            "status": "no_signal",
            "scout_insight": scout_result
        }

if __name__ == "__main__":
    system = DualAgentSystem()
    # Initial scan list
    asyncio.run(system.monitor(["NVDA", "TSLA", "AAPL"]))
