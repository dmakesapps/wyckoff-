# MISSION: AlphaBot Dual-Agent Trading System

## Role & Goal
You are an expert FinTech Engineer building a Stock Alpha bot for a MacBook Air environment. The goal is a two-step "Scout and Strategist" system using OpenRouter.

## Stack Requirements
- **Language:** Python 3.12+
- **Primary API:** OpenRouter (OpenAI-compatible SDK)
- **Library:** `openai`, `python-dotenv`, `requests`
- **Hardware Target:** MacBook Air (Minimize local overhead, use Cloud models)

## Logic Flow (The Dual-Agent System)
1. **The Scout (MiniMax M2.1):** - Model Slug: `minimax/minimax-m2.1`
   - Task: Continuously scan the user's trading API.
   - Filter: Only output `SIGNAL: [TICKER]` if high-confidence bullish divergence or oversold RSI is detected. Otherwise, output `NO_SIGNAL`.

2. **The Strategist (Kimi K2 Thinking):**
   - Model Slug: `moonshotai/kimi-k2-thinking`
   - Task: Triggered ONLY if the Scout outputs a signal.
   - Deep Dive: Conduct mathematical risk analysis and catalyst research.

## Specific Directives
- **Zero-Coding User:** Write highly commented, robust code. Use `try-except` blocks for all API calls.
- **Environment Variables:** Store the OpenRouter API Key in a `.env` file. Do NOT hardcode it.
- **Cost Efficiency:** Instruct the Scout (MiniMax) to be extremely brief to save on output tokens.
- **Tool Use:** If Antigravity needs to test the API connection, use the terminal to run `curl` commands before writing the full Python script.

## Verification Checklist (Artifacts)
- [ ] Verify OpenRouter connection via a small test script.
- [ ] Validate that the Scout correctly filters noise.
- [ ] Record a browser session of the bot printing a mock "Kimi Research Report"
