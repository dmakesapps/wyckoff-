# Alpha Bot API Integration Overview

## 1. System Architecture
The integration is designed to bridge the user-facing React application with a robust backend powered by Python and the Kimi LLM.

**Core Flow:**
`React Frontend ↔ Backend Proxy/Router ↔ (Kimi Agent + Python Data Engine)`

### Frontend (React + TypeScript)
- **Role:** User interface for chatting, visualization, and portfolio management.
- **Key Integration Points:**
  - `ChatContainer.tsx`: Handles message history and streaming responses.
  - `positions` & `news` pages: Will fetch real-time data instead of using placeholders.
  - **State Management:** Local component state (eventually moving to TanStack Query for data fetching).

### Backend (Python)
- **Role:** The "Brain" and "Muscle" of the operation.
- **Kimi LLM Agent:**
  - Conversational AI capable of complex reasoning.
  - Generates "informed insights" and synthesizes news.
- **Python Data Engine:**
  - `yfinance` / `pandas`: For scraping and analyzing stock prices.
  - Web scraping tools for breaking news.
  - Statistical modules for portfolio metrics.

---

## 2. API Specifications (Proposed)

### A. Chat Endpoint
**`POST /api/chat`**
- **Input:**
  ```json
  {
    "messages": [
      {"role": "user", "content": "Why is NVDA up today?"},
      {"role": "assistant", "content": "..."}
    ],
    "model": "kimi-latest"
  }
  ```
- **Output (Streamed):**
  - Text chunks (SSE) for the chat interface.
  - **Tool Calls:** If Kimi needs data, it requests the Python script to run analysis.

### B. Data Endpoints
**`GET /api/positions`**
- Returns the user's current portfolio with live prices.
- Source: Python Data Engine scripts.

**`GET /api/market/news`**
- Returns breaking news with sentiment analysis.
- Source: Kimi sentiment analysis on scraped Python data.

---

## 3. Implementation Workflow

### Phase 1: Connection Setup
1.  **API Key Management:** Securely storing the Kimi API key (`.env`).
2.  **Proxy Creation:** Setting up a simple FastAPI or Flask server to handle requests from React and forward them to Kimi/Python scripts to avoid exposing keys on the client.

### Phase 2: React Data Hooks
1.  Create `useChat` hook to manage the API communication.
2.  Replace the `setTimeout` in `ChatContainer` with `fetch('/api/chat')`.

### Phase 3: "Tool Use" Integration
1.  Enable Kimi to "call" the Python scripts.
2.  *Example:* User asks "Analyze TSLA". Kimi triggers `get_stock_analysis("TSLA")` in Python, gets the JSON result, and summarizes it for the user.

---

## 4. Key Considerations
- **Latency:** Real-time financial data needs to be fast. We should cache expensive Python script results (e.g., Redis).
- **Streaming:** Essential for the LLM chat to feel responsive.
- **Error Handling:** Graceful fallbacks if the Python scraper blocks or Kimi times out.
