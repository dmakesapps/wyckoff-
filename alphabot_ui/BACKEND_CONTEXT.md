# AlphaBot Backend Implementation Guide

This document defines the architectural and behavioral requirements for the AlphaBot backend agent. Learn this context to assist effectively.

## 1. Project Mission
We are building **AlphaBot**, a premium, institutional-grade financial AI assistant. Unlike generic chatbots, AlphaBot acts like a Wall Street analyst: it is data-driven, precise, and professional.

### Key UX Principles
- **"Show, Don't Tell"**: Users should see data loading states ("Running..."), not read "Let me look that up."
- **Premium Aesthetics**: Responses must be formatted with Markdown tables, bold headers, and clean lists. No raw JSON or XML artifacts.
- **Proactive Intelligence**: Every answer must lead to the next logical step (e.g., "Would you like to see the chart?").

---

## 2. The Streaming Protocol (Critical)

The `/api/chat` endpoint **MUST** use Server-Sent Events (SSE) to enable the "Running..." UI state.

### Event Types
Adhere strictly to this event flow:

1.  **`thinking`** (Optional but recommended)
    - **When**: Immediately after user prompt, before tool selection.
    - **Content**: "Analyzing request..." or "Identifying best tools..."
    - **Frontend Effect**: Shows pulse animation.

2.  **`tool_call`** (REQUIRED for operations)
    - **When**: The model decides to call a tool (e.g., `search_market`).
    - **Content**: `{ "name": "search_market", "arguments": { ... } }`
    - **Frontend Effect**: Displays "Running: search_market" badge.

3.  **`tool_result`**
    - **When**: The tool execution completes.
    - **Content**: `{ "name": "search_market", "result": { ... } }`
    - **Frontend Effect**: Updates badge to "Completed".

4.  **`text`**
    - **When**: The model formulates the **final answer** based on tool data.
    - **Content**: Markdown text segments.
    - **Frontend Effect**: Streams text to the chat bubble.

5.  **`done`**
    - **When**: Response is fully finished.

---

## 3. The System Prompt (Mandatory)

You **MUST** configure the AI model (Kimi/LLM) with the following System Prompt to ensure it behaves correctly.

```markdown
You are **AlphaBot**, an advanced financial AI agent designed to provide real-time market analysis.

### Core Directives
1.  **Tool-First Methodology**:
    - You generally cannot answer financial questions without data. **ALWAYS** use a tool first.
    - **SILENT EXECUTION**: Do NOT announce your plan (e.g., "Let me search for that..."). Just execute the tool. The UI handles the loading state.
    - Once you receive tool data, analyze it and answer.

2.  **Response Format**:
    - Use **Markdown Tables** for data (Symbol | Price | Change | Volume).
    - Use **Bold** for tickers (**AAPL**, **NVDA**).
    - **No raw XML/JSON**: Never leak tool tags in your final text response.

3.  **Engagement Loop**:
    - **CRITICAL**: End EVERY response with a relevant follow-up question.
    - Example: "Would you like to see the technical indicators for **NVDA**?"

4.  **Error Handling**:
    - If a tool returns no results, act like an analyst: "I didn't find exact matches for X, but I found Y. Should we look at those?"
```

---

## 4. Available Tools Overview

Ensure the backend exposes these capabilities to the LLM:

-   `search_market(filters)`: Scan for stocks by volume, sector, market cap.
-   `get_quote(symbol)`: Real-time price and change %.
-   `get_news(symbol | market)`: Latest catalysts and headlines.
-   `analyze_stock(symbol)`: Technicals (RSI, MACD, SMA).

## 5. Success Criteria for the Backend Agent
You know you have succeeded when:
1.  The User asks "Find microcap stocks".
2.  The Chat UI immediately shows "Running: search_market" (No text bubble yet).
3.  After a brief pause, a Markdown table appears with stocks.
4.  The response ends with: "Would you like to analyze any of these?"
