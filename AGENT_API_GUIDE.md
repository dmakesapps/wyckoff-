# Alpha Discovery API Reference for LLM Agents

This API provides high-performance, structured market data from Alpaca and Yahoo Finance. 

**Base URL:** `https://wyckoff-api-no-llm.onrender.com`

## 🛠 Endpoints Reference

### 1. Stock Analysis
*   **`GET /api/analyze/{symbol}`**
    *   **Description:** Get full technical, fundamental, and sentiment data for a symbol.
    *   **Returns:** Quote, technical indicators (RSI, MACD, etc.), volume metrics, options flow summary, and recent news.
    *   **Usage:** Primary tool for evaluating a specific ticker.

### 2. Market Pulse & Sentiment
*   **`GET /api/market/pulse`**
    *   **Description:** "What is happening right now?" categorized headlines (Markets, Crypto, Economy, Tech, etc.).
    *   **Returns:** A list of curated headlines with sentiment labels.
*   **`GET /api/market/fear-greed`**
    *   **Description:** Composite market sentiment score (0-100).
    *   **Returns:** Score, label (e.g., "Extreme Fear"), and component breakdown.

### 3. Market Discovery (Scanners)
*   **`GET/POST /api/scan`**: Flexible scanner for alpha opportunities. Supports filtering by price and volume.
*   **`GET /api/market/gainers`**: Top % gainers.
*   **`GET /api/market/losers`**: Top % losers.
*   **`GET /api/market/unusual-volume`**: Stocks trading significantly higher volume than their 20-day average.
*   **`GET /api/market/new-highs`**: Stocks breaking out near 52-week highs.
*   **`GET /api/market/most-active`**: Highest volume symbols.

### 4. Charting Data
*   **`GET /api/chart/{symbol}?interval=1d&period=1y`**
    *   **Description:** Candlestick data formatted for charting (OHLCV).
    *   **Parameters:** `interval` (1m, 5m, 1h, 1d), `period` (1mo, 1y).

---

## 🤖 Direct Agent Integration Instructions
To use this as a tool for another agent:
1.  **Swagger UI:** Point the agent to `{BASE_URL}/docs`.
2.  **OpenAPI JSON:** Provide `{BASE_URL}/openapi.json` for automatic tool generation (GPT Actions, LangChain, etc.).
3.  **Authentication:** Currently public. If you add security, pass the key via `X-API-KEY` header.
