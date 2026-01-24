# Alpha Bot API Integration Guide for React App

## IMPORTANT: Read This First

You are integrating a Python/FastAPI backend (Alpha Discovery API) into a React/TypeScript frontend. The API provides:
- **Streaming chat** with AI (Kimi) that can call Python tools for real-time stock data
- **Portfolio positions** with live prices
- **Market news** with sentiment analysis
- **Stock analysis** with technicals, options flow, and AI insights

**API Base URL:** `http://localhost:8000/api`

---

## API Endpoints Reference

### 1. Chat (Streaming) - PRIMARY FOR CHATCONTAINER
```
POST /api/chat
Content-Type: application/json

Request:
{
  "messages": [
    {"role": "user", "content": "Why is NVDA up today?"},
    {"role": "assistant", "content": "..."} // previous messages
  ],
  "stream": true  // Set false for non-streaming
}

Response (Server-Sent Events):
data: {"type": "text", "content": "NVDA is up "}
data: {"type": "text", "content": "3.2% today "}
data: {"type": "tool_call", "name": "get_stock_analysis", "arguments": {"symbol": "NVDA"}}
data: {"type": "tool_result", "name": "get_stock_analysis", "result": {...}}
data: {"type": "text", "content": "driven by strong earnings..."}
data: {"type": "done", "content": "full response text"}
```

### 2. Positions
```
GET /api/positions

Response:
{
  "positions": [
    {
      "symbol": "AAPL",
      "company_name": "Apple Inc.",
      "shares": 100,
      "avg_cost": 150.00,
      "current_price": 185.50,
      "current_value": 18550.00,
      "gain_loss": 3550.00,
      "gain_loss_percent": 23.67,
      "day_change": 2.30,
      "day_change_percent": 1.25
    }
  ],
  "summary": {
    "total_value": 125000.00,
    "total_cost": 110000.00,
    "total_gain_loss": 15000.00,
    "total_gain_loss_percent": 13.64
  },
  "updated_at": "2024-01-24T20:00:00Z"
}
```

### 3. Market News
```
GET /api/market/news?limit=15

Response:
{
  "overall_sentiment": "positive",
  "article_count": 15,
  "articles": [
    {
      "id": 1,
      "title": "S&P 500 hits new record high...",
      "source": "Reuters",
      "url": "https://...",
      "published_at": "2024-01-24T15:30:00Z",
      "sentiment": "positive"
    }
  ],
  "fetched_at": "2024-01-24T20:00:00Z"
}
```

### 4. Stock Analysis (Full)
```
GET /api/analyze/{symbol}?include_options=true&include_news=true&include_ai=true

Response: Complete analysis with quote, technicals, alpha score, options, news, and AI analysis
```

### 5. Quick Quote
```
GET /api/quote/{symbol}

Response:
{
  "symbol": "AAPL",
  "price": 185.50,
  "change": 2.30,
  "change_percent": 1.25,
  "volume": 45000000
}
```

### 6. Stock News
```
GET /api/news/{symbol}?limit=10

Response: News articles with sentiment for specific stock
```

---

## TypeScript Types

Create file: `src/types/api.ts`

```typescript
// ═══════════════════════════════════════════════════════════════
// CHAT TYPES
// ═══════════════════════════════════════════════════════════════

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
}

export interface ChatStreamChunk {
  type: 'text' | 'tool_call' | 'tool_result' | 'done' | 'error';
  content?: string;
  name?: string;
  arguments?: Record<string, any>;
  result?: Record<string, any>;
}

export interface ChatRequest {
  messages: ChatMessage[];
  stream?: boolean;
}

export interface ChatResponse {
  response: string;
  tools_used: string[];
  error?: string;
}

// ═══════════════════════════════════════════════════════════════
// POSITION TYPES
// ═══════════════════════════════════════════════════════════════

export interface Position {
  symbol: string;
  company_name: string;
  shares: number;
  avg_cost: number;
  current_price: number;
  current_value: number;
  cost_basis: number;
  gain_loss: number;
  gain_loss_percent: number;
  day_change: number;
  day_change_percent: number;
}

export interface PositionsSummary {
  total_value: number;
  total_cost: number;
  total_gain_loss: number;
  total_gain_loss_percent: number;
}

export interface PositionsResponse {
  positions: Position[];
  summary: PositionsSummary;
  updated_at: string;
}

// ═══════════════════════════════════════════════════════════════
// NEWS TYPES
// ═══════════════════════════════════════════════════════════════

export interface NewsArticle {
  id: number;
  title: string;
  source: string;
  url: string;
  published_at: string;
  sentiment: 'positive' | 'negative' | 'neutral';
  summary?: string;
}

export interface MarketNewsResponse {
  overall_sentiment: string;
  article_count: number;
  articles: NewsArticle[];
  fetched_at: string;
}

export interface StockNewsResponse {
  symbol: string;
  overall_sentiment: string;
  earnings_date?: string;
  catalysts: string[];
  article_count: number;
  articles: NewsArticle[];
}

// ═══════════════════════════════════════════════════════════════
// QUOTE & ANALYSIS TYPES
// ═══════════════════════════════════════════════════════════════

export interface Quote {
  symbol: string;
  price: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  previous_close: number;
  change: number;
  change_percent: number;
  timestamp: string;
}

export interface AlphaSignal {
  name: string;
  type: 'bullish' | 'bearish' | 'neutral';
  strength: number;
  description: string;
}

export interface AlphaScore {
  total_score: number;
  signal_strength: 'strong' | 'moderate' | 'weak';
  overall_grade: 'A' | 'B' | 'C' | 'D' | 'F';
  bullish_signals: number;
  bearish_signals: number;
  signals: AlphaSignal[];
  summary: string;
}

export interface AIAnalysis {
  summary: string;
  sentiment: 'bullish' | 'bearish' | 'neutral';
  confidence: number;
  thesis?: string;
  key_points: string[];
  catalysts: string[];
  risks: string[];
  projections?: {
    bull_case: { price: number; thesis: string };
    base_case: { price: number; thesis: string };
    bear_case: { price: number; thesis: string };
    timeframe: string;
  };
  price_targets?: {
    support: number;
    resistance: number;
  };
  recommendation: string;
  source_references?: Array<{
    num: number;
    source: string;
    title: string;
    url: string;
  }>;
}

export interface StockAnalysis {
  symbol: string;
  company_name: string;
  quote: Quote;
  alpha_score: AlphaScore;
  ai_analysis?: AIAnalysis;
  technicals: any;
  options?: any;
  news?: any;
  fundamentals?: any;
  analyzed_at: string;
}
```

---

## API Client

Create file: `src/api/alphaApi.ts`

```typescript
import type {
  ChatMessage,
  ChatStreamChunk,
  ChatResponse,
  PositionsResponse,
  MarketNewsResponse,
  StockNewsResponse,
  Quote,
  StockAnalysis,
} from '../types/api';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

// ═══════════════════════════════════════════════════════════════
// CHAT API (STREAMING)
// ═══════════════════════════════════════════════════════════════

/**
 * Stream chat response from the API
 * 
 * @param messages - Conversation history
 * @param onChunk - Callback for each streamed chunk
 * @param onComplete - Callback when stream is complete
 * @param onError - Callback for errors
 */
export async function streamChat(
  messages: ChatMessage[],
  onChunk: (chunk: ChatStreamChunk) => void,
  onComplete: (fullResponse: string) => void,
  onError: (error: string) => void
): Promise<void> {
  try {
    const response = await fetch(`${API_BASE}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ messages, stream: true }),
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error('No response body');
    }

    const decoder = new TextDecoder();
    let fullResponse = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const text = decoder.decode(value, { stream: true });
      const lines = text.split('\n').filter(line => line.startsWith('data: '));

      for (const line of lines) {
        try {
          const data: ChatStreamChunk = JSON.parse(line.slice(6));
          
          if (data.type === 'text' && data.content) {
            fullResponse += data.content;
          }
          
          if (data.type === 'error') {
            onError(data.content || 'Unknown error');
            return;
          }
          
          onChunk(data);
          
          if (data.type === 'done') {
            onComplete(fullResponse);
            return;
          }
        } catch (e) {
          // Skip malformed chunks
        }
      }
    }

    onComplete(fullResponse);
  } catch (error) {
    onError(error instanceof Error ? error.message : 'Chat failed');
  }
}

/**
 * Non-streaming chat (simpler but no real-time updates)
 */
export async function chat(messages: ChatMessage[]): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ messages, stream: false }),
  });

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }

  return response.json();
}

// ═══════════════════════════════════════════════════════════════
// POSITIONS API
// ═══════════════════════════════════════════════════════════════

export async function getPositions(): Promise<PositionsResponse> {
  const response = await fetch(`${API_BASE}/positions`);
  if (!response.ok) throw new Error('Failed to fetch positions');
  return response.json();
}

// ═══════════════════════════════════════════════════════════════
// NEWS API
// ═══════════════════════════════════════════════════════════════

export async function getMarketNews(limit = 15): Promise<MarketNewsResponse> {
  const response = await fetch(`${API_BASE}/market/news?limit=${limit}`);
  if (!response.ok) throw new Error('Failed to fetch market news');
  return response.json();
}

export async function getStockNews(symbol: string, limit = 10): Promise<StockNewsResponse> {
  const response = await fetch(`${API_BASE}/news/${symbol.toUpperCase()}?limit=${limit}`);
  if (!response.ok) throw new Error(`Failed to fetch news for ${symbol}`);
  return response.json();
}

// ═══════════════════════════════════════════════════════════════
// STOCK API
// ═══════════════════════════════════════════════════════════════

export async function getQuote(symbol: string): Promise<Quote> {
  const response = await fetch(`${API_BASE}/quote/${symbol.toUpperCase()}`);
  if (!response.ok) throw new Error(`Failed to fetch quote for ${symbol}`);
  return response.json();
}

export async function analyzeStock(symbol: string): Promise<StockAnalysis> {
  const response = await fetch(`${API_BASE}/analyze/${symbol.toUpperCase()}`);
  if (!response.ok) throw new Error(`Failed to analyze ${symbol}`);
  return response.json();
}

// ═══════════════════════════════════════════════════════════════
// HEALTH CHECK
// ═══════════════════════════════════════════════════════════════

export async function checkHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE}/health`);
    return response.ok;
  } catch {
    return false;
  }
}
```

---

## React Hooks

Create file: `src/hooks/useChat.ts`

```typescript
import { useState, useCallback, useRef } from 'react';
import { streamChat, type ChatMessage, type ChatStreamChunk } from '../api/alphaApi';

interface UseChatReturn {
  messages: ChatMessage[];
  isLoading: boolean;
  isStreaming: boolean;
  streamingContent: string;
  error: string | null;
  sendMessage: (content: string) => Promise<void>;
  clearMessages: () => void;
  toolCalls: Array<{ name: string; result?: any }>;
}

export function useChat(): UseChatReturn {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingContent, setStreamingContent] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [toolCalls, setToolCalls] = useState<Array<{ name: string; result?: any }>>([]);
  
  const abortRef = useRef<AbortController | null>(null);

  const sendMessage = useCallback(async (content: string) => {
    if (!content.trim() || isLoading) return;

    setError(null);
    setIsLoading(true);
    setIsStreaming(true);
    setStreamingContent('');
    setToolCalls([]);

    // Add user message
    const userMessage: ChatMessage = { role: 'user', content };
    const updatedMessages = [...messages, userMessage];
    setMessages(updatedMessages);

    await streamChat(
      updatedMessages,
      // onChunk
      (chunk: ChatStreamChunk) => {
        if (chunk.type === 'text' && chunk.content) {
          setStreamingContent(prev => prev + chunk.content);
        } else if (chunk.type === 'tool_call') {
          setToolCalls(prev => [...prev, { name: chunk.name || 'unknown' }]);
        } else if (chunk.type === 'tool_result') {
          setToolCalls(prev => 
            prev.map(tc => 
              tc.name === chunk.name ? { ...tc, result: chunk.result } : tc
            )
          );
        }
      },
      // onComplete
      (fullResponse: string) => {
        const assistantMessage: ChatMessage = { role: 'assistant', content: fullResponse };
        setMessages(prev => [...prev, assistantMessage]);
        setStreamingContent('');
        setIsStreaming(false);
        setIsLoading(false);
      },
      // onError
      (errorMessage: string) => {
        setError(errorMessage);
        setIsStreaming(false);
        setIsLoading(false);
      }
    );
  }, [messages, isLoading]);

  const clearMessages = useCallback(() => {
    setMessages([]);
    setStreamingContent('');
    setError(null);
    setToolCalls([]);
  }, []);

  return {
    messages,
    isLoading,
    isStreaming,
    streamingContent,
    error,
    sendMessage,
    clearMessages,
    toolCalls,
  };
}
```

Create file: `src/hooks/usePositions.ts`

```typescript
import { useState, useEffect, useCallback } from 'react';
import { getPositions, type PositionsResponse } from '../api/alphaApi';

export function usePositions(autoRefresh = false, refreshInterval = 30000) {
  const [data, setData] = useState<PositionsResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchPositions = useCallback(async () => {
    try {
      setIsLoading(true);
      const result = await getPositions();
      setData(result);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch positions');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchPositions();

    if (autoRefresh) {
      const interval = setInterval(fetchPositions, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [fetchPositions, autoRefresh, refreshInterval]);

  return { data, isLoading, error, refresh: fetchPositions };
}
```

Create file: `src/hooks/useMarketNews.ts`

```typescript
import { useState, useEffect, useCallback } from 'react';
import { getMarketNews, type MarketNewsResponse } from '../api/alphaApi';

export function useMarketNews(limit = 15) {
  const [data, setData] = useState<MarketNewsResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchNews = useCallback(async () => {
    try {
      setIsLoading(true);
      const result = await getMarketNews(limit);
      setData(result);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch news');
    } finally {
      setIsLoading(false);
    }
  }, [limit]);

  useEffect(() => {
    fetchNews();
  }, [fetchNews]);

  return { data, isLoading, error, refresh: fetchNews };
}
```

---

## Integration Instructions

### Step 1: Setup Environment

**IMPORTANT: The Python API uses a `.env` file for secrets.**

The backend `.env` file (in the Python project root) contains:
```
OPENROUTER_API_KEY=sk-or-v1-xxxxx  # Already configured - DO NOT commit to git
```

For your React app, create/add to `.env`:
```
VITE_API_URL=http://localhost:8000/api
```

**Security Note:** The `.env` file is gitignored. Never hardcode API keys in source files.

### Step 2: Create the files above
- `src/types/api.ts` - TypeScript interfaces
- `src/api/alphaApi.ts` - API client functions
- `src/hooks/useChat.ts` - Chat hook with streaming
- `src/hooks/usePositions.ts` - Positions hook
- `src/hooks/useMarketNews.ts` - News hook

### Step 3: Integrate ChatContainer

Replace the existing chat logic in `ChatContainer.tsx` with:

```typescript
import { useChat } from '../hooks/useChat';

export function ChatContainer() {
  const {
    messages,
    isLoading,
    isStreaming,
    streamingContent,
    error,
    sendMessage,
    clearMessages,
    toolCalls,
  } = useChat();

  const [input, setInput] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim()) {
      sendMessage(input);
      setInput('');
    }
  };

  return (
    <div className="chat-container">
      {/* Messages */}
      <div className="messages">
        {messages.map((msg, i) => (
          <div key={i} className={`message ${msg.role}`}>
            {msg.content}
          </div>
        ))}
        
        {/* Streaming message */}
        {isStreaming && streamingContent && (
          <div className="message assistant streaming">
            {streamingContent}
            <span className="cursor">▊</span>
          </div>
        )}
        
        {/* Tool calls indicator */}
        {toolCalls.length > 0 && (
          <div className="tool-calls">
            {toolCalls.map((tc, i) => (
              <span key={i} className="tool-badge">
                🔧 {tc.name}
              </span>
            ))}
          </div>
        )}
        
        {/* Loading indicator */}
        {isLoading && !isStreaming && (
          <div className="message assistant loading">
            Thinking...
          </div>
        )}
        
        {/* Error */}
        {error && (
          <div className="error">{error}</div>
        )}
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="chat-input">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about any stock... (e.g., 'Why is NVDA up today?')"
          disabled={isLoading}
        />
        <button type="submit" disabled={isLoading || !input.trim()}>
          Send
        </button>
      </form>
    </div>
  );
}
```

### Step 4: Integrate Positions Page

```typescript
import { usePositions } from '../hooks/usePositions';

export function PositionsPage() {
  const { data, isLoading, error, refresh } = usePositions(true, 30000);

  if (isLoading && !data) return <div>Loading positions...</div>;
  if (error) return <div>Error: {error}</div>;
  if (!data) return null;

  return (
    <div className="positions-page">
      {/* Summary */}
      <div className="portfolio-summary">
        <div className="total-value">
          ${data.summary.total_value.toLocaleString()}
        </div>
        <div className={`total-gain ${data.summary.total_gain_loss >= 0 ? 'positive' : 'negative'}`}>
          {data.summary.total_gain_loss >= 0 ? '+' : ''}
          ${data.summary.total_gain_loss.toLocaleString()}
          ({data.summary.total_gain_loss_percent.toFixed(2)}%)
        </div>
      </div>

      {/* Positions Table */}
      <table className="positions-table">
        <thead>
          <tr>
            <th>Symbol</th>
            <th>Shares</th>
            <th>Price</th>
            <th>Value</th>
            <th>Gain/Loss</th>
            <th>Day Change</th>
          </tr>
        </thead>
        <tbody>
          {data.positions.map((pos) => (
            <tr key={pos.symbol}>
              <td>
                <strong>{pos.symbol}</strong>
                <small>{pos.company_name}</small>
              </td>
              <td>{pos.shares}</td>
              <td>${pos.current_price.toFixed(2)}</td>
              <td>${pos.current_value.toLocaleString()}</td>
              <td className={pos.gain_loss >= 0 ? 'positive' : 'negative'}>
                {pos.gain_loss >= 0 ? '+' : ''}${pos.gain_loss.toFixed(2)}
                ({pos.gain_loss_percent.toFixed(2)}%)
              </td>
              <td className={pos.day_change >= 0 ? 'positive' : 'negative'}>
                {pos.day_change >= 0 ? '+' : ''}{pos.day_change_percent.toFixed(2)}%
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      
      <button onClick={refresh}>Refresh</button>
    </div>
  );
}
```

### Step 5: Integrate News Page

```typescript
import { useMarketNews } from '../hooks/useMarketNews';

export function NewsPage() {
  const { data, isLoading, error, refresh } = useMarketNews(15);

  const sentimentIcon = {
    positive: '🟢',
    negative: '🔴',
    neutral: '⚪',
  };

  if (isLoading && !data) return <div>Loading news...</div>;
  if (error) return <div>Error: {error}</div>;
  if (!data) return null;

  return (
    <div className="news-page">
      <div className="news-header">
        <h2>Market News</h2>
        <span className="overall-sentiment">
          Overall: {sentimentIcon[data.overall_sentiment as keyof typeof sentimentIcon]} 
          {data.overall_sentiment}
        </span>
      </div>

      <div className="news-list">
        {data.articles.map((article) => (
          <a
            key={article.id}
            href={article.url}
            target="_blank"
            rel="noopener noreferrer"
            className={`news-item ${article.sentiment}`}
          >
            <span className="sentiment-icon">
              {sentimentIcon[article.sentiment]}
            </span>
            <div className="news-content">
              <h3>{article.title}</h3>
              <div className="news-meta">
                <span className="source">{article.source}</span>
                <span className="date">
                  {new Date(article.published_at).toLocaleString()}
                </span>
              </div>
            </div>
          </a>
        ))}
      </div>

      <button onClick={refresh}>Refresh</button>
    </div>
  );
}
```

---

## CSS Suggestions

```css
/* Chat */
.chat-container {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.messages {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
}

.message {
  padding: 0.75rem 1rem;
  margin-bottom: 0.5rem;
  border-radius: 8px;
  max-width: 80%;
}

.message.user {
  background: #3b82f6;
  color: white;
  margin-left: auto;
}

.message.assistant {
  background: #1f2937;
  color: #e5e7eb;
}

.message.streaming .cursor {
  animation: blink 1s infinite;
}

@keyframes blink {
  50% { opacity: 0; }
}

.tool-calls {
  display: flex;
  gap: 0.5rem;
  margin: 0.5rem 0;
}

.tool-badge {
  background: #374151;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
}

/* Positions */
.positive { color: #22c55e; }
.negative { color: #ef4444; }

/* News */
.news-item {
  display: flex;
  padding: 1rem;
  border-bottom: 1px solid #374151;
  text-decoration: none;
  color: inherit;
}

.news-item:hover {
  background: #1f2937;
}

.news-item.positive { border-left: 3px solid #22c55e; }
.news-item.negative { border-left: 3px solid #ef4444; }
.news-item.neutral { border-left: 3px solid #6b7280; }
```

---

## Testing

1. Make sure the Python API is running:
```bash
cd /path/to/wyckoff-
python3 run_api.py
```

2. Verify API is healthy:
```bash
curl http://localhost:8000/api/health
```

3. Test chat:
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"What is AAPL trading at?"}],"stream":false}'
```

---

## Key Features

1. **Streaming Chat**: Real-time responses with tool calling
2. **Auto Tool Execution**: AI automatically fetches stock data when needed
3. **Cited Sources**: News references with [1], [2] citations
4. **Live Prices**: Real-time portfolio updates
5. **Sentiment Analysis**: News sentiment for market awareness

The API is running at `http://localhost:8000` with docs at `http://localhost:8000/docs`.

